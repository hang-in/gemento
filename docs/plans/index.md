# Plans

Plan document index. Register new plans here.

## Active

- (보류) e2b 전용 push-기반 외재화 + paper-review P1-3 LLM-as-judge.

## Recently Done — Stage 8 (2026-06-30)

- [mandatory-tool-opt-in.md](mandatory-tool-opt-in.md) — **Stage 8**: mandatory-tool 프롬프트를 `run_abc_chain(mandatory_tool_prompt=False)` opt-in 으로 정식 편입 (안 A — caller-decides, 자동 게이트 아님). `system_prompt.MANDATORY_TOOL_RULES` source-of-truth + 검증된 4규칙. **기본 False → 거동 byte-identical** (회귀 게이트 `tests/test_mandatory_optin.py` 5/5, param 경로 cloud 2/3). failure-mode-specific (큰 로그 1-needle ON / 추론 중심 OFF). 3 subtask 완료. 커밋 `1066b82`(코드)/`fb56a7e`(테스트). 2026-06-30.

## Recently Done — Stage 7 (소급 등록, 2026-06-28~29)

> ⚠ Stage 7 은 plan/verdict skill 워크플로를 우회해 수행됨 — plan 문서 없음. 아래는 소급 기록.

- **Stage 7 Exp19: 실데이터 검증 (n100 journald → boxie e4b)** — 소형 e4b(@boxie GPU)가 n100 실 저널(7d, 34.5K줄/~1.15M tok)을 router+mandatory+retry 로 진단. **실 장애 5/5 정확**(certbot.service 반복 실패, ans5 root cause까지). mean 0.7(keyword artifact — "failing to renew"≠"failed to start", 실정확도 5/5). **mock caddy(`is_fallback`) 정직한 대체.** 인프라: 5060Ti gemma4:e4b gen~95/prefill~1620 tok/s → router 가 prefill 비용을 로그 크기서 분리(stuffing ~12분 vs router ~3초). 분석 §17. 2026-06-30.
- **Stage 7 Exp18: repo-규모 추론 상한 (H18 ✅ size invariance)** — multihop3/multineedle × {50K,100K,200K tok} × n=8, router+retry, mandatory off. **size↑ 저하 전무**: multihop3 75→92→100%, multineedle 100% 전부. **~245K tok(컨텍스트 7.5배)에서도 92~100%**. 메커니즘 = router 가 인지 부하를 로그 크기와 분리(O(1), 모델은 grep 결과만 봄). 소형(~4B)+router 로 repo-규모 디버깅 입증. 터널 불안정으로 3회 분할 resume. 분석 §16. 2026-06-30.
- **Stage 7 Exp17: 복잡도 상한 (H17 부분)** — 4 hard task(multihop2/3, multineedle, distractor) × {baseline, stack} × n=8. **전반 ✅**: e4b+router baseline 92%(multihop2 75/multihop3 92/집계 100/판별 100) — 진짜 복잡 디버깅 스케일. **후반 ❌**: mandatory+retry 스택 89%(−3pp) — Exp16b 의 +57pp 는 큰-로그 전사누락 전용이라 hard task 엔 무효. mandatory = failure-mode-specific. 분석 §14. 2026-06-30.
- **Stage 7 Exp16c: mandatory + retry 결합 (H16c ✅ 채택)** — mandatory(per-attempt↑) + retry-on-None(K=2). e4b router 전 size **100% (30/30)**, 평균 시도 1.0~1.7. progression: retry-only ~60% → mandatory 83% → 결합 100%. **H15 Context Router = e4b 실용 완성** (Stage 7 arc 종결). caveat: n=10 합성, 참값 ~95~100%. 분석 §12. 2026-06-30.
- **Stage 7 Exp16b: mandatory-tool 프롬프트 (H16b ✅ 채택)** — 라우터 prompt 에 mandatory-tool 지시(특히 "매치 라인 그대로 전사"). e4b router per-attempt **27%→83% (+57pp)**, 전 size +50~70pp. **핵심: tool_rounds 오히려↓** → baseline 실패는 tool-neglect 아닌 전사 누락. retry(증상)가 아닌 per-attempt(원인)가 레버. mandatory+retry ≈ 99% 경로. 분석 §10. 2026-06-30.
- **Stage 7 Exp16: Orchestrator 출력 안정화 (H16 ⚠ 부분 채택)** — `final_answer=None` retry-on-None (e4b router, size{12K,25K,50K} × baseline vs stabilized≤3시도 × n=10). retry +30~60pp lift(12k 30→60, 25k 20→50, 50k 10→70) 하나 **~90% 미달, 50~70% 정체** (평균 2.3~2.7 시도, ~2.5× 비용). 근본 = 큰 로그 per-attempt 성공률 ~10~30%. 진짜 레버 = per-attempt 신뢰도(→Exp16b). 분석: `exp15-v2-context-router-analysis-2026-06-29.md` §8. 2026-06-29.

