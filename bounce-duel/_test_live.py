# -*- coding: utf-8 -*-
"""无头浏览器跑 duel-live.html：多局统计 + 关键画面截图。"""
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
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 6

port = 9431
p = R.start_chrome(os.path.join(BASE, '_live_prof'), 1500, 1000, port)
try:
    drv = R.CDP(R.page_ws(port))
    drv.send('Page.enable')
    drv.send('Runtime.enable')
    drv.send('Page.navigate', {'url': 'file:///' + HTML.replace('\\', '/')})

    ok = False
    for _ in range(70):
        time.sleep(0.2)
        try:
            if drv.eval('!!(window.__sim)'):
                ok = True
                break
        except Exception:
            pass
    if not ok:
        raise SystemExit('页面没起来（可能有 JS 报错）')

    wins = {'rabbit': 0, 'slime': 0}
    durs, ult, counter = [], 0, 0

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
        if st['ult']:
            ult += 1
        print('第 %d 局：%s 胜  %.1fs  兔子 %s / 史莱姆 %s'
              % (i + 1, '兔子' if st['over'] == 'rabbit' else '史莱姆',
                 st['clock'], round(st['hp'][0]), round(st['hp'][1])), flush=True)

    print('\n兔子 %d : %d 史莱姆   平均 %.1fs   大招触发 %d/%d'
          % (wins['rabbit'], wins['slime'],
             sum(durs) / len(durs) if durs else 0, ult, ROUNDS))

    def shot(name):
        s = drv.send('Page.captureScreenshot', {'format': 'png'})
        with open(os.path.join(OUT, name + '.png'), 'wb') as f:
            f.write(base64.b64decode(s['data']))

    # 1) 普通对局画面
    drv.eval("document.getElementById('btnReset').click()")
    drv.eval('__sim.advance(7)')
    shot('normal')

    # 2) 等到大招触发（冰岛背景）
    drv.eval("document.getElementById('btnReset').click()")
    for _ in range(200):
        drv.eval('__sim.advance(0.5)')
        st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
        if st['ult']:
            break
    drv.eval('__sim.advance(0.8)')
    st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
    print('大招瞬间:', st)
    shot('ice')

    # 3) 道德制高点浮空
    drv.eval('__sim.advance(2.0)')
    shot('ice2')

    # 4) 详细面板
    drv.eval("document.getElementById('btnDetail').click()")
    time.sleep(0.3)
    shot('detail')

    print('截图 ->', OUT)
finally:
    p.terminate()
    time.sleep(0.5)
