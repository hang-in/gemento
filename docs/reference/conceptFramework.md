---
type: reference
status: in_progress
updated_at: 2026-05-03
canonical: true
---

# 제멘토 개념 프레임 (Concept Framework)

> 제멘토는 소형 LLM의 내부 한계를 **체계적으로 외부화**하여 장기·다단계 작업을 가능하게 만드는 오케스트레이션 연구다.

---

## 0. 문서 위치

이 문서는 제멘토의 **canonical 개념 문서**다. Exp00~Exp08b까지 이어진 9차 실험이 공유하는 단일 원리를 정의하고, 4개의 외부화 축과 그 경계를 명시한다. 연구 노트([researchNotebook.md](./researchNotebook.md))의 가설 표는 이 프레임의 언어를 기준으로 재부호화된다.

---

## 1. 최상위 원리 — 외부화

제멘토의 설계 원리는 **"소형 LLM 내부 한계의 외부화"** 한 문장으로 요약된다.

소형 LLM(예: Gemma 4 E4B, 4.5B 파라미터)은 다음 능력이 대형 모델에 미치지 못한다:

- **컨텍스트 유지**: cross-cycle 상태 보존 불가
- **결정론적 계산**: 수치 연산·최적화에서 불안정
- **자가 검증**: 자신의 오류를 스스로 감지하지 못함 (Exp03: 0%)
- **메타 제어**: phase 전이·retry 판단의 자율적 결정이 불안정

제멘토는 이 한계를 **대형 모델로 교체하지 않고**, 각 능력을 외부 자원으로 대체한다. 이 원리는 네 개의 축으로 구체화된다.

---

## 2. 4축 외부화

| 축 | 외부화 대상 | 왜 외부화하는가 | 구현 예시 |
|----|-------------|----------------|-----------|
| **Tattoo** | 상태 (기억) | 소형 LLM은 컨텍스트 cross-cycle 유지 불가 | `experiments/schema.py:Tattoo` |
| **Tool** | 행동 (계산·검색·검증) | LP 최적화 등 결정론적 계산은 모델 내부에서 불안정 | `experiments/tools/math_tools.py` |
| **Role Agent** | 관점 (자가 vs 교차) | 자가 검증 0% (Exp03) → 역할 분리로 80% 회수 (Exp035) | `experiments/system_prompt.py:CRITIC_PROMPT` |
| **Orchestrator** | 메타 제어 (phase 전이·retry) | 자율 phase 전이 0% (Exp02 v1) → 외부 제어로 94.4% (Exp02 v2) | `experiments/orchestrator.py:run_abc_chain` + Judge Role |

### 2.1 Tattoo — 상태의 외부화

소형 LLM은 turn-by-turn 추론만 가능하다. 이전 cycle의 결론·판단·중간 상태를 다음 cycle에 전달하려면 **외부 구조체**에 기록해야 한다.

`experiments/schema.py`의 `Tattoo` dataclass는 다음 필드를 가진다: `meta`, `phase`, `assertions`, `handoff`, `critique_log`, `next_directive`. 매 cycle 모델은 fresh context에 이 JSON 하나만 주입받아 연속성을 유지한다. 컨텍스트 자체는 버려지고 **구조화된 요약만 남는다** — 이것이 상태 외부화의 핵심이다.

### 2.2 Tool — 행동의 외부화

수치 연산·LP 최적화·선형 방정식 풀이는 LLM 내부에서 불안정하다. 동일한 입력에 대해 다른 답을 반복한다.

`experiments/tools/math_tools.py`는 `calculator`, `solve_linear_system`, `linprog` 3종을 구현한다. Exp08에서 이 도구들이 A에게 주입되자 math-04 정답률이 0% → 80%로 상승했다. 모델이 "계산"을 수행하는 것이 아니라, **계산을 도구에 위임하고 그 결과를 추론에 사용**하는 구조다.

### 2.3 Role Agent — 관점의 외부화

