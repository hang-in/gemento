---
type: plan
status: draft
updated_at: 2026-05-05
slug: stage-6-cross-model-llm-as-judge
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default) + 사용자 직접 실행 (Task 04)
parent_strategy: docs/reference/paper-review-action-items-2026-05-05.md (P1-3 + P1-4 + cross-model)
---

# Stage 6 — Cross-model replication + LLM-as-judge

## Description

Stage 5 의 4 가설 (H10 Mixed Intelligence, H11 Extractor, H12 Reducer, H13 Search Tool) 모두 단일 base model (Gemma 4 E4B) 결과. paper draft v0.3 의 §4.3 cross-model 섹션이 [TBD] placeholder. 본 plan = arXiv preprint 전 *publication readiness* 의 마지막 큰 갭 메우기.

**핵심 가설 / 작업 두 갈래**:

1. **Cross-model generalization** — Stage 5 4 가설을 다른 small/medium-size open-weight 모델에서 재현하여 *direction generalize* 여부 검증. 특히 Exp14 의 통계적 유의 negative 결과 (H13) 가 모델 일반인지 Gemma 특정인지 분리.

2. **LLM-as-judge auxiliary evaluation (P1-3)** — H12 (Reducer) 와 H13 (Search Tool) 의 *keyword scorer artifact 가능성* 을 의미적 채점으로 직접 검증. Groq GPT-OSS 120B 를 *별개 judge* 로 사용 (cross-evaluator).

**가설 H14 후보 (cross-model)**: Stage 5 의 directional patterns (H11 +, H12 −, H13 −) 가 Llama 3.1 8B / Llama 3.3 70B / Qwen 2.5 7B Q4_K_M 에서도 *direction-consistent* 로 재현된다. Effect size magnitude 는 모델별 다를 수 있으나 sign 은 보존.

**가설 H15 후보 (LLM-as-judge)**: H12 (Reducer) 의 keyword-scorer 음수 결과 중 일부는 *style mismatch artifact* — 의미적 채점 시 음수 magnitude 감소 또는 0 근접. H13 (Search Tool) 도 동일 검증.

**Stage 6 종합 + 본 plan 동기**:
- ✅ Stage 5 (Exp10/11/12/13/14) 모두 마감 — Gemma 4 E4B baseline 완성
- ✅ Groq client smoke test 완료 (commit `b389534`) — 인프라 준비
- ✅ paper draft v0.3 의 §4.3 / §4.6.2 / §4.7.2 의 명시적 placeholder
- 🎯 **Stage 6 = arXiv preprint 직전 마지막 큰 작업** — cross-model + LLM-as-judge 마감 시 paper v1.0 arXiv 업로드 가능

## Expected Outcome

1. `experiments/_external/groq_client.py` — 확장 (batch helper, rate limit retry, judge wrapper). 기존 `call_with_meter` 보존
2. `experiments/_external/llm_judge.py` (신규) — `judge_answer(question, expected_answer, candidate_answer, model)` helper. Groq GPT-OSS 120B 기본
3. `experiments/cross_model/__init__.py` (신규)
4. `experiments/cross_model/run.py` (신규) — 4 가설 (H10/H11/H12/H13) × 다중 모델 (Local Qwen + Groq Llama 8B/70B) 의 재현 driver. LLM-as-judge 보조 채점 통합
5. `experiments/cross_model/results/exp_stage6_*.json` (사용자 실행)
6. 분석 보고서 `docs/reference/stage6-cross-model-analysis-<TS>.md`
7. `docs/reference/all-hypotheses-statistics.md` (P1-4) — H1/H7/H8/H9a Bootstrap CI 재산정 + 5 가설 통일 5튜플
8. paper draft v0.4 — §4.3 cross-model 본문 채움 + §4.6.2 / §4.7.2 의 LLM-as-judge 결과 통합 + Conclusion §7 작성

## Subtask Index

1. [task-01](./stage-6-cross-model-llm-as-judge-task-01.md) — Groq client 확장 + LLM-as-judge 인프라 (S, parallel_group A, depends_on: [])
2. [task-02](./stage-6-cross-model-llm-as-judge-task-02.md) — Local Qwen 2.5 7B Q4_K_M setup + cross-model orchestrator hook (S, parallel_group B, depends_on: [])
3. [task-03](./stage-6-cross-model-llm-as-judge-task-03.md) — `experiments/cross_model/run.py` (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./stage-6-cross-model-llm-as-judge-task-04.md) — 사용자 직접 실행 — 3 model × 4 가설 (조건부 축소) ~3-5 일 (L, parallel_group D, depends_on: [03])
5. [task-05](./stage-6-cross-model-llm-as-judge-task-05.md) — 분석 + Stage 6 verdict + paper v0.4 + 문서 (M, parallel_group E, depends_on: [04])

