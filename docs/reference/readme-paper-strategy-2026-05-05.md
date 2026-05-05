---
type: reference
status: in_progress
updated_at: 2026-05-05
canonical: true
---

# Gemento README 검토 + 논문 작성 전략

*작성일: 2026-05-05 · 비교 대상: `jaytoone/CTX` (publication-ready 학술 레포 + paper draft 543줄)*

> **갱신 이력**:
> - v1 (2026-05-05): 초안. 위치 `docs/plans/`. EMNLP submission 가정.
> - v2 (2026-05-05): `docs/reference/` 이동. **H13→H12 정정** (Reducer = H12, H13 = Search Tool 진행 중). **arXiv preprint 단일 target 으로 변경** (사용자 결정). Cross-model 모델 후보 갱신 (3060 Ti 8GB 호환). Cerebras Inference 옵션 추가.

## TL;DR

- **Gemento 의 학술 narrative (가설 ID, falsification, scope discipline) 는 CTX 보다 강함.** 다만 publication 의 운영 측면 (citation hygiene, external validity, hero impact, statistical reporting, paper anchor) 이 약해서 reviewer 가 narrative 의 강점에 도달하기 전에 표면적 문제에서 막힐 위험이 큼.
- **즉시 처리 (이번 주):** README 의 4개 "citation pending" 제거, hero 1단락에 핵심 수치 끌어올리기, `docs/paper/draft.md` anchor 생성.
- **단기 (2~4주):** Cross-model reproduce 1~2개 — Local Qwen 2.5 7B Q4_K_M (3060 Ti 8GB 호환, longctx 가능) + (옵션) Cerebras Llama 3.1 8B (22일 내 마감 — main taskset 빠른 재현). 통계 표기 통일 (n, p, d, 95% CI 4종).
- **출간 전략:** **arXiv preprint 단일 target** (사용자 확정). venue submission 압박 없음. 단 *quality bar 는 venue 수준* — reviewer-proof 통계 / citation / external validity 동일 적용.

---

## 1. README 비교 (Gemento vs jaytoone/CTX)

### 1.1 한눈 비교 표

| 축 | Gemento | jaytoone/CTX | Gemento 작업 우선순위 |
|---|---|---|---|
| Hero (5초 안에 보이는 핵심 수치) | 없음 — "not a paper" 자기제한으로 시작 | 첫 단락에 3개 (1.9× TES, 5.2% tokens, +0.163 R@5 external) | **P0** |
| 배지 / cover image / 데모 영상 | 0 / 없음 / 없음 | 6개 / cover graph / 39초 영상 | **P1** |
| 즉시 실행 진입장벽 | clone + venv + pip + llama.cpp 서버 + smoke (5단계) | `pip install ctx-retriever` + 5줄 코드 | **P2** |
| install 전 자기 검증 | 없음 | `python3 benchmarks/ctx_validate.py --days 7` (자기 transcript ceiling 측정) | P3 |
| External / held-out 검증 | 없음 (Gemma E4B 단일) | Flask/FastAPI/Requests + COIR + Bootstrap 95% CI | **P0** |
| 통계 표기 일관성 | 가설별 들쭉날쭉 (d 일부, CI 거의 없음) | Wilson 95% CI, McNemar p, Bootstrap CI 통일 | **P0** |
| paper / arXiv anchor | 없음 | `docs/paper/CTX_paper_draft.md` (543줄) + `.tex` + `.bib` + arXiv TBD + EMNLP 2026 명시 | **P1** |
| Citation hygiene | reference 4개 전부 "*citation pending*" 노출 | (반례 — references.bib 별도) | **P0 (치명적)** |
| Negative result / falsification | H2, H10, H12 정면 보고 — **CTX 보다 강함** (H13 Search Tool 은 Exp14 진행 중, verdict 미확정) | 없음 (results dump) | (유지) |
| 가설 narrative (H1~H12 verdict) | 있음 — **CTX 보다 강함** | 없음 | (유지) |
| Related work + "independent convergence" | 있음 — **CTX 보다 강함** | 없음 | (유지) |
| 다국어 (KO mirror) | 있음 — **CTX 보다 강함** | EN only | (유지) |

