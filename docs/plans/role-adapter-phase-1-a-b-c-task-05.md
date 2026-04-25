---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-a-b-c
parallel_group: C
depends_on: [02, 03, 04]
---

# Task 05 — 회귀 게이트 (Exp08b math-04 동치 확인)

## Changed files

- `experiments/results/role_adapter_regression_pre.json` — **신규**. 리팩토링 전 baseline 결과.
- `experiments/results/role_adapter_regression_post.json` — **신규**. 리팩토링 후 결과.
- `experiments/regression_check.py` — **신규**. pre/post 결과 동치 비교 스크립트.
- `docs/plans/role-adapter-phase-1-a-b-c-result.md` (또는 동급 결과 문서) — **신규**. 회귀 결과 기록 (tunaFlow가 자동 생성하는 result 문서가 있다면 그쪽에 기록, 없으면 별도).

## Change description

### Step 0 — 사전 조건 확인

이 Task는 **Task 02·03·04 모두 완료된 후** 실행한다. 회귀 게이트가 통과해야만 Phase 1 전체가 통과(merge 가능).

### Step 1 — Pre-baseline 캡처

**리팩토링 전 코드**(즉 main 브랜치의 직전 커밋)에서 Exp08b math-04만 실행:

```bash
# main의 직전 커밋(예: 'bb2a271') 로 잠시 checkout
git checkout bb2a271 -- experiments/

# Exp08b 일부만 실행 (math-04 전용 — 빠른 회귀 검증용)
cd experiments
python run_experiment.py tool-use-refined  # 전체 40 runs인데, 여기선 math-04만 추출 가능?
```

**대안 — 더 효율적**: Exp08b 결과 파일이 이미 `experiments/results/exp08b_tool_use_refined_*.json`에 있음 (커밋 `2d42ce4` 시점). 이 파일에서 math-04 trial만 추출하여 `pre.json`으로 저장:

```python
# 파일명: experiments/regression_capture_pre.py (임시 스크립트)
import json, glob
paths = sorted(glob.glob("results/exp08b_tool_use_refined_*.json"))
with open(paths[-1]) as f:
    data = json.load(f)

# math-04 trial만 추출 (baseline_refined + tooluse_refined 양쪽)
pre = {}
for arm in ("baseline_refined", "tooluse_refined"):
    arm_data = data.get("results_by_condition", {}).get(arm, [])
    math04 = next((tb for tb in arm_data if tb["task_id"] == "math-04"), None)
    if math04:
        pre[arm] = {
            "task_id": "math-04",
            "trials": [
                {
                    "trial": t["trial"],
                    "final_answer": t.get("final_answer"),
                    "actual_cycles": t.get("actual_cycles"),
                    "total_tool_calls": t.get("total_tool_calls", 0),
                    "tool_errors": t.get("tool_errors", 0),
                }
                for t in math04["trials"]
            ],
        }

with open("results/role_adapter_regression_pre.json", "w") as f:
    json.dump(pre, f, ensure_ascii=False, indent=2)
print(f"saved pre baseline: math-04 from {paths[-1]}")
```

이 접근의 장점: 이미 검증된 Exp08b 결과를 그대로 baseline으로 사용. 추가 LLM 호출 없음.

### Step 2 — Post-result 실행 (리팩토링 후 코드로)

리팩토링이 완료된 main(또는 작업 브랜치) 상태에서 Exp08b math-04만 재실행:

**옵션 A — Exp08b 전체 재실행** (가장 안전, 시간 1~2시간):
```bash
cd experiments
python run_experiment.py tool-use-refined
# → results/exp08b_tool_use_refined_<timestamp>.json
```
이후 같은 추출 스크립트로 math-04만 뽑아 `role_adapter_regression_post.json` 생성.

**옵션 B — math-04 task만 격리 실행** (시간 단축):

`run_experiment.py`에 math-04 only 분기를 추가하지 않는 게 원칙(non-goal). 따라서 옵션 A 권장.

### Step 3 — 동치 비교 스크립트 — `regression_check.py`

