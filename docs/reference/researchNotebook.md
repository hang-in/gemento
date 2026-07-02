---
type: reference
status: in_progress
updated_at: 2026-07-03
parts: [closed, active]
note: 2026-07-03 v17 — Exp24 a2a Planner→Executor 분할(§22, Stage 12). H24 ⚠ 미결(실효적 기각): scoped_emit_probe(scoped emit 100% vs broad 49%)가 green-light 했으나 A/B(task A n=15)에서 control finalized 47%/correct 47%(asrt {0:9,2:6}) vs a2a 27%/13%(asrt {1:5,2:4,...}, empty-tattoo 0건). Δcorrect −33pp. a2a 가 emit 은 해결(Executor 안정 emit, empty-tattoo 9→0)하나 실패를 Planner 로 이동 — Planner 가 틀린 finding 뽑고 Executor 가 confidently-wrong 으로 충실히 기록. 안전한 None(53%)을 finalized-but-wrong 으로 전환 = 무진단보다 해로움. per-attempt 트랙 3중 음성(H22 프롬프트/H23 도구/H24 구조분할)→retry(§20 K=5→95%) 수용. a2a_proposer opt-in 유지·켜기 비추천. 2026-07-02 v16 — Exp23 list_failed_units facet 레버(§21, Stage 11). H23 ⚠ 미결(실효적 기각): per-attempt retrieval_gap(진단 per_attempt_diag) 을 인자없는 preset 도구로 우회 시도. 도구는 실제 저널서 gohttpserver.service 505,848 신호 #1 반환 확인. 3-arm A/B(task A, pooled): control finalized 47%(n=30)/used_fu 0%, fu_offered 46%(n=26)/used_fu 85%, fu_mandatory 53%(n=17)/used_fu 94% — 세 arm 구별불가(§20 분산대 안). 도구 85-94% 쓰는데도 무개선 → binding constraint = retrieval 아닌 다운스트림 stochastic ceiling(emit/converge). fu_mandatory 샘플 used_fu=True asrt=0 cyc=8 = 답 받고도 emit 실패. per_attempt_diag emission_gap 0 은 소표본 착시. per-attempt 트랙 닫힘: 프롬프트(H22)·retrieval 도구(H23) 둘 다 무개선, 남은 답=retry(§20)/a2a. 도구 opt-in 유지(글로벌 불변, 게이트 66 OK), 켜기 비추천. 2026-07-02 v15 — 오케스트레이터 신뢰성 트랙 종결(§20, 신규 가설 아님). Exp22 가 남긴 "control finalized 17%↔70% 요동" 을 두 진단으로 닫음. 분산 진단(control task A n=30): pooled finalized 57%(Wilson [39,73]), dispersion 0.63<1 = 체계적 batch/시간효과 없음 = 순수 per-chain 노이즈. retry K-sweep(n=20): K=3 70%/K=5 95%, pooled per-attempt 49% → 예측 K=5 96%≈실측 95% = retry-on-None(H16) binomial 산식대로 스케일 실증. 결론: 신뢰성 문제=per-attempt ≈49% 고분산(35~57%), 체계적 결함/nudge부재 아님. 레버=retry K↑(즉효)+per-attempt(Exp16b류, a2a). 레버 유령+50pp·Exp22 실패는 소표본 진폭 착시. 2026-07-01 v14 — Exp22 retrieval-discipline opt-in 재검증 (Stage 10, 오케스트레이터 신뢰성). H22 ⚠ 미결 (실효적 기각): anti-give-up/narrow-query nudge 를 run_abc_chain(retrieval_discipline_prompt) opt-in 편입. 레버 A/B(n=6, task A, 수동 constraint)는 finalized 17%→67%(+50pp) 유망했으나 정식 플래그 경로 재검증(n=10, task A+B)에서 미재현 — task A control finalized 70%/correct 60% vs discipline 40%/40%(Δ−30/−20pp), task B correct 양 arm 0%. 레버 +50pp = control baseline 17%→70% run-to-run 변동 소표본 착시. discipline = neutral~harmful(cycle 종료 전 assertion 강제 → 조기 오답 커밋). 진짜 문제는 nudge 부재 아닌 finalization 자체 분산. opt-in 플래그 유지(기본 False byte-identical, 회귀게이트 62 OK) — 롤백 X, 켜기 비추천. 2026-06-30 v13 — Exp21 facet 도구 A/B (Stage 9). H21 ⚠ 조건부 채택 (aggregation-specific): aggregate_context(untruncated 전수 집계)가 집계 task 에서 결정적 (score 0.0→0.8 — grep_only 는 16KB 캡으로 confidently-wrong 174.138.8.10 5/5, grep_facet 정답 45.144.212.75 4/5), 단일-needle 엔 무효 (0.3→0.2, facet 거의 미사용). non-null rate 는 무력(양 arm 1.0) → 진짜 신호 accuracy. more structure ≠ monotonically better (failure-mode-specific). H19/H20 공백 = Exp19(실데이터)/Exp20(megalog finalization 진단)은 검증. v12 — Exp19 실데이터 검증 (n100 journald 1.15M tok → boxie e4b router, certbot 장애 5/5 정확 진단, mock caddy 대체; 5060Ti tps gen~95/prefill~1620). v11 — Exp18 repo-규모 (size invariance). H18 ✅ 채택 (multihop3 75→92→100%, multineedle 100% @ ~245K tok; router 인지 부하 O(1) = 로그 크기 무관). Stage 7 Context Router 라인 완결. v10 — Exp17 hard tasks. H17 부분 (전반 ✅ e4b+router 가 multi-hop/집계/distractor 까지 스케일 baseline 92%; 후반 ❌ mandatory 는 failure-mode-specific 처방, hard task 선 −3pp). v9 — Exp16c mandatory+retry 결합. H16c ✅ 채택 (전 size 100% 30/30; H15 Context Router e4b 실용 완성). v8 — Exp16b mandatory-tool 프롬프트. H16b ✅ 채택 (per-attempt 27→83% +57pp; 실패는 tool-neglect 아닌 전사 누락, tool_rounds 오히려↓). 2026-06-29 v7 — Exp16 출력 안정화 (retry-on-None). H16 ⚠ 부분 채택 (retry +30~60pp 나 ~90% 미달, per-attempt 신뢰도가 병목). v6 — Exp15 v2 Context Router Stress Test (canonical gemma4:e4b, n=5, num_ctx 통제). H15 ⚠ 조건부 채택 (입력 크기 의존; router 큰 로그·overflow 우위, 작은 로그 손해; num_ctx artifact 부분적; ErrorBlocks brittle). Context = 4축 넘는 5번째 축 후보. 2026-05-09 v5 — Stage 6 v3 (gemma4:31b H13 추가). M2 4 sub-variants 분화. H13 measurable = Gemma 4 E4B 한정. A-agent JSON-schema contract = measurement-tool fit caveat. (n100 journald 1.15M tok → boxie e4b router, certbot 장애 5/5 정확 진단, mock caddy 대체; 5060Ti tps gen~95/prefill~1620). v11 — Exp18 repo-규모 (size invariance). H18 ✅ 채택 (multihop3 75→92→100%, multineedle 100% @ ~245K tok; router 인지 부하 O(1) = 로그 크기 무관). Stage 7 Context Router 라인 완결. v10 — Exp17 hard tasks. H17 부분 (전반 ✅ e4b+router 가 multi-hop/집계/distractor 까지 스케일 baseline 92%; 후반 ❌ mandatory 는 failure-mode-specific 처방, hard task 선 −3pp). v9 — Exp16c mandatory+retry 결합. H16c ✅ 채택 (전 size 100% 30/30; H15 Context Router e4b 실용 완성). v8 — Exp16b mandatory-tool 프롬프트. H16b ✅ 채택 (per-attempt 27→83% +57pp; 실패는 tool-neglect 아닌 전사 누락, tool_rounds 오히려↓). 2026-06-29 v7 — Exp16 출력 안정화 (retry-on-None). H16 ⚠ 부분 채택 (retry +30~60pp 나 ~90% 미달, per-attempt 신뢰도가 병목). v6 — Exp15 v2 Context Router Stress Test (canonical gemma4:e4b, n=5, num_ctx 통제). H15 ⚠ 조건부 채택 (입력 크기 의존; router 큰 로그·overflow 우위, 작은 로그 손해; num_ctx artifact 부분적; ErrorBlocks brittle). Context = 4축 넘는 5번째 축 후보. 2026-05-09 v5 — Stage 6 v3 (gemma4:31b H13 추가). M2 4 sub-variants 분화. H13 measurable = Gemma 4 E4B 한정. A-agent JSON-schema contract = measurement-tool fit caveat.
---

> **개념 프레임 canonical 문서**: [conceptFramework.md](./conceptFramework.md) — 4축 외부화 원리, 용어 정의, 축 ↔ 실험 매핑.

# 제멘토 연구 노트 (Research Notebook)

> 이 문서는 제멘토 프로젝트의 모든 실험을 육하원칙(5W1H) 기반으로 기록하는 증분형 연구 노트입니다.
> 새 실험이 완료될 때마다 해당 섹션을 추가합니다.

> **이 노트의 구조 (2026-04-25 분할 적용)**
>
> - **Part 1: Closed Findings** — 종결된 실험 결과(Exp00~09)와 가설 판정(H1~H9c). 추가 실험이 나오면 **항목을 append만 하고 기존 내용은 수정하지 않습니다**. 영문 미러: [`researchNotebook.en.md`](./researchNotebook.en.md).
> - **Part 2: Active Research** — 진행 중 가설, 열린 질문, 다음 실험 후보. 계속 갱신됩니다. 영문 번역 없음(설계상).

---

# Part 1 — Closed Findings

> 이 파트는 종결된 실험 결과와 가설 판정만 포함합니다. 새 실험이 추가될 때 **항목을 append만 하고 기존 내용은 수정하지 않는다**는 원칙을 따릅니다. 영문 미러는 [`researchNotebook.en.md`](./researchNotebook.en.md)입니다.

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | 제멘토 (Gemento) |
| 핵심 질문 | 소형 LLM(4.5B)에 외부 상태(문신) + 반복 추론 구조를 부여하면, 단일 추론 대비 통계적으로 유의미한 품질 향상이 가능한가? |
| 대상 모델 | Gemma 4 E4B (Exp00~06: Q4_K_M / Ollama, Exp07부터: Q8_0 / llama.cpp GPU 서버) |
| 실행 환경 | Windows (Ollama 또는 llama.cpp) — 실험 실행 / macOS — 분석·문서화 |
| 연구 기간 | 2026-04-08 ~ 진행 중 |
| Sampling | `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` unset (`config.py:SAMPLING_PARAMS` 단일 source — 2026-04-26 도입, sampling-params-config-exp10 plan 결과) |

> *H1–H9는 외부화 축에 대해 순차 번호를 매긴 가설들입니다 — 통계학의 H₀(영가설) / H₁(대립가설)과는 다른 의미입니다.*

### 핵심 가설

