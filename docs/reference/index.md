# Reference

Reference document index.

## 종합

- [researchNotebook.md](researchNotebook.md) — **연구 노트** (육하원칙 기반, 증분형 — Exp00~06 + 채점 V2)
- [experimentSummary.md](experimentSummary.md) — 실험 종합 보고서 (04-10 기준, `superseded_by: researchNotebook.md`)

## 설계 / 규약

- [experimentDesign.md](experimentDesign.md) — 제멘토 실험 설계서 (실험 0-4, 브랜치 전략, 인프라 정의)
- [conceptFramework.md](conceptFramework.md) — **canonical 개념 프레임** (4축 외부화, Critic/Orchestrator 이중 구분, 용어집)
- [namingConventions.md](namingConventions.md) — **canonical 표기/용어 규약** (Stage NX, task-NN, 옵션 (a)/(i)/1, 결정 N, condition slug, commit message)
- [resultJsonSchema.md](resultJsonSchema.md) — 결과 JSON top-level schema v1.0 (Stage 2A 도입, `7d4ade9`)
- [h4-metric-definitions.md](h4-metric-definitions.md) — H4 재검증 metric 정의 (Stage 2C 도입, `a6104d1`)
- [scoringHistory.md](scoringHistory.md) — 채점 시스템 변천 (v0/v2/v3 적용 범위) — Stage 2B 도입 (`e84d943`)
- [failureLabels.md](failureLabels.md) — failure label 표준 reference (FailureLabel enum + 기존 매핑) — Stage 2B 도입 (`e84d943`)
- [h4-recheck-analysis-2026-05-02.md](h4-recheck-analysis-2026-05-02.md) — Stage 2C H4 재검증 분석 보고서 (15 task × 3 condition × 5 trial = 225 trial, ablation + 카테고리 + 통계). H4 verdict 미결 → 조건부 채택 (synthesis 한정).
- [exp11-mixed-intelligence-analysis-2026-05-03.md](exp11-mixed-intelligence-analysis-2026-05-03.md) — Stage 4 Exp11 Mixed Intelligence 분석 보고서 (15 task × 2 condition × 5 trial = 150 trial). H10 verdict ⚠ 미결 (실효적 기각). Flash Judge 가 약한 모델의 self-discovery chain 을 방해하는 정반대 메커니즘 발견.
- [exp12-extractor-role-analysis-2026-05-04.md](exp12-extractor-role-analysis-2026-05-04.md) — Stage 5 Exp12 Extractor Role 분석 보고서 (15 task × 2 condition × 5 trial = 150 trial). H11 verdict ⚠ 조건부 채택, 검정력 한계 (Δ=+0.05, Cohen d=+0.323, p=0.198 NS). 양수 방향 관찰.
- [exp13-reducer-role-analysis-2026-05-05.md](exp13-reducer-role-analysis-2026-05-05.md) — Stage 5 Exp13 Reducer Role 분석 보고서 (15 task × 2 condition × 5 trial = 150 trial). H12 verdict ⚠ 미결, 실효적 기각 (Δ=−0.053, Cohen d=−0.323 — Exp12 거울상, p=0.180 NS). 제안 메커니즘 = abstraction loss; keyword scorer artifact 가능성 분리 불가.
- [readme-paper-strategy-2026-05-05.md](readme-paper-strategy-2026-05-05.md) — README + paper 작성 전략 (CTX 비교, arXiv preprint single target).
- [paper-review-action-items-2026-05-05.md](paper-review-action-items-2026-05-05.md) — GPT 피드백 + Architect 평가 → P0/P1/P2 분류된 action items (영구 reference).

## 핸드오프

- [handoff-to-gemini-exp5b.md](handoff-to-gemini-exp5b.md) — Gemini 인계: 실험 5b 태스크 스케일업 지시서
- [handoff-to-gemini-exp6.md](handoff-to-gemini-exp6.md) — Gemini 인계: 실험 6 Solo vs ABC 시너지 측정
- [handoff-to-gemini-exp7.md](handoff-to-gemini-exp7.md) — Gemini 인계: 실험 7 Loop Saturation + Loop-Phase
- [handoff-to-gemini-exp8.md](handoff-to-gemini-exp8.md) — 실험 8 Gemini 핸드오프 (Math Tool-Use)
- [handoff-to-gemini-exp8b.md](handoff-to-gemini-exp8b.md) — 실험 8b Gemini 핸드오프 (Tool-Use Refinement)
- [handoff-to-gemini-exp9.md](handoff-to-gemini-exp9.md) — 실험 9 Gemini 핸드오프 (Long-Context Stress Test)

## 실험 결과

- [results/exp-00-baseline.md](results/exp-00-baseline.md) — 실험 0: Baseline (단일 추론) `done`
- [results/exp-01-assertion-cap.md](results/exp-01-assertion-cap.md) — 실험 1: Assertion 상한 `done`
- [results/exp-02-multiloop-quality.md](results/exp-02-multiloop-quality.md) — 실험 2: 다단계 루프 품질 `done`
- [results/exp-03-error-propagation.md](results/exp-03-error-propagation.md) — 실험 3: 오류 전파 `done`
- [results/exp-035-cross-validation.md](results/exp-035-cross-validation.md) — 실험 3.5: 교차 검증 게이트 `done`
- [results/exp-04-abc-pipeline.md](results/exp-04-abc-pipeline.md) — 실험 4: A-B-C 직렬 파이프라인 `done`
- [results/exp-045-handoff-protocol.md](results/exp-045-handoff-protocol.md) — 실험 4.5: Handoff Protocol `done`
- [results/exp-04-tool-loop-separation.md](results/exp-04-tool-loop-separation.md) — 구 실험 4: 도구 루프 분리 `deferred`
- [results/exp-06-solo-budget.md](results/exp-06-solo-budget.md) — 실험 6: Solo vs ABC 시너지 (+Stage 2C H4 재검증 §6) `done`
- [results/exp-09-longctx.md](results/exp-09-longctx.md) — 실험 9: Long-Context Stress Test (ABC vs Solo vs RAG) `done`
- [results/exp-10-reproducibility-cost.md](results/exp-10-reproducibility-cost.md) — 실험 10: Reproducibility & Cost Profile `done`
- [results/exp-11-mixed-intelligence.md](results/exp-11-mixed-intelligence.md) — 실험 11: Mixed Intelligence (Flash Judge) — H10 ⚠ 미결 (실효적 기각) `done`
- [results/exp-12-extractor-role.md](results/exp-12-extractor-role.md) — 실험 12: Extractor Role — H11 ⚠ 조건부 채택 (양수 방향, 검정력 한계) `done`
- [results/exp-13-reducer-role.md](results/exp-13-reducer-role.md) — 실험 13: Reducer Role — H12 ⚠ 미결 (실효적 기각, Exp12 거울상 effect size, scorer artifact 가능성) `done`
