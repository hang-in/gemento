---
type: prompt
status: ready
updated_at: 2026-04-30
for: Sonnet (Developer)
plan: scorer-failure-label-reference
purpose: Stage 2B 작업 시작 신호 — scorer/failure label reference 정리 (단순 plan-side 작업)
---

# Stage 2B 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. 본 프롬프트는 self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 2B plan 을 그대로 진행한다.

## 0. 핵심 규칙 (위반 즉시 중단)

- **Plan 문서 그대로 진행**. 임의 reorder / scope 확장 금지
- **각 subtask 의 "Changed files" 만 수정**. 다른 파일 read-only
- **"Scope boundary" 절 엄수**. 위반 직전이면 멈추고 사용자 호출
- **Risk 발견 시 즉시 보고**. 임의 우회 금지
- **사용자 결정 1-4 확정** (Architect 가 사용자 위임 받아 결정). 변경 금지
- **사용자 직접 실행 task 0** — 모든 task 가 plan-side (마크다운 작성 + enum 추가). Sonnet 가 직접 진행

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
# 기대: 최신 commit fc1c0a5 (Stage 2B 작성 + Stage 2C 정정)
```

## 2. 읽어야 할 plan 파일 (순서대로)

```
docs/plans/scorer-failure-label-reference.md  # parent
docs/plans/scorer-failure-label-reference-task-01.md  # group A 단독
docs/plans/scorer-failure-label-reference-task-02.md  # group B 시작
docs/plans/scorer-failure-label-reference-task-03.md  # group B, depends_on [02]
docs/plans/scorer-failure-label-reference-task-04.md  # group C, depends_on [02]
```

## 3. 사용자 결정 1-4 (Architect 위임 확정 — 변경 금지)

| 결정 | 값 |
|------|---|
| 1. FailureLabel enum 위치 | `experiments/schema.py` (Tattoo / Assertion 옆) |
| 2. Stage 2C ErrorMode 관계 | `FailureLabel` 의 alias (`from experiments.schema import FailureLabel as ErrorMode`) |
| 3. enum value naming | SCREAMING_SNAKE_CASE — `NONE`, `FORMAT_ERROR`, `WRONG_SYNTHESIS`, `EVIDENCE_MISS`, `NULL_ANSWER`, `CONNECTION_ERROR`, `PARSE_ERROR`, `TIMEOUT`, `OTHER` |
| 4. 기존 ad-hoc 라벨 retroactive 보강 | 0 — 기존 result.md / handoff 의 라벨링 보존, 신규 분석부터 표준 enum 사용 |

## 4. 진행 순서 (의존성 그래프)

```
Stage 1 (병렬 가능):
  Group A: task-01 (scoringHistory.md 신규)
  Group B: task-02 (FailureLabel enum) → task-03 (failureLabels.md + 매핑 표)
                                       ↘ task-04 (Stage 2C plan 의 ErrorMode stub 정정)
```

권장 순서: **task-01 → task-02 → task-03 → task-04** 직렬. 한 번에 한 subtask.

## 5. 각 subtask 진행 패턴

각 subtask 마다:

1. **subtask 파일 read** (Step + Verification + Risk + Scope boundary 모두 숙지)
2. **Step 순서대로 실행**
3. **Verification 명령 실행 + 결과 캡처**. 실패 시 즉시 멈추고 사용자 호출
4. **commit message 초안 작성** — `docs(stage-2b-task-NN): <summary>` 형식. 각 subtask 마다 별도 commit 권장
5. **다음 subtask 로 이동 전 사용자 confirm**

## 6. 사용자 호출 분기 (즉시 호출 의무)

- Verification 명령 실패
- Plan 영역 외 파일 수정이 정당하다고 판단되는 경우 (Scope boundary 위반 직전)
- subtask 내 Step 의 코드 stub 이 실제 코드 구조와 충돌
- 임의 결정이 필요한 상황 (plan 에 명시되지 않은 패턴)

## 7. 특이사항 (task-04 의 stub 정정)

Task 04 = "Stage 2C task-03 의 plan 본문 의 ErrorMode 코드 stub 정정". 이미 Architect 가 직전 commit (`fc1c0a5`) 에서 stub 을 alias import 로 정정해 놓았음. Sonnet 의 task-04 는:
- 정정된 stub 이 실제로 alias import 형태인지 검증
- Stage 2C analyze.py (Sonnet 이 Stage 2C task-03 진행 시점에 작성) 가 본 alias 를 사용하는지는 본 plan 영역 외 — Stage 2C 진행 시점에 검증

즉 Stage 2B task-04 는 매우 작은 검증 task. 별도 commit 또는 task-02/03 commit 에 묶음.

## 8. Stage 2B 완료 신호

4 subtask 모두 완료 + Verification 통과:

```bash
# 최종 검증
.venv/Scripts/python -c "
from experiments.schema import FailureLabel, Tattoo, Assertion
labels = [l.value for l in FailureLabel]
assert 'none' in labels and 'connection_error' in labels and 'evidence_miss' in labels
print('ok: FailureLabel enum + 기존 dataclass 보존')
"

# canonical 문서 존재
.venv/Scripts/python -c "
import os
for p in ('docs/reference/scoringHistory.md', 'docs/reference/failureLabels.md'):
    assert os.path.exists(p), f'{p} missing'
    text = open(p, encoding='utf-8').read()
    assert 'canonical: true' in text
print('ok: scoringHistory + failureLabels reference')
"

# Stage 2C plan 의 alias stub 확인
.venv/Scripts/python -c "
text = open('docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md', encoding='utf-8').read()
assert 'FailureLabel as ErrorMode' in text
print('ok: Stage 2C task-03 stub alias')
"
```

위 통과 시 사용자에게 보고:
- 4 subtask commit hash 목록
- Verification 결과 요약
- Stage 2C task-03 의 ErrorMode 정의 (alias) 정합 확인

## 9. 부수 사항

- 영문 노트북 (`researchNotebook.en.md`) 변경 금지 — 본 plan 은 인프라 정리, 외부 노출 0
- README 변경 금지
- `experiments/measure.py` 변경 절대 금지 — score_answer 자체 변경은 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A 영역) 변경 금지 — `TrialError` 와 `FailureLabel` 의 의미 동기는 docstring 명시만
- 본 plan 의 4 subtask 모두 합쳐 ~30 분~1 시간 작업 분량 (작은 reference + 1 enum 추가)

## 10. 다음 단계 (Stage 2B 마감 후)

Stage 2B 마감 후:
1. Architect 가 Stage 2C 진행 (별도 prompt: `docs/prompts/2026-04-30/h4RecheckStart.md`)
2. Stage 2B + 2C 모두 마감 후 → Stage 3 (Exp11 의제 — Mixed Intelligence) 사용자 호출

준비되었으면 task-01 부터 시작. 보고는 한국어.
