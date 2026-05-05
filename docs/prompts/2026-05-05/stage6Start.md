---
type: prompt
status: ready
updated_at: 2026-05-05
for: Sonnet (Developer)
plan: stage-6-cross-model-llm-as-judge
purpose: Stage 6 진행 신호 — Cross-model replication + LLM-as-judge
prerequisites: Stage 2A + 2B + 2C + Stage 4 + Stage 5 (Exp11/12/13/14) 모두 마감 + Groq client smoke test (`b389534`)
---

# Stage 6 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 6 (Cross-model replication + LLM-as-judge) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정
- Risk / Scope boundary 위반 직전 즉시 보고
- 사용자 결정 1-8 모두 확정 (Architect default)
- Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지
- **Llama 3.1 8B 마감 2026-05-27 (22일)** — task-04 의 Llama 3.1 8B Step 3 가 본 plan 의 가장 시급 작업
- **Stage 5 결과 JSON 무변경** — `experiments/exp**/results/*.json` 모두 read-only baseline
- `gemento-experiment-scaffold` 스킬 task-03 활용 + `gemento-verdict-record` 스킬 task-05 활용

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
```

**prerequisite 검증**:

```bash
.venv/Scripts/python -c "
# Stage 2A/2B/2C
from experiments.run_helpers import classify_trial_error, build_result_meta
from experiments.schema import FailureLabel
# Stage 4/5
from experiments.system_prompt import EXTRACTOR_PROMPT, REDUCER_PROMPT
from experiments.tools import SEARCH_TOOL_SCHEMA, make_search_chunks_tool
# Groq client smoke
from experiments._external.groq_client import (
    call_with_meter, LLAMA_3_1_8B, LLAMA_3_3_70B, GPT_OSS_120B,
)
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage', 'search_tool', 'corpus'):
    assert opt in sig.parameters, f'{opt} 미적용'
print('ok: Stage 2A + 2B + 2C + Stage 4 + Stage 5 + Groq client 마감')
"
```

## 2. 읽어야 할 plan 파일

```
docs/plans/stage-6-cross-model-llm-as-judge.md         # parent
docs/plans/stage-6-cross-model-llm-as-judge-task-01.md # group A — Groq client + llm_judge
docs/plans/stage-6-cross-model-llm-as-judge-task-02.md # group B — Local Qwen + model_caller hook
docs/plans/stage-6-cross-model-llm-as-judge-task-03.md # group C — cross_model/run.py
docs/plans/stage-6-cross-model-llm-as-judge-task-04.md # group D — 사용자 직접 실행
docs/plans/stage-6-cross-model-llm-as-judge-task-05.md # group E — 분석 + paper v0.4 + 문서
```

## 3. 사용자 결정 1-8 (Architect 확정)

| 결정 | 값 |
|------|---|
| 1. Cross-model 후보 | Local Qwen 2.5 7B Q4_K_M + Groq Llama 3.1 8B + Groq Llama 3.3 70B |
| 2. LLM-as-judge | Groq GPT-OSS 120B (reasoning model) |
| 3. 재현 가설 | Stage 5 의 4 가설 (H10/H11/H12/H13) — H1/H7~H9 영역 외 |
| 4. taskset | Stage 5 정합 + context 한계 분기 (Llama 8B 의 longctx 부분) |
| 5. trial / cycles | 5 trial × 8 max_cycles (Stage 5 정합) |
| 6. LLM-as-judge 범위 | H12 + H13 한정 (keyword scorer caveat 가장 본질적) |
| 7. P1-4 통계 5튜플 통일 통합 | task-05 에 포함 (`all-hypotheses-statistics.md`) |
| 8. paper draft v0.4 갱신 범위 | §4.3 + §4.6.2 + §4.7.2 + §7 Conclusion |

## 4. 진행 순서

```
Stage 1 (plan-side, A/B 병렬 가능):
  Group A: task-01 (Groq client 확장 + llm_judge.py)
  Group B: task-02 (orchestrator model_caller hook)
       ↓        ↓
  Group C: task-03 (cross_model/run.py — 01/02 의존, gemento-experiment-scaffold 스킬 활용)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (~3-5일, Llama 3.1 8B 22일 마감 우선)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + paper v0.4 + 문서, gemento-verdict-record 스킬 활용)
```

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-6-task-NN): <summary>` 또는 `docs(stage-6-task-NN): ...`
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 — 특히:
  - task-02 의 Risk 1 — c_caller / model_caller mutual exclusion design conflict
  - task-02 의 Risk 2 — Local Qwen tool-calling 호환 (Q4_K_M)
  - task-04 의 Risk 1 — Llama 3.1 8B 22일 마감
  - task-04 의 Risk 2 — Groq rate limit (1000 RPD) 분산 실행 일정
- task-04 진행 시점 (사용자 직접 실행 + Llama 3.1 8B 우선순위)
- task-05 README 갱신 결정

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. 책임:
1. Task 04 plan 본문의 모델 별 명령 정합성 확인 (Step 1-2 dry-run)
2. 사용자에게 우선순위 (Llama 3.1 8B P0 urgent → Local Qwen → Llama 3.3 70B) 안내
3. Groq rate limit 분산 실행 가이드 (1000 RPD = 하루 ~40 trial)
4. 사용자 결과 받으면 task-05 진행
5. **모델 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + 8 종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- result.md 신규 (`docs/reference/results/exp-stage6-cross-model.md`)
- **all-hypotheses-statistics.md 신규** (P1-4)
- researchNotebook.md (한국어): H14 + H15 + Stage 6 섹션
- researchNotebook.en.md: **Closed 추가만**
- paper draft v0.4 (§4.3 + §4.6.2 + §4.7.2 + §7) — 가장 큰 작업
- README 갱신: **사용자 결정**
- paper review action items P1 status 갱신

`gemento-verdict-record` 스킬 활용 — 영문 노트북 Closed-append-only 정책 자동 강제.

## 9. Stage 6 완료 신호

5 subtask 완료 + 검증 (Stage 5 task-05 패턴):

```bash
# 1) 도구 import
.venv/Scripts/python -c "
from experiments._external.llm_judge import judge_answer, compare_answers
from experiments.cross_model.run import MODELS, reproduce_h12_reducer
import inspect, sys
sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
assert 'model_caller' in inspect.signature(run_abc_chain).parameters
print('ok: Stage 6 도구')
"

# 2) trial 수 = N (모델 × 가설 × task × 5)
# 3) 분석 보고서 + paper v0.4 + all-hypotheses-statistics.md 신규
# 4) 영문 노트북 표 / 기존 entry 무변경 (Closed-append-only)
```

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H1~H13 entry 변경 절대 금지
- README 갱신 = 사용자 결정
- `experiments/measure.py` / `system_prompt.py` 의 기존 prompt / `schema.py` / `run_helpers.py` 변경 금지
- Stage 5 의 모든 결과 JSON 변경 금지 (cross-model baseline)
- 본 plan = arXiv preprint v1.0 직전 마지막 큰 작업. 신중한 quality bar (P0 톤다운 정신 유지)

## 11. 다음 단계 (Stage 6 마감 후)

Stage 6 마감 후 Architect 가:
1. paper v0.4 → v1.0 final review (사용자 + Architect 협의)
2. arXiv preprint v1.0 업로드 (사용자 결정)
3. (옵션) venue submission (EMNLP / ACL / NeurIPS Workshop)
4. Stage 7 후보 — Iteration discipline manipulation (mandatory tool rules), Graph Tool, Evidence Tool 등

준비되었으면 task-01 부터 시작. 보고는 한국어.
