---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: stage-6-cross-model-llm-as-judge
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — `experiments/cross_model/run.py` driver

## Changed files

- `experiments/cross_model/__init__.py` — **신규**
- `experiments/cross_model/run.py` — **신규**. Stage 5 4 가설 (H10/H11/H12/H13) × 다중 모델 (Local Qwen + Groq Llama 8B/70B) 재현 driver. LLM-as-judge 보조 채점 옵션 통합
- `experiments/cross_model/results/.gitkeep` — **신규**

신규 3.

## Change description

### 배경

task-01 의 LLM-as-judge 인프라 + task-02 의 model_caller hook 위에서 cross-model driver. **scope 가 큼** — 4 가설 × 3 모델 × N task × 5 trial. 분할 실행 가능 design 의무.

`gemento-experiment-scaffold` 스킬 활용 권장 — 단 본 plan 은 *기존 Exp11/12/13/14 의 run.py 호출* 이므로 패턴 다름.

### Step 1 — 디렉토리

```bash
mkdir -p experiments/cross_model/results
touch experiments/cross_model/__init__.py
touch experiments/cross_model/results/.gitkeep
```

### Step 2 — 모델 설정 dict

```python
"""Stage 6 cross-model replication driver."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._external.groq_client import (
    call_with_meter_retry,
    LLAMA_3_1_8B, LLAMA_3_3_70B,
)
from experiments._external.llm_judge import judge_answer, compare_answers


# Local Qwen 의 LM Studio endpoint — 사용자 환경별 변경
LOCAL_QWEN_ENDPOINT = "http://localhost:1235"  # 또는 192.168.1.179:1235
LOCAL_QWEN_MODEL_ID = "qwen-2.5-7b-q4"  # /v1/models 에서 확인

MODELS = {
    "qwen_25_7b_local": {
        "provider": "lm_studio_local",
        "endpoint": LOCAL_QWEN_ENDPOINT,
        "model_id": LOCAL_QWEN_MODEL_ID,
        "context": 32768,
        "supports_longctx": True,
    },
    "llama_3_1_8b_groq": {
        "provider": "groq",
        "model_id": LLAMA_3_1_8B,
        "context": 8192,    # Groq free tier 한계
        "supports_longctx": False,  # longctx_taskset 부적합
    },
    "llama_3_3_70b_groq": {
        "provider": "groq",
        "model_id": LLAMA_3_3_70B,
        "context": 131072,
        "supports_longctx": True,
    },
}
```

### Step 3 — `model_caller` factory

```python
def make_groq_caller(model_id: str):
    """Groq API 호출을 model_caller 형식 (messages, **kwargs) → (str, dict) 으로 wrap."""
    def _caller(messages, tools=None, tool_functions=None, **kwargs):
        result = call_with_meter_retry(
            messages, model=model_id, tools=tools, **kwargs
        )
        meta = {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "duration_ms": result.duration_ms,
            "cost_usd": result.cost_usd,
            "error": result.error,
            "reasoning_tokens": result.reasoning_tokens,
        }
        return result.raw_response, meta
    return _caller


def make_local_caller(endpoint: str, model_id: str):
    """Local LM Studio 의 별도 endpoint 호출. 기존 call_model 패턴 재사용."""
    # 단순 구현: API_BASE_URL 환경변수 임시 변경 OR 직접 httpx 호출
    # Architect 추천: 직접 httpx 호출 (call_model 의 endpoint 의존성 회피)
    from experiments._external.groq_client import call_with_meter as _generic_call
    def _caller(messages, **kwargs):
        # OpenAI-compatible local endpoint — Groq client 의 endpoint override
        result = _generic_call(
            messages, model=model_id, base_url=endpoint + "/v1/chat/completions",
            **kwargs,
        )
        meta = {...}
        return result.raw_response, meta
    return _caller
```

**중요 — Sonnet 진행 시**:
- `make_local_caller` 의 정확한 구현은 task-01 의 groq_client.py 가 `base_url` 인자 받는지 확인 후 결정
- 만약 받지 않으면 → `experiments/_external/lm_studio_client.py` 신규 client (별도 task 또는 본 task 안)
- 또는 LM Studio 가 여러 모델 동시 로드 안 하므로 `MODEL_NAME` 변경 + 같은 endpoint 사용 옵션

### Step 4 — 가설 재현 함수

각 가설 별 재현 함수 — Exp11/12/13/14 의 `run_*` 함수 패턴 재사용 + `model_caller` 주입.

```python
def reproduce_h11_extractor(model_key: str, task: dict, trial_idx: int) -> dict:
    """Exp12 의 baseline_abc + extractor_abc 재현 with cross-model."""
    from experiments.exp12_extractor_role.run import (
        run_baseline_abc, run_extractor_abc,
    )
    # 단 Exp12 의 run_*_abc 가 model_caller 인자 받도록 *수정 필요* —
    # Architect 결정: Exp12 run.py 변경 금지 (Stage 5 결과 보존), 따라서
    # 본 task 에서 *재구현* — Exp12 의 로직을 cross_model/run.py 에 복사 + model_caller 주입

    # 또는: run_abc_chain 직접 호출 (Exp12 run.py 우회)
    from orchestrator import run_abc_chain
    model_caller = _get_model_caller(model_key)

    # baseline_abc
    baseline_result = run_abc_chain(
        task_id=f"{task['id']}_{model_key}_baseline_t{trial_idx}",
        objective=task["objective"], prompt=task["prompt"],
        # ... Exp12 baseline 동일 인자
        extractor_pre_stage=False,
        model_caller=model_caller,
    )
    # extractor_abc
    extractor_result = run_abc_chain(
        ...,
        extractor_pre_stage=True,
        model_caller=model_caller,
    )
    return {"baseline": baseline_result, "extractor": extractor_result}


# H10 / H12 / H13 도 유사 패턴
def reproduce_h10_mixed(model_key, task, trial_idx): ...
def reproduce_h12_reducer(model_key, task, trial_idx): ...
def reproduce_h13_search(model_key, task, trial_idx): ...
```