| ID | 가설 (외부화 축) | 최종 판정 | 판정 실험 |
|----|------------------|----------|----------|
| H1 | **[Orchestrator 외부화]** 다단계 루프가 단일 추론보다 품질이 높다 | **채택** | Exp02 |
| H2 | **[Role 외부화 필요성 반증]** 오류가 루프를 거치며 증폭된다 | **기각** (오류 무감지) | Exp03 |
| H3 | **[Role 외부화]** 교차 검증(역할 분리)이 오류를 감지할 수 있다 | **채택** (80%) | Exp035 |
| H4 | **[Role 외부화 시너지]** A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ⚠ **조건부 채택 (synthesis 카테고리 한정)** — 2026-05-02 Stage 2C 재검증 결과: 15 task 확대 시 ABC +0.044 우위 (Exp06 9 task subset 의 Solo +0.067 우위와 방향 반전). synthesis 카테고리 +0.140 (명료), 통계 비유의 (n=15 검정력), Cohen d=0.449 medium | Exp06 + Stage 2C |
| H5 | **[Orchestrator 외부화 상한]** MAX_CYCLES 상향이 정답률 향상에 기여한다 (루프 포화점 존재) | **부분 기각** (상한 확장 무효, actual_cycles≈7에서 포화) | Exp07 |
| H6 | **[Role 외부화 정교화]** Phase별 특화 프롬프트가 baseline 대비 우수하다 | **조건부 채택** (장기 루프 15~20에서 +5~6%p) | Exp07 |
| H7 | **[Tool 외부화]** 외부 수학 도구(calculator/linalg/linprog)가 E4B의 계산 한계를 보완한다 | **채택** (+18.3%p, math-04 0→80%) | Exp08 |
| H8 | **[Tool 외부화 안정성]** 에러 힌트 + Mandatory tool rules로 tool_neglect와 operator 혼동을 완화한다 | **채택** (neglect 0%, calculator 100%, math-04 0→100%, 총 +23.3%p) | Exp08b |
| H9a | **[Tattoo 외부화 — 물리 한계 돌파]** ABC+Tattoo(chunked)가 Solo-dump보다 long-context에서 우수하다 | **채택** (+68.3%p, Large 20K에서 Solo 0% → ABC 100%) | Exp09 |
| H9b | **[차별성]** ABC+Tattoo가 RAG baseline 대비 고유 기여를 가진다 | **⚠️ 미결** (5-trial 통계 검정 비유의 p=0.798; overall Δ=+2.0%p; 3-hop에서만 +20.0%p 차별성; Small Paradox 확인) | Exp09 |
| H9c | **[에러 모드 차이]** ABC의 실패 패턴이 Solo·RAG와 질적으로 다르다 | **채택** (Solo: format_error 24, RAG: wrong_synthesis 6, ABC: evidence_miss 2 + wrong_synthesis 3) | Exp09 |
| **H10** | **[Role 외부화 강화 — Mixed Intelligence]** 강한 Judge C (Gemini 2.5 Flash) 가 약한 Proposer/Critic (A/B = Gemma 4 E4B) 의 한계를 보완한다 | ⚠ **미결 (실효적 기각)** — 2026-05-03 Exp11: Δ(mixed−base)=−0.0811 (음수), Cohen d=−0.316 small, Wilcoxon p=0.293 비유의. logic 카테고리 catastrophic (−0.275), synthesis 만 양수 (+0.030). Flash Judge 가 약한 모델의 self-discovery chain 을 *방해* 하는 정반대 메커니즘 발견 | Exp11 |
| **H11** | **[Role 외부화 분리/추가 — Extractor Role]** 신규 Role (Extractor, 동일 Gemma 모델) 이 task prompt 의 claims/entities 를 사전 추출하여 A→B→C input 에 prefix 주입하면, A 부담 감소 + 정확도 향상 | ⚠ **조건부 채택 (양수 방향, 검정력 한계)** — 2026-05-04 Exp12: Δ(ext−base)=+0.0500 (양수, Exp11 정반대), Cohen d=+0.323 small 양수, Wilcoxon p=0.198 비유의 (n=15 한계). logic +0.125 / synthesis +0.050. logic-02 catastrophic 회복 (+0.30) + synthesis-05 (+0.45). Role 축 *분리/추가* 가 *강화* 보다 안전한 진화 방향 입증 | Exp12 |
| **H12** | **[Role 외부화 분리/추가 — Reducer Role]** 신규 Role (Reducer, 동일 Gemma 모델) 이 ABC chain 의 final tattoo + final_answer 를 받아 *post-stage* 에서 정리/통합하면, keyword 매칭 정확도 + final answer 명료성 향상 | ⚠ **미결 (실효적 기각)** — 2026-05-05 Exp13: Δ(red−base)=−0.0533 (bug 제외) / −0.0711 (with bug, 음수 — Exp12 정반대), Cohen d=−0.323 (Exp12 +0.323 거울상), Wilcoxon p=0.180 비유의. logic −0.100 / math −0.083 / **synthesis −0.107 (5/5 task 음수)** / planning +0.100. 메커니즘 = **abstraction loss** (다중 출처/다중 추정 → 단일 추정 압축). **위치-효과 비대칭 확정**: pre-stage = 안전, post-stage = 위험 | Exp13 |
| **H13** | **[Tool 외부화 — agent-active retrieval]** ABC 에이전트가 cycle 중 능동적으로 `search_chunks(query, top_k)` 호출하여 long-context document 의 관련 chunk retrieve 시, 32K context baseline (full document in prompt) 대비 정확도 + 효율 향상 | ⚠ **미결 (실효적 기각, SIG)** — 2026-05-05 Exp14: Δ(search−base)=−0.2200 (음수, Stage 5 의 가장 큰 음수). **Cohen d=−1.000 large effect**, **Wilcoxon p=0.0312 / paired t p=0.0115 — Stage 5 첫 통계적 유의 결과**. Bootstrap 95% CI [−0.36, −0.10] (0 미포함). 메커니즘 = **insufficient retrieval iterations on multi-hop tasks** (large-2hop 진단: 1 call → 0% / 2-3 calls → 100%) + premature termination ("document does not contain" 단정) + sufficient-context baseline saturation. needle (1-hop) 은 정상, multi-hop 만 fail. Tool 축 sub-distinction 발견: deterministic computation (H7/H8 +18~23pp) ≠ agent-iterative retrieval (H13 −22pp) | Exp14 |
| **H14** | **[Cross-model generalization]** Stage 5 의 H11 (Extractor pre-stage 양수) / H12 (Reducer post-stage 음수) / H13 (Search Tool 음수) 의 *direction / mechanism* 이 cross-family / cross-size 모델에서 generalize | ⚠ **조건부 채택 (direction match 강함, family-systematic pattern, mechanism 5-mode 분화, 단일 SIG, *measurement-tool fit caveat*)** — 2026-05-09 Stage 6 v3 (6 model H11/H12 + 5 model H13). **H11 6/7 양수, 1 outlier** (ministral-3:8b −0.043). **H12 family-systematic**: Gemma 3 **2/2 양수**, non-Gemma **4/4 음수** (rnj-1:8b **SIG p=0.036 \|d\|=0.617**) → §4.6.2 *style mismatch (b) family-level 직접 evidence*. **H13 5 small-and-mid dense 모두 fail**: gemma3:4b (M2-a 0/50 calls), gemma3:12b (M2-b "Unknown"), ministral-3:3b/8b (M2-c 100% no-converge), **gemma4:31b (M2-d A-agent JSON schema mismatch, 90% fail)** ⚠ NEW. **(M1) under-iteration measurable = Gemma 4 E4B 한정** — *size threshold 아닌 specific-model identification* (gemma4:31b 도 fail). **gemma4:31b baseline_chunked 95% 정상** = 모델 capability 정상, A-agent contract fit 만 실패. **A-agent JSON-schema contract = measurement-tool fit** (paper §1.3 narrowing + §4.7.4 / §6 limitations). **ministral-3:3b 3B = capability floor 미달** (H11 31.3% reject, H13 100% reject). 상세: `docs/reference/stage6-cross-model-analysis-2026-05-08.md` (v3 2026-05-09) | Stage 6 v3 |
| **H15** | **[Context 외부화]** Redis 핸들 + grep/read 도구로 대용량 로그를 컨텍스트 라우팅하면, log-stuffing 대비 소형 LLM 의 정확도/안정성이 향상된다 | ⚠ **조건부 채택 (입력 크기 의존, n=5 canonical 재검증)** — 2026-06-29 Exp15 v2 (gemma4:e4b, 5 task × 4 arm × num_ctx{4096,32768} × n=5). router 전체 mean 0.857 vs stuffing 0.300; **큰 로그(≥~10K tok) router 0.908 vs stuffing 0.125 (Δ+0.78)**; **overflow(93K, 컨텍스트 초과) router 1.00 vs stuffing 0.00 — 유일 생존 arm**. 단 **작은 로그(pytrace 0.1K)는 stuffing 1.00 > router 0.65 (overhead)**. num_ctx artifact는 부분적 (multihop만 32K서 stuffing 0→100%, rust/caddy/overflow는 32K서도 stuffing 0% = 진짜 lost-in-the-middle). ErrorBlocks-Only brittle (키워드 의존, mean 0.28). 원본 Stage7 "latency 35% 단축"은 n=1+ctx artifact로 **철회**. cross-model ministral-3:8b(35KB)는 라우터 무이득 → **router 효용 = f(모델 용량, 로그 크기)**. ※ H14 와 충돌하던 Context 가설을 H15 로 재부호화. 상세: `docs/reference/exp15-v2-context-router-analysis-2026-06-29.md` | Exp15 v2 |
| **H16** | **[Orchestrator 외부화 — 출력 안정화]** `final_answer=None` 시 체인을 재실행(retry-on-None)하는 결정론적 안정화 층이 e4b router 의 큰 로그 실효 정답률을 ~90%+ 로 끌어올린다 | ⚠ **부분 채택** — 2026-06-29 Exp16 (e4b router, size{12K,25K,50K} × baseline vs stabilized≤3시도 × n=10). retry 가 +30~60pp lift (12k 30→60, 25k 20→50, 50k 10→70) 하나 **~90% 미달, 50~70% 정체** (평균 2.3~2.7 시도, cap 도달 잦음). 원인 = 큰 로그에서 **per-attempt 성공률 자체가 낮음(~10~30%)** → 재시도만으로 부족. 비용 ~2.5× call. 진짜 레버 = per-attempt 신뢰도(Exp16b). run-to-run 변동 큼(baseline soft). 상세: `docs/reference/exp15-v2-context-router-analysis-2026-06-29.md` §8 | Exp16 |
| **H16b** | **[Orchestrator 외부화 — mandatory-tool 프롬프트]** 라우터 task prompt 에 mandatory-tool 지시(반드시 grep 먼저 / 조기 단정 금지 / 매치 라인 3요소 그대로 전사)를 주면 e4b router 의 per-attempt 성공률이 오른다 | **✅ 채택** — 2026-06-30 Exp16b (e4b router, size{12K,25K,50K} × baseline vs mandatory × n=10, 1시도). per-attempt **27%→83% (+57pp)**, 전 size +50~70pp 일관. **핵심: mandatory 에서 tool_rounds 가 오히려 감소**(5.9→3.3 등) → baseline 실패는 tool-neglect 아닌 **전사/결론 누락**(grep 반복하며 final_answer 미전사). 규칙4("그대로 전사")가 레버. per-attempt 83% + Exp16 retry(K=2) 결합 시 기대 ~99%. (n=10 서술적, 대효과 일관.) 상세: `docs/reference/exp15-v2-context-router-analysis-2026-06-29.md` §10 | Exp16b |
| **H16c** | **[Orchestrator 외부화 — mandatory + retry 결합]** mandatory 프롬프트(per-attempt↑) + retry-on-None(K=2) 결합이 e4b router 의 큰 로그 실효 정답률을 ~99%+ 로 만든다 | **✅ 채택** — 2026-06-30 Exp16c (e4b router, size{12K,25K,50K} × mandatory+retry × n=10). **전 size 100% (30/30)**, 평균 시도 1.0~1.7. progression: retry-only ~60%(Exp16) → mandatory-only 83%(Exp16b) → **결합 100%**. (n=10 합성·단일 needle, 참값 ~95~100% 로 읽는 게 안전; 50k 의 1.0시도/100% 는 표본 쏠림 있음.) **H15 Context Router = e4b 에서 실용 완성** (큰 로그·컨텍스트 초과 디버깅 ~안정). 상세: §12 | Exp16c |
| **H17** | **[복잡도 상한 + mandatory 일반성]** e4b + router 가 trivial 1-needle 을 넘어 multi-hop/집계/distractor 까지 스케일하고, mandatory+retry 스택이 거기서도 일반적으로 이득을 준다 | **부분 — 전반 ✅ / 후반 ❌** — 2026-06-30 Exp17 (e4b router, 4 hard task × {baseline, stack} × n=8, ~23K tok). **전반(스케일) ✅**: baseline 만으로 multihop2 75% / multihop3 92% / multineedle 100% / distractor 100% (평균 92%) — 진짜 복잡 디버깅 처리. **후반(mandatory 일반성) ❌**: stack 평균 89% (−3pp, neutral~약간 음수). mandatory 는 **특정 실패 모드(큰 로그 전사 누락, Exp16b) 전용 처방**이지 범용 부스터 아님 — baseline 이 이미 높으면 noise. → "router 기본값 승격" 은 무조건이 아니라 **적응적 적용**. (n=8 합성·부분점수.) 상세: §14 | Exp17 |
| **H18** | **[Context 외부화 — size invariance]** Context Router 는 모델 인지 부하를 로그 크기와 분리(O(1)) — repo-규모(컨텍스트 초과) 로그에서도 multi-hop/집계 추론이 무저하 | **✅ 채택** — 2026-06-30 Exp18 (e4b router+retry, multihop3/multineedle × {50K,100K,200K tok} × n=8). **size↑ 저하 전무**: multihop3 75→92→**100%**, multineedle 100/100/100%. **~245K tok(32K 컨텍스트의 7.5배)에서도 92~100%**. 메커니즘: 모델은 거대 로그가 아닌 grep 결과(작은 매치 라인)만 봄 → 인지 부하 O(1). retry 분화: multihop3 att~3(깊은 추론 None↑ 회복), multineedle att~1.2. 소형(~4B) + router 로 repo-규모 디버깅 입증. (n=8 합성·grep-findable·부분점수.) 상세: §16 | Exp18 |
| **H21** | **[Tool 외부화 — facet 집계]** 결정론적 전수 집계 도구(`aggregate_context`, 16KB 라인덤프 대신 untruncated 그룹별 top-N 카운트)가 소형 모델의 진단 정확도를 끌어올린다 | **⚠ 조건부 채택 (aggregation-specific)** — 2026-06-30 Exp21 (megalog ~29.3M tok, e4b, grep-only vs grep+facet, 2-task × n=5, max_cycles=8). **집계 task 에서 결정적**: task B(최다 brute-force IP) score **0.0→0.8** — grep_only 5/5 confidently-wrong(`174.138.8.10`, 16KB 캡이 시간순 앞부분만 노출 → 일찍 보인 IP 오인) vs grep_facet 4/5 정답(`45.144.212.75`, facet 16 calls untruncated 전수 카운트). **단일-needle task(A gohttpserver)엔 무효** (0.3→0.2, facet 거의 미사용 3 calls, 수렴 확률적). **non-null rate 무력**(양 arm task B 1.0) → 진짜 신호 accuracy. "more structure ≠ monotonically better" — facet 은 failure-mode-specific(Exp17 mandatory 와 동형). H19/H20 공백 = Exp19/Exp20 은 검증. (n=5 소표본·단일 모델·단일 도구.) 상세: §18 | Exp21 |
| **H22** | **[Orchestrator 신뢰성 — retrieval-discipline]** anti-give-up + narrow-query nudge(넓은 grep→노이즈→포기 대신 `Failed with result`/`.service` 로 좁히고 cycle 종료 전 후보 assertion 1개 강제)를 opt-in 편입하면 under-query 조기포기(empty tattoo→`final_answer=None`) finalization 실패가 완화된다 | **⚠ 미결 (실효적 기각)** — 2026-07-01 Exp22 (megalog ~29.3M tok, e4b, control vs discipline, 2-task × n=10, max_cycles=8, 실제 `retrieval_discipline_prompt` 플래그 경로). **레버 A/B(n=6, task A, nudge 를 constraints 에 수동 주입)의 finalized 17%→67%(+50pp)가 재현 안 됨**: task A control finalized **70%**/correct **60%** vs discipline **40%**/**40%** (Δ **−30pp**/−20pp), task B correct 양 arm **0%**(집계 실패=16KB 캡, facet 영역이라 discipline 무효). 레버의 +50pp = control baseline 17%→**70%** run-to-run 변동에 기인한 **소표본 착시**. discipline = **neutral~harmful** (cycle 종료 전 assertion 강제가 조기 오답 커밋 유발 — task A correct 60→40, task B empty 0%나 correct 0% 유지). **진짜 문제 = 특정 nudge 부재가 아니라 finalization 자체의 높은 분산.** opt-in 플래그는 유지(기본 False byte-identical, 회귀게이트 62 OK) — 롤백 X, 켜기 비추천. (n=10 소표본, rate-기반 A/B, 유의성 미검정.) 상세: §19 | Exp22 |
| **H23** | **[Tool 외부화 — failed-unit preset]** 인자없는 preset 도구(`list_failed_units(handle)`, systemd 실패 신호 전수 스캔 → unit 별 top-N)가 per-attempt retrieval_gap(모델이 넓은 grep 후 포기)을 우회해 finalization 을 올린다 | **⚠ 미결 (실효적 기각)** — 2026-07-02 Exp23 (megalog ~29.3M tok, e4b, control/fu_offered/fu_mandatory, task A single-attempt, pooled 2 run). 도구는 실제 저널서 `gohttpserver.service` **505,848 신호 #1** 반환(우회 성공). 그러나 3-arm finalized **구별불가**: control **47%**(n=30, used_fu 0%) / fu_offered **46%**(n=26, **used_fu ~85%**) / fu_mandatory **53%**(n=17, **used_fu ~94%**) — 전부 §20 per-attempt 분산대(35~57%) 안. **도구를 85~94% 쓰는데도 무개선** → binding constraint = retrieval 아니라 **다운스트림 stochastic ceiling**(emit/converge). fu_mandatory 샘플 `used_fu=True asrt=0 cyc=8`(답 받고도 assertion emit 실패)가 직시. per_attempt_diag 의 emission_gap 0 은 소표본(성공 2/2) 착시. **H21 저사용 경고 미재현**(offered 85% 사용). per-attempt 트랙 닫힘: 프롬프트(H22)·retrieval 도구(H23) 둘 다 무개선 → retry(§20)/a2a 만 남음. (pooled n, rate-기반, GPU 간헐 부하로 arm 순차 preempt→mandatory 단독 완주.) 상세: §21 | Exp23 |
| **H24** | **[Orchestrator 외부화 — proposer 분할]** 단일 A(제안자)를 Planner(도구→finding 텍스트)+Executor(finding 을 clean scoped 입력으로 도구 없이 emit) 로 분할하면 per-attempt broad-context overload 를 우회해 finalization/correct 가 오른다 | **⚠ 미결 (실효적 기각)** — 2026-07-03 Exp24 (task A single-attempt, n=15). `scoped_emit_probe`(scoped emit 100% vs broad 49%)가 green-light 했으나 A/B 에서 **악화**: control finalized **47%**/correct **47%**(asrt {0:9, 2:6}) vs a2a **27%**/**13%**(asrt {1:5,2:4,3:2,5:2,8:2}, **empty-tattoo 9→0**). Δfinalized −20pp, **Δcorrect −33pp**. 메커니즘: a2a 가 **emit 은 해결**(Executor 안정 emit, empty-tattoo 소멸 — probe 약속 이행)하나 **실패를 Planner 로 이동** — Planner 가 넓은 검색서 틀린 finding 뽑고 Executor 가 confidently-wrong 으로 충실히 기록·수렴(monolithic A emit 시 47% 정답 vs 분할 Planner 13%). **가장 중요**: control 의 53% 실패는 안전한 None(무해), a2a 는 그 중 ~14%를 **finalized-but-wrong**(confident-wrongness)으로 전환 = 틀린 진단이 무진단보다 해로움(Exp21 confidently-wrong 동형). **per-attempt 트랙 3중 음성**(H22 프롬프트/H23 도구/H24 구조분할) → retry(§20 K=5→95%) 수용이 답. opt-in 유지·켜기 비추천. caveat: MVP a2a(텍스트 planner) 한정, 구조화 planner/verification 미검증. 상세: §22 | Exp24 |

#### 축 ↔ 실험 매트릭스

각 실험이 4개 외부화 축 중 어느 축(들)을 검증했는지의 2D 매트릭스. ✅ = 주 검증, ▶ = 간접 관련, — = 해당 없음.

| 실험 | Tattoo | Tool | Role Agent | Orchestrator |
|------|:------:|:----:|:----------:|:------------:|
| Exp00 (Baseline) | — | — | — | — |
| Exp01 (Assertion Cap) | ✅ | — | — | — |
| Exp02 v2 (Multiloop) | ▶ | — | — | ✅ |
| Exp03 (Error Propagation) | — | — | ✅ (반증) | — |
| Exp035 (Cross Validation) | — | — | ✅ | — |
| Exp04 (A-B-C Pipeline) | ▶ | — | ✅ | ✅ (Judge Role) |
| Exp045 (Handoff Protocol) | ✅ | — | ▶ | — |
| Exp05b (Hard Tasks) | ✅ | — | ✅ | — |
| Exp06 (Solo Budget) | — | — | ✅ | — |
| Exp07 (Loop Saturation) | — | — | ▶ | ✅ |
| Exp08 (Math Tool-Use) | — | ✅ | ▶ | — |
| Exp08b (Tool Refinement) | — | ✅ | — | — |
| Exp11 (Mixed Intelligence) | — | — | ✅ (Role 강화 — H10 미결) | — |
| Exp12 (Extractor Role) | — | — | ✅ (Role 분리/추가 — pre-stage, H11 조건부 채택) | — |
| Exp13 (Reducer Role) | — | — | ✅ (Role 분리/추가 — post-stage, H12 미결/실효적 기각) | — |
| Exp14 (Search Tool) | ▶ | ✅ (agent-active retrieval — H13 미결/SIG 음수) | — | — |
| Exp15 v2 (Context Router) | ✅ (Context 외부화 — H15 조건부 채택) | ▶ (grep/read 도구) | — | ▶ (Fast-Forward 전이) |
| Exp16 (Output Stabilization) | — | — | — | ✅ (출력 안정화 retry — H16 부분 채택) |
| Exp16b (Mandatory-tool Prompt) | — | ▶ (grep/read 도구) | — | ✅ (mandatory 프롬프트 — H16b 채택) |
| Exp16c (Mandatory + Retry) | — | ▶ (grep/read 도구) | — | ✅ (결합 ~100% — H16c 채택) |
| Exp17 (Hard Tasks) | — | ▶ (grep/read 도구) | — | ✅ 스케일 / mandatory 일반성 ❌ (H17 부분) |
| Exp18 (Repo-scale) | ✅ (Context size-invariance — H18 채택) | ▶ (grep/read 도구) | — | ▶ (retry) |
| Exp21 (Facet A/B) | — | ✅ (facet 집계 도구 — H21 조건부, aggregation-specific) | — | ▶ (router+retry) |
| Exp22 (Retrieval-discipline A/B) | — | ▶ (grep/read 도구) | — | ✅ (finalization 신뢰성 nudge — H22 미결/실효적 기각, 레버 미재현) |
| Exp23 (Failed-units facet A/B) | — | ✅ (list_failed_units preset — H23 미결/실효적 기각, retrieval 우회 성공하나 per-attempt 무개선) | — | ▶ (per-attempt ceiling) |
| Exp24 (a2a Planner→Executor A/B) | — | ▶ (planner 도구) | ▶ (Planner/Executor 역할) | ✅ (proposer 분할 — H24 미결/실효적 기각, emit 해결하나 실패 Planner 이동·correct 폭락) |

> 자세한 정의는 [conceptFramework.md § 2](./conceptFramework.md)의 4축 정의 참조. Context 외부화(H15)는 4축을 넘는 5번째 축 후보 — [conceptFramework.md § 8](./conceptFramework.md) 참조.

---

## 실험 기록

---

### Exp00: Baseline (단일 추론)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | Gemma 4 E4B × 1 (단일 모델, 문신 없음) |
| **언제 (When)** | 2026-04-08 |
| **어디서 (Where)** | Windows Ollama 로컬 환경 |
| **무엇을 (What)** | 문신 구조 없이 E4B의 단일 추론 품질 측정 |
| **왜 (Why)** | 이후 모든 실험의 비교 기준(baseline) 확립. 문신 시스템의 효과를 측정하려면 "없을 때"의 성능을 먼저 알아야 함 |
| **어떻게 (How)** | 6개 태스크(math×2, logic×2, synthesis×2) × 3회 반복 = 18 데이터포인트. 질문+필요정보만 제공, 단일 응답 |

**결과:**

| 태스크 | 정답률 | 비고 |
|--------|--------|------|
| math-01 | 3/3 (100%) | 기본 산술 |
| math-02 | 3/3 (100%) | 다변수 연립 |
| logic-01 | 0/3 (0%) | 출력 토큰 한도 초과로 응답 절단 |
| logic-02 | 0/3 (0%) | 포함-배제 원리 실패 |
| synthesis-01 | 3/3 (100%) | 단순 조건 종합 |
| synthesis-02 | 0/3 (0%) | 다단계 경로 계산 실패 |
| **전체** | **9/18 (50%)** | |

**핵심 발견:**
1. 구조화된 수학 → 충분. 복잡한 논리/종합 → 실패 (0%)
2. 자동 채점(substring)이 과대측정 — 수동 검증 필수
3. 채점: v1=0.705, v2=0.722

**결론:** E4B는 단일 추론으로 50% 정확도. 복잡한 문제에서 구조적 지원 필요.

---

### Exp01: Assertion Cap (문신 상한)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 1 |
| **언제** | 2026-04-08 |
| **어디서** | Windows Ollama |
| **무엇을** | Assertion 개수(2~12)에 따른 구조화 출력 안정성 측정 |
| **왜** | RT 토론에서 결정한 soft cap 8 / hard cap 10이 실제로 유효한지 검증. 과도한 assertion이 "중간 망각" 현상을 일으키는지 확인 |
| **어떻게** | Assertion 수 = {2, 4, 6, 8, 10, 12} × 태스크 × 3회. 미리 작성된 정답 assertion을 제공하고 JSON 파싱 성공률 측정 |

**결과:**

| Cap | JSON 성공률 |
|-----|------------|
| 2~12 | 모두 100% |

**핵심 발견:**
1. 12개 assertion까지 안정 — "중간 망각" 효과 없음
2. 응답 시간은 assertion 수에 비례하여 선형 증가
3. RT 권장(soft 8 / hard 10) 유지 타당

**결론:** Assertion 수용 용량은 실험 범위 내에서 병목이 아님.

---

### Exp02: 다단계 루프 품질 누적 (H1 검증)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 1 (반복 호출) |
| **언제** | 2026-04-09 |
| **어디서** | Windows Ollama |
| **무엇을** | 루프 수(1, 2, 4, 8)에 따른 정답률·수렴률 변화 측정 |
| **왜** | **H1 검증** — "같은 소형 LLM을 반복 호출하면 추론 품질이 향상되는가?" |
| **어떻게** | Phase 시퀀스(DECOMPOSE→INVESTIGATE→SYNTHESIZE→VERIFY→CONVERGED)를 오케스트레이터가 관리. v1(모델 자율)→실패→v2(오케스트레이터 강제)로 전환 |

**실행 버전 비교:**

| 버전 | 수렴률 | 핵심 차이 |
|------|--------|----------|
| v1 (모델 자율 phase 전이) | 0/72 (0%) | 모델이 phase 전이/confidence 판단 불가 |
| **v2 (오케스트레이터 강제)** | **17/18 (94.4%)** | 오케스트레이터가 phase 시퀀스 관리 |

**v2 결과:**

| Loops | 정답률 | 수렴률 | Baseline 대비 |
|-------|--------|--------|-------------|
| 1 | 0% | 0% | -50%p (구조적: DECOMPOSE에서 답 불가) |
| 2 | 44.4% | 0% | -5.6%p |
| 4 | 66.7% | 44.4% | +16.7%p |
| **8** | **94.4%** | **94.4%** | **+44.4%p** |

**핵심 발견:**
1. **H1 채택** — Baseline 50% → 8루프 94.4%, 단조 증가
2. **결정적 교훈:** 모델 문제가 아니라 오케스트레이터 설계 문제. v1(0%)→v2(94.4%)
3. 역할 분리 원칙 확립: 오케스트레이터=구조, 모델=실행

**결론:** 다단계 루프는 효과적이나, phase 전이를 모델에 맡기면 실패. 외부 구조 관리 필수.

---

### Exp03: 오류 전파와 자기 교정 (H2 검증)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 1 |
| **언제** | 2026-04-09 |
| **어디서** | Windows Ollama |
| **무엇을** | 문신에 결함(corrupt_content, inflate_confidence, contradiction)을 주입한 후 모델의 자가 감지율 측정 |
| **왜** | **H2 검증** — "결함 있는 assertion이 루프를 거치며 증폭되는가, 자기 교정되는가?" |
| **어떻게** | 루프 2, 4에서 3종 결함 주입. 4개 태스크 × 3~9회 = 15 데이터포인트. Confidence 궤적 추적 |

**결과:**

| 결함 유형 | 시행 | 감지율 | Confidence |
|-----------|------|--------|-----------|
| corrupt_content | 9 | 0% | 1.0 (전부) |
| inflate_confidence | 3 | 0% | 1.0 (전부) |
| contradiction | 3 | 0% | 1.0 (전부) |
| **전체** | **15** | **0%** | **1.0** |

**핵심 발견:**
1. **H2 기각 (예상 밖 방향)** — 오류가 증폭되지도 않지만 감지되지도 않음
2. E4B는 모든 assertion을 무조건 신뢰 — naive executor
3. VERIFY phase가 실질적으로 작동하지 않음
4. Confidence 자가 보고는 신뢰 불가 (항상 1.0)

**결론:** 자가 검증 불가. 오류 감지는 외부(교차 검증)에 위임해야 함.

---

### Exp035: 교차 검증 게이트

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 1 (비판자 전용 프롬프트) |
| **언제** | 2026-04-09 |
| **어디서** | Windows Ollama |
| **무엇을** | 역할 분리된 비판자(B)가 다른 에이전트(A)의 assertion 결함을 감지할 수 있는지 측정 |
| **왜** | A-B-C 파이프라인 구축 전 게이트 판단. 감지율 >50%이면 PASS, <20%이면 A-B-C 포기 |
| **어떻게** | B에게 A의 assertion + 원본 질문 제공. "이 assertion이 유효한가?" 판단 요청. 3종 결함 × 15 시행 |

**결과:**

| 결함 유형 | 감지율 | 자가검증(Exp03) 대비 |
|-----------|--------|-------------------|
| corrupt_content | 9/9 (100%) | 0% → 100% |
| contradiction | 3/3 (100%) | 0% → 100% |
| inflate_confidence | 0/3 (0%) | 0% → 0% (메타데이터는 감지 불가) |
| **전체** | **12/15 (80%)** | **0% → 80%** |

**게이트 판정: PASS** (80% > 50% 임계값)

**핵심 발견:**
1. **같은 E4B라도 역할 분리하면 검증 가능** — 자가검증 0% → 교차검증 80%
2. 내용 기반 결함(산술, 논리 오류)은 정확히 감지 + 근거 제시
3. 메타데이터 결함(confidence 조작)은 감지 불가 → 오케스트레이터 규칙 기반 처리
4. 단순 프롬프트 효과가 아닌 구조적 차이 (0%→80%)

**결론:** 교차 검증 유효. A-B-C 파이프라인 진행 근거 확보.

---

### Exp04: A-B-C 직렬 파이프라인

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 역할 (A=제안자, B=비판자, C=판정자) |
| **언제** | 2026-04-09 |
| **어디서** | Windows Ollama |
| **무엇을** | E4B 3개 역할 분리로 Python 오케스트레이터 없이 전체 추론 파이프라인 운영 가능한지 검증 |
| **왜** | Exp02에서 Python이 phase 전이를 강제했으나, 원래 가설은 "E4B × 3 직렬 구조". C(판정자)가 phase 전이를 자율 결정할 수 있는지 테스트 |
| **어떻게** | A→B→C 직렬 호출. C가 B의 비판 수렴을 판단하여 phase 전이 결정. Python은 안전장치(MAX_CYCLES)만 담당. 4개 태스크 × 3회 = 12 시행 |

**결과:**

| 지표 | Exp04 | Exp02 v2 비교 |
|------|-------|-------------|
| 수렴률 | 12/12 (100%) | 17/18 (94.4%) |
| 정답률 | 10/12 (83.3%) | 17/18 (94.4%) |
| C 자율 phase 전이 | 30/30 (100%) | Python 강제 |
| Python 안전장치 발동 | 0회 | — |

**synthesis-02 실패 (2/3):** `final_answer=None` — C가 아닌 A의 프롬프트 문제. C는 정확히 CONVERGED 판정.

**핵심 발견:**
1. **C가 Python 오케스트레이터를 완전 대체** — 30/30 자율 결정, 0회 안전장치
2. 각 역할의 복잡도가 E4B 능력 범위 내: A(추론), B(비교), C(패턴 매칭)
3. Python은 안전장치로만 존재 — 판단 역할 제거

**결론:** 원래 가설 "E4B × 3 직렬 구조" 성립. 단, A의 출력 구조화가 필요.

---

### Exp05a: 프롬프트 강화

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) |
| **언제** | 2026-04-10 |
| **어디서** | Windows Ollama |
| **무엇을** | Exp04의 synthesis-02 `final_answer=None` 문제를 프롬프트 강화("MUST set final_answer")로 해결 시도 |
| **왜** | synthesis-02에서 A가 최종 답을 생성하지 않는 문제. "더 강하게 지시"하면 해결되는지 테스트 |
| **어떻게** | A의 시스템 프롬프트에 "MUST set final_answer" 강조. 동일 태스크셋으로 재실행 |

**결과:** synthesis-02 여전히 실패. 프롬프트 강화 효과 없음.

**채점:** v1=0.636, v2=0.583

**핵심 발견:**
1. **"더 열심히 해라"는 효과 없음** — 구조적 문제에는 구조적 해결책 필요
2. 이 실패가 Exp045(Handoff Protocol) 설계의 직접적 동기

**결론:** 프롬프트 강화 실패 → 출력 스키마 강제 방향으로 전환.

---

### Exp045: Handoff Protocol (정보 전달 규약)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) + Handoff 스키마 |
| **언제** | 2026-04-13 ~ 2026-04-14 |
| **어디서** | Windows Ollama |
| **무엇을** | 구조화된 Handoff 포맷(HandoffA2B: blueprint, prioritized_focus, constraints)으로 에이전트 간 정보 손실 억제 및 고난도 태스크 처리 |
| **왜** | Exp04의 synthesis-02 실패(구조 문제) 해결 + Exp05b 스케일업 전 정보 전달 안정성 확보 |
| **어떻게** | JSON Mode + Temperature 0.1. 6개 태스크(기존 4 + logic 2개 추가) × 3회 = 18 시행. Handoff Loss Rate·Backprop Accuracy 측정 |

**결과:**

| 지표 | 값 |
|------|-----|
| 수렴률 | 18/18 (100%) |
| 정답률 | 18/18 (100%) |
| Handoff Loss Rate (평균) | 26.4% |
| Backprop Accuracy (평균) | 9.5% |

**난이도별 Loss Rate:**

| 난이도 | Loss Rate | 태스크 예시 |
|--------|-----------|-----------|
| Medium | 19.5~22.9% | math-01, logic-01, synthesis-01 |
| Hard | 39.8~47.3% | math-02, logic-02 |

**핵심 발견:**
1. **synthesis-02 문제 완전 해결** — 지시 강조가 아닌 스키마 강제로
2. JSON Mode + Temperature 0.1이 파싱 오류 99% 제거
3. **시스템은 피드백 전파(backprop 9.5%)가 아닌 반복 수렴으로 작동**
4. Hard 태스크(logic-02: 47.3% loss)에서 E4B 복잡도 상한 확인

**결론:** 출력 구조 강제 > 프롬프트 강화. 100% 정확도 달성. Hard 태스크에서 복잡도 상한 존재.

---

### Exp05b: 태스크 난이도 스케일업 (스트레스 테스트)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) + Handoff Protocol |
| **언제** | 2026-04-14 |
| **어디서** | Windows Ollama |
| **무엇을** | 확장 태스크셋(9개: 기존 6 + 고난도 3종) × 5 트라이얼 = 45 시행으로 스케일업 |
| **왜** | Exp045의 100% 정확도가 태스크 다양성·난이도 증가에서도 유지되는지 검증 |
| **어떻게** | math-03, logic-03, synthesis-03 추가. 각 태스크 5회 반복으로 통계적 신뢰도 확보 |

**결과:**

| 지표 | 값 |
|------|-----|
| 전체 정답률 | 40/45 (88.9%) |
| 신규 고난도 3종 | 14/15 (93.3%) |
| 최약 태스크 | logic-02: 2/5 (40%) |
| Handoff Loss Rate | 20.3% |
| Backprop Accuracy | 25.9% |

**채점:** v1=0.649, v2=0.900

**핵심 발견:**
1. 고난도 태스크에서도 높은 정확도(93.3%) 유지
2. logic-02(모순감지+포함배제)가 유일한 약점 (40%)
3. 5회 반복으로 통계적 신뢰도 확보됨

**결론:** A-B-C + Handoff는 고난도까지 확장 가능. logic-02 유형만 E4B 한계.

---

### Exp06: Solo-Budget 비교 (시너지 측정)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 1 (Solo: 동일 compute 예산) |
| **언제** | 2026-04-15 |
| **어디서** | Windows Ollama |
| **무엇을** | A-B-C와 동일한 compute 예산을 단일 에이전트에 부여했을 때의 성능 비교 |
| **왜** | A-B-C의 우위가 "역할 분리 시너지"인지 "단순 반복 효과"인지 구분. 동일 예산 → 성능 차이 = 구조적 시너지 |
| **어떻게** | Solo: E4B × 1에 ABC와 동일 루프 예산 부여. 9개 태스크 × 5 trial = **45 시행** (ABC와 동일) |

**결과 (v1/v2/v3 정합 비교, 45 vs 45):**

| 채점법 | Solo (45 trial) | ABC (45 trial) | Δ (Solo−ABC) |
|--------|-----------------|----------------|-------------|
| v1 (partial score) | 0.663 | 0.649 | +0.015 |
| v2 (keyword group) | 0.967 | 0.900 | +0.067 |
| v3 (neg+keyword) | 0.967 | 0.900 | +0.067 |

95% CI (bootstrap N=10,000): v1 Solo [0.573, 0.748] vs ABC [0.553, 0.737] — 중첩, 통계적 유의미성 미확인.

**주의사항 (2026-04-29 채점 정합성 정정):**
- 기존 기록 "Solo 표본 9"는 **사실 오류** — Solo = 9 task × 5 trial = 45 trial. ABC와 동일.
- 기존 비교 "ABC 88.9% > Solo 66.3%" (+22.6%p)의 출처:
  - trial-level `v1 > 0.2` 기준 → ABC 40/45 = **88.9%** 재현 가능 (Solo는 같은 기준 41/45 = 91.1%)
  - task-level `v2 mean ≥ 0.75` 기준 → ABC **8/9 = 88.9%** 재현 가능 (logic-02만 탈락)
  - 원본 채점법의 정확한 정의 불명 — disclosure에 그침
- v2 keyword 매칭이 Solo의 조기 수렴 답을 과대평가할 가능성 (keyword 존재만 확인)

**핵심 발견 (정합 비교 기반):**
1. 재현 가능한 모든 채점법(v1/v2/v3)에서 Solo ≥ ABC — ABC 정확도 우위 미확인
2. **Solo 조기 수렴** — 평균 4.5 loops에서 수렴 (ABC 21.6 calls 대비). 외부 비판 없이 빠르게 종료
3. ABC는 logic-01에서 완전 정답(5/5), Solo는 1건 실패(4/5) — 복잡 추론에서 ABC 안정성 잔존
4. CI 중첩 → 현 task set에서 차이가 통계적으로 유의미하지 않을 수 있음

**결론 (H4 재평가):** 이 9-task set에서 채점 정합 비교로는 ABC 구조적 우위를 확인할 수 없음.
역할 분리의 구조적 차이(비판 루프 유무)는 실재하나, 이 task 난이도 범위에서 정확도 Δ로 나타나지 않음.
확대 task set 또는 고난도 task 집중 검증이 H4 재확인의 다음 단계. → **H4: 미결** (해소: 2026-05-02 Stage 2C — 아래 §"H4 재검증 (2026-05-02)" 참조)

#### H4 재검증 (2026-05-02 Phase 2 Stage 2C)

확대 task set (12 → 15: planning 2 + synthesis-05) + 3 condition (Solo-1call / Solo-budget / ABC) ablation 재검증. **plan**: `exp06-h4-recheck-expanded-taskset-pre-exp11`.

| 비교 | Δ acc |
|------|------:|
| Solo-budget − Solo-1call (다단계 효과, H1 재확인) | +0.0700 |
| **ABC − Solo-budget (역할 분리 단독 효과, H4 본 가설)** | **+0.0444** |
| ABC − Solo-1call (합산) | +0.1144 |

condition mean: Solo-1call 0.6444 / Solo-budget 0.7144 / **ABC 0.7589**. median per-task: 0.667 / 0.867 / **1.000**.

**카테고리별 Δ(abc−sb)**: math +0.000 (saturation) / logic −0.025 (logic-04 v3 negative_patterns 효과) / **synthesis +0.140 (회복 핵심)** / planning +0.033 (신규 2 task).

**통계** (n=15 paired): Wilcoxon p=0.16, t-test p=0.10 (NOT SIGNIFICANT — n=15 검정력 한계). Cohen's d = 0.449 (medium). Bootstrap 95% CI Δ(abc−sb): [−0.0044, +0.0911] (0 거의 포함, 임계).

**verdict 변경**: ⚠ 미결 → **⚠ 조건부 채택 (synthesis 카테고리 한정)**. 9-task subset 의 Solo +0.067 우위 → 15-task 확대 시 ABC +0.044 우위로 방향 반전.

**한계**:
- assertion turnover ABC 측정 불가 (`run.py:115` 의 tattoo_history 저장 결함 — final tattoo 1 개만, cycle-by-cycle 부재). Stage 4 Exp11 plan 시 보강
- logic-04 의 ABC −0.20: v3 negative_patterns 가 false positive 차단 효과. ABC 약함 vs 채점 정직성 분리 어려움

상세: `docs/reference/h4-recheck-analysis-2026-05-02.md`. 결과 JSON: `experiments/exp_h4_recheck/results/h4_recheck_{solo_1call,solo_budget,abc}.json`.

→ Stage 3 (Exp11 Mixed Intelligence) 함의: Role 축 강화 가설 정합성 부분 회복. synthesis 카테고리 강조 권장.

---

### Exp07: Loop Saturation + Loop-Phase 프롬프트

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) — 모델 소스가 Ollama Q4_K_M → llama.cpp Q8_0으로 전환 |
| **언제** | 2026-04-23 ~ 2026-04-24 (Gemini CLI / Windows에서 완주) |
| **어디서** | Windows + 외부 llama.cpp GPU 서버 (`yongseek.iptime.org:8005`, OpenAI 호환 `/v1/chat/completions`) |
| **무엇을** | 2(프롬프트: baseline/phase) × 4(MAX_CYCLES: 8/11/15/20) 요인설계로 루프 포화점 식별 + phase 특화 프롬프트 효과 측정 |
| **왜** | "11루프는 정말 충분한 샘플인가?"라는 의문에서 출발. 기존 태스크셋이 저난도(조기 수렴)에 치우쳐 루프 한계를 측정하지 못함. 고난도 태스크(04급) 3종 추가 + MAX_CYCLES 상한을 변수화하여 **한계 수익 0에 수렴하는 포화점 탐색** |
| **어떻게** | 고난도 태스크(math-04, logic-04, synthesis-04) 3종 추가 → 총 12 태스크. 각 태스크 × 3 trial × 8 조건 = **288 시행**. `orchestrator.py`/`config.py`에 MAX_CYCLES·use_phase_prompt 파라미터 추가, `run_experiment.py`에 loop_saturation 분기 추가, measure.py에 phase별 집계 + High-Difficulty 표 추가 |

**결과 (정답률, substring 기반 — exp07_report.md):**

| MAX_CYCLES | Baseline 정답률 | Phase 정답률 | Δ (Phase − Base) | Baseline 수렴률 | Phase 수렴률 |
|------------|----------------|-------------|------------------|-----------------|--------------|
| 8  | 79.2% | 83.8% | +4.6%p  | 91.7%  | 100.0% |
| 11 | 86.6% | 83.8% | −2.8%p  | 100.0% | 100.0% |
| 15 | 81.5% | **88.0%** | **+6.5%p** | 100.0% | 100.0% |
| 20 | 80.1% | 85.6% | +5.6%p  | 100.0% | 100.0% |

**고난도(04) 태스크:**

| 태스크 | 최고 정답률 | 최고 조건 | 평균 cycles |
|--------|-----------|-----------|-------------|
| logic-04     | 100.0% | baseline_11 | 7.0 |
| math-04      | **50.0%** | baseline_11 | 6.0 |
| synthesis-04 | 100.0% | baseline_11 | 7.0 |

**actual_cycles 분포 (모든 조건, 288 trial 원시 데이터):**

| 조건 | 평균 actual_cycles |
|------|-------------------|
| baseline_8  | 7.00 |
| baseline_11 | 7.00 |
| baseline_15 | 6.89 |
| baseline_20 | 6.86 |
| phase_8     | 7.03 |
| phase_11    | 6.97 |
| phase_15    | 7.11 |
| phase_20    | 7.00 |

**핵심 발견:**
1. **포화점은 MAX_CYCLES가 아니라 actual_cycles ≈ 7** — MAX_CYCLES 상한을 15, 20으로 올려도 실제 사용 cycle은 약 7에서 멈춤. 즉 C(판정자)의 수렴 판정이 "루프 예산 소진" 이전에 항상 선행됨.
2. **H5 부분 기각** — "상한 확장 = 정답률 증가"는 성립하지 않음. MAX_CYCLES=11에서 baseline이 가장 좋고(86.6%), 15/20에서는 오히려 소폭 감소. 상한 자체는 정답률의 함수가 아니라 "안전장치" 역할.
3. **H6 조건부 채택** — Phase 특화 프롬프트는 **장기 루프(15, 20)에서만** baseline 대비 +5~6%p 우위. 짧은 루프(11)에서는 오히려 −2.8%p. 해석: phase 가이드는 "짧은 추론에선 불필요, 긴 추론에선 drift 억제" 효과.
4. **math-04 벽** — 수학적 다단계 추론(04급)은 루프·프롬프트 양쪽 어떤 조건으로도 50%를 넘지 못함. logic-04/synthesis-04는 모든 조건에서 100%. → 수학 추론 한계는 구조 개선으로 해소되지 않음. **※ Exp08 정정**: 이 "50%"는 **채점 데이터 결함**에 따른 artifact였다. 당시 `taskset.json`의 `expected_answer="X=30,Y=30,Z=10,profit=$2800"`은 material 제약(3·30+2·30+1·10=160 > 150 kg)을 위반하는 비가능 해였으며, `scoring_keywords=[["30"],["2800"]]` 기준으로 우연히 "30"을 포함한 답변들이 부분점수를 받았다. 정답 보정(X=31, Y=10, Z=37, profit=$3060) 후 Exp08 baseline에서 math-04는 **0%**였다. 즉 E4B는 tool 없이 이 LP 문제를 실질적으로 풀지 못한다.
5. **수렴률은 거의 무차별** — baseline_8만 91.7%, 나머지 7개 조건 100%. Q8_0 전환 + 루프 여유로 수렴 자체는 안정화됨.
6. **인프라 전환 영향** — Q4_K_M(Ollama) → Q8_0(llama.cpp) 전환으로 모델 정밀도 2배. 이전 실험 대비 같은 태스크(math-01~03, logic-01~03, synthesis-01~03)의 기저 품질이 상승했을 가능성. **Exp05b와의 직접 비교는 주의.**

**결론:**
- **루프 수 증가로 얻을 수 있는 이득은 이미 소진됨** — E4B A-B-C 구조의 cycle 포화점은 약 7.
- **Phase 프롬프트는 "비용 없는 안전마진"**으로 작용 — 긴 루프에서 drift 억제 효과.
- **다음 병목은 루프가 아닌 task-intrinsic 복잡도** (math-04).
- 운영 기본값: `MAX_CYCLES=11, use_phase_prompt=True` 권장 (phase_11이 저비용·고안정).

**알려진 이슈:**
- `experiments/results/exp07_report.md`가 UTF-16 LE로 저장됨 (Windows PowerShell `>` 리다이렉트 기본 인코딩). `measure.py` 출력 경로 또는 run 스크립트에서 UTF-8 강제 필요 — 후속 정리 항목. **Exp08에서 `--output` 옵션 도입으로 근본 해결.**

---

### Exp08: Math Tool-Use (calculator + linalg + linprog)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) + 외부 수학 도구 3종을 A 경로에만 주입. B/C는 도구 없음. |
| **언제** | 2026-04-24 (Gemini CLI / Windows에서 완주) |
| **어디서** | Windows + 외부 llama.cpp GPU 서버 (`yongseek.iptime.org:8005`, OpenAI 호환 tool_calls 경로) |
| **무엇을** | H7 검증 — "외부 수학 도구가 E4B의 계산 한계를 보완하는가". 그리고 Exp07 math-04 50% 정체의 진짜 원인 규명. |
| **왜** | Exp07에서 math-04가 8개 조건 모두 50%로 완전 정체 → 루프·프롬프트로는 돌파되지 않는 구조적 벽 확인. llama.cpp 서버의 `supports_tools: true` 활용 가능성 + `scipy.linprog`으로 해당 LP 문제가 실제 정확히 풀림을 확인한 상태에서 실험 설계. |
| **어떻게** | **부수적 발견**: 설계 과정에서 기존 `taskset.json`의 math-04 `expected_answer="X=30, Y=30, Z=10, profit=$2800"`이 material 제약 위반 (material 160 > 150)임을 발견. 올바른 최적해 X=31, Y=10, Z=37, profit=$3060으로 정정 (커밋 `6c6f198`). 이후 실험: 2 arm(baseline_phase15 / tooluse_phase15) × 4 math 태스크(math-01~04) × 5 trial = **40 runs**. MAX_CYCLES=15, use_phase_prompt=True 고정. 도구: `calculator`(AST 화이트리스트 eval), `solve_linear_system`(numpy), `linprog`(scipy HiGHS). |

**결과 (v2 채점):**

| Arm | Accuracy (v2) | Accuracy (v1) | Avg Cycles | Tool Calls / Errors |
|-----|---------------|---------------|------------|---------------------|
| baseline_phase15 | 0.72 | 0.64 | 7.8 | — |
| **tooluse_phase15** | **0.90** | **0.75** | **7.2** | **18 / 4** |
| **Δ (v2)** | **+0.183 (+18.3%p)** | +0.11 | −0.6 | — |

**태스크별:**

| 태스크 | Baseline | Tool-use | Δ | 평균 tool_calls |
|--------|----------|----------|-----|-----------------|
| math-01 | 1.00 | 1.00 | ±0 | 1.6 |
| math-02 | 1.00 | 1.00 | ±0 | 0.8 |
| math-03 | 0.87 | 0.80 | −0.07 (노이즈, 양쪽 모두 "inconsistent" 정답) |
| **math-04** | **0.00** | **0.80** | **+0.80** | 1.0 |

**도구별 성공률:**

| Tool | Calls | Errors | 성공률 | 주요 에러 |
|------|-------|--------|--------|-----------|
| `linprog` | 5 | 0 | 100% | — |
| `solve_linear_system` | 7 | 1 | 86% | `Singular matrix` 1건 (모델이 LP를 연립방정식으로 오해) |
| `calculator` | 6 | 3 | 50% | `BitXor` 3건 (모델이 `^`를 거듭제곱으로 사용 — Python 의미는 XOR) |

**핵심 발견:**
1. **H7 채택** — 전체 정답률 +18.3%p, 특히 math-04에서 0% → 80% (+80%p)로 결정적 돌파.
2. **Exp07 해석 전복** — math-04 baseline 5 trial을 전수 확인한 결과: 4건이 `final_answer=None` (10~11 cycle 돌고도 답 생성 실패), 1건은 `X=25, Y=10, Z=35, profit=2700` 오답. 즉 E4B는 tool 없이 이 LP 문제를 거의 풀지 못한다. Exp07의 50%는 잘못된 expected_answer(X=30,Y=30,Z=10,profit=2800)의 부분 substring 매칭으로 인한 채점 artifact.
3. **제멘토 가설 재확인** — "소형 LLM + 외부 상태(문신)" 설계 패턴이 "소형 LLM + 외부 도구(tool_calls)" 방향으로 자연스럽게 확장됨. 내부 능력이 아닌 **외부 자원으로 구조적 한계를 뚫는다**는 설계 원칙이 두 차원 모두에서 성립.
4. **Tool 부작용 1 — Tool neglect** — math-04 tooluse trial 2에서 도구가 주입되어도 모델이 한 번도 호출하지 않고(tc=0) 10 cycle 돌다 `None` 반환. 도구의 존재가 사용을 보장하지 않음 → 프롬프트 또는 `tool_choice` 전략 필요.
5. **Tool 부작용 2 — Calculator `^` 혼동** — 모델이 Python `^`(XOR)를 수학적 거듭제곱으로 오인하여 `2^10` 같은 식을 생성. AST whitelist가 정확히 차단하지만 에러 메시지("Disallowed operator: BitXor")가 모델에게 친절하지 않음. 개선안: 힌트 추가 또는 `^`를 `**`로 전처리.
6. **math-03 "하락"은 노이즈** — 답변 전수 확인 결과 baseline/tooluse 양쪽 모두 "문제가 모순이다"라는 올바른 결론. 차이는 표현상 keyword 매칭 변동(특히 한국어 답변 1건이 영향). 실질적 성능 차이 없음.
7. **평균 cycle 감소** — Baseline 7.8 → Tooluse 7.2. 도구가 조기 수렴을 유도. 특히 math-04에서 baseline 10~11 cycle(모두 실패) vs tooluse 7~8 cycle(대부분 성공) 대비 뚜렷.

**결론:**
- **H7 완전 채택**. 외부 도구는 E4B의 **구조적 계산 한계**(특히 최적화)를 돌파한다.
- 제멘토의 원래 설계 원칙("외부 자원으로 한계 보완")이 도구 차원에서도 유효함을 입증.
- Exp07의 math-04 해석은 **채점 데이터 결함으로 인한 오류**였음 — 연구 파이프라인에서 expected_answer 검증 절차의 필요성 부각.

**알려진 이슈 / 후속 과제:**
- Calculator `^` BitXor 혼동 → 에러 메시지 개선 또는 전처리. **→ Exp08b에서 해결**.
- Tool neglect 패턴 → tool_choice 전략 또는 프롬프트 강화. **→ Exp08b에서 해결**.
- math-03 한국어 답변 + v2 scoring 매칭 확인 필요.
- 본 실험은 **Exp07과 직접 비교 불가** (math-04 expected_answer 변경, Q8_0 환경 동일하나 태스크셋 수정).

---

### Exp08b: Tool-Use Refinement (에러 힌트 + Mandatory rules)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) + 개선된 도구 + 강화된 SYSTEM_PROMPT |
| **언제** | 2026-04-24 (Gemini CLI / Windows에서 완주) |
| **어디서** | Windows + 외부 llama.cpp GPU 서버 |
| **무엇을** | H8 검증 — Exp08에서 발견된 2개 부작용(calculator `^` 혼동, tool neglect) 완화 후 재측정 |
| **왜** | Exp08 결과는 H7 채택이었으나 부작용 2가지로 운영 안정성이 제한적. (a) calculator BitXor 3/6 실패, (b) math-04 trial 2에서 tool을 한 번도 호출하지 않고 실패. 이 2개를 최소 침습 개선으로 해결할 수 있는지 검증 |
| **어떻게** | (1) `experiments/tools/math_tools.py`의 `_eval()`에서 `BitXor` 케이스에 "use `**` for power; Python `^` is bitwise XOR" 힌트 추가. (2) `experiments/system_prompt.py:SYSTEM_PROMPT` Tool use 섹션에 Mandatory rules 4개 추가(LP는 linprog 의무 호출, `^` 사용 금지, 에러 후 재시도 의무, fabrication 금지). (3) `run_experiment.py`에 `tool-use-refined` 커맨드 추가하여 2 arm × 4 math 태스크 × 5 trial = **40 runs** 동일 설정 재측정. (4) `measure.py:analyze_tool_use`에 `tool_neglect_rate` 메트릭 추가 |

**결과 (v2 채점):**

| Arm | Accuracy (v2) | Accuracy (v1) | Avg Cycles | Tool Calls / Errors |
|-----|---------------|---------------|------------|---------------------|
| baseline_refined | 0.73 | 0.53 | 8.0 | — |
| **tooluse_refined** | **0.97** | **0.77** | **6.9** | **37 / 6** |
| **Δ (v2)** | **+0.233 (+23.3%p)** | +0.24 | −1.1 | — |

**태스크별 (v2):**

| 태스크 | Baseline | Tool-use | Δ | 평균 tool_calls |
|--------|----------|----------|-----|-----------------|
| math-01 | 1.00 | 1.00 | ±0 | 1.8 |
| math-02 | 1.00 | 1.00 | ±0 | 2.2 |
| math-03 | 0.93 | 0.87 | −0.07 | 1.4 |
| **math-04** | **0.00** | **1.00** | **+1.00** | 2.0 |

**도구별 성공률:**

| Tool | Calls | Errors | 성공률 | 변화 (Exp08 → Exp08b) |
|------|-------|--------|--------|---------------------|
| `calculator` | 16 | 0 | **1.00** | 0.50 → **1.00** (BitXor 힌트 완전 성공) |
| `solve_linear_system` | 12 | 6 | 0.50 | 0.86 → 0.50 (호출 증가로 에러 노출, 전부 math-03 Singular matrix) |
| `linprog` | 9 | 0 | **1.00** | 1.00 → 1.00 (유지) |

**부작용 해결 상태:**

| 개선 대상 | Exp08 | Exp08b | 목표 | 달성 |
|----------|-------|--------|------|------|
| Calculator 성공률 | 0.50 | **1.00** | ≥0.85 | ✅ 초과 |
| Tool Neglect Rate | 0.20 (1/5) | **0.00 (0/20)** | 0.00 | ✅ 정확 |
| Tooluse arm 정답률 | 0.90 | **0.97** | ≥0.95 | ✅ 초과 |
| math-04 정답률 | 0.80 | **1.00 (5/5)** | — | ✅ 완승 |

**핵심 발견:**
1. **H8 완전 채택** — 3개 목표 모두 달성·초과. Exp08 대비 **+7%p** 추가 상승 (90%→97%).
2. **math-04 완승** — Exp08에서 4/5(trial 2 neglect)였던 것이 **5/5 전부 정답** (31, 10, 37, 3060). "LP는 linprog 의무 호출" 규칙이 tool neglect를 완전히 차단.
3. **Calculator BitXor 완전 해결** — Exp08에서 6회 호출 중 3회 실패(50%)였던 것이 **16회 호출 전부 성공**. 에러 힌트가 모델의 **재시도 방향**을 성공적으로 교정했다는 직접 증거.
4. **Avg Cycles 감소** — baseline 8.0 vs tooluse 6.9. 도구와 Mandatory rules이 **조기 수렴**을 유도. Exp08 tooluse(7.2)보다도 더 짧아짐.
5. **Exp07 해석 재확인** — math-04 baseline은 0% (Exp08과 동일). 즉 "Exp07의 50% 정체는 채점 데이터 artifact"였다는 결론이 독립 측정으로 재확인됨.
6. **math-03 0.93 → 0.87**: baseline에 비해 tool 도입 후 0.07 하락. 답변 내용은 양쪽 모두 "문제가 모순"이라는 올바른 결론 — 노이즈 범위로 해석.
7. **solve_linear_system Singular matrix 6건**: 전부 math-03 (모순 문제). 모델이 연립방정식 접근을 시도하고 도구가 "특이 행렬"로 정확히 반환. 도구 측 문제가 아니라 **모순 문제에서 모델의 자연스러운 탐색 경로**. 최종적으로 "inconsistent" 결론 도달. 운영 이슈 아님.

**결론:**
- **H8 완전 채택**. 에러 힌트 + Mandatory rules이라는 **프롬프트·피드백 수준의 최소 침습 개선**이 97% 정답률을 만든다.
- 소형 모델도 **오케스트레이션(규칙)과 정밀한 도구 활용**이 결합되면 초거대 모델급의 추론 안정성을 달성할 수 있음을 입증.
- 제멘토 설계 원칙("외부 자원으로 한계 보완 + 결정론적 제약이 비결정론적 품질을 끌어올린다")의 추가 증거.

**알려진 이슈 / 후속 과제:**
- **solve_linear_system 에러 힌트 추가 후보** — "Singular matrix" 에러에 "데이터가 inconsistent할 수 있음" 힌트를 붙이면 모델의 "모순 문제" 판단을 가속할 수 있을지 검증 가능 (Exp08c 후보).
- math-03 한국어 답변 + v2 scoring 편차 여전 — 독립 이슈로 남음.
- **다음은 Exp09** — Exp08b의 성공이 "단일 태스크 단발 추론"에 한정된 증거. Long-context stress / stream workflow / cross-model 중 하나로 진행 필요.

---

### Exp09: Long-Context Stress Test (ABC vs Solo-dump vs RAG)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B × 3 (A-B-C) + Tattoo evidence_ref + 신규 longctx 태스크셋 |
| **언제** | 2026-04-25 (Gemini CLI / Windows에서 완주) |
| **어디서** | Windows + 외부 llama.cpp GPU 서버 (n_ctx 8K × 4 slot) |
| **무엇을** | H9 검증 — 제멘토의 **원래 핵심 가설**("외부 상태로 유효 컨텍스트 확장")의 정면 측정. 제멘토 ABC + Tattoo가 (a) Solo-dump보다 우수하고 (b) 표준 RAG baseline 대비 고유 기여를 보이는가 |
| **왜** | 지금까지 H1·H4·H7·H8은 "계산·추론" 한계를 외부화 도구로 보완. 그러나 **컨텍스트 자체**의 한계는 직접 측정한 적 없음. Exp09는 sliding_window(512)의 20~40배 크기 문서로 이 가설을 정면 검증. RAG 대비 차별성도 함께 측정하여 "제멘토 = 그냥 RAG + loop" 반론 차단 |
| **어떻게** | 신규 태스크셋 `experiments/tasks/longctx_taskset.json` (10 tasks, 3 size class × 3 hop type). 3 arm × 10 tasks × 3 trial = **90 runs**. Arm: (1) `solo_dump` — 문서 전체+질문 단일 호출, n_ctx 초과 시 truncation, (2) `rag_baseline` — `bm25s` top-K=5 chunks 단일 호출, (3) `abc_tattoo` — chunk 순회 + evidence_ref 누적 + 최종 B+C 수렴. 새 인프라: `tools/chunker.py`, `tools/bm25_tool.py`, `Assertion.evidence_ref` 필드, `run_abc_chunked()`, `analyze_longctx`+error mode taxonomy |

**결과 (v2 채점, 90 runs):**

| Arm | Accuracy v2 | Accuracy v1 | Errors |
|-----|-------------|-------------|--------|
| solo_dump | 0.20 | 0.20 | 24/30 (format_error) |
| rag_baseline | 0.85 | 0.90 | 0 |
| **abc_tattoo** | **0.88** | **0.93** | 0 |

**Key Deltas (v2):**
- **H9a (abc − solo)**: **+68.3%p** ✅ 압도적 채택
- **H9b (abc − rag)**: **+3.3%p** ✅ 조건부 채택 (전체는 미세, 3-hop에서 +33%p로 차별성 명확)

**Size class 분해 — 물리 한계 돌파 검증:**

| Arm | Small 3K | Medium 10K | Large 20K |
|-----|---------|-----------|----------|
| solo_dump | 1.00 | **0.00** | **0.00** |
| rag_baseline | 1.00 | 0.88 | 0.75 |
| **abc_tattoo** | **0.67** | 0.88 | **1.00** |

**Hop type 분해 — H9b 차별성의 origin:**

| Arm | needle | 2-hop | 3-hop |
|-----|--------|-------|-------|
| solo_dump | 0.33 | 0.25 | 0.00 |
| rag_baseline | 1.00 | 0.88 | 0.67 |
| **abc_tattoo** | 0.78 | 0.88 | **1.00** |

**Per-task 하이라이트:**

- `longctx-large-3hop-01`: solo 0% / **rag 0%** / **abc 100%** — RAG의 정보 단절이 실측 데이터로 입증된 단일 태스크.
- `longctx-small-needle-01`: solo 1.00 / rag 1.00 / **abc 0.33** — Small Paradox의 핵심 사례.

**에러 모드 (H9c):**

| Arm | 주요 실패 패턴 |
|-----|--------------|
| solo_dump | `format_error` 24건 — n_ctx 초과 truncation으로 인한 응답 불완전 |
| rag_baseline | `wrong_synthesis` 6건 — 검색은 맞았지만 통합 실패 |
| abc_tattoo | `evidence_miss` 2 + `wrong_synthesis` 3건 — 검증 경로 거쳤기에 다른 패턴 |

**Evidence Hit Rate (ABC arm):**
- Overall: 0.35
- needle 0.33 / 2-hop 0.50 / **3-hop 0.23**
- 흥미로운 비대칭: 3-hop은 hit rate가 가장 낮은데 정답률은 100%. "필요한 모든 증거를 찾는 것"보다 "검증 경로로 합리화하는 것"이 정답률에 더 영향이라는 가설.

**핵심 발견:**
1. **H9a 압도적 채택** — Solo는 Medium 이상에서 **완전 전멸 (0%)**, ABC는 Large 20K에서 **100%**. 제멘토 원래 가설 ("외부 상태가 유효 context 확장")의 가장 강력한 단일 증거.
2. **H9b 조건부 채택 — 차별성은 3-hop에서 발생** — needle/2-hop은 RAG와 거의 동등(±0~12%p). **3-hop만 ABC 100% vs RAG 67% (+33%p)**. 즉 "제멘토 ≠ 그냥 RAG + loop"는 **다중 증거 통합 영역에서만** 성립.
3. **H9c 채택** — 3개 arm의 실패 모드가 질적으로 다름 (truncation vs 정보 단절 vs 검증 후 잔여 오류).
4. **Small Paradox 새 발견** — ABC가 small에서 RAG보다 약함(0.67 vs 1.00). 표본 노이즈일 수도, 실제 패러독스(chunk 적을 때 cycle iteration이 오버킬)일 수도. Gemini도 Exp10 후보로 명시.
5. **Solo의 단조 붕괴** — 1.00 (small) → 0.00 (medium) → 0.00 (large). n_ctx 8K에 근접하는 시점부터 truncation이 즉시 실패로 이어짐. 모델이 chunk 잘린 응답을 정상화하지 못함.

**결론:**
- **제멘토 원래 핵심 가설(컨텍스트 한계 외부화) 정면 입증**. conceptFramework § 1의 4축 외부화 원리 중 **Tattoo(상태 외부화)**의 가장 강력한 단일 증거가 확보됨.
- "제멘토 = RAG + loop"라는 단순화 반론 차단 — 단 차별성은 **다중 증거 통합 영역에 한정**. needle 같은 단순 retrieval에선 RAG로 충분.
- **다음 후보 (Exp10+)**: Small Paradox 해결, 병렬 chunk 순회 (Gemini 핸드오프 제언), Stream Workflow (장기 처리).

**알려진 이슈 / 후속 과제:**
- **Small Paradox** — small needle 1개 태스크에서 ABC 0.33. 표본(small=2 tasks × 3 trial = 6 데이터포인트) 작아 노이즈 가능. 추가 trial 또는 small 태스크 확대로 검증 필요.
- **Evidence Hit Rate ↔ 정답률 비대칭** — 3-hop hit 0.23 vs 정답률 100%. 모델이 정답 외 chunk도 evidence_ref에 첨부하는 경향. gold_evidence_chunks 라벨링이 너무 엄격할 가능성도.
- **통계 신뢰도 검정 완료 (Phase 1, 5-trial)** — paired t-test p=0.7976, Wilcoxon p=1.000 → **비유의**. H9b verdict "조건부 채택"→"미결"로 변경. **단, 2026-04-30 후속 분석에서 trial 4-5 무효 판정** — 아래 §5-trial 점수 하락 분석 참고.
- **5-trial 점수 하락 분석 (2026-04-30 Phase 1 후속)** — trial 4-5 가 Windows 모델 서버 (`http://yongseek.iptime.org:8005`) connection refused (WinError 10061) 로 인한 무효 실행 (rag/solo 20/20 error, abc 20/20 `num_assertions=0`). 3-trial mean × 3/5 = 5-trial mean 정확 일치 (0.883×0.6=0.530, 0.850×0.6=0.510). 5-trial 통계 비유의는 부당한 강등 근거. 3-trial 결과 (Δ=+0.033) 가 여전히 H9b 의 가장 정확한 데이터. 상세: `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`. `run_append_trials.py` 의 retry / healthcheck 보강은 별도 plan 후보.

#### 통계 검정 최종 결과 (Phase 1, 2026-04-30)

5 trial × 10 task (50 데이터포인트/arm) 기반:

| 검정 | 통계량 | p-value | 판정 |
|------|--------|---------|------|
| Paired t-test (task mean, n=10) | t=0.264 | 0.7976 | 비유의 |
| Wilcoxon signed-rank | W=1.0 | 1.000 | 비유의 |

- Overall mean: abc=0.530, rag=0.510 (Δ=+0.020)
- Cohen's d = 0.084 (효과 크기 극히 작음)
- Bootstrap 95% CI for Δ(abc−rag): [−0.170, 0.210] (포함 0)

> **해석**: n=10 task로 검정력 부족. 비유의 = "효과 없음"이 아니라 "현재 데이터로 판단 불가". 전체 Δ=+2.0%p는 실질적 차이로 보기 어려움.

Size class / Hop type 분해 (5-trial):
- small tasks (n=2): abc=0.400 vs rag=0.600 (Δ=−0.200) ◄ **Small Paradox 확인**
- medium tasks (n=4): abc=0.525 vs rag=0.525 (Δ=0.000)
- large tasks (n=4): abc=0.600 vs rag=0.450 (Δ=+0.150)
- 3-hop tasks (n=3): abc=0.600 vs rag=0.400 (Δ=+0.200) ← 차별성 잔존
- needle tasks (n=3): abc=0.467 vs rag=0.600 (Δ=−0.133)

Small Paradox 상세:
- `longctx-small-needle-01`: abc=0.200 vs rag=0.600 (Δ=−0.400, trials=[0,0,1,0,0])
- `longctx-small-2hop-01`: abc=0.600 vs rag=0.600 (Δ=0.000, trials=[1,1,1,0,0])

---

### Exp10: Reproducibility & Cost Profile (v2 final)

| 항목 | 내용 |
|------|------|
| **누가** | Gemma 4 E4B (LM Studio Q4_K_M) × ABC 8루프 vs Gemma 4 E4B 단발 vs Gemini 2.5 Flash 1-call |
| **언제** | 2026-04-28 (Windows 본 run) → 2026-04-29 (Mac retry/merge/finalize) |
| **어디서** | Windows + LM Studio (gemma_8loop, gemma_1loop) + Google AI Studio (gemini_flash_1call) |
| **무엇을** | 정확도 + 비용 + 지연 3축 cost-aware 비교. 3 condition × 9 task × N=20 trial = **540 trial** |
| **왜** | "제멘토 ABC 가 폐쇄형 대형 1-call 을 능가하는가"의 직접 측정. 동일 모델 1-loop vs 8-loop 비교로 H1(외부 상태+반복) 의 직접 증거 추가 확보 |
| **어떻게** | gemma_8loop = ABC + max_cycles=15 + use_phase_prompt=True. gemma_1loop = 단발. gemini_flash_1call = response_mime_type=application/json. 본 v2 결과 두 artifact 패치 — `(gemma_8loop, math-04)` 20 trial 을 use_tools=True debug rerun 으로 substitute, `(gemini_flash, logic-04)` 4 timeout trial 을 timeout=300s 재시도로 substitute |

**결과 (v3 채점, 540 trial):**

| condition | mean_acc (v2) | **mean_acc (v3)** | cost / 180 trial | avg_dur | err+null |
|-----------|--------------:|------------------:|----------------:|--------:|---------:|
| **gemma_8loop** | 0.822 | **0.783** | $0.0000 | 8 min | 8 |
| gemini_flash_1call | 0.620 | **0.593** | $0.0143 | 24 s | 0 |
| gemma_1loop | 0.415 | **0.415** | $0.0000 | 33 s | 11 |

> v3 채점 (2026-04-29 patch): `score_answer_v3` + `taskset.json` logic-04 의 `negative_patterns` 4개. v2 → v3 격차는 logic-04 한정 (false positive 12건 제거).
> **2026-04-30 Phase 1 후속 v3 재산정**: Taskset 3 FAIL (math-03 prompt / synthesis-04 keyword / longctx-medium-2hop-02 expected) 정정 후 `rescore_v3` 재실행 (`exp10_v3_rescored_20260430_152306.json`). 직전 053939 대비 모든 condition Δ +0.0019 (synthesis-04 task 단독 +0.017, math-03 / logic-04 변동 0). condition mean |Δ| < 0.01 — README 본문 갱신 영향 없음 (사소). 상세: `docs/reference/results/exp-10-reproducibility-cost.md` §8.

**핵심 발견:**
1. **H1 직접 증거 — 외부 상태 + 반복** — 같은 모델 1-loop → 8-loop 가 0.413 → 0.781 (**+37%p**). ABC chain 이 모델 능력을 거의 두 배 끌어올림. 동일 weight·quantization·sampling 조건에서의 측정이라 inference 구조 효과로만 해석 가능.
2. **소형 로컬 vs 폐쇄형 대형** — gemma_8loop (4.5B) 가 Gemini 2.5 Flash 를 정확도에서 **+19%p** 능가. 비용 $0, 단 속도 1/20 (8 min vs 24 s).
3. **logic-04 false positive 발견 (채점기 한계)** — substring 채점으로 v2 acc 0.400 (gemma_8loop) / 0.250 (flash) 이지만 본문은 "no solution"/"contradiction" 류라 strict acc 0.050 / 0.000. 13/60 trial 이 false positive. condition 순위는 동일하지만 v3 채점기 강화 결정적 후보.
4. **로컬 모델 천장 (logic-04)** — strict acc 모든 condition ≤ 0.05. ABC 8루프도 4-suspect 귀류법은 못 뚫음. v3 에서 도구화 또는 multi-stage prompt 검토.
5. **math-04 도구 정책 결정적** — use_tools=False 면 0/20 (전수 fail), True 면 20/20 (linprog 호출). 모델 능력의 한계가 아니라 시스템 정책의 한계. v3 에서 math 카테고리 use_tools 통일 필요.
6. **ABC infrastructure 4 fail** — gemma_8loop 4건 JSON parse 실패 (math-03 t13, synthesis-01 t14, logic-04 t2/t6). 모델 능력이 아닌 인프라 안정성 이슈. v3 patch 후보.

**상세 보고서:** `docs/reference/results/exp-10-reproducibility-cost.md`
**데이터:** `experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json`
**패치 절차:** `docs/reference/exp10-v2-finalize-2026-04-29.md`

**다음 단계 (v3 우선순위):**
1. 채점기 강화 (substring → affirmative/negative 분류 또는 LLM-judge)
2. ABC chain JSON parse 안정성 (raw_response 디버그 로그 분석 → 추출 정규식 보강)
3. logic 카테고리 도구화/multi-stage 또는 외부 propositional logic 도구
4. use_tools 정책 통일 (math 전체 True 강제 후 v3 재실행)
5. 다른 task 의 strict 채점 전수 재산정

---

### Exp11: Mixed Intelligence (Flash Judge)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B = Gemma 4 E4B (LM Studio Q8_0) + C = Gemini 2.5 Flash (`gemini-2.5-flash` API) — Mixed condition. baseline = A/B/C 모두 Gemma |
| **언제 (When)** | 2026-05-02 ~ 2026-05-03 |
| **어디서 (Where)** | Windows + LM Studio (`http://192.168.1.179:1234`) + Google AI Studio (Gemini API) |
| **무엇을 (What)** | H10 후보 — "강한 Judge 가 약한 Proposer/Critic 의 한계를 보완". 2 condition × 15 task × 5 trial = **150 trial** |
| **왜 (Why)** | Stage 2C 의 H4 ⚠ 조건부 채택 (synthesis +0.140 회복) 위에서 Role 축 강화 효과 정밀 측정. README §1 "역할 기반 배치 — 크기가 아니라 판단 유형" 운영 원칙의 가장 직접적 측정 |
| **어떻게 (How)** | `experiments/orchestrator.py:run_abc_chain` 에 `c_caller` 인자 추가 (1-2라인 patch) + `experiments/exp11_mixed_intelligence/run.py` 의 Mixed condition 이 Gemini Flash c_caller 주입. Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history cycle-by-cycle fix 모두 적용 |

**결과 (v3 채점, 150 trial):**

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur | total cost |
|-----------|--:|---------:|----------------:|--------:|-----------:|--------:|-----------:|
| baseline_abc | 75 | **0.7778** | 0.9333 | 7+7 | 7.2 | 437s | $0.0000 |
| mixed_flash_judge | 75 | **0.6967** | 0.8000 | 8+8 | 6.7 | 377s | **$0.0843** |

**Δ(mixed − baseline) = −0.0811** (음수). 통계 (n=15 task paired): Wilcoxon p=0.293 / paired t p=0.241 (NOT SIGNIFICANT). Cohen's d = −0.316 (small effect 음수). Bootstrap 95% CI Δ: [−0.220, +0.022].

**카테고리별 Δ(mixed−baseline)**:
- math: −0.050 (math-01 saturation 깨짐)
- **logic: −0.275** (catastrophic — logic-02 0.9→0)
- **synthesis: +0.030** (유일한 양수 — Stage 2C H4 회복 영역 정합)
- planning: −0.033

**핵심 발견:**
1. **H10 ⚠ 미결 (실효적 기각)** — Mixed (Flash Judge) 가 baseline (모두 Gemma) 대비 우위 부재
2. **assertion turnover 의 H10 메커니즘 부재** — modified 차이 미미 (0.04). Flash Judge 의 "보완" 효과 직접 반증
3. **logic-02 case study (Δ=−0.900)** — baseline 4/5 trial 이 "105 inconsistent" 명시 (inclusion-exclusion 자기 발견), mixed 5/5 trial 이 null 또는 keyword 부재. Flash Judge 가 cycle 단축 + 추론 chain 단절
4. **의외 — Judge 강화의 정반대 메커니즘** — 강한 Judge 가 약한 모델의 self-discovery chain 을 *방해*. 새 가설 후보
5. **synthesis 일부 양수** (+0.030) — Stage 2C H4 회복 영역과 정합. 단 logic catastrophic 가 종합 음수의 동력

**Stage 5 의제 함의:**
- ❌ Mixed Intelligence (Role 강화) 가설 잠정 기각 — 본 방향 후속 plan 비추천
- 🎯 Search Tool / Extractor / Reducer (다른 미외부화 축) 우선 (Exp12 후보)
- Judge prompt 강화 + Mixed 재검증 — 단 정반대 메커니즘 발견으로 동기 흔들림

**상세 보고서:** `docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md`
**결과 데이터:**
- `experiments/exp11_mixed_intelligence/results/exp11_mixed_intelligence_20260502_143554.json` (baseline_abc)
- `experiments/exp11_mixed_intelligence/results/exp11_mixed_flash_judge.json` (mixed)

**한계:**
- n=15 task paired — 통계 검정력 부족. 단정적 기각 어려움 (미결 결론)
- 5 trial 한계
- Tool 축 미검증 (math-04 양쪽 0)
- Flash 의 reasoning 능력 활용 안 됨 (JUDGE_PROMPT 가 단순 verdict 요구)

---

### Exp12: Extractor Role (Role 분리/추가)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B/C 모두 Gemma 4 E4B (LM Studio Q8_0) + **Extractor 도 동일 Gemma**. 외부 API 0 |
| **언제 (When)** | 2026-05-03 ~ 2026-05-04 |
| **어디서 (Where)** | Windows + LM Studio (`http://192.168.1.179:1234`) |
| **무엇을 (What)** | H11 후보 — "신규 Role (Extractor) 이 task prompt 의 claims/entities 를 사전 추출하여 A→B→C input 에 prefix 주입하면 A 부담 감소 + 정확도 향상". 2 condition × 15 task × 5 trial = **150 trial** |
| **왜 (Why)** | Stage 4 Exp11 의 H10 ⚠ 미결 (실효적 기각, 정반대 메커니즘 — 강한 Judge 가 약한 모델 self-discovery 방해) 후 Architect 권장 방향. Role 축 *강화* 가 아니라 *분리/추가* 가 framework 의 자연 진화인지 검증. README §1 "역할 기반 배치" 운영 원칙의 다양화 측정 |
| **어떻게 (How)** | `experiments/system_prompt.py` 에 `EXTRACTOR_PROMPT` + `build_extractor_prompt()` 추가 (claims/entities JSON schema, "do NOT solve / propose" 강제). `experiments/orchestrator.py:run_abc_chain` 에 `extractor_pre_stage: bool = False` 옵션 추가 (1-2 라인 patch, default backward compat). `experiments/exp12_extractor_role/run.py` 신규 (baseline_abc + extractor_abc). Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history cycle-by-cycle fix + Exp11 c_caller 보존 모두 적용 |

**결과 (v3 채점, 150 trial):**

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|----------------:|--------:|-----------:|--------:|
| baseline_abc | 75 | 0.7500 | 1.0000 | 10+10 | 7.3 | 412s |
| **extractor_abc** | 75 | **0.8000** | 1.0000 | 5+5 | 7.1 | 425s |

**Δ(extractor − baseline) = +0.0500** (양수, Exp11 의 −0.0811 정반대). 통계 (n=15 paired): Wilcoxon p=0.198 / paired t p=0.231 (NOT SIGNIFICANT). Cohen's d = +0.323 (small effect 양수). Bootstrap 95% CI Δ: [−0.020, +0.133].

**카테고리별 Δ(ext−base)**:
- math: +0.000 (saturation)
- **logic: +0.125** ⬆ (logic-02 회복 +0.30 — Stage 2C / Exp11 catastrophic 영역)
- **synthesis: +0.050** (synthesis-05 catastrophic 회복 +0.45)
- planning: +0.000 (saturation)

**핵심 발견:**
1. **H11 ⚠ 조건부 채택 (양수 방향, 검정력 한계)** — Δ +0.05 임계, Cohen d +0.323 small 양수, 모든 metric 의 방향이 ext > baseline
2. **Exp11 의 정반대 메커니즘** — 같은 모델 Role 분리는 양수 (+0.05), 강한 모델 Role 강화는 음수 (−0.08)
3. **catastrophic 영역 회복** — logic-02 (0.3→0.6, +0.30) / synthesis-05 (0.55→1.0, +0.45). Stage 2C / Exp11 의 약점 영역에서 Extractor 가 자기 발견 chain 안정화
4. **error mode 안정성 ↑** — NONE 58→63 (+5), err 13%→7% (절반). Extractor 가 catastrophic fail 회피
5. **synthesis-02 역효과** (1.0→0.8, −0.20) — saturation 깨짐, Extractor prefix 가 안정 답을 흔드는 negative case
6. **메커니즘** — assertion turnover (added/modified) 차이 미미. Extractor 효과는 cycle 1 의 *입력 정리* (prompt prefix) 형태 — A 의 작업 *대체* 가 아니라 *보조*

**Role 축 정밀화 진화** (Stage 2C / Exp11 / Exp12 종합):
- H4 (Stage 2C) ⚠ 조건부 채택 — A-B-C 시너지 (synthesis +0.140)
- H10 (Exp11) ⚠ 미결 (실효적 기각) — Role 강화 (Mixed) 정반대 메커니즘
- **H11 (Exp12) ⚠ 조건부 채택** — Role 분리/추가 (Extractor) 양수 방향
- → Role 축 *다양화* (분리/추가) 가 framework 의 자연 진화. 강한 모델 도입 비추천

**Stage 5 다음 의제 (Exp13+):**
- 🎯 Reducer Role (Exp14 후보) — Role 다양화 라인 연속
- Search Tool (Exp13 후보) — Tool 축 신규, Stage 5 SQLite ledger 동기
- Mixed Intelligence 재시도 — 비추천 (Exp11 정반대 메커니즘)
- math-* use_tools 통일 — 별도 plan 후보

**상세 보고서:** `docs/reference/exp12-extractor-role-analysis-2026-05-04.md`
**결과 데이터:**
- `experiments/exp12_extractor_role/results/exp12_extractor_role_20260503_151724.json` (baseline_abc)
- `experiments/exp12_extractor_role/results/exp12_extractor_abc.json` (extractor)

**한계:**
- n=15 task paired — 통계 검정력 부족
- 5 trial 한계
- first_cycle_assertions = 0 — Extractor 메커니즘 직접 측정 결함 (정확도/error mode 로 간접만)
- synthesis-02 역효과 (−0.20) — 추가 분석 필요
- Tool 축 미검증 (math-04 양쪽 0)
- 외부 API 비교 부재 — Exp11 의 cost-aware 와 직접 비교 불가 (다른 메커니즘)

---

### Exp13: Reducer Role (Role 분리/추가 — post-stage)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B/C 모두 Gemma 4 E4B (LM Studio Q8_0) + **Reducer 도 동일 Gemma**. 외부 API 0. Exp12 와 같은 모델 구성, 단 위치만 pre-stage → post-stage 변경 |
| **언제 (When)** | 2026-05-04 ~ 2026-05-05 |
| **어디서 (Where)** | Windows + LM Studio (`http://192.168.1.179:1234`) |
| **무엇을 (What)** | H12 후보 — "신규 Role (Reducer) 가 ABC chain 의 final tattoo + final_answer 를 받아 *post-stage* 에서 정리/통합하면 keyword 매칭 정확도 + final answer 명료성 향상". 2 condition × 15 task × 5 trial = **150 trial** |
| **왜 (Why)** | Exp12 H11 ⚠ 조건부 채택 (Δ +0.05, catastrophic 회복) 후 Architect 권장. **Extractor (pre-stage) ↔ Reducer (post-stage) 대칭 가정 검증** — Role 분리/추가 라인이 위치에 무관하게 안전한지, 또는 위치-효과 비대칭이 존재하는지 측정 |
| **어떻게 (How)** | `experiments/system_prompt.py` 에 `REDUCER_PROMPT` + `build_reducer_prompt()` 추가 (assertions list + candidate answer → plain text final answer). `experiments/orchestrator.py:run_abc_chain` 에 `reducer_post_stage: bool = False` 옵션 + `_apply_reducer` 헬퍼 추가 (cycle 루프 *외부* post-stage). `experiments/exp13_reducer_role/run.py` 신규. Stage 2A/2B/2C + Exp11 c_caller / Exp12 extractor_pre_stage 보존 모두 적용. 분석 중 orchestrator bug 발견 + 즉시 fix (commit `cf057b6`, `len(fa)` int 입력 처리) |

**결과 (v3 채점, 150 trial):**

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|--------:|-----------:|--------:|
| baseline_abc | 75 | **0.7744** | 9+9 | 7.2 | 429s |
| **reducer_abc** | 75 | **0.7033** | 8+8 (+ 2 TypeError bug) | 7.0 | 414s |

**Δ(reducer − baseline) = −0.0711** (음수, Exp12 의 +0.0500 정반대). bug 제외 시 **−0.0533** (방향 불변). 통계 (n=15 paired): Wilcoxon p=0.180 / paired t p=0.204 (NOT SIGNIFICANT). Cohen's d = **−0.344** (with bug) / **−0.323** (bug 제외) — Exp12 의 +0.323 와 거울상. Bootstrap 95% CI Δ: [−0.176, +0.024].

**카테고리별 Δ(red−base)**:
- math: **−0.083** ⬇ (math-02 catastrophic 1.0→0.4, 2/5 = bug)
- **logic: −0.100** ⬇ (logic-02/04 catastrophic 강화)
- **synthesis: −0.107** ⬇ (5/5 task 음수, synthesis-04 −0.27 핵심)
- planning: +0.100 (n=2 작음, planning-02 saturation 안정)

**핵심 발견:**
1. **H12 ⚠ 미결 (실효적 기각)** — Δ −0.05~−0.07, Cohen d −0.32~−0.34, 카테고리 logic/math/synthesis 모두 음수, catastrophic 영역 4/4 음수 강화
2. **Exp12 ↔ Exp13 거울상** — 같은 모델 Role 분리/추가의 효과는 *위치 의존*: pre-stage = 양수 (+0.05), post-stage = 음수 (−0.05). 거의 동일 크기 |d|≈0.32, 정반대 방향
3. **메커니즘 = abstraction loss** — synthesis-04 case study: baseline 의 구조화된 분석 ("## Comprehensive Analysis ... Identification of Contradictions") 이 acc=1.0, reducer 의 단일 추정 압축 ("The best estimate is 270 individuals") 이 acc=0.33~0.67. Reducer prompt 의 "polish for clarity" + "do NOT change conclusion" 이 *다중 출처/다중 추정 → 단일 추정* 압축 유발 → keyword 매칭 실패
4. **길이가 아니라 content 가 핵심** — Reducer 평균 길이 281 chars > baseline 230 chars (오히려 김). 짧아져서가 아니라 *추상화* 손실로 keyword 누락
5. **error mode 안정성 미미** — NONE 66→67 (+1), no_final_answer 9→6. Reducer 가 미완성 답을 *완성* 시키는 효과는 있으나 정확도 손실이 압도
6. **orchestrator bug 발견** — `len(final_answer)` 가 int 입력에서 깨짐. 한 줄 fix (`isinstance` coercion). Tattoo schema 의 final_answer type 일관성 결함 (별도 plan 후보)

**framework-level 새 원칙 (H4 + H10 + H11 + H12 통합)**:

| Role 변경 유형 | 효과 | 메커니즘 |
|---------------|------|----------|
| Role *강화* (강한 모델 도입) | ❌ 음수 | self-discovery chain 단절 (Exp11) |
| Role *분리/추가* — pre-stage | ✅ 양수 | input 안정화 (Exp12) |
| Role *분리/추가* — **post-stage** | ❌ **음수** | **output abstraction loss (Exp13)** |

→ **외부화 framework 의 위치-효과 비대칭** 확정. 약한 모델의 chain 은 *건드리지 않을 때* 가장 풍부함. 외부 Role 의 "도움" 은 신중해야.

**Stage 5 다음 의제 (Exp14+):**
- 🎯 **Search Tool (Exp14 후보)** — Tool 축 신규. Role 축 3 회 검증 (강화/pre/post) 마감. H7 +18.3pp / H8 +23.3pp 강한 효과 + 결정성 보장 — 안전한 다음 단계
- Reducer prompt 강화 — 비추천 (위치 자체의 위험성이 prompt 보다 본질)
- Extractor + Reducer 조합 (Exp15 후보) — 비추천 (서로 상쇄)
- 다른 post-stage Role 변형 (Verifier 등) — 보류 (post-stage = 위험 패턴 일반화 가능성)

**상세 보고서:** `docs/reference/exp13-reducer-role-analysis-2026-05-05.md`
**결과 데이터:**
- `experiments/exp13_reducer_role/results/exp13_reducer_role_20260504_191208.json` (baseline_abc)
- `experiments/exp13_reducer_role/results/exp13_reducer_abc.json` (reducer)

**한계:**
- n=15 task paired — 통계 검정력 부족
- 5 trial 한계
- orchestrator bug 2 trial 영향 — Δ 방향 불변, 단 데이터 정합성 zero-impact 아님
- score_answer_v3 keyword 매칭 의존 — Reducer 의 *의미적* 정확성 측정 한계
- Tool 축 미검증 (math-04 양쪽 ~0)
- Tattoo schema final_answer type 불일치 — bug 의 근본 원인, 별도 plan 후보

---

### Exp14: Search Tool (Tool 축 — agent-active BM25 retrieval)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B/C 모두 Gemma 4 E4B (LM Studio Q8_0, 32K context) + agent 가 `search_chunks(query, top_k)` 능동 호출. 외부 API 0 (local BM25 인덱스, `bm25s` 패키지). |
| **언제 (When)** | 2026-05-05 (A-1 + A-2 + 진단 3 회) |
| **어디서 (Where)** | Windows + LM Studio (`http://192.168.1.179:1234`) |
| **무엇을 (What)** | H13 후보 — "ABC 에이전트가 cycle 중 *능동적* search_chunks 호출하여 long-context document 의 관련 chunk retrieve 시 baseline (full document in prompt) 대비 우수". 2 condition × 10 task (longctx_taskset) × 5 trial = **100 trial** + 진단 15 trial |
| **왜 (Why)** | Stage 5 Role 축 3 회 검증 (Exp11 강화 ❌ / Exp12 pre ✅ / Exp13 post ❌) 마감 후 Architect 권장 — Tool 축 신규 도입. 직전 두 음수 (Exp11/13) 비결정성 외부 vs 본 plan = **결정성 외부 도구** (BM25). H7/H8 의 +18~23pp 라인 연속 검증. Exp09 RAG arm (1-shot retrieve) vs 본 plan (agent-active iterative) 의 차별성 측정 |
| **어떻게 (How)** | `experiments/tools/bm25_tool.py` 의 기존 `bm25_retrieve` 재사용 + `SEARCH_TOOL_SCHEMA` (OpenAI tool-calling) 등록 + stop-words 추가 + `make_search_chunks_tool(corpus)` factory. `experiments/orchestrator.py:run_abc_chain` 에 `search_tool: bool = False` + `corpus: list[dict] | None = None` 옵션. closure 로 corpus 주입 (agent 는 corpus 존재 모름, tool 만 노출). Stage 2A/2B/2C + Exp11/12/13 hooks 모두 보존. **A-2 본 실행 후 tool_calls capture fix** (run.py 의 trial dict whitelist 누락) → 진단 15 trial 만 호출 데이터 capture |

**결과 (v3 채점, 100 trial 본 + 15 trial 진단):**

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|--------:|-----------:|--------:|
| baseline_abc_chunked | 50 | **0.9500** | 0+0 | 7.0 | 390s |
| **abc_search_tool** | 50 | **0.7300** | 7+7 | 7.1 | 235s (−40%) |

**Δ(search − baseline) = −0.2200** (음수, Stage 5 가장 큰 음수). 통계 (n=10 task paired): **Wilcoxon p=0.0312 ✅ / paired t p=0.0115 ✅** — **Stage 5 의 첫 통계적 유의 결과**. **Cohen's d = −1.000 large effect**. Bootstrap 95% CI Δ: **[−0.360, −0.100]** (0 미포함).

**hop_type 별 search mean_acc**:
- needle (1-hop, n=15): **0.800** (진단 5/5 모두 1 call + 5/5 정답)
- 2-hop (n=20): **0.675** (catastrophic large-2hop-01: base 1.0 → search 0.4)
- 3-hop (n=15): 0.733
- baseline 모든 hop_type 에서 1.000 (full document 라 hop count 무관)

**핵심 발견:**
1. **H13 ⚠ 미결 (실효적 기각, SIG)** — Stage 5 의 첫 *통계적 유의* 결과 (negative direction, |d|=1.0)
2. **Mechanism = insufficient retrieval iterations on multi-hop tasks** — large-2hop 진단 5 trial: [1, 2, 2, 3, 0] calls → [0, 1, 1, 1, 0] acc. agent 가 *hop count 만큼* iteration 결정 못함. 1 call 후 "document does not contain" 으로 단정 + 종료
3. **needle 은 정상** — 진단 v2 5/5 trial 모두 1 call + 5/5 정답. multi-hop 한정 음수
4. **baseline saturation** — 32K context 가 충분 → full document 가 prompt 에 들어가 multi-hop 자연. search 의 추가 가치 0 + iterative 결정 cost 만 발생
5. **Tool 축 sub-distinction 발견** — *deterministic computation* (calculator/linprog, H7/H8 +18~23pp) ≠ *agent-iterative retrieval* (H13 −22pp). 같은 "Tool 축" 의 sign 정반대
6. **Cost / time trade-off** — search 가 40% 빠름 (prompt 가벼움) but 22%p accuracy 손실. 32K 환경에서는 비합리적 trade-off
7. **A-2 50 trial tool_calls 미캡처** — run.py 의 trial dict whitelist 누락 (line 288), 진단 15 trial 만 capture. fix 적용 commit `a3b71af`

**Stage 5 framework-level 통합 원칙 (Exp11/12/13/14)**:

| 외부화 차원 | 효과 | 메커니즘 |
|------------|------|----------|
| Role 강화 (강한 모델 도입) | ❌ Δ=−0.08 NS | self-discovery chain 단절 (Exp11) |
| Role 분리/추가 — pre-stage | ✅ Δ=+0.05 NS | input 안정화 (Exp12) |
| Role 분리/추가 — post-stage | ❌ Δ=−0.05 NS | abstraction loss caveat (Exp13) |
| **Tool — agent-iterative retrieval** | ❌ **Δ=−0.22 SIG** | **insufficient hop iterations + premature termination + sufficient-context saturation (Exp14)** |

→ **외부화의 효과는 sign 자체가 *유형 / 위치 / iteration count* 의 복잡한 함수**. "more is better" 는 광범위하게 부정. paper-level claim 후보.

**Stage 6 다음 의제 (Exp15+):**
- 🎯 **Cross-model replication** (Llama 3.1 8B / Llama 3.3 70B / Qwen 2.5 7B Q4_K_M, Groq free + Local) — Stage 5 4 가설 일반화
- 🎯 **LLM-as-judge 보조 평가** (Groq GPT-OSS 120B) — H12 + H13 의 의미적 채점 (keyword scorer artifact 방어)
- Mandatory tool rules 변형 (Exp08b 패턴) — H13 mechanism 직접 fix 시도, 후순위
- Tool 축 다른 sub-type (Graph / Evidence / 강화된 Critic) — 보류

**상세 보고서:** `docs/reference/exp14-search-tool-analysis-2026-05-05.md`
**결과 데이터:**
- `experiments/exp14_search_tool/results/exp14_baseline_abc_chunked.json` (50 trial)
- `experiments/exp14_search_tool/results/exp14_search_tool_abc.json` (50 trial)
- `experiments/exp14_search_tool/results/diag_search_medium_needle_v2.json` (진단 needle, 5 trial fix 적용)
- `experiments/exp14_search_tool/results/diag_search_large_2hop.json` (진단 multi-hop, 5 trial)

**한계:**
- n=10 task paired (longctx_taskset 의 task 수, Exp11/12/13 의 n=15 보다 작음) — 단 |d|=1.0 large effect 라 유의 도달
- 5 trial 한계
- A-2 본 실행 50 trial 의 tool_calls 미캡처 — 진단 15 trial 만 사용
- score_answer_v3 keyword 매칭 — H12 와 동일 caveat (단답형 task 라 영향 작음)
- Tool axis 의 단일 sub-type — agent-active BM25 retrieval. 다른 sub-type 미검증
- baseline 의 sufficient context — 32K 환경. context-limited 환경 다를 수 있음
- tool_choice = "auto" — mandatory tool rules 적용 시 결과 변할 수 있음

---

### Exp15: Ephemeral Context Router (이중 기억 티어링 & 실증)

- **날짜:** 2026-06-28
- **목적:** 소형 로컬 LLM 환경에서 대용량 로그 주입 시 발생하는 Attention Breakdown 및 Latency 지연, 출력 구조(JSON) 붕괴를 방어하기 위해 SQLite(장기억) + Redis(휘발성 작업기억) 티어링 프레임워크와 하이브리드 오류 선제 슬라이서(ErrorBlocks)를 검증 및 실증.
- **가설:** **H15** (Context 외부화 가설) — ⚠ **예비 (n=1, 재검증 대기)**. ※ H14 는 Stage 6 cross-model 에 이미 사용되어 충돌하므로 H15 로 재부호화 (2026-06-28 정정).
- **실험 및 실증 설계:**
  - **대조 실험 (4개 Arm, arm당 n=1)**: Arm A (Stuffing), Arm B (Router-Basic), Arm C (ErrorBlocks-Only), Arm D (Hybrid). `max_cycles=5`.
  - **실물 프로젝트 실증**: [tunaCtx](file:///d:/privateProject/tunaCtx) (unittest) 단위 테스트 디버깅 및 [n100 Caddy](file:///C:/Users/사자/.ssh/config#L63-L67) (SSH 원격 로그) 분석.
- **결과 (검증 기준 보정 — 2026-06-28):**
  - **대조 실험은 arm당 1회 시행** (`exp15_ab_test_result.json`). 점수: Stuffing 100% / Router-Basic 100% / Hybrid 100% / ErrorBlocks-Only 0%. **라우터의 정확도 우위는 미확인** (3개 arm 동률), 관측된 차이는 단일 측정 latency 뿐 (Stuffing 332.3s → Hybrid 251.3s, −81s / −24%; "35%"는 보고서 표기, 단일 측정값). 4개 arm 모두 `cycles=5` (exp15 arm 중 조기 수렴 없음).
  - **JSON 무결성**: Hybrid arm 이 dict 구조 답변 산출 성공(1회). "100% 보존"은 n=1 관측.
  - **Fast-Forward 조기 수렴 (실재)**: C(Judge)가 CONVERGED 신호 시 순차 단계 전이 제약을 풀어 직접 전이 허용(`orchestrator.py:967`). `tunaCtx` 실증에서 3 cycle 수렴(Score 100%, 131.1s) 확인 — exp15 대조 arm 이 아니라 tunaCtx 실증에서 관측됨. "262s→131s 50% 단축"의 before 값(262s)은 저장된 결과 파일에 없음.
  - **n100 Caddy = mock fallback**: `caddy_n100_analysis_result.json` `is_fallback: true` — **실서버 미접속**, 스크립트가 생성한 mock 로그(IP `192.168.1.103` 등)를 다시 추출한 것. 실서버 연동은 미실증 (핸드오프 액션아이템 #3).
- **v1 판정 보류 사유 (2026-06-28)**: arm당 n=1, 점수 동률(라우터 우위 미입증), 실서버 미연동. → **Exp15 v2 (아래)에서 n=5 canonical 재검증으로 해소.**

**v1 산출물:**
- `experiments/run_tuna_real_test.py` (tunaCtx 연동 러너)
- `experiments/run_caddy_n100_analysis.py` (SSH n100 Caddy 분석기 — mock fallback)
- `experiments/exp15_context_router/results/{tuna_ctx_real_test,caddy_n100_analysis}_result.json` (Stage 8 에서 top-level results/ → exp15 하위로 이동)
- `docs/reference/stage7-context-router-analysis-2026-06-28.md` (보고서, 검증범위 보정본)

---

### Exp15 v2: Context Router Stress Test (canonical 재검증, H15 verdict)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | gemma4:e4b (Q4_K_M) — 지인 서버 RTX 5060 Ti 16GB, SSH 터널(`:2232`→ollama) 경유. 로컬 VRAM 무관. |
| **언제 (When)** | 2026-06-28 ~ 2026-06-29 |
| **어디서 (Where)** | Windows + 원격 Ollama 0.24 (네이티브 `/api/chat`, num_ctx 요청단위 통제 + tool-loop 내장 caller) |
| **무엇을 (What)** | H15 — "Context Router(Redis 핸들 + grep/read 도구)가 log-stuffing 대비 우수". 5 task × 4 arm(stuffing/router_basic/error_blocks_only/hybrid) × num_ctx{4096,32768} × n=5 = **200 ABC chains** (5.3h) |
| **왜 (Why)** | 원본 Exp15 v1 이 arm당 n=1 + 점수 동률 + num_ctx 미통제. 복제(n=5) + 입력 크기/컨텍스트 통제 + canonical 모델로 H15 정식 판정 |
| **어떻게 (How)** | side 브랜치 격리. `native_ollama_caller.py`(num_ctx 통제 + tool 실행 루프 — orchestrator model_caller 경로의 tool 미실행 한계 우회) + `run_v2.py`(matrix 드라이버, healthcheck/증분저장/resume). 채점 = final_answer + 최종 tattoo assertions 합집합(final_answer=None fragility 보정, 전 arm 동일). 공유 orchestrator/Stage6 코드 불변 |

**결과 (mean_score, n=5):**

| task (~tok) | ctx | stuffing | router | errorblk | hybrid |
|---|---|---|---|---|---|
| pytrace (0.1K, 통제) | 4096/32768 | **100/100%** | 60/70% | 100/60% | 100/70% |
| multihop (9K) | 4096/32768 | 0/**100%** | **87/100%** | 0/0% | 13/100% |
| caddy_5xx (11K) | 4096/32768 | 0/0% | 80/**100%** | 0/0% | 80/47% |
| rust_35k (16K) | 4096/32768 | 0/0% | **100**/60% | 0/60% | 0/20% |
| overflow (93K, 결정적) | 4096/32768 | 0/0% | **100/100%** | 0/60% | 0/80% |

