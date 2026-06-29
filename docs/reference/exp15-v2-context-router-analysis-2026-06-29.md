---
type: reference
status: done
updated_at: 2026-06-29
---

# Exp15 v2 — Context Router Stress Test 분석 보고서

- **작성일**: 2026-06-29
- **대상 모델**: `gemma4:e4b` (Q4_K_M, effective 4B) — 지인 서버 RTX 5060 Ti 16GB, SSH 터널(`:2232`→ollama) 경유
- **가설**: H15 (Context 외부화) — Context Router(Redis 핸들 + `grep_context`/`read_context` 도구)가 log-stuffing 대비 소형 LLM 의 정확도/안정성을 향상시킨다
- **결과 데이터**: `experiments/exp15_context_router/results/exp15_v2_stress_gemma4_e4b.json` (200 chains) + `exp15_crossmodel_ministral_3_8b.json` (cross-model)

---

## 1. 동기 — v1 의 한계

원본 Exp15 v1(2026-06-28)은 (a) **arm당 n=1**, (b) Stuffing/Router/Hybrid 점수 100% 동률(라우터 우위 미입증), (c) **num_ctx 미통제**, (d) n100 Caddy 는 mock fallback 이었다. 즉 H15 채택 근거가 부족했고 "latency 35% 단축"은 단일 측정값이었다. v2 는 이를 **복제(n=5) + 입력 크기/컨텍스트 통제 + canonical 모델**로 정식 판정한다.

## 2. 설계

- **요인**: 5 task × 4 arm × num_ctx{4096, 32768} × n=5 = **200 ABC chains** (실행 5.3h).
- **Arm**: stuffing(로그 통째 주입) / router_basic(핸들+도구) / error_blocks_only(±25줄 사전슬라이스, 도구 없음) / hybrid(둘 다).
- **Task**: pytrace(~0.1K tok, 통제군) / multihop(9K, 2-hop 상관) / caddy_5xx(11K) / rust_35k(16K) / overflow_60k(~93K, 컨텍스트 초과).
- **인프라**: side 브랜치 격리. `native_ollama_caller.py` 가 네이티브 `/api/chat` 으로 **num_ctx 를 요청 단위 통제**하고 **tool 실행 루프를 caller 내부에서 완결**한다(orchestrator 의 `model_caller` 경로가 tool_calls 를 실행하지 않는 한계 우회 — `orchestrator.py:521-528`). healthcheck/증분저장/resume 포함. 공유 orchestrator/Stage6 코드 불변.
- **채점**: final_answer ∪ 최종 tattoo assertions 합집합에 대한 keyword-group substring. E4B 의 `final_answer=None` fragility 를 모든 arm 에 동일 보정(검색된 needle 이 시스템 최종 상태 어디든 도달했는가를 측정).

## 3. 결과 (mean_score, n=5)

| task (~tok) | ctx | stuffing | router_basic | error_blocks_only | hybrid |
|---|---|:--:|:--:|:--:|:--:|
| pytrace (0.1K) | 4096 | **1.00** | 0.60 | 1.00 | 1.00 |
| pytrace (0.1K) | 32768 | **1.00** | 0.70 | 0.60 | 0.70 |
| multihop (9K) | 4096 | 0.00 | **0.87** | 0.00 | 0.13 |
| multihop (9K) | 32768 | **1.00** | **1.00** | 0.00 | **1.00** |
| caddy_5xx (11K) | 4096 | 0.00 | **0.80** | 0.00 | 0.80 |
| caddy_5xx (11K) | 32768 | 0.00 | **1.00** | 0.00 | 0.47 |
| rust_35k (16K) | 4096 | 0.00 | **1.00** | 0.00 | 0.00 |
| rust_35k (16K) | 32768 | 0.00 | 0.60 | 0.60 | 0.20 |
| overflow (93K) | 4096 | 0.00 | **1.00** | 0.00 | 0.00 |
| overflow (93K) | 32768 | 0.00 | **1.00** | 0.60 | 0.80 |