### 1.2 Gemento 가 잘하는 것 (살려야 할 자산)

1. **Hypothesis-driven narrative** — H1~H12 + ✅/❌/⚠ verdict + evidence link. Reviewer 가 "어떤 claim 을 어떤 실험으로 검증했나" 를 한 표에서 추적 가능. CTX 의 results dump 보다 학술적으로 우수.
2. **Negative result 정직성** — H2 (0/15 detected), H10 (effectively rejected, inverse mechanism), H12 (Reducer abstraction loss). Negative result 자체가 publication value. H13 (Search Tool, Exp14) 는 진행 중.
3. **Pre/post 대칭 설계 (Exp12 vs Exp13)** — "position-effect asymmetry confirmed". 단일 실험이 아닌 *대칭 쌍* 으로 가설을 검증한 것은 design rigor 의 강한 신호.
4. **Scope discipline** — "What this is / is not", "Contributed / Not contributed" 명시적 부정 진술. Reviewer 의 over-claim 의심 차단.
5. **Related work 의 ethical framing** — "independent convergence ... not a derivation". Priority dispute 회피의 모범.

### 1.3 Gemento 가 부족한 것 (CTX 와 비교)

| 항목 | 현 상태 | 영향 |
|---|---|---|
| Hero impact | 첫 줄이 자기제한 ("not a paper") | 학술 reviewer / 잠재 contributor 의 attention 즉시 이탈 |
| Citation hygiene | "citation pending" 4회 노출 (LightMem, ESAA, Chain-of-Agents, externalization preprint) | Reviewer reject 사유로 직접 지목 가능 |
| External / held-out | 단일 모델 (Gemma 4 E4B) + 단일 taskset (15 tasks) | Generalizability 질문에 답할 카드 없음 |
| 통계 보고 | H1, H7, H8, H9 등은 (n, p, d, CI) 표기 없음. H10/H11/H12 만 d 와 p 모두 표기 | Reviewer 의 "어디서는 보이고 어디서는 없냐" 일관성 지적 |
| One-line install | llama.cpp 서버 + tool_calls 지원 확인이 prerequisite | Reproducer 진입장벽 → 외부 reproduce 0건 위험 |
| Paper anchor | `docs/paper/` 폴더 없음 | 외부 인용 / 학술 연락 포인트 부재 |
| Demo / 시각자료 | 표만 있음 | 첫인상 약함, 트위터/Hacker News 노출 시 thumbnail 없음 |

---

## 2. CTX 논문 초안에서 추출한 학술 패턴

`hang-in/tunaCtx/docs/paper/` (CTX_paper_draft.md 543줄, paper2 502줄, .tex, references.bib, outline 189줄) 정독 후 Gemento 가 그대로 차용할 수 있는 패턴을 정리.

### 2.1 Abstract 압축 패턴 (CTX abstract 의 분해)

CTX abstract 한 문단에 다음 8개 요소가 모두 들어감:
1. 문제 (1문장): "context dilution ... Lost in the Middle"
2. 기존 한계 (1문장): "RAG ... treats code as flat text, ignoring structural dependency"
3. 솔루션 이름 + 한 줄 정의: "CTX, a trigger-driven dynamic context loading system that classifies ... into four trigger types"
4. 메소드 핵심 (1문장): "BFS over codebase import graph ... concept-aware BM25"
5. 평가 setup (1문장): "five datasets (synthetic 50/166, external Flask/FastAPI/Requests 256, COIR 100)"
6. 핵심 수치 (수치 5개): R@5 0.874 (synthetic), R@5 0.495 with 95% CI (external), G1 +0.890, G2 +0.688
7. Ablation 1개: "removing classifier reduces TES 48%"
8. 결론 한 줄: "trigger-aware, code-structure-informed retrieval achieves both high accuracy and strong generalization"

