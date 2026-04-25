---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: C
depends_on: [05]
---

# Task 06 — 후속 실험 4개 분리 (loop-saturation·tool-use·tool-use-refined·longctx)

## Changed files

4개 후속 실험을 task-04·05 패턴 그대로 분리. 모두 active. 키·값 변경 없음.

- `experiments/exp07_loop_saturation/__init__.py` — **신규**.
- `experiments/exp07_loop_saturation/run.py` — **신규**. `run_experiment.py:run_loop_saturation` 본문 이동 (line 번호는 task-05 후 재확인).
- `experiments/exp07_loop_saturation/INDEX.md` — **신규**.
- `experiments/exp08_tool_use/__init__.py` — **신규**.
- `experiments/exp08_tool_use/run.py` — **신규**. `run_experiment.py:run_tool_use` 본문 이동.
- `experiments/exp08_tool_use/INDEX.md` — **신규**.
- `experiments/exp08b_tool_use_refined/__init__.py` — **신규**.
- `experiments/exp08b_tool_use_refined/run.py` — **신규**. `run_experiment.py:run_tool_use_refined` 본문 이동.
- `experiments/exp08b_tool_use_refined/INDEX.md` — **신규**.
- `experiments/exp09_longctx/__init__.py` — **신규**.
- `experiments/exp09_longctx/run.py` — **신규**. `run_experiment.py:run_longctx` 본문 이동.
- `experiments/exp09_longctx/INDEX.md` — **신규**.
- `experiments/run_experiment.py` — **수정**. 4개 함수 본문 제거 + 상단 import 4줄 추가.
- `experiments/tests/test_static.py` — **수정**. `TestPerExperimentImports.SPLIT_EXPERIMENTS` 에 4개 추가 (총 13개 active).

신규 외 다른 파일 수정 금지.

## Change description

### 패턴

task-04·05와 완전 동일.

### 4개 실험 매핑

| dispatcher key | 함수 | 새 디렉토리 | 결과 파일 |
|----------------|------|-------------|----------|
| `loop-saturation` | `run_loop_saturation` | `exp07_loop_saturation/` | exp07 JSON 1 + report.md |
| `tool-use` | `run_tool_use` | `exp08_tool_use/` | exp08 JSON 1 + report.md |
| `tool-use-refined` | `run_tool_use_refined` | `exp08b_tool_use_refined/` | exp08b JSON 1 + report.md |
| `longctx` | `run_longctx` | `exp09_longctx/` | exp09 JSON 1 + report.md |

본 task 후, **`experiments/run_experiment.py` 안에 `^def run_` 매칭 0건**이 되어야 한다. 14개 함수 모두 분리 완료.

### Step 1 — line 번호 재확인 (필수)

```bash
grep -n "^def run_" experiments/run_experiment.py
```

task-05 후 남은 함수 4개의 정확한 line 번호 확인. 본 task 작업 시 line 번호 큰 함수부터 (= `run_longctx` 부터) 제거하면 line 번호 안정.

### Step 2 — 4개 디렉토리 분리

각각 `__init__.py`, `run.py`, `INDEX.md` 신규. 결과 파일은 task-02에서 이미 `expXX/results/` 로 이동되어 있음.

`exp08b_tool_use_refined/INDEX.md`:

```markdown
# 실험 8b: Tool-Use Refinement (에러 메시지 + Prompt 강화)

## 개요

(원본 docstring 또는 docs/plans/exp08b-tool-use-refinement-prompt.md
[abandoned 처리됨, main 보존] 의 내용 1-2문단 흡수)

핵심 가설: H8 — 도구 호출 에러 메시지 명료화로 정답률 개선.
결과: math-04 100% 달성.

## dispatcher key

`tool-use-refined`

## 결과 파일

- `results/exp08b_tool_use_refined_20260424_234043.json`
- `results/exp08b_report.md`

## 핵심 메트릭

| 조건 | 정답률 | 핵심 메모 |
|------|-------|----------|
| baseline_refined | TBD | exp08b_report.md 참조 |
| tooluse_refined | TBD | exp08b_report.md 참조 |

(메트릭은 결과 JSON·report 분석으로 채울 수 있음. 본 task 범위에서는
링크만 명시.)

## 변경 이력

- 2026-04-24: 실험 실행 (Exp08b 완주, math-04 100%).
- 2026-04-25: experiments-task-06 으로 분리.
```

