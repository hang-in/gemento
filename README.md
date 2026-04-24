# gemento (제멘토)

> **소형 LLM의 계산·추론 한계를, 외부 상태와 외부 도구로 뚫는다.**

제멘토(gemento)는 **Gemma 4 E4B**(~4.5B) 같은 소형 언어모델이 단일 추론으로 해결할 수 없는 복잡한 태스크를, **외부 구조(문신/Tattoo) + 역할 분리(A-B-C) + 외부 도구(tool-use)**의 세 축으로 확장할 수 있는지 체계적으로 검증하는 연구 프로젝트입니다. 2026-04-08 착수, 현재 9차 실험(Exp08b)까지 완료.

---

## 핵심 가설과 판정

| ID | 가설 | 판정 | 판정 실험 |
|----|------|------|----------|
| **H1** | 다단계 루프가 단일 추론보다 품질이 높다 | ✅ 채택 | Exp02 v2 (50%→94.4%) |
| **H2** | 오류가 루프를 거치며 증폭된다 | ❌ 기각 (대신 silent failure 발견) | Exp03 |
| **H3** | 교차 검증(역할 분리)이 오류를 감지할 수 있다 | ✅ 채택 (자가 0% → 교차 80%) | Exp035 |
| **H4** | A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ✅ 채택 (+22.6%p) | Exp06 |
| **H5** | MAX_CYCLES 상향이 정답률 향상에 기여한다 | ⚠️ 부분 기각 (포화점은 상한이 아니라 actual_cycles≈7) | Exp07 |
| **H6** | Phase별 특화 프롬프트가 baseline보다 우수하다 | ✅ 조건부 채택 (장기 루프에서 +5~6%p) | Exp07 |
| **H7** | 외부 수학 도구가 E4B의 계산 한계를 보완한다 | ✅ 채택 (+18.3%p, math-04 0→80%) | Exp08 |
| **H8** | 에러 피드백 + Prompt 강화로 tool neglect/오용이 감소한다 | 🔄 **Exp08b 실행 대기** | — |

---

## 핵심 개념 (3축)

### 1. 문신(Tattoo) — 외부 상태

소형 LLM은 컨텍스트·집중력 제약으로 다단계 추론을 한 번에 끝내지 못한다. **문신은 "다음 추론을 가능하게 하는 구조화된 외부 상태"**이다 (로그나 기억이 아님). 각 loop마다 모델은 fresh context로 호출되며, 이전 진행상황은 JSON 스키마로 보존된 문신을 통해서만 전달된다.

핵심 필드:
- `meta` — 태스크 식별자, 목표, 제약조건
- `phase` — `DECOMPOSE → INVESTIGATE → SYNTHESIZE → VERIFY → CONVERGED`
- `assertions` — 확정된 사실 (soft cap 8)
- `handoff_a2b`, `handoff_b2c` — 에이전트 간 정보 전달 규약
- `critique_log` — B의 판정 이력
- `next_directive` — 다음 loop가 수행할 지시

### 2. A-B-C 직렬 파이프라인 — 역할 분리

같은 E4B 모델 3개가 **서로 다른 역할 프롬프트**로 직렬 연결된다. Python 오케스트레이터는 안전장치만 담당한다.

| 역할 | 프롬프트 이름 | 기능 | 검증된 능력 |
|------|---------------|------|-------------|
| **A (Proposer)** | `SYSTEM_PROMPT` | 추론 실행, assertion 생성 | 단계적 추론 ✅ |
| **B (Critic)** | `CRITIC_PROMPT` | A의 assertion을 단위별 검증 | 교차 검증 80% ✅ |
| **C (Judge)** | `JUDGE_PROMPT` | B의 비판 수렴 여부 판단, phase 전이 결정 | 자율 phase 전이 100% ✅ |

> **주의**: A-B-C는 제멘토 내부의 역할명이며, tunaFlow의 워크플로우 역할(Architect/Developer/Reviewer)과는 **별개의 개념**이다.

**핵심 원칙**: "한 모델이 추론과 메타 판단(phase 전이, 자가 검증)을 동시에 수행하지 못한다. 역할 분리가 필수다." (Exp02 v1 → v2에서 입증)

### 3. 외부 도구(Tool-use) — 계산 한계 보완

구조적 계산 한계(LP 최적화, 선형계수 대수 등)는 루프 수나 프롬프트 강화로 돌파되지 않는다. OpenAI 호환 `tool_calls` 경로로 A에게 외부 도구를 제공한다.

