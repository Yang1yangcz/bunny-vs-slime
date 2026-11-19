# -*- coding: utf-8 -*-
"""无头浏览器跑 duel-live.html：多局统计 + K.O./MVP 关键帧截图。"""
import base64
import json
import os
import sys
import time

SKILL = r'C:\Users\yang1yang\.workbuddy\skills\bounce-duel-video'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
import record as R  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, 'duel-live.html')
OUT = os.path.join(BASE, 'shots')
os.makedirs(OUT, exist_ok=True)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 8

port = 9441
p = R.start_chrome(os.path.join(BASE, '_live_prof'), 1920, 1080, port)
try:
    drv = R.CDP(R.page_ws(port))
    drv.send('Page.enable')
    drv.send('Runtime.enable')
    drv.send('Emulation.setDeviceMetricsOverride',
             {'width': 1920, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
    drv.send('Page.navigate', {'url': 'file:///' + HTML.replace('\\', '/')})

    ok = False
    for _ in range(80):
        time.sleep(0.2)
        try:
            if drv.eval('!!(window.__sim)'):
                ok = True
                break
        except Exception:
            pass
    if not ok:
        raise SystemExit('页面没起来（可能有 JS 报错）')

    def shot(name):
        s = drv.send('Page.captureScreenshot', {'format': 'png'})
        with open(os.path.join(OUT, name + '.png'), 'wb') as f:
            f.write(base64.b64decode(s['data']))

    wins = {'rabbit': 0, 'slime': 0}
    durs = []

    for i in range(ROUNDS):
        drv.eval("document.getElementById('btnReset').click()")
        st = None
        for sec in range(1, 121):
            drv.eval('__sim.advance(1)')
            st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
            if st['over']:
                break
        if not st['over']:
            print('第 %d 局 120s 未分胜负' % (i + 1))
            continue
        wins[st['over']] += 1
        durs.append(round(st['clock'], 1))
        print('第 %d 局：%s 胜  %.1fs  兔子 %s / 史莱姆 %s'
              % (i + 1, '兔子' if st['over'] == 'rabbit' else '史莱姆',
                 st['clock'], round(st['hp'][0]), round(st['hp'][1])), flush=True)

    print('\n兔子 %d : %d 史莱姆   平均 %.1fs'
          % (wins['rabbit'], wins['slime'], sum(durs) / len(durs) if durs else 0))

    # 普通画面（大场地 + 大字号）
    drv.eval("document.getElementById('btnReset').click()")
    drv.eval('__sim.advance(7)')
    shot('normal')

    # 打到 K.O.（死后再走 0.3s，KO 大字动画中）
    drv.eval("document.getElementById('btnReset').click()")
    for _ in range(240):
        drv.eval('__sim.advance(0.5)')
        st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
        if st['over']:
            break
    drv.eval('__sim.advance(0.3)')
    time.sleep(0.75)
    shot('ko')

    # 再过 1.6s → MVP 卡片
    drv.eval('__sim.advance(1.6)')
    time.sleep(0.75)
    shot('mvp')

    print('截图 ->', OUT)
finally:
    p.terminate()
    time.sleep(0.5)
