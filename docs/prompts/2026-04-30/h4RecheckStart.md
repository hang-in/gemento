---
type: prompt
status: ready
updated_at: 2026-04-30
for: Sonnet (Developer)
plan: exp06-h4-recheck-expanded-taskset-pre-exp11
purpose: Stage 2C 작업 시작 신호 — Exp06 H4 재검증 (확대 task set + 3 condition ablation)
prerequisites: Stage 2A 마감 (commit c0e18c9) + Stage 2B 마감 (FailureLabel enum 도입)
---

# Stage 2C 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. 본 프롬프트는 self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 2C plan 을 그대로 진행한다. **사용자 명시: Exp11 전 마감 의무**.

## 0. 핵심 규칙 (위반 즉시 중단)

- **Plan 문서 그대로 진행**. 임의 reorder / scope 확장 금지
- **각 subtask 의 "Changed files" 만 수정**. 다른 파일 read-only
- **"Scope boundary" 절 엄수**. 위반 직전이면 멈추고 사용자 호출
- **Risk 발견 시 즉시 보고**. 임의 우회 금지
- **사용자 결정 1-8 모두 확정** (Architect 가 사용자 위임 받아 결정). 변경 금지
- **신규 3 task 정답 = Architect 검증 완료** — Sonnet 가 task 정의 변경 / 시각 검토 의무 0
- **메모리 정책**: Task 04 = **사용자 직접 실행** (15 task × 3 condition × 5 trial = 225 trial). Sonnet 는 명령 명세 + 보고서 placeholder 까지만. 모델 호출 금지

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
# 기대: 최신 commit fc1c0a5 (Stage 2C 정정) 또는 그 이후 (Stage 2B 마감 commits 포함)
```

**Stage 2A 마감 검증** (필수 prerequisite):

```bash
.venv/Scripts/python -c "
from experiments.run_helpers import (
    classify_trial_error, is_fatal_error, check_error_rate,
    build_result_meta, get_taskset_version, normalize_sampling_params,
    parse_result_meta,
)
print('ok: Stage 2A helper 마감')
"
```

**Stage 2B 마감 검증** (Task 03 의 FailureLabel alias 의무):

```bash
.venv/Scripts/python -c "
from experiments.schema import FailureLabel
labels = [l.value for l in FailureLabel]
assert 'connection_error' in labels and 'evidence_miss' in labels
print('ok: Stage 2B FailureLabel 마감')
"
```

위 둘 다 통과해야 본 plan 진행. 미통과 시 사용자 호출 (Stage 2A/2B 미마감).

## 2. 읽어야 할 plan 파일 (순서대로)

```
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11.md         # parent
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-01.md # group A, 신규 3 task 정의
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-02.md # group B, 3 condition + run.py
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md # group C, 분석 helper (FailureLabel alias)
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-04.md # group D, 사용자 직접 실행
docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-05.md # group E, 분석 + verdict + 문서
```

## 3. 사용자 결정 1-8 (Architect 위임 확정 — 변경 금지)

| 결정 | 값 |
|------|---|
| 1. task 수 확대 | task 수 (i) 12 → 15 (trial 수 (ii) 회피 — Exp09 5-trial dilute 학습) |
| 2. 새 도메인 | (d) 현 카테고리 + planning 1~2 추가 |
| 3. Solo 정의 | (iii) 둘 다 분리 측정 — Solo-1call (loop=1) + Solo-budget (loop=N) + ABC |
| 4. 측정 metric | (iv) 셋 다 — 정확도 + assertion turnover + error mode |
| 5. max_cycles N | **8** (Exp06 정합) |
| 6. 신규 1 추가 카테고리 | **synthesis** (H4 본질 — 다관점 종합에서 Role 분리 명료) |
| 7. task set 저장 위치 | **`taskset.json` append** (12 → 15) |
| 8. 영어 vs 한국어 task | **영어 통일** |

## 4. 신규 3 task 정의 (Architect 검증 완료, 변경 금지)

### planning-01 (sequential schedule, unique 정답)

```json
{
  "id": "planning-01",
  "category": "planning",
  "difficulty": "medium",
  "objective": "의존성 있는 다단계 task 의 sequential 일정 계산.",
  "prompt": "Three tasks (A, B, C) must be completed in strict sequential order: A first, then B, then C (each task depends on the previous one finishing). Task durations: A = 2 hours, B = 3 hours, C = 1 hour. A single worker handles all tasks with no preemption. The worker starts at 9:00 AM. Compute: (1) the start and end time of each task, and (2) the total elapsed time from start to finish.",
  "expected_answer": "A: 9:00 AM - 11:00 AM (2 hours). B: 11:00 AM - 2:00 PM (3 hours). C: 2:00 PM - 3:00 PM (1 hour). Total elapsed time: 6 hours.",
  "scoring_keywords": [["9:00", "11:00"], ["2:00"], ["3:00"], ["6", "hours"]],
  "constraints": [
    "Sequential order must be respected: A → B → C",
    "Single worker, no preemption",
    "Compute exact start/end times + total elapsed"
  ]
}
```

### planning-02 (critical path, unique 정답 12h)

```json
{
  "id": "planning-02",
  "category": "planning",
  "difficulty": "very_hard",
  "objective": "프로젝트 작업 그래프에서 critical path 식별 + 자원 충돌 해소.",
  "prompt": "A project has 6 tasks: A(2h), B(3h), C(1h), D(4h), E(2h), F(3h). Dependencies: B requires A, C requires A, D requires B and C, E requires D, F requires D. Available workers: 2 (each can do one task at a time, no preemption). Compute the minimum total project time. List the schedule (which worker does which task at which time) and identify the critical path.",
  "expected_answer": "Total time: 12 hours. Critical path: A → B → D → F (2+3+4+3 = 12h). Schedule: W1 does A(0-2), B(2-5), D(5-9), E(9-11). W2 idle (0-2), C(2-3), idle (3-5), idle (5-9), F(9-12). E (9-11) finishes earlier than F (9-12), so total = 12h driven by F.",
  "scoring_keywords": [["12", "hours"], ["A", "B", "D", "F"], ["critical path"]],
  "constraints": [
    "Dependencies must be respected",
    "Each worker does one task at a time",
    "Total time must be minimized"
  ]
}
```

### synthesis-05 (3 출처 모순 종합)

task-01 의 plan 본문 그대로 사용. **검증 완료 — 변경 금지**.

## 5. 진행 순서 (의존성 그래프)

```
Stage 1 (병렬 가능, plan-side):
  Group A: task-01 (taskset.json + validate_taskset 통합)
  Group B: task-02 (3 condition + run.py)
  Group C: task-03 (analyze.py — FailureLabel alias import)

       ↓ (3 group 마감 후)