**arm별 종합 mean**: router **0.857** > hybrid 0.510 > stuffing 0.300 ≈ error_blocks 0.280. **큰 로그(≥~10K)만**: router **0.908** vs stuffing 0.125 (Δ **+0.78**). **overflow(컨텍스트 초과)**: router **1.00** vs stuffing 0.00.

**핵심 발견:**
1. **H15 ⚠ 조건부 채택** — Context Router 는 모델 용량에 근접/초과하는 큰 로그(≥~10K tok)에서 stuffing 대비 견고 우위, **로그가 컨텍스트를 초과하면 유일하게 작동**(overflow 100% vs 0%).
2. **작은 로그에선 손해** — pytrace(0.1K): stuffing 1.00 > router 0.65. 도구 왕복이 noise. → 라우터는 **입력이 클 때만** 유효.
3. **num_ctx artifact 는 부분적** — multihop 만 32K서 stuffing 0→100% 회복(순수 artifact). **rust/caddy/overflow 는 32K서도 stuffing 0%** = 로그가 컨텍스트에 들어가도 소형 모델이 needle 을 못 찾는 **진짜 lost-in-the-middle**. 원본 "라우터 우위"는 일부 ctx 탓이지만 정확도 이점 자체는 실재.
4. **ErrorBlocks-Only brittle** — mean 0.28. ±25줄 슬라이싱이 "error" 키워드 의존 → caddy(문자열 없음)·multihop(원인이 에러서 멀리) 0%. 원본 "Arm C 0%" 재현·일반화(인출 없는 사전요약의 취약성).
5. **원본 latency 주장 철회** — Stage7 "35% 단축"은 n=1 + num_ctx=4096 artifact. v2 에서 stuffing 은 truncate 로 빠르되 오답.
6. **cross-model 합치** — ministral-3:8b(8B, 35KB)는 라우터 무이득(앞 사이드테스트). gemma4:e4b(~4B)는 16K도 버거워 이득 큼. → **router 효용 = f(모델 용량, 로그 크기)**.

