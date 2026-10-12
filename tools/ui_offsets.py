# -*- coding: utf-8 -*-
r"""메뉴 글자 x 보정값 계산 → data/ui_offsets.tsv (id · 640 보정 · 1024 보정 · 근거)
  FSO 메뉴 글자 = UI_XSTR {글, id, x, y, 색, 글꼴, 묶인 버튼} — «왼쪽 x 고정»으로 찍고, 번역판은 strings.tbl 항목 뒤
  보정값(640·1024)만큼 옮긴다(ui/window.cpp draw_one_xstr: x + lcl_get_xstr_offset(id, res)).
  원래 영어 글은 오른쪽 끝을 버튼에 맞춰 x 를 잡은 것이 많다 → 한글은 끝이 들쭉날쭉(2026-10-12 «오른쪽 메뉴가 물결»).
  판정: 같은 배열·같은 해상도 안에서 영어 오른쪽 끝(x + 폭)이 다른 항목과 ±2 화소로 맞고 왼쪽 x 는 다른 항목 = 오른쪽 정렬.
  폭: 영어 = font01.vf 글자 간격 합(work/fonts, sparky_fs2.vp) · 한글 = 나눔고딕 12px(fonts.tbl font01 과 같게).
  python tools/ui_offsets.py
"""
import collections, glob, os, re, struct, sys, zipfile
from PIL import ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'work', 'fsosrc2601', 'src.zip')   # 설치 FSO = 26.0.1(2026-10-12~, 예전 fsosrc242)
KFONT = r'C:\claude\utils\font\nanum-gothic\NanumGothic.ttf'
KSIZE = 12
# TTF 는 화면 화소로 찍히고(크기 고정) 메뉴 좌표만 1024 기준에서 확대된다 → 한글 폭을 1024 좌표로 바꾸려면 배율로 나눔.
# 하스피 화면 실측(2026-10-12): 메뉴 1024 → 화면 약 1116 화소 = 1.09
SCALE = float(os.environ.get('UI_SCALE', '1.09'))


def vf_widths(p):
    b = open(p, 'rb').read()
    _, ver, n, first, w, h, nk, kds, cds, pds = struct.unpack_from('<4s9i', b, 0)
    off = 40 + kds
    sp = {}
    for i in range(n):
        spacing, = struct.unpack_from('<i', b, off + 16 * i)
        sp[first + i] = spacing
    return sp


def en_width(s, sp):
    return sum(sp.get(ord(c), sp.get(32, 3)) for c in s)


ENT = re.compile(r'\{\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*([A-Za-z_0-9]+)\s*,\s*(-?\d+)\s*,')


def arrays():
    """[(파일, 배열 이름, 해상도 번호, [(글, id, x, y, 글꼴)])]"""
    out = []
    z = zipfile.ZipFile(SRC)
    for p in z.namelist():
        if not p.endswith('.cpp') or '/code/' not in p:
            continue
        t = z.read(p).decode('latin1')
        for m in re.finditer(r'UI_XSTR\s+(\w+)\s*\[\s*GR_NUM_RESOLUTIONS\s*\]\s*\[[^\]]*\]\s*=\s*\{', t):
            # 배열 본문: 중괄호 짝 맞추기
            i = m.end(); depth = 1; j = i
            while depth and j < len(t):
                if t[j] == '{': depth += 1
                elif t[j] == '}': depth -= 1
                j += 1
            body = t[i:j - 1]
            # 해상도 블록 = 깊이 1 의 { … } 두 개
            blocks = []; d = 0; st = None
            for k, ch in enumerate(body):
                if ch == '{':
                    if d == 0: st = k
                    d += 1
                elif ch == '}':
                    d -= 1
                    if d == 0: blocks.append(body[st:k + 1])
            for r, bl in enumerate(blocks[:2]):
                ents = [(e.group(1), int(e.group(2)), int(e.group(3)), int(e.group(4)), int(e.group(6))) for e in ENT.finditer(bl)]
                out.append((os.path.basename(p), m.group(1), r, ents))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sp = vf_widths(os.path.join(ROOT, 'work', 'fonts', 'font01.vf'))
    kf = ImageFont.truetype(KFONT, KSIZE)
    ko = {}
    for ln in list(open(os.path.join(ROOT, 'data', 'strings_ko.tsv'), encoding='utf-8'))[1:]:
        i, s, t = ln.rstrip('\n').split('\t')
        ko[int(i)] = t
    res_off = collections.defaultdict(dict)    # id → {res: [보정값]}
    why = collections.defaultdict(list)
    n_arr = 0
    for f, name, r, ents in arrays():
        n_arr += 1
        info = []
        for s, i, x, y, font in ents:
            if font not in (-1, 0):      # font01 이 아닌 글꼴은 이번엔 손대지 않음
                continue
            en = s[1:] if s.startswith('&') else s
            we = en_width(en, sp)
            info.append((s, i, x, y, we))
        for s, i, x, y, we in info:
            r_e = x + we
            mates = [o for o in info if o[1] != i and abs((o[2] + o[4]) - r_e) <= 2 and abs(o[2] - x) > 3]
            if not mates or i not in ko:
                continue
            k = ko[i]; k = k[1:] if k.startswith('&') else k
            wk = kf.getlength(k.replace('\\n', '')) / SCALE
            res_off[i].setdefault(r, []).append(round(r_e - (x + wk)))
            why[i].append('%s:%s' % (f, name))
    rows = []; conflict = 0
    for i, d in sorted(res_off.items()):
        o640 = d.get(0, [0]); o1024 = d.get(1, [0])
        if len(set(o640)) > 1 or len(set(o1024)) > 1:
            conflict += 1
        rows.append((i, int(sum(o640) / len(o640)), int(sum(o1024) / len(o1024)), ' '.join(sorted(set(why[i])))))
    with open(os.path.join(ROOT, 'data', 'ui_offsets.tsv'), 'w', encoding='utf-8', newline='') as w:
        w.write('id\t640\t1024\t근거(오른쪽 정렬 무리)\n')
        for r in rows:
            w.write('%d\t%d\t%d\t%s\n' % r)
    print('배열 %d개 · 오른쪽 정렬로 판정한 문구 %d개 · 자리마다 값이 다른 것 %d' % (n_arr, len(rows), conflict))
    for r in rows[:15]:
        print(' ', r[0], ko.get(r[0]), r[1], r[2], r[3][:60])


if __name__ == '__main__':
    main()
