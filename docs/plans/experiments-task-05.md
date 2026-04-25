---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: C
depends_on: [04]
---

# Task 05 — handoff·prompt·solo·deprecated 계열 4개 분리 (prompt-enhance·handoff-protocol·solo-budget·tool-separation deprecated)

## Changed files

4개 실험을 task-04 패턴 그대로 분리. 단 `run_tool_separation` 은 `_archived/` 로 격리하고 dispatcher 에서 제거 (deprecated 처리).

- `experiments/exp05a_prompt_enhance/__init__.py` — **신규**.
- `experiments/exp05a_prompt_enhance/run.py` — **신규**. `run_experiment.py:run_prompt_enhance` (line 545-660 기준, task-04 후 line 번호는 재확인) 본문 이동.
- `experiments/exp05a_prompt_enhance/INDEX.md` — **신규**.
- `experiments/exp045_handoff_protocol/__init__.py` — **신규**.
- `experiments/exp045_handoff_protocol/run.py` — **신규**. `run_experiment.py:run_handoff_protocol` 본문 이동.
- `experiments/exp045_handoff_protocol/INDEX.md` — **신규**.
- `experiments/exp06_solo_budget/__init__.py` — **신규**.
- `experiments/exp06_solo_budget/run.py` — **신규**. `run_experiment.py:run_solo_budget` 본문 이동.
- `experiments/exp06_solo_budget/INDEX.md` — **신규**.
- `experiments/_archived/__init__.py` — **신규** (빈 파일).
- `experiments/_archived/exp04_tool_separation_deprecated/__init__.py` — **신규**.
- `experiments/_archived/exp04_tool_separation_deprecated/run.py` — **신규**. `run_experiment.py:run_tool_separation` 본문 이동.
- `experiments/_archived/exp04_tool_separation_deprecated/INDEX.md` — **신규**. deprecated 사유 + 격리 일자 명시.
- `experiments/exp04_tool_separation/` — **삭제** (`설명.md` 와 함께 비어진 디렉토리). 안의 `설명.md` 는 `_archived/` 의 INDEX.md 로 흡수.
- `experiments/run_experiment.py` — **수정**.
  - 4개 함수 본문 제거.
  - 상단 import 3줄 추가 (active 3개).
  - `_archived` 의 `run_tool_separation` 도 import 가능하지만 **dispatcher 에서 제거**.
  - `EXPERIMENTS` dict 의 `"tool-separation"` 항목 제거. dict 가 14 → 13 키.
- `experiments/tests/test_static.py` — **수정**.
  - `TestDispatcherIntegrity.EXPECTED_KEYS_INITIAL` 을 `EXPECTED_KEYS_AFTER_TASK_05` 로 갱신 (또는 별도 set으로 13개). `tool-separation` 제거.
  - `TestPerExperimentImports.SPLIT_EXPERIMENTS` 에 3개 active 추가.
  - `TestArchivedExperiments` 신규 TestCase — `_archived/exp04_tool_separation_deprecated/` import 가능 + dispatcher 에 없음 검증.

신규 외 다른 파일 수정 금지.

## Change description

### 패턴 (task-03·04와 동일)

3개 active 실험은 task-04 절차 그대로:
1. `expXX/__init__.py`, `expXX/run.py`, `expXX/INDEX.md` 신규.
2. `run_experiment.py` 상단 import 추가, 함수 본문 제거.
3. `EXPERIMENTS` dict 에서 키-값 그대로 (변경 없음).

`run_tool_separation` 은 별도 처리 — `_archived/` 격리 + dispatcher 에서 제거.

### 4개 실험 매핑 (line 번호는 task 시작 시점 재확인 필요)

| dispatcher key | 함수 | 원본 라인 (task-04 시점) | 새 위치 |
|----------------|------|------------------------|---------|
| `prompt-enhance` | `run_prompt_enhance` | 545-660 | `exp05a_prompt_enhance/` |
| `tool-separation` | `run_tool_separation` | 661-683 | `_archived/exp04_tool_separation_deprecated/` (dispatcher 에서 제거) |
| `handoff-protocol` | `run_handoff_protocol` | 684-776 | `exp045_handoff_protocol/` |
| `solo-budget` | `run_solo_budget` | 777-888 | `exp06_solo_budget/` |

**주의**: task-04 가 5개 함수를 제거하면서 line 번호가 위로 당겨짐. **task-05 시작 시 첫 번째 명령으로 `grep -n "^def run_" experiments/run_experiment.py` 실행하여 현재 line 번호 재확인.**

### Step 1 — 활성 실험 3개 분리 (exp05a, exp045, exp06)