Stage 2 (사용자 직접 실행):
  Group D: task-04 (15 × 3 × 5 = 225 trial)
           ⚠ Stage 2A healthcheck/abort 첫 실전 검증 무대

       ↓ (실험 결과 받은 후)

Stage 3 (분석 + verdict):
  Group E: task-05 (분석 + H4 verdict + 문서 갱신)
```

권장: **task-01 → task-02 → task-03** 직렬, 그 후 task-04 사용자 호출, task-05 분석.

## 6. 각 subtask 진행 패턴

각 subtask 마다:

1. **subtask 파일 read** (Step + Verification + Risk + Scope boundary 모두 숙지)
2. **Step 순서대로 실행**
3. **Verification 명령 실행 + 결과 캡처**
4. **commit message 초안 작성** — `feat(stage-2c-task-NN): <summary>` 형식 (task-01/02/03), `docs(stage-2c-task-05): <summary>` (task-05). task-04 는 사용자 실행 후 결과 보고 commit
5. **다음 subtask 로 이동 전 사용자 confirm**

## 7. 사용자 호출 분기 (즉시 호출 의무)

- Verification 명령 실패
- Plan 영역 외 파일 수정이 정당하다고 판단되는 경우 (Scope boundary 위반 직전)
- subtask 내 Step 의 코드 stub 이 실제 코드 구조와 충돌
- Risk 발견 시 (특히 Risk 5 — Stage 2A 마감 미확인 시 task-04 차단)
- task-04 진행 시점 (사용자 직접 실행 신호)

## 8. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. Sonnet 의 책임:

1. Task 04 plan 본문의 명령 명세 (Step 1-5) 정합성 확인
2. 사용자에게 실행 명령 제시 (옵션 A: condition 별 분할 / 옵션 B: 단일 실행)
3. 사용자 실행 후 결과 받으면 task-05 진행
4. **모델 서버 호출 / dry-run / 결과 JSON 생성 절대 금지** (메모리 정책 `feedback_agent_no_experiment_run.md`)

Task 04 의 예상 시간: **~20 시간** (3 condition × 75 trial). 분할 권장 (옵션 A).

## 9. Task 05 특이사항 (분석 + 문서 갱신)

Task 04 마감 후:
1. `analyze.py` 실행 (Sonnet 또는 사용자) — condition aggregate + ablation + task-level break-down 출력
2. 분석 보고서 작성 (`docs/reference/h4-recheck-analysis-<TS>.md`)
3. H4 verdict 결정 트리 적용 (Step 3) — 채택 / 조건부 채택 / 미결 / 기각
4. 문서 갱신:
   - `docs/reference/results/exp-06-solo-budget.md` §6 추가
   - `docs/reference/researchNotebook.md` H4 verdict 표 갱신 + Exp06 disclosure
   - `docs/reference/researchNotebook.en.md` **Closed 추가만** — "H4 recheck note (2026-MM-DD)" 신규 단락. 기존 영문 H4 entry 변경 0
   - `README.md` / `README.ko.md` 갱신은 **사용자 결정 의존** (verdict 변화 영향)

## 10. Stage 2C 완료 신호

5 subtask 모두 완료 + 검증:

```bash
# 1) taskset 15 task
.venv/Scripts/python -m experiments.validate_taskset 2>&1 | grep PASS | tail -1
# 기대: 25 PASS (15 + 10 longctx)