같은 Gemma 4 E4B 모델이라도 prompt에 따라 Proposer(A), Critic(B), Judge(C)로 특화된다. `experiments/system_prompt.py`에는 `SYSTEM_PROMPT`(A), `CRITIC_PROMPT`(B), `JUDGE_PROMPT`(C) 세 개의 역할 프롬프트가 정의된다.

Exp03에서 단일 에이전트의 자가 오류 감지는 0%였다. Exp035에서 역할을 분리하자 교차 검증이 80%에 달했다. 같은 모델이 **다른 관점**을 외부에서 부여받아 자신이 쓴 내용을 비판할 수 있게 된다.

### 2.4 Orchestrator — 메타 제어의 외부화

"다음 phase로 넘어갈 시점인가", "retry가 필요한가", "수렴으로 보아도 되는가" 같은 메타 결정은 두 경로로 나뉜다 (§ 6에서 상세).

`experiments/orchestrator.py:run_abc_chain`의 Python 로직이 결정론적 안전장치를 담당하고, Judge Role(C)이 의미론적 진행 판단을 담당한다.

---

## 3. Memento 비유 — 제멘토 네이밍의 실제 유효성

영화 *Memento*(2000)의 주인공 Leonard는 단기 기억상실증에도 불구하고 외부 자원을 활용해 장기 목표를 추적한다. 제멘토의 4축 구조는 이 영화 요소와 일대일 대응된다.

| Memento 영화 요소 | 제멘토 대응 | 의미 |
|-------------------|-------------|------|
| 문신 (지워지지 않는 핵심) | **Tattoo (Structured State Imprint)** | 잊어선 안 되는 핵심 상태 |
| 폴라로이드 사진 | **evidence_ref (스냅샷 포인터)** | 특정 사실의 출처 |
| 메모 (임시 해석) | 압축 DB / 작업일지 (handoff_a2b 등) | 임시 요약과 해석 |
| 전화 (외부 정보 확인) | **Tool (Search/Compute/Evidence)** | 외부 정보 확인·계산 |
| 조연 인물 (다른 관점) | **Role Agent (B 비판자, C 판정자)** | 상호 검증 제공 |
| 자동차·장소 (실행 환경) | 파일시스템 / DB / API | 탐색·접근 |
| 반복 조사 (cycle) | **Orchestrator loop** | 상태 갱신하며 사건 재구성 |

영화와 달리 제멘토는 **각 요소를 명시적·구조화된 형태로 설계**한다 — 종이 문신이 아니라 JSON 스키마, 우연한 만남이 아니라 A-B-C 직렬 호출. 비유는 네이밍의 근거일 뿐, 제멘토의 동작 방식을 영화와 동일시하지 않는다.

---

## 4. Critic의 이중 구분

**Critic은 Tool과 Agent로 분리된다.** 판단 성격(결정론/비결정론)과 구현 방식(순수 함수/LLM 호출)이 다르다.

| | Critic Tool | Critic Agent (Role) |
|---|-------------|---------------------|
| 판단 성격 | **결정론적** 검증 | **비결정론적** 비판 |
| 예시 | JSON 스키마 검증, `evidence_ref` 존재 확인, citation resolve, AST 화이트리스트 | 논리 모순 감지, 근거 충분성 판단, 의미적 일관성, 누락 감지 |
| 구현 | 순수 함수 (Python) | LLM 호출 + system prompt 역할 지정 |
| 장단점 | 빠름·저비용·재현 가능, 단 의미론적 판단 불가 | 의미 판단 가능, 단 80% 한계 존재 (Exp035) |
| 현재 제멘토 구현 | 부분 (AST 화이트리스트 `experiments/tools/math_tools.py:_eval`) | 완전 (`experiments/system_prompt.py:CRITIC_PROMPT`, Exp035/Exp04에서 B 역할) |

### 4.1 구분 원칙

