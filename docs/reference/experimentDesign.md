---
type: reference
status: archived
updated_at: 2026-05-03
archived_at: 2026-05-03
superseded_by: docs/reference/conceptFramework.md + docs/reference/researchNotebook.md
canonical: false
---

# 제멘토 실험 설계서 (DEPRECATED)

> ⚠ **DEPRECATED (2026-05-03)** — 본 문서는 **실험 0~4 시점 (2026-04-08)** 의 초기 설계서로,
> 이후 framework 진화 (Exp00~Exp12, 4축 외부화, Stage 2C H4 재검증, Exp11 Mixed Intelligence,
> Exp12 Extractor) 가 대규모로 진행되어 더 이상 framework 의 현재 상태를 반영하지 못합니다.
>
> **현재 framework 의 canonical reference**:
> - **개념 프레임 + 4축 외부화**: [`docs/reference/conceptFramework.md`](./conceptFramework.md)
> - **모든 실험 + 가설 판정**: [`docs/reference/researchNotebook.md`](./researchNotebook.md) (한국어)
>   / [`docs/reference/researchNotebook.en.md`](./researchNotebook.en.md) (영문 mirror, Closed 추가만)
> - **표기 / 용어 규약**: [`docs/reference/namingConventions.md`](./namingConventions.md)
> - **각 실험 결과**: `docs/reference/results/exp-XX-*.md`
>
> 본 문서는 historical record 로 보존하며, 새 plan / 분석 작성 시 **참조 금지**.
> 실험 0~4 의 *초기 의도* 만 review 시 참고 가능.

---

## 1. 실험 목적

제멘토의 핵심 가설을 검증한다:

> **가설 H1:** 동일한 소형 LLM(Gemma 4 E4B) + 구조화된 문신 스키마에서,
> 추론 단계를 증가시킬 때 단일 추론 대비 통계적으로 유의미한 품질 개선이 발생한다.

> **가설 H2:** 문신에 결함이 존재하면, 오류는 루프 진행에 따라 감쇠되지 않고 증폭된다.

## 2. 모델 제약

| 항목 | 값 |
|------|-----|
| 모델 | Gemma 4 E4B (`gemma4:e4b`) |
| 양자화 | Q4_K_M |
| 유효 파라미터 | 4.5B (8B 총) |
| 컨텍스트 윈도우 | 131,072 토큰 |
| Sliding window | 512 토큰 |
| Capabilities | completion, vision, audio, tools, thinking |
| 실행 환경 | Ollama (로컬) |

## 3. RT 토론 결론 (실험 전제)

### 문신 선택
- Assertion 상한: Soft cap 8 / Hard cap 10
- 1차 게이트: 토큰 예산 기반
- 선택 주체: 규칙 기반 (오케스트레이터)
- 압축: v0 제외

### 외부 도구 통합
- 호출 방식: 하이브리드 (LLM 요청 → 오케스트레이터 실행 → 결과 반환)
- 도구 결과 신뢰도: 승격 기준 통과 필수
- 루프 관계: 실험 4에서 결정

## 4. 실험 목록

### 실험 0: 기준선 (Baseline)

**목적:** 문신 없이 Gemma 4 E4B의 단일 추론 품질 측정

**설계:**
- 입력: 질문 + 필요 정보 (문신 구조 없음)
- 출력: 답변
- 반복: 태스크셋 전체 × 3회 (분산 측정)

**측정:**
- 정확도 (태스크별 정의)
- 응답 토큰 수
- 추론 시간

**산출물:** 태스크별 baseline 점수

---

### 실험 1: Assertion 상한과 추론 품질

**목적:** assertion 수 증가 시 추론 품질 변곡점 탐색

**설계:**
- 고정: 동일 질문, 동일 goal, 동일 시스템 프롬프트
- 독립변수: assertion 수 = {2, 4, 6, 8, 10, 12}
- 각 assertion은 사전 작성된 "정답 assertion" 사용
- 반복: 태스크 × assertion 수 × 3회

**측정:**
- 추론 정확도 (assertion 내용 올바르게 활용했는가)
- assertion 참조율 (실제 사용한 assertion 수 / 제공된 수)
- 배치 순서 효과 (중요 assertion 앞배치 vs 뒤배치)

**판정 기준:**
- 품질이 정체/하락하는 변곡점 → 실제 soft cap 확정
- 배치 순서에 따른 유의미한 차이 → lost-in-the-middle 확인

**브랜치:** `exp/01-assertion-cap`

---

### 실험 2: 다단계 루프 품질 누적

**목적:** 제멘토 핵심 가설 H1 검증

