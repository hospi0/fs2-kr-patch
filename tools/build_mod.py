# -*- coding: utf-8 -*-
r"""프리스페이스 2 한글 모드 빌드 → build/FS2KR-<VER>/ (Knossos.NET 모드 폴더 — MVPS 에 얹음)
  방식(FSO 24 소스 확인, docs/00 «한글 모드 구조»):
   · korean-mod.tbm  $Unicode mode: YES + $Use tabled strings for the default language: YES
       → 영어(기본) 상태에서도 미션·표 XSTR(id≥0)을 tstrings «#default» 에서 찾는다.
   · korean-tlc.tbm  #default — XSTR id≥0 번역(data/fs2_ko.tsv). 줄바꿈은 실제 줄바꿈.
   · korean-lcl.tbm  #English — 엔진 화면 문구 strings.tbl 번역(data/strings_ko.tsv). 줄바꿈은 \n 표기.
   · fonts.tbl + data/fonts/NanumGothic*.ttf — 유니코드 모드는 비트맵 글꼴을 건너뛰므로 TTF 3개(font01·02·03).
   · id −1 글과 «번호 충돌» id(1520·99021~99026)는 표로 못 바꾸므로, 그 파일 사본에서 XSTR 글을 직접 바꿔 넣는다.
  검사: 표 한 줄 4,095 B 이하 · 번역에 큰따옴표 없음 · 빈 번역 · 파일 안 XSTR 개수가 추출 때와 같은지.
  python tools/build_mod.py [VER=0.1]
"""
import collections, glob, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_tsv
import apply_glossary   # 표기 통일 spell()

VER = sys.argv[1] if len(sys.argv) > 1 else '0.1'
MODID = 'FS2KR'
OUT = os.path.join(ROOT, 'build', '%s-%s' % (MODID, VER))
SRC = os.path.join(ROOT, 'work', 'src')
FONTDIR = r'C:\claude\utils\font\nanum-gothic'
XSTR = re.compile(r'XSTR\s*\(\s*"(.*?)"\s*,\s*(-?\d+)\s*\)', re.S)
SPECIAL = {1520, 99021, 99022, 99023, 99024, 99025, 99026}    # 같은 번호에 다른 글 — 파일에서 직접 바꿈
# 메인홀 모드 번역표 #default 에 99051 이 두 번(«fleet locations in the system» 먼저 → FSO 는 먼저 것) — 번역표엔 그 뜻으로,
# 크레디트 파일(mainhall-crd.tbm)의 같은 번호 줄은 글을 직접 바꾸고 번호를 −1 로(번역표를 안 타게). 2026-10-12 MVPS 5.0.2
TLC_OVERRIDE = {99051: '항성계의 함대 위치'}
INLINE_NOID = {('mainhall-crd.tbm', 99051)}
# MVPS 5.0.2 mod.json cmdline 그대로(⛔-reparse_mainhall 넣지 말 것 — 켜면 시작 때 옛 메인홀, 하스피 2026-10-12)
# SCPUI(libRocket) 에 실을 글자 범위 — 번역 글자가 밖이면 빌드 오류(그 화면에서 빈칸으로 나온다)
CHARSET = [(0x20, 0x24F), (0x2000, 0x206F), (0x2190, 0x21FF), (0x2460, 0x24FF), (0x25A0, 0x25FF), (0x3000, 0x303F),
           (0x3131, 0x318E), (0xAC00, 0xD7A3), (0xFF01, 0xFF5E),
           (0x5C0D, 0x5C0D), (0x91CD, 0x91CD)]   # 번역 속 한자 對·重(«대(對)전투기»·«중(重)강습») — 한자 블록 통째는 글리프 텍스처가 커짐
SCPUI_DIR = r'C:\Program Files (x86)\GOG Galaxy\Games\Freespace 2\Knossos.NET\FS2\SCPUI-1.1.2'   # 고친 lua 사본의 원본
# MVPS 5.0.2 mod.json 의 권장 패키지(Knossos 기본 설치분) · MjnMHs 권장 메인홀
MVPS_PKGS =['MV_Music', 'MV_CB_ANI_1', 'MV_CB_ANI_2', 'MV_CB_ANI_3', 'MV_Mainhalls', 'MV_SCPUI']
MJN_PKGS = ['galatea', 'bastion', 'krios', 'intrepid', 'soyakaze', 'wayfarer', 'lucifer', 'centaur', 'aquitaine', 'megiddo', 'amanu', 'cockpit']
MVPS_CMD = '-soft_particles -enable_shadows -dualscanlines -targetinfo -rearm_timer -3dwarp -warp_flash -aa -ship_choice_3d -weapon_choice_3d -ambient_factor 80 -spec_point 0.3 -spec_static 1.2 -spec_tube 0.3 -bloom_intensity 15 -fov 0.6'