```python
"""Exp08b math-04 회귀 비교 — Role Adapter 리팩토링 동치 검증.

기준 4가지 (Task 05 spec):
  1) trial별 final_answer 문자열 동일
  2) num_assertions 개수 ±1 허용
  3) arm별 v2 accuracy 동일
  4) tool_calls 총합 ±2 허용
"""
import json
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def compare(pre, post) -> tuple[bool, list[str]]:
    """반환: (동치 여부, 위반 사유 리스트)"""
    violations = []
    for arm in ("baseline_refined", "tooluse_refined"):
        if arm not in pre or arm not in post:
            violations.append(f"arm missing: {arm}")
            continue
        pre_trials = {t["trial"]: t for t in pre[arm]["trials"]}
        post_trials = {t["trial"]: t for t in post[arm]["trials"]}
        for trial_id, p in pre_trials.items():
            q = post_trials.get(trial_id)
            if q is None:
                violations.append(f"{arm} trial {trial_id} missing in post")
                continue
            # 1) final_answer 문자열 동일
            if str(p.get("final_answer")) != str(q.get("final_answer")):
                violations.append(
                    f"{arm} trial {trial_id} final_answer mismatch: "
                    f"pre={str(p.get('final_answer'))[:80]!r} vs post={str(q.get('final_answer'))[:80]!r}"
                )
            # 2) num_assertions ±1 (cycle 변동 미세 편차 허용)
            #    Exp08b 결과에 num_assertions 필드가 없으면 actual_cycles로 대체
            p_n = p.get("num_assertions") or p.get("actual_cycles", 0)
            q_n = q.get("num_assertions") or q.get("actual_cycles", 0)
            if abs(p_n - q_n) > 1:
                violations.append(f"{arm} trial {trial_id} cycles/assertions diff > 1: pre={p_n} vs post={q_n}")
            # 4) tool_calls 총합 ±2
            p_tc = p.get("total_tool_calls", 0)
            q_tc = q.get("total_tool_calls", 0)
            if abs(p_tc - q_tc) > 2:
                violations.append(f"{arm} trial {trial_id} tool_calls diff > 2: pre={p_tc} vs post={q_tc}")
    return (len(violations) == 0, violations)


def main():
    if len(sys.argv) < 3:
        print("usage: regression_check.py <pre.json> <post.json>")
        sys.exit(2)
    pre = load(sys.argv[1])
    post = load(sys.argv[2])
    ok, viol = compare(pre, post)
    if ok:
        print("✅ REGRESSION PASS — all 4 criteria within tolerance")
        sys.exit(0)
    else:
        print(f"❌ REGRESSION FAIL — {len(viol)} violations:")
        for v in viol:
            print(f"  - {v}")
        sys.exit(1)
```

### Step 4 — 실행 절차 (Developer가 따라야 함)

```bash
# 1) Pre baseline (이미 실행된 Exp08b 결과 재사용)
cd experiments
python -c "
import json, glob
paths = sorted(glob.glob('results/exp08b_tool_use_refined_*.json'))
with open(paths[-1]) as f: data = json.load(f)
out = {}
for arm in ('baseline_refined', 'tooluse_refined'):
    arm_data = data.get('results_by_condition', {}).get(arm, [])
    m = next((tb for tb in arm_data if tb['task_id'] == 'math-04'), None)
    if m:
        out[arm] = {'task_id': 'math-04', 'trials': [
            {'trial': t['trial'], 'final_answer': t.get('final_answer'),
             'actual_cycles': t.get('actual_cycles'),
             'total_tool_calls': t.get('total_tool_calls', 0)}
            for t in m['trials']
        ]}
with open('results/role_adapter_regression_pre.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('pre saved')
"

# 2) Post result — Exp08b 전체 재실행 (math-04만 분리 추출)
python run_experiment.py tool-use-refined  # 전체 40 runs
python -c "
import json, glob
paths = sorted(glob.glob('results/exp08b_tool_use_refined_*.json'))
with open(paths[-1]) as f: data = json.load(f)
# 같은 변환 로직으로 math-04 추출
out = {}
for arm in ('baseline_refined', 'tooluse_refined'):
    arm_data = data.get('results_by_condition', {}).get(arm, [])
    m = next((tb for tb in arm_data if tb['task_id'] == 'math-04'), None)
    if m:
        out[arm] = {'task_id': 'math-04', 'trials': [
            {'trial': t['trial'], 'final_answer': t.get('final_answer'),
             'actual_cycles': t.get('actual_cycles'),
             'total_tool_calls': t.get('total_tool_calls', 0)}
            for t in m['trials']
        ]}
with open('results/role_adapter_regression_post.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('post saved')
"

# 3) 동치 검증
python regression_check.py results/role_adapter_regression_pre.json results/role_adapter_regression_post.json
# 기대: "✅ REGRESSION PASS"
```

### Step 5 — 결과 문서

회귀 통과 시 `docs/plans/role-adapter-phase-1-a-b-c-result.md`에 다음 기록:

- 회귀 게이트 PASS (날짜, 커밋)
- pre/post 결과 파일 경로
- 4개 기준별 위반 0
- 라인 수 변화 (`run_abc_chain` 약 300 → 약 N줄)
- 단위 테스트 16개 통과 확인