- **Stage 7 v3: gemma4 size sweep (e2b vs e4b) + push/pull 메커니즘** — Exp15 v3: 1-needle × 5 size × {stuffing,router} × num_ctx 32768 × n=5 + v2 매트릭스 e2b. **S_e4b ≈ 8~19K tok**(stuffing 19K부터 0%, 그 너머 router만 생존 60%). **e2b 는 agent tool-use 미달**(router 0.097, tool_rounds~0.6) — arm 순위 e4b 와 정반대(e2b 최선=ErrorBlocks push). **메커니즘 push(e2b, 오케스트레이터 추출) vs pull(e4b, agent 도구호출), capacity-gated** — H13 의 "agent-retrieval 최소 ~4B"를 gemma4 패밀리 내부 재현. e2b archived, 주력=e4b. 2026-06-29.
- **Stage 7 v2: Context Router Stress Test (H15 정식 판정)** — Exp15 v2: canonical gemma4:e4b(Q4_K_M, 지인 서버 RTX 5060 Ti, SSH 터널), 5 task × 4 arm × num_ctx{4096,32768} × n=5 = 200 chains. **H15 (Context 외부화) ⚠ 조건부 채택 (입력 크기 의존)** — router 전체 mean 0.857 vs stuffing 0.300; **큰 로그(≥~10K) router 0.908 vs stuffing 0.125 (Δ+0.78)**; **overflow(컨텍스트 초과) router 1.00 vs stuffing 0.00 (유일 생존)**; 작은 로그(pytrace)는 stuffing 1.00 > router 0.65(overhead); num_ctx artifact 부분적(multihop만 32K 회복); ErrorBlocks brittle. 원본 "latency 35%" 철회. router 60% = None-fragility(틀린 답 0, 침묵만 — Exp16 으로 보완 예정). 분석: `docs/reference/exp15-v2-context-router-analysis-2026-06-29.md`. 결과: `experiments/exp15_context_router/results/exp15_v2_stress_gemma4_e4b.json`. 2026-06-29.
- **Stage 7 v1: Ephemeral Context Router (SQLite+Redis + ErrorBlocks + Fast-Forward)** — `orchestrator.py:967` C(Judge) CONVERGED 조기 월반(Fast-Forward) 전이 추가(실재, tunaCtx 3 cycle 수렴 131s). Exp15 A/B/C/D 대조 + tunaCtx/n100 실증. v1 은 arm당 n=1 예비 → v2 가 해소. ※ H14 충돌로 Context 가설 H15 재부호화. 보고서: `docs/reference/stage7-context-router-analysis-2026-06-28.md`(검증범위 보정본). 2026-06-28.

## Recently Done — Stage 6

- [stage-6-cross-model-llm-as-judge.md](stage-6-cross-model-llm-as-judge.md) — **Stage 6 v3**: Cross-model replication 마감 + Ministral 3 추가 + capability floor + gemma4:31b H13 same-family size-up control 추가. **H14 ⚠ 조건부 채택 (direction match 강함, family-systematic pattern, mechanism 5-mode 분화, 단일 SIG, *measurement-tool fit caveat*)** — **H11 6/7 양수, 1 outlier** (ministral-3:8b −0.043). **H12 family-systematic**: Gemma 3 family **2/2 양수**, non-Gemma family **4/4 음수** (rnj-1:8b **SIG p=0.036 \|d\|=0.617**) → §4.6.2 *style mismatch (b) 직접 evidence*. **H13 5 small-and-mid dense 모두 fail**: gemma3:4b (M2-a), gemma3:12b (M2-b), ministral-3:3b/8b (M2-c), **gemma4:31b (M2-d A-agent JSON schema mismatch, 90% fail)** ⚠ NEW. **(M1) measurable = Gemma 4 E4B 한정** — *size threshold 아닌 specific-model identification*. **gemma4:31b baseline_chunked 95% 정상** = capability 정상, A-agent contract fit 만 실패 = *measurement-tool fit* caveat (paper §1.3 narrowing). **ministral-3:3b 3B = capability floor 미달**. 분석 v3: `docs/reference/stage6-cross-model-analysis-2026-05-08.md`. result v3: `docs/reference/results/exp-stage6-cross-model.md`. LLM-as-judge 보조 평가 (P1-3) 는 future work. 2026-05-09 v3.

## Recently Done — Stage 5

- [exp14-search-tool.md](exp14-search-tool.md) — **Stage 5 (Exp14)**: Search Tool (agent-active BM25 retrieval) 마감. 5 subtask 완료. **H13 ⚠ 미결 (실효적 기각, statistically significant negative)** — Δ=−0.220, Cohen d=−1.000 large effect, **Wilcoxon p=0.031 / paired t p=0.012 (Stage 5 의 첫 통계적 유의 결과)**. mechanism = insufficient retrieval iterations on multi-hop tasks (large-2hop 진단: 1 call → 0% / 2-3 calls → 100%) + sufficient-context baseline saturation. needle 정상, multi-hop 만 catastrophic. Tool 축 sub-distinction 발견 (deterministic computation H7/H8 +18~23pp ≠ agent-iterative retrieval H13 −22pp). 2026-05-05.
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
