---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: C
depends_on: [01, 02, 03, 04]
---

# Task 05 — INDEX.md + tests 갱신 + smoke 실행 (정적)

## Changed files

- `experiments/exp10_reproducibility_cost/INDEX.md` — **신규**. 실험 개요·하이퍼파라미터·결과 placeholder
- `experiments/run_experiment.py` — **수정**. EXPERIMENTS dict 에 `"reproducibility-cost"` 키 추가 + 상단 import 1줄
- `experiments/INDEX.md` — **수정**. 13 active → 14 active 표 갱신
- `experiments/tests/test_static.py` — **수정**. `SPLIT_EXPERIMENTS` 에 `exp10_reproducibility_cost` 추가, `EXPECTED_KEYS_AFTER_TASK_05` 에 `"reproducibility-cost"` 추가

신규 외 다른 파일 수정 금지.

## Change description

### 배경

task-01~04 의 신규 디렉토리 + run.py + analyze.py 가 작성됐으니 dispatcher (run_experiment.py) 와 INDEX, tests 통합 단계. 본 task 는 LLM 호출 0 (정적 검증만). 실증은 task-06.

### Step 1 — `experiments/exp10_reproducibility_cost/INDEX.md` 작성

```markdown
# 실험 10: Reproducibility & Cost Profile

## 개요

3 condition × 9 task × N=20 trial = 540 호출 비교 실험.
- **Q1 (재현성)**: 같은 입력 N=20 trial 의 정답률 표준편차
- **Q2 (비용·시간)**: Gemma 8루프 vs Gemini 2.5 Flash 1회 trade-off

이전 9개 실험은 정확도 평균만 보고했지만 본 실험은 **외부 평가용 데이터**
(분산 + 비용) 를 산출한다.

## dispatcher key

`reproducibility-cost` (`python run_experiment.py reproducibility-cost`)

## 하이퍼파라미터

- DEFAULT_TRIALS: 20 (per condition × task)
- 9 task subset: math-01~04, synthesis-01·03·04, logic-03·04
- 3 condition: `gemma_8loop`, `gemma_1loop`, `gemini_flash_1call`
- gemma_8loop max_cycles: 15 (loop_saturation baseline_phase15 동등)
- Gemini 2.5 Flash 가격 (2025-04 기준): input $0.075/M, output $0.30/M
- gemini_flash_1call rate limit: 호출 후 1초 sleep (Google AI Studio 무료 tier 안전)
- API 키 로드: `gemento/.env` (GEMINI_API_KEY) 또는 `../secall/.env` (SECALL_GEMINI_API_KEY) 자동 fallback

## 결과 파일 (task-06 후 채워짐)

- `results/exp10_reproducibility_cost_*.json` — 540 trial 원본
- `results/exp10_report.md` — analyze.py 가 생성한 markdown report

## 핵심 메트릭 (task-06 후 채워짐)

| condition | accuracy mean ± std | total cost USD | total wallclock (s) |
|-----------|--------------------:|---------------:|--------------------:|
| gemma_8loop | TBD | $0 | TBD |
| gemma_1loop | TBD | $0 | TBD |
| gemini_flash_1call | TBD | TBD | TBD |

## 변경 이력

- 2026-04-26: 본 task-05 까지 — 코드 인프라 + 정적 검증 완료. task-06 에서 실증 실행.
```

### Step 2 — `experiments/run_experiment.py` 수정

상단 import 영역 마지막에 1줄 추가:

```python
from exp10_reproducibility_cost.run import run as run_reproducibility_cost
```

`EXPERIMENTS` dict 에 마지막 항목으로 1줄 추가:

```python
EXPERIMENTS = {
    "baseline": run_baseline,
    ...
    "longctx": run_longctx,
    "reproducibility-cost": run_reproducibility_cost,  # NEW (Exp10)
}
```

dict 가 13 → 14 키.

### Step 3 — `experiments/INDEX.md` 수정