### Step 5 — main + argparse

```python
def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 6 cross-model replication")
    parser.add_argument("--model", required=True,
                        choices=list(MODELS.keys()),
                        help="대상 모델 (qwen_25_7b_local / llama_3_1_8b_groq / llama_3_3_70b_groq)")
    parser.add_argument("--hypothesis", nargs="+", required=True,
                        choices=["h10", "h11", "h12", "h13"],
                        help="재현할 Stage 5 가설")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="task_id filter")
    parser.add_argument("--out-name", default=None)
    parser.add_argument("--judge", action="store_true",
                        help="LLM-as-judge 보조 채점 활성 (H12/H13 권장)")
    args = parser.parse_args()
    # ... run + save
```

### Step 6 — LLM-as-judge 통합 (옵션)

`--judge` 활성 시 trial 결과의 baseline / treatment 답변 페어를 GPT-OSS 120B 로 비교:

```python
if args.judge:
    from experiments._external.llm_judge import compare_answers
    import random
    for trial in trials:
        # order randomization
        if random.random() < 0.5:
            answer_A = trial["baseline_final_answer"]
            answer_B = trial["treatment_final_answer"]
            order = "baseline_first"
        else:
            answer_A = trial["treatment_final_answer"]
            answer_B = trial["baseline_final_answer"]
            order = "treatment_first"
        verdict = compare_answers(
            question=trial["task_question"],
            expected_answer=trial["expected_answer"],
            answer_A=answer_A, answer_B=answer_B,
        )
        trial["judge_verdict"] = verdict
        trial["judge_order"] = order
```

## Dependencies

- task-01 (Groq client + llm_judge)
- task-02 (orchestrator model_caller hook)
- 기존 `experiments/exp11~14/run.py` — read-only 참조 (로직 패턴)
- 기존 `experiments/system_prompt.py` (Extractor / Reducer prompts) — read-only
- 기존 `experiments/tools/bm25_tool.py` (Search Tool) — read-only

## Verification

```bash
# 1) syntax + help
.venv/Scripts/python -m py_compile experiments/cross_model/run.py
.venv/Scripts/python -m experiments.cross_model.run --help

# 2) MODELS dict 정확성
.venv/Scripts/python -c "
from experiments.cross_model.run import MODELS
for k, v in MODELS.items():
    assert 'provider' in v
    assert 'context' in v
print(f'MODELS ok: {list(MODELS.keys())}')
"

# 3) reproduce_h12_reducer 의 model_caller 주입 검증
.venv/Scripts/python -c "
import inspect
from experiments.cross_model.run import reproduce_h12_reducer
src = inspect.getsource(reproduce_h12_reducer)
assert 'model_caller' in src
assert 'reducer_post_stage' in src
print('verification 3 ok: H12 reducer with model_caller')
"

# 4) (Sonnet 직접 실행 금지) — task-04 의 dry-run 단계
```

3 명령 모두 정상.

## Risks

- **Risk 1 — Exp11/12/13/14 의 run.py 변경 유혹**: 본 task 영역 외. cross_model/run.py 에 *재구현* 또는 `run_abc_chain` 직접 호출. Stage 5 결과 보존 의무
- **Risk 2 — model_caller 의 tool-calling 호환**: Local Qwen Q4 의 `tool_calls` 응답 신뢰성. H7/H8 (Tool axis) 재현 안 함이므로 단순 chat 만 — 호환성 영향 작음. 단 H13 (Search Tool) 시 호환 필수
- **Risk 3 — Llama 3.1 8B 의 8K context 한계**: H13 의 longctx_taskset 부적합. cross_model run 시 model 별 task filter 자동 적용 (`MODELS[k]['supports_longctx']`)
- **Risk 4 — 시간 초과**: 3 model × 4 가설 × 15 task × 5 trial = ~900 trial. Local Qwen ~30s/trial, Groq ~5s/trial. Local 이 ~7-8h, Groq 둘 합 ~2h. 단 Groq 1000 RPD 한도로 분산 — ~3 일 소요
- **Risk 5 — judge 의 cost / time**: ~125 페어 × 1 호출 = 125 호출. Groq 1000 RPD 안에 안전. 단 trial 별 *order randomization seed 보존* 의무 (재현성)
- **Risk 6 — Sonnet 이 cross_model 영역에서 Stage 5 결과 JSON 임의 변경**: read-only 의무. 본 plan task 결과는 별도 디렉토리 (`experiments/cross_model/results/`)

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/_external/groq_client.py` (task-01) — read-only
- `experiments/_external/llm_judge.py` (task-01) — read-only
- `experiments/orchestrator.py` (task-02) — read-only 호출만
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py`
- `experiments/schema.py`
- 모든 기존 `experiments/exp**/run.py` — read-only 참조
- `experiments/exp**/results/*.json` — read-only (Stage 5 baseline)
- `experiments/tasks/*.json` — read-only
