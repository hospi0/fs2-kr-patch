# -*- coding: utf-8 -*-
r"""받은 번역 검사 — 원문(work/tsv/fs2_*.tsv)과 ID·원문 일치, 빈 번역, 토큰 보존.
  토큰: \n 개수 · \t · printf(%s %d %i %f %%) · 키 표시 $…$ · 색 태그 $f $h $b $y $w $g $r … 와 $| · [숫자] 각주
  python tools/check_tr.py <번역 폴더>  → work/check_tr.tsv
"""
import collections, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

KEY = re.compile(r'\$(?![a-z] )[^\s$|][^$\n\\]*?\$(?!\|)')     # $t$ · $alt-j$ · $left ctrl$ (색 태그 «$b 낱말» 과 «$|» 는 제외)
COLOR = re.compile(r'\$([a-z])(?=[ ㄱ-힣A-Za-z0-9])')  # 색 태그(다음 낱말)
PRINTF = re.compile(r'%[-+0-9.]*[sdifu]|%%')


def toks(s):
    keys = KEY.findall(s)
    rest = KEY.sub(' ', s)
    return {
        '줄바꿈': s.count('\\n'), '탭': s.count('\\t'),
        'printf': sorted(PRINTF.findall(s)),
        '키': sorted(keys),
        '색': sorted(COLOR.findall(rest)), '색끝': rest.count('$|'),
        '각주': sorted(re.findall(r'\[\d+\]', s)),
    }


def load(folder):
    tr = collections.OrderedDict()
    for p in sorted(glob.glob(os.path.join(folder, '*.tsv'))):
        for n, ln in enumerate(list(open(p, encoding='utf-8-sig'))[1:], 2):
            c = ln.rstrip('\r\n').split('\t')
            tr[c[0]] = (os.path.basename(p), n, c)
    return tr


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    src = collections.OrderedDict()
    for p in sorted(glob.glob(os.path.join(ROOT, 'work', 'tsv', 'fs2_*.tsv'))):
        for ln in list(open(p, encoding='utf-8'))[1:]:
            c = ln.rstrip('\n').split('\t'); src[c[0]] = c
    tr = load(sys.argv[1])
    out = []; cnt = collections.Counter()
    for i, c in src.items():
        if i not in tr:
            out.append((i, '빠짐', '', '')); cnt['빠짐'] += 1; continue
        f, n, t = tr[i]
        if len(t) != 5:
            out.append((i, '열 %d' % len(t), f, '')); cnt['열'] += 1; continue
        if t[3] != c[3]:
            out.append((i, '원문 바뀜', f, t[3][:80])); cnt['원문 바뀜'] += 1
        k = t[4]
        if not k.strip():
            out.append((i, '빈 번역', f, '')); cnt['빈 번역'] += 1; continue
        a, b = toks(c[3]), toks(k)
        for key in a:
            if a[key] != b[key]:
                out.append((i, '토큰 ' + key, f, '%s → %s' % (a[key], b[key]))); cnt['토큰 ' + key] += 1
    extra = [i for i in tr if i not in src]
    for i in extra:
        out.append((i, '원문에 없는 ID', tr[i][0], '')); cnt['원문에 없는 ID'] += 1
    with open(os.path.join(ROOT, 'work', 'check_tr.tsv'), 'w', encoding='utf-8', newline='') as o:
        o.write('ID\t문제\t파일\t내용\n')
        for r in out:
            o.write('\t'.join(r) + '\n')
    print('원문 %d · 번역 %d' % (len(src), len(tr)))
    for k, v in cnt.most_common():
        print('  %s %d' % (k, v))


if __name__ == '__main__':
    main()
