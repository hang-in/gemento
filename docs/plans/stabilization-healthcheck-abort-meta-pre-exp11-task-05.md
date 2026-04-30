---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: stabilization-healthcheck-abort-meta-pre-exp11
parallel_group: C
depends_on: [02, 04]
---

# Task 05 — dry-run 통합 검증 (사용자 직접 실행)

## Changed files

- `docs/reference/stabilization-dryrun-2026-04-30.md` — **신규**. dry-run 결과 보고서 (placeholder 0)

신규 1, 수정 0.

## Change description

### 배경

Subtask 01~04 가 모든 multi-trial 도구에 healthcheck/abort + 결과 JSON meta v1.0 + analyze 호환을 도입. 본 task 는 통합 dry-run 으로 다음을 동시 검증:

1. **신규 schema_version="1.0" 출력 확인** — 가장 단순한 도구 (예: Exp00 baseline) 1 task × 1 trial 짧은 run
2. **healthcheck/abort 동작 확인** — 모델 서버를 의도적으로 끄거나 잘못된 endpoint 로 1 trial 시도 → CONNECTION_ERROR classify + abort
3. **저장 직전 error 비율 검사 동작** — 가짜 결과 dict 의 error 비율이 30% 이상이면 저장 거부

### Step 1 — 사용자 직접 실행 (메모리 정책)

본 task 는 **사용자 직접 실행**. 메모리 정책 (`feedback_agent_no_experiment_run.md`) 준수. Architect/Developer 는 명령만 작성하고 사용자가 실행 + 결과 보고.

#### 1a — schema_version 출력 검증 (정상 path)

```powershell
# 가장 짧은 도구 1 task × 1 trial
# (도구 별 정확한 명령은 subtask 02 의 적용 결과 보고서를 참조하여 plan 진행 시 확정)
.\.venv\Scripts\python.exe -m experiments.exp00_baseline.run --tasks math-01 --trials 1
```

기대:
- 새 출력 JSON 의 top-level 에 `schema_version: "1.0"` + `model{name,engine,endpoint}` + `sampling_params` + `scorer_version` 보유
- abort 미발생 (정상 trial)
- error 비율 0%

#### 1b — healthcheck abort 동작 검증 (fatal error path)

```powershell
# 모델 서버를 끄거나 endpoint 를 잘못 지정
$env:LM_STUDIO_BASE = "http://localhost:9999"  # invalid port
.\.venv\Scripts\python.exe -m experiments.exp00_baseline.run --tasks math-01 --trials 1
```

기대:
- stdout 에 `[ABORT] ... fatal=connection_error` 출력
- 결과 JSON 저장 거부 (`SystemExit(1)`) 또는 0 trial 의 부분 결과
- exit code != 0

#### 1c — error 비율 검사 단위 테스트

```powershell
.\.venv\Scripts\python.exe -c @"
from experiments.run_helpers import check_error_rate
trials = [
    {'error': '[WinError 10061] connection refused', 'final_answer': None},
] * 5 + [
    {'error': None, 'final_answer': 'ok'},
] * 5
ok, rate = check_error_rate(trials, threshold=0.30)
assert not ok, f'expected reject, got ok with rate={rate}'
assert abs(rate - 0.5) < 0.01
print('check 1c ok: error rate 50% rejected')
"@
```

#### 1d — backward-compat 회귀 검증

직전 결과 JSON (Exp09 3-trial / Exp10 v3) 으로 analyze 스크립트 회귀:

```powershell
.\.venv\Scripts\python.exe -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.\.venv\Scripts\python.exe -m experiments.exp10_reproducibility_cost.rescore_v3
```

기대: 본 plan 도입 전 출력과 **동일** (helper 추가만, 기존 로직 변경 0). 차이 발견 시 즉시 보고.

### Step 2 — 결과 보고서 작성

`docs/reference/stabilization-dryrun-2026-04-30.md` 에 다음 형식:

```markdown
---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# Stage 2A 통합 dry-run 결과 (2026-04-30)

**Plan**: `stabilization-healthcheck-abort-meta-pre-exp11`

## 1a — schema_version="1.0" 출력 (정상 path)

명령: `.\.venv\Scripts\python.exe -m experiments.exp00_baseline.run --tasks math-01 --trials 1`

결과: <FILL — 출력 JSON 의 top-level 키 목록 + meta 값>

## 1b — healthcheck abort (fatal error path)

명령: <위와 동일, 단 endpoint 변경>

결과: <FILL — stdout 의 [ABORT] 라인 + exit code>

## 1c — error 비율 검사 단위 테스트

결과: <FILL — `check 1c ok` 출력 또는 실패 사유>

## 1d — backward-compat 회귀

| 명령 | 변경 전 출력 (직전 plan commit) | 변경 후 출력 (본 plan) | 동일 여부 |
|------|--------------------------------|------------------------|----------|
| analyze_5trial_drop --arm abc_tattoo | <FILL> | <FILL> | <FILL> |
| rescore_v3 | <FILL — condition aggregate> | <FILL> | <FILL> |

## 결정

(본 plan 도입 → ok / 회귀 발견 → 사용자 호출)

## 사용 명령 archive

(Step 1 의 4 명령 그대로 + 결과 raw 출력 일부)
```

`<FILL>` 자리는 사용자 실행 결과로 대체.

### Step 3 — 회귀 발견 시 처리

회귀 발견 시:
- subtask 별 책임 추적 — Step 1d 의 회귀가 helper 추가 외 변경에 의한 것인지 git diff 검사
- Architect 호출 + 사용자 호출 (회귀 영향 평가 + roll-back 결정)
- **Developer 가 임의 roll-back 금지**

## Dependencies

- subtask 02 완료 (모든 multi-trial 도구의 healthcheck 적용)
- subtask 04 완료 (analyze 호환 layer)
- 패키지: 표준만

## Verification

```bash
# 1) dry-run 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/stabilization-dryrun-2026-04-30.md | wc -l
# 기대: 0 (보고서 작성 후)

# 2) 보고서 status: done
.venv/Scripts/python -c "
text = open('docs/reference/stabilization-dryrun-2026-04-30.md', encoding='utf-8').read()
assert 'status: done' in text
print('verification 2 ok: 보고서 status=done')
"
```

2 명령 모두 정상 + Step 1 의 4 dry-run 통과.

## Risks

- **Risk 1 — Step 1b 의 fatal error path 가 환경 변수 / endpoint 우회 방식이 도구마다 다름**: 일부 도구는 `LM_STUDIO_BASE` 환경 변수가 아닌 config.py 의 hard-coded 값 참조. fallback: 도구별 endpoint 우회 방법 사전 정찰.
- **Risk 2 — backward-compat 회귀 false positive**: 부동소수점 정확도 / 정렬 순서 차이로 출력이 다를 가능성. **수치 / 의미** 차원 비교만 — 문자열 비교 회피.
- **Risk 3 — 사용자 실행 환경 (Windows) 의 PowerShell 경로 차이**: 직전 dry-run (Phase 1 의 rescore_v3) 에서 `.\.venv\Scripts\python.exe` 경로 우회 필요했음. plan 의 PowerShell 명령 표기 통일.
- **Risk 4 — Developer 가 본 task 를 직접 실행**: 메모리 정책 위반. Architect/Developer 는 명령 작성 + 보고서 placeholder 까지만. 사용자 직접 실행.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 본 plan 의 다른 subtask 영역 (helper / run.py / analyze) — 모두 read-only
- `experiments/orchestrator.py` / `experiments/measure.py` / `experiments/schema.py` — 본 plan 영역 외
- `experiments/tasks/*.json` — Phase 1 후속 영역
- 결과 JSON (모두 read-only)
- README / researchNotebook
- 다른 reference 문서 (stabilization-dryrun-2026-04-30.md 만 신규)
- `docs/reference/resultJsonSchema.md` — subtask 03 영역
- 다른 plan 파일

## 사용자 결정 호출 시점

- Step 1d 의 회귀 발견 시
- Step 1b 의 fatal error path 가 어느 도구에서도 재현 안 될 때 (healthcheck 가 동작 안 한다는 신호)
- 부분 결과 저장 거부 정책 (`SystemExit(1)`) 의 사용자 선호 변경 — 예: `*_partial.json` 저장 + warning 으로 변경
