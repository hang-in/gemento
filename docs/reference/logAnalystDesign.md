---
type: reference
status: draft
updated_at: 2026-07-03
---

# gemento 로그 분석 어시스턴트 — 아키텍처 설계 (방향 전환)

> per-attempt 신뢰성 트랙(§20~22, H22/H23/H24 3중 음성) 종결 후, gemento 의 가치 명제를
> "범용 자율 에이전트" 에서 **"로그 검색·집계 어시스턴트"** 로 재정의한다. 외재화의 강점
> (reach: 데이터 접근·계산)에 정렬하고 약점(judgment: 노이즈 속 판별)을 아키텍처로 벽 친다.

## 0. 핵심 명제 (증거 기반)

**외재화는 소형 모델의 reach 를 확장하나 judgment 를 확장하지 않는다.** 그러므로:
- judgment 가 필요한 부분(무엇이 실패인가 판별)은 **결정론적 추출기**(코드)로 우회한다.
- 소형 모델(e4b)은 **잘하는 일**(scoped 언어화, 라우팅)만 시킨다.
- 신뢰성(throughput)은 **retry** 로, 안전성은 **결정론 finding + 기권** 으로 산다.

### 근거 실험
| 발견 | 실험 | 수치 |
|---|---|---|
| Context Router = 로그 크기에 O(1) 추론부하 | H15/H18 | ~245K tok 92~100%, overflow router 1.0 vs stuffing 0.0 |
| 실 저널 진단 | Exp19 | certbot 5/5 |
| scoped emit 신뢰성 | scoped_emit_probe | 답 clean 주입 시 emit 100% |
| **결정론 finding → fail-safe** | **det_planner_probe** | **correct==finalized (33%), confident-wrong 0** |
| **fail-safe + retry 확증** | **Exp25 (det_planner_retry)** | **wrong 0% (n=30 누적), correct 67%@K=5, C-수렴이 처리량 병목** |
| retry binomial 스케일 | §20 | K=5 → 95% (단 per-attempt 기저에 의존) |
| **judgment(LLM planner)는 노이즈서 틀림** | Exp24 | a2a planner correct 13%, confident-wrong 14% |
| 모델 단독 집계는 confidently-wrong | H21 | grep_only 16KB캡 오답 5/5 |

**결정적 대비**: 결정론 finding(det_planner_probe) → 정답 아니면 침묵(fail-safe). LLM planner(Exp24) → 틀린 답 자신있게(confident-wrong). **confident-wrongness 의 근원 = LLM judgment in noise. 결정론 추출기가 그것을 제거한다.**

## 1. 아키텍처 (4 구성요소)

```
로그(임의 크기, Redis/파일)
   │
   ├─(1) 결정론적 추출기 배터리 ──→ 후보 finding 집합 (judgment 없이 빠짐없이)
   │        list_failed_units / top_error_classes / freq_anomaly / timeline_gap ...
   │
   ├─(2) clean executor (e4b) ──→ 각 finding 을 scoped 언어화 → assertion
   │        (scoped_emit_probe: clean 입력 → 100% emit)
   │
   ├─(3) retry-on-None ──→ C 수렴 실패(safe None)를 재시도로 매입
   │        (§20: K=5 → ~87~95%)
   │
   └─(4) 기권 층(abstain) ──→ 결정론 근거 없으면 "모른다" (confident-wrong 차단)
```

**핵심 성질**: (1)+(2) 는 정답 아니면 침묵(fail-safe), (3) 이 침묵을 정답으로 전환, (4) 가 근거 없는 확신을 막는다. **틀린 진단이 절대 안 나오는** 로그 트리아지.

## 2. "빠짐없이(exhaustive)" 의 정확한 의미

- ❌ 모든 줄 판독(모델이 GB 읽기) — O(1) 원리 위반, 소형 모델 불가.
- ✅ **결정론적으로 열거 가능한 실패 공간을 배터리로 전수 스캔** — 실패 unit·error class·빈도 이상·타임 공백 등을 추출기가 빠짐없이.
- 경계: 규칙으로 추출 안 되는 애매 진단은 못 함(judgment 벽) → 기권.

## 3. 스케일 (GB~TB)

- **모델 부하**: O(1) — 원리상 크기 무관(H18). 벽 아님.
- **도구 백엔드**: 현재 Redis 통짜 문자열 + Python splitlines/정규식 매 호출 재스캔 = 프로토타입. GB 실용엔 **ripgrep/인덱스/청크 스트리밍** 교체 필요(엔지니어링, 연구 아님).
- **시간**: 며칠 허용 시 추출기 배터리·retry 다수 → 커버리지·신뢰성↑. 단 judgment 상한은 시간 불변.

## 4. 실험 로드맵 (다음 Stage 후보)

