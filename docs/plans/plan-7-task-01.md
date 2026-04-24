---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: plan
parallel_group: A
depends_on: []
---

# Task 01 — conceptFramework.md 신설

## Changed files

- `docs/reference/conceptFramework.md` — **신규 파일**. canonical 개념 프레임 문서.

## Change description

신규 문서. 아래 10개 섹션을 순서대로 작성한다. 각 섹션은 설명과 함께 **구현 파일 경로 또는 실험 번호 1개 이상을 반드시 인용**하여 추상 부유를 막는다.

### 섹션 0 — Metadata + 한 줄 요약

```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-24
canonical: true
---

# 제멘토 개념 프레임 (Concept Framework)

> 제멘토는 소형 LLM의 내부 한계를 **체계적으로 외부화**하여 장기·다단계 작업을 가능하게 만드는 오케스트레이션 연구다.
```

### 섹션 1 — 최상위 원리

```markdown
## 1. 최상위 원리 — 외부화

제멘토의 설계 원리는 **"소형 LLM 내부 한계의 외부화"** 한 문장으로 요약된다.

소형 LLM(예: Gemma 4 E4B)은 컨텍스트·집중력·자가 검증·메타 판단 능력이 대형 모델에 미치지 못한다. 제멘토는 이 한계를 **대형 모델로 바꾸지 않고**, 부족한 각 능력을 외부 자원으로 대체한다. 이 원리는 네 개의 축으로 구체화된다.
```

### 섹션 2 — 4축 외부화 정의

표로 요약 + 각 축별 하위 섹션으로 설명:

```markdown
## 2. 4축 외부화

| 축 | 외부화 대상 | 왜 외부화하는가 | 구현 예시 |
|----|-------------|----------------|-----------|
| **Tattoo** | 상태 (기억) | 소형 LLM은 컨텍스트 cross-cycle 유지 불가 | `experiments/schema.py:Tattoo` |
| **Tool** | 행동 (계산·검색·검증) | LP 최적화 등 결정론적 계산은 모델 내부에서 불안정 | `experiments/tools/math_tools.py` |
| **Role Agent** | 관점 (자가 vs 교차) | 자가 검증 0% (Exp03) — 역할 분리로 80% 회수 (Exp035) | `experiments/system_prompt.py:CRITIC_PROMPT` |
| **Orchestrator** | 메타 제어 (phase 전이·retry) | 자율 phase 전이 0% (Exp02 v1) — 외부 제어로 94.4% (Exp02 v2) | `experiments/orchestrator.py:run_abc_chain` + Judge Role |

### 2.1 Tattoo — 상태의 외부화

…설명… `schema.py`의 Tattoo dataclass가 meta/phase/assertions/handoff/critique_log/next_directive 필드를 가진다. 매 cycle 모델은 fresh context에 이 JSON 하나만 주입받아 연속성을 유지한다.

### 2.2 Tool — 행동의 외부화

…설명… Exp08에서 calculator/solve_linear_system/linprog 3종이 A에게 주입되어 math-04가 0%→80%로 상승 (`experiments/tools/math_tools.py`).

### 2.3 Role Agent — 관점의 외부화

…설명… 같은 E4B 모델이라도 prompt에 따라 Proposer/Critic/Judge로 특화됨 (`experiments/system_prompt.py`: SYSTEM_PROMPT, CRITIC_PROMPT, JUDGE_PROMPT).

### 2.4 Orchestrator — 메타 제어의 외부화

…설명… Python 쪽은 결정론적 안전장치, C(Judge Role)는 비결정론적 판단을 담당 (섹션 6에서 상세).
```

### 섹션 3 — Memento 영화 비유 매핑

```markdown
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

영화와 달리 제멘토는 **각 요소를 명시적·구조화된 형태로 설계**한다 — 종이 문신이 아니라 JSON 스키마, 우연한 만남이 아니라 A-B-C 직렬 호출.
```

### 섹션 4 — Critic Tool vs Critic Agent 경계

