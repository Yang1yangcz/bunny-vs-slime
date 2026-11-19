# -*- coding: utf-8 -*-
"""跑 N 局实时演算，统计胜率 / 时长 / 大招次数。可临时覆盖 CFG 里的任意参数：
    python _tune.py 20
    python _tune.py 20 slime.spit.period=3.4 slime.spit.dmgAtkRatio=0.7
"""
import json
import os
import sys
import time

sys.path.insert(0, r'C:\Users\yang1yang\.workbuddy\skills\bounce-duel-video\scripts')
import record as R

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, 'duel-live.html').replace('\\', '/')
PORT = 9471
MAX_SIM = 240          # 单局最多推进 240 模拟秒


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


def set_path_js(path, val):
    return ("(function(){var o=window.__CFG,p='%s'.split('.');"
            "for(var i=0;i<p.length-1;i++)o=o[p[i]];o[p[p.length-1]]=%s;})()"
            % (path, json.dumps(val)))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    overrides = []
    for a in sys.argv[2:]:
        if '=' not in a:
            continue
        k, v = a.split('=', 1)
        overrides.append((k.strip(), float(v) if '.' in v or 'e' in v.lower() else int(v)))

    prof = os.path.join(BASE, '_tune_prof')
    p = R.start_chrome(prof, 1920, 1080, PORT)
    rows = []
    try:
        drv = R.CDP(R.page_ws(PORT))
        drv.send('Page.enable')
        drv.send('Runtime.enable')
        drv.send('Emulation.setDeviceMetricsOverride',
                 {'width': 1920, 'height': 1080, 'deviceScaleFactor': 1, 'mobile': False})
        drv.send('Page.navigate', {'url': 'file:///' + HTML})
        for _ in range(80):
            time.sleep(0.2)
            try:
                if drv.eval('!!window.__sim'):
                    break
            except Exception:
                pass

        drv.eval(SEED_JS)
        # 暂停页面自带的实时主循环，否则它会和 __sim.advance 叠加，结果不可复现
        drv.eval('__sim.pause()')
        time.sleep(0.2)

        for path, val in overrides:
            drv.eval(set_path_js(path, val))
        if overrides:
            print('覆盖参数:', ', '.join('%s=%s' % kv for kv in overrides))

        for i in range(n):
            drv.eval('__seed(%d)' % (i * 7919 + 13))
            drv.eval("document.getElementById('btnReset').click()")
            for path, val in overrides:
                drv.eval(set_path_js(path, val))
            t = 0.0
            st = None
            while t < MAX_SIM:
                drv.eval('__sim.advance(0.5)')
                t += 0.5
                st = json.loads(drv.eval('JSON.stringify(__sim.state())'))
                if st['over']:
                    break
            rows.append(st)
            d, h = st['dealt'], st.get('hits', [0, 0])
            print('  #%-2d %-6s %5.1fs hp=%-13s ult=%d 回血=%-5s | 兔输出%-6d(命中%d) 史输出%-6d(命中%d)'
                  % (i + 1, st['over'] or 'TIMEOUT', st['clock'], st['hp'],
                     st.get('ultCount', -1), st.get('healed', [0, 0])[0],
                     d[0], h[0], d[1], h[1]))

        a = sum(1 for r in rows if r['over'] == 'rabbit')
        b = sum(1 for r in rows if r['over'] == 'slime')
        to = sum(1 for r in rows if not r['over'])
        dur = [r['clock'] for r in rows if r['over']]
        ults = [r.get('ultCount', 0) for r in rows]
        print('\n结果: 兔子 %d : 史莱姆 %d%s  平均 %.1fs  大招平均 %.2f 次'
              % (a, b, '' if not to else '  超时 %d' % to,
                 sum(dur) / len(dur) if dur else 0, sum(ults) / len(ults)))
    finally:
        p.terminate()
        time.sleep(0.4)


if __name__ == '__main__':
    main()
