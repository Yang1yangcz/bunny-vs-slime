# -*- coding: utf-8 -*-
"""生成 README / release 用的截图（docs/screenshots/）。

    python _shots.py
"""
import base64
import json
import os
import sys
import time

sys.path.insert(0, r'C:\Users\yang1yang\.workbuddy\skills\bounce-duel-video\scripts')
import record as R

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
HTML = os.path.join(BASE, 'duel-live.html').replace('\\', '/')
OUT = os.path.join(ROOT, 'docs', 'screenshots')
PORT = 9487

SEED_JS = '''(function(){
  window.__seed = function(s){
    var a = s >>> 0;
    Math.random = function(){
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  };
})()'''


def shot(drv, name, clip=None):
    os.makedirs(OUT, exist_ok=True)
    params = {'format': 'png', 'captureBeyondViewport': False}
    if clip:
        params['clip'] = {'x': clip[0], 'y': clip[1], 'width': clip[2], 'height': clip[3], 'scale': 1}
    res = drv.send('Page.captureScreenshot', params)
    path = os.path.join(OUT, name)
    open(path, 'wb').write(base64.b64decode(res['data']))
    print('  ->', path, os.path.getsize(path) // 1024, 'KB')


def main():
    p = R.start_chrome(os.path.join(BASE, '_shots_prof'), 1600, 1000, PORT)
    try:
        drv = R.CDP(R.page_ws(PORT))
        drv.send('Page.enable')
        drv.send('Runtime.enable')
        drv.send('Emulation.setDeviceMetricsOverride',
                 {'width': 1600, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': False})
        drv.send('Page.navigate', {'url': 'file:///' + HTML})
        for _ in range(80):
            time.sleep(0.2)
            try:
                if drv.eval('!!window.__sim'):
                    break
            except Exception:
                pass
        drv.eval(SEED_JS)
        drv.eval('__sim.pause()')

        # 1) 中立阶段的完整画面
        drv.eval('__seed(20261128)')
        drv.eval('__sim.setAuto(true)')
        drv.eval('document.getElementById("btnReset").click()')
        drv.eval('__sim.advance(4.6, true)')
        for _ in range(8):
            st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
            if st['iceT'] <= 0 and not st['over']:
                break
            drv.eval('__sim.advance(1.0, true)')
        drv.eval('__sim.resume()')
        time.sleep(0.45)
        shot(drv, 'v3-duel.png')

        # 2) 增益落地后的画面
        drv.eval('__sim.pause()')
        for _ in range(40):
            st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
            if st['duck']['round'] >= 1:
                break
            drv.eval('__sim.advance(0.8, true)')
        # 让横幅淡出，并避开冰岛背景
        drv.eval('__sim.advance(2.4, true)')
        for _ in range(6):
            st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
            if st['iceT'] <= 0 or st['over']:
                break
            drv.eval('__sim.advance(1.2, true)')
        drv.eval('__sim.resume()')
        time.sleep(0.45)
        shot(drv, 'v3-buffed.png')

        # 3) 增益弹窗（B 站登录风）—— 先等冰岛背景退掉，避免整页发暗
        drv.eval('__sim.pause()')
        for _ in range(10):
            st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
            if st['iceT'] <= 0 or st['over']:
                break
            drv.eval('__sim.advance(1.0, true)')
        # 让主循环跑一帧，把冰岛背景 / 全屏暗色的 DOM 状态刷新掉
        drv.eval('__sim.resume()')
        time.sleep(0.35)
        drv.eval('__sim.pause()')
        drv.eval('__sim.setAuto(false)')
        drv.eval("__sim.settle('rabbit')")
        time.sleep(1.1)          # 等入场动画 + 错层动画播完
        shot(drv, 'v3-buff-modal.png')

        # 4) 策划面板
        drv.eval("document.getElementById('btnDesigner').click()")
        time.sleep(0.35)
        shot(drv, 'v3-designer.png')
        drv.eval("document.getElementById('dClose').click()")
        drv.eval('__sim.closeModal()')

        print('errors:', drv.eval('JSON.stringify(window.__errors||[])'))
        drv.close()
    finally:
        p.terminate()
        time.sleep(0.4)


if __name__ == '__main__':
    main()
