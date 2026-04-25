---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: C
depends_on: [03]
---

# Task 04 — ABC 계열 5개 분리 (assertion-cap·multiloop·error-propagation·cross-validation·abc-pipeline)

## Changed files

5개 실험을 task-03 패턴 그대로 분리. 각 실험마다 3개 신규 파일.

- `experiments/exp01_assertion_cap/__init__.py` — **신규**.
- `experiments/exp01_assertion_cap/run.py` — **신규**. `run_experiment.py:run_assertion_cap` (line 99-153) 본문 이동.
- `experiments/exp01_assertion_cap/INDEX.md` — **신규**. `experiments/exp01_assertion_cap/설명.md` 흡수.
- `experiments/exp02_multiloop/__init__.py` — **신규**.
- `experiments/exp02_multiloop/run.py` — **신규**. `run_experiment.py:run_multiloop` (line 154-213) 본문 이동.
- `experiments/exp02_multiloop/INDEX.md` — **신규**. `experiments/exp02_multiloop/설명.md` 흡수.
- `experiments/exp03_error_propagation/__init__.py` — **신규**.
- `experiments/exp03_error_propagation/run.py` — **신규**. `run_experiment.py:run_error_propagation` (line 214-305) 본문 이동.
- `experiments/exp03_error_propagation/INDEX.md` — **신규**. `experiments/exp03_error_propagation/설명.md` 흡수.
- `experiments/exp035_cross_validation/__init__.py` — **신규**.
- `experiments/exp035_cross_validation/run.py` — **신규**. `run_experiment.py:run_cross_validation` (line 306-437) 본문 이동.
- `experiments/exp035_cross_validation/INDEX.md` — **신규**. exp035 자체는 신규 디렉토리이므로 설명.md 없음 — 직접 작성.
- `experiments/exp04_abc_pipeline/__init__.py` — **신규**.
- `experiments/exp04_abc_pipeline/run.py` — **신규**. `run_experiment.py:run_abc_pipeline` (line 438-544) 본문 이동.
- `experiments/exp04_abc_pipeline/INDEX.md` — **신규**.
- `experiments/exp01_assertion_cap/설명.md` — **삭제**. 내용은 INDEX.md 로 흡수.
- `experiments/exp02_multiloop/설명.md` — **삭제**.
- `experiments/exp03_error_propagation/설명.md` — **삭제**.
- `experiments/run_experiment.py` — **수정**. 5개 함수 본문 제거 + 상단 import 5줄 추가.
- `experiments/tests/test_static.py` — **수정**. `TestPerExperimentImports.SPLIT_EXPERIMENTS` 에 5개 추가.

신규 외 다른 파일 수정 금지. exp04_tool_separation/설명.md 는 task-05 영역이라 손대지 않음.

## Change description

### 패턴

각 실험에 대해 task-03 의 절차를 그대로 따른다:

1. `expXX_<slug>/__init__.py` 빈 파일 생성.
2. `expXX_<slug>/run.py` 신규 — 원본 `run_experiment.py` 의 `run_<func>` 본문 그대로 + 사용하는 import.
3. `expXX_<slug>/INDEX.md` 작성 — 실험 개요·결과·메트릭. 기존 `설명.md` 가 있으면 그 내용 흡수 후 삭제.
4. `run_experiment.py` 상단에 `from expXX_<slug>.run import run as run_<func>` import 추가.
5. `run_experiment.py` 의 `def run_<func>():` 본문 제거.

`EXPERIMENTS` dict 의 키·값은 변경 없음 (값이 함수 객체로 자동 매핑).

### 5개 실험 매핑

| dispatcher key | 함수 | 라인 | 새 디렉토리 | 기존 설명.md? |
|----------------|------|------|-------------|----------------|
| `assertion-cap` | `run_assertion_cap` | 99-153 | `exp01_assertion_cap/` | 있음 (흡수) |
| `multiloop` | `run_multiloop` | 154-213 | `exp02_multiloop/` | 있음 (흡수) |
| `error-propagation` | `run_error_propagation` | 214-305 | `exp03_error_propagation/` | 있음 (흡수) |
| `cross-validation` | `run_cross_validation` | 306-437 | `exp035_cross_validation/` | 없음 (신규 작성) |
| `abc-pipeline` | `run_abc_pipeline` | 438-544 | `exp04_abc_pipeline/` | 없음 (신규 작성) |

