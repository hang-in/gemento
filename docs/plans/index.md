# Plans

Plan document index. Register new plans here.

## Active

(없음 — Stage 5 Exp13 Reducer Role 마감, Exp14 후보 결정 대기)

## Recently Done — Stage 5

- [exp13-reducer-role.md](exp13-reducer-role.md) — **Stage 5 (Exp13)**: Reducer Role 마감. 5 subtask 완료. **H12 ⚠ 미결 (실효적 기각)** — Δ=−0.0533 (bug 제외) / −0.0711 (with bug, 음수, Exp12 정반대), Cohen d=−0.323 (Exp12 +0.323 거울상). synthesis 5/5 task 음수. 메커니즘 = **abstraction loss** (다중 출처/다중 추정 → 단일 추정 압축). **위치-효과 비대칭 확정**: pre-stage = 안전, post-stage = 위험. orchestrator bug 1건 fix (`cf057b6`). 2026-05-05.
- [exp12-extractor-role-pre-search.md](exp12-extractor-role-pre-search.md) — **Stage 5 (Exp12)**: Extractor Role 마감. 5 subtask 완료. **H11 ⚠ 조건부 채택 (양수 방향, 검정력 한계)** — Δ=+0.0500, Cohen d=+0.323 small 양수. logic-02 catastrophic 회복 (+0.30) + synthesis-05 (+0.45). Exp11 의 정반대 메커니즘 — Role 분리/추가가 강화보다 안전. 2026-05-04.

## Recently Done — Stage 4

- [exp11-mixed-intelligence-haiku-judge.md](exp11-mixed-intelligence-haiku-judge.md) — **Stage 4 (Exp11)**: Mixed Intelligence (Flash Judge, v2 — Haiku→Flash). 5 subtask 완료 (commit `d5d4cd7`). **H10 ⚠ 미결 (실효적 기각)** — Δ=−0.0811, Cohen d=−0.316 small 음수. Flash Judge 가 약한 모델의 self-discovery chain 을 *방해* 하는 정반대 메커니즘 발견 (logic-02 case study). Search Tool / 다른 미외부화 축 우선 권장. 2026-05-03.

## Recently Done

- [exp06-h4-recheck-expanded-taskset-pre-exp11.md](exp06-h4-recheck-expanded-taskset-pre-exp11.md) — **Stage 2C**: Exp06 H4 재검증. 5 subtask 완료. **H4 verdict ⚠ 미결 → ⚠ 조건부 채택 (synthesis 카테고리 한정)**. Δ(abc−sb)=+0.044, synthesis +0.140 (회복 핵심), 통계 비유의, Cohen d=0.449. 분석: `docs/reference/h4-recheck-analysis-2026-05-02.md`. 2026-05-02.
- [scorer-failure-label-reference.md](scorer-failure-label-reference.md) — Stage 2B: scorer/failure label reference. 4 subtask 완료 (commit `e84d943`). FailureLabel enum + scoringHistory.md + failureLabels.md + Stage 2C alias 통합. 2026-04-30.
- [stabilization-healthcheck-abort-meta-pre-exp11.md](stabilization-healthcheck-abort-meta-pre-exp11.md) — Stage 2A: 작은 안정화. 5 subtask 완료, dry-run 통과, plan status: done. 2026-04-30.
- [phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md](phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md) — Phase 1 후속 정리 (Taskset 3 FAIL fix + Exp09 5-trial drop 분석 + Exp10 v3 재산정 + 문서 갱신). 4 subtask 완료 (Mac 01/02 + Windows 03/04). 2026-04-30.

## Abandoned (2026-04-25 일괄 정리)

- [readme-memento-acknowledgement.md](readme-memento-acknowledgement.md) — 오픈소스 좌표 선점: README 한·영 + 연구노트 분할·종결 파트 영문화 + Memento Acknowledgement
- [role-adapter-phase-1-rev-1-post-parse-check.md](role-adapter-phase-1-rev-1-post-parse-check.md) — Role Adapter 리팩토링 (Phase 1) rev.1 — 회귀 게이트 + `_post_parse_check` 동작 동치 복원
- [role-adapter-phase-1-a-b-c.md](role-adapter-phase-1-a-b-c.md) — Role Adapter 리팩토링 (Phase 1) — A/B/C 어댑터 분리 + 회귀 게이트 (rev.0)
- [exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag.md](exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag.md) — 실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG)
- [exp08b-tool-use-refinement-prompt.md](exp08b-tool-use-refinement-prompt.md) — 실험 8b: Tool Use Refinement Prompt
- [exp08-math-tool-use-calculator-linalg-lp-exp07.md](exp08-math-tool-use-calculator-linalg-lp-exp07.md) — 실험 8: Math Tool Use (calculator/linalg/LP)
- [exp07-loop-saturation.md](exp07-loop-saturation.md) — 실험 7: Loop Saturation + Loop-Phase 프롬프트 (2×4 요인 설계)
- [exp045-v2.md](exp045-v2.md) — exp045 v2 재채점 지원 추가
- [scoring-v2.md](scoring-v2.md) — 채점 시스템 통일 (Scoring V2)
- [7-loop-saturation-loop-phase.md](7-loop-saturation-loop-phase.md) — 실험 7 — Loop Saturation + Loop-Phase 프롬프트 (구식 형식)
- [plan-7.md](plan-7.md) — 제멘토 개념 프레임 정립 + 가설 재부호화 (구식 형식)
