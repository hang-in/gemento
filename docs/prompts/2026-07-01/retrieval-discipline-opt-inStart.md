---
type: prompt
status: ready
updated_at: 2026-07-01
for: Sonnet (Developer)
plan: retrieval-discipline-opt-in
purpose: retrieval-discipline nudge 를 system_prompt/orchestrator opt-in 으로 편입 + 회귀게이트 + 재검증 드라이버
prerequisites: Stage 9(Exp21) 마감 (b763f81), 오케스트레이터 신뢰성 진단 완료 (diagnostics/, 레버 A/B +50pp)
---

# Sonnet 진행 — Stage 10: retrieval-discipline opt-in 편입

## 1. 핵심 규칙

1. **Plan 그대로** 진행. scope 확장 금지 — 자동 게이트 / `MANDATORY_TOOL_RULES` 수정 / a2a / facet 강제 전부 범위 밖.
2. **결정 1~4 변경 금지** (별도 독립 플래그 / `system_prompt.py` 위치 / nudge 문구 보존 / mandatory→discipline 순서).
3. **기본 False 불변식이 최우선** — Task 02 회귀 게이트 통과 전 Task 04 진행 금지.
4. `MANDATORY_TOOL_RULES` 는 **read-only** (Exp16b 검증 보존). lever_test.py `NUDGE` 핵심 문구 보존.
5. **재검증 실행(Task 03)은 사용자** — Sonnet 은 드라이버 파일까지. 로컬 LLM 로딩 / 긴 실험 실행 금지.
6. 각 task: read → Step → Verification → commit → 사용자 confirm. commit 메시지는 repo 관례(`feat(stage-10-...)`).
7. 사용자 언어(한국어)로 보고, 결론 먼저.

## 2. 컨텍스트 동기

```bash
git log --oneline -3          # dbf3bea(handoff) 확인, 로컬 main
python -m unittest discover -s experiments/tests -t .   # 56 OK (baseline)
```
`python` = `C:\Python\Python314\python.exe`. pytest 미설치 — **unittest**. 테스트는 **repo root** 에서 (cwd=experiments 는 경로 아티팩트).

## 3. 읽어야 할 plan 파일

- `docs/plans/retrieval-discipline-opt-in.md` (parent)
- `docs/plans/retrieval-discipline-opt-in-task-01.md` (code)
- `docs/plans/retrieval-discipline-opt-in-task-02.md` (회귀 게이트)
- `docs/plans/retrieval-discipline-opt-in-task-03.md` (재검증 드라이버 — 사용자 실행)
- `docs/plans/retrieval-discipline-opt-in-task-04.md` (문서 + verdict)
- 참조: `experiments/exp15_context_router/diagnostics/lever_test.py` (NUDGE 원문), `lever_test_result.json` (레버 결과), `docs/plans/mandatory-tool-opt-in.md` (자매 패턴).

## 4. 사용자 결정 (parent plan mirror)

| # | 결정 | 값 |
|---|---|---|
| 1 | 편입 방식 | 별도 독립 opt-in 파라미터 (MANDATORY 병합 X) |
| 2 | 상수 위치/이름 | `system_prompt.py` / `RETRIEVAL_DISCIPLINE_RULES` |
| 3 | 재검증 규모 | n≥10/arm, task A + task B (사용자 실행) |
| 4 | 두 플래그 순서 | mandatory 먼저, discipline 나중 |

## 5. 진행 순서

```
Task 01 (code)  →  Task 02 (regression) ∥ Task 03 (재검증 드라이버)  →  Task 04 (docs+verdict)
```
Task 01 선행. 02(테스트)와 03(드라이버)은 병렬 가능. 04 는 02 통과 + 사용자 재검증 결과 후.

## 6. 각 subtask 패턴

- **Task 01**: `system_prompt.py` 상수 추가(선행 `\n\n`) + `orchestrator.py` 파라미터·가드 추가 → Verification 1~4 (syntax / 상수 문구 / 파라미터 default False / MANDATORY 무변경) → commit → confirm.
- **Task 02**: 신규 테스트 파일 → `python -m unittest discover -s experiments/tests -t .` 56 OK + 신규 + 기존 `test_mandatory_optin` 재통과 → commit → confirm.
- **Task 03**: 드라이버 파일 작성 → syntax + arm/task 정적 확인 (Verification 1~2) → commit → confirm. **실행 안 함.**
- **Task 04**: (사용자 재검증 후) `gemento-verdict-record` 스킬로 verdict → conceptFramework 가이드 → Verification → commit → confirm.

## 7. 사용자 호출 분기

- Verification 실패 → 원인 보고 후 사용자 호출 (임의 우회 금지).
- Scope boundary 위반 직전 (MANDATORY 수정 / 다른 경로 변경 필요) → 호출.
- Risk 발견 (특히 기본 False 비불변, nudge 문구 drift) → 호출.
- Task 03 재검증 **실행 필요** 시점 → 사용자에게 넘김 (터널 재수립 + 메가로그 재pull 핸드오프 §2).
- README / README.ko 갱신 결정 → 사용자.

## 8. 특이사항 — 사용자 직접 실행

Task 03 재검증은 **사용자 실행**. Sonnet 은 `run_v22_retrieval_discipline.py` 파일 작성 + 정적 검증까지. 모델 호출 / 터널 실행 금지. 실행 명령은 파일 docstring 에 명시.

## 9. 분석 task 특이사항 (Task 04)

- placeholder 0 의무 (TODO/TBD/XXX 금지).
- 영문 노트북 `.en.md` = **Closed-append-only** — 기존 문장/표 절대 수정, append 만.
- verdict 방향은 재검증 데이터 따라감 — 소표본/task-specific 이면 조건부 명시.

## 10. 본 plan 마감 신호

```bash
python -m unittest discover -s experiments/tests -t .          # 56 OK + 신규 게이트
git log --oneline -6                                            # task-01~04 커밋
grep -c "retrieval-discipline-opt-in" docs/plans/index.md      # Recently Done Stage 10 등록
```

## 11. 부수 사항

- 영문 노트북 Closed-append-only 강제 (`gemento-verdict-record`).
- README 갱신 = 사용자 결정.
- 변경 금지: `MANDATORY_TOOL_RULES`, `run_abc_chain` 의 다른 경로, 결과 JSON, `run_v21_facet_ab.py`.

## 12. 다음 단계 (Architect, 본 plan 마감 후)

- 재검증이 +50pp 재현 → plan-first 로 caller 별 default-on 조건 검토.
- task-specific(집계만) → facet 강제 레버(핸드오프 §4.4 #3) 병행.
- 효과 소멸 → 강제 iteration(#2) 또는 a2a(가장 비싼 카드).