`exp09_longctx/INDEX.md` 등 나머지 3개도 같은 패턴.

### Step 3 — `run_experiment.py` 수정

상단 import 영역에 4줄 추가:

```python
from exp07_loop_saturation.run import run as run_loop_saturation
from exp08_tool_use.run import run as run_tool_use
from exp08b_tool_use_refined.run import run as run_tool_use_refined
from exp09_longctx.run import run as run_longctx
```

4개 함수 본문 제거.

`EXPERIMENTS` dict 그대로 (13개 키, 본 task에서는 변경 없음).

### Step 4 — `tests/test_static.py` 의 `SPLIT_EXPERIMENTS` 최종 확장

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
    ("exp07_loop_saturation", "run", "run"),
    ("exp08_tool_use", "run", "run"),
    ("exp08b_tool_use_refined", "run", "run"),
    ("exp09_longctx", "run", "run"),
)  # 13 active experiments
```

또한 신규 TestCase `TestNoLegacyRunFunctions` 추가:

```python
class TestNoLegacyRunFunctions(unittest.TestCase):
    """task-06 후 — run_experiment.py 본문에 def run_* 가 0개"""

    def test_no_legacy_run_functions_in_dispatcher(self):
        run_exp = EXPERIMENTS_DIR / "run_experiment.py"
        text = run_exp.read_text(encoding="utf-8")
        legacy = re.findall(r"^def run_\w+\s*\(", text, flags=re.M)
        self.assertEqual(legacy, [],
                         f"run_experiment.py still has legacy run_* defs: {legacy}")
```

## Dependencies

- **Task 05 완료** — handoff·prompt·solo 분리 + tool-separation deprecated 격리 후.
- 외부 패키지: 없음.

## Verification

```bash
# 0. line 번호 재확인 (반복)
grep -n "^def run_" experiments/run_experiment.py
# task-05 후 4개 함수 (loop_saturation, tool_use, tool_use_refined, longctx) 만 남아 있어야 함

# 1. 신규 12 파일 (4 active × 3)
test -f experiments/exp07_loop_saturation/__init__.py && \
test -f experiments/exp07_loop_saturation/run.py && \
test -f experiments/exp07_loop_saturation/INDEX.md && \
test -f experiments/exp08_tool_use/__init__.py && \
test -f experiments/exp08_tool_use/run.py && \
test -f experiments/exp08_tool_use/INDEX.md && \
test -f experiments/exp08b_tool_use_refined/__init__.py && \
test -f experiments/exp08b_tool_use_refined/run.py && \
test -f experiments/exp08b_tool_use_refined/INDEX.md && \
test -f experiments/exp09_longctx/__init__.py && \
test -f experiments/exp09_longctx/run.py && \
test -f experiments/exp09_longctx/INDEX.md && \
echo "OK 12 new files"

# 2. 4개 신규 모듈 import 가능
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp07_loop_saturation.run import run as r1
from exp08_tool_use.run import run as r2
from exp08b_tool_use_refined.run import run as r3
from exp09_longctx.run import run as r4
for r in (r1, r2, r3, r4):
    assert callable(r)
print('OK 4 modules callable')
"

# 3. run_experiment.py 의 4개 함수 본문 제거됨
cd experiments && for f in run_loop_saturation run_tool_use run_tool_use_refined run_longctx; do
  count=$(grep -c "^def $f" run_experiment.py)
  test "$count" = "0" || { echo "FAIL $f still defined"; exit 1; }
done && echo "OK 4 functions removed"

# 4. **결정적 검증** — run_experiment.py 본문에 ^def run_ 가 0개
count=$(grep -c "^def run_" experiments/run_experiment.py)
test "$count" = "0" && echo "OK 0 legacy run_* in run_experiment.py" || echo "FAIL: $count remain"

# 5. 13 dispatcher 키 그대로 (변경 없음)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
keys = set(run_experiment.EXPERIMENTS.keys())
assert len(keys) == 13, f'expected 13, got {len(keys)}'
print('OK 13 dispatcher keys preserved')
"