**의의:** Context 외부화(H15)는 4축을 넘는 5번째 축 후보로 **조건부 입증**. 단 "만능"이 아니라 **입력 크기 의존** — 작은 입력엔 stuffing 이 낫고, 큰/초과 입력엔 라우터가 필수.

**상세 보고서:** `docs/reference/exp15-v2-context-router-analysis-2026-06-29.md`
**결과 데이터:** `experiments/exp15_context_router/results/exp15_v2_stress_gemma4_e4b.json` (200 chains) + `exp15_crossmodel_ministral_3_8b.json` (cross-model n=1)
**코드:** `experiments/exp15_context_router/{run_v2.py, native_ollama_caller.py, run_crossmodel_ministral.py}`

#### v3 부록 — gemma4 동일-패밀리 size sweep (e2b vs e4b, 2026-06-29)

ministral 제외(임시 대체였음), gemma4 본질에 맞춰 e2b(~2B)+e4b(~4B) 로 부하-용량 임계 측정 (1-needle × 5 size × {stuffing,router} × num_ctx 32768 × n=5) + v2 매트릭스 e2b 재실행.

- **S_e4b ≈ 8~19K tok**: stuffing 은 ~8K 까지(40~80%), 19K 부터 0% 붕괴. 그 너머 router 만 생존(60%, None-fragility 로 bimodal). → 동적 게이트: e4b 입력 >~10K tok 이면 router.
- **e2b 는 agent tool-use 미달**: v3 전 size router 0% (tool_rounds ~0.6). v2 arm 순위가 **e4b 와 정반대** — router 0.097(실패) < stuffing 0.287 < error_blocks 0.340 < hybrid 0.413. e2b 는 **읽기는 되나 도구를 못 몬다**(pytrace stuffing 100%, ErrorBlocks overflow 100%).
- **메커니즘 = push vs pull**: e4b(~4B)=agent-active Router(pull, 모델이 도구 호출), e2b(~2B)=deterministic ErrorBlocks(push, 오케스트레이터 추출·모델 읽기만). Exp14/Stage6 의 *"agent-retrieval 최소 용량 ~4B, M1=E4B 한정"* 을 gemma4 패밀리 내부에서 재현 — **H15(Context)와 H13(Tool) 이 같은 capability-floor 공유**(e2b tool-call 부재 = gemma3:4b M2-a 동형).
- **e2b 는 archived** (향후 push-기반 e2b 전용 실험 후보). 주력 = gemma4:e4b.
- 다음(Exp16 1순위): **오케스트레이터 출력 안정화** — `final_answer=None`(router 60% 의 정체, 틀린 답 아닌 침묵) 을 assertions 합성+retry 로 보완 → e4b router 실효 ~60%→~90%+ 목표. Orchestrator 축.