- **모든 가능한 입력에 대해 정해진 출력이 있는 판단은 Tool**. 예: JSON 스키마 합치 여부.
- **문맥에 따라 판단이 달라지는 것은 Agent**. 예: "이 논리가 충분한 근거인가".

두 경로는 **병렬 사용 가능**하다. 예: Critic Tool이 먼저 스키마 적합성을 검증한 뒤, Critic Agent가 의미적 모순을 판단.

---

## 5. Tattoo–Evidence Tool 결합 쌍

Tattoo는 **상태 자체뿐 아니라 환경 포인터**(evidence_ref)를 포함한다 — `Assertion.evidence_ref` 필드가 `experiments/schema.py:130` 에 이미 구현됨 (Optional[dict] schema-level pointer). Evidence Tool 은 이 포인터를 resolve / validate 하는 역할이며, citation resolver / validator 자체는 아직 미구현 (별도 후속 과제). 두 요소는 독립이 아니라 **결합 쌍**으로 설계되어야 한다.

### 5.1 결합 원리

- Tattoo의 `assertion.evidence_ref` 필드는 "이 주장의 출처는 어디인가"를 기록.
- Evidence Tool은 ref를 받아 raw text/chunk/turn을 반환.
- 둘이 동시에 설계되어야 Critic Tool/Agent가 "주장 vs 근거" 일치성을 검증 가능.

### 5.2 최소 예시 (가상 스키마)

```json
{
  "assertion_id": "a_012",
  "claim": "factory profit maximized at X=31, Y=10, Z=37",
  "confidence": 0.95,
  "evidence_ref": {
    "source_type": "tool_result",
    "tool_name": "linprog",
    "call_id": "tc_4f2a",
    "raw_key": "cycle_3.tool_calls[0]"
  }
}
```

Evidence Tool은 `raw_key="cycle_3.tool_calls[0]"`을 resolve하여 원본 tool_call 응답을 반환. Critic은 이 응답이 정말 claim을 뒷받침하는지 검증.

### 5.3 현재 구현 상태

- Tattoo 스키마: `experiments/schema.py`에 `assertions` 리스트와 `Assertion.evidence_ref: Optional[dict]` 필드 모두 구현됨 (line 130). 다만 Exp04~08b 는 evidence_ref 를 채우지 않고 암묵적으로 cycle_details 의 tool_calls 에 로그하는 방식이라, **schema-level pointer 는 구현, runtime population 은 부분적**.
- Evidence Tool: 현재 제멘토에는 공식 Evidence Tool / citation resolver / validator 가 없다 — 미구현.
- **미완 항목** — § 9에 후속 과제로 명시 (Evidence Tool / resolver / validator 구현, evidence_ref runtime population 일관화).

---

## 6. Orchestrator의 이중 구분

"Orchestrator"는 실제로 **두 가지 상이한 역할**의 합성어다. 혼동을 막기 위해 분리한다.

| | Python Orchestrator | Judge Role (C) |
|---|---------------------|----------------|
| 성격 | **결정론적** 안전장치 | **비결정론적** 메타 판단 |
| 담당 | `MAX_CYCLES` 상한, phase fallback gate, retry policy, schema validation | 현재 phase의 수렴 여부, 다음 phase 전이, accept/reject/retry/escalate |
| 구현 | `experiments/orchestrator.py:run_abc_chain`의 Python 로직 | `experiments/system_prompt.py:JUDGE_PROMPT` + C 호출 |
| 발동 빈도 (Exp04) | 안전장치 0회 | 30/30 자율 결정 |
| 교체 가능성 | 결정론적 → 다른 언어·플랫폼으로 이식 쉬움 | LLM 호출이라 교체 시 품질 회귀 검증 필요 |

### 6.1 왜 둘이어야 하는가