task-04 패턴 그대로. 각 디렉토리에 3 파일 (init, run, INDEX) + run_experiment.py 수정.

`exp045_handoff_protocol/INDEX.md` 의 메트릭 placeholder는 `docs/plans/exp045-v2.md` (이미 abandoned 상태이지만 main에 보존됨)를 참조 가능 — 단순 링크만.

### Step 2 — `_archived/exp04_tool_separation_deprecated/` 생성

```bash
mkdir -p experiments/_archived/exp04_tool_separation_deprecated
touch experiments/_archived/__init__.py
touch experiments/_archived/exp04_tool_separation_deprecated/__init__.py
```

`run.py` 작성 — `run_tool_separation` 본문을 그대로 옮김.

`INDEX.md`:

```markdown
# 실험 4 (deprecated): Tool Separation

> **상태**: deprecated. 결과 파일 0개. 이후 abc-pipeline (exp04) 으로 대체됨.
> 격리 일자: 2026-04-25 (experiments-task-05).

## 격리 사유

(원본 함수 docstring 또는 코드 주석에서 1-2문단 추출. 또는
experiments/exp04_tool_separation/설명.md 의 내용 흡수.)

## 기존 위치

- 함수: `experiments/run_experiment.py:run_tool_separation`
- 디렉토리: `experiments/exp04_tool_separation/설명.md` (현재 삭제됨)
- dispatcher key: `tool-separation` (제거됨)

## 현재 위치

- 함수: `experiments/_archived/exp04_tool_separation_deprecated/run.py:run`
- dispatcher 에서 제거되었으므로 CLI 호출 불가. 수동 호출은 가능:
  ```python
  from _archived.exp04_tool_separation_deprecated.run import run
  run()
  ```

## 변경 이력

- 2026-04-25: experiments-task-05 으로 격리. dispatcher 에서 제거.
```

### Step 3 — `experiments/exp04_tool_separation/` 삭제

```bash
cd experiments
git rm -r exp04_tool_separation/
```

설명.md 1개만 있는 디렉토리. 내용은 `_archived/exp04_tool_separation_deprecated/INDEX.md` 로 흡수.

### Step 4 — `run_experiment.py` 수정

(1) 상단 import 영역에 3줄 추가:

```python
from exp05a_prompt_enhance.run import run as run_prompt_enhance
from exp045_handoff_protocol.run import run as run_handoff_protocol
from exp06_solo_budget.run import run as run_solo_budget
```

`run_tool_separation` 은 dispatcher 에서 제거하므로 import 안 함. (필요 시 명시적 호출자가 `_archived` 에서 직접 import.)

(2) 4개 함수 본문 제거 (line 번호는 task 시작 시점 재확인).

(3) `EXPERIMENTS` dict 에서 `"tool-separation": run_tool_separation` 라인 1개 삭제. 13개 키로 줄어듦.

```python
EXPERIMENTS = {
    "baseline": run_baseline,
    "assertion-cap": run_assertion_cap,
    "multiloop": run_multiloop,
    "error-propagation": run_error_propagation,
    "cross-validation": run_cross_validation,
    "abc-pipeline": run_abc_pipeline,
    "prompt-enhance": run_prompt_enhance,
    # "tool-separation": run_tool_separation,  # REMOVED in task-05 — see _archived/exp04_tool_separation_deprecated/
    "handoff-protocol": run_handoff_protocol,
    "solo-budget": run_solo_budget,
    "loop-saturation": run_loop_saturation,
    "tool-use": run_tool_use,
    "tool-use-refined": run_tool_use_refined,
    "longctx": run_longctx,
}
```

### Step 5 — `tests/test_static.py` 수정

(1) `TestDispatcherIntegrity` 의 `EXPECTED_KEYS_INITIAL` 을 `EXPECTED_KEYS_AFTER_TASK_05` 로 갱신 (이름 변경) 및 `tool-separation` 제거:

```python
EXPECTED_KEYS_AFTER_TASK_05 = {
    "baseline", "assertion-cap", "multiloop", "error-propagation",
    "cross-validation", "abc-pipeline", "prompt-enhance",
    "handoff-protocol", "solo-budget",
    "loop-saturation", "tool-use", "tool-use-refined", "longctx",
}
# 13 keys. tool-separation 제거됨 (deprecated).
```

`test_dispatcher_keys_match_expected` 도 갱신.

(2) `TestPerExperimentImports.SPLIT_EXPERIMENTS` 에 3개 active 추가:

