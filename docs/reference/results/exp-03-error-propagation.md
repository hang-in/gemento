---
type: result
status: pending
updated_at: 2026-04-08
experiment: 실험 3 — 오류 전파와 자기 교정
branch: exp/03-error-propagation
---

# 실험 3 결과: 오류 전파와 자기 교정

## 핵심 가설

> **H2:** 문신에 결함이 존재하면, 오류는 루프 진행에 따라 감쇠되지 않고 증폭된다.

## 실행 정보

| 항목 | 값 |
|------|-----|
| 모델 | gemma4:e4b (Q4_K_M) |
| 결함 유형 | corrupt_content, inflate_confidence, contradiction |
| 주입 시점 | Loop 2, Loop 4 |
| 실행일 | — |

## 결과

| 결함유형 | 평균 Error Half-life | 감지율 | 최종신뢰도 |
|---------|---------------------|--------|----------|
| — | — | — | — |

## 핵심 메트릭

- contamination_ratio: —
- self_correction_rate: —

## 가설 판정

- H2 채택/기각: —

## 방어 메커니즘 필요도

- self_correction_rate > 0.5 → 모델 자체 감지 가능
- self_correction_rate < 0.2 → 오케스트레이터 보호 필수

## 다음 단계

- (결과에 따른 방어 설계)
