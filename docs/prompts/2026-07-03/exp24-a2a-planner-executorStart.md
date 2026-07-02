---
type: prompt
status: ready
updated_at: 2026-07-03
for: Sonnet (Developer)
plan: exp24-a2a-planner-executor
purpose: a2a Planner→Executor proposer 분할 opt-in 구현 + 회귀게이트 + A/B 드라이버
prerequisites: per-attempt 트랙(§20/§21) + scoped_emit_probe(scoped emit 100%, 커밋 2f23552)
---

# Sonnet 진행 — Stage 12: Exp24 a2a Planner→Executor

## 1. 핵심 규칙

1. **Plan 그대로**. scope 확장 금지 — B/C 변경 / 별도 모델 / multi-step planner / pre-stage push 전부 범위 밖.
2. **결정 1~4 변경 금지** (같은 E4B 2 스코프 호출 / Planner=텍스트 / task A n=15 2arm / B·C 무변경).
3. **기본 False 불변식 최우선** — `a2a_proposer=False` 시 A-stage = 기존 `run_loop` 문자 동일. Task 02 통과 전 Task 04 금지.
4. **Executor 는 probe 조건 재현** — finding 을 clean scoped 입력으로, **도구 없이, decompose 없이** emit (`scoped_emit_probe.py` 참고). 기존 `extract_json_from_response`+`apply_llm_response`+`LoopLog` 재사용, 신규 파서 금지.
5. **B/C 계약** — `_a2a_propose` 반환은 `run_loop` 와 동일 `(Tattoo, LoopLog, str|None, list)`.
6. **실험 실행은 사용자/에이전트(cloud/boxie)** — Sonnet 은 드라이버 파일까지. 로컬 LLM 로딩 금지.
7. 한국어 보고, 결론 먼저. commit `feat(stage-12-...)`.

## 2. 컨텍스트 동기

```bash
git log --oneline -3     # 2f23552(scoped_emit_probe) 확인
python -m unittest discover -s experiments/tests -t .   # 66 OK baseline
```
`python`=`C:\Python\Python314\python.exe`. unittest(pytest 미설치). repo root 실행.

## 3. 읽어야 할 plan 파일

- `docs/plans/exp24-a2a-planner-executor.md` (parent)
- `docs/plans/exp24-a2a-planner-executor-task-01.md` ~ `-task-04.md`
- 참조: `experiments/exp15_context_router/diagnostics/scoped_emit_probe.py`(Executor 경로 검증·100%), `experiments/orchestrator.py`(`run_loop`/`apply_llm_response`/`extract_json_from_response`/`LoopLog`, A-stage `:823`), `experiments/system_prompt.py`(`SYSTEM_PROMPT`/`build_prompt`, **수정 금지**), `run_v23_failed_units_ab.py`(드라이버 인프라).

## 4. 사용자 결정 (parent plan mirror)

| # | 결정 | 값 |
|---|---|---|
| 1 | a2a 형태 | 같은 E4B 2 스코프 호출 (Planner 텍스트 → Executor emit) |
| 2 | Planner 출력 | clean 텍스트 finding (assertion 아님) |
| 3 | 실험 규모 | task A, n=15, 2 arm (control/a2a) |
| 4 | B/C 변경 | 없음 |

## 5. 진행 순서

```
Task 01 (프롬프트+a2a 경로)  →  Task 02 (게이트) ∥ Task 03 (A/B 드라이버)  →  Task 04 (분석+verdict)
```
Task 01 이 가장 큼(신중히). 02·03 병렬. 04 는 둘 다 + 사용자 실행 후.

## 6. 각 subtask 패턴

- **Task 01**: system_prompt.py(Planner/Executor 빌더) + orchestrator.py(파라미터+분기+`_a2a_propose`) → Verification 1~4(터널시 smoke) → commit → confirm. **`_a2a_propose` 는 모듈 레벨 def** 권장(Task 02 test_helper 가 `inspect.getsource(orchestrator._a2a_propose)` 사용 — 내부 def 로 두면 Task 02 검사식 조정 필요).
- **Task 02**: 신규 테스트 → discover 66+신규 OK + 기존 게이트 재통과 → commit → confirm.
- **Task 03**: 드라이버 → syntax + arm/flag/task 정적 → commit → confirm. **실행 안 함.**
- **Task 04**: (사용자 A/B 후) `gemento-verdict-record` 로 H24 → Verification → commit → confirm.

## 7. 사용자 호출 분기

- Verification 실패(특히 Task 01 smoke 에서 a2a 가 assertion emit 못 하면 = 설계 문제) → 호출.
- Scope boundary 위반 직전(SYSTEM_PROMPT/B/C/run_loop 수정 필요) → 호출.
- Task 03 A/B **실행 필요** 시점 → 사용자/에이전트에게 넘김(boxie 터널; GPU 부하시 단독 arm 러너 §21).
- README/conceptFramework 갱신 결정 → 사용자.

## 8. 특이사항 — 사용자/에이전트 실행

Task 03 A/B 는 사용자/cloud 에이전트 실행. Sonnet 은 파일+정적 검증까지. a2a arm 은 호출 2배라 GPU 부하 심화 가능 — 단독 arm 러너 대비(§21 `run_v23_mandatory_only.py` 패턴).

## 9. 분석 task 특이사항 (Task 04)

- placeholder 0. 영문 `.en.md` Closed-append-only(표 무변경). verdict 데이터 따라감 — a2a 유효해도 **비용(호출 2배) 대비 retry 와 비교** 명시.

## 10. 본 plan 마감 신호

```bash
python -m unittest discover -s experiments/tests -t .          # 66 + 신규 게이트
git log --oneline -6                                            # task-01~04 커밋
grep -c "exp24-a2a-planner-executor" docs/plans/index.md        # Recently Done Stage 12
```

## 11. 부수 사항

- 영문 append-only 강제. README 사용자 결정. 변경 금지: SYSTEM_PROMPT/build_prompt/critic/judge/run_loop 본문, B/C 경로, 결과 JSON.

## 12. 다음 단계 (Architect, 본 plan 마감 후)

- a2a 유효 → Critic/Judge 도 스코프 분할 검토(별도 plan) / 비용-정확도 파레토.
- a2a 무효 → **per-attempt = retry 수용** 최종 확정(H22/H23/H24 3중 음성) → 다른 축(도메인 확장/크로스모델)으로.
