---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: B
depends_on: [01, 02]
---

# Task 03 — exp00 분리 (단독, 패턴 확립)

## Changed files

- `experiments/exp00_baseline/__init__.py` — **신규** (빈 파일, 패키지 표지).
- `experiments/exp00_baseline/run.py` — **신규**. `run_experiment.py:run_baseline` (line 56-98) 본문 그대로 이동.
- `experiments/exp00_baseline/INDEX.md` — **신규**. 실험 0 개요·결과·메트릭 표.
- `experiments/run_experiment.py` — **수정**. `run_baseline` 함수 본문 제거 + 상단 import 추가 + `EXPERIMENTS` dict의 `"baseline"` 값을 `exp00_baseline.run.run` 으로 갱신.
- `experiments/tests/test_static.py` — **수정**. `TestPerExperimentImports` TestCase 신규 추가 (이번 task에서는 exp00 만 검사. 후속 task가 확장).

신규 외 다른 파일 수정 금지. 이 task의 핵심: **exp00 패턴이 잡히면 task-04~06이 그대로 따라간다**.

## Change description

### Step 1 — `experiments/exp00_baseline/__init__.py` 생성

빈 파일. Python 패키지 인식용.

### Step 2 — `experiments/exp00_baseline/run.py` 작성

원본 `experiments/run_experiment.py:run_baseline` (line 56-98, 약 43라인) 본문을 그대로 옮긴다. 추가로 docstring과 사용 import를 정리.

```python
"""실험 0: Baseline.

가정: Gemma 4 E4B 단독 실행 (Tattoo·ABC 없음). 단순 prompt → response.

dispatcher key: `baseline`
원본 함수: experiments/run_experiment.py:run_baseline (line 56)
"""

# 본 함수가 사용하는 import 는 원본 run_experiment.py 상단에서 가져온다.
# 단, run_experiment.py 가 import 하는 것 중 본 함수가 실제 사용하는 것만:
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

# 공용 모듈은 experiments/ 최상위에 있으므로 sys.path 보정 후 import
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orchestrator import call_model  # 또는 원본이 사용하는 함수
# (실제 import 명세는 run_baseline 본문 안에서 필요한 것만 가져온다)
sys.path.pop(0)


def run():
    """원본 run_baseline() 본문을 그대로 옮긴 함수."""
    # === BEGIN copy from experiments/run_experiment.py:run_baseline (line 56-98) ===
    # ... (원본 본문 그대로) ...
    # === END copy ===
```

**정확한 옮김 절차**:

1. `experiments/run_experiment.py` 의 line 56-98 (또는 다음 `def run_*` 시작 직전까지) 본문 추출.
2. 본문 내부 또는 함수 외부에서 사용하는 모듈·상수·헬퍼 함수 식별 (예: `call_model`, `score_answer_v2`, `TASKSET_PATH` 등).
3. 의존하는 식별자가 `run_experiment.py` 상단에 정의된 경우 (예: `from config import OLLAMA_TIMEOUT`), 해당 import 를 `run.py` 상단에도 옮김.
4. 의존하는 식별자가 `run_experiment.py` 안에서 정의된 헬퍼 함수인 경우 (있다면), 그 헬퍼는 별도 처리 — task-07에서 dispatcher 슬림화 시 dispatcher가 보유 vs 각 run.py 가 import vs 공용 모듈로 빼기 결정. **본 task 범위에서는 헬퍼가 있다면 일단 `run.py` 안에 함께 복사** (중복 OK, task-07에서 정리).
5. **로직은 한 글자도 수정 금지**. 들여쓰기·변수명·로깅 메시지 등 모두 원본 그대로.

### Step 3 — `experiments/exp00_baseline/INDEX.md` 작성

```markdown
# 실험 0: Baseline

## 개요

가정: Gemma 4 E4B 단독 실행 (Tattoo·ABC 없음). 단순 prompt → response.
이후 모든 실험의 기준선.

dispatcher key: `baseline`
원본 함수: `experiments/run_experiment.py:run_baseline` (line 56-98, task-03 시점)
이동된 함수: `experiments/exp00_baseline/run.py:run`

## 실행

```
cd experiments
../.venv/bin/python run_experiment.py baseline
```

## 결과 파일

- `results/exp00_baseline_20260408_080053.json`
- `results/exp00_baseline_20260408_082421.json`
- `results/exp00_baseline_20260408_102018.json`

## 핵심 메트릭

(메트릭 표는 결과 JSON에서 추출되어야 함. 본 task에서는 placeholder.)

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류) | - | - | - |

## 변경 이력

- 2026-04-25: experiments-task-03 으로 분리.
- (이전): `experiments/run_experiment.py:run_baseline` 단일 함수.
```

### Step 4 — `experiments/run_experiment.py` 수정

**가장 위험한 수정**. 다음 3가지를 정확히 수행:

(1) line 56-98 의 `run_baseline` 함수 본문 통째 제거.

(2) 파일 상단 import 영역에 다음 추가 (구체 위치는 다른 import 들 사이, 알파벳 순):

```python
from exp00_baseline.run import run as run_baseline
```

