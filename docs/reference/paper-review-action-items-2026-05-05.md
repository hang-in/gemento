---
type: reference
status: in_progress
updated_at: 2026-05-05
canonical: true
source: GPT 피드백 + Architect (Opus) 평가, 2026-05-05
related: docs/reference/readme-paper-strategy-2026-05-05.md
---

# Paper / README Review Action Items (2026-05-05)

GPT 가 paper draft v0.1 + README 검토 후 제공한 피드백을 Architect 가 평가하여 우선순위 분류한 action items. **P1 / P2 항목이 다음 세션에서 잊혀지지 않도록 본 문서로 영구화** — 진행 상태는 본 문서의 status 표를 직접 갱신.

## 1. 핵심 framing 변화

### 1.1 Paper positioning — Framework paper → Measurement paper

**현재 draft v0.1 의 contribution 순서**:
1. 4-axis externalization framework
2. Position-effect asymmetry
3. Reproducible measurement protocol

**revised 순서 (수용)**:
1. **Position-effect asymmetry in role-axis addition** (sharpest single claim)
2. **Same-model isolation protocol** for measuring structural workflow effects (model-quality confound 분리 — 새 contribution)
3. **Reproducible small-LLM externalization harness with negative results**

**근거**: Zhou et al. 2026 등 선행 externalization framework 와 직접 충돌. *Measurement / ablation paper* 포지셔닝이 Gemento 의 실제 강점 (negative result 정직, mirror-image 거울상, same-model rigor) 에 부합.

### 1.2 제목 변경

**from**: "Externalization for Small-LLM Workflows: Position-Effect Asymmetry in Role-Axis Addition"
**to**: "**Role Addition Is Not Monotonic: Position Effects in Small-LLM Workflow Externalization**"

수동태 → 능동태, claim 명료화.

### 1.3 4-axis framework 의 위치 재정의

framework 는 *organizing principle* 로 유지 (가설 분류 도구), 단 contribution 1순위에서 제거 + Section 3 비중 축소. "framework 기여" 가 아니라 "가설을 organize 하는 분류 도구".

---

## 2. P0 — 외부 공개 전 차단 요인 (즉시 실행)

| ID | 항목 | 상태 | 비고 |
|---|---|---|---|
| P0-1 | README (한·영) **톤다운 pass** — confirmed→observed, mirror-image 완화, Gemini 비교 wall-time 명시, H11/H12 비유의 명시, scorer limitation 1단락 | **done** (2026-05-05) | hero / 가설 표 H11+H12 / Roadmap / What this is not / Exp10 Exp12 Exp13 단락 모두 적용 |
| P0-2 | `docs/paper/draft.md` **revision v0.2** — contribution reorder, abstract defensive, 제목 변경, position effect §5.5 로 이동, scorer limitation Results 위치, same-model isolation protocol 명시 | **done** (2026-05-05) | 제목 "Role Addition Is Not Monotonic" / contribution 순서 변경 / abstract defensive / §4.6 main observation + §4.6.1 case study + §4.6.2 caveat / §5.1 same-model isolation 명시. 단 §5.5 로의 위치 이동은 P1-5 (논문 구조 reorder) 에서 |
| P0-3 | Reproducibility 보완 — README "Reproduce headline Exp10" 섹션 + Python version 정정 + LM Studio/llama.cpp 일관 | **done** (2026-05-05) | Python 3.14 전제 + 3.12+ 호환 명시 / LM Studio + llama.cpp 양쪽 명령 / `curl /v1/models` 의 model id 매칭 / Exp10 reproduce 명령 추가 |
| P0-4 | `docs/reference/index.md` Exp13 링크 검증 + 누락 시 보완 | **done** (2026-05-05) | 분석 보고서 + result.md + readme-paper-strategy + paper-review-action-items 4개 추가 |
| P0-5 | H12 mechanism 보강 — synthesis-04 baseline vs reducer 원문 case study 섹션 추가 (paper draft) | **done (1차)** (2026-05-05) | §4.6.1 stub + §4.6.2 caveat (keyword scorer artifact 가능성 명시 + LLM-as-judge replication 예정). 본문 확장 (전문 인용, evidence coverage 비교) 은 P1-3 LLM-as-judge 결과 후 v0.3 에서 |

