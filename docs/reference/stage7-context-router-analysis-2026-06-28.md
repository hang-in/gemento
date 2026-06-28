# Stage 7: Ephemeral Context Router 및 실증 디버깅 결과 분석 보고서

- **작성일**: 2026-06-28
- **저자**: Gemento Research (hang-in/gemento)
- **대상 모델**: `google/gemma-3n-e4b-it` (effective 4B parameters, `gemma4:e4b`)
- **실증 타겟**: [tunaCtx](file:///d:/privateProject/tunaCtx) (pytest) 및 [n100 Caddy](file:///C:/Users/사자/.ssh/config#L63-L67) (SSH 원격 로그)

---

## 1. 초록 (Abstract)
소형 로컬 LLM(8B 이하) 환경에서 수십~수백 KB 단위의 대형 시스템 로그나 빌드 에러를 단일 컨텍스트 프롬프트에 직접 주입(Stuffing)하는 방식은 **주의력 붕괴(Attention Breakdown), 극심한 추론 지연(Latency), 지정된 구조적 JSON 출력 깨짐** 현상을 지속 유발합니다. 

본 연구는 이 문제를 완화하기 위해 **SQLite(장기 기억/재현용) + Redis(휘발성 작업기억/스풀용) 이중화 인지 메모리 티어링**을 설계하고, 컨텍스트 라우팅 도구(`read_context`/`grep_context`) 및 하위 오류 선제 슬라이서(`ErrorBlocks`)를 탑재한 **ExoMind (Gemento Ephemeral Context Router)** 하네스 아키텍처를 구현했습니다.

로컬 `gemma4:e4b` 모델을 이용한 **arm당 1회(n=1) 예비 대조 실험** 및 tunaCtx 실물 리포지토리 실증 결과, ExoMind 아키텍처가 단순 Stuffing 방식 대비 단일 측정 기준 **추론 지연을 단축**(332s→251s)하고 소형 모델의 **JSON 구조 답변을 산출**하면서 대용량 로그 분석을 수행할 수 있음을 *예비적으로* 확인했습니다.

> ⚠ **검증 범위 한계 (2026-06-28 보정)**: 본 보고서의 정량 수치는 **arm당 n=1 단일 시행** 결과입니다. 정확도 점수는 Stuffing/Router-Basic/Hybrid 모두 100% 동률이라 라우터의 *정확도* 우위는 미입증이며, 차이는 단일 측정 latency 뿐입니다(분산 없음). n100 Caddy 절은 실서버 미접속 **mock fallback**입니다. 따라서 가설 판정은 ✅ 채택이 아니라 ⚠ **예비(재검증 대기)**입니다. "35% 단축", "O(1) 복잡도", "100% 보존"은 단일 관측·개념 주장이며 n≥5 재실행으로 확정 필요.

---

## 2. 가설 및 검증 결과 (Hypothesis & Verdict)

### 📌 가설 H15 (Context 외부화 가설)
> ※ **H14 는 Stage 6 cross-model 가설에 이미 사용** — 본 Context 외부화 가설은 **H15** 로 재부호화 (2026-06-28 정정).

> **[가설]** 외부 메모리 버퍼(Redis)와 하이브리드 사전 슬라이싱(ErrorBlocks)을 활용하여 에이전트의 단기 작업기억을 제한(Context Routing)하면, 토큰 복잡도를 O(1) 수준으로 억제하고 주의력 붕괴를 예방하여 대용량 로그 분석 시 Stuffing 대비 높은 속도와 출력 무결성을 보장한다.

* **판정**: ⚠ **예비 (n=1)** → **Exp15 v2 (2026-06-29)에서 ⚠ 조건부 채택으로 확정**. 본 v1 보고서는 v2 가 supersede 합니다 → **`docs/reference/exp15-v2-context-router-analysis-2026-06-29.md` 참조.**
* **v2 결론 요약**: canonical gemma4:e4b, 5 task × 4 arm × num_ctx{4096,32768} × n=5. router 전체 mean 0.857 vs stuffing 0.300; **큰 로그(≥~10K) router 0.908 vs stuffing 0.125**; **overflow(컨텍스트 초과) router 1.00 vs stuffing 0.00 (유일 생존)**. 단 **작은 로그(0.1K)는 stuffing 1.00 > router 0.65 (overhead)** — 라우터는 입력 크기 의존. num_ctx artifact 부분적, ErrorBlocks brittle. 아래 v1 의 "latency 35% 단축"은 n=1+ctx artifact 로 **철회**.
* **v1 근거 및 한계 (참고)**: Exp15 v1 대조 실험(arm당 n=1)에서 Router/Hybrid 가 Stuffing 대비 latency 를 단축하고 JSON 구조 답변을 산출함을 관측. 단 정확도 점수는 3개 arm 100% 동률, tunaCtx 실증(Fast-Forward 3 cycle 수렴)은 실재, n100 Caddy 는 mock fallback.

---

## 3. 실험 설계 및 방법론 (Methodology)

본 연구에서는 4개 조건(Arm A/B/C/D)의 상호 대조 분석 체계를 수립했습니다:

1. **Arm A (Stuffing — 대조군)**:
   * 35KB 이상의 원본 Traceback 로그 전체를 매 루프마다 프롬프트 컨텍스트에 직접 쏟아 넣는 전통적인 단일 에이전트 및 RAG 모방 시나리오.
2. **Arm B (Router-Basic)**:
   * 로그는 Redis에 분리 보관하며, 에이전트가 `context_handles` 정보만을 전달받아 필요한 지점만 `read_context`/`grep_context` 도구로 부분 인출하여 분석하는 기본 라우터 시나리오.
3. **Arm C (ErrorBlocks-Only)**:
   * 도구 호출 권한을 거세하고, 오케스트레이터가 에러 키워드 주변부(±25줄)만 선제적으로 잘라내어 컨텍스트 프롬프트에 주입(요약)해 준 축소 요약본 제공 시나리오.
4. **Arm D (Hybrid — ExoMind 최종 진화형)**:
   * 오케스트레이터의 `ErrorBlocks` 사전 슬라이싱을 통해 에러 발생 구역을 선제 노출함과 동시에, 에이전트가 필요에 따라 세부 컨텍스트를 Redis로부터 유연하게 인출할 수 있도록 도구 권한을 이중 결합한 시나리오.

---

## 4. 정량적 실험 결과 (Quantitative Results)

`gemma4:e4b` (로컬) 모델과 `Ollama Cloud 120B (llm_judge)`를 채점기(Scorer v4)로 연동하여 진행한 A/B/C/D Cross-Comparison 최종 수치는 다음과 같습니다.

> ※ 아래는 **arm당 1회(n=1)** 측정값입니다. `cycles` 는 `exp15_ab_test_result.json` 기준 **4개 arm 모두 5** — exp15 대조 arm 중 조기 수렴한 arm 은 없습니다(초판의 "Arm B 조기 수렴" 표기는 데이터와 불일치하여 삭제). Fast-Forward 조기 수렴(3 cycle)은 §6.1 tunaCtx 실증에서만 관측됨.

| 실험 조건 (Arm) | 정답률 (Score) | 수행 시간 (Latency, n=1) | 최종 답변 형식 (Answer) | cycles |
| :--- | :---: | :---: | :--- | :---: |
| **Arm A (Stuffing)** | **100.0%** | 332.3s | String (성공) | 5 (max) |
| **Arm B (Router-Basic)** | **100.0%** | 270.3s | String (성공) | 5 (max) |
| **Arm C (ErrorBlocks-Only)** | 0.0% | 203.8s | None (실패) | 5 (max) |
| **Arm D (Hybrid)** | **100.0%** | 251.3s | JSON/Dict (성공) | 5 (max) |

### 📈 데이터 분석 및 의의
1. **속도 향상 (단일 측정, 조기 수렴 아님)**:
   * **Arm B (Router-Basic)**는 도구 규약 적용으로 Stuffing 대비 **62초 단축**(270.3s, n=1). 단 4개 arm 모두 cycles=5 로, Arm B 가 조기 수렴한 것은 아닙니다(초판 서술 정정).
   * **Arm D (Hybrid)**는 사전 요약본 + 도구 인출을 결합해 Stuffing 대비 **81초 단축**(251.3s, n=1, 단일 측정 −24%)하며 JSON/Dict 구조 답변을 산출했습니다. latency 는 n=1 측정으로 분산이 없어 일반화 불가.
2. **인지 차단의 위험성 입증 (Arm C)**:
   * 로그 정보 인출 권한이 차단된 **Arm C**의 경우, 모델이 모호한 오류 맥락에 대해 심층 지식 탐구를 수행할 수 없어 정답률 0%로 완전히 붕괴했습니다. 이는 **"인출 권한이 없는 텍스트 요약은 소형 모델의 오진율을 심각하게 높인다"**는 귀중한 설계 규칙을 실증합니다.

---

## 5. 실물 리포지토리 연동 실증 분석 (Real-world Validation)

### 5.1 [tunaCtx](file:///d:/privateProject/tunaCtx) pytest 디버깅 (로컬 프로젝트)
* **상황**: `tunaCtx` 에이전트 라우터 구동 단계에서 AttributeError가 발생하는 고의 실패 테스트 코드를 작성하여 빌드 실행.
* **실증 결과**: 에이전트 체인이 3 cycle 만에 실패를 유발한 유닛 테스트 명세(`test_routing_failure_none_config`), 발생 예외(`AttributeError`) 등의 핵심 단서 6가지(Assertion)를 100% 오류 없이 도출하는 데 성공하여 뇌의 탐색 기재가 완벽히 작동함을 증명했습니다.

### 5.2 [n100 Caddy](file:///C:/Users/사자/.ssh/config#L63-L67) SSH 원격 로그 진단 — ⚠ **Mock Fallback (실서버 미접속)**
* **상황**: ssh config를 자동 파싱해 n100 리눅스 서버에 접속하여 caddy access.log를 인출하도록 스크립트 실행.
* **실증 결과 (한계 명시)**: `caddy_n100_analysis_result.json` 의 `is_fallback: true` — **실제 n100 서버 로그에는 접속하지 못했고**(파일 부재/경로), 스크립트의 `generate_mock_caddy_log()` 가 생성한 **가상 로그**로 폴백했습니다. 따라서 추출된 IP(`192.168.1.103`)·URL(`/api/v2/payment/checkout`)은 스크립트가 심어둔 mock 값을 다시 읽은 **순환 검증**이며, 실서버 연동은 아직 미실증입니다. 의미 있는 것은 "예외 시 크래시 없이 폴백하는 회복 경로가 동작했다"는 점뿐입니다. 실 Caddy 로그 연동은 핸드오프 액션아이템 #3(절대경로 확인 후 재검증).

---

## 6. 한계점 및 향후 과제 (Limitations & Future Work)

### 6.1 오케스트레이터 상태 머신의 조기 수렴(Fast-Forward) 튜닝 완료
* **상황**: 초기 실증 테스트 중 C 에이전트(Judge)가 조기 수렴을 선언해 `next_phase: CONVERGED`를 보내도, 상태 기계의 강한 단계 규칙(`DECOMPOSE ➔ INVESTIGATE ➔ SYNTHESIZE`) 때문에 전이가 무시되어 무한 루프를 돌다 미수렴(None)되는 한계가 있었습니다.
* **보완 결과**: `next_phase == "CONVERGED"`를 예외적으로 즉각 승인하는 **조기 월반(Fast-Forward) 규칙**을 오케스트레이터 검증 함수에 반영했습니다. 그 결과, `tunaCtx` 실물 재테스트 시 에이전트 체인이 불필요한 루프를 스킵하고 **단 3 cycle 만에 정상 수렴(Status: SUCCESS, Score: 100%)**하여 조기 탈출에 성공했으며, 지연 시간이 `262.3초`에서 **`131.1초`로 50% 대폭 절감**되었습니다.

### 6.2 상용 제품(Production)을 위한 아키텍처 제언
* 실험 대조군인 **Arm A (Stuffing)**는 소형 모델의 Attention 붕괴를 학술적으로 대조하기 위한 장치일 뿐이므로, 실제 상용 제품(Production) 배포 시에는 Stuffing을 영구 제거하고 오직 **ExoMind (Redis Router + ErrorBlocks)** 단일 엔진으로만 파이프라인을 고정합니다.
* 이를 통해 **수백 MB ~ 수 GB급의 초대형 프로덕션 로그 파일 환경에서도 토큰 복잡도를 상수 $O(1)$ 수준으로 통제**하는 것을 목표로 합니다. (※ 현재까지의 실증은 35KB 합성 로그 1건 + tunaCtx Traceback 1건 규모이며, "항상 2KB 미만 / 비용 $0 수렴"은 설계 목표이지 측정된 보장값이 아닙니다 — 대용량 실로그 부하 테스트는 future work.)