`## 실험 목록 (13 active + 1 archived)` → `## 실험 목록 (14 active + 1 archived)` 으로 변경.

표에 마지막 active 행으로 1줄 추가 (exp09_longctx 다음):

```markdown
| 10 | [exp10_reproducibility_cost](exp10_reproducibility_cost/INDEX.md) | `reproducibility-cost` | Q1·Q2 — 재현성·비용 프로파일 | TBD (task-06 후) |
```

### Step 4 — `experiments/tests/test_static.py` 수정

(1) `TestDispatcherIntegrity.EXPECTED_KEYS_AFTER_TASK_05` 에 `"reproducibility-cost"` 추가:

```python
EXPECTED_KEYS_AFTER_TASK_05 = {
    "baseline", "assertion-cap", "multiloop", "error-propagation",
    "cross-validation", "abc-pipeline", "prompt-enhance",
    "handoff-protocol", "solo-budget", "loop-saturation",
    "tool-use", "tool-use-refined", "longctx",
    "reproducibility-cost",  # NEW (Exp10 task-05)
}
# 14 keys
```

(2) `TestPerExperimentImports.SPLIT_EXPERIMENTS` 에 추가:

```python
SPLIT_EXPERIMENTS = (
    ...
    ("exp09_longctx", "run", "run"),
    ("exp10_reproducibility_cost", "run", "run"),  # NEW
)
```

(3) Outline 보호: `TestNoLegacyRunFunctions` 는 그대로 PASS — `^def run_` 0건 유지.

(4) 새 TestCase 또는 메소드 추가 불필요 — 기존 `test_each_split_experiment_imports` 가 loop 로 자동 검증.

### Step 5 — Smoke 실행 (LLM 호출 0)

본 task 끝에 `--dry-run` smoke 1회. CLI dispatcher 라우팅이 동작하는지 import 체인 검증:

```bash
cd experiments
../.venv/bin/python run_experiment.py reproducibility-cost --help
# 또는
../.venv/bin/python -m exp10_reproducibility_cost.run --dry-run --trials 1
```

LLM 호출 0 (dry-run 또는 --help). 실제 1회 호출 smoke 도 옵션이지만 본 plan Constraints (Reviewer 가드) 에 따라 task-06 으로 보류.

## Dependencies

- **Task 01·02·03·04 모두 완료** — `_external/`, `exp10_reproducibility_cost/{__init__,tasks,run,analyze}.py` 모두 존재해야 import 통과.

## Verification