**v3 데이터:** `experiments/exp15_context_router/results/{exp15_v3_sweep_gemma4_e2b_e4b, exp15_v2_stress_gemma4_e2b}.json`

---

### Exp16: Orchestrator 출력 안정화 (None-fragility fix, H16)

| 항목 | 내용 |
|------|------|
| **누가/언제/어디서** | gemma4:e4b, 2026-06-29, 지인 서버 RTX 5060 Ti (SSH 터널) |
| **무엇을** | H16 — `final_answer=None` 시 체인 재실행(retry-on-None, 최대 K=2)이 router 큰 로그 실효 정답률을 ~90%+ 로 올리는가. router_basic × size{12K,25K,50K} × baseline vs stabilized × n=10 |
| **왜** | Exp15 v2/v3 에서 e4b router 의 0점은 틀린 답이 아니라 `final_answer=None`(침묵) — 재현성 문제. retry 가 메우는지 측정. Orchestrator(Python safety-net) 축 |
| **어떻게** | 드라이버 래퍼(`run_v16_stabilize.py`) — None 이면 재실행, 배포 가능 신호(gold 불필요). 공유 orchestrator 불변 |

**결과:** 12k 30→60%, 25k 20→50%, 50k 10→70% (lift +30~60pp), 평균 2.3~2.7 시도.

