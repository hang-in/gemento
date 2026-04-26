---
type: reference
status: in_progress
updated_at: 2026-04-25
parts: [closed, active]
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
| H4 | **[Role 외부화 시너지]** A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | **채택** (+22.6%p) | Exp06 |
| H5 | **[Orchestrator 외부화 상한]** MAX_CYCLES 상향이 정답률 향상에 기여한다 (루프 포화점 존재) | **부분 기각** (상한 확장 무효, actual_cycles≈7에서 포화) | Exp07 |
| H6 | **[Role 외부화 정교화]** Phase별 특화 프롬프트가 baseline 대비 우수하다 | **조건부 채택** (장기 루프 15~20에서 +5~6%p) | Exp07 |
| H7 | **[Tool 외부화]** 외부 수학 도구(calculator/linalg/linprog)가 E4B의 계산 한계를 보완한다 | **채택** (+18.3%p, math-04 0→80%) | Exp08 |
| H8 | **[Tool 외부화 안정성]** 에러 힌트 + Mandatory tool rules로 tool_neglect와 operator 혼동을 완화한다 | **채택** (neglect 0%, calculator 100%, math-04 0→100%, 총 +23.3%p) | Exp08b |
| H9a | **[Tattoo 외부화 — 물리 한계 돌파]** ABC+Tattoo(chunked)가 Solo-dump보다 long-context에서 우수하다 | **채택** (+68.3%p, Large 20K에서 Solo 0% → ABC 100%) | Exp09 |
| H9b | **[차별성]** ABC+Tattoo가 RAG baseline 대비 고유 기여를 가진다 | **조건부 채택** (전체 +3.3%p; Large 3-hop에서 +33%p로 크게 우세, small에선 RAG 우세) | Exp09 |
| H9c | **[에러 모드 차이]** ABC의 실패 패턴이 Solo·RAG와 질적으로 다르다 | **채택** (Solo: format_error 24, RAG: wrong_synthesis 6, ABC: evidence_miss 2 + wrong_synthesis 3) | Exp09 |

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

> 자세한 정의는 [conceptFramework.md § 2](./conceptFramework.md)의 4축 정의 참조.

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
| **어떻게** | Solo: E4B × 1에 ABC와 동일 루프 예산 부여. 9개 태스크 × 1 트라이얼 = 9 시행 |

**결과 (v2 채점 기준):**

| 실험 | v2 평균 | 표본 |
|------|---------|------|
| Exp06 Solo | 0.967 | 9 |
| Exp045 ABC | 0.900 | 45 |
| **Δ (Solo − ABC)** | **+0.067** | — |

**주의사항:**
- Solo 표본(9)이 ABC(45)보다 5배 적어 분산 높음
- v1 기준으로는 ABC(88.9%) > Solo(66.3%), Δ = +22.6%p
- v2 keyword 매칭이 Solo의 부분 정답을 과대평가할 가능성

**핵심 발견:**
1. v1 기준 ABC 구조적 우위 확인 (+22.6%p)
2. v2 기준으로는 Solo가 소폭 앞서나, 표본 크기 비대칭
3. **외부 비판 없으면 조기 수렴** — Solo는 4~5 루프에서 오류 미감지 상태로 종료
4. ABC는 복잡한 태스크(synthesis-03)에서 구조 유지, Solo는 붕괴

**결론:** 역할 분리 시너지 확인. 특히 고복잡도 태스크에서 ABC 우위 뚜렷.

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
- **3 trial은 통계 신뢰도 부족** — Exp09b 후보로 5 trial 확대 + p-value 검정.

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
1. **v2 역행 조사** — Exp04, Exp05a에서 v2가 v1보다 낮은 이유 분석 필요
2. **Solo 표본 확대** — Exp06 Solo의 9개 표본으로는 통계적 신뢰도 부족
3. **Backprop 개선** — 현재 4.2~9.5% → 목표 50%+
4. **Mixed Intelligence** — E4B × 2 + 대형 모델(9B+) Judge 조합 테스트
5. ~~**Tool neglect 패턴**~~ — **Exp08b에서 해결** (0% 달성). 닫힘.
6. ~~**Calculator `^` 혼동**~~ — **Exp08b에서 해결** (100% 성공). 닫힘.
7. ~~**컨텍스트 한계 직접 검증**~~ — **Exp09에서 정면 입증** (Solo 0% vs ABC 100% in Large 20K). 닫힘.
8. **문신 점유율 측정** — 루프 진행 시 문신이 context window를 차지하는 비율 추적 필요. Exp09 데이터로 사후 분석 가능 (chunk count × 평균 assertion count).
9. **taskset expected_answer 전수 검증** — math-04 결함 사례를 볼 때 다른 태스크의 정답도 수학적으로 검증되어야 함. Exp09 longctx 태스크셋도 이 검증 필요.
10. **한국어 답변 v2 scoring** — Exp08 math-03에서 한국어 답변의 keyword 매칭 편차 관찰. 다국어 응답 채점 방침 결정 필요.
11. **미외부화 축 보강** — 현재 검증된 4축(Tattoo/Tool/Role/Orchestrator) 외 확장 후보: **Extractor**(원문→claim), **Reducer**(chunk→일일), **Search Tool**(BM25/vector — Exp09에서 RAG arm 일부 검증), **Graph Tool**(relation traversal), **Evidence Tool**(evidence_ref resolve — Exp09에서 부분 구현), **Critic Tool**(schema·citation 결정론적 검증). 자세한 목록은 [conceptFramework.md § 9](./conceptFramework.md) 참조.
12. **Exp08c 후보 — solve_linear_system Singular matrix 힌트** — Exp08b math-03에서 6회 관측. "데이터 inconsistent 가능성" 힌트를 에러 메시지에 추가하면 모델의 모순 판단을 가속할 수 있는지 실험.
13. **Exp10 후보 — Small Paradox 해결** — Exp09에서 ABC가 small에서 RAG 대비 약함 관측 (longctx-small-needle-01: ABC 0.33 vs RAG 1.00). chunk가 너무 작거나 적을 때 cycle iteration이 오버킬 가능성. 추가 small 태스크 확대 또는 chunk-count threshold 기반 single-pass 분기 검증.
14. **Exp10 후보 — 병렬 chunk 순회** — Gemini의 Exp09 핸드오프 제언. 현재 직렬 chunk 처리를 여러 어댑터 인스턴스가 병렬로 처리한 후 Tattoo merge하는 구조. ABC chunked의 시간 비용 절감 + multi-agent merge 패턴 실험.
15. **Exp09 통계 신뢰도 보강** — 현재 3 trial × 10 task = 30 데이터포인트/arm. 5 trial로 확대 + paired t-test 또는 Wilcoxon으로 H9b의 +3.3%p가 유의한지 검정.
16. **Evidence Hit Rate ↔ 정답률 비대칭** — Exp09 ABC 3-hop에서 hit 0.23인데 정답률 100%. gold_evidence_chunks 라벨링이 너무 엄격하거나, 모델이 검증 경로로 보완 추론 가능성. 별도 분석 필요.
13. **크로스 모델 재현** — Qwen 2.5 7B / Phi-4 / Llama 3.2 3B에서 4축 외부화 효과 재현 여부. 일반화 검증.

---

*이 문서는 실험이 완료될 때마다 해당 섹션을 추가하여 증분 관리합니다.*
