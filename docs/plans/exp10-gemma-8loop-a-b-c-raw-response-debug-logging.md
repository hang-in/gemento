---
type: plan
status: done
completed_at: 2026-04-27  # auto-set 2026-05-03 stale cleanup
updated_at: 2026-04-27
slug: exp10-gemma-8loop-a-b-c-raw-response-debug-logging
version: 1
---

# Exp10 gemma_8loop A/B/C raw response debug logging

## Description

Codex CLI 가 `docs/reference/handoff-to-opus-exp10-2026-04-27.md` 에서 보고한 권고 3 — **gemma_8loop A/B/C raw response debug logging 추가** — 를 v2 재실행 전에 적용한다.

현재 `experiments/exp10_reproducibility_cost/run.py:trial_gemma_8loop()` 는 `run_abc_chain()` 에서 받은 `abc_logs: list[ABCCycleLog]` 의 길이만 사용하고 (`actual_cycles = len(abc_logs)`), 본문은 폐기한다. 그러나 `ABCCycleLog` 는 이미 `b_raw` / `c_raw` (그리고 nested `LoopLog.raw_response` for A) 를 capture 중이라, 결과 JSON 에 `_debug.abc_logs` 필드만 추가하면 사후 분석이 가능해진다.

크기 통제: 각 raw 필드를 **4KB (4096 char) truncate**. 540 trial 중 gemma_8loop 180 trial 만 영향. 예상 결과 JSON 추가 크기 ~17 MB (truncate 후), git push 가능 범위.

상위 목표: Exp10 v2 재실행 (사용자 직접 터미널 실행) 시점에 결과 JSON 이 분석 가치 있는 디버그 정보 보유 → researchNotebook Exp10 분석 + 한국어 응답 패널티 (권고 4) 사후 rescoring 의 입력.

## Expected Outcome

1. `experiments/exp10_reproducibility_cost/run.py:trial_gemma_8loop()` 의 return dict 에 신규 `_debug` 필드 추가.
2. `_debug.abc_logs` 가 `list[dict]` — 각 dict 는 `{"cycle": int, "phase": str, "a_raw": str, "a_error": str|None, "b_raw": str, "b_error": str|None, "c_raw": str, "c_error": str|None, "phase_transition": str|None}` 구조.
3. 각 raw 필드 4096 char truncate. 끝에 `... (truncated, original_len=N)` 표시 (truncate 발생 시).
4. `gemma_1loop` / `gemini_flash_1call` 의 trial 함수는 변경 없음 — 단일 호출이라 abc_logs 무관.
5. `experiments/tests/test_static.py` 에 `TestExp10DebugLoggingSchema` 신규 — `_debug.abc_logs` 의 schema 검증. dummy `ABCCycleLog` fixture 로 직렬화 helper 검증, LLM 호출 0.
6. v2 재실행 결과 JSON 의 gemma_8loop 180 trial 모두 `_debug.abc_logs` 필드 보유 — Codex 의 "parse fail 사후 분석" 가능 상태.
7. 결과 JSON 크기 +17 MB 이내 (truncate 후), git push 가능.

## Subtask Index

1. [task-01](./exp10-gemma-8loop-a-b-c-raw-response-debug-logging-task-01.md) — trial_gemma_8loop debug logging 추가 (parallel_group A, depends_on: [])
2. [task-02](./exp10-gemma-8loop-a-b-c-raw-response-debug-logging-task-02.md) — test_static 에 schema 정합성 테스트 추가 (parallel_group B, depends_on: [01])

### 의존성 (Stage 기반)

```
Stage 1 (단독):
  task-01 (debug logging 추가 — _debug.abc_logs)
       │
       ▼ (헬퍼 함수 + dict schema 확정 후)
Stage 2 (단독):
  task-02 (정합성 정적 테스트 추가)
```

순차 진행 권고 — task-01 의 helper 함수 시그니처가 task-02 의 schema 검증 input.

## Constraints

- **orchestrator.py 변경 금지**: `LoopLog.raw_response`, `ABCCycleLog.b_raw`/`c_raw` 가 이미 capture 중. 본 plan 영역 외.
- **gemma_1loop / gemini_flash_1call 변경 금지**: 단일 호출이라 abc_logs 없음. trial_gemma_8loop 만 영향.
- **truncate 4KB 정책 고정**: 각 raw 필드 4096 char 초과 시 truncate. 결과 JSON 크기 ~17 MB 이내 유지.
- **JSON 직렬화 호환**: `dataclasses.asdict()` 또는 manual extraction. nested 구조 (LoopLog 안의 tattoo_in/out dict) 도 직렬화 가능.
- **v1 재실행 시점 호환**: 본 plan 적용 후 결과 JSON 의 schema 가 변경됨. analyze.py 가 `_debug` 필드를 무시하도록 (analyze.py 의 aggregate 함수가 `_debug` 키 미참조 — 현재 코드 검증 필요).
- **결과 동일성 보장**: 본 plan 은 result dict 에 필드 *추가* 만. 기존 필드 (`accuracy`, `final_answer` 등) 변경 0 → analyze.py 의 통계 결과 동일.
- **Reviewer 가드**: LLM 호출 0. 정적 검증만.
- **arXiv timeline 의식**: 작은 plan, ~30 분 작업. v2 재실행 (5-12h) 전 완료 가능.

## Non-goals

- orchestrator.py 의 raw capture 수정 — 이미 OK.
- gemma_1loop / gemini_flash 의 raw 저장 — 단일 호출 함수. 별도 plan.
- Codex 권고 4 (한국어 응답 채점 패널티) — 별도 plan.
- analyze.py 가 `_debug.abc_logs` 를 분석에 사용 — 별도 plan (v2 결과 받은 후 결정).
- raw response 의 정밀 분석 자동화 — analyze.py 영역, 별도 plan.
- truncate 정책 변경 (4KB 외) — 본 plan 내 결정. 향후 변경 시 별도 plan.
- v1 결과 JSON 정정 — 무효 데이터, 그대로 둠.

## 변경 이력

- 2026-04-27 v1: 초안. v2 재실행 전 적용.
