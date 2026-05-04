---
name: gemento-experiment-scaffold
description: gemento 의 새 실험 디렉토리 (`experiments/expNN_<slug>/`) 와 `run.py` 보일러플레이트를 *직전 Exp 의 run.py 패턴 그대로* 복제 후 condition / hook 만 변경하여 만든다. Sonnet (Developer) 가 plan 의 task-03 (`exp## run.py`) 진행 시 사용. 사용자가 "Exp## scaffold", "run.py 작성", "experiment 디렉토리 생성", "Stage 2A/2B/2C 패턴 복사" 등을 언급할 때 트리거. **임의 단순화 금지** — Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C cycle-by-cycle tattoo_history fix + 결과 JSON meta v1.0 보일러플레이트를 보존한다.
---

# gemento-experiment-scaffold

Sonnet 의 가장 큰 위험 — *Exp## run.py 의 임의 단순화* — 를 차단. 직전 Exp 의 run.py 를 정확히 복제 후 *최소한의 변경* (condition dispatch + run_<treatment> 함수 + import 한 줄) 만 적용.

## 언제 실행하는가

다음 신호 중 하나라도:

- Sonnet 이 plan 의 `task-03` (또는 동등) 인 `experiments/exp##_<slug>/run.py` 작성 단계 진입
- 사용자가 "Exp## run.py", "experiment scaffold", "보일러플레이트" 언급
- 새 plan 의 `Changed files` list 에 `experiments/exp##_<slug>/run.py — **신규**` 가 있을 때

## 사용 전 확보해야 할 정보

1. **새 Exp 번호 + slug** — 예: `exp14`, `search-tool` → 디렉토리명 `exp14_search_tool` (snake_case)
2. **참조 Exp** — 직전 Exp 의 run.py path. 보통 가장 최근 마감된 Exp 의 것:
   - Exp13 작성 시 → `experiments/exp12_extractor_role/run.py` 참조
   - Exp14 작성 시 → 직전 마감 Exp (예: Exp13 마감 후 `exp13_reducer_role/run.py`)
3. **condition list** — 보통 2 개 (baseline_<x> + treatment_<y>). plan 의 결정 항목에 명시되어 있어야 함
4. **추가 hook** — 어떤 `run_abc_chain` argument 가 새로 추가되는가? (예: `reducer_post_stage=True`, `search_tool=True`)
5. **plan task-03 본문** — Sonnet 이 받은 task 파일. Step 별 코드 stub 가 있으면 그것을 우선 따른다

## 처리 순서

### 1. 디렉토리 생성

```bash
mkdir -p experiments/exp##_<slug>/results
touch experiments/exp##_<slug>/__init__.py
touch experiments/exp##_<slug>/results/.gitkeep
```

`__init__.py` 는 빈 파일. `.gitkeep` 도 빈 파일.

### 2. 참조 Exp 의 run.py 정독

**중요 — Sonnet 이 자주 실수하는 부분**: 참조 Exp 의 run.py 를 *전체 read* 한다. snippet 만 보고 패턴 추측 금지. 다음 요소를 모두 식별:

- `_extract_tattoo_history()` 헬퍼 (Stage 2C cycle-by-cycle fix)
- `run_<condition>(task, trial_idx, max_cycles)` 함수 시그니처와 return dict 형식
- `CONDITION_DISPATCH` 매핑
- `run_experiment(*, taskset_path, trials_per_condition, conditions, max_cycles, out_name)` 본체
- `main()` argparse 본체
- Stage 2A 인프라: `classify_trial_error`, `is_fatal_error`, `check_error_rate`, `build_result_meta`, `get_taskset_version`, `normalize_sampling_params` import + 호출
- error rate abort 로직 (보통 50% 임계)
- partial result JSON 저장 (checkpoint resume)
- 최종 result JSON meta v1.0 schema

### 3. 새 run.py 작성 — 변경 최소화 원칙

다음 4 곳만 변경. 나머지는 참조 run.py 와 정확히 동일:

**(a) module docstring + 상단 import**
```python
"""Exp## <slug> — <한 줄 설명>.

H## 후보 가설: <가설 본문>.
"""
```

**(b) `run_<treatment>` 함수 추가** — `run_<baseline>` 와 같은 시그니처, `run_abc_chain` 호출에 새 argument 만 다르게:

```python
def run_<treatment>(task, trial_idx, max_cycles=DEFAULT_MAX_CYCLES) -> dict:
    """<한 줄> — <treatment 의 차이>"""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_<treatment>_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            <기존 hook>=False,
            <새 hook>=True,  # ⭐ 본 plan 의 핵심 차이
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"<treatment>: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }
```