근데 `experiments/run_experiment.py` 자체가 `experiments/` 안에 있으므로, `experiments` 가 PYTHONPATH 에 있어야 `from exp00_baseline.run import run` 가 동작. CLI 호출(`python run_experiment.py baseline`) 시 CWD가 `experiments/` 이면 자동 동작. CWD 가 다르면 실패. 이 점은 README 또는 INDEX.md 에 명시.

대안: `from .exp00_baseline.run import run as run_baseline` (relative import). 단 `run_experiment.py`가 패키지의 일부여야 동작. `experiments/__init__.py` 가 있으면 가능. 본 task에서는 **`experiments/__init__.py` 도 같이 신규 추가**해서 패키지화 + relative import 채택.

→ **결정**: relative import. `experiments/__init__.py` 추가.

수정 후 import:

```python
from exp00_baseline.run import run as run_baseline
```

(또는 `from experiments.exp00_baseline.run import run` — 호출 컨텍스트에 따라 결정. **본 task에서는 절대 import 채택**: `from exp00_baseline.run import run as run_baseline` — `run_experiment.py` 가 `experiments/` 디렉토리에서 직접 실행될 때 동작.)

(3) `EXPERIMENTS` dict (line 1442) 의 `"baseline": run_baseline` 항목은 **변경 없음** (값이 함수 객체 `run_baseline` 으로 동일하니까). 단, 위 import 가 함수 객체를 import 하므로 dict 정의가 그대로 동작.

### Step 5 — `experiments/__init__.py` 신규

빈 파일. `experiments/` 를 Python 패키지로 만들어 import 안정성 확보.

근데 `experiments/__init__.py` 가 추가되면 `python run_experiment.py baseline` 호출 시 import 동작이 약간 달라짐. 정확히는 CWD 가 `experiments/` 라면 `run_experiment.py` 가 top-level script 로 동작 (`__name__ == "__main__"`) 하면서 sibling 디렉토리 `exp00_baseline/` 를 import 가능. 단, sibling 디렉토리도 패키지 (= `__init__.py` 보유) 여야 함. Step 1에서 `exp00_baseline/__init__.py` 추가했으므로 OK.

### Step 6 — `tests/test_static.py` 확장 — `TestPerExperimentImports`

기존 test_static.py 끝에 추가:

```python
class TestPerExperimentImports(unittest.TestCase):
    """task-03~06 — 각 실험 디렉토리의 run.py 가 import 가능한가"""

    SPLIT_EXPERIMENTS = (
        # task-03 후 추가될 항목. task-04~06이 확장.
        ("exp00_baseline", "run", "run"),  # (dir, module, attr)
    )

    def test_each_split_experiment_imports(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            for exp_dir, module_name, attr in self.SPLIT_EXPERIMENTS:
                full_module = f"{exp_dir}.{module_name}"
                mod = __import__(full_module, fromlist=[attr])
                self.assertTrue(hasattr(mod, attr),
                                f"{full_module} has no `{attr}`")
                self.assertTrue(callable(getattr(mod, attr)),
                                f"{full_module}.{attr} not callable")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_split_dir_has_index_md(self):
        for exp_dir, _, _ in self.SPLIT_EXPERIMENTS:
            index = EXPERIMENTS_DIR / exp_dir / "INDEX.md"
            self.assertTrue(index.exists(), f"{exp_dir}/INDEX.md missing")

    def test_split_dir_has_results(self):
        for exp_dir, _, _ in self.SPLIT_EXPERIMENTS:
            results = EXPERIMENTS_DIR / exp_dir / "results"
            self.assertTrue(results.is_dir(), f"{exp_dir}/results missing")
```

또한 `TestDispatcherIntegrity.test_dispatcher_keys_match_expected`의 `EXPECTED_KEYS_INITIAL` 은 그대로 유지 (14개 키, baseline 포함). `run_baseline` 함수가 dict value 로 그대로 매핑되어 있으므로 변화 없음.

### Step 7 — verification 명령으로 핵심 동작 보존 확인

`python run_experiment.py --help` 가 `baseline` choice 를 출력하는지 정적으로 확인.

## Dependencies

- **Task 01·02 완료** — tests/test_static.py 가 16 tests PASS, 결과 파일 분류 완료.
- 외부 패키지: 없음.

## Verification