### 2.1 톤다운 단어 매핑 (P0-1 + P0-2 공통)

| 현재 | 수정 |
|---|---|
| "Position-effect asymmetry **confirmed**" | "evidence consistent with a position effect" 또는 "observed pattern" |
| "**clean** mirror-image result" | "mirrored directional effect at similar effect size (|d|=0.323)" |
| "**safe** vs **risky**" | "appears safer / more failure-prone under this setup" |
| "**matching** Gemini Flash by +19pp" | "outperformed one-call Flash on 9-task cost-aware benchmark with ~20× wall-time" |
| "Cross-model replication [TBD] **confirms** direction" | "is planned to test whether direction generalizes" |
| "**validated**" | "supported by current runs" 또는 "conditionally supported" |
| "Stage 5 Role-axis **triply validated**" | "Stage 5 provides converging evidence on role-axis effects" |

**원칙**: p>0.05 결과에 "confirmed" 사용 금지. n=15 paired 의 검정력 한계 명시.

### 2.2 P0-5 H12 보강 핵심

**문제**: GPT 가 짚은 가장 큰 약점.

> "Reducer 가 *더 좋은 답* 을 했는데, deterministic keyword scorer 가 keyword 손실만 벌점 처리한 것 아닌가?"

**현재 draft 가 답하지 못함**. synthesis-04 의 "270 individuals" answer 는 의미적으로 정확할 수 있음. baseline 의 multi-paragraph 답변이 keyword 매칭에 유리했을 뿐일 가능성.

**필수 보강 (P0-5)**:
- (a) synthesis-04 baseline vs reducer 의 *전문 비교* (Results / Mechanism 섹션 직접 노출)
- (b) `gold_evidence_chunks` / `expected_answer` 와 reducer 답변의 evidence coverage 비교 (가능한 범위)
- (c) keyword scorer limitation 을 Discussion 이 아니라 *Results 직후* 에 명시

**추가 보강 (P1, 별도)**:
- (d) **LLM-as-judge** 보조 평가 — Groq GPT-OSS 120B 로 의미적 채점 → §3 P1-3 참조

---

## 3. P1 — 개선 (Stage 6 와 병행 또는 외부 공개 전)

| ID | 항목 | 상태 | 시점 |
|---|---|---|---|
| P1-1 | Related Work 차별화 추가 — AutoGen / MetaGPT / Reflexion / Self-Refine / Toolformer / Gorilla 1문장씩 | pending | Stage 6 본격화 시 |
| P1-2 | Gemma 4 E4B 정확 표기 — 모델 카드 검증 후 일관 적용 ("4B effective" → "4.5B effective / 8B incl. embeddings" 추정) | pending | 검증 후 결정 |
| P1-3 | LLM-as-judge 보조 평가 — Groq GPT-OSS 120B 로 H12 (그리고 가능 시 H11) 의 의미적 채점 추가. 본 keyword scorer 의 artifact 가능성 직접 반증 | pending | Stage 6 cross-model 인프라 활용 |
| P1-4 | 통계 5튜플 모든 가설 통일 — H1, H7, H8, H9a 의 Bootstrap CI 재산정 (현재 H10/H11/H12 만 5튜플 갖춤) | pending | Stage 6 와 병합 |
| P1-5 | 논문 구조 reorder — Framework 작게, Section 5 Results 5 sub-section 으로 분리 (5.5 main claim) | pending | P0-2 와 함께 또는 직후 |
| P1-6 | manual adjudication sample — synthesis-04 의 5 trial × 2 condition = 10 답변 사용자 직접 평가 (1-5점) | pending | 사용자 결정 |

---

## 4. P2 — 조건부 / 보류

| ID | 항목 | 조건 |
|---|---|---|
| P2-1 | 정량적 보조 지표 (`score_answer_v4`) — evidence coverage / contradiction coverage / multi-source structure preservation | 새 채점 인프라 필요. P1-3 (LLM-as-judge) 결과로 충분하면 보류 |
| P2-2 | Demo / cover image / 시각자료 (CTX 패턴) | 비용 큼, 본 plan 영역 외. arXiv 업로드 직전 |
| P2-3 | Bibtex 별도 `references.bib` 파일 분리 | LaTeX 변환 시점에 |