**(c) `CONDITION_DISPATCH` 갱신**:

```python
CONDITION_DISPATCH = {
    "<baseline>": run_<baseline>,
    "<treatment>": run_<treatment>,
}
```

**(d) `main()` 의 `--conditions` default 갱신**:

```python
parser.add_argument("--conditions", nargs="+",
                    default=["<baseline>", "<treatment>"])
```

다른 모든 코드 — `_extract_tattoo_history`, `run_experiment`, partial JSON 저장, error rate check, meta v1.0 — **참조 Exp 와 정확히 동일** 해야 한다.

### 4. baseline 함수 동기화

**중요**: 참조 Exp 의 `run_baseline_abc` (또는 등가) 의 `run_abc_chain` 호출 인자를 그대로 가져온다. 단 *신규 hook* 은 `False` 로 명시:

```python
def run_baseline_abc(task, trial_idx, max_cycles=DEFAULT_MAX_CYCLES) -> dict:
    ...
    tattoo, abc_logs, final_answer = run_abc_chain(
        ...
        <기존 hook 1>=False,
        <기존 hook 2>=False,
        <새 hook>=False,  # ⭐ baseline 명시
    )
    ...
```

이렇게 해서 baseline 의 의미 = "이전 Exp 의 baseline + 새 hook=False" 로 명확.

### 5. 검증

`Verification` 명령 (plan task-03 본문) 그대로 실행:

```bash
# syntax + import + help
.venv/Scripts/python -m py_compile experiments/exp##_<slug>/run.py
.venv/Scripts/python -m experiments.exp##_<slug>.run --help

# CONDITION_DISPATCH 검증
.venv/Scripts/python -c "
from experiments.exp##_<slug>.run import CONDITION_DISPATCH
assert '<baseline>' in CONDITION_DISPATCH
assert '<treatment>' in CONDITION_DISPATCH
print('verification ok')
"

# 새 hook 호출 검증
.venv/Scripts/python -c "
import inspect
from experiments.exp##_<slug>.run import run_<treatment>
src = inspect.getsource(run_<treatment>)
assert '<새 hook>=True' in src
print('verification ok: <새 hook>=True 호출')
"
```

세 명령 모두 정상 시 task-03 마감 신호.

## 자주 하는 실수 (사용자 보고에서 누적)

다음을 *절대* 하지 않는다:

1. **`run_experiment` / `main` 본체 단순화** — 참조 run.py 와 정확히 같아야. healthcheck/abort, partial JSON checkpoint, error rate abort 모두 보존.
2. **`_extract_tattoo_history` 누락 또는 단순화** — Stage 2C 결함 fix 임. 단순히 `[tattoo.to_dict()]` 한 줄로 대체 금지.
3. **새 hook argument 를 baseline 에 누락** — baseline 의 `run_abc_chain` 호출에서 새 hook 인자가 없으면 Python 의 default 값을 받게 되어 의도와 다를 수 있다. 명시적으로 `False` 적기.
4. **CONDITION_DISPATCH key 명명 불일치** — `--conditions default` 와 `CONDITION_DISPATCH` key 가 같아야. 둘 중 하나만 바꾸지 말 것.
5. **참조 Exp 의 import 누락** — `from experiments.run_helpers import ...` block 그대로 복사. 새 Exp 의 import 만 끝에 추가.
6. **결과 JSON meta v1.0 schema 변경** — `build_result_meta()` 가 그대로 사용되어야. 임의 필드 추가 금지.

위 6 종 실수는 task-03 의 Risk section 에 보통 명시되어 있다. plan 본문 우선.

## 외부에서 변경 금지

- `experiments/orchestrator.py` (다른 task 영역 — `run_abc_chain` hook 추가)
- `experiments/system_prompt.py` (다른 task 영역 — 프롬프트 추가)
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py`
- `experiments/schema.py`
- `experiments/tasks/taskset.json`
- 기존 다른 `experiments/exp**/run.py` (read-only 참조)

## 종료 시 보고

```
<Exp##> scaffold 완료 — task-03

생성:
- experiments/exp##_<slug>/__init__.py
- experiments/exp##_<slug>/run.py (참조: <reference Exp> 패턴 정확 복제)
- experiments/exp##_<slug>/results/.gitkeep

CONDITION_DISPATCH:
- <baseline>: <기존 hook>=False, <새 hook>=False
- <treatment>: <기존 hook>=False, <새 hook>=True

검증 명령 결과: <ok|fail 상세>

다음 단계: 사용자에게 task-03 완료 보고 + task-04 (사용자 직접 실행) 신호
```
