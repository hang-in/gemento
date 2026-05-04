---
type: plan
status: done
updated_at: 2026-05-04
slug: exp12-extractor-role-pre-search
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default) + 사용자 직접 실행 (Task 04)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 5)
completed_at: 2026-05-04
final_verdict: "H11 ⚠ 조건부 채택 (양수 방향, 검정력 한계) — Δ(ext−base)=+0.0500, Cohen d=+0.323 small 양수, 통계 비유의. logic +0.125 / synthesis +0.050. logic-02 catastrophic 회복 (+0.30) + synthesis-05 (+0.45). Exp11 정반대 메커니즘 — Role 분리/추가가 강화보다 안전한 진화 방향"
analysis_doc: docs/reference/exp12-extractor-role-analysis-2026-05-04.md
---

# Stage 5 — Exp12: Extractor Role (Search Tool 이전 Role 축 확장)

## Description

Stage 4 (Exp11) 의 H10 ⚠ 미결 (실효적 기각) + 정반대 메커니즘 발견 ("강한 Judge 가 약한 모델의 self-discovery 를 *방해*") 후, Architect 권장에 따라 **Role 축 강화 (실패) 가 아니라 Role 축 분리/추가** 방향으로 framework 확장.

**가설 H11 후보**: 신규 Role (Extractor) 이 task prompt 의 원문/문맥에서 claim/entity 를 사전 추출하여 A→B→C chain 의 input 으로 prefix 제공하면, A 의 부담 감소 + 정확도 향상 + assertion turnover 안정화.

**조건**:
- baseline_abc: A/B/C 모두 Gemma 4 E4B (Stage 2C abc + Exp11 baseline 와 정합)
- extractor_abc: **Extractor (Gemma) → A → B → C** (모두 Gemma 동일 모델, 단 Extractor 가 신규 Role 분리)

**Stage 2C/Exp11 정합**:
- ✅ Stage 2C 의 H4 ⚠ 조건부 채택 (synthesis +0.140) 정합성 보존 — Extractor 가 long synthesis task 효과 명료할 영역
- ✅ Exp11 의 정반대 메커니즘 회피 — 같은 모델 (Gemma E4B) 의 Role 다양화. 강한 모델 도입 0
- ✅ conceptFramework §9 의 첫 번째 미외부화 축 (Extractor Role)
- 🎯 4축 framework 의 자연 진화 — Tool 처럼 "Role 도 다양화 가능"

**Mac 핸드오프 §2 Stage 5 의 의제**:
- 본 plan 마감 후 **Exp13 (Search Tool)** 진입 — Stage 5 SQLite ledger 동기는 Exp13 결과 후 시점
- Mixed Intelligence (Judge prompt 강화) 재시도는 본 plan + Exp13 결과 후 별도 검토 (정반대 메커니즘 disclosure 의 결과 따라)

## Expected Outcome

1. `experiments/system_prompt.py` — `EXTRACTOR_PROMPT` 신규 + `build_extractor_prompt()` 함수 (기존 `SYSTEM_PROMPT` / `CRITIC_PROMPT` / `JUDGE_PROMPT` 패턴 따름)
2. `experiments/orchestrator.py` — `run_abc_chain` 에 `extractor_pre_stage` 옵션 추가 (1-2 라인, default=False=기존 동작)
3. `experiments/exp12_extractor_role/run.py` (신규) — 2 condition (baseline_abc + extractor_abc) + cycle-by-cycle tattoo_history 저장
4. `experiments/exp12_extractor_role/results/exp12_baseline_abc.json` + `exp12_extractor_abc.json` (사용자 실행 출력)
5. 분석 보고서 `docs/reference/exp12-extractor-role-analysis-<TS>.md`
6. H11 verdict + 문서 갱신 (researchNotebook 한·영 + 신규 result.md `exp-12-extractor-role.md` + README 조건부)

## Subtask Index

1. [task-01](./exp12-extractor-role-pre-search-task-01.md) — `EXTRACTOR_PROMPT` + `build_extractor_prompt()` (S, parallel_group A, depends_on: [])
2. [task-02](./exp12-extractor-role-pre-search-task-02.md) — `run_abc_chain` 에 extractor pre-stage hook (S, parallel_group B, depends_on: [01])
3. [task-03](./exp12-extractor-role-pre-search-task-03.md) — `exp12_extractor_role/run.py` (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./exp12-extractor-role-pre-search-task-04.md) — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial (L, parallel_group D, depends_on: [03])
5. [task-05](./exp12-extractor-role-pre-search-task-05.md) — 분석 + H11 verdict + 문서 갱신 (M, parallel_group E, depends_on: [04])

### 의존성

```
Stage 1 (plan-side):
  Group A: task-01 (Extractor prompt 정의)
       ↓
  Group B: task-02 (orchestrator hook)
       ↓        ↓
  Group C: task-03 (run.py — 01/02 의존)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial 실험, ~25h 추정)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H11 + 문서)
```

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0 (Stage 2B 영역)
- `experiments/orchestrator.py` 변경 = `run_abc_chain` 의 `extractor_pre_stage` 옵션 추가 1-2 라인 (default=False=backward compat). Exp11 의 c_caller 추가와 같은 패턴
- `experiments/schema.py` 변경 0 — Tattoo schema 보존 (Extractor 결과는 task prompt 의 prefix 로 주입, schema 변경 0)
- `experiments/run_helpers.py` (Stage 2A) 변경 0
- `experiments/tasks/taskset.json` 변경 0 (Stage 2C 의 15 task 정합)
- 영문 노트북 Closed 추가만
- README 갱신은 사용자 결정 (verdict 변화 영향)

