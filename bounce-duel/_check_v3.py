# -*- coding: utf-8 -*-
"""v3.0 自检：打开 duel-live.html，抓 JS 报错、跑几秒、截图（含弹窗）。

    python _check_v3.py            # 正常流程 + 截图
    python _check_v3.py --modal    # 强制弹一次增益弹窗并截图
"""
import base64
import json
import os
import sys
import time

sys.path.insert(0, r'C:\Users\yang1yang\.workbuddy\skills\bounce-duel-video\scripts')
import record as R

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, 'duel-live.html').replace('\\', '/')
SHOTS = os.path.join(BASE, 'shots')
PORT = 9483

HOOK = r'''(function(){
  window.__errors = [];
  window.addEventListener('error', function(e){ window.__errors.push(String(e.message) + ' @' + e.lineno); });
  window.addEventListener('unhandledrejection', function(e){ window.__errors.push('rejection: ' + e.reason); });
  var ce = console.error;
  console.error = function(){ window.__errors.push('console.error: ' + Array.prototype.join.call(arguments,' ')); ce.apply(console, arguments); };
})()'''


def shot(drv, name):
    os.makedirs(SHOTS, exist_ok=True)
    res = drv.send('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
    path = os.path.join(SHOTS, name)
    open(path, 'wb').write(base64.b64decode(res['data']))
    print('  shot ->', path)
    return path


def main():
    modal = '--modal' in sys.argv
    modal2 = '--modal2' in sys.argv
    prof = os.path.join(BASE, '_chk_v3_prof')
    p = R.start_chrome(prof, 1600, 1000, PORT)
    try:
        drv = R.CDP(R.page_ws(PORT))
        drv.send('Page.enable')
        drv.send('Runtime.enable')
        drv.send('Emulation.setDeviceMetricsOverride',
                 {'width': 1600, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': False})
        drv.send('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        drv.send('Page.navigate', {'url': 'file:///' + HTML})
        for _ in range(80):
            time.sleep(0.2)
            try:
                if drv.eval('!!window.__sim'):
                    break
            except Exception:
                pass
        time.sleep(0.6)

        try:
            print('errors:', json.loads(drv.eval('JSON.stringify(window.__errors)') or '[]'))
        except Exception as exc:
            print('errors: <read failed>', exc)
        print('state :', json.dumps(json.loads(drv.eval('JSON.stringify(__sim.state())')), ensure_ascii=False))

        drv.eval('__sim.pause()')
        drv.eval('__sim.setAuto(true)')
        drv.eval('__sim.advance(6, true)')
        drv.eval('__sim.resume()')
        time.sleep(0.5)
        print('after 6s:', json.dumps(json.loads(drv.eval('JSON.stringify(__sim.state())')), ensure_ascii=False))
        shot(drv, 'v3_play.png')

        # 中后期：已经吃过一次增益
        drv.eval('__sim.pause()')
        drv.eval('__sim.advance(9, true)')
        drv.eval('__sim.resume()')
        time.sleep(0.5)
        print('after +9s:', json.dumps(json.loads(drv.eval('JSON.stringify(__sim.duckState())')), ensure_ascii=False))
        shot(drv, 'v3_mid.png')

        # 强制弹窗：直接调用内部结算
        if modal or modal2:
            drv.eval('__sim.pause()')
            drv.eval('__sim.setAuto(false)')
            drv.eval("__sim.settle('rabbit')")
            time.sleep(0.5)
            shot(drv, 'v3_modal.png')
            print('modal state:', json.dumps(json.loads(drv.eval('JSON.stringify(__sim.duckState())')), ensure_ascii=False))
            drv.eval('__sim.closeModal()')
            drv.eval('__sim.setAuto(true)')
            time.sleep(0.4)
            drv.eval('__sim.advance(1.2, true)')
            drv.eval('__sim.resume()')
            time.sleep(0.5)
            shot(drv, 'v3_joined.png')
        if modal2:
            # 切到「增益对象」页并打开策划面板
            drv.eval("document.querySelector('.bili-tabs .tab[data-pane=info]').click()")
            time.sleep(0.3)
            shot(drv, 'v3_modal_info.png')
            drv.eval("document.getElementById('btnDesigner').click()")
            time.sleep(0.3)
            shot(drv, 'v3_designer.png')
        print('errors end:', json.loads(drv.eval('JSON.stringify(window.__errors)')))
        drv.close()
    finally:
        p.terminate()
        time.sleep(0.4)


if __name__ == '__main__':
    main()