**arm별 종합 mean** (10 cell): router_basic **0.857** > hybrid 0.510 > stuffing 0.300 ≈ error_blocks_only 0.280.
**큰 로그만** (≥~9K, 8 cell): router_basic **0.908** vs stuffing 0.125 — **Δ +0.78**.
**overflow** (2 cell): router_basic **1.00** vs stuffing **0.00**.
**pytrace(통제)**: stuffing **1.00** vs router_basic 0.65.

## 4. 핵심 발견

1. **H15 ⚠ 조건부 채택.** Context Router 는 모델 용량에 근접/초과하는 큰 로그(≥~10K tok)에서 stuffing 대비 견고 우위(Δ+0.78)이며, **로그가 컨텍스트를 초과하면 유일하게 작동하는 arm**(overflow 1.00 vs 0.00, tool_rounds≈1 로 grep 한 번에 needle 인출).

2. **작은 로그에선 손해.** pytrace(0.1K): stuffing 1.00 > router 0.65. 로그가 trivially 작으면 도구 왕복이 실패 모드를 더한다. → 라우터는 **입력이 클 때만** 유효 (Exp14 H13 의 *sufficient-context saturation* 과 동형).

3. **num_ctx artifact 는 부분적.** stuffing 의 4096→32768 변화:
   - multihop: 0%→**100%** (순수 컨텍스트 크기 artifact — 9K 로그가 4K 에 안 들어갔을 뿐).
   - rust_35k / caddy / overflow: **32K 에서도 stuffing 0%**. rust(16K)·caddy(11K)는 32K 에 들어가는데도 못 찾음 = **진짜 lost-in-the-middle**(소형 모델 attention breakdown). overflow 는 93K>32K 라 truncate.
   - 결론: 원본 "라우터 우위"는 일부 num_ctx=4096 탓이지만, **정확도 이점 자체는 ≥~10K 로그에서 실재**.

4. **ErrorBlocks-Only brittle** (mean 0.28). ±25줄 슬라이싱이 리터럴 "error" 문자열에 의존 → caddy(5xx 라인에 "error" 없음)·multihop(원인 config 가 에러 라인서 멀리)에서 0%. 원본 v1 의 "Arm C 0% 붕괴"가 **재현·일반화**: 인출 권한 없는 사전요약은 키워드 운에 좌우된다.

5. **hybrid 불안정** (0~100%). 사전슬라이스 + 도구 결합이 때로 모델을 혼동(rust 32K 0.20, multihop 4K 0.13). router_basic 단독이 가장 신뢰성 높음.

6. **원본 latency 주장 철회.** v1 "35% 단축"은 n=1 + num_ctx=4096 artifact. v2 에서 stuffing 은 truncate 로 빠르되 오답(0%)이라 "빠름"이 무의미.

7. **cross-model 합치.** ministral-3:8b(8B)는 동일 35KB 로그(자기 용량 내)에서 라우터 무이득(별도 n=1 사이드테스트). gemma4:e4b(~4B)는 16K 도 버거워 이득 큼. → **router 효용 = f(모델 용량, 로그 크기)**: 모델이 작고 로그가 클수록 라우터가 유효, 로그가 컨텍스트를 초과하면 모델 무관 필수.

## 5. 의의 & 한계

**의의**: Context 외부화(H15)는 기존 4축(Tattoo/Tool/Role/Orchestrator)을 넘는 **5번째 축**으로 조건부 입증. 단 "만능 라우팅"이 아니라 **입력 크기 의존** — 이 경계 조건이 핵심 기여.

**한계**:
- 합성 로그(프로덕션 실로그 아님). 실 n100 Caddy 연동은 미완(Active 액션아이템).
- keyword-substring 채점 (의미 채점 아님). LLM-as-judge 보조 평가 future work.
- v2 매트릭스는 단일 소형 모델(gemma4:e4b). cross-model 은 ministral-3:8b n=1 뿐 — 중간 크기 모델의 부하-임계 sweep 미실시.
- n=5 (서술적, 유의성 검정 아님).
- hybrid arm 비특성화(0~100% 변동).