**핵심 발견:**
1. **H16 ⚠ 부분 채택** — retry 가 유의미한 lift(+30~60pp) 주지만 **~90% 미달, 50~70% 정체**.
2. **근본 원인 = per-attempt 성공률 자체가 낮음** — 큰 로그(12~50k)에서 시도당 ~10~30%. per-attempt 30%면 3시도 = 1−0.7³≈66% (관측 일치). 재시도는 증상 완화일 뿐.
3. **비용** ~2.5× call (평균 2.3~2.7 시도, cap 도달 잦음).
4. **변동 큼** — baseline 이 v3(60%)보다 낮게(10~30%) 나옴. 큰 로그 router 신뢰도의 run-to-run 변동 자체가 "재현성이 병목"을 뒷받침. 점추정 soft.

**함의:** 진짜 레버는 retry 가 아니라 **per-attempt 신뢰도 향상** — mandatory-tool 프롬프트(Exp08b 패턴, tool_neglect 0% 전례)/A-JSON 산출 강화/cycle·num_predict 상향. → **Exp16b** 후보.

**데이터:** `experiments/exp15_context_router/results/exp16_stabilize_gemma4_e4b.json` | **코드:** `run_v16_stabilize.py`

---

### Exp16b: mandatory-tool 프롬프트 (per-attempt 신뢰도, H16b)

| 항목 | 내용 |
|------|------|
| **누가/언제/어디서** | gemma4:e4b, 2026-06-30, 지인 서버 RTX 5060 Ti (SSH 터널) |
| **무엇을** | H16b — 라우터 task prompt 에 mandatory-tool 지시를 주면 per-attempt 성공률이 오르는가. router_basic × size{12K,25K,50K} × baseline vs mandatory × n=10 (1시도, retry 없음) |
| **왜** | Exp16 에서 retry 만으론 정체 — per-attempt(원인)를 고친다. Exp08b 의 mandatory-tool rules(tool_neglect 0% 전례)를 라우터 prompt prefix 로 각색. Orchestrator 축 |
| **어떻게** | mandatory 4규칙(반드시 grep 먼저 / 다양한 패턴 / "not found" 조기 단정 금지 / **매치 라인 파일·라인·모듈 그대로 전사**)을 driver task prompt 에만. 공유 system_prompt.py 불변 |

**결과 (per-attempt):** 12k 20→90% (tr 5.9→3.3), 25k 40→90% (6.6→2.2), 50k 20→70% (6.7→4.4). **평균 27%→83% (+57pp).**

**핵심 발견:**
1. **H16b ✅ 채택** — mandatory 프롬프트가 per-attempt 27%→83% (+57pp), 전 size +50~70pp 일관.
2. **메커니즘: tool_rounds 가 오히려 감소** — baseline 은 grep 을 *더*(~6회) 부르고도 27%. 실패는 **tool-neglect 아닌 전사/결론 누락**(찾은 라인을 final_answer 로 안 옮김, 또는 결론 못 내고 재검색). mandatory 규칙4("그대로 전사")가 결단력↑·재검색↓로 잡음.
3. **Exp16 재해석** — retry(증상) 가 아니라 **per-attempt 신뢰도(원인)**가 진짜 레버. H13 premature-termination·H16 None-fragility 의 공통 뿌리 = "찾은 걸 답으로 커밋 못 함".
4. **경로 완성** — per-attempt 83% + retry(K=2) ≈ 99% 기대 (Exp16c 로 실측 예정). H15 Context Router 가 "유망하지만 flaky" → "실용적"으로 승격.

**의의:** 라우터의 약점은 도구 *능력*이 아니라 도구를 *안정적으로 쓰고 결과를 커밋하게* 만드는 프롬프트. mandatory 프롬프트의 라우터 기본값 승격(공유 코드 변경)은 별도 plan 후보.

**데이터:** `experiments/exp15_context_router/results/exp16b_mandatory_gemma4_e4b.json` | **코드:** `run_v16b_mandatory.py`

---

### Exp16c: mandatory + retry 결합 (H16c)

mandatory 프롬프트(원인 fix, per-attempt↑) + retry-on-None(K=2) 결합. gemma4:e4b router, size{12K,25K,50K} × n=10.

**결과:** 전 size **100% (30/30)**, 평균 시도 12k 1.7 / 25k 1.3 / 50k 1.0.

**progression**: retry-only ~60%(Exp16, 증상) → mandatory-only 83%(Exp16b, 원인) → **결합 100%**(Exp16c).

**핵심 발견:**
1. **H16c ✅ 채택** — mandatory(per-attempt 83%) + retry(K=2) = 실효 ~100%. 기대(~99%) 부합·상회.
2. **낮은 시도 횟수** — mandatory 로 per-attempt 가 높아 retry 가 거의 불필요(평균 1.0~1.7). 비용 효율적.
3. **caveat** — n=10 합성·단일 needle·keyword 채점. 100%는 30 trial 표본(50k 1.0시도/100%는 Exp16b 70% 대비 쏠림). 참값 ~95~100%.

**의의:** **H15 Context Router 가 e4b 에서 실용 완성** — mandatory 프롬프트 + retry 로 큰 로그(컨텍스트 초과 포함) 디버깅을 ~안정적으로 처리. Stage 7 핵심 arc 종결(Exp15 발견 → v2 조건부 채택 → v3 capacity 분기 → Exp16 retry 정체 → Exp16b 원인규명 → Exp16c 완성).

**데이터:** `experiments/exp15_context_router/results/exp16c_combined_gemma4_e4b.json` | **코드:** `run_v16c_combined.py`

---

### Exp17: 복잡도 상한 (hard tasks, H17)

| 항목 | 내용 |
|------|------|
| **누가/언제/어디서** | gemma4:e4b, 2026-06-30, 지인 서버 RTX 5060 Ti (SSH 터널) |
| **무엇을** | e4b + router 가 trivial 1-needle 을 넘어 복잡 디버깅까지 가는지 + mandatory+retry 스택이 거기서도 이득인지. 4 hard task(multihop2/multihop3/multineedle/distractor, ~23K tok) × {baseline, stack} × n=8, num_ctx=32768. 부분점수 채점 |
| **왜** | 지금까지 needle 은 한 줄에 3요소가 다 있어 grep 한 방이면 끝. 실제 디버깅(2-hop 상관, 3-hop 사슬, 다중 집계, 오답 판별)에서 e4b 의 *추론* 한계 측정 |
| **어떻게** | 신규 4 task 생성/채점. stack = mandatory 프롬프트 + retry-on-None(K=2). 공유 코드 불변 |