## 결정 (Architect 직접 결정, 2026-05-03)

사용자 위임 ("진행하자") — 모든 결정 Architect default.

### 결정 1 — Extractor 모델 — **Gemma 4 E4B (동일)** 확정

Exp11 의 정반대 메커니즘 발견 — 다른 모델 (Flash) 이 schema mismatch + chain 단절. 같은 모델 (Gemma E4B) 가 prompt 만 다른 Role 분리 (Exp03/035 와 같은 패턴) 가 정합. 외부 API 호출 0.

### 결정 2 — Extractor 출력 schema — **JSON 형식 claims + entities** 확정

```json
{
  "claims": [
    {"text": "...", "type": "fact|constraint|requirement"},
    ...
  ],
  "entities": [
    {"name": "...", "role": "actor|object|quantity"},
    ...
  ]
}
```

A 의 input 에 system prompt 또는 user message 의 prefix 로 주입 (`build_prompt` 시 Extractor 결과 prefix 추가). A 가 자체 추출 노력 절감.

### 결정 3 — Extractor 호출 시점 — **trial 시작 시 1회** 확정

cycle 별 반복 호출 회피 — task prompt 는 cycle 간 변화 없음. 1회 추출 → cycle 마다 A 의 input 에 prefix 재사용. 비용/시간 절감.

### 결정 4 — task set / trial / cycles — **Stage 2C 정합** 확정

- task: `taskset.json` 의 15 task (Stage 2C / Exp11 정합)
- trial: 5
- max_cycles: 8

### 결정 5 — condition 구성 — **2 condition** 확정

- baseline_abc: Stage 2C abc / Exp11 baseline 와 정합. **Exp11 의 baseline_abc 결과 (75 trial, mean=0.7778) 재사용 검토 → 단 본 plan 의 신규 도구 (extractor pre-stage hook 추가된 orchestrator) 검증 차원에서 신규 baseline 재실행 권장**
- extractor_abc: Extractor + A→B→C

→ 신규 baseline 실행 (~12h 추가) 의무. Exp11 baseline 와 직접 비교는 cross-reference 분석에서 가능.

### 결정 6 — Extractor prompt 의 길이 / 복잡도 — **simple JSON 추출** 확정

`SYSTEM_PROMPT` (Proposer) 의 복잡한 phase / assertion 관리 부재. 단순 JSON schema 응답만 강제. 첫 cycle 의 A 가 자기 phase=DECOMPOSE 로 claims 만드는 작업의 일부를 Extractor 가 미리 수행.

### 결정 7 — 메커니즘 측정 — **assertion turnover 강조** 확정

Stage 2C task-03 의 `count_assertion_turnover` 재사용. extractor_abc 의 cycle 1 의 assertions 가 baseline 보다 많거나 빠름 → Extractor 효과 직접 증거.

## Non-goals

- Search Tool / Graph Tool / Evidence Tool 외 다른 미외부화 축 (Exp13+ 후보)
- score_answer_v4 도입
- Anthropic / Gemini 외부 API (사용자 의도 — Stage 4 Exp11 결과 학습)
- Extractor 가 다른 강한 모델 (Mixed Intelligence 정반대 메커니즘 회피)
- 새 task / 새 카테고리 (Stage 2C 15 task 정합)
- Reducer Role 동시 추가 (Exp14 후보)

## Risks

- **Risk 1 — Extractor 가 추론 chain 을 단순화시켜 정확도 ↓**: A 가 자기 발견 chain 을 만드는 task (logic-02 같은 inconsistent puzzle) 에서 Extractor 의 사전 claims 가 잘못된 방향 유도 가능. dry-run 시 logic-02 결과 확인 의무
- **Risk 2 — Extractor 응답 schema 깨짐**: Gemma E4B 의 JSON 응답 한계 (Exp10 v3 ABC 4 fail / 본 baseline_abc 9% err) — Extractor 도 같은 패턴 가능. fallback: 빈 claims/entities 로 처리, A 가 자체 추출
- **Risk 3 — cycle 1 의 A 가 Extractor 결과 무시**: prompt 조작 어려움. dry-run 시 A 의 첫 응답이 Extractor claims 참조하는지 확인
- **Risk 4 — Exp11 의 정반대 메커니즘 재발**: 같은 모델 사용으로 schema mismatch 0 — 단 Extractor prompt 가 A prompt 와 호환 안 되면 비슷한 패턴. **Architect 가 Extractor prompt 설계 시 A prompt schema 와 호환 의무**
- **Risk 5 — 비용/시간**: 본 plan = local Gemma만, API 비용 0. 시간 ~25h (baseline 12h + extractor 13h, Extractor 호출 1 회/trial 만 추가)
- **Risk 6 — synthesis 카테고리 효과 미확정**: Stage 2C H4 회복 (synthesis +0.140) 정합. extractor 가 synthesis 강화 / 약화 어느 방향인지 측정 필수

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행:

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-7 default 사용 (사용자 위임)
4. Verification 명령 + 결과 보고
5. Risk 발견 시 즉시 보고
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지

## 변경 이력

- 2026-05-03 v1: 초안. Stage 4 Exp11 마감 (`d5d4cd7`) + 사용자 위임 ("진행하자") 직후 Architect 작성. Mac 핸드오프 §2 의 Stage 5 진입. Search Tool (Exp13) 이전 Role 축 분리/추가 방향 우선.
