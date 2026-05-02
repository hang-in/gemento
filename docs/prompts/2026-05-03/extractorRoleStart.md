---
type: prompt
status: ready
updated_at: 2026-05-03
for: Sonnet (Developer)
plan: exp12-extractor-role-pre-search
purpose: Stage 5 Exp12 진행 신호 — Extractor Role (Search Tool 이전 Role 축 확장)
prerequisites: Stage 2A + 2B + 2C + Stage 4 (Exp11) 모두 마감
---

# Stage 5 (Exp12) 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 5 Exp12 (Extractor Role) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정
- Risk / Scope boundary 위반 직전 즉시 보고
- 사용자 결정 1-7 모두 확정 (Architect 위임). 변경 금지
- Task 04 = **사용자 직접 실행** (모델 호출 금지)
- 본 plan 은 **외부 API 호출 0** — local Gemma 만 사용 (Exp11 Mixed 의 정반대 메커니즘 회피)

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
# 기대: 최신 commit (Stage 5 Exp12 plan 작성 후) 동기
```

**prerequisite 검증**:

```bash
.venv/Scripts/python -c "
# Stage 2A
from experiments.run_helpers import (classify_trial_error, build_result_meta, check_error_rate)
# Stage 2B
from experiments.schema import FailureLabel
# Stage 2C
from experiments.exp_h4_recheck.analyze import classify_error_mode, count_assertion_turnover
# Stage 4 Exp11
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'c_caller' in sig.parameters, 'Exp11 c_caller 미적용'
print('ok: Stage 2A + 2B + 2C + Stage 4 마감')
"
```

## 2. 읽어야 할 plan 파일

```
docs/plans/exp12-extractor-role-pre-search.md         # parent
docs/plans/exp12-extractor-role-pre-search-task-01.md # group A
docs/plans/exp12-extractor-role-pre-search-task-02.md # group B, depends_on [01]
docs/plans/exp12-extractor-role-pre-search-task-03.md # group C, depends_on [01,02]
docs/plans/exp12-extractor-role-pre-search-task-04.md # group D, 사용자 직접 실행
docs/plans/exp12-extractor-role-pre-search-task-05.md # group E, 분석 + verdict + 문서
```

## 3. 사용자 결정 1-7 (Architect 위임 확정)

| 결정 | 값 |
|------|---|
| 1. Extractor 모델 | **Gemma 4 E4B (동일)** — Exp11 정반대 메커니즘 회피, 외부 API 0 |
| 2. Extractor schema | JSON `{claims, entities}` |
| 3. 호출 시점 | trial 시작 시 1회 (cycle 별 반복 회피) |
| 4. task set / trial / cycles | Stage 2C 정합 (15 / 5 / 8) |
| 5. condition 구성 | 2 condition (baseline_abc + extractor_abc) |
| 6. Extractor prompt | simple JSON 추출 (SYSTEM_PROMPT 의 phase / assertion 관리 부재) |
| 7. 메커니즘 측정 | assertion turnover (Stage 2C analyze 재사용) + first cycle assertions |

## 4. 진행 순서

```
Stage 1 (plan-side):
  Group A: task-01 (EXTRACTOR_PROMPT + build_extractor_prompt)
       ↓
  Group B: task-02 (orchestrator extractor_pre_stage hook)
       ↓        ↓
  Group C: task-03 (run.py — Exp11 패턴 그대로 + CONDITION_DISPATCH 변경)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial, ~25h)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H11 + 문서)
```

권장: task-01 → 02 → 03 직렬, 그 후 task-04 사용자 호출.

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-5-task-NN): <summary>` (코드) / `docs(stage-5-task-NN): <summary>` (문서)
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 (특히 task-01 의 Risk 3 — synthesis/logic-02 같은 task 에서 Extractor 가 잘못 추출)
- task-04 진행 시점 (사용자 직접 실행 신호)
- task-05 의 README 갱신 결정

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. 책임:
1. Task 04 plan 본문 명령 정합성 확인
2. 사용자에게 명령 제시 (분할 옵션 권장)
3. 사용자가 환경 변수 (`GEMENTO_API_BASE_URL`) 설정 + 실행
4. 결과 받으면 task-05 진행
5. **모델 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + 5종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- exp-12-extractor-role.md 신규
- researchNotebook.md (한국어): H11 entry + Exp12 섹션 + 축 매트릭스
- researchNotebook.en.md: **Closed 추가만**
- README 갱신: **사용자 결정** (Sonnet 임의 금지)

## 9. Stage 5 (Exp12) 완료 신호

5 subtask 완료 + 검증 (Exp11 task-05 패턴):

```bash
# 1) 도구 import + 시그니처
.venv/Scripts/python -c "
from experiments.system_prompt import EXTRACTOR_PROMPT, build_extractor_prompt
from experiments.exp12_extractor_role.run import (
    run_baseline_abc, run_extractor_abc, CONDITION_DISPATCH,
)
import inspect
from experiments.orchestrator import run_abc_chain
assert 'extractor_pre_stage' in inspect.signature(run_abc_chain).parameters
print('ok: Exp12 도구')
"

# 2) 결과 파일 + trial 수 = 150
.venv/Scripts/python -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp12_extractor_role/results/exp12_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    total += len(d['trials'])
assert total == 150
print('ok: 150 trial')
"

# 3) 분석 보고서 + result.md 신규
.venv/Scripts/python -c "
import os
for p in ('docs/reference/results/exp-12-extractor-role.md',):
    assert os.path.exists(p)
print('ok: exp-12 result.md')
"
```

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H1~H10 entry 변경 절대 금지
- README 갱신 = 사용자 결정
- `experiments/measure.py` / `system_prompt.py` 의 기존 prompt / `schema.py` / `run_helpers.py` 변경 금지
- `experiments/_external/gemini_client.py` 변경 금지 (Exp11 영역, 본 plan 영역 외)
- Exp11 의 `c_caller` 분기 — orchestrator 의 read-only 보존
- 본 plan = Exp11 마감 (H10 ⚠ 미결) 후 Architect 권장 방향. Search Tool (Exp13) 이전 Role 축 분리/추가 검증

## 11. 다음 단계 (Stage 5 Exp12 마감 후)

Exp12 마감 후 Architect 가:
1. H11 verdict 따라 Stage 5 의 다음 plan 결정
   - H11 채택 → Search Tool (Exp13) 진입
   - H11 미결/기각 → Search Tool 우선 또는 Reducer / 다른 축 검토
2. Stage 5 SQLite ledger — Exp13 (Search Tool) 결과 후 시점에 별도 결정

준비되었으면 task-01 부터 시작. 보고는 한국어.
