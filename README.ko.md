# gemento (제멘토)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-active-success)]()
[![Last commit](https://img.shields.io/github/last-commit/hang-in/gemento)](https://github.com/hang-in/gemento/commits/main)
[![Paper](https://img.shields.io/badge/Paper-draft%20in%20progress-orange)](docs/paper/draft.md)
[![arXiv](https://img.shields.io/badge/arXiv-TBD-b31b1b)]()

> **9-task cost-aware benchmark 에서 Gemma 4 E4B 8-loop ABC = 78.1% vs 1-loop solo = 41.3%, Gemini 2.5 Flash 1-call = 59.1%. 외부 API 비용은 0 이지만 wall time 약 20배 trade-off.** 13 가설 (H1–H13, 540+ trial) 의 role-axis ablation 에서 **위치-효과 패턴 관찰**: pre-stage role 추가 (Extractor, H11) Δ=+0.05 (Cohen's d=+0.32, p=0.198), post-stage role 추가 (Reducer, H12) Δ=−0.05 (d=−0.32, p=0.180) — 거울상 방향성. **두 결과 모두 n=15 paired 검정에서 통계적으로 비유의; cross-model replication 으로 일반화 여부 확인 예정.**

> **소형 LLM의 내부 한계를 체계적으로 외부화한다.** 기억은 환경에 새기고, 계산은 도구에 맡기고, 검증은 다른 역할에게 비판받는다.

제멘토는 Gemma 4 E4B (effective 4B 파라미터, Q8_0) 같은 소형 언어모델이 단일 추론으로 해결하지 못하는 복잡한 태스크를, **외부 상태(문신) + 역할 분리(A-B-C) + 외부 도구(tool-use) + 오케스트레이션** 의 4축으로 확장할 수 있는지 측정하는 오픈 연구 노트입니다.

**증명된 핵심 수치 (재현 가능)**

| 실험 | Before | After | Δ | 외부화 축 |
|------|--------|-------|------|----------|
| Exp02 (다단계 루프) | 50% (1-shot) | **94.4%** (8 loops) | +44.4%p | Orchestrator |
| Exp035 (교차 검증) | **0%** (자가) | **80%** (역할 분리) | +80%p | Role Agent |
| Exp08 (Tool-use, math-04 LP) | 0% (tool 없음) | **80%** (linprog 주입) | +80%p | Tool |

> 이 결과는 effective 4B 소형 모델에서 관측된 것이며, 모든 실험은 단일 GPU로 로컬 재현 가능합니다.

이 레포는 **MIT 라이선스로 공개된 1인 연구 노트**입니다. 관심 있는 누구든 자유롭게 fork·재현·확장할 수 있습니다. 협업 창구는 프로젝트가 더 성숙한 시점에 열 예정입니다.

> *Last updated: 2026-05-05*

> 📚 English version: [README.md](./README.md)

### Scope 와 재현성 caveats (수치 인용 전 읽기)

- 모든 headline 수치는 **단일 base 모델** (Gemma 4 E4B) + **소형 자체 benchmark** (main 15 task + longctx 10 task) 기준. Cross-model replication 은 *예정*, 미완료.
- Stage 5 의 다수 가설 (H4, H10, H11, H12) 은 **n=15 paired 검정에서 통계적으로 비유의** — Cohen's d / bootstrap CI 와 함께 *replication target* 으로 보고. 확정 효과 아님.
- 결정성 keyword scorer (`score_answer_v3`) 는 *실제 품질 차이* 와 *답변 스타일과 keyword set 의 mismatch* 를 구분하지 못함. H12 (Reducer 의 다출처 압축) 에 가장 직접 영향. LLM-as-judge 보조 평가 예정.
- Exp10 vs Gemini Flash 비교는 *9-task cost-aware benchmark 한정* + wall time 약 20배 trade-off — 일반화된 우월 주장 아님.
- H11+H12 의 "position effect" 관찰은 *거울상 방향성* 이며 *확정 비대칭* 아님.

---

## 목차

1. [Why Gemento — 설계 원칙](#1-why-gemento--설계-원칙)
2. [The Core Idea — 외부화](#2-the-core-idea--외부화)
3. [What We've Proven](#3-what-weve-proven)
4. [What's Still Open — 열린 연구 질문](#4-whats-still-open--열린-연구-질문)
5. [Who Might Find This Useful](#5-who-might-find-this-useful)
6. [Quickstart (10 minutes)](#6-quickstart-10-minutes)
7. [Reproduce / Extend](#7-reproduce--extend)
8. [Roadmap](#8-roadmap)
9. [How to Contribute](#9-how-to-contribute)
10. [Docs Map](#10-docs-map)
11. [Acknowledgements](#11-acknowledgements)
12. [License](#12-license)

---

## 1. Why Gemento — 설계 원칙

제멘토는 소형 LLM을 대형 LLM의 "축소판"으로 보지 않습니다. 소형 모델에는 소형 모델이 잘하는 판단이, 대형 모델에는 대형 모델이 잘하는 판단이 있으며, 그 두 층위를 **크기가 아닌 역할로 배치**하는 것이 설계의 출발점입니다.

요약하면 **쓸 땐 쓰고 새는 건 막는다** — 4가지 운영 원칙으로 구체화합니다:

- **역할 기반 배치** — 크기가 아니라 태스크가 요구하는 판단 유형(결정론적 검증, 의미론적 비판, 메타 제어)에 맞춰 모델을 고른다.
- **자원은 필요할 때 충분히** — Tool 호출, 루프 예산, 대형 모델 escalation은 품질이 요구할 때 아끼지 않는다. 맥락 없는 절약이 오히려 품질을 떨어뜨린다.
- **중복·드리프트는 설계로 차단** — 같은 작업의 중복 호출, 근거 없는 재계산, 조건 없는 retry는 Tattoo와 Handoff Protocol이 구조적으로 막는다.
- **측정은 있는 그대로** — 채점 오류(Exp07 math-04 `expected_answer` 결함)를 발견 즉시 정정하고, 유의미하지 않은 수치에 의미를 덧붙이지 않는다.

모델 규모에 따라 자연스럽게 형성되는 불균형을 **설계 차원에서 완화**할 수 있다고 보는 실용 연구 노트입니다.

---

## 1.5. What this is / is not — 본 repo 는 무엇이고 무엇이 아닌가

이 repo 는:

- 소형 로컬 LLM workflow 의 재현 가능한 실험 하네스
- 외부화된 상태 / 도구 / 역할 / 제어를 측정한 연구 노트
- 재현·반박을 위한 공개 baseline

이 repo 는 아니다:

- 새로운 모델 architecture
- 학습 기법
- 4B 모델이 frontier 모델을 대체한다는 주장
- ABC+Tattoo 가 RAG 를 보편적으로 능가한다는 주장

---

## 2. The Core Idea — 외부화

소형 LLM은 모든 것을 기억할 수 없다. 제멘토는 **기억 대신 환경에 새기고**, **생각 대신 도구로 확인하고**, **자기 검증 대신 다른 역할에게 비판받는다**. 이 원리는 영화 *Memento*의 Leonard가 단기 기억상실과 함께 살아가는 방식과 정확히 닮았다 — 우연이 아니라 **설계의 근간**이다.

제멘토의 출발점은 secall / tunaflow를 만들면서 마주친 실제 문제들이었다 — 장기 기억 보존·검색, 컨텍스트의 유연한 확장(무절제한 토큰 사용 지양), 멀티세션. 처음 가설은 단순했다: *"컨텍스트를 전부 비우고 DB 검색만 시키면, DB를 거의 무한한 컨텍스트로 쓸 수 있는 것 아닌가?"* 그 생각을 더듬어 가다 Memento의 Leonard가 떠올랐다 — 문신·폴라로이드·전화로 기억상실을 보완하는 방식이 정확히 같은 구조였다. 제멘토는 그 메타포를 4개 외부화 축으로 구체화한 **1인 사이드 트랙 연구 노트**다.

### Memento ↔ 제멘토 매핑

| Memento 영화 요소 | 제멘토 대응 | 외부화 대상 |
|-------------------|-------------|-------------|
| 문신 (지워지지 않는 핵심) | **Tattoo** (Structured State Imprint, JSON 스키마) | 상태 (기억) |
| 폴라로이드 사진 | `evidence_ref` (스냅샷 포인터) | 증거 |
| 전화 (외부 정보 확인) | **Tool** (calculator / linprog / search) | 행동 |
| 조연 인물 (다른 관점) | **Role Agent** (Proposer / Critic / Judge) | 관점 |
| 반복 조사 (단서 재구성) | **Orchestrator loop** (A→B→C cycle) | 메타 제어 |

영화와 달리 제멘토는 **각 요소를 명시적·구조화된 스키마**로 설계한다 — 종이 문신이 아니라 JSON, 우연한 만남이 아니라 A-B-C 직렬 호출.

### 4축 구조

```
            소형 LLM (Gemma 4 E4B)
                    │
          ┌─────────┴─────────┐
          │    내부 한계        │
          └─────────┬─────────┘
      ┌────────┬───┴───┬───────┬───────┐
      ▼        ▼       ▼       ▼
  ┌────────┐┌──────┐┌──────┐┌─────────┐
  │ Tattoo ││ Tools││ Role ││ Orches- │
  │ (상태) ││(행동)││(관점)││ trator  │
  │        ││      ││      ││  (메타) │
  └────────┘└──────┘└──────┘└─────────┘
      │        │       │       │
      └────────┴───┬───┴───────┘
                   ▼
         ┌─────────────────┐
         │   외부 환경       │
         │ (FS/DB/API)     │
         └─────────────────┘
```

### Critic은 두 종류다

| | Critic Tool | Critic Agent (Role) |
|---|-------------|---------------------|
| 판단 성격 | 결정론적 검증 | 비결정론적 비판 |
| 예시 | JSON schema, `evidence_ref` 존재, citation resolve | 논리 모순, 근거 충분성, 의미적 일관성 |
| 구현 | 순수 함수 (Python/Rust) | LLM + 역할 프롬프트 |

제멘토에서 B(Critic Agent)는 Exp035에서 **자가 검증 0% → 교차 검증 80%** 회수를 증명했다. 결정론적 검증(Schema/Citation/AST)은 Critic Tool로 분리 — 두 경로는 병렬 사용 가능하며, 각자 다른 실패 유형을 잡는다.

### Orchestrator도 두 종류다

| | Python Orchestrator | Judge Role (C) |
|---|---------------------|----------------|
| 성격 | 결정론적 안전장치 | 비결정론적 메타 판단 |
| 담당 | MAX_CYCLES 상한, phase fallback, tool loop, schema validation | 수렴 판단, phase 전이, accept / reject / retry |
| Exp04 발동 빈도 | 0회 (안전망만 존재) | 30/30 (자율 결정) |

**"Orchestrator를 완전히 LLM화할 수 있는가"는 틀린 질문**이다. 결정론적 안전망(Python)과 비결정론적 메타 판단(Judge Role)은 서로 **대체재가 아니라 보완재**. Exp02 v1(모델 자율 0%) → v2(외부 강제 94.4%)와 Exp04(C 자율 전이 100%)가 이 구분을 각각 반대 방향에서 증명했다.

**자세한 프레임 정의**: [docs/reference/conceptFramework.md](docs/reference/conceptFramework.md) — 4축 구현 예시, Critic Tool vs Critic Agent 경계, Tattoo–Evidence 결합 쌍, Orchestrator 이중 구분(Python vs Judge Role), 실험별 축 매핑.

---

## 3. What We've Proven

지금까지 14개 실험(총 600+ trials)에서 확인된 가설:

| ID | 가설 (외부화 축) | 판정 | 근거 실험 |
|----|-----------------|------|----------|
| **H1** | [Orchestrator 외부화] 다단계 루프가 단일 추론보다 품질이 높다 | ✅ 채택 (+44.4%p Exp02; +37%p Exp10) | Exp02 v2, Exp10 |
| **H2** | [Role 외부화 필요성 반증] 자가 검증으로 오류를 감지할 수 있다 | ❌ 기각 (0/15 감지) | Exp03 |
| **H3** | [Role 외부화] 교차 검증(역할 분리)이 오류를 감지할 수 있다 | ✅ 채택 (12/15, 80%) | Exp035 |
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ⚠ 조건부 채택 (synthesis 카테고리 한정, Stage 2C 2026-05-02) — 15-task 확대 ablation 결과 ABC > Solo-budget +0.0444 (Exp06 9-task subset 의 Solo +0.067 와 방향 반전), synthesis +0.140 (회복 핵심); n=15 검정력 미달, Cohen d=0.449 medium. 상세: `docs/reference/h4-recheck-analysis-2026-05-02.md` | Exp06 + Stage 2C |
| **H5** | [Orchestrator 상한 효과] MAX_CYCLES 상향이 정답률 향상에 기여한다 | ⚠️ 부분 기각 — 포화점은 상한이 아니라 actual_cycles ≈ 7 | Exp07 |
| **H6** | [Role 외부화 정교화] Phase별 특화 프롬프트가 baseline보다 우수하다 | ✅ 조건부 채택 (장기 루프 +5~6%p) | Exp07 |
| **H7** | [Tool 외부화] 외부 수학 도구가 E4B의 계산 한계를 보완한다 | ✅ 채택 (+18.3%p, math-04 0→80%) | Exp08 |
| **H8** | [Tool 외부화 안정성] 에러 힌트 + Mandatory rules로 tool_neglect와 operator 혼동을 완화한다 | ✅ 채택 (neglect 0%, calculator 100%, math-04 0→100%, +23.3%p) | Exp08b |
| **H9a** | [Tattoo 외부화 — 물리 한계 돌파] ABC+Tattoo(chunked)가 Solo-dump보다 long-context에서 우수하다 | ✅ 채택 (+68.3%p, Large 20K에서 Solo 0% → ABC 100%) | Exp09 |
| **H9b** | [차별성] ABC+Tattoo가 RAG baseline 대비 고유 기여를 가진다 | ⚠️ 미결 (5-trial 통계 검정 비유의 p=0.798; overall Δ=+2.0%p; 3-hop에서만 +20.0%p 차별성; Small Paradox 확인) | Exp09 |
| **H9c** | [에러 모드 차이] ABC의 실패 패턴이 Solo·RAG와 질적으로 다르다 | ✅ 채택 (Solo: format_error 24, RAG: wrong_synthesis 6, ABC: evidence_miss 2 + wrong_synthesis 3) | Exp09 |
| **H10** | [Role 외부화 강화 — Mixed Intelligence] 강한 Judge C (Gemini 2.5 Flash) 가 약한 Proposer/Critic (A/B = Gemma 4 E4B) 의 한계를 보완한다 | ⚠ 미결 (실효적 기각, Exp11 2026-05-03). Δ(mixed − baseline) = −0.0811 (mixed 가 baseline-모두-Gemma 보다 *약함*); Cohen d = −0.316 (small, 음수); 통계 비유의 (n=15, p=0.293); logic 카테고리 catastrophic (−0.275). **정반대 메커니즘 발견**: 강한 Judge 가 약한 모델의 self-discovery chain 을 *방해* (logic-02 case study). 상세: `docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md` | Exp11 |
| **H11** | [Role 외부화 분리/추가 — Extractor Role] 신규 Role (Extractor, 동일 Gemma 모델) 이 task prompt 의 claims/entities 를 사전 추출하여 A→B→C input 에 prefix 주입하면 정확도 향상 | ⚠ 조건부 채택 (양수 방향, 검정력 한계, Exp12 2026-05-04). Δ(ext − baseline) = +0.0500 (Exp11 정반대 양수); Cohen d = +0.323 (small, 양수); 통계 비유의 (n=15, p=0.198). **catastrophic 영역 회복**: logic-02 0.3→0.6 (+0.30), synthesis-05 0.55→1.0 (+0.45). Role 축 *분리/추가* 가 *강화* 보다 안전한 진화 방향 입증. 상세: `docs/reference/exp12-extractor-role-analysis-2026-05-04.md` | Exp12 |

핵심 통찰:
- **모델 능력이 아니라 구조가 성능을 결정한다** — 같은 E4B 모델이 Exp02 v1에서 자율 phase 전이 0%, v2에서 외부 강제 94.4%.
- **자가 검증은 작동하지 않는다** (H2). 역할을 바꾼 비판자(B)가 같은 모델에서 80% 회수 (H3).
- **"채점 데이터 결함"이 실험 결론을 뒤집을 수 있다** — Exp07의 math-04 "50% 정체"는 expected_answer 자체가 제약 위반이었음이 Exp08에서 판명.
- **외부 상태(Tattoo)가 유효 컨텍스트를 물리적으로 확장한다** — Exp09에서 Solo-dump는 Medium/Large에서 완전 전멸(0%), ABC+Tattoo는 Large 20K에서 100%. (H9a)
- **소형 로컬 + ABC 가 폐쇄형 대형 1-call 을 능가한다** — Exp10 의 9-task / 540-trial cost-aware 비교에서 같은 Gemma 4 E4B 가 1-loop 41.3% → 8-loop ABC 78.1% (+37%p, H1 추가 evidence). 동일 ABC 조건이 Gemini 2.5 Flash 1-call 의 59.1% 를 +19%p 능가, 비용 \$0, 시간은 약 20× (8min vs 24s). ABC chain 인프라 4 trial 의 JSON parse fail (early-stop 패턴, 상세는 `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`).
- **확대 task set 에서 H4 회복 — synthesis 카테고리가 핵심** — Stage 2C (2026-05-02) 의 15-task 재검증 결과 ABC > Solo-budget +0.044, **synthesis 카테고리 +0.140 회복 핵심**. 9-task subset 의 Solo +0.067 우위 → 15-task 확대 시 ABC 우위로 방향 반전. 통계 비유의 (n=15 검정력) 단 Cohen d=0.449 medium effect. 추가 task (다관점 종합 task) 가 Role 분리 시너지의 자연 측정 영역. (H4 ⚠ 조건부 채택)
- **강한 Judge 는 약한 모델의 self-discovery 를 *방해* 할 수 있다** — Exp11 (2026-05-03) Mixed Intelligence 결과: Gemini 2.5 Flash 를 Judge C 로 두고 Gemma A/B 와 결합 → **baseline (모두 Gemma) 보다 −0.081 약함** (logic-02 case study: baseline 4/5 trial 이 "105 inconsistent" 자기 발견, mixed 5/5 trial null/keyword 부재). 가설 H10 의 정반대 메커니즘 — Tattoo schema mismatch + cycle 단축 + 추론 chain 단절. **Mixed Intelligence (Role *강화*) 가설 잠정 기각** → Role *분리/추가* (Extractor 같은 신규 Role) 가 framework 의 자연 진화 방향.
- **Role 분리/추가 (Extractor) 는 양수 방향** — Exp12 (2026-05-04) 에서 동일 Gemma 모델로 Extractor Role 을 신규 추가 (claims/entities 사전 추출 → A 의 input prefix). **Δ +0.050 양수** (Exp11 정반대), Cohen d=+0.323 small 양수. **catastrophic 영역 회복** 명확 — logic-02 (Stage 2C/Exp11 의 약점) 0.3→0.6 +0.30, synthesis-05 0.55→1.0 +0.45. 메커니즘 = cycle 1 의 *입력 정리* (A 의 작업 대체가 아니라 보조). H11 ⚠ 조건부 채택. → **Role 축 진화 방향 명확**: 강화 ❌ vs 분리/추가 ✅. Stage 5 다음 후보 = **Reducer Role (Exp13)**.

---

## 4. What's Still Open — 열린 연구 질문

검증 대기 중이거나 미외부화된 축들. 재현·확장 결과는 어떤 규모든 환영합니다.

### 3.1 열린 연구 질문 (Stage 5+ 후보)

- ~~**Exp09 통계 신뢰도 보강**~~ — Phase 1 후속 (2026-04-30) 5-trial 실행 + 분석 완료. 단 trial 4-5 가 Windows 환경 모델 서버 connection refused (`WinError 10061`) 로 인한 **인프라 무효** 발견 (`docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`). H9b verdict 는 3-trial 결과 (Δ=+0.033) 우선 권고 — 단 영문 노트북 Closed 추가만 정책 보존 (재산정 미적용). 닫힘.
- **Small Paradox 해결** — Exp09에서 ABC가 small 태스크에서 RAG보다 약함 (0.67 vs 1.00). chunk 수가 적을 때 cycle iteration이 오버킬 가능성. (Exp13+ 후보)
- **병렬 chunk 순회** — 현재 직렬 chunk 처리를 병렬로 전환 + Tattoo merge 패턴 실험. ABC 시간 비용 절감. (Exp13+ 후보)
- **Stage 5 Role 축 ablation 후 framework 방향 결정** — Exp11/12/13 의 Role 축 3 회 측정 (강화/pre-stage/post-stage) 의 수렴 신호 종합 후 Tool 축 (Search Tool, Exp14 진행 중) 검증.

### 3.2 미외부화 축 (conceptFramework § 9)

| 축 | 현재 상태 | 기여 기회 |
|----|----------|-----------|
| **Extractor Role (pre-stage)** | **Exp12 마감** (2026-05-04) — H11 ⚠ 조건부 채택 (Δ=+0.050, d=+0.323, p=0.198 NS). 양수 방향 관찰, catastrophic 영역 회복 신호 | pre-stage 효과의 cross-model replication |
| **Reducer Role (post-stage)** | **Exp13 마감** (2026-05-05) — H12 ⚠ 미결, 실효적 기각 (Δ=−0.053, d=−0.323, p=0.180 NS). 제안 메커니즘 = abstraction loss; 단 keyword scorer artifact 가능성 분리 불가, LLM-as-judge replication 예정 | scorer-side 검증 (P1-3) + cross-model |
| **Search Tool** | 미구현 — **Exp14 후보** (Role 축 마감 후 Tool 축 우선) | Tool 통합 + Stage 5 SQLite ledger 동기 |
| **Graph Tool** | 미구현 (Exp14+ 후보) | entity/relation 다중 hop traversal |
| **Evidence Tool** | 미구현 | `evidence_ref` resolve API — Tattoo와 결합 쌍 |
| **Critic Tool** | 부분 (`FailureLabel` enum + Stage 2B `failureLabels.md` heuristic 분류만) | JSON schema·citation 결정론적 검증기 강화 |
| ~~**Large Model Tool**~~ | **Exp11 시도 → ⚠ 미결 (실효적 기각, 2026-05-03)** | Sonnet/Opus/Flash escalation 경로 비추천 — 정반대 메커니즘 발견 (강한 Judge 가 약한 모델 self-discovery 방해) |

### 3.3 확장 실험 질문

- **다른 소형 모델에서도 4축 외부화가 같은 효과인가?** — Qwen 2.5 7B, Phi-4, Llama 3.2 3B 등에서 재현.
- **한국어·다국어 scoring 편차** — Exp08 math-03에서 한국어 답변의 v2 keyword 매칭 변동 관찰. 다국어 응답 채점 방침 미정.
- **taskset expected_answer 수학적 검증** — math-04 결함 사례를 볼 때 다른 태스크 정답의 전수 검증 필요.

---

## 5. Who Might Find This Useful

다음과 같은 분에게는 이 레포가 흥미로울 수 있습니다 (적극 모집이 아닌 초대입니다 — 원할 때 fork해서 돌려보시면 됩니다):

- **🧪 다른 모델 보유자** — Qwen/Phi/Llama/Mistral 등 소형 모델을 돌려볼 수 있는 분. 재현 결과 자체가 의미 있음. *[난이도: 낮음]*
- **🛠️ 프롬프트·툴 엔지니어** — 새 Tool(Search/Graph/Evidence) 또는 새 Role(Extractor/Reducer) 구현·평가에 관심 있는 분. *[난이도: 중]*
- **🌐 다국어·도메인 전문가** — 한국어·일본어·의료·법률 태스크로 확장, scoring 다국어 이슈 해결에 관심 있는 분. *[난이도: 중]*
- **📐 RAG/벡터DB 경험자** — Search Tool이나 외부 지식 환경 통합 설계에 관심 있는 분. *[난이도: 중~높음]*
- **📊 ML 연구자** — 실패 모드 분석, 통계적 유의성 검증, ablation 설계에 관심 있는 분. *[난이도: 높음]*

---

## 6. Quickstart (10 minutes)

### 환경 준비
```bash
git clone https://github.com/hang-in/gemento.git
cd gemento
python3.14 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 추론 서버 연결
`experiments/config.py`의 `API_BASE_URL`을 llama.cpp 서버 주소로 설정(OpenAI 호환 `/v1/chat/completions` + `tool_calls` 지원 필요). 로컬이면 `http://localhost:8080`.

```bash
# 서버 헬스 체크
curl -s $API_BASE_URL/v1/models | jq .data[].id
# 기대: "gemma4-e4b" 또는 본인이 로드한 모델 id
```

### Smoke test (실제 tool round-trip 검증)
```bash
cd experiments
python tools/smoke_test.py
# 기대: "SMOKE TEST PASSED: math-04 answer=..., tool_calls=..."
```

### 첫 실험 실행
```bash
# 가장 짧은 실험 (baseline, 약 2-3분)
python run_experiment.py baseline

# 가장 흥미로운 실험 (tool-use, 약 1-2시간)
python run_experiment.py tool-use
python measure.py "results/exp08_*.json" --markdown --output results/exp08_report.md
```

모든 실험은 체크포인트 지원 — 중단 후 재실행 시 `partial_*.json`에서 자동으로 이어갑니다.

---

## 7. Reproduce / Extend

### (a) 다른 모델로 실험
`experiments/config.py`에서 2줄만 변경:
```python
MODEL_NAME = "qwen2.5-7b-instruct"  # 또는 phi-4, llama-3.2-3b, ...
API_BASE_URL = "http://localhost:8080"
```
llama.cpp 서버가 tool_calls를 지원해야 함 (`/props` 응답의 `chat_template_caps.supports_tools: true` 확인). 같은 실험 명령 (`python run_experiment.py tool-use`)으로 비교 가능.

### (b) 새 Tool 추가
`experiments/tools/math_tools.py` 패턴을 따라 `experiments/tools/{your_tool}.py`에 순수 함수 + OpenAI schema 정의. `experiments/tools/__init__.py`의 `TOOL_FUNCTIONS`, `TOOL_SCHEMAS`에 등록. 예시:

```python
def search_tool(query: str, limit: int = 10) -> list[dict]:
    """BM25/vector hybrid search over your knowledge base."""
    ...

TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "search_tool",
        "parameters": {...},
    },
})
TOOL_FUNCTIONS["search_tool"] = search_tool
```

### (c) 새 Role 추가
`experiments/system_prompt.py`의 `SYSTEM_PROMPT` / `CRITIC_PROMPT` / `JUDGE_PROMPT` 패턴을 따라 새 역할 프롬프트 추가. `experiments/orchestrator.py:run_abc_chain`을 참고해 호출 순서 확장.

### (d) 새 태스크셋
`experiments/tasks/taskset.json`에 항목 추가. 필수 필드: `id`, `category`, `difficulty`, `prompt`, `expected_answer`, `scoring_keywords`. **주의**: 수학 문제의 경우 expected_answer의 제약 조건 위반 여부를 직접 풀어 검증할 것 (math-04 결함 교훈).

---

## 8. Roadmap

| 시점 | 항목 | 상태 |
|------|------|------|
| Phase 1 (마감) | Exp00~Exp10 — 4축 외부화 baseline + cost-aware (Exp10) | ✅ |
| Phase 1 후속 (마감, 2026-04-30) | Taskset 3 FAIL 정정 + Exp09 5-trial drop 분석 + Exp10 v3 재산정 | ✅ |
| Stage 2A/2B (마감, 2026-04-30) | 인프라 안정화 (healthcheck/abort + 결과 JSON meta v1.0) + scorer/failure label reference | ✅ |
| Stage 2C (마감, 2026-05-02) | Exp06 H4 재검증 (확대 task set 15) — H4 ⚠ 조건부 채택 (synthesis +0.140) | ✅ |
| Stage 4 (마감, 2026-05-03) | Exp11 Mixed Intelligence (Flash Judge) — H10 ⚠ 미결 (실효적 기각). 정반대 메커니즘 발견 | ✅ |
| Stage 5 Exp12 (마감, 2026-05-04) | Extractor Role (pre-stage) — H11 ⚠ 조건부 채택 (Δ=+0.050, d=+0.323, p=0.198 NS). 양수 방향성 관찰 | ✅ |
| Stage 5 Exp13 (마감, 2026-05-05) | Reducer Role (post-stage) — H12 ⚠ 미결, 실효적 기각 (Δ=−0.053, d=−0.323, p=0.180 NS). **거울상 effect size 의 position effect 일관 증거**; cross-model + LLM-as-judge replication 예정 | ✅ |
| **Stage 5 Exp14 진행 중** | **Search Tool** (Tool 축 신규) — agent-active retrieval. Role 축 H10/H11/H12 의 수렴 신호 후 Tool 축 검증 (결정성 외부화 후보) | 🔄 |
| 중기 | 미외부화 축 보강 — Search Tool / Graph Tool / Evidence Tool 통합. Stage 5 SQLite ledger 동기 | |
| 중장기 | 외부 지식 환경 (4-layer) 통합 실험 (벡터·그래프 사용) | |
| 장기 | 크로스 모델 재현 (Qwen / Phi / Llama) · 체계적 ablation · 연구 결과 정리 (technical report / blog) | |

상세 이력·다음 질문: [docs/reference/researchNotebook.md](docs/reference/researchNotebook.md)의 "현재 상태 및 다음 단계" 섹션 + [docs/plans/index.md](docs/plans/index.md) 의 Active/Recently Done.

---

## 9. How to Contribute

### Contribution ladder (쉬운 것부터)

| 난이도 | 예시 | 기여 형태 |
|--------|------|----------|
| ⭐ 5분 | 오탈자·문서 개선 | PR |
| ⭐⭐ 수 시간 | 기존 실험을 다른 모델로 재현 → 결과 공유 | Issue (Reproduction) |
| ⭐⭐⭐ 수 일 | 새 Tool 1개 구현 + 단위 테스트 + 통합 실험 | PR + 결과 리포트 |
| ⭐⭐⭐⭐ 수 주 | 새 Role(Extractor/Reducer) 설계·구현·평가 | PR + 연구 노트 섹션 |
| ⭐⭐⭐⭐⭐ 수 개월 | Long-context stress / cross-model 체계적 ablation | Acknowledgements 상단 + research write-up 공동 저자(해당 시) |

### 기여 프로세스

1. **Issue로 의사 표시** — "I'll try reproducing Exp08 with Qwen 2.5 7B" 같은 한 줄이면 충분. 중복 방지용.
2. **Fork & 실험** — 결과는 본인 fork의 `experiments/results/` 또는 별도 gist로 공유.
3. **PR 또는 결과 공유** — 코드 기여면 PR, 재현 결과만이면 Issue 댓글도 OK.

### Credit 정책

- **⭐⭐⭐⭐⭐ 기여** (새 축 외부화, 체계적 ablation) → **Acknowledgements 상단 + research write-up 공동 저자 (해당 시)**
- **⭐⭐⭐ 이상 기여** (Tool/Role 구현, cross-model 재현) → **Acknowledgements + CONTRIBUTORS.md 명단**
- **⭐~⭐⭐ 기여** → **GitHub contributor 자동 반영**

제멘토는 *현재 1인 연구 노트*이며 체계적 연구 커뮤니티는 아닙니다. 어떤 기여가 들어오든 실험 결과·문서에 기여자 이름이 명시됩니다. 레포가 성숙하고 체계적 연구로 발전하면 그때 공동 저작 가능성도 열립니다.

---

## 10. Docs Map

### Canonical reference
| 경로 | 내용 |
|------|------|
| [docs/reference/conceptFramework.md](docs/reference/conceptFramework.md) | **4축 외부화 프레임** — canonical 개념 문서 (§8 매트릭스 Exp00~Exp12) |
| [docs/reference/researchNotebook.md](docs/reference/researchNotebook.md) | **메인 연구 노트** — 모든 실험 6하원칙 기록 + H1~H10 가설 판정 |
| [docs/reference/researchNotebook.en.md](docs/reference/researchNotebook.en.md) | 영문 mirror (Closed Findings 추가만 정책) |
| [docs/reference/namingConventions.md](docs/reference/namingConventions.md) | 표기/용어 규약 (Stage NX, task-NN, condition slug 등) |
| [docs/reference/scoringHistory.md](docs/reference/scoringHistory.md) | 채점기 변천 (v0/v2/v3) |
| [docs/reference/failureLabels.md](docs/reference/failureLabels.md) | `FailureLabel` enum + 실패 분류 표준 |
| [docs/reference/resultJsonSchema.md](docs/reference/resultJsonSchema.md) | 결과 JSON top-level meta v1.0 |
| [docs/reference/index.md](docs/reference/index.md) | reference 전체 인덱스 |

### 실험 결과 + 분석 보고서
| 경로 | 내용 |
|------|------|
| [docs/reference/results/](docs/reference/results/) | 실험별 result.md (exp-00 ~ exp-13) |
| [docs/reference/h4-recheck-analysis-2026-05-02.md](docs/reference/h4-recheck-analysis-2026-05-02.md) | Stage 2C H4 재검증 분석 (15-task ablation) |
| [docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md](docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md) | Exp11 Mixed Intelligence 분석 (H10 verdict) |
| [docs/reference/exp12-extractor-role-analysis-2026-05-04.md](docs/reference/exp12-extractor-role-analysis-2026-05-04.md) | Exp12 Extractor Role 분석 (H11 verdict) |
| [docs/reference/exp13-reducer-role-analysis-2026-05-05.md](docs/reference/exp13-reducer-role-analysis-2026-05-05.md) | Exp13 Reducer Role 분석 (H12 verdict) |
| [docs/reference/exp09-5trial-drop-analysis-2026-04-30.md](docs/reference/exp09-5trial-drop-analysis-2026-04-30.md) | Exp09 5-trial 점수 하락 원인 분석 |

### 작업 진행
| 경로 | 내용 |
|------|------|
| [docs/plans/index.md](docs/plans/index.md) | Active / Recently Done plan 인덱스 |
| [docs/plans/](docs/plans/) | 각 실험 / Stage plan + subtask + review 기록 |
| [docs/reference/handoff-to-*.md](docs/reference/) | 과거 핸드오프 (대부분 archived) |
| [docs/agents/](docs/agents/) | Architect / Developer / Reviewer 역할 정의 |
| [docs/agentSessionHistory.md](docs/agentSessionHistory.md) | 멀티에이전트 세션 history |

### 코드 (gemento/experiments/)
| 경로 | 내용 |
|------|------|
| `experiments/schema.py` | Tattoo 스키마 (Assertion, Phase, Handoff*, `FailureLabel`) |
| `experiments/system_prompt.py` | A / B / C / Extractor 역할별 system prompt |
| `experiments/orchestrator.py` | `call_model` (tool_calls loop), `run_abc_chain` (c_caller + extractor_pre_stage hook) |
| `experiments/run_helpers.py` | Stage 2A — healthcheck/abort + 결과 JSON meta v1.0 helper |
| `experiments/measure.py` | 채점 (v0/v2/v3 — `negative_patterns` 적용) |
| `experiments/tools/math_tools.py` | calculator / solve_linear_system / linprog |
| `experiments/_external/gemini_client.py` | Gemini 2.5 Flash 호출 + cost meter (Exp10/Exp11 사용) |

---

## 11. Related Work — 인접 흐름

"LLM 의 인지를 외부화한다" 는 framing 자체는 본 프로젝트 고유가 아니다. 인접하거나 겹치는 아이디어:

- **Externalization in LLM Agents** (Zhou et al., 2026)¹ — 4축 외부화 (memory / skills / protocols / harness engineering) 를 통합 review 한 preprint. 제멘토는 secall / tunaFlow 를 만들면서 마주친 실제 컨텍스트·기억 문제에서 출발해 독립적으로 개발됨 — 저자는 위 preprint 를 나중에 알게 됨. 4축 분리 (Tattoo / Tools / Role / Orchestrator) 는 그 흐름의 **independent convergence (독립적 수렴)** 으로 읽는 것이 정확하며, 그로부터 도출된 것이 아니다. 축 매핑은 다름 (제멘토는 Role 과 Orchestrator 를 명시적으로 분리, Zhou et al. 은 control 을 harness engineering 에 통합).
- **LightMem** (Fang et al., 2026)² — 3-stage 메모리 (sensory / short-term / long-term, sleep-time consolidation) 의 lightweight memory-augmented generation. 세션 간 장기 retrieval 중심. 제멘토는 loop 간 *working state* 에 가까우며, 과거 세션 retrieval 이 아니다.
- **StateFlow** (Wu et al., 2024)³ — 복잡한 task-solving 을 state machine 으로 conceptualize, control flow 를 LLM 외부로 빼냄. 제멘토의 Orchestrator 축과 개념적 인접; 제멘토는 그 위에 명시적 역할 분리 (A/B/C) + Tattoo schema 를 추가.
- **Chain-of-Agents** (Zhang et al., 2024)⁴ — 긴 입력을 여러 worker agent 가 segment 처리 + manager 가 종합. 제멘토의 A→B→C 파이프라인이 구조를 공유하지만, *동일 base model* 을 모든 역할에 사용하고 prompt + validation contract 로만 분리.

기여한 것 / **기여하지 않은** 것:

- 기여: Gemma 4 E4B (실효 4B 파라미터) 의 4축에서의 행동을 측정한 workbook, 재현 가능한 수치와 sampling parameters 동반.
- 비기여: 새로운 architecture, 새로운 학습 방법, 소형 LLM 이 대형을 대체한다는 주장. 제멘토는 unmodified open-weight 모델 위의 구조적 workflow 하네스.

---
¹ Zhou, C., Chai, H., Chen, W., et al. (2026). *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering*. [arXiv:2604.08224](https://arxiv.org/abs/2604.08224).
² Fang, J., Deng, X., Xu, H., et al. (2026). *LightMem: Lightweight and Efficient Memory-Augmented Generation*. ICLR 2026. [arXiv:2510.18866](https://arxiv.org/abs/2510.18866).
³ Wu, Y., et al. (2024). *StateFlow: Enhancing LLM Task-Solving through State-Driven Workflows*. [arXiv:2403.11322](https://arxiv.org/abs/2403.11322).
⁴ Zhang, Y., Sun, R., Chen, Y., Pfister, T., Zhang, R., Arik, S. Ö. (2024). *Chain of Agents: Large Language Models Collaborating on Long-Context Tasks*. NeurIPS 2024. [arXiv:2406.02818](https://arxiv.org/abs/2406.02818).

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — 외부 메모 보조의 원형 메타포. 4축 외부화의 직관적 모델이 됨.
- secall · tunaflow — 본 연구의 실제 출발점. 거기서 마주친 컨텍스트·기억 문제가 제멘토 설계의 토대가 됐다.

---

## 12. License
[MIT](./LICENSE) — 자유롭게 fork·수정·재배포·상업 사용 가능. 저작권 고지만 유지해주세요.

---

**질문·제안·기여**: GitHub Issues 또는 Discussions(활성화 예정). 연구 결과 공유는 언제든 환영합니다.