### Step 1 — `exp01_assertion_cap/run.py` 작성 + 설명.md 흡수

원본 `run_experiment.py` 의 line 99-153 본문 추출. 의존 import 식별 후 `run.py` 상단에 옮김. 헬퍼 함수가 있다면 함께 옮김 (중복 OK).

`exp01_assertion_cap/INDEX.md`:

```markdown
# 실험 1: Assertion 상한과 추론 품질

(기존 experiments/exp01_assertion_cap/설명.md 의 내용을 그대로 옮김.
"## 결과 파일" 섹션 추가.)

## 결과 파일

- `results/exp01_assertion_cap_20260408_170400.json`
- `results/exp01_assertion_cap_partial_20260408_153229.json`
- ... (총 7개)
- `exp01_run.log` (top-level에서 이동)

## dispatcher key

`assertion-cap`

## 변경 이력

- 2026-04-25: experiments-task-04 으로 분리. 설명.md 흡수.
```

기존 `experiments/exp01_assertion_cap/설명.md`는 `git rm` 으로 제거.

### Step 2 — `exp02_multiloop`, `exp03_error_propagation` 동일 패턴

`설명.md` 흡수 + `git rm`. 결과 파일 링크 + 메트릭 placeholder.

### Step 3 — `exp035_cross_validation`, `exp04_abc_pipeline` — 신규 디렉토리 (설명.md 없음)

`INDEX.md`를 직접 작성. 함수 docstring 또는 원본 코드 주석에서 추출한 1-2문단 개요.

`exp035_cross_validation/INDEX.md`:

```markdown
# 실험 3.5: Cross Validation

## 개요

(원본 run_experiment.py:run_cross_validation 의 docstring 또는 주석에서
1-2문단 추출. 없으면 함수 본문 분석으로 1문장 작성.)

## dispatcher key

`cross-validation`

## 결과 파일

- `results/exp035_cross_validation_20260409_150703.json`

## 변경 이력

- 2026-04-25: experiments-task-04 으로 분리. INDEX.md 신규 작성.
```

### Step 4 — `run_experiment.py` 수정

상단 import 영역에 5줄 추가:

```python
from exp01_assertion_cap.run import run as run_assertion_cap
from exp02_multiloop.run import run as run_multiloop
from exp03_error_propagation.run import run as run_error_propagation
from exp035_cross_validation.run import run as run_cross_validation
from exp04_abc_pipeline.run import run as run_abc_pipeline
```

함수 본문 5개 제거:
- line 99-153 (`run_assertion_cap`)
- line 154-213 (`run_multiloop`)
- line 214-305 (`run_error_propagation`)
- line 306-437 (`run_cross_validation`)
- line 438-544 (`run_abc_pipeline`)

`EXPERIMENTS` dict 그대로.

### Step 5 — `tests/test_static.py` 의 `TestPerExperimentImports.SPLIT_EXPERIMENTS` 확장

```python
SPLIT_EXPERIMENTS = (
    ("exp00_baseline", "run", "run"),
    ("exp01_assertion_cap", "run", "run"),
    ("exp02_multiloop", "run", "run"),
    ("exp03_error_propagation", "run", "run"),
    ("exp035_cross_validation", "run", "run"),
    ("exp04_abc_pipeline", "run", "run"),
)
```

`test_each_split_experiment_imports`, `test_split_dir_has_index_md`, `test_split_dir_has_results` 메소드는 그대로 (loop가 자동 6개로 증가).

### Step 6 — line 번호 변경 처리

본 task 진행 중 line 번호가 줄어든다 (함수 본문 제거 → 후속 함수 line 번호 감소). 이는 task-05 의 line 정보가 stale 해지는 위험 — task-05 작업자는 본 task 완료 직후 `grep -n "^def run_" experiments/run_experiment.py` 로 재검증 필요. **task-05 의 Verification 첫 줄에 이 명령 명시.**

## Dependencies

- **Task 03 완료** — exp00_baseline 패턴이 잡혀 있어야 본 task가 그대로 따라감.
- 외부 패키지: 없음.

