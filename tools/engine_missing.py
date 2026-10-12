# -*- coding: utf-8 -*-
r"""FSO 24.2 코드의 XSTR(엔진 문구) 중 strings.tbl #English 에 없는 번호 → work/text/engine_missing.tsv
  (표에 없으면 영어가 코드 안 글 그대로 나온다 — 2026-10-12 종료 창 «No/Yes» = POPUP_YES/NO 505·506)
  python tools/engine_missing.py
"""
import collections, os, re, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
X = re.compile(r'XSTR\s*\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*[,)]')
# 조작 설정 항목: (ENUM, 키, -1, 탭, 번호, "이름", CC_TYPE_…) — 번호가 글 앞
C = re.compile(r'\b(\d{3,4}),\s*"((?:[^"\\]|\\.)*)",\s*CC_TYPE')
U = re.compile(r'\{\s*"((?:[^"\\]|\\.)*)"\s*,\s*(\d+)\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*UI_XSTR')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    z = zipfile.ZipFile(os.path.join(ROOT, 'work', os.environ.get('FSO_SRC', 'fsosrc2601'), 'src.zip') if os.environ.get('FSO_SRC', 'fsosrc2601') != 'fsosrc242' else os.path.join(ROOT, 'work', 'fsosrc242', 'zip', 'src.zip'))   # 설치 FSO = 26.0.1(2026-10-12~)
    have = {int(l.split('\t')[0]) for l in list(open(os.path.join(ROOT, 'work', 'text', 'strings.tsv'), encoding='utf-8'))[1:]}
    miss = collections.OrderedDict(); allc = 0
    for n in z.namelist():
        low = n.lower()
        if '/code/' not in n or not n.endswith(('.cpp', '.h')) or 'fred' in low:
            continue
        t = z.read(n).decode('latin1')
        for m in list(X.finditer(t)) + list(U.finditer(t)):
            i = int(m.group(2)); allc += 1
            if i not in have:
                miss.setdefault(i, (m.group(1), n.split('/')[-1]))
        for m in C.finditer(t):
            i = int(m.group(1)); allc += 1
            if i not in have:
                miss.setdefault(i, (m.group(2), n.split('/')[-1]))
    with open(os.path.join(ROOT, 'work', 'text', 'engine_missing.tsv'), 'w', encoding='utf-8', newline='') as w:
        w.write('id\t원문\t파일\n')
        for i, (s, f) in sorted(miss.items()):
            w.write('%d\t%s\t%s\n' % (i, s, f))
    print('코드 XSTR %d곳 · 영어 표에 없는 번호 %d' % (allc, len(miss)))
    for i, (s, f) in list(sorted(miss.items()))[:30]:
        print(i, repr(s)[:60], f)


if __name__ == '__main__':
    main()
