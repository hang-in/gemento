---
type: prompt
status: ready
updated_at: 2026-05-04
for: Sonnet (Developer)
plan: exp13-reducer-role
purpose: Stage 5 Exp13 진행 신호 — Reducer Role (Role 다양화 라인 연속)
prerequisites: Stage 2A + 2B + 2C + Stage 4 (Exp11) + Stage 5 (Exp12) 모두 마감
---

# Stage 5 (Exp13) 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 5 Exp13 (Reducer Role) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정
- Risk / Scope boundary 위반 직전 즉시 보고
- 사용자 결정 1-7 모두 확정 (Architect 위임 "리듀서 롤 먼저 해보자, 작성해 줘"). 변경 금지
- Task 04 = 사용자 직접 실행 — 모델 호출 금지
- 본 plan = **외부 API 0** (local Gemma만, Exp12 패턴)
- **Exp12 `exp12_extractor_role/run.py` 의 패턴 정확 재사용** — 임의 단순화 금지

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
```

**prerequisite 검증**:

```bash
.venv/Scripts/python -c "
# Stage 2A
from experiments.run_helpers import (classify_trial_error, build_result_meta, check_error_rate)
# Stage 2B
from experiments.schema import FailureLabel
# Stage 2C analyze
from experiments.exp_h4_recheck.analyze import classify_error_mode, count_assertion_turnover
# Exp12 Extractor
from experiments.system_prompt import EXTRACTOR_PROMPT, build_extractor_prompt
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'c_caller' in sig.parameters, 'Exp11 c_caller 미적용'
assert 'extractor_pre_stage' in sig.parameters, 'Exp12 extractor_pre_stage 미적용'
print('ok: Stage 2A + 2B + 2C + Stage 4 + Stage 5 Exp12 마감')
"
```

## 2. 읽어야 할 plan 파일

```
docs/plans/exp13-reducer-role.md         # parent
docs/plans/exp13-reducer-role-task-01.md # group A — REDUCER_PROMPT
docs/plans/exp13-reducer-role-task-02.md # group B — orchestrator reducer_post_stage
docs/plans/exp13-reducer-role-task-03.md # group C — run.py
docs/plans/exp13-reducer-role-task-04.md # group D — 사용자 직접 실행
docs/plans/exp13-reducer-role-task-05.md # group E — 분석 + verdict + 문서
```

## 3. 사용자 결정 1-7 (Architect 위임 확정)

| 결정 | 값 |
|------|---|
| 1. Reducer 모델 | **Gemma 4 E4B (동일)** — Exp12 패턴, 외부 API 0 |
| 2. Reducer schema | input: assertions list + candidate_answer / output: plain text final_answer |
| 3. 호출 시점 | trial 종료 시 1회 (post-stage). Extractor 의 pre-stage 와 대칭 |
| 4. task / trial / cycles | 15 / 5 / 8 (Stage 2C / Exp12 정합) |
| 5. condition 구성 | 2 (baseline_abc + reducer_abc) |
| 6. Reducer prompt 자율도 | 재정리만, 새 결론/factual claim 추가 금지 (Risk 1 차단) |
| 7. 메커니즘 측정 | error mode + final_answer 길이 + task essential keyword 출현 비율 |

## 4. 진행 순서

```
Stage 1 (plan-side):
  Group A: task-01 (REDUCER_PROMPT)
       ↓
  Group B: task-02 (orchestrator reducer_post_stage hook)
       ↓        ↓
  Group C: task-03 (run.py — Exp12 패턴 그대로 + CONDITION_DISPATCH 변경)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial, ~25h)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H12 + 문서)
```

권장: task-01 → 02 → 03 직렬, 그 후 task-04 사용자 호출.

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-5-exp13-task-NN): <summary>` 또는 `docs(stage-5-exp13-task-NN): ...`
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 (특히 task-01 의 Risk 1 — Reducer 가 답을 바꿈)
- task-04 진행 시점 (사용자 직접 실행 신호)
- task-05 README 갱신 결정

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. 책임:
1. Task 04 plan 본문 명령 정합성 확인
2. 사용자에게 명령 제시 (분할 옵션 권장)
3. 사용자 결과 받으면 task-05 진행
4. **모델 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + 5종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- exp-13-reducer-role.md 신규
- researchNotebook.md (한국어): H12 entry + Exp13 섹션 + 축 매트릭스
- researchNotebook.en.md: **Closed 추가만**
- README 갱신: **사용자 결정**

분석 보고서 의 **Exp12 ↔ Exp13 결정적 대비 표** 의무 — Role 분리/추가 라인의 일관성 검증.

## 9. Stage 5 Exp13 완료 신호

5 subtask 완료 + 검증 (Exp12 task-05 패턴):

```bash
# 1) 도구 import
.venv/Scripts/python -c "
from experiments.system_prompt import REDUCER_PROMPT, build_reducer_prompt
from experiments.exp13_reducer_role.run import (
    run_baseline_abc, run_reducer_abc, CONDITION_DISPATCH,
)
import inspect
from experiments.orchestrator import run_abc_chain
assert 'reducer_post_stage' in inspect.signature(run_abc_chain).parameters
print('ok: Exp13 도구')
"

# 2) trial 수 = 150
# 3) 분석 보고서 + result.md 신규
```

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H1~H11 entry 변경 절대 금지
- README 갱신 = 사용자 결정
- `experiments/measure.py` / `system_prompt.py` 의 기존 prompt / `schema.py` / `run_helpers.py` 변경 금지
- `experiments/_external/gemini_client.py` 변경 금지 (Exp11 영역)
- Exp11 c_caller / Exp12 extractor_pre_stage — orchestrator 의 read-only 보존
- 본 plan = Exp12 마감 (H11 ⚠ 조건부 채택) 후 Architect 권장. Role 분리/추가 라인 연속 검증

## 11. 다음 단계 (Stage 5 Exp13 마감 후)

Exp13 마감 후 Architect 가:
1. H12 verdict + Exp12 ↔ Exp13 비교 결과
2. Stage 5 다음 plan 결정 — Search Tool (Exp14) / Extractor + Reducer 조합 (Exp15) / 다른 축
3. Stage 5 SQLite ledger — Search Tool 결과 후 시점 별도 결정

준비되었으면 task-01 부터 시작. 보고는 한국어.