## 6. 부록 — Exp15 v3: 동일-패밀리 size sweep (gemma4 e2b vs e4b, 2026-06-29)

ministral 은 제외(임시 대체 모델이었음). gemento 본질(똑똑한 소형 gemma4 의 외재화 한계)에 맞춰 **gemma4:e2b(~2B) + gemma4:e4b(~4B)** 로 부하-용량 임계(S)를 측정. 1-needle 로그를 5 size(~1.5K/8K/19K/40K/80K tok)로 스케일, stuffing vs router_basic, num_ctx=32768 고정, n=5. + v2 전체 매트릭스를 e2b 에도 실행.

### S 임계 (v3, num_ctx=32768)

| size(~tok) | e4b stuffing | e4b router | e2b stuffing | e2b router |
|---|---|---|---|---|
| 1.5K | 40% | **100%** | 0% | 0% |
| 8K | 80% | 40% | 0% | 0% |
| 19K | **0%** | 60% | 0% | 0% |
| 40K | 0% | 60% | 0% | 0% |
| 80K | 0% | 60% | 0% | 0% |

- **e4b: stuffing 은 ~8K 까지 작동, 19K 부터 완전 붕괴 → S_e4b ≈ 8~19K tok.** 그 너머는 router 만 생존(60%). router 60% 는 품질 천장이 아니라 **None-fragility**(per-trial bimodal 0/1 — 답을 내면 3/3 완벽, 일부 trial 은 `final_answer=None`). 동적 게이트: e4b 는 입력 >~10K tok 이면 router 전환.
- **e2b: 전 size·양 arm 0%, router tool_rounds ~0.6.** ~2B 는 **agent tool-use 를 못 몬다**(도구를 거의 호출 안 함 + 답 None).

### e2b 전체 매트릭스 (v2) — arm 순위가 e4b 와 정반대

| arm 종합 mean | e4b | **e2b** |
|---|---|---|
| router_basic | 0.857 | **0.097** (실패) |
| hybrid | 0.510 | 0.413 (최선) |
| error_blocks_only | 0.280 | 0.340 |
| stuffing | 0.300 | 0.287 |

e2b 는 pytrace stuffing 100%, **error_blocks/hybrid 가 overflow(93K)에서도 100%**("File: src/auth/jwt.rs, Line: 1873, ExpiredSignature" 정확). 즉 **읽기는 되는데 도구를 못 몬다**.

### 결론 — 올바른 외재화 메커니즘은 모델 용량에 따라 갈린다 (push vs pull)

- **e4b(~4B)**: **agent-active Router (pull)** — 모델이 직접 grep/read 호출. S 너머에서 stuffing 압도.
- **e2b(~2B)**: **agent tool-use 능력 미달** → deterministic 사전 슬라이싱(**ErrorBlocks, push** — 오케스트레이터가 추출, 모델은 읽기만)이 최선. overflow 도 push 로 100%.

이는 Exp14/Stage6 의 *"agent-active retrieval 은 최소 용량(~4B) 필요, M1 measurable = Gemma 4 E4B 한정"* 발견을 **gemma4 패밀리 내부(e2b vs e4b)에서 재현** — H15(Context)와 H13(Tool agent-retrieval)이 **같은 capability-floor 메커니즘** 공유. e2b 의 tool-call 부재 = Stage6 gemma3:4b 의 M2-a 와 동형.

**e2b 는 archived (향후 e2b 전용 외재화 — push 기반 — 실험 후보). 주력 모델은 gemma4:e4b 로 고정.**

### v3/e2b 결과 데이터
- `experiments/exp15_context_router/results/exp15_v3_sweep_gemma4_e2b_e4b.json`
- `experiments/exp15_context_router/results/exp15_v2_stress_gemma4_e2b.json`
- 코드: `run_v3_sweep.py` + `run_v2.py`(model 인자화)

## 8. Exp16 — Orchestrator 출력 안정화 (retry-on-None, H16, 2026-06-29)