**Exp02 v1 → v2**가 이 구분의 직접 근거다. v1에서 phase 전이를 모델 자율에 맡겨 0% 실패, v2에서 Python 강제로 94.4%. 그런데 Exp04의 C Role이 "자율 phase 전이"를 100% 성공시키면서 **비결정론 경로도 가능함**을 입증했다.

결론: Python은 **실패 방지용 안전망**, C Role은 **의미론적 진행 결정자**. 서로 대체재가 아니라 보완재.

### 6.2 설계 시사점

- "Orchestrator를 완전히 LLM화할 수 있는가"라는 질문은 **틀렸다**. 두 종류의 판단이 섞여 있기 때문.
- Python 안전장치는 **남겨야 한다** — 모델이 무한 루프·malformed output에 빠질 때 개입.
- 의미론적 진행 결정은 **Judge Role에 완전 위임 가능** — Exp04가 입증.

---

## 7. 4축 통합 다이어그램

4축이 어떻게 소형 LLM의 내부 한계를 외부화하고 상호 연결되는지 나타낸다.

```
┌─────────────────────────────────────────────────────────────────┐
│                        소형 LLM (Gemma 4 E4B)                   │
│                                                                 │
│          내부 한계: 상태 휘발 / 계산 불안정 / 관점 고착 / 제어 취약   │
│                            │                                    │
│             외부화 (Externalization)                             │
│   ┌─────────┬──────────────┼─────────────┬──────────────┐       │
│   ▼         ▼              ▼             ▼              ▼       │
│ ┌──────┐ ┌──────┐    ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│ │      │ │      │    │          │  │  Role    │  │ Orches-  │  │
│ │Tattoo│ │ Tool │    │Evidence  │  │  Agents  │  │ trator   │  │
│ │(상태)│ │(행동)│    │ Tool(ref)│  │ A/B/C    │  │ Py+Judge │  │
│ └──┬───┘ └──┬───┘    └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│    │        │             │             │              │        │
│    └────────┴─────────────┴─────────────┴──────────────┘        │
│                                │                                │
│                                ▼                                │
│                   ┌────────────────────────┐                    │
│                   │    외부 환경             │                    │
│                   │ (파일시스템 / DB / API)  │                    │
│                   └────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘

흐름: Role Agent(A)가 Tool을 호출 → 결과를 Tattoo에 기록
      Role Agent(B)가 Tattoo를 읽어 비판 → Critic Tool이 스키마 검증
      Judge Role(C)가 수렴 여부 판단 → Python Orchestrator가 안전장치
      Evidence Tool이 evidence_ref를 resolve → Critic이 근거 확인
```

---

## 8. 실험별 검증 축 매핑 (Exp00~Exp12)