### 의존성

```
Stage 1 (plan-side, 병렬 가능):
  Group A: task-01 (Groq client 확장 + llm_judge.py)
  Group B: task-02 (Local Qwen 셋업 + orchestrator model_caller hook)
       ↓        ↓
  Group C: task-03 (cross_model/run.py — 01/02 의존)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (3 model × 가설 재현 + LLM-as-judge, ~3-5 일)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + paper v0.4 + 문서)
```

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- Stage 5 의 모든 결과 JSON (`experiments/exp10~14_*/results/*.json`) — read-only (재실행 금지, cross-model 비교 baseline)
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0
- `experiments/orchestrator.py` 변경 = `model_caller: Callable | None = None` hook 추가 (Exp11 의 c_caller 패턴 일반화). 기존 c_caller / extractor / reducer / search_tool 5 hook 보존
- `experiments/schema.py` 변경 0
- `experiments/run_helpers.py` (Stage 2A) 변경 0
- `experiments/tasks/*.json` 변경 0 (Stage 5 정합)
- 영문 노트북 Closed 추가만 (Stage 6 verdict 후)
- README 갱신은 사용자 결정 (task-05 마감 후)
- **외부 API 비용 < $5** (Groq free tier + GPT-OSS 의 LLM-as-judge 호출량 제한)
- **Llama 3.1 8B 22일 마감 (2026-05-27)** — 본 plan 의 task-04 이 5/27 이전 완료 의무

## 결정 (Architect 직접 결정 / 사용자 위임 default, 2026-05-05)

### 결정 1 — Cross-model 후보 — **3 model 우선** 확정

| 모델 | 용도 | 호스팅 | 비용 |
|---|---|---|---|
| **Qwen 2.5 7B Q4_K_M** (Local) | main cross-model — 32K context, 영구 보존 | LM Studio (3060 Ti 8GB) | $0 (전기) |
| **Llama 3.1 8B Instant** (Groq) | size class up + speed (LPU 2200 tok/s) | Groq free | $0 (free tier) |
| **Llama 3.3 70B Versatile** (Groq) | ceiling check (size scaling) | Groq free | $0 (free tier) |

**(보조)**: Phi-3.5 mini 3.8B Q8 (Local) — Stage 5 의 secondary scaling point. 시간 여유 시.

### 결정 2 — LLM-as-judge 모델 — **Groq GPT-OSS 120B** 확정

reasoning model (o1-style) → 의미적 채점에 강함. Groq free tier. 비용 $0.

판단 정확성 강화 위해 *임의 비교* (baseline vs treatment 답변 페어) — Judge 가 어느 답이 더 정확한지 평가 + 등급 (1-5).

### 결정 3 — 재현 가설 범위 — **Stage 5 의 4 가설** 확정

H10 (Exp11 Mixed) / H11 (Exp12 Extractor) / H12 (Exp13 Reducer) / H13 (Exp14 Search). H1 (Exp10 cost-aware) 는 본 plan 영역 외 (별도 plan 가능, 비용 큼).

**비용 추정**:
- 모델 × 가설 × task × trial = 3 × 4 × 15 × 5 = **900 trial** (full)
- 단 longctx_taskset 의 large-20K task 는 Llama 3.1 8B (8K context) 부적합 → H13 cross-model 시 medium 이하만 (3 task) 또는 Local Qwen 만
- 실질 trial: 약 600-700 trial × 다중 모델

### 결정 4 — taskset — **Stage 5 정합** + **context 한계 분기** 확정

| 가설 | taskset | Llama 3.1 8B (8K) | Llama 3.3 70B (128K) | Local Qwen 7B (32K) |
|---|---|---|---|---|
| H10/11/12 | main 15 task | ✅ | ✅ | ✅ |
| H13 | longctx 10 task | ⚠ small/medium 만 (6 task) | ✅ | ✅ |

### 결정 5 — trial / cycles — **Stage 5 정합** (5 trial × 8 max_cycles) 확정

paper readiness 의 일관성 우선. 단 시간 부담 시 *3 trial* 로 축소 가능 (Architect 별도 결정).

### 결정 6 — LLM-as-judge 호출 범위 — **H12 + H13 한정** 확정

