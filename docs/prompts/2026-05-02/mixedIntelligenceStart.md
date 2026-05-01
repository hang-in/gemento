---
type: prompt
status: ready
updated_at: 2026-05-02
for: Sonnet (Developer)
plan: exp11-mixed-intelligence-haiku-judge
purpose: Stage 4 Exp11 진행 신호 — Mixed Intelligence (Haiku Judge C)
prerequisites: Stage 2A + 2B + 2C 모두 마감
---

# Stage 4 (Exp11) 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 4 (Exp11 Mixed Intelligence) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정. 다른 read-only
- Scope boundary 위반 직전이면 멈추고 보고
- Risk 발견 시 즉시 보고
- 사용자 결정 1-10 모두 확정 (Architect 위임). 변경 금지
- Task 04 = **사용자 직접 실행** — Sonnet 모델 호출 금지

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
# 기대: 최신 commit (Stage 4 Exp11 plan 작성 후) 동기
```

**prerequisite 검증**:

```bash
.venv/Scripts/python -c "
# Stage 2A
from experiments.run_helpers import (classify_trial_error, build_result_meta,
                                      parse_result_meta, check_error_rate)
# Stage 2B
from experiments.schema import FailureLabel
# Stage 2C 의 결함 disclosure (cycle-by-cycle 부재 — 본 plan task-03 에서 fix)
from experiments.exp_h4_recheck.analyze import classify_error_mode, count_assertion_turnover
print('ok: Stage 2A + 2B + 2C 마감')
"
```

## 2. 읽어야 할 plan 파일

```
docs/plans/exp11-mixed-intelligence-haiku-judge.md         # parent
docs/plans/exp11-mixed-intelligence-haiku-judge-task-01.md # group A
docs/plans/exp11-mixed-intelligence-haiku-judge-task-02.md # group B
docs/plans/exp11-mixed-intelligence-haiku-judge-task-03.md # group C, depends_on [01,02]
docs/plans/exp11-mixed-intelligence-haiku-judge-task-04.md # group D, 사용자 직접 실행
docs/plans/exp11-mixed-intelligence-haiku-judge-task-05.md # group E, 분석 + verdict + 문서
```

## 3. 사용자 결정 1-10 (Architect 위임 확정)

| 결정 | 값 |
|------|---|
| 1. Exp11 주제 | **Mixed Intelligence (Haiku Judge)** 확정 (Search Tool 보류) |
| 2. Judge 모델 | `claude-haiku-4-5-20251001` (Sonnet/Opus 회피) |
| 3. baseline 재실행 vs 재사용 | **재실행** 확정 (Stage 2C abc 의 turnover 결함 회복) |
| 4. task set | Stage 2C 의 15 task 정합 |
| 5. trial 수 | 5 trial (Stage 2C 정합) |
| 6. max_cycles | 8 (Stage 2C 정합) |
| 7. condition 구성 | 2 condition (baseline_abc + mixed_haiku_judge) |
| 8. API key 관리 | 환경 변수 `ANTHROPIC_API_KEY` |
| 9. 비용 한계 | ~$10 미만 추정 (정확한 가격 task-01 에서 확인) |
| 10. 측정 metric | 3축 (정확도 + turnover + error mode) + cost-aware (Exp10 패턴) |

## 4. 진행 순서

```
Stage 1 (병렬, plan-side):
  Group A: task-01 (anthropic_client + cost meter)
  Group B: task-02 (run_abc_chain c_caller 인자 추가, 1-2 라인 patch)
       ↓        ↓
  Group C: task-03 (run.py — 01/02 의존 + Stage 2C tattoo_history 결함 fix)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial 실험, ~25시간, 분할 권장)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H10 verdict + 문서 갱신)
```

권장: task-01 → task-02 → task-03 직렬, 그 후 task-04 사용자 호출.

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-4-task-NN): <summary>` (코드) / `docs(stage-4-task-NN): <summary>` (문서)
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 (특히 Risk 2/5 — 비용 임계, cherry-pick 의심)
- Anthropic 가격 정확한 값 확인 시 (task-01 Step 2)
- Task 04 진행 시점 (사용자 직접 실행 신호)
- Step 11 README 갱신 결정 (task-05)

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. Sonnet 책임:

1. Task 04 plan 본문의 명령 명세 (Step 1-5) 정합성 확인
2. 사용자에게 명령 제시 (분할 옵션 A 권장)
3. 사용자가 환경 변수 (`ANTHROPIC_API_KEY` + `GEMENTO_API_BASE_URL`) 설정 + 실행
4. 결과 받으면 task-05 진행
5. **Anthropic API 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + 5종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- exp-11-mixed-intelligence.md 신규
- researchNotebook.md (한국어): H10 entry + Exp11 섹션
- researchNotebook.en.md: **Closed 추가만** (기존 H 표 / 영문 수치 변경 0)
- README 갱신: **사용자 결정** (Sonnet 임의 금지)

## 9. Stage 4 완료 신호

5 subtask 완료 + 검증:

```bash
# 1) anthropic_client 동작
.venv/Scripts/python -c "
from experiments.anthropic_client import call_haiku, HaikuCostAccumulator, _calc_cost
from experiments.config import HAIKU_MODEL_ID
assert HAIKU_MODEL_ID == 'claude-haiku-4-5-20251001'
print('ok: anthropic_client + config')
"

# 2) run_abc_chain c_caller 인자
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
assert 'c_caller' in inspect.signature(run_abc_chain).parameters
print('ok: c_caller 인자')
"

# 3) exp11 도구 import
.venv/Scripts/python -c "
from experiments.exp11_mixed_intelligence.run import (
    run_baseline_abc, run_mixed_haiku_judge, CONDITION_DISPATCH,
)
assert 'baseline_abc' in CONDITION_DISPATCH
assert 'mixed_haiku_judge' in CONDITION_DISPATCH
print('ok: Exp11 도구')
"

# 4) 결과 파일 + trial 수
.venv/Scripts/python -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp11_mixed_intelligence/results/exp11_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    total += len(d['trials'])
assert total == 150, f'expected 150, got {total}'
print('ok: 150 trial')
"

# 5) 분석 보고서 + result.md
.venv/Scripts/python -c "
import os
for p in ('docs/reference/results/exp-11-mixed-intelligence.md',):
    assert os.path.exists(p), f'{p} missing'
print('ok: 문서 갱신')
"
```

위 통과 시 사용자에게 보고:
- 5 subtask commit hash + Verification 결과
- H10 verdict + ablation 핵심 수치
- Stage 5 (SQLite / Search Tool 재검토) 진입 신호

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H 표 (H1~H9c) 변경 절대 금지
- README 갱신 = 사용자 결정 (verdict 변화 영향)
- `experiments/measure.py` 변경 금지
- `experiments/system_prompt.py` 변경 금지 (Judge prompt 검증만)
- `experiments/schema.py` 변경 금지
- `experiments/run_helpers.py` (Stage 2A) 변경 금지
- 본 plan 영역 외 다른 도구 (`exp_h4_recheck` / `exp10_*` 등) 변경 금지

## 11. 다음 단계 (Stage 4 마감 후)

1. Architect 가 Stage 5 (SQLite ledger / Search Tool 등 큰 인프라 재검토) 사용자 호출
2. H10 결과 + Stage 2C H4 결과 종합하여 다음 외부화 축 결정
3. Exp12 (Search Tool / Extractor / Reducer 등) 후보 확정

준비되었으면 task-01 부터 시작. 보고는 한국어.