| 실험 | 검증된 축 | 결과 요약 |
|------|-----------|-----------|
| Exp00 | — (baseline, 외부화 없음) | 9/18 (50%) — 외부화 부재 기준점 |
| Exp01 | Tattoo 용량 | assertion 12개까지 안정 (soft cap 8 타당성 확인) |
| Exp02 v1→v2 | **Orchestrator 외부화** | 자율 0% → Python 강제 94.4% |
| Exp03 | — (자가 검증 한계 확인) | silent failure 0/15 감지 — Role 외부화 필요성 입증 |
| Exp035 | **Role 외부화** | 자가 0% → 교차 80% |
| Exp04 | **Role 외부화 + Judge Role** | 100% 수렴, C 자율 phase 전이 30/30 |
| Exp045 | Tattoo 정교화 (Handoff Protocol) | 18/18 (100%) — `prioritized_focus + constraints` 필드 |
| Exp05b | Tattoo + Role (어려운 태스크) | synthesis-02 안정화 |
| Exp06 | Role 외부화 (Solo 대비) | 9-task subset Solo 우위, **Stage 2C 재검증으로 H4 ⚠ 조건부 채택** (synthesis +0.140) |
| Exp07 | Orchestrator 포화점 | actual_cycles ≈ 7 고정 (MAX_CYCLES 상한 ≠ 포화점) |
| Exp08 | **Tool 외부화** | +18.3%p, math-04 0%→80% |
| Exp08b | Tool 부작용 완화 | BitXor 힌트 + prompt 강화 — tool_neglect_rate 개선 |
| Exp09 | **Tattoo 물리 한계 돌파** | H9a Solo 0% → ABC 100% (Large 20K). H9b ⚠ 미결 (RAG 차별성). H9c 에러 모드 차이 |
| Exp10 | H1 추가 evidence + cost-aware | 1-loop 41.3% → 8-loop 78.3% (+37%p). Gemini Flash 1-call 대비 +19%p, 비용 $0 (4 fail JSON parse 등 인프라 이슈 disclosure) |
| **Stage 2C** (H4 재검증) | **Role 외부화 시너지 정밀화** | 15-task ablation: ABC > Solo-budget +0.044, **synthesis +0.140 회복 핵심**, n=15 검정력 한계, Cohen d=0.449 medium |
| **Exp11** (Mixed Intelligence) | **Role 강화 (H10)** | ⚠ 미결 (실효적 기각). Δ(Mixed Flash − baseline)=−0.081, Cohen d=−0.316 음수. **정반대 메커니즘 발견** — 강한 Judge 가 약한 모델 self-discovery 방해 (logic-02 case study) |
| **Exp12** (Extractor Role) | **Role 분리/추가 (H11)** | 진행 중 (2026-05-03~). Extractor pre-stage hook 으로 task prompt → claims/entities 사전 추출. 같은 Gemma 모델 (Exp11 정반대 메커니즘 회피) |

**관찰**: 4축 각각 최소 1개 실험으로 외부화 효과가 확인됨. Orchestrator·Role은 Exp02/Exp035부터, Tattoo는 Exp01/Exp045/Exp09 에서, Tool은 Exp08 에서 독립적으로 검증. **Role 축 정밀화** — Stage 2C (시너지 H4 ⚠ 조건부) → Exp11 (강화 H10 ⚠ 미결, 정반대 메커니즘) → Exp12 (분리/추가 H11 진행 중) 의 진화. **Mixed Intelligence 결과 (H10 미결) 가 framework 의 다음 방향을 결정** — Judge 강화 비추천, Role 분리 (Exp12 Extractor) 또는 다른 외부화 축 (Exp13 Search Tool) 우선.

---

## 9. 외부화 미완 영역 (향후 확장 후보)

현재 4축 외에 다음이 미검증 또는 미구현 상태다:

| 후보 | 현재 상태 | 필요한 실험/구현 |
|------|-----------|------------------|
| **Extractor Role** | **Exp12 진행 중** (2026-05-03~, Gemma E4B 동일 모델) | task prompt → claims/entities 사전 추출 → A→B→C chain 의 input prefix. H11 후보 |
| **Reducer Role** | 미구현 | 다수 chunk-level Tattoo → 일일/프로젝트 단위 요약. Exp14+ 후보 |
| **Search Tool** | 미구현 | 과거 세션·문서 retrieval (BM25/vector). Stage 5 의 SQLite ledger 와 직결 — **Exp13 후보 (Stage 5 다음)** |
| **Graph Tool** | 미구현 | entity/relation 다중 hop traversal. Exp14+ 후보 |
| **Critic Tool** | 부분 (AST 화이트리스트만) | JSON schema 검증, citation resolve 같은 구조적 검증기. Stage 2B FailureLabel enum 도입 (2026-04-30) — heuristic 분류만 |
| **Evidence Tool** | 미구현 | evidence_ref 스키마 + resolve API (§ 5와 연계) |
| **Large Model Tool** (Mixed Intelligence) | **Exp11 시도 → ⚠ 미결 (실효적 기각)**, 2026-05-03 | 강한 Judge C (Flash) 가 약한 A/B 보완 가설. 정반대 메커니즘 발견 — Judge 가 self-discovery 방해. **Sonnet/Opus escalation 경로 비추천** (Stage 5 의제 변경) |