1. ~~**Exp25 — 척추 확인**~~ — **완료(2026-07-03)**. 결정론 finding + retry K=5, n=15: **wrong 0%(fail-safe 확증, 누적 n=30)**, correct 67%@K=5. 예측 ~87% 미달 — first-attempt C-수렴 20% draw 라 K=5→67%(retry 산식 성립). **새 병목 = C(판정자) 수렴**: 정답 assertion 줘도 ~20-33%만 수렴 → 처리량은 K↑ 로 매입(K≈7-10 이면 ~90%). 결과 `det_planner_retry_result.json`.
2. ~~**Exp25b — C-수렴 병목 진단**~~ — **완료(2026-07-03)**. n=15 계측(공유코드 무변경).
   **핸드오프의 3개 가설 전부 반증**: (A) confidence 게이트는 코드에 **없음**(C 출력=converged/next_phase/reasoning). (B) termination 과엄격 아니라 정반대 — **under-gated**(답 없이 CONVERGED 허용). **진짜 원인 = premature CONVERGED**: C 가 DECOMPOSE/INVESTIGATE 에서 `next_phase="CONVERGED"` 로 **조기 월반**(orchestrator.py:1021 이 어느 phase서든 CONVERGED 직행 허용). B handoff 에 (주입한) 정답이 보이니 "수렴"으로 판정하지만 `final_answer` 는 A 가 SYNTHESIZE/VERIFY 에서만 emit → **답 쓰는 phase 스킵 → null 종료**. 비-finalized 9개 중 **8개(89%)** 가 이것, 1개만 productive-emit 실패. finalize된 6개는 전부 C 가 조기수렴 *안 한* chain(safety-limit 가 SYNTHESIZE까지 crawl→emit). **C 조기수렴이 처리량 원흉, fail-safe(wrong 0%)는 스킵 chain 이 None 반환이라 유지.** 결과 `exp25b_c_convergence_result.json`.
3. ~~**Exp25c — CONVERGED 게이팅**~~ — **완료(2026-07-03)**. orchestrator opt-in `converged_requires_answer`(off byte-identical): 답 없이 DECOMPOSE/INVESTIGATE→CONVERGED 월반을 SYNTHESIZE 로 redirect. A/B(n=15/arm, 동일 결정론 finding): **finalized 13%(off)→87%(on), reached_productive 20%→100%, wrong 0%(양 arm)**, correct Wilson95=(0.62,0.96). **게이트가 처리량 레버 확증 + fail-safe 보존**(confident-wrong 0 추가). 결과 `exp25c_converged_gate_ab_result.json`. **새 잔여 천장 = productive-no-emit**(SYNTHESIZE 도달했으나 A 가 emit 실패, on 실패 13% 전부) → A-emit 이슈(C 아님), 다음 레버 후보.
4. **Exp26 — 추출기 다종화 + 다실패모드**: list_failed_units 외 top_error_classes/freq_anomaly 등 + crashloop 아닌 task(brute-force, OOM, cert-expiry). fail-safe·커버리지 일반화.
5. **Exp27 — 기권 층**: 추출기 근거 없을 때 "모른다" 반환 정확도. confident-wrong 최종 차단.
6. **Exp28 — GB 백엔드**: ripgrep/인덱스 도구로 교체, 크기 O(1) 실증.
7. **(논문/제품)** 크로스모델 O(1) 재현(Qwen/Llama) → reach 명제 일반화.

## 5. 확신 수준 (정직)

- **높음**: Context Router O(1)(H15/H18 다회), scoped emit 100%, confident-wrong 근원=LLM judgment. **fail-safe(결정론 finding→정답 아니면 침묵, wrong 0%) — Exp25/25b/25c 반복 확증(누적 n≫30).** **처리량 레버 확증: premature CONVERGED(Exp25b, 원인) → CONVERGED 게이팅(Exp25c, A/B 13→87% & wrong 0 & prod 20→100%).**
- **중간→높음**: first-attempt 기저는 게이트 ON 시 ~80-87%. **잔여 천장 = productive-no-emit 진단 완료(Exp25d, n=25)**: SYNTHESIZE 도달 후 A 실패 chain 의 productive A 응답이 **100% `empty_final`**(final_answer 필드는 넣되 값이 빔 — 파싱실패·필드누락·오답 전무), **wrong_content 0**. = 순수 emit 노이즈(일부 GPU 경합 truncation) → **retry 가 값싸게 커버**(87%+K=3→~99.8%). "단발 A-stage 레버" 불필요(per-attempt 트랙 교훈 재확인). 결과 `exp25d_no_emit_result.json`.
- **미검증(설계 가정)**: 추출기 배터리 커버리지(단일 task/추출기), 기권 층, GB 백엔드, 크로스모델.

## 6. 비-목표 / 경계

- 범용 자율 진단 오라클(애매 판단) — 불가(judgment 벽).
- 모델 단독 집계/판별 — confidently-wrong(H21/Exp24). 반드시 결정론 추출기 경유.
- 단발 고정확 — C 수렴 stochastic ceiling(~33~47%). retry 로만 매입.

## 변경 이력
- 2026-07-03 draft: per-attempt 트랙(3중 음성) 종결 + det_planner_probe(fail-safe 발견) 후 방향을 로그 분석 어시스턴트로 재정의. 4-구성요소 아키텍처 + 실험 로드맵 초안.
- 2026-07-03 Exp25 반영: fail-safe 확증(wrong 0% @ n=30), 처리량 67%@K=5, 병목이 A-stage→**C-수렴**으로 이동. 로드맵에 Exp25b(C 병목 완화) 최우선 추가, 확신수준 갱신.