**설계:**
- 태스크: 다단계 추론 필요 문제 (수학, 논리, 정보 종합)
- 비교군:
  - A: 단일 추론 (baseline, 실험 0)
  - B: 2 루프
  - C: 4 루프
  - D: 8 루프
- 고정: 문신 스키마, soft cap (실험 1 결과 반영), 규칙 기반 선택

**측정:**
- 최종 답변 정확도 (baseline 대비 delta)
- 루프별 assertion 증가 곡선
- 루프별 confidence 추이
- 수렴까지 걸린 루프 수

**판정 기준:**
- Quality_gain > 0 이고 p < 0.05 → H1 채택
- Quality_gain ≤ 0 → H1 기각, 설계 재검토

**브랜치:** `exp/02-multiloop-quality`

---

### 실험 3: 오류 전파와 자기 교정

**목적:** 가설 H2 검증 + 방어 메커니즘 필요도 판단

**설계:**
- 기본 체인: 실험 2의 정상 루프 체인
- 결함 주입 유형:
  - Type A: assertion 내용 미세 오염 (숫자/조건 변경)
  - Type B: confidence 부풀림 (0.5 → 0.9)
  - Type C: 모순 assertion 삽입
- 주입 시점: Loop 2, Loop 4

**측정:**
- contamination_ratio: 오염 assertion에서 파생된 assertion 비율
- error_half_life: confidence가 0.5 이하로 떨어지는 루프 수
- self_correction_rate: 시스템이 오류를 스스로 invalidate한 비율

**판정 기준:**
- self_correction_rate > 0.5 → 4.5B가 오류 감지 가능
- self_correction_rate < 0.2 → 오케스트레이터 레벨 보호 필수

**브랜치:** `exp/03-error-propagation`

---

### 실험 4: 도구 호출과 루프 분리

**목적:** 도구 호출을 같은 루프에서 처리할지, 분리할지 결정

**설계:**
- 태스크: 외부 정보 필요 질문 (계산, 검색 시뮬레이션)
- 비교군:
  - A: 단일 루프 (도구 호출 + 결과 해석 + 추론)
  - B: 분리 루프 (루프 N: 도구 요청 → 루프 N+1: 결과 해석)

**측정:**
- 도구 결과 활용 정확도
- 추론 품질 (baseline 대비)
- 총 소요 루프 수

**판정 기준:**
- A와 B의 품질 차이 < 5% → 단일 루프 채택 (효율)
- A와 B의 품질 차이 ≥ 5% → 분리 루프 채택 (품질)

**브랜치:** `exp/04-tool-loop-separation`

---

## 5. 실험 순서와 의존성

```
실험 0 (baseline)
  │
  ▼
실험 1 (assertion cap) ──→ soft cap 수치 확정
  │
  ▼
실험 2 (multiloop) ──→ H1 검증/기각
  │
  ├──→ 실험 3 (error propagation) ──→ H2 검증 + 방어 필요도
  └──→ 실험 4 (tool separation) ──→ 도구 통합 방식 확정
```

실험 3, 4는 실험 2 이후 병렬 실행 가능.

## 6. 실험 인프라

```
experiments/
├── config.py          # 모델/실험 설정
├── schema.py          # 문신 스키마 정의
├── orchestrator.py    # 루프 실행 엔진
├── system_prompt.py   # LLM용 시스템 프롬프트
├── tasks/
│   └── taskset.json   # 평가 태스크셋
├── measure.py         # 측정/채점 스크립트
├── run_experiment.py  # 실험 실행 진입점
└── results/           # 실험 결과 저장 (gitignore 대상 아님)
    └── .gitkeep
```

## 7. 결과 문서화

각 실험 완료 후:
1. `docs/reference/results/exp-{N}-{slug}.md` 에 최종 결과 기록
2. `docs/reference/experimentDesign.md` (이 문서)에 상태 업데이트
3. 확정된 수치는 `docs/reference/` 관련 문서에 반영

## 8. 브랜치 전략

| 브랜치 | 실험 | 의존성 |
|--------|------|--------|
| `main` | — | 실험 인프라, 설계 문서 |
| `exp/00-baseline` | 실험 0 | — |
| `exp/01-assertion-cap` | 실험 1 | 실험 0 결과 |
| `exp/02-multiloop-quality` | 실험 2 | 실험 1 결과 |
| `exp/03-error-propagation` | 실험 3 | 실험 2 결과 |
| `exp/04-tool-loop-separation` | 실험 4 | 실험 2 결과 |

각 브랜치에서 실험 실행 → 결과 기록 → main으로 결과 문서만 머지.