```bash
# 1. 신규 파일 존재 (INDEX.md)
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/INDEX.md && \
echo "OK INDEX.md exists"

# 2. run_experiment.py 의 EXPERIMENTS 가 14 키
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
keys = set(run_experiment.EXPERIMENTS.keys())
assert len(keys) == 14, f'expected 14, got {len(keys)}'
assert 'reproducibility-cost' in keys
from exp10_reproducibility_cost.run import run
assert run_experiment.EXPERIMENTS['reproducibility-cost'] is run
print('OK 14 dispatcher keys, reproducibility-cost mapped')
"

# 3. 최상위 INDEX.md 가 14 active 표시
grep -q "14 active" /Users/d9ng/privateProject/gemento/experiments/INDEX.md && \
grep -q "exp10_reproducibility_cost" /Users/d9ng/privateProject/gemento/experiments/INDEX.md && \
echo "OK top-level INDEX.md updated"

# 4. test_static.py 모두 PASS — 20 + (TestPerExperimentImports loop 1개 추가) = 20+ tests OK
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -8
# 기대: "Ran 20 tests" 또는 그 이상 + "OK"

# 5. INDEX.md 의 모든 [text](path.md) 링크 실재 (exp10_reproducibility_cost/INDEX.md 포함)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import re
from pathlib import Path
text = Path('INDEX.md').read_text(encoding='utf-8')
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+\.md)\)', text):
    link = m.group(2)
    if link.startswith('http'): continue
    target = Path(link).resolve()
    if not target.exists():
        broken.append(link)
assert not broken, f'broken: {broken}'
print('OK INDEX.md links resolve')
"

# 6. CLI --help 가 14 choices 표시
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_experiment.py --help 2>&1 | grep -q "reproducibility-cost" && echo "OK CLI shows reproducibility-cost"

# 7. dry-run smoke (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m exp10_reproducibility_cost.run --dry-run --trials 1 2>&1 | head -5
# 기대: "(dry-run, skipping LLM call)" 출력

# 8. EXPECTED_KEYS_AFTER_TASK_05 가 dispatcher 와 정확 일치
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
from tests.test_static import TestDispatcherIntegrity as T
assert set(run_experiment.EXPERIMENTS.keys()) == T.EXPECTED_KEYS_AFTER_TASK_05
print('OK EXPECTED_KEYS_AFTER_TASK_05 matches actual dispatcher')
"

# 9. SPLIT_EXPERIMENTS 가 14 디렉토리 (13 + exp10)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from tests.test_static import TestPerExperimentImports as T
assert len(T.SPLIT_EXPERIMENTS) == 14, f'expected 14, got {len(T.SPLIT_EXPERIMENTS)}'
dirs = {d for d, _, _ in T.SPLIT_EXPERIMENTS}
assert 'exp10_reproducibility_cost' in dirs
print('OK SPLIT_EXPERIMENTS has 14 entries including exp10')
"

# 10. 라인 수 — run_experiment.py 약간 증가 (~83 → ~85)
cd /Users/d9ng/privateProject/gemento/experiments && wc -l run_experiment.py
# 기대: 약 85-88 라인 (1줄 import + dict 1행)
```

## Risks

- **EXPERIMENTS dict 의 한 줄 추가가 dict 크기 검증 (TestRunExperimentSlim) 깨뜨릴까?**: `TestRunExperimentSlim.MAX_LINES = 200`. 현재 83 → 85 라인. 충분히 안전.
- **import 순서 — circular**: `exp10_reproducibility_cost.run` 이 `_external/gemini_client` 를 import → 그게 stdlib + httpx 만 사용. circular 없음. `tasks.py` 가 `measure` import — measure 는 다른 expXX 와 독립. 안전.
- **INDEX.md "13 active" → "14 active" 미반영 위험**: 정직하게 표 헤더+행만 갱신. 변경 폭 작음.
- **test_static.py 의 test_dispatcher_keys_match_expected 가 깨질 수 있음**: 정확히 EXPECTED_KEYS_AFTER_TASK_05 갱신해야 통과. 본 task 의 핵심 변경 중 하나.
- **smoke 실행이 LLM 호출 발생시킬 가능성**: `--dry-run` 가 dispatcher 함수 호출 직전 print 후 return. 코드를 정확히 읽어 dry-run 분기 검증. 본 task 작성자는 Verification 7 결과를 직접 눈으로 확인.

## Scope boundary

**Task 05 에서 절대 수정 금지**:

- `experiments/exp10_reproducibility_cost/__init__.py`, `tasks.py`, `run.py`, `analyze.py` — task-02·03·04 결과물 그대로.
- `experiments/_external/` — task-01 결과물 그대로.
- `experiments/orchestrator.py`, `config.py`, `schema.py`, `system_prompt.py`, `measure.py`.
- 다른 expXX/ 디렉토리.
- `experiments/run_experiment.py` 의 `EXPERIMENTS` dict 외 영역 (main, argparse, docstring 등).

**허용 범위**:

- `experiments/exp10_reproducibility_cost/INDEX.md` 신규.
- `experiments/run_experiment.py` 의 import 1줄 추가 + EXPERIMENTS dict 1줄 추가.
- `experiments/INDEX.md` 의 표 헤더 + 1행 추가.
- `experiments/tests/test_static.py` 의 `EXPECTED_KEYS_AFTER_TASK_05`·`SPLIT_EXPERIMENTS` 갱신.
