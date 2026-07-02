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
| retry binomial 스케일 | §20 | K=5 → 95% |
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

1. **Exp25 — 척추 확인**: 결정론 finding + retry(K=5). det_planner_probe 단발 33%/fail-safe 를 retry 로 확장 → correct ~87%+/wrong 0 실측 (fail-safe 성질 n↑ 재확인). *가장 값싼 첫 확인.*
2. **Exp26 — 추출기 다종화 + 다실패모드**: list_failed_units 외 top_error_classes/freq_anomaly 등 + crashloop 아닌 task(brute-force, OOM, cert-expiry). fail-safe·커버리지 일반화.
3. **Exp27 — 기권 층**: 추출기 근거 없을 때 "모른다" 반환 정확도. confident-wrong 최종 차단.
4. **Exp28 — GB 백엔드**: ripgrep/인덱스 도구로 교체, 크기 O(1) 실증.
5. **(논문/제품)** 크로스모델 O(1) 재현(Qwen/Llama) → reach 명제 일반화.

## 5. 확신 수준 (정직)

- **높음**: Context Router O(1)(H15/H18 다회), scoped emit 100%, confident-wrong 근원=LLM judgment.
- **중간(n=15 소표본)**: det_planner_probe 의 fail-safe(correct==finalized, 5/5) — Exp25 로 확인 필요.
- **미검증(설계 가정)**: 추출기 배터리 커버리지, 기권 층, GB 백엔드, 크로스모델.

## 6. 비-목표 / 경계

- 범용 자율 진단 오라클(애매 판단) — 불가(judgment 벽).
- 모델 단독 집계/판별 — confidently-wrong(H21/Exp24). 반드시 결정론 추출기 경유.
- 단발 고정확 — C 수렴 stochastic ceiling(~33~47%). retry 로만 매입.

## 변경 이력
- 2026-07-03 draft: per-attempt 트랙(3중 음성) 종결 + det_planner_probe(fail-safe 발견) 후 방향을 로그 분석 어시스턴트로 재정의. 4-구성요소 아키텍처 + 실험 로드맵 초안.