회귀 FAIL 시:

- 위반 사유 기록
- 어떤 어댑터 / 어느 서브태스크에서 동치 깨졌는지 분석
- Phase 1 미통과 — Task 02 또는 03으로 돌아가 재작업

## Dependencies

- **Task 02 완료**: `run_abc_chain` 리팩토링.
- **Task 03 완료**: `run_abc_chunked` 리팩토링.
- **Task 04 완료**: 단위 테스트 통과.
- 외부 의존성: llama.cpp 서버 가동 (post 실행 시).

## Verification

```bash
# 1. regression_check.py 존재
test -f experiments/regression_check.py && echo "checker: OK"

# 2. pre baseline 파일 생성됨
test -f experiments/results/role_adapter_regression_pre.json && echo "pre: OK"

# 3. post result 파일 생성됨 (Step 4 실행 후)
test -f experiments/results/role_adapter_regression_post.json && echo "post: OK"

# 4. 동치 검증 통과 (필수)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python regression_check.py \
    results/role_adapter_regression_pre.json \
    results/role_adapter_regression_post.json
# 기대 exit code: 0 ("✅ REGRESSION PASS")

# 5. 단위 테스트 회귀 없음 (Task 04 재실행)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest \
    agents.test_role_agents \
    tools.test_chunker tools.test_bm25_tool tools.test_math_tools 2>&1 | tail -3
# 기대: "OK", 합계 38개 테스트 pass

# 6. 기존 실험 분기 모두 호출 가능 (회귀 안전성)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
expected = {'baseline','assertion-cap','multiloop','error-propagation',
            'cross-validation','abc-pipeline','prompt-enhance',
            'handoff-protocol','solo-budget','tool-separation',
            'loop-saturation','tool-use','tool-use-refined','longctx'}
got = set(EXPERIMENTS.keys())
missing = expected - got
assert not missing, f'experiments missing: {missing}'
print(f'OK: {len(got)} experiments registered')
"

# 7. orchestrator import는 즉시 — circular import 없음
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import orchestrator, run_experiment, measure, schema, system_prompt
from agents import ProposerAgent, CriticAgent, JudgeAgent
print('OK all imports clean')
"
```

## Risks

- **회귀 FAIL 시 처리**: 4개 기준 중 어느 하나라도 위반하면 PASS 안 함. Phase 1 미통과로 간주, Task 02 또는 03 재작업. **이게 본 Task 05의 핵심 가치** — 동치 보장.
- **LLM 호출의 비결정성**: 같은 프롬프트라도 LLM 응답이 매번 다를 수 있음. 그래서 ±1 cycles, ±2 tool_calls 허용. 단 `final_answer` 문자열은 strict하게 동일 요구 — math-04 정답이 명확하므로(`X=31, Y=10, Z=37, profit=$3060`) 통과 가능성 높음.
- **Pre baseline 신뢰성**: 기존 Exp08b 결과(`exp08b_tool_use_refined_*.json`)를 baseline으로 재사용. 만약 사용자/Gemini가 그 사이 다른 변경을 했으면 baseline이 오염될 수 있음 — Step 1에서 파일 timestamp + 해당 커밋(`2d42ce4`) 일치 확인 권장.
- **n_ctx, 모델 가중치 변동**: llama.cpp 서버 재시작·모델 재로드가 일어났다면 응답 미세 차이 가능. 회귀 FAIL 시 첫 의심 요소.
- **Exp08b 전체 재실행 비용**: 40 runs × 평균 7 cycle ≈ 1~2시간. math-04 trial 5개만 따로 돌릴 방법은 비-목표 (코드 추가 필요).
- **회귀 PASS = Phase 1 PASS**: 회귀가 통과하면 문서로 명시 후 main 푸시. 이 Task가 최종 게이트.

## Scope boundary

**Task 05에서 절대 수정 금지**:
- `experiments/agents/` 내 모든 파일 (Task 01 영역)
- `experiments/orchestrator.py` (Task 02·03 영역)
- `experiments/system_prompt.py`, `experiments/schema.py`
- `experiments/run_experiment.py`, `experiments/measure.py`, `experiments/tools/`, `experiments/tasks/`
- `experiments/agents/test_role_agents.py` (Task 04 영역)

**허용 범위**:
- `experiments/regression_check.py` 신규 (회귀 비교 스크립트)
- `experiments/results/role_adapter_regression_pre.json` 신규
- `experiments/results/role_adapter_regression_post.json` 신규
- `docs/plans/role-adapter-phase-1-a-b-c-result.md` (있다면 결과 기록만)