**결과:** baseline → stack — multihop2 75→71%, multihop3 92→83%, multineedle 100→100%, distractor 100→100%. **평균 92→89% (−3pp).**

**핵심 발견:**
1. **전반(스케일) ✅** — baseline 만으로 평균 92%. e4b+router 가 **2-hop 상관·3-hop 인과 사슬·다중 발견 집계·오답 유인 판별**까지 처리. "똑똑한 소형 모델이 외재화로 얼마나 큰 일?"의 긍정 근거.
2. **후반(mandatory 일반성) ❌** — stack 이 hard task 에선 neutral~약간 음수(−3pp). Exp16b 에서 +57pp 살리던 스택이 여기선 무효.
3. **이유** — Exp16b/c 의 lift 는 **큰 로그 1-needle 의 전사 누락** 실패 모드 전용 처방이었음. Exp17 은 로그가 작고(~23k) baseline 이 이미 높아(추론 완성도 한계, 0.67 = 2/3 키워드) mandatory 의 "여러 번 grep"이 noise 만 더함(stack tr 3.8-4.6 > base 1.5-3.5인데 정확도 안 오름).
4. **함의** — mandatory = 범용 부스터 아닌 **failure-mode-specific 처방**. "router 기본값 승격"은 무조건이 아니라 **입력 크기/실패 모드에 따른 적응적 적용**. 제멘토 주장 *"more structure is not monotonically better"* 의 또 다른 사례.

**caveat:** n=8(−3pp 노이즈 범위), 합성·단일 크기(~23k), 부분점수.

**데이터:** `experiments/exp15_context_router/results/exp17_hardtasks_gemma4_e4b.json` | **코드:** `run_v17_hardtasks.py`

---

### Exp18: repo-규모 추론 상한 (size invariance, H18)

| 항목 | 내용 |
|------|------|
| **누가/언제/어디서** | gemma4:e4b, 2026-06-30, 지인 서버 RTX 5060 Ti (SSH 터널) |
| **무엇을** | 컨텍스트(32K) 초과 repo-규모(50K~200K tok)에서 e4b+router 추론이 유지되나. multihop3/multineedle × {50K,100K,200K} × n=8, router + retry-on-None(K=2), mandatory off, needle 을 로그 전체 20/55/85% 분산 |
| **왜** | Exp17(~23K)에서 92%. router 가 필수인 repo-규모에서 추론 천장이 내려가는지 / router 가 size-invariant 인지 검증 |
| **어떻게** | `run_v18_reposcale.py`. 로그 Redis 보관·grep 필터(모델은 매치 라인만 봄). 공유 코드 불변. 터널 불안정으로 3회 분할 resume |

**결과:** multihop3 50K **75%** / 100K 92% / 200K **100%**. multineedle 50K/100K/200K 모두 **100%**.

**핵심 발견:**
1. **H18 ✅ 채택 — size↑ 저하 전무** (오히려 multihop3 75→92→100% 상승). ~245K tok(32K 컨텍스트의 **7.5배**)에서도 3-hop 인과 추적·3-way 집계 92~100%.
2. **메커니즘 = 인지 부하 O(1)** — 모델은 거대 로그가 아닌 grep 결과(작은 매치 라인)만 봄. needle 이 13,000줄에 흩어져도 추론 부하 일정 → router 가 **로그 크기를 모델 인지 부하에서 분리**.
3. **retry 분화** — multihop3 att~3(깊은 추론 None-fragility↑, retry 회복), multineedle att~1.2(첫 시도 집계 성공). 50K multihop3 75%(최저)는 size 아닌 None 변동(200K=100%).
4. **함의** — "똑똑한 소형(~4B) 모델 + router 로 repo-규모 디버깅"의 강한 입증. Stage 7 Context Router 라인 완결(Exp15 조건부 → 16b/c ~100% → 17 추론 → 18 repo-규모 무저하).

**caveat:** 합성 로그·grep-findable needle·부분점수·n=8. 추론은 인출 라인 대상(전체 245K 아님) — 그게 router 의 요점.

**데이터:** `experiments/exp15_context_router/results/exp18_reposcale_gemma4_e4b.json` | **코드:** `run_v18_reposcale.py`

---

### Exp19: 실데이터 검증 — n100 journald → boxie e4b router 진단

신규 가설 아님 — H15/H18(Context Router)의 **실데이터 검증** + Stage 7 v1 mock caddy(`is_fallback:true`)의 정직한 대체.

| 항목 | 내용 |
|------|------|
| **누가/언제/어디서** | 진단 모델 gemma4:e4b @ **boxie**(외부 GPU 서버 RTX 5060Ti), 진단 대상 **n100**(내부 장기운영 서버) 실 journald. 2026-06-30 |
| **무엇을** | n100 실 저널(7일, **34,528줄 / ~1.15M tok**)을 Windows 에서 SSH-pull → 로컬 Redis → boxie e4b 가 router+mandatory+retry 로 "반복 실패 서비스" 진단. n=5 |
| **왜** | Exp18(합성 245K)을 진짜 운영 로그로. mock caddy 대체 — 소형 모델이 다른 박스의 대형 실 로그를 router 로 진단 가능한지 |
| **어떻게** | `run_v19_n100_journald.py`. `ssh n100 'journalctl --since "7 days ago"'` pull. 공유 코드 불변 |

**결과:** scores [0.5,0.5,1.0,0.5,1.0], mean **0.7**, ~24.5분(retry 2.2×).

**핵심 발견:**
1. **실 진단 5/5 정확** — 모든 답변이 **certbot** 지목(`certbot.service` 반복 Failed to start), 타임스탬프 포함, ans5 는 root cause("certificate renewal — challenges failed / rate-limited")까지. **stuffing 불가(1.15M tok), router 만 가능.**
2. **0.7 = keyword-scorer artifact** — 채점이 literal "failed to start" 요구하나 모델이 "failing to renew"로 패러프레이즈 → 0.5 처리. 실 정확도는 5/5. H12/H13 의 scorer caveat 재현(의미 채점이면 ~100%).
3. **mock 대체 완성** — Stage 7 v1 의 n100 caddy mock(`is_fallback:true`)을 진짜 n100 journald 로 대체. 소형(~4B) 모델 + router 로 **실 운영 장애 진단** 입증.
4. **인프라 사실 (RTX 5060Ti, gemma4:e4b Q4_K_M)**: 생성 **~95 tok/s**, prefill **~1,620 tok/s**(Ollama 서버측 측정). → router 가 **prefill 비용을 로그 크기와 분리**: stuffing 이면 1.15M tok prefill ≈ ~12분/호출(+컨텍스트 초과), router 는 grep 결과만 prefill ≈ ~3초. Exp18 의 O(1) 를 tps 로 재확인.

**caveat:** keyword 채점(의미 채점 아님), n=5, 단일 needle(certbot), retry 2.2× 시간.

**데이터:** `experiments/exp15_context_router/results/exp19_n100_journald_gemma4_e4b.json` | **코드:** `run_v19_n100_journald.py`

---

### Stage 8 (운영): mandatory-tool 프롬프트 opt-in 편입

신규 가설 아님 — H16b/c 의 **운영화(productionization)**. 드라이버 3곳에 흩어진 mandatory 블록을 공유 코드의 opt-in 파라미터로 정식 편입 (안 A — caller-decides, 자동 게이트 아님).

- `system_prompt.MANDATORY_TOOL_RULES` 상수 (검증된 4규칙, source-of-truth) + `run_abc_chain(mandatory_tool_prompt=False)` 파라미터. True 시 error_blocks 직후 prompt 에 append.
- **불변식**: 기본 False → prompt/거동 byte-identical (회귀 게이트 `tests/test_mandatory_optin.py` 5/5 통과). param 경로 cloud 검증 2/3 (None-fragility 변동).
- **언제 켜나**: 큰 로그 1-needle 류 retrieval(전사 누락 실패 모드) ON / 추론 중심·작은 입력 OFF. **failure-mode-specific** (Exp17: hard task 에선 −3pp).
- 자동 (log-size) 게이트는 증거 부족으로 보류 (별도 plan). plan: `docs/plans/mandatory-tool-opt-in.md`. 커밋 `1066b82`(코드)/`fb56a7e`(테스트).

### Exp21: Facet 집계 도구 A/B — grep-only vs grep+facet (§18, H21)

| 항목 | 내용 |
|---|---|
| **무엇** | 결정론적 전수 집계 도구 `aggregate_context`(handle, pattern, group_by, top_n) — 16KB 라인덤프 대신 untruncated 그룹별 top-N 카운트 |
| **왜** | Exp20 진단: megalog grep-only 가 high-volume + 16KB 캡에서 실패. 절단 없는 집계가 정확도를 회복하는지 |
| **어떻게** | megalog test9ng 30d (~29.3M tok), e4b @ boxie, grep-only vs grep+facet(caller opt-in 주입, 글로벌 도구 불변), 2-task × n=5, max_cycles=8 |
| **누가/어디** | Architect 설계 + Sonnet 구현(task-01~03) + 에이전트 직접 실행(boxie 원격) |

**결과:**

| arm | task | non_null_rate | mean_score | facet_calls |
|---|---|---|---|---|
| grep_only | A 크래시루프 | 0.4 | 0.3 | — |
| grep_only | B 집계 | **1.0** | **0.0** | — |
| grep_facet | A 크래시루프 | 0.2 | 0.2 | 3 |
| grep_facet | B 집계 | **1.0** | **0.8** | 16 |

**핵심 발견:**
1. **facet 은 집계 task 에서 결정적** (task B score 0.0→0.8). grep_only 5/5 **confidently-wrong**: 전부 `174.138.8.10` 을 최다로 단정 — `grep_context('Failed password')` 가 5,093 매치를 16KB(시간순 앞 ~100여 줄)로 절단 → 그 윈도우에서 일찍 보인 IP 를 전역 최다로 오인. **일관된 동일 오답 = 캡의 체계적 아티팩트.** grep_facet 4/5 정답(`45.144.212.75`, `aggregate_context` 가 `truncated:False` 로 전수 카운트).
2. **단일-needle task(A)엔 무효** (0.3→0.2, facet 거의 미사용 3 calls). 단일 needle 은 grep 으로 찾히고 절단이 답 자체를 안 막음. 수렴은 양 arm 모두 확률적(0.4/0.2).
3. **non-null rate(1차 지표)가 task B 에서 무력** (양 arm 1.0) — grep_only 는 "finalize 는 하되 틀림". 진짜 신호는 **accuracy(score)**. 향후 finalization 과 accuracy 분리 측정 필요.
4. **"more structure ≠ monotonically better" 확인** — facet 은 failure-mode-specific(Exp17 mandatory 와 동형 패턴). 집계형(top-N by field) 진단에 한해 채택 가치.
5. **Exp20 진단 재평가**: 진단은 task A finalization=None 에 집착했으나, 전체 n=5 에서 task A finalization 은 확률적이고 facet 도 못 고친다. facet 의 진짜 가치는 task B 정확도(핵심 실패모드 = "16KB 캡 → confidently-wrong 집계").

**Stage 9 함의**: Tool 축 sub-distinction 추가 — deterministic computation(H7/H8 +) / agent-iterative retrieval(H13 −) / **facet aggregation(H21 집계 task 한정 +)**. 후속 = 도메인 facet 다종화(`list_failed_units` 등)는 집계 벤치에 한해 재고. 상세: `docs/reference/exp21-facet-ab-analysis-2026-06-30.md`. 결과: `experiments/exp15_context_router/results/exp21_facet_ab_gemma4_e4b.json`. 드라이버: `run_v21_facet_ab.py`. 커밋 task-01 `5202991`/task-02 `63d6c51`/task-03 `cdbcb6b`/결과 `6905ca5`.

### Exp22: Retrieval-discipline nudge opt-in 재검증 A/B (§19, H22)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B/C 전부 gemma4:e4b (boxie RTX 5060Ti, SSH 터널 11435), native ollama caller(num_ctx 32768, 내부 tool-loop) |
| **언제 (When)** | 2026-07-01 (~122분, 40 chain) |
| **어디서 (Where)** | Windows 드라이버 → boxie ollama(터널), Redis 메가로그 키 `ctx:test9ng_journal_30d:stdout`(111MB/1.1M줄/~29.3M tok) |
| **무엇을 (What)** | H22 후보 — "anti-give-up/narrow-query nudge 를 `run_abc_chain(retrieval_discipline_prompt)` opt-in 편입하면 under-query 조기포기 finalization 실패가 완화된다". 2 arm(control/discipline) × 2 task(A crashloop / B bruteforce) × n=10 = **40 chain** |
| **왜 (Why)** | Phase 0/micro 진단: `final_answer=None` 근본원인은 judge 아닌 상류 A 의 empty-tattoo(~50% chain assertion 0개), 메커니즘은 under-query+조기포기(Exp14 H13 재출현). 레버 A/B(n=6, task A, nudge 를 constraints 에 수동 주입)가 finalized 17%→67%(+50pp)로 유망 → **정식 opt-in 플래그 경로 + n↑ + task B 로 일반화 재검증** |
| **어떻게 (How)** | Stage 10 편입: `system_prompt.RETRIEVAL_DISCIPLINE_RULES`(레버 nudge 정형화) + `orchestrator.run_abc_chain(retrieval_discipline_prompt=False)` 독립 가드(mandatory 주입 직후, mandatory→discipline 순서). 기본 False → prompt byte-identical. 드라이버 `run_v22_retrieval_discipline.py`: 양 arm `mandatory_tool_prompt=True` 공통, discipline 플래그만 토글(수동 constraint 주입 아님). Stage 2A/2B/2C 인프라 보존 |

**결과 (finalization-rate A/B, 40 chain):**

| task | arm | n | finalized | empty_tattoo | correct |
|------|-----|--:|----------:|-------------:|--------:|
| A crashloop | control | 10 | **70%** | 30% | **60%** |
| A crashloop | discipline | 10 | 40% | 40% | 40% |
| B bruteforce | control | 10 | 70% | 20% | 0% |
| B bruteforce | discipline | 10 | 50% | 0% | 0% |

**Δ(discipline − control)**: task A finalized **−30pp** / correct **−20pp**, task B finalized −20pp / correct **+0pp**. (rate-기반 A/B, n=10 소표본, 통계 유의성 미검정.)

**레버 A/B(n=6, task A) 대비**: control finalized 17→**70%**, nudge/discipline 67→**40%**. 레버의 +50pp 는 재현되지 않고 **부호 역전**.

**핵심 발견:**
1. **H22 ⚠ 미결 (실효적 기각)** — 레버의 finalized +50pp 가 정식 플래그 경로 n=10 에서 미재현, 오히려 discipline 이 control 보다 낮음.
2. **control baseline 변동이 지배적** — 레버 control 17% → Exp22 control 70%. finalization 은 run-to-run 분산이 극심하고, 레버의 catastrophic control 은 소표본(n=6) 나쁜 draw 였을 개연성. → "고칠 문제"가 이번 run 엔 거의 없었음.
3. **discipline = neutral~harmful** — "cycle 종료 전 후보 assertion 1개 강제"가 **조기 오답 커밋**을 유발(task A correct 60→40). task B 는 empty_tattoo 를 20→0%로 없앴으나 correct 는 0% 유지 = 강제된 assertion 이 confidently-wrong IP(16KB 캡 아티팩트).
4. **task B 는 예측대로 discipline 영역 밖** — 집계 실패(16KB 캡→confidently-wrong)는 facet(H21) 영역이지 under-query nudge 영역이 아님. 양 arm correct 0%.
5. **경로 confound** — 레버는 nudge 를 `constraints` 리스트에 주입, 편입은 `prompt` 끝 append(위치·정형화 상이). 단 control 변동(17 vs 70)이 지배적이라 confound 만으로 설명 안 됨.

**Stage 10 함의:**
- ❌ retrieval-discipline nudge 채택 안 함 — 레버 미재현, 조기 오답 위험. opt-in 플래그는 인프라로 유지(기본 False, byte-identical, 회귀게이트 62 OK)하되 **켜기 비추천**, 롤백 X.
- 🎯 다음 = **finalization 자체의 run-to-run 분산** 을 새 진단 대상으로. 진짜 레버는 "특정 nudge"가 아니라 분산 축소(예: retry-on-None 재조명, per-attempt 신뢰도, a2a planner-executor)일 가능성.
- ⚠ 방법론 교훈: 단발 소표본 A/B(n=6)는 finalization 분산을 잡기엔 검정력 부족 — 신뢰성 레버는 n↑ + 정식 경로 재검증 필수. (Exp21 "non-null≠correct" 교훈의 신뢰성 렌즈 재확인.)

**상세 결과:** `experiments/exp15_context_router/diagnostics/v22_retrieval_discipline_result.json`. 드라이버: `run_v22_retrieval_discipline.py`. 커밋 편입 `f466d40`/게이트 `47db68e`/드라이버 `3d64823`/결과 `3a5a480`.

### 오케스트레이터 신뢰성 트랙 종결: finalization 분산 + retry K-sweep (§20)

Exp22(H22 미결)가 남긴 질문 — "control finalized 가 레버 17% ↔ Exp22 70% 로 왜 요동치나" — 을 두 진단으로 닫는다. **신규 가설 아님**(H16 retry-on-None 의 재검증/특성화). 공유 코드 무변경, `diagnostics/` 진단 스크립트.

**진단 1 — 분산 특성화 (`variance_diag.py`, control task A, 3 batch × n=10 = 30):**
- **pooled finalized = 57%** (Wilson95 [39%, 73%]). batch rates [70%, 60%, 40%].
- **dispersion(obs/exp batch-var) = 0.63 < 1** → under-dispersed = **체계적 batch/시간/서버 효과 없음.** 단일 분포 + per-chain 독립.
- → 레버 17%(n=6)·Exp22 70%(n=10)는 **둘 다 이 분포의 꼬리 draw.** "17% 문제"는 소표본 착시. judge_conv 60% ≈ finalized (phase0 재확인 — 신호 있으면 judge 수렴).

**진단 2 — retry K-sweep (`retry_capstone.py`, control task A, n=20, retry-on-None):**

| K | first-attempt | finalized after retry | 예측 1−(1−p)ᴷ |
|---|---|---|---|
| K=3 | 35% | **70%** (Wilson [48%,86%]) | 72.5% (p=.35) |
| K=5 | 50% | **95%** (Wilson [76%,99%]) | 96% (p=.50) |

- **pooled per-attempt (3 진단, n=70) = 49%.** 예측 finalized: K=1 49% / K=3 86% / **K=5 96%**. **실측 K=5 = 95% ≈ 예측 96%** → retry-on-None 이 binomial 산식대로 스케일함을 실증.
- correct = finalized (task A 는 finalize 하면 gohttpserver 정답).

**트랙 종결 결론:**
1. **"신뢰성 문제"의 실체 = per-attempt finalization ≈49%, run 마다 35~57% 고분산.** 체계적 결함 아님(dispersion 0.63), 특정 nudge 부재 아님(H22 narrow-query 반증).
2. **retry-on-None(H16)이 확인된 레버이고 예측 가능하게 스케일** — ≥90% robust 하려면 K≈5(실측 95%). Exp16 의 "retry ~90% 미달"은 낮은 K + per-attempt 저기저율 조합의 특정 조건이었고, K↑ 로 해소됨(단 비용 avg attempts↑).
3. 레버의 유령 +50pp(H22)와 Exp22 실패는 **모두 35~57% per-attempt 진폭**으로 설명. → 신뢰성 레버는 소표본 단발 A/B 로 판정 금물(n↑ 필수).
4. **durable 레버 2개**: (a) **retry K 상향** — 즉효, 튜닝만, 비용선형. (b) **per-attempt 신뢰도** — Exp16b(전사규칙 +57pp)류, 더 깊지만 어려움. a2a(planner-executor)는 (b)의 상위 후보.

**상세 결과:** `variance_diag_result.json` / `retry_capstone_result.json`(K=3) / `retry_capstone_k5_result.json`(K=5) — 모두 `experiments/exp15_context_router/diagnostics/`. 스크립트: `variance_diag.py` / `retry_capstone.py`.

### Exp23: list_failed_units facet 레버 — per-attempt retrieval_gap 우회 시도 (§21, H23)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A/B/C 전부 gemma4:e4b (boxie RTX 5060Ti, SSH 터널 11435), native ollama caller |
| **언제 (When)** | 2026-07-02 (~2 run, GPU 간헐 부하로 arm 순차 preempt → mandatory 단독 완주) |
| **어디서 (Where)** | Windows 드라이버 → boxie ollama(터널), Redis 메가로그 `ctx:test9ng_journal_30d:stdout`(111MB/1.1M줄) |
| **무엇을 (What)** | H23 후보 — "인자없는 preset 도구 `list_failed_units(handle)`가 per-attempt retrieval_gap 을 우회해 finalization 을 올린다". 3 arm(control/fu_offered/fu_mandatory) × task A(exp21a_crashloop) × single-attempt |
| **왜 (Why)** | per_attempt_diag(pooled n=9): per-attempt 실패 = **retrieval_gap**(모델이 넓은 `error` 만 반복 grep, gohttpserver 못 띄움), emission_gap 0. narrow-query nudge(H22) 반증 → "좁혀라" 대신 결정론적 도구로 실패 unit 직접 건넴 |
| **어떻게 (How)** | `context_tools.list_failed_units`(systemd 실패 신호 `Failed with result`/`Main process exited`/`start-limit` + `(\S+\.service)` 전수 집계, untruncated top-N, pattern formulate 불필요). FACET(H21) opt-in 패턴 복제 — `FAILED_UNITS_TOOL_*` 별도, 글로벌 `CONTEXT_TOOL_*` byte-identical. orchestrator 무변경. fu_mandatory 만 드라이버가 "먼저 호출" constraint 주입. `used_fu` = 도구 함수 per-trial 카운팅 래퍼 계측 |