- H12 Reducer: baseline_abc vs reducer_abc 답변 페어 × 15 task × 5 trial = 75 페어 → judge 채점
- H13 Search: baseline_chunked vs search_tool 답변 페어 × 10 task × 5 trial = 50 페어
- H10 / H11 도 가능 단 H12/H13 의 keyword scorer caveat 가 더 본질적 → 본 plan 우선

총 LLM-as-judge 호출: ~125 페어 × 1 = ~125 호출. Groq free 1000 RPD 안에 충분.

### 결정 7 — 통계 5튜플 통일 (P1-4) 통합 — **본 plan task-05 에 포함** 확정

H1 / H7 / H8 / H9a 의 기존 결과 JSON 에서 Bootstrap CI 재산정 + 5튜플 통일. `docs/reference/all-hypotheses-statistics.md` 신규.

### 결정 8 — paper draft v0.4 갱신 범위 — **§4.3 + §4.6.2 + §4.7.2 + §7** 확정

- §4.3 cross-model: 본 plan 결과로 본문 채움
- §4.6.2 / §4.7.2 의 LLM-as-judge replication 결과 통합
- §7 Conclusion: cross-model + Stage 5 종합 narrative 작성
- arXiv preprint v1.0 업로드 가능 상태 도달

## Non-goals

- H1 (Exp10 cost-aware) cross-model 재현 — 별도 plan, 비용 큼
- H7/H8 (Tool 축 H7/H8) cross-model 재현 — math-04 단일 task, 본 plan 우선순위 외
- H9a/b/c (longctx) cross-model 재현 — Llama 3.1 8B 8K 한계, Local Qwen 으로만 가능 — 시간 여유 시
- 새 가설 도입 — Stage 5 의 4 가설 일반화에 집중
- score_answer_v4 / 새 채점 인프라
- arXiv 실제 업로드 — task-05 마감 후 별도 결정
- venue submission — arXiv preprint single target 정책 유지

## Risks

- **Risk 1 — Llama 3.1 8B 22일 마감 (2026-05-27)**: 본 plan task-04 이 그 전에 완료 의무. 사용자 일정 우선순위 — Llama 3.1 8B 가설 재현이 가장 시급. Llama 3.3 70B / Qwen 2.5 7B 는 마감 후도 가능
- **Risk 2 — LLM-as-judge 의 자체 bias**: GPT-OSS 120B 가 *특정 답변 스타일 선호* 할 가능성. baseline 과 treatment 답변 페어를 *random order* 로 제시 (treatment-first 50% / baseline-first 50%) 로 mitigation
- **Risk 3 — Local Qwen 의 tool-calling 호환성**: Q4_K_M quantization 의 tool-calling 신뢰도. dry-run 첫 trial 의 tool_call_log 검증 의무
- **Risk 4 — Groq rate limit (1000 RPD)**: ABC 1 trial = ~24 API call (8 cycle × 3 role). 1000 RPD 한도 → 하루 ~40 trial 가능. 100 trial 재현 시 ~3 일 분산 실행 필요. 또는 *3 trial 축소* 옵션 (결정 5)
- **Risk 5 — model_caller hook 의 design conflict**: Exp11 의 c_caller 와의 관계. 본 plan = c_caller 의 *상위 일반화* (a_caller / b_caller / c_caller 모두 포함) — 신규 hook 또는 c_caller 확장 결정 필요
- **Risk 6 — score_answer_v3 keyword 매칭 의 cross-model 차이**: 다른 모델은 다른 답변 스타일 → keyword 매칭 정합성 변동 가능. LLM-as-judge 결과로 보조 검증
- **Risk 7 — 본 plan 의 scope 큼**: 5 subtask, 사용자 직접 실행 ~3-5 일, 분석 ~2-3 일. 분할 실행 / 우선순위 축소 가능

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행:

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-8 default 사용
4. Verification 명령 + 결과 보고
5. Risk 발견 시 즉시 보고 — 특히 Risk 1 (Llama 3.1 8B 마감), Risk 5 (model_caller hook design)
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지
8. **신규**: `gemento-experiment-scaffold` 스킬 task-03 작성 시 활용 + `gemento-verdict-record` 스킬 task-05 활용

## 변경 이력

- 2026-05-05 v1: 초안. Stage 5 마감 (`6df5eff`) + paper review action items 의 P1-3 / P1-4 / cross-model 통합. paper draft v0.3 의 §4.3 / §4.6.2 / §4.7.2 / §7 placeholder 채움이 본 plan 의 핵심 산출물. arXiv preprint v1.0 업로드 가능 상태 도달.
