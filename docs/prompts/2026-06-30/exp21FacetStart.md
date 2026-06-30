---
type: prompt
status: ready
updated_at: 2026-06-30
for: Sonnet (Developer)
plan: exp21-facet-aggregate-tool
purpose: Exp21 facet 집계 도구 A/B 구현 — grep-only vs grep+facet finalization 비교
prerequisites: Stage 7/8 마감 + Exp20 finalization 진단 완료 (HEAD ~ee604f9 이후)
---

# Exp21 — Facet Aggregate Tool A/B 진행 프롬프트 (Sonnet/Developer)

## 1. 핵심 규칙

1. **Plan 그대로 구현** — `docs/plans/exp21-facet-aggregate-tool.md` + task-01~04. scope 확장 금지.
2. **결정 표 값 변경 금지** (parent plan 결정 1~6). 이견은 사용자 호출.
3. **`orchestrator.py` 수정 금지.** facet 은 `context_tools.py`(도구) + `native_ollama_caller.py`(opt-in 주입)에서만.
4. **글로벌 `CONTEXT_TOOL_SCHEMAS`/`CONTEXT_TOOL_FUNCTIONS` 불변** — facet 은 `FACET_TOOL_*` 별도. 회귀 게이트 필수.
5. **caller 신규 파라미터 default None → byte-identical.**
6. one-path-at-a-time: task 순서대로, 각 task Verification 통과 후 다음.
7. **more structure ≠ monotonically better** — facet 채택은 A/B 결과가 정함. 분석은 실측 후에만(placeholder 금지).

## 2. 컨텍스트 동기

```bash
cd "D:/privateProject/gemento" && git pull --ff-only
git log --oneline -3                      # Exp20/Stage8 반영 확인
ls experiments/tools/context_tools.py experiments/exp15_context_router/native_ollama_caller.py
```

## 3. 읽어야 할 plan 파일

- `docs/plans/exp21-facet-aggregate-tool.md` (parent — 가설/결정/Risk)
- `docs/plans/exp21-facet-aggregate-tool-task-01.md` (facet + caller)
- `docs/plans/exp21-facet-aggregate-tool-task-02.md` (테스트/회귀)
- `docs/plans/exp21-facet-aggregate-tool-task-03.md` (A/B 드라이버)
- `docs/plans/exp21-facet-aggregate-tool-task-04.md` (분석/verdict)
- 배경: 메모리 `exp20-finalization-diagnosis`, `docs/reference/handoff-to-next-agent.md` §4

## 4. 사용자 결정 표 (parent mirror)

| # | 항목 | 확정값 |
|---|------|--------|
| 1 | facet 도구 | 단일 `aggregate_context(handle, pattern, group_by=None, top_n=10)` |
| 2 | opt-in | `FACET_TOOL_*` 분리 + caller `extra_tool_schemas`/`extra_tool_fns`(default None) |
| 3 | A/B | n=5, max_cycles=8, retry K=2(mandatory), num_ctx 32768, boxie gemma4:e4b, megalog 2-task |
| 4 | 실행 | 에이전트 직접(boxie 원격) |
| 5 | 1차 지표 | non-null ans rate(finalization), score 2차 |
| 6 | 채택 | facet arm 유의 개선 시에만 H21 채택 |

## 5. 진행 순서 (의존성)

```
task-01 (A) ──▶ task-02 (B, 테스트)
            └─▶ task-03 (B, 드라이버) ──▶ task-04 (C, 분석/verdict)
```
task-02 와 task-03 은 task-01 후 병렬 가능. task-04 는 task-03 **실행 결과** 후.

## 6. 각 task 진행 패턴

read task md → Step 순차 구현 → Verification bash 그대로 실행 → 통과 시 commit(`feat(stage-9-exp21-task-0N): ...`) → 사용자 confirm → 다음 task.

## 7. 사용자 호출 분기

- Verification 실패 후 self-fix 1회 실패 시.
- Scope boundary 위반 직전(예: orchestrator.py 수정이 필요해 보임 → 설계 재검토 필요).
- **Risk 1 (양 arm non-null rate 0v0)** 발견 시 — A/B 무정보 → harness 수렴 사안 회부 결정.
- **facet_calls==0** (도구 제공≠사용) 발견 시.
- README/conceptFramework 갱신이 필요해 보일 때(본 plan 범위 밖).

## 8. 실행(task-03) 특이사항

- boxie 원격 → Sonnet/에이전트 직접 실행 가능(로컬 LLM 로딩 아님).
- 선행: megalog 재pull(`ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw`) + 터널 11435 healthcheck + Redis 적재.
- **stdout block-buffer 주의**: `python -u` 로 실행하거나 결과 JSON(`results/exp21_facet_ab_gemma4_e4b.json`, trial 마다 flush) polling.

## 9. 분석 task(04) 특이사항

- **결과 JSON 존재 후에만** 분석 작성. placeholder 0 의무(실측치).
- 영문 `researchNotebook.en.md` = **Closed-append-only**(기존 무수정). `gemento-verdict-record` 스킬 사용.
- 갱신 문서: 분석 신규 + researchNotebook.md/.en.md + index.md(Active→Recently Done).
- `test_static` 인벤토리 카운트가 신규 `exp21_*.json` 으로 흔들리면 갱신(Stage 7/8 선례).

## 10. 본 plan 마감 신호

```bash
cd experiments && python -m pytest tests/ -q                       # 전체 green(+facet 테스트)
python -c "import json; d=json.load(open('exp15_context_router/results/exp21_facet_ab_gemma4_e4b.json',encoding='utf-8')); print(d['arms'].keys())"
cd "D:/privateProject/gemento" && grep -q "H21" docs/reference/researchNotebook.md && echo "verdict recorded"
```

## 11. 부수 사항

- 영문 노트북 Closed-append-only 엄수.
- README 한·영 갱신은 **사용자 결정** 후에만(본 plan 범위 밖).
- 변경 금지: `orchestrator.py`, 글로벌 `CONTEXT_TOOL_*`, `conceptFramework.md`.

## 12. 다음 단계 (Architect, 본 plan 마감 후)

- H21 채택 시: facet 도구 다종화(`list_failed_units`/`error_type_histogram`) 후속 plan, paper 갱신(H15~H21).
- H21 기각/0v0 시: orchestrator ABC 수렴(judge finalization) 사안 별도 plan.
- 보류: e2b push-외재화, LLM-as-judge 채점.