**결과 (finalization-rate A/B, pooled 2 run):**

| arm | pooled n | finalized | correct | used_fu |
|-----|--------:|----------:|--------:|--------:|
| control | 30 | **47%** | ~43% | 0% |
| fu_offered | 26 | **46%** | ~40% | **~85%** |
| fu_mandatory | 17 | **53%** | ~53% | **~94%** |

**도구 검증**: `list_failed_units('ctx:test9ng_journal_30d:stdout')` → `gohttpserver.service` **505,848 failure_signals #1**(전체의 99.99%), truncated:false. 우회 자체는 완벽 성공.

**핵심 발견:**
1. **H23 ⚠ 미결 (실효적 기각)** — 세 arm finalized 47/46/53% 구별불가(전부 §20 per-attempt 분산대 35~57% 안). 도구가 retrieval 을 우회하고 85~94% 사용되는데도 finalization 무개선.
2. **binding constraint = retrieval 아니라 다운스트림** — 답(gohttpserver)을 쥐여줘도 per-attempt 절반은 실패. fu_mandatory 샘플 `used_fu=True asrt=0 cyc=8`(도구로 답 받고도 assertion 0개 emit·미finalize)가 직접 증거.
3. **per_attempt_diag 재해석** — 그 "emission_gap 0"(retrieved→항상 finalize)은 소표본(성공 2/2) 착시였고, 큰 표본선 retrieved→~절반만 finalize. retrieval_gap 은 실재하나 **finalization 실패의 일부일 뿐**, 나머지는 emit/converge stochasticity.
4. **H21 저사용 경고 미재현** — Exp21 task A 에서 모델이 facet 을 거의 안 썼으나, list_failed_units 는 offered arm 에서도 85% 사용("Call this FIRST" 설명이 salient). 그럼에도 무개선 = 사용 문제 아닌 다운스트림 문제.
5. **per-attempt 트랙 종결** — 프롬프트(H22 narrow-query)도, retrieval 도구(H23 list_failed_units)도 per-attempt 를 못 올린다. 남은 레버 = retry(§20, 검증됨)/per-attempt 근본은 아키텍처 전환(a2a).

**Stage 11 함의:**
- Tool 축 sub-distinction 갱신: deterministic computation(H7/H8+) / agent-iterative retrieval(H13−) / facet aggregation(H21 집계+) / **failed-unit preset(H23 − retrieval 우회하나 per-attempt 무개선)**. → "도구가 상류(retrieval)를 고쳐도 하류(finalization) ceiling 이 지배하면 무효" 실증.
- 도구 opt-in 은 인프라로 유지(글로벌 불변 byte-identical, 회귀게이트 66 OK)하되 켜기 비추천, 롤백 X.
- 다음 = pre-stage auto-inject(push, 결정 4 후속)도 같은 다운스트림 ceiling 에 막힐 개연 → per-attempt 근본은 a2a(planner-executor) 또는 retry 수용.

**상세 결과:** `v23_failed_units_result.json`(control+offered) / `v23_mandatory_only_result.json`(mandatory) — `experiments/exp15_context_router/diagnostics/`. 드라이버 `run_v23_failed_units_ab.py` + `run_v23_mandatory_only.py`. 커밋 도구 `e20b48a`/게이트 `c7c41c0`/드라이버 `5673e0c`/결과 `d29f862`.

### Exp24: a2a Planner→Executor proposer 분할 — per-attempt 트랙 종결 (§22, H24)

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | A(→Planner+Executor)/B/C 전부 gemma4:e4b (boxie), native ollama caller |
| **언제 (When)** | 2026-07-03 (~90분, 완주 — GPU 안정) |
| **어디서 (Where)** | Windows 드라이버 → boxie ollama(터널), Redis 메가로그 |
| **무엇을 (What)** | H24 후보 — "단일 A 를 Planner→Executor 스코프 분할하면 per-attempt overload 를 우회해 finalization/correct 가 오른다". 2 arm(control/a2a) × task A × single-attempt × n=15 |
| **왜 (Why)** | per-attempt 실패 = A 가 답 알아도 assertion 0개 emit(§21). **싼 falsification `scoped_emit_probe`(n=20)**: 답을 clean scoped 입력으로 handed 시 emit **100%**(broad 49% 대비) → 실패는 structural 아닌 **broad-context overload**. a2a 만이 probe 가 green-light 한 방향 |
| **어떻게 (How)** | `run_abc_chain(a2a_proposer=False)` opt-in — True 시 A-stage(run_loop)를 `_a2a_propose` 로 대체: (1) Planner(`build_a2a_planner_prompt`, 도구로 finding 텍스트 산출) (2) Executor(`build_a2a_executor_prompt`, finding 을 clean scoped 입력으로 도구 없이 emit = probe 조건). 기존 `extract_json_from_response`/`apply_llm_response`/`LoopLog` 재사용. B/C 무변경. 기본 False byte-identical(회귀게이트 71 OK) |

**결과 (finalization-rate A/B, n=15):**

| arm | finalized | correct | n_assertions 분포 |
|-----|----------:|--------:|-------------------|
| control (monolithic A) | **47%** | **47%** | {0:9, 2:6} |
| a2a (Planner→Executor) | **27%** | **13%** | {1:5, 2:4, 3:2, 5:2, 8:2} |

**Δ(a2a − control)**: finalized −20pp, **correct −33pp**. (n=15 소표본, rate-기반.)

**핵심 발견:**
1. **H24 ⚠ 미결 (실효적 기각)** — a2a 가 per-attempt 를 **악화**. Δcorrect −33pp.
2. **emit 문제는 실제로 해결됨** — a2a 의 **empty-tattoo 9→0**(control 은 15 중 9 chain 이 asrt=0). Executor 가 scoped_emit_probe 약속대로 안정 emit. probe 는 옳았다.
3. **그러나 실패가 Planner 로 이동** — correct 47%→13%. Planner 가 넓은 검색서 **틀린 finding** 뽑고 Executor 가 그걸 confidently-wrong assertion 으로 충실히 기록·수렴. **plan Risk 3(planner 실패=실패 이동) 실현.** monolithic A 는 emit 할 때 47% 정답, 분할 Planner 는 13% — 분할이 planning 충실도마저 악화(통합 추론의 coherence 상실).
4. **emit 은 진짜 병목이 아니었다** — 병목은 retrieval/planning 충실도. §21 이 "다운스트림 emit/converge ceiling" 이라 했으나, Exp24 가 정밀화: emit 은 고칠 수 있고(a2a) 실제 고쳤으나, **정답률의 병목은 finding 자체의 정확도**다.
5. **안전한 침묵 → confident-wrongness (가장 중요)** — control 의 53% 실패는 None(무해, 침묵). a2a 는 그 중 ~14%를 **finalized-but-wrong**(finalized 27% 중 correct 13%)으로 전환. **틀린 진단이 무진단보다 해롭다**(Exp21 grep_only 16KB-캡 confidently-wrong 과 동형 — gemento 반복 테마).

**Stage 12 함의 (per-attempt 트랙 최종 종결):**
- **3중 음성**: per-attempt finalization 은 프롬프트(H22 narrow-query)·retrieval 도구(H23 list_failed_units)·구조분할(H24 a2a) **모두로 안 오른다**. 
- **결론 = retry 수용** — per-attempt ≈47~49% 는 소형 모델의 대형 로그 단발 진단 상한이고, 신뢰성은 retry(§20, K=5→95% 검증)로 매입한다. "더 영리한 단발 구조" 추구는 중단.
- a2a_proposer opt-in 은 인프라로 유지(기본 False byte-identical)하되 켜기 비추천, 롤백 X.
- **caveat / future**: 본 결과는 MVP a2a(텍스트 planner, verification 없음) 한정. 구조화 planner + verifiable-diagnosis oracle(tunaRound a2a 교차문서 방향)은 미검증 — planner 충실도를 검증으로 보강하면 다를 수 있으나, 본 plan 범위 밖.

**상세 결과:** `v24_a2a_result.json` — `experiments/exp15_context_router/diagnostics/`. 드라이버 `run_v24_a2a_ab.py`. probe `scoped_emit_probe.py`. 커밋 코드 `e28cc03`/게이트 `dae21b1`/드라이버 `c90026d`/결과 `b073ed8`.

---

## 채점 시스템 변천

### v1 → v2 전환 (2026-04-15)

| 항목 | v1 (substring) | v2 (keyword-group) |
|------|----------------|-------------------|
| 방식 | expected 문자열이 응답에 포함되는지 | scoring_keywords 그룹의 핵심 값이 모두 포함되는지 |
| 문제점 | 긴 문장, 포맷 차이, 설명 삽입 → false negative | — |
| 도입 동기 | — | Exp06에서 채점 버전 간 비교 신뢰도 훼손 발견 |

**전체 재채점 결과:**

| 실험 | v1 | v2 | Δ |
|------|-----|-----|-----|
| Exp00 Baseline | 0.705 | 0.722 | +1.7% |
| Exp02 Multiloop | 0.369 | 0.438 | +6.9% |
| Exp04 ABC Pipeline | 0.607 | 0.583 | -2.3% |
| Exp05a Prompt Enhance | 0.636 | 0.583 | -5.2% |
| Exp045 Handoff | 0.649 | 0.900 | +25.1% |
| Exp06 Solo Budget | 0.663 | 0.967 | +30.3% |

#### v2 역행 근본 원인 (Phase 1 진단, 2026-04-30)

`scoring_diagnostic.py` 분석 결과 (24 trial 전수 검사):
- **역행 trial**: 6건, 전부 `synthesis-01` 태스크에 집중
- **역행 유형**: TYPE_C (v1 partial_overlap > 0이지만 v2 keyword group = 0)
- **원인**: `synthesis-01` keyword group `['provider a', 'only']`가 v1의 token-level partial 점수보다 엄격. 모델이 정답("Provider A가 기준 충족")을 내면서 "only" 없이 답하면 v2=0.0 but v1>0.
- **일반 결함 아님**: Exp00/02/045/06에서 v2 ≥ v1이므로 v2 scoring 함수 자체 문제가 아닌 특정 keyword group 설계 문제.
- **권고**: `synthesis-01` keyword를 `['provider a']`로 단순화하거나 `['only', 'provider a']`에서 'only' 제거 검토.

### v2 → v3 전환 (2026-04-29)

| 항목 | v2 (substring contains) | v3 (negative_patterns 보강) |
|------|-------------------------|----------------------------|
| 방식 | scoring_keywords 그룹 매칭 (substring) | v2 + task 별 `negative_patterns` 차단 + 옵션 `conclusion_required` |
| 문제점 | "no solution / contradiction" 류 결론 답을 정답으로 잡음 (logic-04 13/60 false positive) | — |
| 도입 동기 | — | Exp10 v2 final 의 logic-04 false positive 발견 |

**Exp10 v2 final 재채점 결과 (053939, 직전 canonical):**

| condition | v2 mean | v3 mean | Δ |
|-----------|--------:|--------:|--:|
| gemma_8loop | 0.820 | 0.781 | -0.039 |
| gemini_flash_1call | 0.619 | 0.591 | -0.028 |
| gemma_1loop | 0.413 | 0.413 | 0.000 |

→ v2 → v3 격차는 logic-04 한정 (다른 8 task 는 v2 == v3). 본 v3 patch 는 Exp10 만 적용. 다른 실험 (Exp00~09) 의 result JSON 에 logic-04 task 가 포함되지 않음 (정찰 grep 확인) — `score_answer_v3` 적용 시 변동 0 예상. 다른 task 의 false positive 발견 시 task 별 negative_patterns 보강 별도 plan.

**2026-04-30 Phase 1 후속 v3 재산정 (taskset patched):** Task 00 의 taskset 정정 (math-03 prompt 96→88 + r=s+2 / synthesis-04 keyword `[["reports"],["5"],["6"]]` / longctx-medium-2hop-02 expected `"500 horsepower (500 hp)"`) 후 `rescore_v3.py` 재실행 (`exp10_v3_rescored_20260430_152306.json`). 직전 canonical (053939) 대비 모든 condition Δ +0.0019, task-level 은 synthesis-04 단독 (3 condition × +0.017). math-03 변동 0 (v3 trial 답변이 새 정답에 매칭 안 됨), logic-04 변동 0 (negative_patterns 보존). condition mean |Δ| < 0.01 → README 본문 갱신 없음.

---

## 종합 발견: E4B 능력 프로파일

| 능력 | 가능 여부 | 근거 |
|------|----------|------|
| Assertion 읽기 (12개까지) | **가능** | Exp01 |
| 지시 따르기 (next_directive) | **가능** | Exp02 |
| 단계적 추론·답변 생성 | **가능** | Exp02 |
| 교차 검증 (비판 역할) | **가능 (80%)** | Exp035 |
| Phase 전이 자율 판단 (C 역할) | **가능 (100%)** | Exp04 |
| Phase 전이 자율 판단 (단독 E4B) | **불가** | Exp02 v1 |
| 자가 Assertion 검증 | **불가 (0%)** | Exp03 |
| Confidence 자가 보고 | **불가** | Exp03 |

### 확정된 아키텍처 원칙

```
A (E4B 제안자)  = 추론 실행기 (executor)
B (E4B 비판자)  = 교차 검증기 (cross-validator, 80% 감지)
C (E4B 판정자)  = 수렴 판단 + phase 전이 (100% 자율)
Python          = 안전장치만 (safety net, 0회 발동)
```

---

# Part 2 — Active Research

> 이 파트는 진행 중 가설, 열린 질문, 다음 실험 후보를 다룹니다. **계속 갱신됩니다**. 영문 번역은 설계상 두지 않습니다 — 종결되면 Part 1으로 이동합니다.

## 현재 상태 및 다음 단계

### 완료된 보조 작업
- [x] Scoring V2 채점 체계 구축 (2026-04-15)
- [x] Exp045 v2 재채점 (2026-04-15)
- [x] E4B API 전환: Ollama(`gemma4:e4b`, Q4_K_M) → llama.cpp(`gemma4-e4b`, Q8_0) (2026-04-21)
- [x] Exp07 Loop Saturation + Phase Prompt (288 시행, 2026-04-24)
- [x] Exp08 Math Tool-Use (40 시행, +18.3%p, math-04 0→80%, 2026-04-24)
- [x] taskset math-04 expected_answer 데이터 결함 정정 (2026-04-24, 커밋 `6c6f198`)
- [x] measure.py `--output` UTF-8 직접 기록 옵션 (Exp08 Task 01)
- [x] Exp08b Tool-Use Refinement (40 시행, +23.3%p, math-04 0→100%, tool_neglect 0%, calculator 100%, 2026-04-24)
- [x] Exp09 Long-Context Stress Test (90 시행, ABC 88% / RAG 85% / Solo 20%, Large 20K에서 ABC 100%, 2026-04-25)
- [x] `config.py:SAMPLING_PARAMS` 일원화 (2026-04-26, sampling-params-config-exp10 plan). `lmstudio_client.py` 가 sampling 명시 시작. 도입 전 LM Studio 기본값과 본 명시값 (`temperature=0.1`, `max_tokens=4096`) 차이로 Exp10 결과가 Exp00~09 과 미세한 차이 가능 — baseline 비교 시 본 시점 이전·이후 분리.

### 열린 질문
1. ~~**v2 역행 조사**~~ — **Phase 1 진단 완료** (2026-04-30). 근본 원인: **synthesis-01 한 태스크에 국한된 TYPE_C 역행** (6건/24 trial). `['provider a', 'only']` keyword group이 v1 partial_overlap보다 엄격해 발생. v2 일반적 결함 아님. 정책 결정: keyword group 재설계 또는 v3 전면 전환 검토 권고. 닫힘.
2. ~~**Solo 표본 확대**~~ — **Exp06 정합성 정리에서 해소** (2026-04-29). Solo = 45 trial (9 task × 5 trial), ABC와 동일. 표본 비대칭 아님. **H4 재검증은 확대 task set으로** — 현 9-task에서 Inconclusive. 닫힘.
3. **Backprop 개선** — 현재 4.2~9.5% → 목표 50%+
4. **Mixed Intelligence** — E4B × 2 + 대형 모델(9B+) Judge 조합 테스트
5. ~~**Tool neglect 패턴**~~ — **Exp08b에서 해결** (0% 달성). 닫힘.
6. ~~**Calculator `^` 혼동**~~ — **Exp08b에서 해결** (100% 성공). 닫힘.
7. ~~**컨텍스트 한계 직접 검증**~~ — **Exp09에서 정면 입증** (Solo 0% vs ABC 100% in Large 20K). 닫힘.
8. **문신 점유율 측정** — 루프 진행 시 문신이 context window를 차지하는 비율 추적 필요. Exp09 데이터로 사후 분석 가능 (chunk count × 평균 assertion count).
9. ~~**taskset expected_answer 전수 검증**~~ — **Phase 1 자동 검증 완료** (2026-04-30). `validate_taskset.py`로 12개 기본 + 10개 longctx = 22개 태스크 전수 검증. **19 PASS / 3 FAIL**: (1) math-03 총 좌석 수 불일치(기대 96, 답안 88) — 문제 텍스트 오류 가능성, (2) synthesis-04 keyword 'report 6'이 expected_answer의 복수형 "Reports 5 and 6"에 불포함, (3) longctx-medium-2hop-02 keyword '500 hp'이 expected_answer "500 horsepower"에 불포함. 3개 항목 별도 수정 필요. 닫힘.
10. **한국어 답변 v2 scoring** — Exp08 math-03에서 한국어 답변의 keyword 매칭 편차 관찰. 다국어 응답 채점 방침 결정 필요.
11. **미외부화 축 보강** — 현재 검증된 4축(Tattoo/Tool/Role/Orchestrator) 외 확장 후보: **Extractor**(원문→claim), **Reducer**(chunk→일일), **Search Tool**(BM25/vector — Exp09에서 RAG arm 일부 검증), **Graph Tool**(relation traversal), **Evidence Tool**(evidence_ref resolve — Exp09에서 부분 구현), **Critic Tool**(schema·citation 결정론적 검증). 자세한 목록은 [conceptFramework.md § 9](./conceptFramework.md) 참조.
12. **Exp08c 후보 — solve_linear_system Singular matrix 힌트** — Exp08b math-03에서 6회 관측. "데이터 inconsistent 가능성" 힌트를 에러 메시지에 추가하면 모델의 모순 판단을 가속할 수 있는지 실험.
13. **Exp10 후보 — Small Paradox 해결** — Exp09에서 ABC가 small에서 RAG 대비 약함 관측 (longctx-small-needle-01: ABC 0.33 vs RAG 1.00). chunk가 너무 작거나 적을 때 cycle iteration이 오버킬 가능성. 추가 small 태스크 확대 또는 chunk-count threshold 기반 single-pass 분기 검증.
14. **Exp10 후보 — 병렬 chunk 순회** — Gemini의 Exp09 핸드오프 제언. 현재 직렬 chunk 처리를 여러 어댑터 인스턴스가 병렬로 처리한 후 Tattoo merge하는 구조. ABC chunked의 시간 비용 절감 + multi-agent merge 패턴 실험.
15. ~~**Exp09 통계 신뢰도 보강**~~ — **Phase 1 통계 검정 완료** (2026-04-30). 5 trial × 10 task = 50 데이터포인트/arm. Paired t-test p=0.7976, Wilcoxon p=1.000, Bootstrap CI [−0.170, 0.210] (포함 0). **비유의 — H9b verdict "조건부 채택"→"미결"로 변경**. 3-hop(+20.0%p)에서만 차별성 잔존, Small Paradox(abc 0.40 vs rag 0.60) 확인. 닫힘.
16. **Evidence Hit Rate ↔ 정답률 비대칭** — Exp09 ABC 3-hop에서 hit 0.23인데 정답률 100%. gold_evidence_chunks 라벨링이 너무 엄격하거나, 모델이 검증 경로로 보완 추론 가능성. 별도 분석 필요.
13. **크로스 모델 재현** — Qwen 2.5 7B / Phi-4 / Llama 3.2 3B에서 4축 외부화 효과 재현 여부. 일반화 검증.
17. ~~**오케스트레이터 신뢰성 (finalization 확률성)**~~ — **종결 (2026-07-02, §20 + §21)**. 근본 = per-attempt finalization ≈49%(pooled n=70), run 마다 35~57% 고분산. 체계적 결함/시간효과 없음(dispersion 0.63), 특정 nudge 부재 아님(H22 narrow-query 반증). **레버 = retry-on-None(H16, 기존) — binomial 산식대로 스케일(K=5 실측 95%)**; ≥90% robust 하려면 K≈5. **per-attempt 근본 상향 시도 3건 모두 실패**: 프롬프트(H22 narrow-query nudge)·retrieval 도구(H23 list_failed_units, 85~94% 사용해도 무개선)·구조분할(H24 a2a Planner→Executor, emit 은 고쳤으나 실패를 Planner 로 이동시켜 correct 47→13% **악화**, §22). binding constraint 는 emit 도 retrieval 도 아닌 **finding 자체의 정확도**(소형 모델 대형 로그 단발 진단 상한). **최종 결론 = retry(§20 K=5→95%) 수용** — "더 영리한 단발 구조" 추구 중단. 구조화 planner+verification(a2a 심화)은 미검증 future. 신뢰성 레버는 소표본 단발 A/B 로 판정 금물. 닫힘.

---

*이 문서는 실험이 완료될 때마다 해당 섹션을 추가하여 증분 관리합니다.*
