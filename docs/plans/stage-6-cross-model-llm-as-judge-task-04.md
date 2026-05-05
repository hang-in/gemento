---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: stage-6-cross-model-llm-as-judge
parallel_group: D
depends_on: [03]
---

# Task 04 — 사용자 직접 실행 (3 model × 4 가설, ~3-5일)

## Changed files

- `experiments/cross_model/results/exp_stage6_*.json` — **신규 (사용자 실행)**

신규 N (자동 생성, 모델 × 가설 별).

## Change description

### 책임

- **Sonnet (Developer)**: 본 task **직접 실행 금지**. 책임 = 명령 정합성 + dry-run 검증 + 사용자 안내
- **사용자**: 직접 실행 + 결과 보고
- **Architect**: 결과 받으면 task-05 진행

### 시간 budget 추정

| 모델 | trial / sec | 가설 × task × 5 trial | 추정 시간 | 비고 |
|---|---|---|---|---|
| Qwen 2.5 7B Q4 (Local) | ~30-50s | 4 × 15 × 5 = 300 trial | ~3-4h | 32K context 가능, longctx 포함 |
| Llama 3.1 8B (Groq) | ~5-10s | 3 × 15 × 5 = 225 trial | ~30min | **5/27 deprecate 마감!** longctx 부분 (small 만) |
| Llama 3.3 70B (Groq) | ~10-15s | 4 × 15 × 5 = 300 trial | ~1-2h | longctx 가능, free tier 1000 RPD 한도 — 분산 가능 |

**총 ~5-7 시간** 의 모델 호출 + Groq rate limit 으로 분산 ~2-3 일.

### 우선순위 (Llama 3.1 8B 22일 마감)

1. **P0 — Llama 3.1 8B (Groq) 재현** (마감 5/27, 22 일) — H10/H11/H12 (main 15 task) + H13 (small 만)
2. **P0 — Local Qwen 2.5 7B Q4** (마감 없음) — 4 가설 모두 (longctx 포함)
3. **P1 — Llama 3.3 70B (Groq)** (마감 없음) — ceiling check, 시간 여유 시

### Step 1 — Sonnet 사전 검증

```bash
# 1) task-01/02/03 마감 검증
.venv/Scripts/python -c "
from experiments._external.llm_judge import judge_answer, compare_answers
from experiments._external.groq_client import call_with_meter_retry
import inspect, sys
sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'model_caller' in sig.parameters
from experiments.cross_model.run import MODELS, reproduce_h12_reducer
print('task-01/02/03 마감 검증 ok')
"

# 2) Local Qwen LM Studio endpoint 응답 (사용자 환경별)
curl http://localhost:1235/v1/models 2>&1 | head
# 또는 MODEL_ID 가 정확한지 확인

# 3) Groq smoke test (재확인)
.venv/Scripts/python -c "
from experiments._external.groq_client import call_with_meter_retry, LLAMA_3_1_8B
result = call_with_meter_retry([
    {'role': 'user', 'content': 'What is 2+2?'},
], model=LLAMA_3_1_8B, max_tokens=50)
assert result.error is None
print(f'Groq smoke ok: {result.raw_response[:50]!r}')
"
```

### Step 2 — Dry-run (각 모델 × 1 task × 1 trial)

각 모델 별 dry-run 으로 호환성 + 시간 추정.

```powershell
# Local Qwen dry-run (H11 Extractor, math-01 1 trial)
.venv\Scripts\python.exe -m experiments.cross_model.run --model qwen_25_7b_local --hypothesis h11 --tasks math-01 --trials 1 --out-name dry_qwen_h11

# Groq Llama 3.1 8B dry-run
.venv\Scripts\python.exe -m experiments.cross_model.run --model llama_3_1_8b_groq --hypothesis h11 --tasks math-01 --trials 1 --out-name dry_llama8b_h11

# Groq Llama 3.3 70B dry-run
.venv\Scripts\python.exe -m experiments.cross_model.run --model llama_3_3_70b_groq --hypothesis h11 --tasks math-01 --trials 1 --out-name dry_llama70b_h11
```

dry-run 결과 검증:
- final_answer 생성 (None / 빈 문자열 아님)
- 시간 ~1-3 분 (Local Qwen) / ~1 분 (Groq)
- error 0

### Step 3 — Llama 3.1 8B 본 실행 (P0 urgent)

22일 마감. H10/H11/H12 + H13 (small/medium needle 만, 8K context 가능 영역):