→ **Gemento abstract 에 적용**: 8요소 모두 채울 수 있음 (§4.3 draft 참조).

### 2.2 Three-fold contribution 구조

CTX intro 의 contribution 3개:
1. "A four-type trigger taxonomy" — taxonomy / framework 기여
2. "Import graph traversal" — algorithm / mechanism 기여
3. "TES metric ... validated by Pearson r=0.87 with NDCG" — metric / measurement 기여

→ **Gemento 적용**: (1) Four-axis externalization framework, (2) ABC role-separation pipeline, (3) Position-effect asymmetry (pre vs post role addition) 가 자연스러운 3-fold.

### 2.3 Related work 의 single-sentence differentiation

CTX 는 각 선행연구마다 1~2문장으로 차별점을 명시:
- MemGPT: "general-purpose ... does not exploit domain-specific structure"
- Memori: "treats all documents as flat text chunks ... CTX exploits import graphs"
- MeCo: "model-dependent ... cannot be used with proprietary API-only models"
- CAR: "CAR clusters by embedding similarity, while CTX classifies by trigger type"

→ **Gemento 의 "citation pending" 4개 (LightMem, ESAA, Chain-of-Agents, externalization preprint) 도 동일 패턴**으로 1문장씩 차별화 + bibtex 확정 필요.

### 2.4 Statistical rigor pattern

CTX 가 reviewer-proof 통계 표기:
- Recall 보고 시 항상 (n, 95% CI) 동반: "External mean 0.495 [0.441, 0.550]"
- Pairwise 비교는 McNemar p-value 표 (CTX 는 4 데이터셋 × 4 baseline = 16개 p-value 한 표에)
- Metric 신뢰성은 cross-metric correlation 으로 입증: "TES-NDCG Pearson r=0.87 (t=9.05, df=26, p<0.001)"
- LLM 평가는 Wilson 95% CI: "0.265 [0.162, 0.403]"

