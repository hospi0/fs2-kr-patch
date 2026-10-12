# -*- coding: utf-8 -*-
r"""배포판 → dist/FS2KR_v<VER>/ (모드 폴더 FS2KR-<VER> + 설치방법.txt) + 같은 이름 .zip
  python tools/make_dist.py 0.8
"""
import hashlib, os, shutil, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ver = sys.argv[1]
    r = subprocess.run([sys.executable, os.path.join(HERE, 'build_mod.py'), ver], cwd=ROOT)
    if r.returncode:
        sys.exit('빌드 실패')
    src = os.path.join(ROOT, 'build', 'FS2KR-%s' % ver)
    name = 'FS2KR_v%s' % ver
    out = os.path.join(ROOT, 'dist', name)
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(src, os.path.join(out, 'FS2KR-%s' % ver))
    readme = open(os.path.join(ROOT, 'data', 'dist_readme.txt'), encoding='utf-8').read().replace('{VER}', ver)
    open(os.path.join(out, '설치방법.txt'), 'w', encoding='utf-8-sig', newline='\r\n').write(readme)
    zp = out + '.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(out):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, out))
    n = sum(len(fs) for _, _, fs in os.walk(out))
    print('→ %s (파일 %d개, %d B, md5 %s)' % (zp, n, os.path.getsize(zp), hashlib.md5(open(zp, 'rb').read()).hexdigest().upper()))


if __name__ == '__main__':
    main()