```python
SPLIT_EXPERIMENTS = (
    ("exp00_baseline", "run", "run"),
    ("exp01_assertion_cap", "run", "run"),
    ("exp02_multiloop", "run", "run"),
    ("exp03_error_propagation", "run", "run"),
    ("exp035_cross_validation", "run", "run"),
    ("exp04_abc_pipeline", "run", "run"),
    ("exp05a_prompt_enhance", "run", "run"),
    ("exp045_handoff_protocol", "run", "run"),
    ("exp06_solo_budget", "run", "run"),
)
```

(3) 신규 `TestArchivedExperiments` TestCase:

```python
class TestArchivedExperiments(unittest.TestCase):
    """task-05 — _archived/ 격리 정합성"""

    def test_archived_dir_exists(self):
        archived = EXPERIMENTS_DIR / "_archived"
        self.assertTrue(archived.is_dir())
        self.assertTrue((archived / "__init__.py").exists())

    def test_deprecated_tool_separation_importable_but_not_in_dispatcher(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from _archived.exp04_tool_separation_deprecated.run import run
            self.assertTrue(callable(run))
            import run_experiment
            self.assertNotIn("tool-separation", run_experiment.EXPERIMENTS,
                             "tool-separation should be removed from dispatcher")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_old_exp04_tool_separation_dir_removed(self):
        old_dir = EXPERIMENTS_DIR / "exp04_tool_separation"
        self.assertFalse(old_dir.exists(),
                         "old exp04_tool_separation/ should be removed (content absorbed)")
```

## Dependencies

- **Task 04 완료** — 5개 ABC 계열 함수 분리 후 line 번호가 안정.
- 외부 패키지: 없음.

## Verification

```bash
# 0. line 번호 재확인 (task-04 후 stale 가능성)
grep -n "^def run_" experiments/run_experiment.py
# 기대: 9개 함수 (baseline, assertion_cap, multiloop, error_propagation, cross_validation, abc_pipeline 6개는 사라졌고 prompt_enhance ~ longctx 8개만 남음)
# task-05 시작 시 stdout 기록해서 본문 제거 시 정확한 line 사용

# 1. 신규 13 파일 (3 active × 3 + _archived 4)
test -f experiments/exp05a_prompt_enhance/__init__.py && \
test -f experiments/exp05a_prompt_enhance/run.py && \
test -f experiments/exp05a_prompt_enhance/INDEX.md && \
test -f experiments/exp045_handoff_protocol/__init__.py && \
test -f experiments/exp045_handoff_protocol/run.py && \
test -f experiments/exp045_handoff_protocol/INDEX.md && \
test -f experiments/exp06_solo_budget/__init__.py && \
test -f experiments/exp06_solo_budget/run.py && \
test -f experiments/exp06_solo_budget/INDEX.md && \
test -f experiments/_archived/__init__.py && \
test -f experiments/_archived/exp04_tool_separation_deprecated/__init__.py && \
test -f experiments/_archived/exp04_tool_separation_deprecated/run.py && \
test -f experiments/_archived/exp04_tool_separation_deprecated/INDEX.md && \
echo "OK 13 new files"

# 2. exp04_tool_separation/ 삭제 확인
test ! -d experiments/exp04_tool_separation && echo "OK exp04_tool_separation removed"

# 3. dispatcher 13 키 (tool-separation 제거됨)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
keys = set(run_experiment.EXPERIMENTS.keys())
expected = {'baseline', 'assertion-cap', 'multiloop', 'error-propagation',
            'cross-validation', 'abc-pipeline', 'prompt-enhance',
            'handoff-protocol', 'solo-budget',
            'loop-saturation', 'tool-use', 'tool-use-refined', 'longctx'}
assert keys == expected, f'mismatch: {keys ^ expected}'
print(f'OK 13 dispatcher keys (tool-separation removed)')
"

# 4. _archived 모듈 import 가능 (단 dispatcher 에 없음)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _archived.exp04_tool_separation_deprecated.run import run
assert callable(run)
import run_experiment
assert 'tool-separation' not in run_experiment.EXPERIMENTS
print('OK _archived importable, removed from dispatcher')
"

# 5. 4개 함수 본문 제거됨
cd experiments && for f in run_prompt_enhance run_tool_separation run_handoff_protocol run_solo_budget; do
  count=$(grep -c "^def $f" run_experiment.py)
  test "$count" = "0" || { echo "FAIL $f still defined"; exit 1; }
done && echo "OK 4 functions removed from run_experiment.py"

# 6. test_static.py PASS — 19 + 0 (TestArchivedExperiments 3 메소드 추가) = 22 tests
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -8
# 기대: "Ran 22 tests" (또는 그 이상) + "OK"

# 7. 9개 active split 디렉토리 모두 INDEX.md + results/ 존재
for d in exp00_baseline exp01_assertion_cap exp02_multiloop exp03_error_propagation \
         exp035_cross_validation exp04_abc_pipeline exp05a_prompt_enhance \
         exp045_handoff_protocol exp06_solo_budget; do
  test -f experiments/$d/INDEX.md || { echo "FAIL $d/INDEX.md missing"; exit 1; }
  test -d experiments/$d/results || { echo "FAIL $d/results missing"; exit 1; }
done && echo "OK 9 active split dirs intact"

# 8. CLI choices 13개 (tool-separation 빠짐 확인)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_experiment.py --help 2>&1 | grep -o "tool-separation" | head -1 || echo "OK tool-separation not in CLI"
# 기대: 출력 0 라인 (or "OK ...")

# 9. 후속 task-06 영역 함수 4개 본문 보존
cd experiments && for f in run_loop_saturation run_tool_use run_tool_use_refined run_longctx; do
  count=$(grep -c "^def $f" run_experiment.py)
  test "$count" = "1" || { echo "FAIL $f changed unexpectedly"; exit 1; }
done && echo "OK 4 task-06 functions untouched"
```