| 도구 | 구현 | 용도 |
|------|------|------|
| `calculator(expression)` | Python AST 화이트리스트 eval | 사칙연산·거듭제곱·괄호 |
| `solve_linear_system(A, b)` | `numpy.linalg.solve` | n×n 연립방정식 |
| `linprog(c, A_ub, b_ub, bounds, ...)` | `scipy.optimize.linprog(method='highs')` | 선형계획법 최적화 |

도구는 **A에게만** 주입되어 역할 분리 원칙이 유지된다. B/C는 도구 없이 텍스트만으로 검증한다 (Exp08에서 +18.3%p, math-04 0→80% 돌파).

---

## 실험 여정

| 실험 | 주제 | 핵심 결과 |
|------|------|-----------|
| **Exp00** | 단일 추론 Baseline | 9/18 (50%) — 구조적 지원 필요성 확인 |
| **Exp01** | Assertion Cap | cap 12까지 JSON 파싱 100% — soft cap 8 타당성 |
| **Exp02** | Multi-loop (H1) | v1(모델 자율) 0% → v2(오케스트레이터 강제) 94.4% |
| **Exp03** | 오류 전파 (H2) | 자가 검증 0/15 — silent failure 발견 |
| **Exp035** | 교차 검증 게이트 (H3) | 12/15 (80%) 감지 — A-B-C 진행 근거 확보 |
| **Exp04** | A-B-C 파이프라인 (H4) | 수렴 100%, C 자율 phase 전이 30/30 |
| **Exp045** | Handoff Protocol | `prioritized_focus + constraints`로 18/18 (100%) |
| **Exp05b** | 고난도 태스크 확장 | 9 태스크 40/45 (88.9%), logic-02 유일 약점 |
| **Exp06** | Solo-Budget 비교 | ABC vs Solo — Scoring V2 도입으로 재측정 필요성 발견 |
| **Exp07** | Loop Saturation (H5, H6) | 288 trials, 포화점 actual_cycles≈7 (상한 아님) |
| **Exp08** | **Math Tool-Use (H7)** | **+18.3%p, math-04 0→80% 돌파** |
| **Exp08b** | Tool-Use Refinement (H8) | 🔄 실행 대기 — calculator `^` 혼동 + tool neglect 완화 |

### 주요 발견

- **모델 vs 구조**: 실험 2에서 동일 E4B를 "자율 phase 전이"로 돌리면 0%, Python 오케스트레이터가 강제하면 94.4%. 모델 지능이 아닌 **구조 설계**가 성능을 결정한다.
- **Silent failure**: 실험 3에서 corrupted assertion을 주입해도 모델이 confidence 1.0으로 무비판 수용. 자가 검증은 작동하지 않는다.
- **역할 분리의 본질적 효과**: 같은 E4B라도 "비판자 역할 프롬프트"를 주면 80% 오류 감지. 자가 0% → 교차 80%.
- **Exp07 포화점 재해석**: MAX_CYCLES를 8→20으로 올려도 실제 사용 cycle은 ~7에 고정. 포화는 상한이 아니라 C의 수렴 판정이 결정.
- **Exp08 math-04 0→80%**: Exp07에서 "50% 정체"로 보였던 것은 실제로는 **채점 데이터 결함(제약 위반 expected_answer)**에 의한 artifact. 정정 후 baseline은 0%였고, `linprog` 도구 주입으로 80%까지 상승.

---

## 아키텍처 구조

```
┌────────────────────────────────────────────────────────────┐
│ Python Orchestrator (safety net only)                      │
│  ├ MAX_CYCLES 상한                                          │
│  ├ Phase 강제 전이 (fallback)                               │
│  └ tool_calls loop (max_tool_rounds=5)                     │
└─────────────────┬──────────────────────────────────────────┘
                  │
        ┌─────────▼─────────┐    ┌──────────┐    ┌──────────┐
        │  A (Proposer)     │ ─→ │  B       │ ─→ │  C       │
        │  E4B Q8_0         │    │ (Critic) │    │ (Judge)  │
        │  + tools (math)   │    │  E4B     │    │  E4B     │
        └─────────┬─────────┘    └────┬─────┘    └────┬─────┘
                  │                   │                │
                  └───────────┬───────┴────────────────┘
                              ▼
                    ┌──────────────────┐
                    │  Tattoo (JSON)   │ ← 외부 상태 (fresh ctx 간 유일한 채널)
                    └──────────────────┘
```

---

## 기술 스택

