---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# 채점 시스템 변천 (Scoring History)

> `experiments/measure.py` 의 score_answer 함수 변천 + 적용 범위 단일 reference.
> 본 reference 는 도입 시점 / 동기 / 적용 범위 / 변천 영향만 정리. 알고리즘 상세는 `measure.py` 직접 참조.

## 1. 변천 요약

| 버전 | 도입 시점 | 핵심 변화 | 적용 범위 (canonical) |
|------|----------|-----------|----------------------|
| **v0** (substring) | 2026-04-08 (Exp00 동시) | expected_answer 가 응답에 substring 으로 포함되는지 | Exp00 ~ Exp045 의 원본 채점 (사후 v2 재채점 적용 시 v0 기록 보존) |
| **v2** (keyword group) | 2026-04-15 (Exp06 시점) | scoring_keywords 의 group 별 핵심 값이 모두 포함되는지 (group AND, 항목 OR) | Exp06+ 의 원본 채점, Exp00 ~ Exp045 의 재채점, Exp08+ 의 ground truth |
| **v3** (negative_patterns) | 2026-04-29 (Exp10 v3 rescore plan) | v2 + task 별 `negative_patterns` 차단 + 옵션 `conclusion_required` | Exp10 v3 rescore (`exp10_v3_rescored_*.json`), Stage 2C exp_h4_recheck (예정), Exp11+ (예정) |

## 2. v0 → v2 전환 동기

- v0 의 false negative — 긴 문장 / 포맷 차이 / 설명 삽입 시 expected_answer substring 매칭 실패. 모델 능력 측정 정확도 훼손
- Exp06 의 채점 비교 신뢰성 회복 시점에 v2 도입. group 별 핵심 keyword 매칭으로 표현 다양성 흡수
- 전체 재채점 결과 (researchNotebook §"채점 시스템 변천" 표):

| 실험 | v0 | v2 | Δ |
|------|-----|-----|-----|
| Exp00 Baseline | 0.705 | 0.722 | +1.7% |
| Exp02 Multiloop | 0.369 | 0.438 | +6.9% |
| Exp04 ABC Pipeline | 0.607 | 0.583 | -2.3% |
| Exp05a Prompt Enhance | 0.636 | 0.583 | -5.2% |
| Exp045 Handoff | 0.649 | 0.900 | +25.1% |
| Exp06 Solo Budget | 0.663 | 0.967 | +30.3% |

→ Exp045 / Exp06 의 큰 향상은 v0 의 substring 매칭 한계 (Handoff Protocol 의 정교한 답변 형식). Exp04 / Exp05a 의 음수 Δ 는 v2 의 keyword group 의 엄격성 (예: synthesis-01 의 `'only'` 누락 — Phase 1 후속 진단).

## 3. v2 의 한계 — v3 도입 동기

Exp10 v2 final (2026-04-28) 채점에서 logic-04 의 false positive 발견:
- v2 keyword `[["casey"]]` 가 본문에 'Casey' 등장 시 1.0 부여
- 그러나 본문이 "all four suspects... lead to contradictions" / "no single suspect can be identified" / "puzzle is logically inconsistent" 같은 reject 류 결론
- gemma_8loop logic-04: v2 0.400 (8/20) but v3 strict 0.050 (1/20) — 7건 false positive
- gemini_flash logic-04: v2 0.250 → v3 0.000 — 5건 false positive

v3 patch (`exp10-readme-v2-abc-4-fail-v3-disclosure` plan, 2026-04-29):
- `score_answer_v3` 신규 — v2 keyword 매칭 + `negative_patterns` 차단 + 옵션 `conclusion_required`
- `taskset.json` 의 `logic-04` 에 `negative_patterns` 4개 추가:
  - `no\s+(unique|definitive|clear)\s+(culprit|answer|solution)`
  - `cannot\s+be\s+(identified|determined|solved)`
  - `contradicts?|contradiction|contradictions`
  - `puzzle\s+is\s+(flawed|inconsistent|ill-?posed)`

## 4. v3 의 적용 범위

- **Exp10 v3 rescore**: 540 trial 전수 재산정. 결과 JSON 의 각 trial 에 `accuracy_v2` (보존) + `accuracy_v3` (신규) 두 필드. canonical = `exp10_v3_rescored_<TS>.json` (직전 053939 / 본 plan 의 152306)
- **다른 실험 (Exp00~09) retroactive 적용 0**: logic-04 task 가 Exp00~09 result JSON 에 미포함 (정찰 grep 확인). v3 적용 시 변동 0 예상 — 별도 재산정 plan 우선순위 낮음
- **Stage 2C exp_h4_recheck (예정)**: 신규 도구라 v3 채점 적용 (`measure.py:score_answer_v3` 호출)
- **Stage 4 Exp11+ (예정)**: v3 default

## 5. v4 도입 검토 — 본 plan 영역 외

v4 후보:
- LLM-judge 도입 (의미적 일관성 판단)
- `evidence_ref` 정합성 검증 (Critic Tool)
- 다국어 keyword 매칭 (한·영 / 일본어 등)

→ 모두 별도 plan 후보. **본 plan (Stage 2B) 영역 외**. 사용자 합의 "작은 B" 전략 — score_answer_v4 명시 배제.

## 6. 변천 정책

- **재채점 시점**: v0 → v2 / v2 → v3 모두 *전수 재채점 결과를 새 파일* 로 보존. 기존 결과 JSON 변경 0 (immutability)
- **Disclosure**: 새 채점 도입 시 result.md / researchNotebook 한·영 갱신 의무. 영문 노트북은 Closed 추가만 (기존 수치 변경 0)
- **다음 도입 후보 결정**: Architect / 사용자 합의 후. 본 reference 갱신 의무

## 7. 관련 코드

- `experiments/measure.py:score_answer_v0` (legacy, 보존)
- `experiments/measure.py:score_answer_v2` (default for Exp06+)
- `experiments/measure.py:score_answer_v3` (Exp10 v3, Stage 2C+ 예정)
- `experiments/tasks/taskset.json` 의 `negative_patterns` (logic-04 적용)

## 8. 변경 이력

- 2026-04-30 v1: 초안. Stage 2B (`scorer-failure-label-reference`) plan 의 task-01 결과. 분산된 변천 기록 단일화.
