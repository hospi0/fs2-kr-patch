# 프리스페이스 2 한글 패치

**내려받기: [최신 v0.8 릴리즈](https://github.com/hospi0/fs2-kr-patch/releases/latest)** — `FS2KR_v0.8.zip`

FreeSpace 2 (PC, GOG/스팀) 를 [Knossos.NET](https://fsnebula.org/knossos/) + MediaVPs 5.0.2 로 즐길 때 쓰는 한글 모드(FS2KR)입니다.
미션 무전·브리핑·디브리핑·목표·기술실 설명·메뉴(SCPUI 포함)를 한글로 바꿉니다. 무전 음성은 영어 그대로, 화면 메시지가 한글로 나옵니다.

## 필요한 것
- FreeSpace 2 + Knossos.NET
- Knossos 모드 **MediaVPs 5.0.2** (GOTYMissions · MjnMHs · SCPUI 는 함께 설치됨)
- FSO 엔진 25.0.0 이상 (26.0.1 에서 확인)

## 설치
1. 릴리즈 zip 안의 `FS2KR-0.8` 폴더를 Knossos 라이브러리의 `FS2` 폴더에 넣습니다 (`...\Knossos.NET\FS2\FS2KR-0.8\mod.json`).
2. Knossos.NET 에서 **Reload Data** → Play 목록의 «FreeSpace 2 한글 패치» 로 실행합니다.

자세한 내용은 zip 안 `설치방법.txt` 를 보세요.

## 이 저장소
- `data/` 번역(미션·표 `fs2_ko.tsv`, 화면 문구 `strings_ko.tsv`·`engine_ko.tsv`, SCPUI 스크립트 문구 `scpui_lua_ko.tsv`), 용어집·표기 통일표
- `tools/` 추출·빌드 도구 (`build_mod.py`, `make_dist.py`)
- `docs/` 작업 기록

게임 원본 파일·MediaVPs 자료는 들어 있지 않습니다.

## 외부 자료
- 나눔고딕 (c) NAVER Corporation — SIL Open Font License 1.1
- SCPUI 1.1.2 스크립트 사본(한글 문구·한글 단축키 수정) — CC BY-NC-SA 4.0, 원작 SCPUI 제작진

제작: hospi
