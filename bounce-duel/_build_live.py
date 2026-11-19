# -*- coding: utf-8 -*-
"""把 live.template.html 里的占位符替换成 base64 图片，产出可直接双击运行的单文件 HTML。"""
import base64
import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, 'live.template.html')
OUT = os.path.join(BASE, 'duel-live.html')

ASSETS = {
    '__IMG_A__': os.path.join(BASE, 'art', 'a.png'),
    '__IMG_B__': os.path.join(BASE, 'art', 'b.png'),
    '__IMG_HAMMER__': os.path.join(BASE, 'props', 'hammer.png'),
}

src = io.open(TPL, encoding='utf-8').read()

for key, path in ASSETS.items():
    raw = open(path, 'rb').read()
    uri = 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')
    if key not in src:
        raise SystemExit('模板里找不到占位符 ' + key)
    src = src.replace(key, uri)
    print('%-16s %6.1f KB' % (os.path.basename(path), len(raw) / 1024))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(src)
print('-> %s  (%.0f KB)' % (OUT, os.path.getsize(OUT) / 1024))