# 6. test_static.py PASS — 22 + 1 (TestNoLegacyRunFunctions) = 23 tests
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -10
# 기대: "Ran 23 tests" (또는 그 이상) + "OK"

# 7. 13개 active split 디렉토리 모두 INDEX.md + results/ 존재
for d in exp00_baseline exp01_assertion_cap exp02_multiloop exp03_error_propagation \
         exp035_cross_validation exp04_abc_pipeline exp05a_prompt_enhance \
         exp045_handoff_protocol exp06_solo_budget \
         exp07_loop_saturation exp08_tool_use exp08b_tool_use_refined exp09_longctx; do
  test -f experiments/$d/INDEX.md || { echo "FAIL $d/INDEX.md missing"; exit 1; }
  test -d experiments/$d/results || { echo "FAIL $d/results missing"; exit 1; }
done && echo "OK 13 active split dirs intact"

# 8. exp08b INDEX.md 가 결과 + report 링크 보유
grep -q "exp08b_tool_use_refined_20260424_234043.json" experiments/exp08b_tool_use_refined/INDEX.md && \
grep -q "exp08b_report.md" experiments/exp08b_tool_use_refined/INDEX.md && \
echo "OK exp08b INDEX has both result + report links"

# 9. run_experiment.py 라인 수 — task-06 후 약 200~300 라인 예상 (dispatcher + import + main + helpers)
wc -l experiments/run_experiment.py
# 기대: ≤ 300

# 10. CLI choices 13개 그대로
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_experiment.py --help 2>&1 | grep -oE "(baseline|assertion-cap|multiloop|error-propagation|cross-validation|abc-pipeline|prompt-enhance|handoff-protocol|solo-budget|loop-saturation|tool-use|tool-use-refined|longctx)" | sort -u | wc -l
# 기대: 13
```

## Risks

- **line 번호 stale (반복)**: task-05 후 line 변동. Verification 0번이 첫 단계.
- **헬퍼 함수 누락 (반복)**: 4개 함수 분석 시 의존 식별자 누락 시 ImportError. 본 task가 마지막 분리 task 이므로 매우 중요.
- **공용 헬퍼 추출 미루기**: 14개 함수가 공유하는 헬퍼 (예: `_load_tasks`, `score_answer_v2 wrapper`) 가 있다면, 본 task에서는 각 run.py 가 중복으로 갖거나 `run_experiment.py` 에 그대로 둔다. 공용 모듈로의 추출은 task-07 또는 별도 plan.
- **`run_experiment.py` 본문에 헬퍼 함수만 남는 경우**: 14개 `run_*()` 모두 제거 후 dispatcher + import + main + 헬퍼들만 남음. task-07 에서 dispatcher 슬림화 시 헬퍼 처리 결정 (그대로 두기 vs 공용 모듈로 빼기).
- **graph data 증가**: code-review-graph 가 14개 새 모듈 분석. 분석 시간 증가하지만 동작 변화 없음.

## Scope boundary

**Task 06에서 절대 수정 금지**:

- `experiments/run_experiment.py` 의 dispatcher dict, main, argparse, 상단 import 외 영역 (예: 헬퍼 함수가 있다면 task-07 영역).
- `experiments/exp00_baseline/` ~ `exp06_solo_budget/`, `_archived/` (task-03~05 영역).
- 공용 모듈 (`orchestrator.py`, `schema.py` 등).
- `experiments/INDEX.md` (task-07 갱신 영역).
- `experiments/_template/`.
- `docs/plans/*` — 본 task 외 plan 문서.

**허용 범위**:

- `exp07_loop_saturation/`, `exp08_tool_use/`, `exp08b_tool_use_refined/`, `exp09_longctx/` 4개 디렉토리에 `__init__.py`·`run.py`·`INDEX.md` 신규.
- `experiments/run_experiment.py` 의 4개 함수 본문 제거 + 상단 import 4줄 추가.
- `experiments/tests/test_static.py` 의 `SPLIT_EXPERIMENTS` 4개 추가 + `TestNoLegacyRunFunctions` 신규.
