---
type: plan
status: done
updated_at: 2026-05-03
slug: exp11-mixed-intelligence-haiku-judge
version: 2
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default) + 사용자 직접 실행 (Task 04)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 4)
note: "v2 (2026-05-02): Judge 모델 Haiku 4.5 → Gemini 2.5 Flash 변경. 사용자 명시 (이미 GEMINI_API_KEY 보유, 비용 1/30, 기존 _external/gemini_client.py 재사용). slug 보존 (history)."
completed_at: 2026-05-03
final_verdict: "H10 ⚠ 미결 (실효적 기각) — Δ(mixed−base)=−0.0811, Cohen d=−0.316 small 음수, 통계 비유의. logic 카테고리 catastrophic (−0.275). Flash Judge 가 약한 모델의 self-discovery chain 을 *방해* 하는 정반대 메커니즘 발견 (logic-02 case study)."
analysis_doc: docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md
---

# Stage 4 — Exp11: Mixed Intelligence (Gemini Flash Judge C)

## Description

Mac 핸드오프 Stage 5 + 사용자 의도 (강한 Judge / 시간 vs 성능 trade-off / 양극 명료) 의 Architect plan 화.

**가설 H10 후보**: 강한 Judge C 가 약한 Proposer/Critic (A/B) 의 한계를 보완한다 — Role 축 강화. Stage 2C 의 H4 ⚠ 조건부 채택 (synthesis +0.140 회복) 위에서 Mixed Intelligence 정밀 측정.

**조건**:
- baseline: A/B/C 모두 Gemma 4 E4B (Stage 2C abc 와 정합)
- mixed: A/B = Gemma 4 E4B, **C = Gemini 2.5 Flash** (`gemini-2.5-flash`)

**사용자 의도 반영**:
- Sonnet 회피 (reasoning 흡수 위험 + 비용 어중간) — Gemini Flash 가 "충분히 강한 Judge" 의 적정 위치
- 시간 vs 성능 trade-off — Exp10 의 3축 (정확도 / 비용 / 지연) cost-aware 패턴 적용
- 양극 명료 — Gemma E4B (소형 로컬) ↔ Gemini Flash (적정 강도 + 매우 저렴 API)
- 사용자 이미 GEMINI_API_KEY 보유 (Exp10 의 `gemini_flash_1call` condition 에서 사용)
- Exp10 결과: Flash 1-call mean_acc=0.591 (8-loop ABC 0.781 보다 약함 — 단 본 plan 의 Judge 역할 = phase 전이 / 수렴 판단으로 충분)

**Stage 2C 발견 반영**:
- ✅ Stage 2C 의 abc tattoo_history 결함 (cycle-by-cycle 부재) — 본 plan 에서 fix 의무
- ✅ Stage 2A healthcheck/abort + Stage 2B FailureLabel 모두 적용
- ✅ Stage 2C 의 run_chain unpacking fix (commit `ee7c88d`) 적용 상태 보존

## Expected Outcome

1. `experiments/_external/gemini_client.py` — **기존 재사용** (Exp10 영역, `call_with_meter` + `resolve_gemini_key`). 신규 코드 0
2. `experiments/config.py` — Gemini Flash 관련 상수 추가 (작은 추가만, 또는 task-01 영역 외 — gemini_client 자체에 이미 정의)
3. `experiments/orchestrator.py` 의 `run_abc_chain` 에 `c_caller` 인자 추가 (1-2 라인, default=None=기존 동작)
4. `experiments/exp11_mixed_intelligence/run.py` (신규) — 2 condition (baseline_abc, mixed_flash_judge) + tattoo_history cycle-by-cycle 저장 (Stage 2C 결함 fix)
5. `experiments/exp11_mixed_intelligence/results/exp11_baseline_abc.json` + `exp11_mixed_flash_judge.json` (사용자 실행 출력)
6. 분석 보고서 `docs/reference/exp11-mixed-intelligence-analysis-<TS>.md`
7. H10 verdict + 문서 갱신 (researchNotebook 한·영 + 신규 result.md `exp-11-mixed-intelligence.md` + README 조건부)

## Subtask Index

1. [task-01](./exp11-mixed-intelligence-haiku-judge-task-01.md) — Gemini Flash client 재사용 검증 + config 보강 (S, parallel_group A, depends_on: [])
2. [task-02](./exp11-mixed-intelligence-haiku-judge-task-02.md) — `run_abc_chain` c_caller 인자 추가 (S, parallel_group B, depends_on: [])
3. [task-03](./exp11-mixed-intelligence-haiku-judge-task-03.md) — `exp11_mixed_intelligence/run.py` (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./exp11-mixed-intelligence-haiku-judge-task-04.md) — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial (L, parallel_group D, depends_on: [03])
5. [task-05](./exp11-mixed-intelligence-haiku-judge-task-05.md) — 분석 + H10 verdict + 문서 갱신 (M, parallel_group E, depends_on: [04])

