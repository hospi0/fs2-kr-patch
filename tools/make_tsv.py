# -*- coding: utf-8 -*-
r"""번역 TSV 나누기 — work/text/xstr.tsv → work/tsv/fs2_NNN.tsv (기본 50 KB, UTF-8 바이트 기준)
  순서: ①본편 캠페인(FreeSpace2.fc2 의 $Mission 순서) ②표(.tbl/.tbm) ③Templar 캠페인 ④그 밖의 미션 ⑤협동(CoOp) ⑥캠페인·메인홀 파일.
  미션 안은 보는 순서(미션 정보 → 사령부 브리핑 → 브리핑 → 목표 → 지시 → 무전 → 디브리핑 → 함선·윙).
  같은 XSTR id 는 처음 한 번만(id −1 은 같은 파일 안 같은 글만 합침).
  열: ID(X<id> | <파일>#<순번>) · 파일 · 종류 · 원문 — 따옴표 없는 TSV, 줄바꿈·탭은 \n \t 글자.
  python tools/make_tsv.py [KB=50]
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KORD = ['미션 정보', '사령부 브리핑', '브리핑', '목표', '지시', '무전', '디브리핑', '함선·윙']
MIS = os.path.join(ROOT, 'work', 'src', 'data', 'missions')


def camp(fc2):
    t = open(os.path.join(MIS, fc2), encoding='latin1').read()
    return [fc2.lower()] + [m.lower() for m in re.findall(r'(?m)^\$Mission:\s*(\S+)', t)]


def load_rows():
    return [ln.rstrip('\n').split('\t') for ln in list(open(os.path.join(ROOT, 'work', 'text', 'xstr.tsv'), encoding='utf-8'))[1:]]


def build(rows):
    """(out = [[ID, 파일, 종류, 원문]], rid = xstr.tsv 행 번호 → ID(빈 글은 None)). 빌더도 이걸로 자리를 찾는다"""
    main_c = camp('FreeSpace2.fc2'); templar = camp('Templar.fc2')

    def key(r):
        f = r[0]; b = f.split('/')[-1].lower()
        k2 = KORD.index(r[2]) if r[2] in KORD else 99
        if b in main_c: return (0, main_c.index(b), k2)
        if not b.endswith(('.fs2', '.fc2')): return (1, 0, 0)
        if b in templar: return (2, templar.index(b), k2)
        if b.startswith('coop'): return (4, 0, 0)
        if b.endswith('.fc2'): return (5, 0, 0)
        return (3, 0, 0)
    order = sorted(range(len(rows)), key=lambda n: (key(rows[n]), n))   # 같은 묶음 안은 파일 속 순서 유지
    seen = {}; out = []; neg = {}; rid_of = [None] * len(rows)
    for n in order:
        f, m, kind, i, s = rows[n]
        if not s.strip():
            continue
        i = int(i); base = f.split('/')[-1]
        k = ('id', i) if i >= 0 else ('t', base, s)
        if k in seen:
            rid_of[n] = seen[k]; continue
        if i >= 0:
            rid = 'X%d' % i
        else:
            neg[base] = neg.get(base, 0) + 1; rid = '%s#%d' % (base, neg[base])
        seen[k] = rid; rid_of[n] = rid
        out.append([rid, base, kind.strip(), s])
    return out, rid_of


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    kb = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    out, _ = build(load_rows())
    d = os.path.join(ROOT, 'work', 'tsv'); os.makedirs(d, exist_ok=True)
    head = 'ID\t파일\t종류\t원문\n'
    lim = kb * 1024; files = []; cur = head
    def flush(cur):
        p = os.path.join(d, 'fs2_%03d.tsv' % (len(files) + 1))
        open(p, 'w', encoding='utf-8', newline='').write(cur); files.append(p)
    for r in out:
        ln = '\t'.join(r) + '\n'
        if len((cur + ln).encode('utf-8')) > lim and cur != head:
            flush(cur); cur = head
        cur += ln
    if cur != head:
        flush(cur)
    for p in files:
        rs = list(open(p, encoding='utf-8'))[1:]
        print('%s %6d B %4d줄  %s … %s' % (os.path.basename(p), os.path.getsize(p), len(rs), rs[0].split('\t')[1], rs[-1].split('\t')[1]))
    print('합계 %d줄 · %d파일' % (len(out), len(files)))


if __name__ == '__main__':
    main()