**관찰** (Exp11 결과 반영): "강한 모델 escalation" (Mixed Intelligence) 가 약한 모델의 self-discovery chain 을 *방해* 가능 — Role 축 *강화* 가 아니라 *분리/추가* (Extractor 같은 신규 Role) 가 framework 의 자연 진화 방향. Exp12 (Extractor) 결과로 Stage 5 다음 외부화 축 우선순위 재검토.

---

## 10. 용어집

알파벳/가나다 순으로 정렬. 각 항목 1~3줄.

**Assertion** — Tattoo 내 하나의 주장 단위. `claim`, `confidence`, `evidence_ref`(schema-level 구현, runtime population 부분적) 필드를 가진다. `experiments/schema.py:Assertion`.

**Critic Agent** — 비결정론적 판단을 수행하는 LLM 역할. 논리 모순·근거 충분성을 평가. `experiments/system_prompt.py:CRITIC_PROMPT`. → § 4 참조.

**Critic Tool** — 결정론적 검증 함수. JSON 스키마 합치, AST 화이트리스트 등. 현재 `experiments/tools/math_tools.py:_eval`에 부분 구현. → § 4 참조.

**Evidence Tool** — Tattoo의 `evidence_ref` 포인터를 resolve하여 원문 근거를 반환하는 도구. 현재 미구현. → § 5 참조.

**evidence_ref** — Tattoo 내 assertion이 가리키는 출처 포인터. `source_type`, `tool_name`, `call_id`, `raw_key` 등으로 구성되는 스키마. `experiments/schema.py:130` 의 `Assertion.evidence_ref: Optional[dict]` 로 schema-level 구현됨. runtime population (실제 채움) 은 부분적, Evidence Tool / resolver / validator 는 미구현. → § 5 참조.

**Handoff Protocol** — Tattoo의 `handoff` 필드 중 `prioritized_focus`와 `constraints`를 포함하는 정교화 스키마. Exp045에서 추가되어 18/18 100% 달성.

**Judge Role (C)** — Orchestrator의 비결정론 경로. 현재 phase 수렴 여부와 다음 phase 전이를 결정. `experiments/system_prompt.py:JUDGE_PROMPT`. → § 6 참조.

**next_directive** — Tattoo의 필드. 다음 cycle에서 A가 집중해야 할 지시사항을 담는다. C(Judge)가 작성하고 A가 읽는다.

**Orchestrator** — 본 문서에서 두 역할로 분리: Python Orchestrator(결정론 안전장치) + Judge Role(비결정론 메타 판단). → § 6 참조.

**Phase** — 작업 진행 단계. 예: `EXPLORE`, `SYNTHESIZE`, `CONCLUDE`. `experiments/schema.py`의 Tattoo meta 필드에 기록.

**Proposer (A)** — 답변을 제안하는 역할. `experiments/system_prompt.py:SYSTEM_PROMPT`.

**Python Orchestrator** — `experiments/orchestrator.py:run_abc_chain`의 Python 로직. `MAX_CYCLES` 상한, phase fallback, schema validation 등 결정론적 안전장치 담당. → § 6 참조.

**Role Agent** — prompt에 의해 특화된 LLM 인스턴스. Proposer(A), Critic(B), Judge(C)의 세 역할. 같은 모델(Gemma 4 E4B)이라도 역할 prompt에 따라 관점이 분화됨. → § 2.3 참조.

**Structured State Imprint (SSI)** — Tattoo의 공식 별칭. 소형 LLM의 비휘발성 외부 기억 구조체임을 강조한 명칭.

**Tattoo** — 제멘토의 핵심 외부 상태 구조체. 소형 LLM이 cycle 간 연속성을 유지할 수 있도록 JSON 형태로 외부에 저장된다. `experiments/schema.py:Tattoo`. → § 2.1 참조.