### 의존성

```
Stage 1 (병렬, plan-side):
  Group A: task-01 (anthropic_client + cost meter)
  Group B: task-02 (orchestrator patch + tattoo_history fix)
        ↓        ↓
  Group C: task-03 (run.py — 01/02 의존)
        ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial 실험)
        ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H10 + 문서)
```

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0 (Stage 2B 영역)
- `experiments/orchestrator.py` 변경 = `run_abc_chain` 에 c_caller 인자 추가 1-2 라인만 (default=None=backward compat). Stage 2A "orchestrator.py 변경 0" 정책 예외 — plan 기능 확장 (Mixed C 주입)
- `experiments/schema.py` 변경 0
- `experiments/run_helpers.py` (Stage 2A) 변경 0 — TrialError + meta helper 그대로 사용
- `experiments/tasks/taskset.json` 변경 0 (Stage 2C 의 15 task 그대로 사용)
- 영문 노트북 Closed 추가만 — Task 05 의 H10 verdict note 신규 단락만, 기존 영문 변경 0
- README 갱신은 사용자 결정 (verdict 변화 영향)

## 결정 (Architect 직접 결정, 2026-05-02)

사용자 위임 ("Architect 권장대로 진행") — 모든 결정 Architect default.

### 결정 1 — Exp11 주제 — **Mixed Intelligence (Haiku Judge) 확정**

| 후보 | 사유 | 결정 |
|------|------|------|
| Mixed Intelligence (Haiku Judge) | 인프라 0, Stage 2C H4 부분 회복 정합 | **확정** |
| Search Tool Externalization | 인프라 큼 (FTS / tokenizer), 후속 (Exp12) | 보류 |

근거: 사용자 양극 명료성 (Gemma ↔ Haiku) + Stage 2C synthesis +0.140 회복 + Mac 핸드오프 §5 Architect 권장 + 사용자 명시 ("Sonnet 회피, Haiku 적정")

### 결정 2 — Judge 모델 — **Gemini 2.5 Flash (`gemini-2.5-flash`) 확정** (v2 변경)

v1 의 Anthropic Haiku 4.5 → Gemini Flash 변경. 사유:
- 사용자 이미 GEMINI_API_KEY 보유 (Exp10 의 `gemini_flash_1call` 에서 사용)
- 비용 1/30 (~$0.18 vs Haiku $5) — 결정 9 한도 ($10) 의 1/55
- 기존 `experiments/_external/gemini_client.py` 재사용 — 신규 코드 0
- Judge 역할 (phase 전이 / 수렴 판단) 에 Flash 충분 (Exp10 결과: Flash 1-call 0.591 acc 으로 Gemma E4B 대비 명확히 강함)
- `claude -p` 모드는 cache_creation 매 호출 부담 (~$42) 으로 부적합

Sonnet (어중간) / Opus (trivial) 회피 의도는 그대로. Flash 가 양극 명료성의 적정 위치.

### 결정 3 — baseline 재실행 vs Stage 2C abc 재사용 — **재실행 확정**

Stage 2C 의 abc 결과 (75 trial, mean=0.7589) 는 turnover 측정 결함 (tattoo_history cycle-by-cycle 부재). 본 plan 의 task-02 가 fix 적용 — baseline_abc 신규 75 trial 재실행 + cycle-by-cycle history 저장. 시간 비용 ~10h.

대안 (재사용) 회피 사유: turnover 측정 = H10 의 핵심 ablation. 기존 결함 데이터로는 Mixed vs ABC 의 *질적 차이* 측정 불가.

### 결정 4 — task set — **Stage 2C 의 15 task 정합 사용**

신규 task 추가 0. Stage 2C 와 직접 비교 위해 15 task (12 + planning 2 + synthesis-05) 정합.

### 결정 5 — trial 수 — **5 trial 유지** (Stage 2C 정합)

직전 Exp09 5-trial dilute 학습 — task 확대 우선. 본 plan 은 task 변경 0, trial 5 정합.

### 결정 6 — max_cycles — **8 (Stage 2C 정합)**

Stage 2C 의 ABC max_cycles=8 그대로. Mixed condition 도 동일.

### 결정 7 — condition 구성 — **2 condition** (baseline_abc + mixed_haiku_judge)

Solo-1call / Solo-budget 은 본 plan 영역 외 (Stage 2C 에서 측정 완료). 본 plan = Mixed effect 단독 측정.

### 결정 8 — API key 관리 — **`GEMINI_API_KEY` 환경 변수** (또는 `gemento/.env` 또는 `secall/.env`) 확정

기존 `experiments/_external/__init__.py:resolve_gemini_key()` 가 자동 탐색. 사용자 이미 보유.