## Risks

- **line 번호 stale (반복)**: task-04 가 line 번호 변동시킴. 본 task 시작 시 재검증 필수. Verification 0번이 첫 단계.
- **dispatcher key 제거의 영향**: `tool-separation` 키가 사라지면서 `python run_experiment.py tool-separation` 호출이 KeyError. 본 plan Constraints 에 "deprecated 실험 명시적 격리 — dispatcher 에서 제거" 명시되어 있으므로 의도된 동작. 단 외부 문서·script 가 이 키를 참조하면 깨짐. 검색: `grep -rn "tool-separation" experiments/ docs/` 로 확인. 본 plan 범위 밖에서 참조 시 영향 표면화.
- **`_archived/` 명명 컨벤션**: 이후 다른 deprecated 실험 격리 시 같은 패턴 사용. `_` prefix 는 Python 컨벤션상 internal/non-public 의미.
- **EXPECTED_KEYS_AFTER_TASK_05 명명**: 본 task 후 dispatcher 키 셋이 안정됨 (task-06 은 함수 이동만, 키 보존). 따라서 task-06 verification 도 같은 set 사용. 별도 변수명 갱신 불필요.
- **헬퍼 함수 누락 (반복)**: 4개 함수 본문 분석 시 의존 식별자 누락 시 ImportError. 작성자는 line 단위 정독.
- **graph data 영향**: `run_tool_separation` 가 dispatcher 에서 사라져 dead code 로 보일 수 있음. `_archived/` 안의 함수로 옮겨졌으므로 git history 추적 가능. 위험 1/10.
- **결과 파일 확인 — exp04_abc_pipeline 결과는 task-04 영역**: `exp04_abc_pipeline_*.json` 1개 결과 파일은 이미 task-02 에서 분류. `exp04_tool_separation` 은 결과 0개라 분류 대상 없음.

## Scope boundary

**Task 05에서 절대 수정 금지**:

- `experiments/run_experiment.py` 의 task-06 영역 함수 4개 (`run_loop_saturation`, `run_tool_use`, `run_tool_use_refined`, `run_longctx`).
- `experiments/exp00_baseline/` ~ `exp04_abc_pipeline/` (task-03·04 영역).
- `experiments/exp07_loop_saturation/`, `exp08_tool_use/`, `exp08b_tool_use_refined/`, `exp09_longctx/` (task-06 영역. 본 task에서는 결과 디렉토리만 task-02에서 만들어진 상태).
- 공용 모듈 (`orchestrator.py`, `schema.py` 등).
- `experiments/INDEX.md` (task-07 갱신 영역).
- `experiments/_template/`.
- `docs/plans/*` — 본 task 외 plan 문서.

**허용 범위**:

- `exp05a_prompt_enhance/`, `exp045_handoff_protocol/`, `exp06_solo_budget/` 3개 active 디렉토리에 `__init__.py`·`run.py`·`INDEX.md` 신규.
- `_archived/exp04_tool_separation_deprecated/` 신규 (`__init__.py` × 2 + `run.py` + `INDEX.md` 4파일).
- `experiments/exp04_tool_separation/` 디렉토리 통째 삭제.
- `experiments/run_experiment.py` 의 4개 함수 본문 제거 + 상단 import 3줄 추가 + `EXPERIMENTS` dict 의 `"tool-separation"` 1줄 제거.
- `experiments/tests/test_static.py` 의 `EXPECTED_KEYS_*` 갱신 + `SPLIT_EXPERIMENTS` 확장 + `TestArchivedExperiments` 신규.
