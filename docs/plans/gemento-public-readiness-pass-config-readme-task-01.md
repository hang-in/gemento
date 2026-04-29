---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: A
depends_on: []
---

# Task 01 — config.py API URL 환경변수화 + requirements.txt 신규

## Changed files

- `experiments/config.py` — **수정**. line 14 (`API_BASE_URL = "http://yongseek.iptime.org:8005"`) 를 환경변수 기반으로 변경. line 15 의 `API_CHAT_URL` 은 동일 유지.
- `requirements.txt` — **신규**. 프로젝트 루트에 작성.
- `README.md` — **수정**. Quickstart 의 `pip install httpx scipy numpy` 라인을 `pip install -r requirements.txt` 로 변경.
- `README.ko.md` — **수정**. Quickstart 동일 변경 (한국어판 위치 확인 후).

신규 파일 1, 수정 3.

## Change description

### 배경

`experiments/config.py:14` 에 개인 서버 (`yongseek.iptime.org:8005`) 가 노출. README Quickstart 에는 `localhost:8080` 기본값으로 설명되지만 실제 코드는 개인 도메인. 외부 공개 시 신뢰도 저하 + 사용자 환경 의존성 노출.

또 Exp09 RAG baseline 의 `experiments/tools/bm25_tool.py` 가 `bm25s` 를 import 하는데 README Quickstart 의 `pip install httpx scipy numpy` 라인에서 누락. 재현 시 `ModuleNotFoundError`.

### Step 1 — `experiments/config.py:14` 환경변수화

기존:
```python
API_BASE_URL = "http://yongseek.iptime.org:8005"
API_CHAT_URL = f"{API_BASE_URL}/v1/chat/completions"
```

변경:
```python
import os  # 모듈 상단에 이미 import 되어 있는지 확인 후 필요 시 추가

API_BASE_URL = os.getenv("GEMENTO_API_BASE_URL", "http://localhost:8080")
API_CHAT_URL = f"{API_BASE_URL}/v1/chat/completions"
```

요구사항:
- `os` 모듈 import (`config.py` 의 import 영역 점검 — 이미 있으면 추가 안 함)
- 환경변수명: `GEMENTO_API_BASE_URL` (사용자 정책 명시)
- 기본값: `http://localhost:8080` (README Quickstart 와 일치)
- `API_CHAT_URL` 그대로 유지 — 기존 호출자 회귀 0

### Step 2 — `requirements.txt` 신규

프로젝트 루트에 작성:

```
httpx
numpy
scipy
bm25s
```

요구사항:
- 4 패키지만 (Exp09 RAG baseline + 기존 Quickstart)
- 버전 unpinned (loose) — 사용자 정책상 재현성 vs 호환성 trade-off, 별도 결정
- 마지막 줄에 newline

### Step 3 — README.md Quickstart 갱신

기존 `pip install httpx scipy numpy` 라인 위치를 grep 으로 찾아 변경:

```markdown
pip install -r requirements.txt
```

요구사항:
- 변경 전 grep 으로 정확한 라인 위치 확인 (라인 번호 변동 가능)
- 한·영 동시 변경

### Step 4 — README.ko.md 동기화

한국어 README 의 Quickstart 영역을 grep 으로 찾아 동일 변경.

## Dependencies

- 패키지: 표준 `os`. 신규 의존성 0 (requirements 자체가 외부 의존성 명시).
- 다른 subtask: 없음. parallel_group A 의 시작점.

## Verification

```bash
# 1) config.py 의 API_BASE_URL 이 환경변수 기반인지
.venv/bin/python -c "
import os
os.environ.pop('GEMENTO_API_BASE_URL', None)  # ensure default
from experiments.config import API_BASE_URL, API_CHAT_URL
assert API_BASE_URL == 'http://localhost:8080', f'default wrong: {API_BASE_URL}'
assert API_CHAT_URL == 'http://localhost:8080/v1/chat/completions'
# env override
os.environ['GEMENTO_API_BASE_URL'] = 'http://example.com:9000'
import importlib, experiments.config
importlib.reload(experiments.config)
from experiments.config import API_BASE_URL as B2
assert B2 == 'http://example.com:9000', f'env override failed: {B2}'
print('config.py 환경변수화 ok')
"

# 2) 개인 도메인 노출 0
grep -rn "yongseek\|iptime" experiments/ docs/ README.md README.ko.md 2>/dev/null | grep -v ".pyc" | head -5
# 기대: 0 라인 (단, docs/reference/handoff-* 의 과거 기록은 변경 불가)

# 3) requirements.txt 존재 + 4 패키지
test -f requirements.txt && echo "requirements.txt 존재"
.venv/bin/python -c "
with open('requirements.txt') as f:
    pkgs = [l.strip() for l in f if l.strip() and not l.startswith('#')]
assert set(pkgs) == {'httpx', 'numpy', 'scipy', 'bm25s'}, f'pkgs mismatch: {pkgs}'
print('requirements.txt 4 패키지 ok')
"

# 4) README 둘 다 'pip install -r requirements.txt' 사용
grep -c "pip install -r requirements.txt" README.md README.ko.md
# 기대: 양쪽 1+

# 5) 기존 'pip install httpx scipy numpy' 라인 제거됨
grep -c "pip install httpx scipy numpy" README.md README.ko.md
# 기대: 0 / 0
```

5 명령 모두 정상 + assertion 통과.

## Risks

- **`os` import 중복 위험**: `config.py` 에 `os` 가 이미 import 되어 있을 수 있음. Step 1 진행 전 grep 으로 확인 후 중복 import 추가 금지.
- **환경변수 시점**: 다른 모듈이 `from config import API_BASE_URL` 한 후 환경변수가 변경되면 그 모듈은 갱신 안 됨. 본 task 는 단순 default 변경이라 영향 없음 (런타임에 환경변수 변경 가정 안 함).
- **`yongseek` 단어 grep 의 false positive**: `docs/reference/handoff-*` 등 과거 기록에 등장 가능. Verification 2 에서 `experiments/` + 두 README 만 검사 (handoff 기록은 보존).
- **bm25s 의존성**: `pip install bm25s` 가 다른 의존성 (예: numpy 충돌) 일으킬 수 있음. 본 task 의 verification 은 import 확인만 (실제 RAG run 검증은 별도).
- **requirements.txt 의 버전 unpinned**: 미래 패키지 업데이트로 호환성 깨질 위험. 사용자 정책상 trade-off 명시, 별도 plan 후보.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` / `experiments/measure.py` / `experiments/schema.py` / `experiments/tasks/taskset.json` — 다른 영역
- `experiments/exp10_reproducibility_cost/` 의 코드 / 결과 JSON — 직전 plan 산출물
- `docs/reference/conceptFramework.md` — Task 02 영역
- `experiments/exp10_reproducibility_cost/INDEX.md` — Task 03 영역
- README 의 H4 행 / Related work / Headline 등 — Task 04/05/06 영역
- `experiments/_external/lmstudio_client.py` 등 다른 client 코드 (API_BASE_URL 사용처 호출자) — config 의 default 만 변경, 호출 코드 변경 0