---

## 5. Architect 가 GPT 피드백에 push back / 조정한 항목

### 5.1 "mirror image" 시각적 metaphor — 보존

GPT: "clean mirror-image result" → "mirrored directional effect" (전면 단순화 권장)

**Architect**: |d|=0.323 가 양/음 정확히 동일한 *정량적 사실* 보존. 단 통계 위치 명시 부가.

권장 표기:

> "The two roles produced effect sizes of opposite sign with nearly identical magnitude (|Cohen's d| = 0.323), an observed mirroring that — though not statistically significant at n=15 — provides a concrete pattern for future replication."

→ 거울상의 시각적 metaphor 보존, 통계 위치 동시 명시.

### 5.2 Same-model isolation protocol 격상 — 수용

GPT 권장 contribution 2번이 의외로 강함. 동일 base model 로 모든 Role 을 채우는 것이 *role separation 효과를 model-quality confound 와 분리* 하는 protocol — 이 자체가 measurement methodology 기여. paper 에서 명시적 contribution 으로 다룬 적 없음. P0-2 의 일부.

### 5.3 framework novelty 약화 — 조건부 수용

framework 자체는 *organizing principle* 로 유지. contribution 1순위에서 제외 + Section 3 비중 축소. "framework 기여" 가 아니라 "가설 분류 도구" 로 재정의.

---

## 6. 예상 외부 공격 + 방어 카드

GPT 정리한 5 가지 예상 반응 — Architect 평가:

| 예상 공격 | 방어 카드 | 현재 상태 |
|---|---|---|
| "n=15 면 의미 없지 않나?" | 비유의성 명시 + replication target | P0-1/2 톤다운 시 자동 해결 |
| "keyword scorer 면 답변 품질이 아니라 키워드 맞추기 아닌가?" | scorer limitation Results 위치 + LLM-as-judge 보조 (P1-3) | P0-5 + P1-3 |
| "Gemini 보다 낫다는 건 과장 아닌가?" | 9-task benchmark 한정 + ~20× wall-time | P0-1 톤다운 |
| "그냥 RAG 아닌가?" | H9b inconclusive 명시 | 이미 README 명시 ✅ |
| "논문도 아닌데 논문처럼 포장?" | measured notebook + draft skeleton, arXiv는 보강 후 | README 의 "What this is / is not" 강화 |

---

## 7. 진행 우선순위 + 완료 조건

### 외부 공개 가능 조건 (arXiv 업로드 전)

- [ ] 모든 P0 완료 (P0-1 ~ P0-5)
- [ ] P1-1 (Related Work 차별화 완료)
- [ ] P1-3 또는 P1-6 (의미적 채점 보조 평가 — H12 scorer artifact 방어)
- [ ] P1-4 (통계 5튜플 모든 가설 통일)
- [ ] Cross-model replication 1건 이상 (Stage 6, 별도 plan)

### Architect 권장 진행 순서

1. **본 문서 작성 + commit** ← 지금
2. **P0-1 ~ P0-5 즉시 (A-2 진행 중 ~3-5h 분량)** ← 다음
3. P1 항목 — Stage 6 본격화 시 통합

### 다음 세션 인계 방법

1. 본 문서 (`docs/reference/paper-review-action-items-2026-05-05.md`) 를 먼저 read
2. 위 표의 status 컬럼 확인 → pending 항목부터 진행
3. 진행 시 status → in_progress, 완료 시 → done 으로 갱신
4. 새 발견 시 P0/P1/P2 표에 row 추가

---

## 8. 변경 이력

- 2026-05-05 v1: 초안. GPT 피드백 (16 항) + Architect 평가 (P0/P1/P2 분류 + 5 push back) 통합 정리. P1 망각 차단을 위한 영구 문서. 진행 시 본 문서의 status 표를 직접 갱신.
- 2026-05-05 v2: P0-1 ~ P0-5 모두 **done**. 다음 차단 작업 없음 — P1 진입 가능. P1 의 LLM-as-judge replication (P1-3) 이 H12 핵심 약점 방어이므로 Stage 6 cross-model 인프라 (Groq client) 와 자연 결합 권장.
