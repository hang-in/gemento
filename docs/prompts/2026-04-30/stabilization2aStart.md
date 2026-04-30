---
type: prompt
status: ready
updated_at: 2026-04-30
for: Sonnet (Developer)
plan: stabilization-healthcheck-abort-meta-pre-exp11
purpose: Stage 2A 작업 시작 신호 — Architect (Opus) 가 작성한 plan 을 Developer 가 그대로 진행
---

# Stage 2A 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. 본 프롬프트는 self-contained — 이전 대화 컨텍스트 없이도 진행 가능.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 2A plan 을 그대로 진행한다.

## 0. 핵심 규칙 (위반 즉시 중단)

- **Plan 문서 그대로 진행**. 임의 reorder / scope 확장 / 파일 추가 금지.
- **각 subtask 의 "Changed files" 만 수정**. 다른 파일은 read-only.
- **"Scope boundary" 절 엄수**. 위반 직전이면 멈추고 사용자 호출.
- **Risk 발견 시 즉시 보고**. 임의 우회 금지.
- **메모리 정책**: 실험 실행 (모델 호출 / dry-run 등) 은 사용자 직접. Developer 는 코드 / 문서만. Task 05 의 dry-run 도 사용자 차례.
- **사용자 결정 의존 사항** 의 default 값 그대로 사용. 결정 1-4 는 plan 본문에 확정 표시 — 변경 금지.

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
# 기대: 최신 commit 00807a6 (Stage 2A 결정 1-4 + (a)~(d) 반영)
```

## 2. 읽어야 할 plan 파일 (순서대로)

```bash
# parent plan
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11.md

# subtask
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11-task-01.md  # group A, 시작
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11-task-02.md  # group A, depends_on [01]
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11-task-03.md  # group B, 병렬 가능
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11-task-04.md  # group B, depends_on [03]
docs/plans/stabilization-healthcheck-abort-meta-pre-exp11-task-05.md  # depends_on [02, 04], 사용자 직접 실행
```

## 3. 사용자 결정 1-4 (확정 — 변경 금지)

| 결정 | 값 |
|------|---|
| healthcheck/abort 정책 | (b) + (d) 조합 — 단일 fatal error 즉시 abort + 저장 직전 error 비율 검사 |
| error 비율 임계값 | 0.30 (`check_error_rate(trials, threshold=0.30)`) |
| helper 모듈 위치 | `experiments/run_helpers.py` |
| model_endpoint 마스킹 | 도입 안 함 (사용자: 현재 로컬/LAN lmstudio `http://192.168.1.179:1234` (RFC1918 사설 IP) 사용, 외부 endpoint 미사용) |

## 4. 진행 순서 (의존성 그래프)

```
Stage 1 (병렬 가능):
  Group A:                          Group B:
    task-01 (helper + run_append)    task-03 (meta helper + schema 문서)
       │                                │
       ▼                                ▼
    task-02 (모든 run.py 적용)        task-04 (analyze backward-compat)
       │                                │
       └──────────────┬─────────────────┘
                      ▼
              Stage 2 (단독, 사용자 직접):
                task-05 (dry-run 검증)
```

권장 순서: **task-01 → task-02 → task-03 → task-04** 직렬 진행. group A/B 병렬 진행 시도 금지 (한 번에 한 subtask 만 — context 안정).

## 5. 각 subtask 진행 패턴

각 subtask 마다:

1. **subtask 파일 read** (Step 1, 2, ... 와 Verification / Risk / Scope boundary 모두 숙지)
2. **Step 순서대로 실행** — 코드 수정 / 신규 파일 작성 / import 추가 등
3. **Verification 명령 실행 + 결과 캡처**. 실패 시 즉시 멈추고 사용자 호출
4. **commit message 초안 작성** — subtask 단위 commit. `docs(stage-2a-task-NN): <summary>` 형식. 각 subtask 마다 별도 commit
5. **다음 subtask 로 이동 전 사용자 confirm**. "task-01 완료. task-02 진행해도 되는가?" 형식

## 6. 사용자 호출 분기 (즉시 호출 의무)

- 검증 명령 실패
- Plan 영역 외 파일 수정이 정당하다고 판단되는 경우 (Scope boundary 위반 직전)
- subtask 내 Step 의 코드 stub 이 실제 코드 구조와 충돌
- 임의 결정이 필요한 상황 (plan 에 명시되지 않은 패턴)

위 외의 일반 진행은 Developer 권한 — 사용자 confirm 만 받으면 됨.

## 7. Task 05 특이사항 (사용자 직접 실행)

Task 05 = dry-run 통합 검증. **사용자 직접 실행** (메모리 정책).
Developer 는:
- 명령 명시 (`docs/prompts/2026-04-30/...` 또는 task-05 의 Step 1 그대로)
- `docs/reference/stabilization-dryrun-2026-04-30.md` 보고서의 placeholder (`<FILL>`) 형식 미리 작성
- 사용자가 명령 실행 후 결과 보고하면 Developer 가 placeholder 채움
- 회귀 발견 시 Architect 호출 (사용자 + Architect 양쪽)

Developer 가 직접 모델 서버 호출 / 결과 JSON 생성 / abort 동작 검증 **금지**.

## 8. Stage 2A 완료 신호

5 subtask 모두 완료 + Verification 5종 통과 + dry-run 보고서 placeholder 0:

```bash
# 최종 검증
.venv/Scripts/python -c "
from experiments.run_helpers import (
    TrialError, classify_trial_error, is_fatal_error,
    check_error_rate, build_result_meta, get_taskset_version,
    normalize_sampling_params, parse_result_meta,
)
print('ok: 모든 helper import')
"

# placeholder 0
grep -E '<FILL[^>]*>' docs/reference/stabilization-dryrun-2026-04-30.md | wc -l
# 기대: 0

# resultJsonSchema.md 존재 + canonical
grep -c 'canonical: true' docs/reference/resultJsonSchema.md
# 기대: 1
```

위 통과 시 사용자에게 보고:
- 5 subtask commit hash 목록
- Verification 결과 요약
- 회귀 / 미해결 항목 (있다면)

이후 사용자가 plan status 를 `in_progress` → `done` 으로 변경 신호 + Architect (Opus) 가 Stage 2B / 2C 로 진행.

## 9. 부수 사항

- 영문 노트북 (`researchNotebook.en.md`) 변경 금지 — 본 plan 은 README / 노트북 변경 0 정책 (외부 노출 톤 보존)
- 직전 사고 (Exp09 5-trial WinError 10061 dilute) 가 본 plan 의 동기. 이 사고를 다시 일으키지 않는 것이 본 plan 의 본질. 코드 작성 시 이 사고 시나리오 의식
- Stage 2A 마감 후 Architect 가 Stage 2B / 2C 진행 — Developer 는 Stage 2A 만 책임

준비되었으면 task-01 부터 시작. 보고는 한국어.