## Verification

```bash
# 1. 신규 12 파일 (5 expdir × (init + run + INDEX) - 1 (exp01의 INDEX는 흡수가 새 파일이지만 설명.md 삭제) = 14 신규 + 3 삭제)
# 단순화: __init__.py 5, run.py 5, INDEX.md 5
test -f experiments/exp01_assertion_cap/__init__.py && \
test -f experiments/exp01_assertion_cap/run.py && \
test -f experiments/exp01_assertion_cap/INDEX.md && \
test -f experiments/exp02_multiloop/__init__.py && \
test -f experiments/exp02_multiloop/run.py && \
test -f experiments/exp02_multiloop/INDEX.md && \
test -f experiments/exp03_error_propagation/__init__.py && \
test -f experiments/exp03_error_propagation/run.py && \
test -f experiments/exp03_error_propagation/INDEX.md && \
test -f experiments/exp035_cross_validation/__init__.py && \
test -f experiments/exp035_cross_validation/run.py && \
test -f experiments/exp035_cross_validation/INDEX.md && \
test -f experiments/exp04_abc_pipeline/__init__.py && \
test -f experiments/exp04_abc_pipeline/run.py && \
test -f experiments/exp04_abc_pipeline/INDEX.md && \
echo "OK 15 new files"

# 2. 설명.md 3개 삭제 (exp01·02·03)
test ! -f experiments/exp01_assertion_cap/설명.md && \
test ! -f experiments/exp02_multiloop/설명.md && \
test ! -f experiments/exp03_error_propagation/설명.md && \
echo "OK 3 legacy 설명.md removed"
# 단 exp04_tool_separation/설명.md 는 task-05 영역이라 그대로 둬야 함
test -f experiments/exp04_tool_separation/설명.md && echo "OK exp04 설명.md untouched"

# 3. 5개 신규 모듈 import 가능
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp01_assertion_cap.run import run as r1
from exp02_multiloop.run import run as r2
from exp03_error_propagation.run import run as r3
from exp035_cross_validation.run import run as r4
from exp04_abc_pipeline.run import run as r5
for r in (r1, r2, r3, r4, r5):
    assert callable(r)
print('OK 5 modules callable')
"

# 4. run_experiment.py 의 5개 함수 본문 제거됨
cd experiments && for f in run_assertion_cap run_multiloop run_error_propagation run_cross_validation run_abc_pipeline; do
  count=$(grep -c "^def $f" run_experiment.py)
  test "$count" = "0" || { echo "FAIL $f still defined"; exit 1; }
done && echo "OK 5 functions removed from run_experiment.py"

# 5. 14개 dispatcher 키 그대로
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
keys = set(run_experiment.EXPERIMENTS.keys())
expected = {'baseline', 'assertion-cap', 'multiloop', 'error-propagation',
            'cross-validation', 'abc-pipeline', 'prompt-enhance',
            'tool-separation', 'handoff-protocol', 'solo-budget',
            'loop-saturation', 'tool-use', 'tool-use-refined', 'longctx'}
assert keys == expected
# dispatcher value 가 새 import 와 동일 객체
from exp01_assertion_cap.run import run as r1
assert run_experiment.EXPERIMENTS['assertion-cap'] is r1
print('OK dispatcher mappings intact')
"

# 6. test_static.py PASS — 19 + 0(메소드 추가 없음, loop만 확장) = 19 tests
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -8
# 기대: "Ran 19 tests" 또는 그 이상 + "OK"

# 7. run_experiment.py 라인 수가 task-03 후 대비 약 320 라인 추가 감소 (5개 함수 ~약 50라인 평균)
wc -l experiments/run_experiment.py
# 기대: 약 1100 ± 50 라인

# 8. 5개 INDEX.md 가 결과 파일 링크 포함
for f in exp01_assertion_cap exp02_multiloop exp03_error_propagation exp035_cross_validation exp04_abc_pipeline; do
  grep -q "results/" experiments/$f/INDEX.md || { echo "FAIL $f INDEX missing results link"; exit 1; }
done && echo "OK 5 INDEX.md have results link"

# 9. 다른 함수 (task-05/06 영역) 본문 보존
cd experiments && for f in run_prompt_enhance run_tool_separation run_handoff_protocol run_solo_budget run_loop_saturation run_tool_use run_tool_use_refined run_longctx; do
  count=$(grep -c "^def $f" run_experiment.py)
  test "$count" = "1" || { echo "FAIL $f changed unexpectedly"; exit 1; }
done && echo "OK 8 untouched functions preserved"
```