# 2) exp_h4_recheck/run.py + analyze.py 정합
.venv/Scripts/python -c "
from experiments.exp_h4_recheck.run import run_experiment
from experiments.exp_h4_recheck.analyze import analyze, ErrorMode
from experiments.schema import FailureLabel
assert ErrorMode is FailureLabel  # alias 동작
print('ok: Stage 2C 도구 + alias')
"

# 3) 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/h4-recheck-analysis-*.md | wc -l
# 기대: 0

# 4) 영문 노트북 추가만 (기존 H4 entry 보존)
grep -c "H4 recheck note" docs/reference/researchNotebook.en.md
# 기대: 1
```

위 통과 시 사용자에게 보고:
- 5 subtask commit hash 목록
- 분석 결과 요약 (3 ablation Δ + verdict)
- 다음 단계 — Stage 3 (Exp11 의제) 진입 신호

## 11. 부수 사항

- 영문 노트북 정책 — **Closed 추가만**. 기존 영문 H4 verdict (`⚠ Inconclusive`) 변경 절대 금지. Task 05 에서 새 단락 추가만
- README 변경은 사용자 결정 (Task 05 Step 8). Sonnet 임의 갱신 금지
- `experiments/measure.py` 변경 절대 금지
- `experiments/orchestrator.py` 변경 절대 금지 — ABC chain 구조 보존
- `experiments/schema.py` 변경 금지 (Stage 2B 영역 — `FailureLabel` 만 추가됨)
- `experiments/tasks/longctx_taskset.json` 변경 금지 (본 plan 영역 외)
- 본 plan = Mixed Intelligence (Stage 3 Exp11) 의 가설 정합성 회복이 목적. **H4 기각 결과** 도 의미 있음 — Stage 3 의제 재검토 신호

## 12. 다음 단계 (Stage 2C 마감 후)

Stage 2C 마감 후:
1. Architect 가 Stage 3 의제 (Mixed Intelligence vs Search Tool) 사용자 호출
2. 사용자가 Exp11 주제 확정
3. Architect 가 Exp11 plan 작성 (Stage 4)

준비되었으면 task-01 부터 시작. 보고는 한국어.
