---
type: plan
status: abandoned
updated_at: 2026-04-25
version: 1
---

# Exp09 — Long-Context Stress Test (ABC vs Solo-dump vs RAG)

## Description

제멘토의 **원래 핵심 가설** — "외부 상태(Tattoo)로 소형 LLM의 유효 컨텍스트를 확장한다" — 를 직접 검증한다. 지금까지 실험(H1·H3·H4·H7·H8)은 "계산·추론 능력 한계"를 외부화로 보완했지만, **컨텍스트 자체**의 한계는 직접 스트레스 테스트하지 않았다. Exp09는 sliding_window(512)의 20~40배 크기 문서에서 multi-hop 추론을 요구하여 이 가설을 정면으로 측정한다.

### 핵심 질문 + 가설 H9 (3단 분해)

**주요 질문**: 제멘토 ABC + Tattoo(chunked)가 (a) naive long-context 투입보다 우수하고, (b) 표준 RAG baseline 대비 고유 기여를 보이는가?

- **H9a (기본선)**: ABC+Tattoo(chunked) > Solo-dump. 외부 상태의 effective context 확장 효과.
- **H9b (차별성)**: ABC+Tattoo ≥ RAG baseline. 제멘토가 "그냥 RAG + loop"가 아님을 증명.
- **H9c (에러 모드)**: ABC+Tattoo의 실패 패턴이 RAG와 **질적으로 다름** (검증/비판 경로로 인한 차이).

가장 중요한 것은 **H9b** — 이게 부정되면 제멘토의 long-context 주장은 RAG 대비 신규성이 약함.

### 실험 규모 (MVP)

- **10 태스크** × **3 context size** (Small 3K / Medium 10K / Large 20K tokens) × **3 arm** (solo_dump / rag_baseline / abc_tattoo) × **3 trial** = **90 runs**
- MVP 수준. 통계적 유의성 본격 검증은 Exp09b에서 5 trial로 확대.

### 배경 이론

- **n_ctx 8K 제약**: 현재 llama.cpp 서버 설정은 slot당 8192 tokens. Small(3K)는 1회 호출에 들어가지만 Medium(10K)부터는 주의, Large(20K)는 명백한 초과 → Solo-dump는 구조적으로 실패 예상.
- **sliding_window 512**: 모델이 한 번에 attend할 수 있는 local window. 외부 상태로 관련 증거만 골라 넣으면 이 제약을 우회 가능하다는 가설.
- **RAG baseline 필요성**: "제멘토 = RAG + loop"라는 가장 단순한 대안 설명을 차단하기 위한 **필수 대조군**.

## Expected Outcome

1. **Long-document 태스크셋**: `experiments/tasks/longctx_taskset.json` 신규 — 10개 태스크, 3 size class, 3 hop type 분포.
2. **Chunker 모듈**: `experiments/tools/chunker.py` — 문서를 고정 크기 chunk로 분할 (words 기준, overlap 지원). tiktoken 의존성 없음.
3. **BM25 tool**: `experiments/tools/bm25_tool.py` — RAG arm용 retrieval. `bm25s` 패키지 사용 (순수 Python, 경량).
4. **Tattoo `evidence_ref` 필드**: `experiments/schema.py`의 `Assertion` dataclass에 `evidence_ref: dict | None = None` 추가. 기존 실험과 **역호환 유지**.
5. **ABC chunked 오케스트레이터**: `experiments/orchestrator.py`에 `run_abc_chunked()` 신규. 기존 `run_abc_chain` 재사용 원칙.
6. **Exp09 실행 분기**: `experiments/run_experiment.py`에 `run_longctx()` + `EXPERIMENTS["longctx"]`. 3 arm 루프 + 체크포인트.
7. **Measure analyzer**: `experiments/measure.py`에 `analyze_longctx` 추가. arm × size × hop_type 3-way breakdown + error mode taxonomy.
8. **Gemini 핸드오프**: `docs/reference/handoff-to-gemini-exp9.md` + `docs/prompts/2026-04-25/run-exp9.md`.

## Subtasks (Summary)

| # | Title | parallel_group | depends_on |
|---|-------|----------------|------------|
| 01 | Long-doc 태스크셋 설계 (10 tasks, 3 size × 3 hop) | A | — |
| 02 | Chunker 모듈 (`tools/chunker.py`) | A | — |
| 03 | BM25 tool 통합 (`tools/bm25_tool.py` + bm25s 의존성) | A | — |
| 04 | Tattoo 스키마 확장 (`Assertion.evidence_ref`) | A | — |
| 05 | ABC chunked 오케스트레이터 (`run_abc_chunked`) | B | 02, 04 |
| 06 | Exp09 실행 분기 (`longctx` 커맨드, 3 arm) | C | 01, 02, 03, 05 |
| 07 | Measure analyzer + Gemini 핸드오프 | D | 06 |

**Group A (task 01~04)**: 상호 독립 — 병렬 착수 가능.
**Group B (task 05)**: chunker + 스키마 확장 필요.
**Group C (task 06)**: 모든 요소 통합 실행자.
**Group D (task 07)**: 실행 후 분석 + Gemini 전달.

## Constraints

- 기존 실험 코드 **완전 보존** — longctx는 별도 커맨드·함수·체크포인트(`partial_longctx.json`).
- 외부 LLM judge 사용 금지 — v2 scoring_keywords 체계 그대로 (비용·재현성).
- Tattoo 스키마 `evidence_ref` 추가는 **Optional** — 기본값 `None`, 기존 실험 역호환.
- BM25는 `bm25s` 또는 `rank_bm25` 중 순수 Python — 벡터 임베딩 사용 안 함 (범위 제한).
- Context Large 20K에서 Solo-dump는 n_ctx 8K 초과 필연적 → **의도적 truncation**이 측정 포인트.
- 태스크는 **수동 작성 + 최소 2회 교차 검증** — math-04 expected_answer 결함 교훈 반영.

## Non-goals

- 벡터 임베딩 기반 RAG → Exp09b 이후로 분리 (BM25로 baseline 고정).
- Extractor/Reducer 신규 역할 도입 → Exp10+ (Stream Workflow).
- Cross-model 재현 (Qwen/Phi/Llama) → 별도 플랜 (B 경로).
- 태스크셋 **자동 생성** (LLM으로 질문·정답 생성) → 금지. 수동 작성.
- 대규모 벤치마크 (MultiDoc, LooGLE 등) 통합 → 범위 외.
- `evidence_ref`의 완전한 graph-style relation 표현 → dict 1개 수준 제한.
- Stream hook, 실시간 ingest → 범위 외.

## Version

- v1 (2026-04-25): 최초 작성. 7 서브태스크, 90 runs MVP, 3-arm 비교(Solo-dump / RAG baseline / ABC+Tattoo).