```markdown
## 4. Critic의 이중 구분

**Critic은 Tool과 Agent로 분리된다.** 판단 성격(결정론/비결정론)과 구현 방식(순수 함수/LLM 호출)이 다르다.

| | Critic Tool | Critic Agent (Role) |
|---|-------------|---------------------|
| 판단 성격 | **결정론적** 검증 | **비결정론적** 비판 |
| 예시 | JSON 스키마 검증, `evidence_ref` 존재 확인, citation resolve, AST 화이트리스트 | 논리 모순 감지, 근거 충분성 판단, 의미적 일관성, 누락 감지 |
| 구현 | 순수 함수 (Python, Rust) | LLM 호출 + system prompt 역할 지정 |
| 장단점 | 빠름·저비용·재현 가능, 단 의미론적 판단 불가 | 의미 판단 가능, 단 80% 한계 존재 (Exp035) |
| 현재 제멘토 구현 | 부분 (AST 화이트리스트 `tools/math_tools.py:_eval`) | 완전 (`system_prompt.py:CRITIC_PROMPT`, Exp035/04에서 B 역할) |

### 4.1 구분 원칙

- **모든 가능한 입력에 대해 정해진 출력이 있는 판단은 Tool**. 예: JSON 스키마 합치 여부.
- **문맥에 따라 판단이 달라지는 것은 Agent**. 예: "이 논리가 충분한 근거인가".

두 경로는 **병렬 사용 가능**하다. 예: Tool이 먼저 스키마 적합성을 검증한 뒤, Agent가 의미적 모순을 판단.
```

### 섹션 5 — Tattoo–Evidence Tool 결합 쌍

```markdown
## 5. Tattoo–Evidence Tool 결합 쌍

Tattoo는 **상태 자체뿐 아니라 환경 포인터**(evidence_ref)를 포함한다. Evidence Tool은 이 포인터를 resolve하여 원문 근거를 재확인한다. 이 두 요소는 독립이 아니라 **결합 쌍**으로 설계되어야 한다.

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

- Tattoo 스키마: `experiments/schema.py`에 `assertions` 리스트는 있으나 `evidence_ref` 필드는 **미구현** (Exp04~08b는 암묵적으로 cycle_details에 tool_calls를 로그하는 방식).
- Evidence Tool: 현재 제멘토에는 공식 Evidence Tool이 없다. 외부 seCall 같은 환경에선 `/api/get/:id`가 역할을 수행.
- **미완 항목** — 섹션 9에 후속 과제로 명시.
```

### 섹션 6 — Orchestrator 이중 구분

```markdown
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

- **Exp02 v1 → v2**가 이 구분의 직접 근거. v1에서 phase 전이를 모델 자율에 맡겨 0% 실패, v2에서 Python 강제로 94.4%. 그런데 Exp04의 C Role이 "자율 phase 전이"를 100% 성공시키면서 **비결정론 경로도 가능함**을 입증.
- 결론: Python은 **실패 방지용 안전망**, C Role은 **의미론적 진행 결정자**. 서로 대체재가 아니라 보완재.

### 6.2 설계 시사점

- "Orchestrator를 완전히 LLM화할 수 있는가"라는 질문은 **틀렸다**. 두 종류의 판단이 섞여 있기 때문.
- Python 안전장치는 **남겨야 한다** — 모델이 무한 루프·malformed output에 빠질 때 개입.
- 의미론적 진행 결정은 **Judge Role에 완전 위임 가능** — Exp04가 입증.
```

### 섹션 7 — 4축 통합 다이어그램