- **모델**: Gemma 4 E4B (7.5B params, Q8_0 GGUF)
- **추론 엔진**: llama.cpp server (OpenAI-compatible `/v1/chat/completions`, `tool_calls` 지원)
- **서버 스펙**: n_ctx=8192×4 slots, flash-attn, 전체 GPU offload
- **언어**: Python 3.14 (venv 필수 — PEP 668)
- **런타임 의존성**: `httpx` (LLM 호출), `scipy`, `numpy` (Exp08+ 도구)

### 인프라 이력

| 시점 | 추론 엔진 | 양자화 | 실험 |
|------|-----------|--------|------|
| 2026-04-08 ~ 04-15 | Ollama `gemma4:e4b` | Q4_K_M (4.5GB) | Exp00 ~ Exp06 |
| 2026-04-21 ~ 현재 | llama.cpp `gemma4-e4b` | **Q8_0 (8.0GB)** | Exp07 이후 |

Q4_K_M → Q8_0 전환으로 정밀도 2배 향상. 과거 실험과의 **직접 비교 시 주의 필요**.

---

## 시작하기

### 1. 환경 준비

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
pip install httpx scipy numpy
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install httpx scipy numpy
```

### 2. 추론 서버

`experiments/config.py`의 `API_BASE_URL`을 llama.cpp 서버 주소로 설정. 로컬이면 `http://localhost:8080`, 원격이면 해당 endpoint.

```bash
# 서버 헬스 체크
curl -s $API_BASE_URL/v1/models
# 기대: {"object": "list", "data": [{"id": "gemma4-e4b", ...}]}
```

### 3. 실험 실행

```bash
cd experiments

# 사용 가능한 실험 목록
python run_experiment.py --help

# 예: Exp08 Math Tool-Use 실행
python run_experiment.py tool-use

# 결과 분석 (UTF-8 권장)
python measure.py "results/exp08_tool_use_*.json" --markdown --output results/exp08_report.md
```

모든 실험은 체크포인트 지원 — 중단 후 재실행 시 자동으로 이어간다 (`partial_*.json`).

### 4. Smoke test (Exp08+ 필수)

```bash
cd experiments
python tools/smoke_test.py
# 기대 종료: "SMOKE TEST PASSED: math-04 answer=..., tool_calls=..."
```

---

## 문서 맵

| 경로 | 내용 |
|------|------|
| `docs/reference/researchNotebook.md` | **메인 연구 노트** — 모든 실험의 6하원칙 기록 + 가설 판정 |
| `docs/reference/experimentDesign.md` | 초기 실험 설계서 |
| `docs/reference/experimentSummary.md` | 실험 서사적 요약 |
| `docs/reference/handoff-to-gemini-exp*.md` | 각 실험의 Gemini 핸드오프 |
| `docs/plans/` | 각 실험의 플랜·작업지시서·리뷰·결과 |
| `docs/prompts/YYYY-MM-DD/` | 타 에이전트 전달용 단일 프롬프트 |
| `experiments/schema.py` | Tattoo 스키마 (Assertion, Phase, Handoff*) |
| `experiments/system_prompt.py` | A / B / C 역할별 system prompt |
| `experiments/orchestrator.py` | `call_model` (tool_calls loop), `run_abc_chain` |
| `experiments/run_experiment.py` | 실험별 실행 함수 (`baseline`, `multiloop`, `abc-pipeline`, `handoff-protocol`, `loop-saturation`, `tool-use`, `tool-use-refined`) |
| `experiments/measure.py` | 채점(v1 substring, v2 keyword group) + 실험별 analyzer |
| `experiments/tools/math_tools.py` | calculator / solve_linear_system / linprog + OpenAI schema |

---

## 다음 단계

현재 열린 후보:

- **Exp08b** (대기): Tool-use 부작용 완화 (calculator `^` 혼동, tool neglect) — 40 runs 재측정, H8 판정 목표
- **Exp08c** (검토): `tool_choice="required"` 전략 실험
- **Exp09** (설계 필요): Long-context multi-hop QA — sliding_window(512)를 직접 스트레스하여 "외부 상태가 유효 attention을 확장하는가"를 직접 검증. 제멘토 원래 가설의 최종 증명.
- **taskset 전수 검증**: math-04 expected_answer 결함 사례를 계기로 다른 태스크 정답의 수학적 검증 필요.

자세한 로드맵은 `docs/reference/researchNotebook.md`의 "현재 상태 및 다음 단계" 참조.

---

## 라이선스 / 기여

개인 연구 프로젝트. 외부 기여 체계 없음.
