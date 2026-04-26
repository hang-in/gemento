---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: C
depends_on: [01, 02, 03, 04, 05, 06]
---

# Task 07 — broken link 정적 검증

## Changed files

- 없음. 본 task 는 정적 검증만 수행 (코드/문서 변경 0).

## Change description

### 배경

task-01~06 의 누적 변경 (swap + 톤 정정 + 신규 섹션 3개 + cross-link 정정) 후 README.md / README.ko.md 의 모든 markdown 링크가 실재 파일을 가리키는지 단독 task 로 검증한다.

본 task 는 변경 0 — 읽기 + grep + python 으로 link target 실재 여부 확인.

### Step 1 — README.md 의 markdown 링크 모두 추출 + 실재 검증

regex `\[([^\]]+)\]\(([^)]+)\)` 로 모든 `[text](path)` 추출. external (http/https) 제외, anchor (`#section`) 제외, 나머지 path 모두 실재 검증.

```bash
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
import re
from pathlib import Path

readme = Path('README.md').read_text(encoding='utf-8')
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', readme):
    text, link = m.group(1), m.group(2)
    if link.startswith(('http://', 'https://', 'mailto:', '#')):
        continue
    # anchor 제거 (예: 'foo.md#section' → 'foo.md')
    path_only = link.split('#')[0]
    if not path_only:
        continue
    target = Path(path_only).resolve()
    if not target.exists():
        broken.append((text, link))
assert not broken, f'README.md broken links: {broken}'
print('OK README.md all links resolve')
"
```

### Step 2 — README.ko.md 동일 검증

```bash
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
import re
from pathlib import Path

readme = Path('README.ko.md').read_text(encoding='utf-8')
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', readme):
    text, link = m.group(1), m.group(2)
    if link.startswith(('http://', 'https://', 'mailto:', '#')):
        continue
    path_only = link.split('#')[0]
    if not path_only:
        continue
    target = Path(path_only).resolve()
    if not target.exists():
        broken.append((text, link))
assert not broken, f'README.ko.md broken links: {broken}'
print('OK README.ko.md all links resolve')
"
```

### Step 3 — 누적 무결성 — Plan 단위 검증

전체 plan 의 산출물 한꺼번에 sanity:

- `README.md` 영문, `README.ko.md` 한국어, `README.en.md` 부재.
- 4 docs 링크 (`README.ko.md`, `researchNotebook.md`, `researchNotebook.en.md`, `conceptFramework.md`) 모두 README.md 에서 참조 + 실재.
- README.md 의 `## Core idea`, `## Related work`, `## Research notes` 모두 등장.
- claim inflation 단어 (`proves`, `conquers`, `wins`) README.md 본문 0건.
- README.md 안의 `README.en.md` 참조 0건.

```bash
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
from pathlib import Path

assert Path('README.md').exists(), 'README.md missing'
assert Path('README.ko.md').exists(), 'README.ko.md missing'
assert not Path('README.en.md').exists(), 'README.en.md must be removed'

readme = Path('README.md').read_text(encoding='utf-8')
ko = Path('README.ko.md').read_text(encoding='utf-8')

# 신규 섹션 3개
for section in ('## Core idea', '## Related work', '## Research notes'):
    assert section in readme, f'README.md missing {section}'

# Docs Map 4 링크
for link in ('README.ko.md', 'researchNotebook.md', 'researchNotebook.en.md', 'conceptFramework.md'):
    assert link in readme, f'README.md missing link to {link}'

# claim inflation
import re
strong = re.findall(r'\b(proves|conquers|wins)\b', readme)
assert not strong, f'claim-inflation words: {strong}'

# stale en.md 참조
assert 'README.en.md' not in readme, 'stale README.en.md ref in README.md'
assert 'README.en.md' not in ko, 'stale README.en.md ref in README.ko.md'

print('OK all plan-level sanity passed')
"
```

### Step 4 — 본 task 는 변경 0 보고

`git diff HEAD` 가 본 task 시점 기준 변경 없음 (task-06 까지의 변경만 누적). 본 task 자체는 read-only 검증.

## Dependencies

- **task-01·02·03·04·05·06 완료** — 모든 README 변경이 끝나야 broken link 검증 의미 있음.
- 외부 패키지: stdlib `re`, `pathlib` 만 (Python 3 기본).

## Verification

```bash
# 1. README.md broken link 0건
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
import re
from pathlib import Path
readme = Path('README.md').read_text(encoding='utf-8')
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', readme):
    text, link = m.group(1), m.group(2)
    if link.startswith(('http://', 'https://', 'mailto:', '#')):
        continue
    path_only = link.split('#')[0]
    if not path_only:
        continue
    target = Path(path_only).resolve()
    if not target.exists():
        broken.append((text, link))
assert not broken, f'README.md broken links: {broken}'
print('OK README.md all links resolve')
"

# 2. README.ko.md broken link 0건
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
import re
from pathlib import Path
readme = Path('README.ko.md').read_text(encoding='utf-8')
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', readme):
    text, link = m.group(1), m.group(2)
    if link.startswith(('http://', 'https://', 'mailto:', '#')):
        continue
    path_only = link.split('#')[0]
    if not path_only:
        continue
    target = Path(path_only).resolve()
    if not target.exists():
        broken.append((text, link))
assert not broken, f'README.ko.md broken links: {broken}'
print('OK README.ko.md all links resolve')
"

# 3. plan-level sanity (Step 3 의 누적 검증)
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
from pathlib import Path
import re
assert Path('README.md').exists()
assert Path('README.ko.md').exists()
assert not Path('README.en.md').exists()
readme = Path('README.md').read_text(encoding='utf-8')
ko = Path('README.ko.md').read_text(encoding='utf-8')
for section in ('## Core idea', '## Related work', '## Research notes'):
    assert section in readme, f'missing {section}'
for link in ('README.ko.md', 'researchNotebook.md', 'researchNotebook.en.md', 'conceptFramework.md'):
    assert link in readme, f'missing link {link}'
strong = re.findall(r'\b(proves|conquers|wins)\b', readme)
assert not strong, f'claim words: {strong}'
assert 'README.en.md' not in readme
assert 'README.en.md' not in ko
print('OK plan-level sanity')
"

# 4. 본 task 자체는 변경 0
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only > /tmp/changed_files.txt
wc -l /tmp/changed_files.txt
# 기대: task-01~06 의 변경만 누적 (README.md, README.ko.md 정도). 본 task 가 추가하는 변경 0.
```

## Risks

- **regex anchor 처리**: `[label](file.md#section)` 같은 anchor link 가 path 부분만 검증됨. anchor 자체가 실재하는 heading 인지는 검증 안 함 (markdown anchor 는 lib 의존). 본 task 의 검증 한계 명시.
- **GitHub 자동 변환 anchor**: `## Core idea` → `#core-idea` GitHub 자동 anchor. 본 task 가 그것까지 검증하면 over-engineering. 단순 file path 만 검증.
- **Python 3 의존**: stdlib 만 사용하므로 `.venv` 부재해도 system python3 OK.
- **broken link 발견 시**: 본 task 는 검증만 — finding 보고 후 task-06 또는 별도 fix task 로 회귀.

## Scope boundary

**Task 07 에서 절대 수정 금지**:

- 모든 파일 — 본 task 는 read-only 검증.
- README.md, README.ko.md.
- `docs/`, `experiments/` 의 모든 파일.

**허용 범위**:

- python3 / shell command 실행 (read-only).
- broken link 발견 시 보고 (수정은 task-06 으로 회귀).