```markdown
## 7. 4축 통합 다이어그램

ASCII로 외부화 원리와 4축의 상호작용을 표현. 예시 형태:

```
┌────────────────────────────────────────────────────────────┐
│                소형 LLM (Gemma 4 E4B)                        │
│                                                            │
│                    ▲                                       │
│                    │                                       │
│              ┌─────┴─────┐                                 │
│  외부화       │   내부     │                                 │
│              │   한계     │                                 │
│              └─────┬─────┘                                 │
│     ┌──────────────┼──────────────┐                        │
│     ▼              ▼              ▼              ▼         │
│ ┌────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│ │ Tattoo │   │  Tools   │   │ Role     │   │ Orches-  │   │
│ │ (상태) │   │ (행동)   │   │ Agents   │   │ trator   │   │
│ │        │   │          │   │ (관점)   │   │ (메타)   │   │
│ └────────┘   └──────────┘   └──────────┘   └──────────┘   │
│     │              │              │              │         │
│     └──────────────┴──────────────┴──────────────┘         │
│                          │                                 │
│                          ▼                                 │
│              ┌─────────────────────┐                       │
│              │   외부 환경           │                       │
│              │ (파일시스템/DB/API)   │                       │
│              └─────────────────────┘                       │
└────────────────────────────────────────────────────────────┘
```

Tattoo와 Tools는 외부 환경에 직접 쓰고 읽는다. Role Agents는 Tattoo를 읽어 Tools로 행동하고 새 Tattoo를 쓴다. Orchestrator는 이 전 과정의 시점을 조율한다.
```

### 섹션 8 — 실험별 검증 축 매핑

```markdown
## 8. 실험별 검증 축 매핑 (Exp00~08b)

| 실험 | 검증된 축 | 결과 요약 |
|------|-----------|-----------|
| Exp00 | — (baseline, 외부화 없음) | 9/18 (50%) — 외부화 부재 기준점 |
| Exp01 | Tattoo 용량 | assertion 12개까지 안정 (soft cap 8 타당성) |
| Exp02 v1→v2 | **Orchestrator 외부화** | 자율 0% → Python 강제 94.4% |
| Exp03 | — (자가 검증 한계 확인) | silent failure 0/15 감지, Role 외부화 필요성 입증 |
| Exp035 | **Role 외부화** | 자가 0% → 교차 80% |
| Exp04 | **Role 외부화 + Judge Role** | 100% 수렴, C 자율 phase 전이 30/30 |
| Exp045 | Tattoo 정교화 (Handoff Protocol) | 18/18 (100%) — `prioritized_focus + constraints` 필드 |
| Exp07 | Orchestrator 포화점 | actual_cycles ≈ 7 고정 (MAX_CYCLES 상한 ≠ 포화점) |
| Exp08 | **Tool 외부화** | +18.3%p, math-04 0→80% |
| Exp08b | Tool 부작용 완화 | 실행 대기 (H8 판정) |

**관찰**: 4축 각각 최소 1개 실험으로 외부화 효과가 확인됨.
```

### 섹션 9 — 외부화 미완 영역

```markdown
## 9. 외부화 미완 영역 (향후 확장 후보)

현재 4축 외에 다음이 미검증 또는 미구현:

| 후보 | 현재 상태 | 필요한 실험/구현 |
|------|-----------|------------------|
| **Extractor Role** | 미구현 | 원문 chunk → claim·entity 추출. 장기 워크플로우에서 원천→Tattoo 변환 역할 |
| **Reducer Role** | 미구현 | 다수 chunk-level Tattoo → 일일/프로젝트 단위 요약 |
| **Search Tool** | 미구현 | 과거 세션·문서 retrieval (BM25/vector) |
| **Graph Tool** | 미구현 | entity/relation 다중 hop traversal |
| **Critic Tool** | 부분 (AST 화이트리스트만) | JSON schema 검증, citation resolve 같은 구조적 검증기 |
| **Evidence Tool** | 미구현 | evidence_ref 스키마 + resolve API |
| **Large Model Tool** | 미구현 | Sonnet/Opus escalation 경로 |

이 후보들은 Exp09+ 실험에서 개별 또는 조합으로 검증될 수 있다. 각각을 추가할 때마다 "해당 축의 외부화가 어떤 성능 축을 어떤 폭으로 회수하는가"를 측정.
```

### 섹션 10 — 용어집