Exp15 의 e4b router 0점 trial = `final_answer=None`(침묵, 틀린 답 아님). retry 가 메우는지 측정.
gemma4:e4b, router_basic, size{12K,25K,50K}, num_ctx=32768, baseline(1시도) vs stabilized(≤3시도, retry-on-None), n=10.

| size | baseline | stabilized | lift | 평균 시도 |
|---|---|---|---|---|
| 12K | 30% | 60% | +30pp | 2.3 |
| 25K | 20% | 50% | +30pp | 2.4 |
| 50K | 10% | 70% | +60pp | 2.7 |

**H16 ⚠ 부분 채택.** retry 가 유의미한 lift(+30~60pp)를 주지만 **~90% 미달, 50~70% 정체**. 근본 원인은 큰 로그에서 **per-attempt 성공률 자체가 낮음(~10~30%)** — per-attempt 30%면 3시도 = 1−0.7³≈66%로 관측과 일치. retry 는 증상 완화. 비용 ~2.5× call. baseline 이 v3(60%)보다 낮게 나온 건 큰 로그 router 신뢰도의 run-to-run 변동(점추정 soft, 방향은 명확).

**함의:** 진짜 레버 = per-attempt 신뢰도 — mandatory-tool 프롬프트(Exp08b: tool_neglect 0% 전례)/A-JSON 산출 강화/cycle·num_predict 상향. → Exp16b.

**데이터:** `experiments/exp15_context_router/results/exp16_stabilize_gemma4_e4b.json`. **코드:** `run_v16_stabilize.py`.

## 10. Exp16b — mandatory-tool 프롬프트 (per-attempt 신뢰도, H16b, 2026-06-30)

Exp16 의 retry 정체 → per-attempt(원인)를 고친다. 라우터 task prompt 에 mandatory 4규칙(반드시 grep / 다양한 패턴 / 조기 단정 금지 / **매치 라인 3요소 그대로 전사**) 주입(driver only, Exp08b 각색). gemma4:e4b, router, size{12K,25K,50K}, num_ctx=32768, baseline vs mandatory, n=10, 1시도.

| size | baseline | mandatory | lift |
|---|---|---|---|
| 12K | 20% (tr 5.9) | **90%** (tr 3.3) | +70pp |
| 25K | 40% (tr 6.6) | **90%** (tr 2.2) | +50pp |
| 50K | 20% (tr 6.7) | **70%** (tr 4.4) | +50pp |
| **평균** | **27%** | **83%** | **+57pp** |

**H16b ✅ 채택.** 핵심 메커니즘: **mandatory 에서 tool_rounds 가 오히려 감소**(도구를 *덜* 부름). baseline 은 grep ~6회 부르고도 27% — 실패는 **tool-neglect 아닌 전사/결론 누락**(찾은 라인을 final_answer 로 안 옮기거나 결론 못 내고 재검색). 규칙4("그대로 전사")가 commit-to-answer 단계를 잡음. → Exp16 재해석: retry=증상, per-attempt 신뢰도(프롬프트)=원인. H13 premature-termination·H16 None-fragility 의 공통 뿌리 = "찾은 걸 답으로 커밋 못 함". per-attempt 83% + retry(K=2) ≈ 99% 기대(Exp16c). H15 Context Router 가 실용 단계로 승격.

**데이터:** `experiments/exp15_context_router/results/exp16b_mandatory_gemma4_e4b.json`. **코드:** `run_v16b_mandatory.py`.

## 11. 다음 후보
- **Exp16c (1순위) — mandatory + retry 결합**: per-attempt 83% + retry-on-None(K=2) → ~99% 실측 검증. ~1h.
- mandatory 프롬프트의 라우터 기본값 승격(공유 system_prompt.py 변경, 별도 plan).
- Exp17 — multi-hop/multi-needle/repo-규모 로그로 e4b+router 진짜 상한 측정.
- 실 Caddy/프로덕션 로그 연동(Active, mock→실서버).
- (보류) e2b 전용 push-기반 외재화 + LLM-as-judge 보조 채점.