```powershell
.venv\Scripts\python.exe -m experiments.cross_model.run --model llama_3_1_8b_groq --hypothesis h10 h11 h12 --trials 5 --out-name stage6_llama8b_main

.venv\Scripts\python.exe -m experiments.cross_model.run --model llama_3_1_8b_groq --hypothesis h13 --tasks longctx-small-needle-01 longctx-medium-needle-01 longctx-small-2hop-01 --trials 5 --out-name stage6_llama8b_h13_small
```

예상 시간: ~30min × 2 + Groq 1000 RPD 분산 → ~1-2일.

### Step 4 — Local Qwen 본 실행

```powershell
.venv\Scripts\python.exe -m experiments.cross_model.run --model qwen_25_7b_local --hypothesis h10 h11 h12 h13 --trials 5 --out-name stage6_qwen_full
```

예상 시간: ~3-4h.

### Step 5 — Llama 3.3 70B 본 실행 (P1, 시간 여유 시)

```powershell
.venv\Scripts\python.exe -m experiments.cross_model.run --model llama_3_3_70b_groq --hypothesis h10 h11 h12 h13 --trials 5 --out-name stage6_llama70b_full
```

### Step 6 — LLM-as-judge 보조 채점 (H12 + H13)

본 plan 의 핵심 — keyword scorer artifact 직접 검증.

```powershell
# H12 (Reducer) 의 baseline vs reducer 페어 의미적 채점
.venv\Scripts\python.exe -m experiments.cross_model.run --model qwen_25_7b_local --hypothesis h12 --trials 5 --judge --out-name stage6_qwen_h12_judged

# 또는 기존 Stage 5 의 H12 결과에 judge 만 추가 적용 — 별도 helper 스크립트 가능
```

### Step 7 — 결과 정합성 확인

각 모델 × 가설 결과 JSON 의 trial 수 / err+null / mean_acc 보고.

## Dependencies

- task-03 마감 (cross_model/run.py 작성 + 검증)
- LM Studio 서버 (Local Qwen 2.5 7B Q4 로드, endpoint 응답)
- Groq API key (`.env` 의 `GROQ_API_KEY`, smoke test 통과)
- Stage 5 의 모든 결과 JSON (cross-model baseline 비교용) — read-only

## Verification

본 task = 사용자 직접 실행. Sonnet 의 책임:
- task-03 마감 + 모든 dry-run pre-flight (Step 1-2)
- 각 본 실행 명령의 사용자 제시
- 사용자 결과 받으면 task-05 진행
- 모델 호출 / dry-run 외 / 결과 JSON 임의 작성 절대 금지

## Risks

- **Risk 1 — Llama 3.1 8B 22일 마감 violation**: 본 task 시작 후 ~7 일 내 Step 3 완료 필수. 다른 모델은 마감 후 가능
- **Risk 2 — Groq rate limit (1000 RPD) 위반**: 본 task 의 Groq 호출량 = 모델 × ~225-300 trial × 24 calls/trial = ~5400-7200 calls — *5-7 일 분산 필요*. with_rate_limit_retry decorator + 자체 sleep 활용
- **Risk 3 — Local Qwen tool-calling 호환 실패**: H13 (Search Tool) 재현 시 발생 가능. 발견 시 사용자 보고 → H13 cross-model 은 Llama 3.3 70B 만 (Qwen 제외)
- **Risk 4 — context overflow (Llama 3.1 8B + longctx large)**: 8K 한계로 medium-large task overflow. 본 task 에서 small 만 실행 (Step 3 의 task filter)
- **Risk 5 — partial JSON checkpoint resume**: Groq 호출 실패 / network blip 시 partial JSON 으로 resume. Exp14 와 동일 패턴
- **Risk 6 — 시간 부담 + 분산 실행**: 사용자 일정 우선순위 — Llama 3.1 8B 가장 시급. 다른 모델은 분할 실행 가능 (각 가설 별 partial save)
- **Risk 7 — Sonnet 직접 실행 시도**: 본 task = 사용자 전용. 위반 시 임의 결과 데이터 생성 위험

## Scope boundary

본 task 에서 **변경 금지**:
- 모든 코드 파일 (task-01/02/03 영역)
- 모든 plan 문서
- Stage 5 의 결과 JSON (`experiments/exp**/results/*.json`)

본 task 에서 **생성 가능**:
- `experiments/cross_model/results/stage6_*.json` (자동, run.py 출력)
- `experiments/cross_model/results/dry_*.json` (dry-run 결과)
- `experiments/cross_model/results/partial_*.json` (자동 checkpoint)

**Sonnet 절대 금지**:
- LM Studio API 호출 (Local Qwen)
- Groq API 호출
- run.py 본 실행
- 결과 JSON 임의 작성 / 편집
