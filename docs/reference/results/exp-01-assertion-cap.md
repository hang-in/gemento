---
type: result
status: done
updated_at: 2026-04-09
experiment: 실험 1 — Assertion 상한
branch: exp/01-assertion-cap
---

# 실험 1 결과: Assertion 상한과 추론 품질

## 실행 정보

| 항목 | 값 |
|------|-----|
| 모델 | gemma4:e4b (Q4_K_M) |
| Cap 변수 | 2, 4, 6, 8, 10, 12 |
| 반복 횟수 | 3 |
| 유효 실행 | exp01_assertion_cap_20260408_170400.json |
| 실행일 | 2026-04-08 |

## 결과

| Cap | JSON 응답 성공률 | 비고 |
|-----|-----------------|------|
| 2 | 100% | |
| 4 | 100% | |
| 6 | 100% | |
| 8 | 100% | |
| 10 | 100% | |
| 12 | 100% | |

## 관찰

- 모든 cap에서 JSON 파싱 성공률 100%
- E4B는 assertion 12개까지 안정적으로 읽고 구조화된 JSON 출력 생성
- assertion 수 증가에 따라 응답 시간 선형 증가 (assertion당 ~1초)
- 정확도 변곡점은 이 실험에서 측정 불가 (SYNTHESIZE phase 단일 루프 설계)

## 결론

- **E4B는 문신을 읽을 수 있다** — 핵심 전제 확인
- RT 토론 결론(soft cap 8 / hard cap 10)을 변경할 근거 없음 — 유지
- lost-in-the-middle 효과는 관찰되지 않음 (12개까지 안정)
