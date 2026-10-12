# -*- coding: utf-8 -*-
r"""프리스페이스 2 (FSO + Knossos) 번역 분량 조사.
  실제로 쓰이는 파일 = 우선순위 MVPS > MjnMHs > GOTYMissions > 원본(FS2) (Knossos 의 -mod 순서),
  같은 모드 안에서는 낱개 파일 > VP. 그중 글이 든 .fs2/.fc2/.tbl/.tbm 을 work/src/ 로 꺼내고
  XSTR("…", id) 를 모아 work/text/xstr.tsv · strings.tbl(#English) 를 work/text/strings.tsv 로.
  python tools/survey.py
"""
import collections, csv, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vp

KN = r'C:\Program Files (x86)\GOG Galaxy\Games\Freespace 2\Knossos.NET\FS2'
# 앞이 우선 = MVPS mod.json «mod_flag» 순서 [MVPS, GOTYMissions, MjnMHs, SCPUI] (2026-10-12 MVPS 5.0.2 업데이트, 예전 4.7.3 추출본 work/text_mvps473)
MODS = ['MVPS-5.0.2', 'GOTYMissions-1.0.3', 'MjnMHs-1.7.3', 'SCPUI-1.1.2', '.']
EXT = ('.fs2', '.fc2', '.tbl', '.tbm')
SRC = os.path.join(ROOT, 'work', 'src'); TXT = os.path.join(ROOT, 'work', 'text')


def effective():
    """{소문자 경로: (모드, 출처, 읽기 함수)}"""
    eff = {}
    for m in MODS:
        base = os.path.join(KN, m)
        cand = {}
        for vpf in sorted(glob.glob(os.path.join(base, '*.vp')), reverse=True):
            for name, o, s in vp.entries(vpf):
                if name.lower().endswith(EXT):
                    cand[name.lower()] = (m, os.path.basename(vpf), name, (vpf, o, s))
        for p in glob.glob(os.path.join(base, 'data', '**', '*'), recursive=True):
            # tables/translations/ 는 FSO 가 안 읽는 하위 폴더(SCPUI 의 다른 언어 번역 견본)
            if p.lower().endswith(EXT) and 'translations' not in p.lower().replace('\\', '/').split('/data/')[-1]:
                name = os.path.relpath(p, base).replace('\\', '/')
                cand[name.lower()] = (m, '(낱개)', name, (p, None, None))
        for k, v in cand.items():
            eff.setdefault(k, v)
    return eff


def read(src):
    p, o, s = src
    with open(p, 'rb') as f:
        if o is None:
            return f.read()
        f.seek(o); return f.read(s)


XSTR = re.compile(r'XSTR\s*\(\s*"(.*?)"\s*,\s*(-?\d+)\s*\)', re.S)


