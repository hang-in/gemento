---
type: prompt
status: ready
updated_at: 2026-07-02
for: Sonnet (Developer)
plan: exp23-failed-units-facet
purpose: list_failed_units preset 도구(retrieval_gap 우회) 구현 + 회귀게이트 + 3-arm A/B 드라이버
prerequisites: 오케스트레이터 신뢰성 트랙 종결(§20) + per_attempt_diag(retrieval_gap 확인, 커밋 7b0c735)
---

# Sonnet 진행 — Stage 11: Exp23 list_failed_units facet 레버

## 1. 핵심 규칙

1. **Plan 그대로**. scope 확장 금지 — orchestrator pre-stage / system_prompt 편입 / task B / aggregate_context 수정 전부 범위 밖.
2. **결정 1~4 변경 금지** (인자없는 preset / offered+mandatory 양 arm / task A n=15 / pre-stage 제외).
3. **글로벌 불변식 최우선** — `CONTEXT_TOOL_*`(read/grep)·`FACET_TOOL_*`(aggregate) 무변경. Task 02 통과 전 Task 04 금지.
4. FACET_TOOL(H21) 패턴을 정확히 미러 — 별도 스키마/함수 dict + `__init__` export.
5. **실험 실행은 사용자/에이전트(cloud/boxie)** — Sonnet 은 드라이버 파일까지. 로컬 LLM 로딩 금지.
6. 각 task: read → Step → Verification → commit → 사용자 confirm. commit 메시지 `feat(stage-11-...)`.
7. 한국어 보고, 결론 먼저.

## 2. 컨텍스트 동기

```bash
git log --oneline -3     # 7b0c735(per-attempt diag) 확인
python -m unittest discover -s experiments/tests -t .   # 62 OK baseline
```
`python` = `C:\Python\Python314\python.exe`. pytest 미설치 — **unittest**. 테스트는 **repo root**.

## 3. 읽어야 할 plan 파일

- `docs/plans/exp23-failed-units-facet.md` (parent)
- `docs/plans/exp23-failed-units-facet-task-01.md` (도구)
- `docs/plans/exp23-failed-units-facet-task-02.md` (회귀게이트)
- `docs/plans/exp23-failed-units-facet-task-03.md` (3-arm 드라이버 — 사용자 실행)
- `docs/plans/exp23-failed-units-facet-task-04.md` (분석+verdict)
- 참조: `experiments/tools/context_tools.py`(`aggregate_context`/`FACET_TOOL_*` 미러 원본), `experiments/tests/test_facet_tool.py`, `experiments/exp15_context_router/run_v21_facet_ab.py`(드라이버 인프라), `diagnostics/per_attempt_diag.py`(retrieval_gap 근거).

## 4. 사용자 결정 (parent plan mirror)

| # | 결정 | 값 |
|---|---|---|
| 1 | 레버 형태 | 인자없는 preset 도구 (aggregate_context 재사용 아님) |
| 2 | 사용 강제 | fu_offered + fu_mandatory 양 arm |
| 3 | 실험 규모 | task A, n=15/arm, 3 arm |
| 4 | pre-stage 스캐폴드 | 본 plan 제외 (후속) |

## 5. 진행 순서

```
Task 01 (도구+export)  →  Task 02 (게이트) ∥ Task 03 (3-arm 드라이버)  →  Task 04 (분석+verdict)
```

## 6. 각 subtask 패턴

- **Task 01**: `context_tools.py` `list_failed_units` + `FAILED_UNITS_TOOL_*` + `__init__` export → Verification 1~4(import/글로벌불변/fixture/실제로그) → commit → confirm.
- **Task 02**: 신규 테스트 → `discover` 62+신규 OK + `test_facet_tool` 재통과 → commit → confirm.
- **Task 03**: 3-arm 드라이버 → syntax + arm/tool/task 정적 확인 → commit → confirm. **실행 안 함.**
- **Task 04**: (사용자 A/B 실행 후) `gemento-verdict-record` 로 H23 verdict → Verification → commit → confirm.

## 7. 사용자 호출 분기

- Verification 실패 (특히 Task 01 Verification 4 실제 로그서 gohttpserver 미반환 = Risk 4) → 호출.
- Scope boundary 위반 직전 (글로벌/orchestrator/system_prompt 수정 필요) → 호출.
- Task 03 A/B **실행 필요** 시점 → 사용자/에이전트에게 넘김 (boxie 터널 §2).
- README/conceptFramework 갱신 결정 → 사용자.

## 8. 특이사항 — 사용자/에이전트 실행

Task 03 A/B 는 **사용자 또는 cloud 에이전트 실행**. Sonnet 은 `run_v23_failed_units_ab.py` 파일 + 정적 검증까지. 모델 호출 금지.

## 9. 분석 task 특이사항 (Task 04)

- placeholder 0 (TODO/TBD 금지).
- 영문 노트북 `.en.md` = Closed-append-only — 기존 문장/표 절대 수정, append 만. 표 row 무변경 검증.
- verdict 방향은 데이터 따라감 — fu_offered vs fu_mandatory 분리 기술(H21 저사용 경고 검증).

## 10. 본 plan 마감 신호

```bash
python -m unittest discover -s experiments/tests -t .          # 62 + 신규 게이트
git log --oneline -6                                            # task-01~04 커밋
grep -c "exp23-failed-units-facet" docs/plans/index.md          # Recently Done Stage 11
```

## 11. 부수 사항

- 영문 노트북 append-only 강제.
- README 갱신 = 사용자 결정.
- 변경 금지: `CONTEXT_TOOL_*`/`FACET_TOOL_*`/`aggregate_context`, orchestrator.py, system_prompt.py, 결과 JSON.

## 12. 다음 단계 (Architect, 본 plan 마감 후)

- fu_mandatory 유효 → pre-stage 스캐폴드(auto-inject, 결정 4) 편입 검토.
- offered/mandatory 모두 무효 → retrieval 넘어선 병목(§20 재확인) → a2a.
- 유효 → 도메인 facet 다종화(H21 후속) 재고.
