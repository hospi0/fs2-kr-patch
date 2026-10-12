# -*- coding: utf-8 -*-
r"""받은 번역 + 용어집(data/glossary.tsv) → data/fs2_ko.tsv (ID·파일·종류·원문·번역) + work/glossary_changes.tsv(바뀐 줄 전후)
  · 각 용어는 «원문에 그 낱말이 있는 줄»에만 적용(«하지 마라» → Mara 같은 사고 방지).
  · 한글: 번역에 남은 영어 원어와 «다른 표기» → 표기.  영어: «다른 표기»(한글 음역, 뒤 «호/급» 포함) → 원어.
  · 한글 자리는 뒤가 «조사 묶음 + 한글 아닌 글자»일 때만 바꾼다(낱말 일부 보호). 첫 조사는 읽기 받침에 맞춘다.
  · 긴 원어부터(Gamma Draconis → Draconis). 남은 «Gamma 드라코니스» 꼴도 표기로 합친다.
  python tools/apply_glossary.py <번역 폴더> [--write]
"""
import collections, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_tr

PAIRS = {'은': ('은', '는'), '는': ('은', '는'), '이': ('이', '가'), '가': ('이', '가'), '을': ('을', '를'), '를': ('을', '를'),
         '과': ('과', '와'), '와': ('과', '와'), '으로': ('으로', '로'), '로': ('으로', '로'), '이나': ('이나', '나'), '나': ('이나', '나'),
         '이랑': ('이랑', '랑'), '랑': ('이랑', '랑'), '이라는': ('이라는', '라는'), '라는': ('이라는', '라는'), '이란': ('이란', '란'), '란': ('이란', '란'),
         '이다': ('이다', '다'), '이었': ('이었', '였'), '였': ('이었', '였'), '으로서': ('으로서', '로서'), '로서': ('으로서', '로서'),
         '으로부터': ('으로부터', '로부터'), '로부터': ('으로부터', '로부터')}
OTHER = ['의', '에서', '에게', '에', '도', '만', '까지', '부터', '처럼', '보다', '께서', '께', '조차', '마저', '측', '쪽', '들', '함', '형', '급', '호', '와의', '과의', '에는', '에서는', '에도', '에서도']
JOSA = sorted(set(PAIRS) | set(OTHER), key=len, reverse=True)
JRE = '(?:%s)' % '|'.join(map(re.escape, JOSA))
TAIL = re.compile(r'((?:%s){0,3})(?![가-힣])' % JRE)


def batchim(word):
    h = [c for c in word if '가' <= c <= '힣']
    if not h:
        return None
    j = (ord(h[-1]) - 0xAC00) % 28
    return None if j == 0 else ('ㄹ' if j == 8 else 'O')


def fix_first(js, reading):
    for a in JOSA:
        if js.startswith(a):
            if a in PAIRS:
                hb, nb = PAIRS[a]
                b = batchim(reading)
                want = hb if b == 'O' or (b == 'ㄹ' and hb not in ('으로', '으로서', '으로부터')) else nb
                return want + js[len(a):]
            return js
    return js


def load_spelling():
    """data/spelling.tsv (변경 전 → 변경 후) — 한국어 표기 통일(타기팅→타게팅 등). 받침이 같은 것만 넣을 것(조사 안 바꿈)"""
    p = os.path.join(ROOT, 'data', 'spelling.tsv')
    if not os.path.exists(p):
        return []
    out = []
    for ln in list(open(p, encoding='utf-8'))[1:]:
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 2 and c[0]:
            if batchim(c[0]) != batchim(c[1]):
                sys.exit('⛔spelling: 받침이 달라 조사가 어긋남 %s→%s' % (c[0], c[1]))
            out.append((c[0], c[1]))
    return out


SPELL = None


def spell(t):
    global SPELL
    if SPELL is None:
        SPELL = load_spelling()
    for a, b in SPELL:
        t = t.replace(a, b)
    return t


def load_glossary():
    g = []
    for ln in list(open(os.path.join(ROOT, 'data', 'glossary.tsv'), encoding='utf-8'))[1:]:
        c = ln.rstrip('\n').split('\t')
        if len(c) < 3 or not c[0]:
            continue
        var = [v.strip() for v in (c[3].split(',') if len(c) > 3 else []) if v.strip()]
        g.append((c[0], c[1], c[2], var))
    g.sort(key=lambda x: -len(x[0]))
    return g