def mission_kind(sec, key):
    if sec == '#messages': return '무전'
    if sec in ('#briefing',): return '브리핑'
    if sec in ('#command briefing',): return '사령부 브리핑'
    if sec in ('#debriefing_info',): return '디브리핑'
    if sec in ('#goals',): return '목표'
    if sec in ('#events',): return '지시'
    if sec in ('#mission info',): return '미션 정보'
    if sec in ('#fiction viewer',): return '픽션'
    if sec in ('#objects', '#wings', '#players'): return '함선·윙'
    return '기타 ' + sec


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    eff = effective()
    os.makedirs(SRC, exist_ok=True); os.makedirs(TXT, exist_ok=True)
    rows = []          # 파일, 종류, id, 글
    for k in sorted(eff):
        m, vpn, name, src = eff[k]
        b = read(src)
        out = os.path.join(SRC, name.replace('/', os.sep)); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'wb').write(b)
        t = b.decode('latin1')
        if name.lower().endswith('tstrings.tbl') or name.lower().endswith('strings.tbl'):
            continue
        if name.lower().endswith('-tlc.tbm'):
            # 모듈식 번역표 «#default» = 그 모드가 새로 만든 문구(SCPUI 888xxx 등) — 표에만 있어 XSTR 로는 안 잡힘
            dm = re.search(r'(?mi)^#default\s*$', t)
            if dm:
                end = re.search(r'(?m)^#', t[dm.end():])
                sec = t[dm.end():dm.end() + end.start()] if end else t[dm.end():]
                for x in re.finditer(r'(?m)^\s*(\d+)\s*,\s*"([^"]*)"', sec):
                    rows.append((name, m, '표 ' + os.path.basename(name).lower(), int(x.group(1)), x.group(2)))
            continue
        heads = [(mm.start(), mm.group(0).strip().lower()) for mm in re.finditer(r'(?m)^#[^\r\n;]*', t)]
        for x in XSTR.finditer(t):
            sec = ''
            for pos, h in heads:
                if pos > x.start(): break
                sec = h
            if name.lower().endswith(('.fs2', '.fc2')):
                kind = ('캠페인 ' if name.lower().endswith('.fc2') else '') + mission_kind(sec, '')
            else:
                kind = '표 ' + os.path.basename(name).lower()
            rows.append((name, m, kind, int(x.group(2)), x.group(1)))
    # strings.tbl(엔진 UI 문구) — 실제 쓰이는 것
    st = [v for k, v in eff.items() if k.endswith('/strings.tbl')]
    srows = []
    if st:
        t = read(st[0][3]).decode('latin1')
        en = t[t.index('#English'):]; en = en[:en.index('#end')] if '#end' in en else en
        # 항목 = «번호, "글"» + 줄 끝 주석(; Kills) — 예전 정규식은 주석 달린 줄에서 다음 항목까지 삼켰다(2026-10-12)
        #   쉼표 빠진 항목(«1524  "&Go back"»)·주석 안 따옴표(«; short for "red"»)도 있다 → 닫는 따옴표 = 뒤에 공백·주석·줄끝만 오는 첫 «"»
        starts = list(re.finditer(r'(?m)^(\d+),?[ \t]+"', en))
        for k, x in enumerate(starts):
            chunk = en[x.end():starts[k + 1].start() if k + 1 < len(starts) else len(en)]
            end = re.search(r'"(?=[ \t]*(;[^\n]*)?\r?(\n|$))', chunk)
            srows.append((int(x.group(1)), chunk[:end.start()]))
    # 따옴표로 감싸지 않는 TSV(번역기가 "" 를 그대로 옮겨 칸이 뭉친다) — 탭·줄바꿈은 \t \n 글자로
    def esc(s): return s.replace('\r', '').replace('\t', '\\t').replace('\n', '\\n')
    with open(os.path.join(TXT, 'xstr.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('파일\t모드\t종류\tid\t원문\n')
        for r in rows:
            f.write('\t'.join([r[0], r[1], r[2], str(r[3]), esc(r[4])]) + '\n')
    with open(os.path.join(TXT, 'strings.tsv'), 'w', encoding='utf-8', newline='') as f:
        f.write('id\t원문\n')
        for i, s in srows:
            f.write('%d\t%s\n' % (i, esc(s)))
    # 집계 — 같은 id(≥0)는 한 번, id -1 은 글 단위 중복 제거
    def wc(s): return len(s.split())
    seen = set(); agg = collections.OrderedDict()
    for name, m, kind, i, s in rows:
        if not s.strip(): continue
        key = ('id', i) if i >= 0 else ('t', s)
        if key in seen: continue
        seen.add(key)
        a = agg.setdefault(kind, [0, 0, 0]); a[0] += 1; a[1] += wc(s); a[2] += len(s)
    tot = [0, 0, 0]
    print('%-26s %7s %8s %9s' % ('종류', '문장', '단어', '글자'))
    for kind, a in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        print('%-26s %7d %8d %9d' % (kind, *a)); tot = [x + y for x, y in zip(tot, a)]
    print('%-26s %7d %8d %9d' % ('XSTR 합계(중복 제거)', *tot))
    sa = [len(srows), sum(wc(s) for _, s in srows), sum(len(s) for _, s in srows)]
    print('%-26s %7d %8d %9d' % ('strings.tbl 엔진 UI', *sa))
    neg = sum(1 for r in rows if r[3] < 0)
    print('XSTR id -1(번역표로 못 바꾸는 글) %d개' % neg)
    ms = collections.Counter(r[1] for r in rows)
    print('출처 모드별 XSTR 수', dict(ms))
    print('미션 파일 %d · 캠페인 %d · 표 %d' % tuple(sum(1 for k in eff if k.endswith(e)) for e in ('.fs2', '.fc2', ('.tbl'))) )


if __name__ == '__main__':
    main()
