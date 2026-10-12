# -*- coding: utf-8 -*-
r"""용어·고유명사 일관성 조사 — 원문의 대문자 낱말(문장 첫 낱말 제외)·색 태그 낱말별로
  번역에 영어 그대로 남긴 줄 수 / 한글로 옮긴 줄 수 + 한글 후보(그 낱말이 든 줄에만 몰려 나오는 한글 낱말).
  python tools/term_scan.py <번역 폴더> [최소 출현=5]  → work/terms.tsv
"""
import collections, glob, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_tr

STOP = set('I A The This That These Those We You He She It They Our Your My His Her Its Their Is Are Was Were Be If When Then And But Or So As At In On Of To For By With From Not No Yes Do Does Did All Any What Who Why How Where There Here Mr Ms OK Okay Good Well Now Let Sir Please Command Alpha Beta Gamma Delta Epsilon'.split())


def hangul_words(s):
    return set(re.findall(r'[가-힣]{2,}', s))


def strip_josa(w):
    return re.sub(r'(은|는|이|가|을|를|의|에|에서|에게|로|으로|와|과|도|만|께서|이다|다|호|급)$', '', w)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    minc = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    tr = check_tr.load(sys.argv[1])
    rows = [(t[2][0], t[2][3], t[2][4]) for t in tr.values() if len(t[2]) == 5]
    occ = collections.defaultdict(list)
    for i, s, k in rows:
        clean = re.sub(r'\$[a-zA-Z|]\s?', ' ', s).replace('\\n', ' ')
        for sent in re.split(r'(?<=[.!?])\s+', clean):
            words = re.findall(r"[A-Za-z][A-Za-z'\-]+", sent)
            for j, w in enumerate(words):
                if j == 0 or w in STOP or not w[0].isupper() or w.isupper() and len(w) <= 4:
                    continue
                occ[w].append((i, k))
    df = collections.Counter()
    for _, _, k in rows:
        for w in {strip_josa(x) for x in hangul_words(k)}:
            df[w] += 1
    N = len(rows)
    out = []
    for w, L in occ.items():
        ids = {i for i, _ in L}
        if len(ids) < minc:
            continue
        keep = sum(1 for i, k in dict(L).items() if re.search(r'\b%s' % re.escape(w), k))
        tf = collections.Counter()
        for i, k in dict(L).items():
            if not re.search(r'\b%s' % re.escape(w), k):
                for x in {strip_josa(x) for x in hangul_words(k)}:
                    tf[x] += 1
        cand = sorted(((c * math.log(N / df[x]), x, c) for x, c in tf.items() if c >= 2), reverse=True)[:4]
        out.append((len(ids), w, keep, len(ids) - keep, ' '.join('%s(%d)' % (x, c) for _, x, c in cand)))
    out.sort(reverse=True)
    with open(os.path.join(ROOT, 'work', 'terms.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('줄수\t원어\t영어 그대로\t옮김\t한글 후보\n')
        for r in out:
            f.write('%d\t%s\t%d\t%d\t%s\n' % r)
    for r in out[:120]:
        print('%4d %-14s 영%4d 한%4d  %s' % r)


if __name__ == '__main__':
    main()