def sub(k, head, rep, reading, hangul_head):
    """head(정규식) 자리를 rep 로, 뒤 조사 묶음의 첫 조사를 reading 받침에 맞춤"""
    out = []; pos = 0
    for m in re.finditer(head, k):
        if m.start() < pos:
            continue
        t = TAIL.match(k, m.end())
        if hangul_head and not t:
            continue                       # 뒤가 조사 아닌 한글 → 다른 낱말의 일부
        js = t.group(1) if t else ''
        out.append(k[pos:m.start()]); out.append(rep); out.append(fix_first(js, reading))
        pos = m.end() + len(js)
    out.append(k[pos:])
    return ''.join(out)


def apply(src, k, g, hits):
    for word, kind, ko, var in g:
        # 줄바꿈 표기 «\n»(역슬래시+n) 바로 뒤도 낱말 시작으로 본다
        if not re.search(r'(?:(?<=\\n)|(?<![A-Za-z]))%s(?![A-Za-z])' % re.escape(word), src):
            continue
        before = k
        if kind == '한글':
            k = sub(k, r'(?:(?<=\\n)|(?<![A-Za-z$]))%s(?![A-Za-z])' % re.escape(word), ko, ko, False)
            for v in var:
                k = sub(k, r'(?<![가-힣])%s' % re.escape(v), ko, ko, True)
            if ' ' in ko:                  # «Gamma 드라코니스» → «감마 드라코니스»
                k = re.sub(r'(?<![A-Za-z])%s %s' % (re.escape(word.split(' ')[0]), re.escape(ko.split(' ', 1)[1])), ko, k)
        else:
            for v in var:
                # 항성계 이름의 앞말(감마 드라코니스·알파 센타우리 …, 사이에 색 태그가 껴도)은 윙 이름이 아니다
                k = sub(k, r'(?<![가-힣])%s(?:호(?![가-힣]))?(?!(?:\s*\$[a-zA-Z])?\s*(?:드라코니스|페가시|센타우리|아퀼라|세르펜티스))' % re.escape(v), word, v, True)   # «아키텐호» → Aquitaine, «급» 은 남김
        if k != before:
            hits[word] += 1
    return k


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    tr = check_tr.load(sys.argv[1])
    g = load_glossary()
    # 말투 손질(data/tone_fix.tsv, 사람이 쓴 줄) — 용어집 다음에 ID 로 덮어쓴다
    tone = {}
    p = os.path.join(ROOT, 'data', 'tone_fix.tsv')
    if os.path.exists(p):
        for ln in list(open(p, encoding='utf-8'))[1:]:
            c = ln.rstrip('\n').split('\t')
            if c[0] not in tr:
                sys.exit('⛔tone_fix: 없는 ID %s' % c[0])
            tone[c[0]] = c[1]
    hits = collections.Counter(); changes = []; rows = []
    for i, (f, n, c) in tr.items():
        src, k = c[3], c[4]
        k2 = apply(src, k, g, hits)
        if i in tone:
            k2 = tone[i]; hits['(말투 손질)'] += 1
        k3 = spell(k2)                     # 표기 통일(data/spelling.tsv) — 맨 마지막
        if k3 != k2:
            hits['(표기 통일)'] += 1; k2 = k3
        if k2 != k:
            changes.append((i, c[1], src, k, k2))
        rows.append((i, c[1], c[2], src, k2))
    with open(os.path.join(ROOT, 'work', 'glossary_changes.tsv'), 'w', encoding='utf-8', newline='') as o:
        o.write('ID\t파일\t원문\t받은 번역\t고친 번역\n')
        for r in changes:
            o.write('\t'.join(r) + '\n')
    print('바뀐 줄 %d / %d' % (len(changes), len(rows)))
    print('  ' + ' · '.join('%s %d' % kv for kv in hits.most_common()))
    if '--write' in sys.argv:
        with open(os.path.join(ROOT, 'data', 'fs2_ko.tsv'), 'w', encoding='utf-8', newline='') as o:
            o.write('ID\t파일\t종류\t원문\t번역\n')
            for r in rows:
                o.write('\t'.join(r) + '\n')
        print('→ data/fs2_ko.tsv')


if __name__ == '__main__':
    main()