## Risks

- **line 번호 stale**: 본 task 진행 중간에 함수 본문이 제거되면서 후속 함수 line 이 위로 당겨짐. 위 task description 의 line 정보 (예: line 154 multiloop)는 task 시작 시점 기준. 작업 순서: line 번호 큰 함수부터 (= `run_abc_pipeline` 부터 위로) 제거하면 line 번호 안정. **권장 순서**: abc_pipeline → cross_validation → error_propagation → multiloop → assertion_cap.
- **헬퍼 함수 식별 누락**: task-03 위험과 동일. 본 task에서는 5개 함수 각각 헬퍼 의존성 분석 필요.
- **설명.md 한글 파일명**: macOS 환경에서 NFC/NFD 정규화 차이로 git mv 가 실패할 수 있음. 그 경우 `git rm` + 새 INDEX.md `git add` 로 처리 (이 경우 history 끊김 OK — 설명.md 는 짧고 INDEX.md 가 흡수).
- **exp035 vs exp03.5 명명**: 디렉토리 이름은 dot 사용 불가 (Python 모듈 명에 dot 허용 안 됨). `exp035` 로 통일. INDEX 표 헤더에서는 "3.5" 표기 가능.
- **`EXPERIMENTS_DIR` PYTHONPATH 의존성**: import `from exp01_assertion_cap.run import run` 가 동작하려면 CWD 가 `experiments/` 거나 PYTHONPATH 에 `experiments/` 가 있어야. CLI `python run_experiment.py` 는 자동 OK. unittest 호출 (`python -m unittest tests.test_static`) 도 CWD가 `experiments/` 이면 OK.
- **graph data 영향**: code-review-graph 가 `run_*` 함수 5개의 caller 추적 시 변경 감지. dispatcher dict 만 caller (변화 없음). 위험 0.5/10.
- **자식 함수의 import 충돌**: 5개 모듈이 모두 `from orchestrator import ...` 형태로 import 시 sys.path 보정 필요. 본 task에서는 `experiments/__init__.py` (task-03 추가) 가 있어 패키지 컨텍스트로 import 가능. CWD 가 `experiments/` 가 아닐 시 fallback 처리 필요.

## Scope boundary

**Task 04에서 절대 수정 금지**:

- `experiments/run_experiment.py` 의 task-05/06 영역 함수 8개 (`run_prompt_enhance`, `run_tool_separation`, `run_handoff_protocol`, `run_solo_budget`, `run_loop_saturation`, `run_tool_use`, `run_tool_use_refined`, `run_longctx`).
- `experiments/run_experiment.py` 의 `EXPERIMENTS` dict 의 키 (그대로 14개 유지).
- `experiments/exp00_baseline/` (task-03 영역).
- `experiments/exp04_tool_separation/` 디렉토리 (task-05에서 _archived 로 이동).
- 공용 모듈 (`orchestrator.py`, `schema.py` 등).
- `experiments/INDEX.md` (task-07 갱신 영역).
- `experiments/_template/`.
- `docs/plans/*` — 본 task 외 plan 문서.
- `experiments/tests/test_static.py` 의 `TestPerExperimentImports` 외 다른 TestCase 메소드.

**허용 범위**:

- `exp01_assertion_cap/`, `exp02_multiloop/`, `exp03_error_propagation/`, `exp035_cross_validation/`, `exp04_abc_pipeline/` 5개 디렉토리에 `__init__.py`·`run.py`·`INDEX.md` 신규.
- 위 3개 디렉토리(`exp01_assertion_cap`, `exp02_multiloop`, `exp03_error_propagation`)의 `설명.md` 삭제.
- `experiments/run_experiment.py` 의 5개 함수 본문 제거 + 상단 import 5줄 추가.
- `experiments/tests/test_static.py` 의 `TestPerExperimentImports.SPLIT_EXPERIMENTS` 튜플에 5개 항목 추가.