```bash
# 1. 신규 4 파일 존재
test -f experiments/exp00_baseline/__init__.py && \
test -f experiments/exp00_baseline/run.py && \
test -f experiments/exp00_baseline/INDEX.md && \
test -f experiments/__init__.py && \
echo "OK 4 new files exist"

# 2. exp00_baseline.run import 가능
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp00_baseline.run import run
assert callable(run), 'run is not callable'
print('OK exp00_baseline.run.run callable')
"

# 3. run_experiment.py 의 EXPERIMENTS['baseline'] 가 동일 함수 객체
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
from exp00_baseline.run import run
assert run_experiment.EXPERIMENTS['baseline'] is run, \
    f'mismatch: {run_experiment.EXPERIMENTS[\"baseline\"]} vs {run}'
print('OK dispatcher[baseline] === exp00_baseline.run.run')
"

# 4. run_experiment.py 본문에 def run_baseline 사라짐
grep -c "^def run_baseline" experiments/run_experiment.py
# 기대: 0

# 5. run_experiment.py 라인 수가 줄어듦 (기존 1474 → 약 1430 정도)
wc -l experiments/run_experiment.py
# 기대: < 1474

# 6. test_static.py 가 PASS (기존 16 + TestPerExperimentImports 3 = 19 tests)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -10
# 기대: "Ran 19 tests" 와 "OK"

# 7. CLI argparse choices 에 baseline 보존
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_experiment.py --help 2>&1 | grep -q "baseline" && echo "OK CLI baseline choice present"

# 8. 다른 실험 키 영향 없음 (13개 그대로)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
keys = set(run_experiment.EXPERIMENTS.keys())
expected = {'baseline', 'assertion-cap', 'multiloop', 'error-propagation',
            'cross-validation', 'abc-pipeline', 'prompt-enhance',
            'tool-separation', 'handoff-protocol', 'solo-budget',
            'loop-saturation', 'tool-use', 'tool-use-refined', 'longctx'}
assert keys == expected, f'mismatch: {keys ^ expected}'
print('OK 14 dispatcher keys preserved')
"

# 9. exp00_baseline/INDEX.md 가 minimum 형식 검증 — 헤더·결과 링크
grep -q "^# 실험 0" experiments/exp00_baseline/INDEX.md && \
grep -q "exp00_baseline_20260408_080053.json" experiments/exp00_baseline/INDEX.md && \
echo "OK INDEX.md content"

# 10. 다른 함수가 run_baseline 을 직접 호출하는지 (모듈 외부 의존성 깨짐 가능성)
grep -n "run_baseline\b" experiments/run_experiment.py | grep -v "^run_baseline = "
# 기대: dict 정의 line 1개만 (그 외 호출 없음)
```

## Risks

- **import 경로 결정의 영향**: `experiments/__init__.py` 추가로 `experiments` 가 패키지 됨. 외부 도구가 `experiments` 를 디렉토리로 가정하던 경우 (예: `find experiments/ -name "*.py"`) 영향 없음. 단 `import experiments.exp00_baseline` 식 호출이 가능해짐 — 향후 외부 코드에서 활용 가능.
- **헬퍼 함수 누락**: `run_baseline` 본문이 `run_experiment.py` 안의 다른 헬퍼 (예: `_load_tasks`, `_save_result`)를 호출한다면, 그 헬퍼도 함께 옮기거나 import 해야. 누락 시 NameError. 본 task 작성자는 line 56-98 본문을 정독 후 의존 식별자 모두 확인.
- **로직 우발 변경**: 들여쓰기 통일·docstring 추가 등의 cosmetic 변경도 금지 (Plan Constraints). diff 가 줄 이동만 보여야.
- **EXPERIMENTS dict 의 함수 객체 변경**: import 바뀌면 `run_baseline` 식별자가 가리키는 객체가 변경됨. dict 정의에서 `"baseline": run_baseline` 그대로면 import 후 자동 매핑. 별도 dict 수정 불필요.
- **Verification 8의 키 비교 실패**: 만약 본 task 진행 중 dispatcher 키가 의도치 않게 변경되면 fail. 안전장치.
- **CWD 의존성**: `python run_experiment.py baseline` 호출이 `experiments/` CWD 외에서는 import 실패 가능. 본 plan 범위 밖이지만 INDEX.md 에 명시.
- **graph data 영향**: code-review-graph 분석 시 `run_baseline` 이 1개 함수에서 2개 위치 (run_experiment.py 의 import + exp00_baseline/run.py 의 정의)로 보이는 것은 정상. 호출 패턴은 그대로.

## Scope boundary

**Task 03에서 절대 수정 금지**:

- `experiments/run_experiment.py` 의 `run_baseline` 외 함수 (`run_assertion_cap` ... `run_longctx` 13개) — task-04~06 영역.
- `experiments/run_experiment.py` 의 `EXPERIMENTS` dict 의 다른 키 (`"assertion-cap"` ... `"longctx"`) — 그대로 둠.
- 다른 실험 디렉토리 (`exp01_assertion_cap/`, `exp02_multiloop/` 등) 의 새 파일 추가 — task-04~06 영역.
- 공용 모듈 (`orchestrator.py`, `schema.py` 등).
- `experiments/INDEX.md` 의 task-07 갱신 영역.
- `experiments/_template/` (task-01 영역).
- `docs/plans/*` — 본 task 외 plan 문서.
- `experiments/exp04_tool_separation/` — task-05 영역.

**허용 범위**:

- `experiments/exp00_baseline/__init__.py`, `run.py`, `INDEX.md` 신규.
- `experiments/__init__.py` 신규 (실험 패키지화).
- `experiments/run_experiment.py` 의 `run_baseline` 함수 본문 제거 + 상단 import 1줄 추가.
- `experiments/tests/test_static.py` 에 `TestPerExperimentImports` TestCase 추가 (3 메소드).
