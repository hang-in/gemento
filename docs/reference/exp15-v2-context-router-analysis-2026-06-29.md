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

## 6. 다음 후보
- 실 Caddy/프로덕션 로그 연동 1회 실증(Active).
- 부하-용량 임계 sweep: ministral-3:8b 에 컨텍스트 초과(>32K) 로그를 줘 "부하>용량 시 라우터 부활" 확인.
- LLM-as-judge 보조 채점으로 keyword artifact 방어.