### 결정 9 — 비용 한계 — **~$1 추정** (Gemini Flash 가격)

Gemini 2.5 Flash 가격 (`experiments/_external/gemini_client.py`): input $0.075/MTok + output $0.30/MTok.

75 trial × 8 cycles × 평균 (input 2K + output 500) 토큰 = 1.2M input + 0.3M output = **~$0.18**. 한도 여유 매우 큼 (1/55 of Haiku 추정 + 1/200 of `claude -p`).

**정확한 가격 task-01 시 확인 — 단 기존 client 의 정의된 가격 그대로 사용**.

### 결정 10 — 측정 metric — **3축 (Stage 2C 정합) + cost-aware (Exp10 패턴)**

| metric | 정의 | helper |
|--------|------|--------|
| 정확도 | mean acc (v3 채점) | 기존 measure.py |
| assertion turnover | cycle-by-cycle (Stage 2C 결함 fix 후) | Stage 2C analyze.py |
| error mode | FailureLabel (Stage 2B) | Stage 2B failureLabels.md |
| **cost-aware** | trial 당 Haiku API 비용 + total wall time | 신규 helper (task-01) |

**Exp10 의 3축 (정확도/비용/지연)** + Stage 2C 의 3축 (정확도/turnover/error) = 종합 4-5 축.

## Non-goals

- Sonnet / Opus 비교 (사용자 명시 회피)
- A/B 도 Haiku (사용자 의도 외 — Mixed = C 만 강한)
- Search Tool / Graph Tool / Extractor Role 등 다른 외부화 축 (Exp12+ 후보)
- score_answer_v4 도입
- A/B 의 prompt 변경 (Stage 2C 정합 위해 보존)
- 새 task 추가 (Stage 2C 15 task 그대로)

## Risks

- **Risk 1 — Haiku reasoning 흡수**: Judge prompt schema 강제 (verdict + brief justification 만, proposer 답안 재작성 금지). task-03 의 prompt 명세. 위반 시 trial 결과 검증 단계에서 식별
- **Risk 2 — Anthropic API 가격 변동 / 비용 한계 초과**: task-01 에서 정확한 가격 확인 + 사전 비용 추정 + 본 실행 시 dry-run 1 trial 비용 측정. 임계 ($20+) 시 사용자 호출
- **Risk 3 — API 호출 fail (network, rate limit, key invalid)**: Stage 2A healthcheck/abort 패턴 적용 — Anthropic 호출 실패 시 fatal classify + abort
- **Risk 4 — A/B (Gemma) ↔ C (Haiku) 의 prompt schema 호환**: A 가 작성한 Tattoo JSON 이 Haiku C 의 input 으로 호환되는지 검증. dry-run 시 확인
- **Risk 5 — Mixed 가 너무 우위 (cherry-pick 의심)**: Δ(mixed - baseline_abc) > +0.20 면 Judge 가 reasoning 흡수 가능성. task-05 의 verdict 결정 시 disclosure
- **Risk 6 — orchestrator.py 변경 (1-2 라인) 가 다른 도구 영향**: c_caller 의 default=None 보장 backward compat. 기존 Exp10 / Exp08 / 기타 run_abc_chain 호출처 정상 동작 검증 (task-02 verification)
- **Risk 7 — tattoo_history fix 의 backward compat**: Stage 2C abc 결과의 schema 변경 영향. 본 plan 의 신규 결과만 cycle-by-cycle, Stage 2C 결과 보존 (재사용 안 함)

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행.

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-10 default 사용 (사용자 위임)
4. Verification 명령 실행 + 결과 보고
5. Risk 발견 시 즉시 보고
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 (Sonnet 직접 호출 금지)

## 변경 이력

- 2026-05-02 v1: 초안. Stage 2 (2A/2B/2C) 마감 후 Stage 4 진입. 사용자 위임 ("Architect 권장대로 진행") — 모든 결정 1-10 Architect 확정.
- 2026-05-02 v2: Judge 모델 변경 — Anthropic Haiku 4.5 → **Gemini 2.5 Flash**. 사유:
  - 사용자 이미 GEMINI_API_KEY 보유 (Exp10 의 `gemini_flash_1call` 사용 이력)
  - 비용 1/30 (~$0.18 vs Haiku ~$5)
  - 기존 `experiments/_external/gemini_client.py` 재사용 (신규 코드 0)
  - `claude -p` 모드 검토 결과 cache_creation 매 호출 부담 (~$42) 으로 부적합
  - Architect 권장: SDK 신규 도입 회피 + 인프라 재사용 + 비용 절감 동시 달성
  
  영향: 결정 2 / 8 / 9 + Description + Expected Outcome + Subtask Index task-01 갱신.
  Slug `exp11-mixed-intelligence-haiku-judge` 보존 (commit history). 본문은 "Flash Judge" 로 통일.
