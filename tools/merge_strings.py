# -*- coding: utf-8 -*-
r"""받은 strings 번역(id·원문·번역) → data/strings_ko.tsv (work/text/strings.tsv 의 id 기준).
  예전 추출에서 여러 항목이 한 칸에 뭉친 줄(«…""\t\t; Kills \n631, ""…»)은 번역 칸을 같은 경계로 다시 쪼갠다.
  python tools/merge_strings.py <받은.tsv>
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SPLIT = re.compile(r'""[^"]*?\\n(\d+),?\s+""')       # 쉼표 빠진 항목(1524  "&Go back")도


def unq(s):
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == '"' else s


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    src = {}
    for ln in list(open(os.path.join(ROOT, 'work', 'text', 'strings.tsv'), encoding='utf-8'))[1:]:
        i, s = ln.rstrip('\n').split('\t', 1); src[int(i)] = s
    ko = {}
    for ln in list(open(sys.argv[1], encoding='utf-8'))[1:]:
        c = ln.rstrip('\n').split('\t')
        if len(c) == 3 and '""' not in c[2]:
            ko[int(c[0])] = c[2]; continue
        # 뭉친 줄: 원문 칸과 번역 칸이 탭으로 섞여 있다 → 원래 줄 전체에서 원문 개수만큼 번역 쪼개기
        body = '\t'.join(c[1:])
        half = len(c[1:]) // 2
        tr = unq('\t'.join(c[1 + half:]))
        parts = SPLIT.split(tr)
        ids = [int(c[0])] + [int(x) for x in parts[1::2]]
        for i, t in zip(ids, parts[0::2]):
            ko[i] = t.split('""')[0]          # 남은 «"" ; 주석» 꼬리 자르기
        print('쪼갬', ids)
    miss = [i for i in src if i not in ko]
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'strings_ko.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('id\t원문\t번역\n')
        for i, s in src.items():
            f.write('%d\t%s\t%s\n' % (i, s, ko.get(i, '')))
    print('번역 %d / %d · 빈칸 %d %s' % (len(src) - len(miss), len(src), len(miss), miss[:40]))


if __name__ == '__main__':
    main()