def die(m):
    sys.exit('⛔' + m)


def unesc(s):
    return s.replace('\\t', '\t').replace('\\n', '\n')


def fix_mojibake(s):
    """UTF-8 원본을 라틴-1로 읽어 생긴 «Ã¨» 꼴만 되돌림(CrÃ¨me → Crème)"""
    def f(m):
        try:
            return m.group(0).encode('latin1').decode('utf-8')
        except UnicodeError:
            return m.group(0)
    return re.sub(r'[\xc2-\xf4][\x80-\xbf]+', f, s)


def read_text(p):
    b = open(p, 'rb').read()
    try:
        return b.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        return b.decode('latin1'), 'latin1'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    # 번역 찾기 = «XSTR 번호 + 원문 같음» 또는 «파일 + 원문» — ID(파일#순번)로 찾지 않는다.
    # (2026-10-12 MVPS 5.0.2 업데이트로 번호 없는 문장 순번이 밀림 → 예전 번역을 그대로 따라오게)
    byX = {}; byFT = {}
    for p in ('fs2_ko.tsv', 'ko_add.tsv'):          # ko_add = 업데이트 뒤 새로·다시 번역한 줄(뒤가 우선)
        fp = os.path.join(ROOT, 'data', p)
        if not os.path.exists(fp):
            continue
        for ln in list(open(fp, encoding='utf-8'))[1:]:
            c = ln.rstrip('\n').split('\t')
            rid, base, s, t = c[0], c[1], fix_mojibake(c[3]), fix_mojibake(c[4])
            m = re.fullmatch(r'X(\d+)', rid)
            if m:
                byX[int(m.group(1))] = (s, t)
            byFT[(base.lower(), s)] = t
    SKIP = {'options.tbl'}                           # SCPUI 옵션 표의 예제 항목(게임에 안 나옴) — 영어로 둠
    rows = make_tsv.load_rows()
    out_rows, rid_of = make_tsv.build(rows)
    ko = {}; miss = []; changed = []
    for rid, base, kind, s in out_rows:
        s = fix_mojibake(s)
        m = re.fullmatch(r'X(\d+)', rid)
        if m and int(m.group(1)) in byX:
            s0, t = byX[int(m.group(1))]
            if s0 == s:
                ko[rid] = (s, t); continue
            if (base.lower(), s) in byFT:
                ko[rid] = (s, byFT[(base.lower(), s)]); continue
            changed.append(rid); continue
        if (base.lower(), s) in byFT:
            ko[rid] = (s, byFT[(base.lower(), s)]); continue
        if base.lower() in SKIP:
            continue
        miss.append((rid, base, kind, s))
    if miss or changed:
        with open(os.path.join(ROOT, 'work', 'ko_missing.tsv'), 'w', encoding='utf-8', newline='') as w:
            w.write('ID\t파일\t종류\t원문\t번역\n')
            for rid, base, kind, s in miss:
                w.write('%s\t%s\t%s\t%s\t\n' % (rid, base, kind, s))
            for rid in changed:
                r = [x for x in out_rows if x[0] == rid][0]
                w.write('%s\t%s\t%s(원문 바뀜)\t%s\t\n' % (rid, r[1], r[2], r[3]))
        die('번역 없는 줄 %d · 원문 바뀐 번호 %d → work/ko_missing.tsv 를 번역해 data/ko_add.tsv 로' % (len(miss), len(changed)))
    errs = []
    for k, (s, t) in ko.items():
        if not t.strip():
            errs.append('빈 번역 %s' % k)
        if '"' in t:
            errs.append('큰따옴표 %s' % k)
    if os.path.exists(OUT):
        for x in os.listdir(OUT):          # 폴더 자체는 남김(다른 프로세스가 현재 폴더로 잡고 있으면 rmdir 실패)
            q = os.path.join(OUT, x)
            shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
    tdir = os.path.join(OUT, 'data', 'tables'); os.makedirs(tdir)
    # ① 설정
    open(os.path.join(tdir, 'korean-mod.tbm'), 'w', encoding='utf-8', newline='\n').write(
        '; 프리스페이스 2 한글 패치 — 유니코드 + 기본 언어도 번역표(tstrings #default) 사용\n'
        '#GAME SETTINGS\n$Unicode mode: YES\n\n#LOCALIZATION SETTINGS\n$Use tabled strings for the default language: YES\n\n#END\n')
    # ② 글꼴
    fdir = os.path.join(OUT, 'data', 'fonts'); os.makedirs(fdir)
    for f in ('NanumGothic.ttf', 'NanumGothicBold.ttf'):
        shutil.copy(os.path.join(FONTDIR, f), fdir)
    # MVPS 5.0.2 의 fonts.tbl(BankGothic, font01·02·03·fontbighud)을 같은 구성으로 덮어씀 — fontbighud 를 빼면 고해상도 HUD 글꼴이 없어진다.
    # FSO ≥25(MVPS 5 요구)라 +Auto Size·+Can Scale 사용 가능(⛔24.2 엔 없음 — 2026-10-12 «Missing required token [#End]»).
    open(os.path.join(tdir, 'fonts.tbl'), 'w', encoding='utf-8', newline='\n').write(
        '; 한글 TTF(나눔고딕, SIL OFL) — MVPS 5.0.2 fonts.tbl 과 같은 이름·크기 구성\n#Fonts\n'
        '$TrueType: NanumGothic.ttf\n\t+Name: font01\n\t+Size: 12\n\t+Auto Size: true\n\t+Can Scale: true\n\n'
        '$TrueType: NanumGothicBold.ttf\n\t+Name: font02\n\t+Size: 20\n\n'
        '$TrueType: NanumGothic.ttf\n\t+Name: font03\n\t+Size: 12\n\n'
        ';; 고해상도 HUD 확대용(MVPS)\n$TrueType: NanumGothic.ttf\n\t+Name: fontbighud\n\t+Size: 16\n\t+Top offset: -3\n\n#End\n')
    # SCPUI 화면 기본 글꼴 — SCPUI 는 모드가 custom.rcss 를 갈아 끼워 바꾸라고 설계(원래 BankGothic Md BT = 한글 없음)
    cdir = os.path.join(OUT, 'data', 'interface', 'css'); os.makedirs(cdir)
    open(os.path.join(cdir, 'custom.rcss'), 'w', encoding='utf-8', newline='\n').write(
        '/* FreeSpace 2 한글 패치 — SCPUI 기본 글꼴을 나눔고딕으로(SCPUI-1.1.2 custom.rcss 대체) */\n\n'
        # ★SCPUI common.rcss 가 body 에 font-charset: U+0020-024F(라틴만) — libRocket 은 범위 밖 글리프를 안 실어 한글이 빈칸
        #   (2026-10-12 실기: 옵션 화면 이름표가 «: 1.00» 만). custom.rcss 가 common 뒤에 링크되므로 여기서 덮는다.
        'body\n{\n\tfont-family: NanumGothic;\n\tfont-weight: normal;\n\tfont-style: normal;\n'
        '\tfont-charset: ' + ', '.join('U+%04X-%04X' % r for r in CHARSET) + ';\n}\n')
    # ③ 미션·표 XSTR(id≥0) → korean-tlc.tbm
    tl = ['; 미션·표 XSTR 번역(data/fs2_ko.tsv) — tools/build_mod.py 가 만듦', '#default']
    n_tlc = 0
    for rid, (s, t) in ko.items():
        m = re.fullmatch(r'X(\d+)', rid)
        if not m or int(m.group(1)) in SPECIAL:
            continue
        txt = unesc(t)
        if len(txt.encode('utf-8')) > 4095:
            errs.append('표 한 줄 4KB 넘음 %s' % rid)
        if int(m.group(1)) in TLC_OVERRIDE:
            txt = TLC_OVERRIDE[int(m.group(1))]
        tl.append('%s, "%s"' % (m.group(1), txt)); n_tlc += 1
    tl.append('#end')
    open(os.path.join(tdir, 'korean-tlc.tbm'), 'w', encoding='utf-8', newline='\n').write('\n'.join(tl) + '\n')
    # ④ 엔진 화면 문구 → korean-lcl.tbm (#English 항목을 모듈식으로 덮어씀)
    UIOFF = {}
    p_off = os.path.join(ROOT, 'data', 'ui_offsets.tsv')
    if os.path.exists(p_off):
        for ln in list(open(p_off, encoding='utf-8'))[1:]:
            c = ln.rstrip('\n').split('\t')
            UIOFF[int(c[0])] = (int(c[1]), int(c[2]))
    ll = ['; 엔진 화면 문구(strings.tbl) 번역(data/strings_ko.tsv) — tools/build_mod.py 가 만듦', '#English']
    n_lcl = 0
    for ln in list(open(os.path.join(ROOT, 'data', 'strings_ko.tsv'), encoding='utf-8'))[1:]:
        i, s, t = ln.rstrip('\n').split('\t')
        if not t.strip():
            errs.append('빈 화면 문구 %s' % i); continue
        if '"' in t:
            errs.append('화면 문구 큰따옴표 %s' % i); continue
        o = UIOFF.get(int(i))                # 메뉴 글자 x 보정(640·1024) — data/ui_offsets.tsv(tools/ui_offsets.py)
        tail = ' %d %d' % o if o and o != (0, 0) else ''
        ll.append('%s, "%s"%s' % (i, apply_glossary.spell(t).replace('\\t', '\t'), tail)); n_lcl += 1
    # 엔진 코드에만 있고 strings.tbl #English 에 없는 문구(POPUP 예/아니오 505·506 등, tools/engine_missing.py) — data/engine_ko.tsv
    have = {int(x.split(',')[0]) for x in ll[2:] if x[:1].isdigit()}
    n_eng = 0
    for ln in list(open(os.path.join(ROOT, 'data', 'engine_ko.tsv'), encoding='utf-8'))[1:]:
        i, s, t = ln.rstrip('\n').split('\t')
        if int(i) in have:
            errs.append('engine_ko 번호가 strings 와 겹침 %s' % i); continue
        if '"' in t:
            errs.append('engine_ko 큰따옴표 %s' % i); continue
        ll.append('%s, "%s"' % (i, apply_glossary.spell(t))); n_eng += 1
    ll.append('#end')
    open(os.path.join(tdir, 'korean-lcl.tbm'), 'w', encoding='utf-8', newline='\n').write('\n'.join(ll) + '\n')
    # ⑤ id −1 · 번호 충돌 글 → 파일 사본에서 직접 바꿈
    byfile = collections.defaultdict(list)          # 파일 → [(파일 안 순번, 행)]
    cnt = collections.Counter()
    for n, r in enumerate(rows):
        f = r[0]
        byfile[f].append((cnt[f], n)); cnt[f] += 1
    patched = []
    for f, lst in byfile.items():
        if f.lower().endswith('-tlc.tbm'):
            continue                       # 번역표에서 뽑은 줄은 korean-tlc 로 처리(파일 직접 고치기 대상 아님)
        need = [(k, n) for k, n in lst if rid_of[n] and rid_of[n] in ko and (int(rows[n][3]) < 0 or int(rows[n][3]) in SPECIAL or (f.split('/')[-1].lower(), int(rows[n][3])) in INLINE_NOID)]
        if not need:
            continue
        p = os.path.join(SRC, f.replace('/', os.sep))
        text, enc = read_text(p)
        ms = list(XSTR.finditer(text))
        if len(ms) != len(lst):
            die('%s: XSTR %d개 ≠ 추출 때 %d개' % (f, len(ms), len(lst)))
        rep = {}
        for k, n in need:
            rid = rid_of[n]; s0, t = ko[rid]
            src = fix_mojibake(rows[n][4]) if enc == 'utf-8' else rows[n][4]
            raw = ms[k].group(1)
            orig = raw.replace('\r', '')            # 추출본은 \r 를 지웠다
            crlf = '\r\n' in raw
            def put(x):
                return x.replace('\n', '\r\n') if crlf else x
            if unesc(src) != orig and unesc(rows[n][4]) != orig:
                die('%s #%d: 원문 대조 실패' % (f, k))
            if unesc(rows[n][4]) != unesc(ko[rid][0]) and fix_mojibake(unesc(rows[n][4])) != unesc(s0):
                # 번호 충돌: 번역한 원문과 글이 다름 — 숫자만 다르면 숫자를 맞춰 넣고, 아니면 영어 그대로 둠
                a, b = unesc(s0), unesc(rows[n][4])
                if re.sub(r'\d', '#', a) == re.sub(r'\d', '#', b) and re.findall(r'\d+', a) != re.findall(r'\d+', b):
                    da, db = re.findall(r'\d+', a), re.findall(r'\d+', b); tt = unesc(t)
                    for x, y in zip(da, db):
                        if x != y:
                            tt = tt.replace(x, y)
                    rep[k] = put(tt)
                continue
            rep[k] = put(unesc(t))
        if not rep:
            continue
        outt = []; pos = 0
        for k, m in enumerate(ms):
            if k in rep:
                outt.append(text[pos:m.start(1)]); outt.append(rep[k]); pos = m.end(1)
        outt.append(text[pos:])
        dst = os.path.join(OUT, f.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        body = ''.join(outt)
        for (fb, xid) in INLINE_NOID:
            if f.split('/')[-1].lower() == fb:
                body = re.sub(r'(XSTR\s*\(\s*"[^"]*"\s*,\s*)%d(\s*\))' % xid, r'\g<1>-1\g<2>', body)   # 번호만 −1 로
        open(dst, 'w', encoding='utf-8', newline='').write(body)
        patched.append((f, len(rep)))
    # ⑤' 메인홀 «+Door description:» (XSTR 없는 평문 — MjnMHs -reparse_mainhall 이 옵션 다녀오면 다시 읽어 영어로 돌아감, 2026-10-12)
    hall = {}
    for ln in list(open(os.path.join(ROOT, 'data', 'hall_ko.tsv'), encoding='utf-8'))[1:]:
        c = ln.rstrip('\n').split('\t'); hall[c[0]] = c[1]
    n_hall = 0; hall_files = 0; hall_left = set()
    for root_, _, fs in os.walk(os.path.join(SRC, 'data', 'tables')):
        for fn in fs:
            if not fn.lower().endswith(('-hall.tbm', 'mainhall.tbl')):
                continue
            rel = os.path.relpath(os.path.join(root_, fn), SRC)
            dst = os.path.join(OUT, rel)
            text, enc = read_text(dst if os.path.exists(dst) else os.path.join(root_, fn))
            lines = text.split('\n'); ch = 0
            for k, l in enumerate(lines):
                m = re.match(r'(\s*\+Door description:\s*)(.*?)(\s*)$', l)
                if not m or m.group(2).startswith('XSTR'):
                    continue
                if m.group(2) in hall:
                    lines[k] = m.group(1) + hall[m.group(2)] + m.group(3); ch += 1
                else:
                    hall_left.add(m.group(2))
            if ch:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
                n_hall += ch; hall_files += 1
    if hall_left:
        errs.append('메인홀 안내문 번역 없음: %s' % sorted(hall_left))
    print('엔진 문구 %d줄 · 메인홀 안내문 %d곳(%d파일)' % (n_eng, n_hall, hall_files))
    # ⑤-2 SCPUI 스크립트에 영어로 박힌 문구·한글 단축키 버그 → 고친 사본(data/scpui_lua_ko.tsv). 우리 모드가 -mod 맨 앞이라 덮어씀.
    #   lib_dialogs: 버튼 단축키 = 글 첫 «바이트» → 한글이면 반 토막 글자가 되어 «예/아니오» 버튼 글이 사라졌다(2026-10-12)
    scpui_src = os.path.join(SCPUI_DIR, 'data', 'scripts')
    sdir = os.path.join(OUT, 'data', 'scripts'); os.makedirs(sdir)
    lua = {}
    for ln in list(open(os.path.join(ROOT, 'data', 'scpui_lua_ko.tsv'), encoding='utf-8'))[1:]:
        f, a, b = ln.rstrip('\n').split('\t')
        a, b = a.replace('\\n', '\n'), b.replace('\\n', '\n')
        if f not in lua:
            lua[f] = open(os.path.join(scpui_src, f), encoding='utf-8', newline='').read().replace('\r\n', '\n')
        if a not in lua[f]:
            errs.append('SCPUI %s: 원문 못 찾음 %r' % (f, a[:60])); continue
        lua[f] = lua[f].replace(a, b)
    for f, t in lua.items():
        open(os.path.join(sdir, f), 'w', encoding='utf-8', newline='\n').write(t)
    # ⑥ mod.json (Knossos.NET)
    mj = {
        'mod_source': 'local', 'installed': True, 'id': MODID, 'title': 'FreeSpace 2 한글 패치', 'type': 'mod', 'parent': 'FS2',
        'version': VER + '.0', 'private': False, 'stability': None,
        'description': 'FreeSpace 2 (MediaVPs) 한글 패치 — 미션·브리핑·무전·표·화면 문구',
        'notes': '', 'logo': None, 'tile': None, 'banner': None, 'release_thread': None, 'videos': [], 'screenshots': [], 'attachments': [],
        'first_release': '2026-10-12', 'last_update': '2026-10-12', 'cmdline': MVPS_CMD,
        'mod_flag': [MODID, 'MVPS', 'GOTYMissions', 'MjnMHs', 'SCPUI'], 'dev_mode': False, 'custom_build': None, 'owners': ['hospi'],
        'packages': [{'name': 'korean', 'notes': '', 'status': 'required',
                      # MVPS 5 는 SCPUI·MjnMHs 를 «권장 패키지»(MV_SCPUI·MV_Mainhalls)의 의존으로만 건다 — packages [] 면 필수만 따라와
                      # -mod 에서 SCPUI·MjnMHs 가 빠진다(2026-10-12 «우리껀 4.7 화면»). 권장 패키지를 적고 두 모드도 직접 의존.
                      'dependencies': [{'id': 'MVPS', 'version': '>=5.0.2', 'packages': MVPS_PKGS},
                                       {'id': 'SCPUI', 'version': '>=1.1.1', 'packages': []},
                                       {'id': 'MjnMHs', 'version': '>=1.7.3', 'packages': MJN_PKGS},
                                       {'id': 'FSO', 'version': '>=25.0.0', 'packages': []}],
                      'environment': None, 'folder': 'korean', 'is_vp': False, 'files': [], 'filelist': [], 'executables': [],
                      'check_notes': None, 'isEnabled': True}]}
    json.dump(mj, open(os.path.join(OUT, 'mod.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    shutil.copy(os.path.join(FONTDIR, '..', 'nanum-gothic', 'NanumGothic.ttf'), os.path.join(fdir, 'NanumGothic.ttf'))
    open(os.path.join(OUT, 'NanumGothic_OFL.txt'), 'w', encoding='utf-8').write(
        'NanumGothic (c) NAVER Corporation — SIL Open Font License 1.1 (https://openfontlicense.org)\n')
    # 무기 +Description 한 줄은 «바이트» 50 미만(weapons.cpp WEAPON_DESC_MAX_LENGTH — 넘치면 경고, 한글 3바이트라 16자 안팎)
    tl = {int(m.group(1)): m.group(2) for m in re.finditer(r'(?ms)^(\d+), "(.*?)"(?=\s*$)',
                                                              open(os.path.join(tdir, 'korean-tlc.tbm'), encoding='utf-8').read())}
    for wf in glob.glob(os.path.join(SRC, '**', '*-wep.tbm'), recursive=True) + glob.glob(os.path.join(SRC, '**', 'weapons.tbl'), recursive=True):
        for m in re.finditer(r'\+Description:\s*XSTR\(\s*"(.*?)"\s*,\s*(-?\d+)\s*\)', open(wf, encoding='latin1').read(), re.S):
            k = tl.get(int(m.group(2)))
            for n, l in enumerate((k or '').replace('\\n', '\n').split('\n'), 1):
                if len(l.encode('utf-8')) >= 50:
                    errs.append('무기 설명 %s 줄 %d = %d바이트(50 미만이어야): %s' % (m.group(2), n, len(l.encode('utf-8')), l))
    for fn in ('korean-lcl.tbm', 'korean-tlc.tbm'):
        for k, ln in enumerate(open(os.path.join(tdir, fn), encoding='utf-8'), 1):
            for ch in ln:
                if ord(ch) >= 0x20 and not any(a <= ord(ch) <= b for a, b in CHARSET):
                    errs.append('%s:%d 글자 범위 밖 %r(U+%04X) — SCPUI 화면에서 빈칸' % (fn, k, ch, ord(ch)))
    if errs:
        print('\n'.join(errs[:30])); die('검사 오류 %d건' % len(errs))
    print('→ %s' % OUT)
    print('번역표 korean-tlc %d줄 · 화면 문구 korean-lcl %d줄 · 직접 바꾼 파일 %d개(%d곳)' % (n_tlc, n_lcl, len(patched), sum(n for _, n in patched)))


if __name__ == '__main__':
    main()
