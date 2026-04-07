---
type: result
status: pending
updated_at: 2026-04-08
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
| 실행일 | — |

## 결과

| Cap | 성공률 | 평균시간(ms) | 추론 정확도 |
|-----|--------|-------------|-----------|
| — | — | — | — |

## 변곡점 분석

- (실험 실행 후 기록)

## 배치 순서 효과

- (lost-in-the-middle 영향 분석)

## 결론

- 확정된 soft cap: —
- 배치 전략: —

## 다음 단계

- 확정된 soft cap을 config.py에 반영
- 실험 2에서 이 값을 사용