→ **Gemento 적용**: 현재 가설 표의 verdict 를 (Δ, n, p, Cohen's d, 95% CI) 5튜플로 통일.

### 2.5 Held-out / external generalization 의 무게

CTX 의 Section 4.8 "External Codebase Generalization" 한 섹션이 논문 publication-readiness 의 절반을 책임짐:
- 명시적으로 "These codebases were not used during any system development" 선언
- Engineering fix 도 정직하게 (`_index_imports` 의 CTX-internal convention 만 처리하던 것을 real Python import 로 확장 — "fixes ... were motivated by examining failure cases on external codebases—validating that hold-out generalization testing is necessary to detect CTX-internal assumptions")

→ **Gemento 적용 시급**: Cross-model reproduce (Qwen 2.5 7B / Phi-4 / Llama 3.2 3B 중 1개) 가 EMNLP/NeurIPS reviewer 의 첫 질문에 대한 답.

### 2.6 Limitations 섹션 패턴

CTX 의 limitations 가 강한 이유:
- 자기 결과의 약점 정직 (FastAPI 928 files 에서 TEMPORAL 0.100, IMPLICIT 0.240 — degradation at scale)
- COIR 에서 BM25 보다 24% 낮음 명시
- Over-anchoring (20% 빈도) failure mode 명시 + design 권고
- Nemotron-Cascade-2 가 internal model 임을 별표로 명시: "Readers should treat this result as a single-LLM data point rather than a generalizable finding"

→ **Gemento 의 "What this is / is not" 는 이미 같은 정신**. 논문화 시 별도 Limitations 섹션으로 분리하고 H4/H10/H13 의 power 한계 (n=15) 정직하게.

### 2.7 새 metric 도입 시 정당화 3축 (TES 사례)

CTX 의 TES metric 도입 정당화는 3축:
1. **Information-theoretic**: Zipf-distributed file access 가정 → log denominator 도출
2. **Economic interpretation**: marginal benefit / marginal cost ratio
3. **Empirical validation**: cross-metric correlation (TES-NDCG r=0.87)

→ **Gemento 가 만약 새 metric 도입한다면** (예: "externalization gain" = ABC 점수 − Solo 점수, 또는 "role-axis safety score") 같은 3축 정당화 필요.

---

## 3. Gemento 논문 작성 전략

### 3.1 출간 전략 — arXiv preprint 단독 (사용자 확정 2026-05-05)

| 측면 | 결정 |
|---|---|
| 단일 target | **arXiv preprint** — venue submission 압박 없음, rolling submission |
| Quality bar | **venue 수준 유지** — peer review 부재 → self-imposed reviewer-proofing 의무 |
| Timeline | 자유 — Stage 6 cross-model + Exp14 마감 후 본격화 |
| Future venue 전환 가능성 | 보존 — 동일 manuscript 로 EMNLP/ACL Findings track 후 단계 conversion 가능 |

**Framing 권장**: "Position-effect asymmetry in role-axis externalization" 이 가장 sharp 한 single-claim. Exp12 (+0.05) 와 Exp13 (−0.05) 의 거울상 결과 + d=±0.323 대칭 + 메커니즘 (abstraction loss vs cycle-1 input organization) 까지 연결되는 narrative 가 single best contribution.

**arXiv preprint 의 함정 회피**:
- 노출 후 회수 어려움 → 통계 / citation / external validity 모두 venue 수준 검증
- Self-imposed peer review: Architect + Sonnet 의 cross-check + 외부 sanity check (가능 시 1-2명)
- 버전 관리: arXiv v1 → v2 → ... 갱신 가능 — 첫 v1 부터 quality 핵심

### 3.2 Three contributions (제안)

1. **A 4-axis externalization framework for small-LLM workflows** (Tattoo / Tools / Role / Orchestrator) — taxonomy 기여.
2. **Position-effect asymmetry in role-axis addition**: pre-stage role addition (Extractor) is safe (Δ=+0.05), post-stage (Reducer) is risky (Δ=−0.05); mechanism = abstraction loss in post-stage compression — empirical / mechanism 기여.
3. **A reproducible measurement protocol for small-LLM externalization studies** — open-source harness, 13 hypotheses (H1~H12) with verdict / evidence / negative results, single-base-model rigor (Gemma 4 E4B across all roles to isolate structure from model-quality confound) — methodology 기여.

### 3.3 Abstract draft (1문단, ~200단어)

> Small open-weight LLMs (≤7B parameters) struggle on multi-step reasoning tasks where larger frontier models excel. We investigate whether externalizing four cognitive axes—working memory ("Tattoo"), computation ("Tools"), self-validation ("Role"), and control flow ("Orchestrator")—into structured workflow components rather than expanding model capacity can close this gap on a single 4B-effective open-weight model (Gemma 4 E4B). Across 13 sequentially numbered hypotheses (H1–H12) over 540+ trials, we report three primary findings. First, multi-step orchestration with role separation improves Gemma 4 E4B from 41.3% (1-loop solo) to 78.1% (8-loop A-Proposer / B-Critic / C-Judge), matching Gemini 2.5 Flash 1-call (59.1%) by +19pp at zero per-trial API cost. Second, self-validation by the same model fails (0/15 detected), but role-separated cross-validation recovers to 80%—isolating role separation, not model capability, as the active ingredient. Third, we identify a position-effect asymmetry in role-axis addition: pre-stage Extractor role yields Δ=+0.05 (Cohen's d=+0.32), while post-stage Reducer role yields Δ=−0.05 (d=−0.32), a mirror-image result driven by abstraction loss during post-stage compression. We release a reproducible harness with all hypothesis verdicts, including three negative results, to enable cross-model replication.

(수치는 README 표 기준 추정; 최종 arXiv 제출 전 재계산 필요.)

### 3.4 Section outline

```
1. Introduction
   1.1 Small-LLM gap on multi-step reasoning
   1.2 Externalization vs. parameter scaling
   1.3 Three contributions (위 §3.2)
2. Related Work
   2.1 Externalization frameworks (LightMem, ESAA, externalization preprint)
   2.2 Multi-agent role separation (Chain-of-Agents, AutoGen, MetaGPT)
   2.3 Self-validation / self-refine (CRITIC, Self-Refine, Reflexion)
   2.4 Tool use in small LLMs (Toolformer, Gorilla)
   — 각 선행연구 1문장 차별화 (CTX 패턴 §2.3)
3. Framework
   3.1 Four-axis externalization (Tattoo / Tools / Role / Orchestrator)
   3.2 Tattoo schema (structured JSON working memory)
   3.3 Role contracts (A-Proposer / B-Critic / C-Judge)
   3.4 Orchestrator loop (deterministic Python)
   3.5 Hypothesis numbering convention (H1~H12)
4. Experiments
   4.1 Model and base setup (Gemma 4 E4B, vLLM/llama.cpp, sampling params)
   4.2 Tasksets (15-task benchmark + 9-task subset; categories: math/logic/synthesis)
   4.3 Cross-model held-out (Qwen 2.5 7B replication of H1+H9a) ← 신규 작업
   4.4 Main results (H1, H7, H8, H9a — supported)
   4.5 Negative results (H2, H10, H12 [Reducer]; H13 [Search Tool] pending)
   4.6 Position-effect asymmetry (H11 Extractor +0.05 vs H12 Reducer −0.05 mirror analysis) ← 핵심 단일 contribution
   4.7 Statistical reporting (n, p, Cohen's d, 95% CI for all 13 hypotheses)
5. Discussion
   5.1 Why same-model role separation works (mechanism)
   5.2 Why post-stage role addition fails (abstraction loss)
   5.3 Implications for small-LLM deployment cost
6. Limitations
   6.1 Single base model (Gemma 4 E4B) — partially mitigated by §4.3 cross-model
   6.2 Power (n=15 underpowered for several hypotheses)
   6.3 Korean-language scoring caveat (해당 시)
7. Conclusion + Future Work (Tool axis: Search Tool Exp14)
Appendix
   A. Full hypothesis table with all statistics
   B. Tattoo JSON schema
   C. Role prompts (A/B/C system messages)
   D. Failure label taxonomy
```

### 3.5 Statistical reporting protocol (모든 가설 통일)

각 가설 verdict 행은 다음 5개를 모두 표기:

```
Δ = +0.044 (ABC − Solo), n = 15, p = 0.180 (paired Wilcoxon),
Cohen's d = +0.449 (medium), 95% CI [-0.018, +0.106] (paired bootstrap, 10k)
```

p-value 가 NS 라도 effect size + CI 를 반드시 보고 (CTX 가 일관되게 적용한 패턴). README 와 paper 양쪽에 동일 표기.

### 3.6 Held-out / external validity 작업 항목 (arXiv preprint 전 필수)

**Hardware 전제** (2026-05-05 결정): 3060 Ti 8GB 유지. 5060 Ti 교체는 Stage 6 이후. 따라서 모델 선택은 Q4_K_M 또는 더 작은 quantization 으로 8GB 호환.

| 작업 | 우선순위 | 예상 소요 | 산출물 |
|---|---|---|---|
| **Qwen 2.5 7B Q4_K_M** (local) 로 H1 (Exp10) 재현 | **P0** | 2~3일 | `experiments/cross_model/exp10_qwen25_q4.json` + 2 행 비교 표. 8GB VRAM 호환 (~7GB 사용) |
| **Cerebras Llama 3.1 8B** (API) 로 H1 빠른 재현 | **P0 (urgent)** | 1일 | 22일 deprecation 마감 (2026-05-27). 8K context 제약 → main taskset 한정 |
| Qwen 2.5 7B Q4 로 H9a (Exp09 Large 20K) 재현 — longctx 32K context | P1 | 3~5일 | `experiments/cross_model/exp09_qwen25_q4.json` (Cerebras 는 8K 한계로 불가) |
| Phi-3.5 mini 3.8B Q8 로 보조 size-class scaling | P2 | 2~3일 | 4-point scaling: Gemma 4B → Phi 3.8B → Qwen 7B → Llama 8B |
| H11+H12 (Extractor vs Reducer) cross-model 재현 | P1 | 5일 | Position-effect asymmetry 의 cross-model robustness |
| 기존 결과의 Bootstrap 95% CI 재계산 + 표기 통일 | P0 | 1일 | `docs/reference/all-hypotheses-statistics.md` |

### 3.7 README 단기 수정 (이번 주, 논문 작업과 별개로)

| 항목 | 작업 | 소요 |
|---|---|---|
| Citation 4개 확정 | LightMem, ESAA, Chain-of-Agents, externalization preprint 의 BibTeX 확정 (또는 paper-only 로 이동, README 에서 제거) | 2시간 |
| Hero 단락 재구성 | 첫 줄을 "Gemma 4 E4B (4B effective): 41.3% → 78.1% (+37pp) via multi-step orchestration + role separation, matching Gemini 2.5 Flash 1-call at zero per-trial cost." 로 시작 (attribution 정직: 4축 중 Orchestrator + Role 두 축 효과; Tool 은 H7/H8 별도 +18~23pp) | 1시간 |
| 배지 추가 | License, Python 버전, Last commit, (가능시) arXiv badge | 1시간 |
| 1장의 시각자료 | 가설 verdict bar chart (✅ 7개 / ⚠ 4개 / ❌ 2개) 또는 ABC vs Solo line chart | 2시간 |
| `docs/paper/draft.md` anchor 생성 | 빈 파일이라도 README 에서 link — "Paper draft: [docs/paper/draft.md] · arXiv: TBD · venue: EMNLP 2026 (target)" | 30분 |
| Quick Start 단순화 | llama.cpp 의존을 vLLM / Ollama 1줄 recipe 로 대체 | 2시간 |

### 3.8 docs 폴더 구조 변경 제안

현재 `docs/reference/` 에 분석 보고서가 평면적으로 누적 중. 논문 작업 본격화 시:

```
docs/
  paper/               ← 신규
    draft.md           ← § 3.4 outline 기반 main draft
    abstract.md        ← § 3.3 draft 발전형
    references.bib     ← citation 통일 관리
    figures/           ← bar chart, line chart 등
    submission/        ← venue별 LaTeX 변환본
  reference/           ← 기존 유지 (실험 분석 보고서)
  plans/               ← 기존 유지 (이 문서도 여기)
```

CTX 의 `docs/paper/{draft.md, .tex, references.bib, README.md}` 구조를 그대로 차용 권장.

---

## 4. 우선순위 + Timeline

### Phase A — 이번 주 (논문 submit 와 별개로 즉시)

- [ ] README "citation pending" 4개 처리 (확정 또는 제거)
- [ ] README hero 1단락 재배치 (Exp10 핵심 수치 첫 화면)
- [ ] `docs/paper/draft.md` empty anchor + README link
- [ ] 가설 표 Bootstrap 95% CI 재계산 (H1, H7, H8, H9a 우선)

### Phase B — 2~4주 (논문 manuscript draft 0)

- [ ] Cross-model replication 1개 — Qwen 2.5 7B 로 H1 (Exp10) 재현
- [ ] § 3.3 abstract 확정 (수치 재검증 후)
- [ ] § 3.4 outline 기준 Section 1 (Intro) + Section 3 (Framework) draft
- [ ] § 2.3 패턴으로 related work 4개 1문장 차별화
- [ ] 통계 표기 통일된 master hypothesis table (`docs/reference/all-hypotheses-statistics.md`)

### Phase C — 4~8주 (논문 manuscript draft 1)

- [ ] Section 2 (Related Work) 전체 + references.bib
- [ ] Section 4 (Experiments) 전체 (cross-model 결과 포함)
- [ ] Section 5 (Discussion) — 특히 § 4.6 Position-effect asymmetry single-claim narrative
- [ ] Section 6 (Limitations) — H4/H10/H13 의 power 한계 정직
- [ ] Figure 3개 (verdict overview / ABC vs Solo / pre vs post asymmetry)

### Phase D — 8주+ (arXiv 업로드)

- [ ] arXiv 업로드용 LaTeX 변환 (template 자유 — 일반 article 또는 conference 형식 차용 가능)
- [ ] arXiv preprint v1 업로드
- [ ] README 의 "Paper draft" → "arXiv: <ID>" 갱신
- [ ] (옵션) 추후 venue submission — manuscript 동일 reuse

---

## 5. Open Questions

논문 작성 전 결정 필요한 것들:

1. **Single best contribution 을 무엇으로 잡을지**: (a) 4-axis framework 자체 (broad), (b) Position-effect asymmetry (sharp single-claim), (c) 13-hypothesis reproducible harness as resource. 추천: **(b) sharp single-claim 으로 main paper, (a) 와 (c) 는 framework + appendix 로**.
2. **Cross-model replication 의 model 선택** (확정 2026-05-05, 3060 Ti 8GB 호환):
   - **Local Qwen 2.5 7B Q4_K_M** (P0) — modern + popular, 8GB 충분 (Q4 ~4.5GB + KV cache ~1.9GB)
   - **Cerebras Llama 3.1 8B** (P0 urgent, 22일 마감) — API 빠른 재현, main taskset 한정 (8K context)
   - Phi-3.5 mini 3.8B Q8 (P2 보조)
   - ~~Llama 3.2 3B~~ — 사용자 거부 ("오래되고 낮음")
3. **arXiv 업로드 시점**: 사용자 결정 — Stage 6 cross-model + Exp14 verdict 통합 후. venue submission 별도 결정 (option).
4. **Negative result 를 어디까지 main 에 포함할지**: H2 (self-validation 0/15) 는 main 의 핵심 motivation 이라 유지. H10 (Mixed Intelligence) 는 § 4.5 Negative results 에 narrative 로 포함. **H12 (Reducer) 는 § 4.6 position-effect asymmetry 의 절반** (H11 Extractor 와 거울상 = main contribution 의 일부). H13 (Search Tool, Exp14) 은 verdict 후 별도 결정.
5. **Korean mirror 유지 여부 (논문화 후)**: README.ko.md 는 contributor base 확장에 도움. 단 sync 부담. 추천: **유지하되 paper draft 는 영어 단일**.

---

## 6. 종합 평가

Gemento 의 학술 narrative quality 는 CTX 보다 **higher** 입니다 — H1~H12 hypothesis-driven, negative result 정직, scope discipline, related work 의 ethical framing 모두 CTX 가 갖추지 못한 장점입니다. 다만 publication 의 *operational* 측면 (citation hygiene, external validity, statistical reporting consistency, hero impact) 이 CTX 보다 약해서 reviewer 가 narrative 의 강점에 도달하기 전에 표면적 문제로 막힐 위험이 큽니다.

**가장 비용 대비 효과 큰 단일 작업**: Cross-model replication 1건 (Qwen 2.5 7B 로 H1 재현, 2~3일). 이것 1개로 EMNLP reviewer 의 가장 흔한 "single-model overfit" 질문에 대한 답이 생기고, README 의 generalizability 가시성도 동시에 해결됩니다.

**가장 시급한 단일 작업**: README "citation pending" 4개 처리 (2시간). reviewer 가 README 만 보고도 "rigor 부족" 인상을 받는 직접 원인입니다.

**유지해야 할 자산**: H1~H12 verdict 표, "What this is / is not", Related work 의 "independent convergence" framing — 이 셋은 CTX 가 갖지 못한 Gemento 만의 학술적 강점이고, 논문화 후에도 그대로 main paper 의 narrative 척추가 됩니다.