주요 용어(Tattoo, Structured State Imprint, Assertion, Handoff Protocol, Phase, next_directive, Proposer/Critic/Judge, Orchestrator, Tool, evidence_ref 등)의 짧은 정의를 알파벳 순으로. 각 항목 1~3줄.

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음.
- 실제 파일(`experiments/schema.py`, `system_prompt.py`, `tools/math_tools.py`, `orchestrator.py`) 참조를 위한 **검증된 경로만** 인용. 경로 확인은 `grep -n` 또는 `ls`로 미리.

## Verification

```bash
# 1. 파일 생성 확인
test -f docs/reference/conceptFramework.md && echo "created: OK"
# 기대: "created: OK"

# 2. Metadata 및 제목
head -12 docs/reference/conceptFramework.md | grep -E "type: reference|status:|canonical: true|# 제멘토 개념 프레임"
# 기대: 최소 4줄 매칭

# 3. 10개 메인 섹션 존재
grep -cE "^## [0-9]+\." docs/reference/conceptFramework.md
# 기대: 10

# 4. 필수 키워드 포함 확인 (5개 지시사항 반영 검증)
cd /Users/d9ng/privateProject/gemento && \
  for kw in "외부화" "Tattoo" "Role Agent" "Orchestrator" \
            "Critic Tool" "Critic Agent" "evidence_ref" "Judge Role" \
            "Python Orchestrator" "Memento"; do
    c=$(grep -c "$kw" docs/reference/conceptFramework.md)
    echo "$kw: $c"
    [ "$c" -ge 1 ] || { echo "MISSING: $kw"; exit 1; }
  done
# 기대: 모든 키워드 최소 1회 매칭

# 5. 구현 파일 참조 — 추상 부유 방지
grep -cE "experiments/schema\.py|experiments/tools/math_tools\.py|experiments/system_prompt\.py|experiments/orchestrator\.py" docs/reference/conceptFramework.md
# 기대: 4 이상 (4개 축 모두 최소 1회 참조)

# 6. 실험 번호 참조
grep -cE "Exp0[0-9]|Exp08b" docs/reference/conceptFramework.md
# 기대: 8 이상

# 7. 파일이 너무 짧지 않은지 (실질적 내용 확보)
wc -l docs/reference/conceptFramework.md | awk '{print $1}'
# 기대: 150 이상 (10 섹션이면 최소 이 정도)
```

## Risks

- **추상 부유**: 4축·외부화·Memento 같은 개념어가 많아 문서가 공중에 뜰 위험. 대응 — 모든 축 설명에 실제 파일 경로 또는 실험 번호를 인용하도록 Verification 5·6번에서 강제.
- **스키마 재정의 오류**: 섹션 5의 `evidence_ref` 예시는 **가상 스키마**. `experiments/schema.py`의 실제 `Assertion` dataclass에는 현재 이 필드가 없음을 명시해야 혼동 방지. 본 Task는 `experiments/schema.py`를 수정하지 않음.
- **Memento 비유 과장**: 영화 비유는 네이밍 유효성 증명일 뿐. "따라서 제멘토가 영화처럼 작동한다"는 식의 과잉 주장 금지. 섹션 3 말미에 "영화와 달리 명시적·구조화된 설계" 문구로 차별화.
- **섹션 8 실험 매핑의 정확성**: H1~H8 축 할당은 Task 02와 일관되어야 함. Task 02가 본 Task 01 완료 후 진행되므로, Task 01이 canonical source가 된다.
- **용어집 과잉**: 섹션 10이 너무 길어지면 문서 전체가 사전처럼 보임. 주요 용어 10~12개로 제한.

## Scope boundary

**Task 01에서 절대 수정 금지**:
- `experiments/` 전체 (코드 파일 모두)
- `README.md`
- `docs/reference/researchNotebook.md` (Task 02 영역)
- `docs/reference/experimentSummary.md`, `experimentDesign.md` — 역사 서사 문서
- `docs/reference/index.md` — 본 Task에서는 링크 추가 금지 (혼동 방지. 필요 시 별도 플랜)
- `docs/plans/` 하위 다른 파일

**허용 범위**: `docs/reference/conceptFramework.md` 신규 파일 1개만.
