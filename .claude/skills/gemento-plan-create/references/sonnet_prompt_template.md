# Sonnet 진행 프롬프트 템플릿

`docs/prompts/YYYY-MM-DD/<slug>Start.md` 형식. self-contained — Sonnet 이 새 세션에서 복붙으로 시작 가능해야 한다.

```markdown
---
type: prompt
status: ready
updated_at: <YYYY-MM-DD>
for: Sonnet (Developer)
plan: <slug>
purpose: <한 줄 — 본 prompt 의 역할>
prerequisites: <어떤 Stage / commit 이 마감되어야 하는가>
---

# <Stage N (Exp##)> 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 <Stage N (Exp##)> (<plan 제목>) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정
- Risk / Scope boundary 위반 직전 즉시 보고
- 사용자 결정 1-N 모두 확정 (Architect 위임 또는 사용자 직접). 변경 금지
- Task <NN> = 사용자 직접 실행 — 모델 호출 금지 (해당 시)
- 본 plan = <외부 API 사용 여부>

## 1. 컨텍스트 동기

\`\`\`bash
git pull --ff-only
git log --oneline -5
\`\`\`

**prerequisite 검증**:

\`\`\`bash
.venv/Scripts/python -c "
# Stage 2A
from experiments.run_helpers import classify_trial_error, build_result_meta, check_error_rate
# Stage 2B
from experiments.schema import FailureLabel
# <이전 Exp 의존 import>
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert '<expected option>' in sig.parameters, '<이전 Exp 미적용>'
print('ok: <prerequisite 명시>')
"
\`\`\`

## 2. 읽어야 할 plan 파일

\`\`\`
docs/plans/<slug>.md         # parent
docs/plans/<slug>-task-01.md # group A — <한 줄>
docs/plans/<slug>-task-02.md # group B — <한 줄>
docs/plans/<slug>-task-03.md # group C — <한 줄>
docs/plans/<slug>-task-04.md # group D — 사용자 직접 실행
docs/plans/<slug>-task-05.md # group E — 분석 + verdict + 문서
\`\`\`

## 3. 사용자 결정 1-N (Architect 위임 또는 사용자 직접 확정)

| 결정 | 값 |
|------|---|
| 1. <제목> | **<값>** — <이유 한 줄> |
| 2. <제목> | <값> |
| ... | ... |

## 4. 진행 순서

\`\`\`
Stage 1 (plan-side):
  Group A: task-01
       ↓
  Group B: task-02
       ↓        ↓
  Group C: task-03
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (<trial> trial, ~<시간>h)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H## + 문서)
\`\`\`

권장: task-01 → 02 → 03 직렬, 그 후 task-04 사용자 호출.

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-<N>-exp##-task-NN): <summary>` 또는 `docs(...)`
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 (특히 task-NN 의 Risk N — <중요 risk>)
- task-04 진행 시점 (사용자 직접 실행 신호)
- task-05 README 갱신 결정

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. 책임:
1. Task 04 plan 본문 명령 정합성 확인
2. 사용자에게 명령 제시
3. 사용자 결과 받으면 task-05 진행
4. **모델 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + N 종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- result.md (`docs/reference/results/exp-NN-<slug>.md`) 신규
- researchNotebook.md (한국어): H## entry + Exp## 섹션 + 축 매트릭스
- researchNotebook.en.md: **Closed 추가만**
- README 갱신: **사용자 결정**

## 9. <Stage N Exp##> 완료 신호

<N> subtask 완료 + 검증:

\`\`\`bash
# 1) 도구 import
.venv/Scripts/python -c "
<key import + signature check>
print('ok: <plan 마감 신호>')
"

# 2) trial 수 = <expected>
# 3) 분석 보고서 + result.md 신규
\`\`\`

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H1~H## entry 변경 절대 금지
- README 갱신 = 사용자 결정
- `experiments/measure.py` / `system_prompt.py` 의 기존 prompt / `schema.py` / `run_helpers.py` 변경 금지
- <이전 Exp 의 hook> — orchestrator 의 read-only 보존

## 11. 다음 단계 (<Stage N Exp##> 마감 후)

마감 후 Architect 가:
1. H## verdict + <이전 Exp> 비교 결과
2. <다음 Exp 후보> 결정 — <후보 1> / <후보 2> / <후보 3>
3. <인프라 후보> 결정

준비되었으면 task-01 부터 시작. 보고는 한국어.
```

## 작성 시 주의

- **self-contained 의무**: Sonnet 이 본 prompt 만 보고 시작 가능해야. 즉 plan 파일 list, 사용자 결정, 진행 순서, 검증 명령이 모두 본 prompt 안에 있어야.
- **prerequisite 검증 명령은 정확히**: 이전 Stage 가 적용되지 않은 환경에서 시작 시 즉시 fail 해야. import + signature check 둘 다 권장.
- **사용자 결정 표는 parent plan 의 결정 N 표를 그대로 mirror**.
- **사용자 호출 분기 의 Risk 항목** = parent plan 의 Risks 중 가장 중요한 것 1-2 개 인용.
