# -*- coding: utf-8 -*-
"""把 live.template.html 的占位符替换成 base64 图片，产出可直接双击运行的单文件 HTML。"""
import base64
import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, 'live.template.html')
OUT = os.path.join(BASE, 'duel-live.html')

ASSETS = {
    '__IMG_A__': ('art/a.png', 'png'),
    '__IMG_B__': ('art/b.png', 'png'),
    '__IMG_HAMMER__': ('props/hammer.png', 'png'),
    '__IMG_ICE__': ('assets/src/iceland.jpg', 'jpeg'),
    '__IMG_DUCK__': ('art/duck.png', 'png'),      # v3.0 摇摆鸭
    '__IMG_QR__': ('assets/src/qr.png', 'png'),   # v3.0 弹窗二维码（指向仓库）
}

src = io.open(TPL, encoding='utf-8').read()

for key, item in ASSETS.items():
    rel, mime = item
    path = os.path.join(BASE, rel)
    raw = open(path, 'rb').read()
    uri = 'data:image/%s;base64,%s' % (mime, base64.b64encode(raw).decode('ascii'))
    if key not in src:
        raise SystemExit('模板里找不到占位符 ' + key)
    src = src.replace(key, uri)
    print('%-14s %6.1f KB  %s' % (os.path.basename(rel), len(raw) / 1024, mime))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(src)
print('-> %s  (%.0f KB)' % (OUT, os.path.getsize(OUT) / 1024))
