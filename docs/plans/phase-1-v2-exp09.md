---
type: plan
status: in_progress
updated_at: 2026-04-29
title: "Phase 1 측정 기반 보강 — v2 역행 분석 + Exp09 통계 검정"
slug: phase-1-v2-exp09
version: 1
---

# Phase 1: 측정 기반 보강 — v2 역행 분석 + Exp09 통계 검정

## 1. 배경

Exp06 H4 reconciliation(선행 플랜) 과정에서 채점 인프라의 두 가지 미결 이슈가 드러남:

1. **v2 역행**: Exp04(Δ=-2.3%), Exp05a(Δ=-5.2%)에서 v2 < v1. 다른 실험(Exp00, Exp02, Exp045, Exp06)에선 v2 ≥ v1이므로 일반적 결함은 아니나 원인 미규명.
2. **Exp09 통계 부재**: H9b(+3.3%p)가 3 trial × 10 task = 30 데이터포인트/arm으로 통계 검정 없이 "조건부 채택"됨.

이 플랜은 C(채점 인프라) + B1(Exp09 통계 보강)을 하나의 Phase로 묶어 측정 정확도를 확보한다.

## 2. 정합 비교 데이터 (정찰 결과)

### v1↔v2 전 실험 비교

| Experiment | v1 | v2 | Δ | 비고 |
|------------|-----|-----|-----|------|
| Exp00 Baseline | 0.705 | 0.722 | +1.7% | 정상 |
| Exp02 Multiloop | 0.369 | 0.438 | +6.9% | 정상 |
| **Exp04 ABC** | **0.607** | **0.583** | **-2.3%** | 역행 |
| **Exp05a Prompt** | **0.636** | **0.583** | **-5.2%** | 역행 |
| Exp045 Handoff | 0.649 | 0.900 | +25.1% | 정상 |
| Exp06 Solo | 0.663 | 0.967 | +30.3% | 정상 |

### Exp09 H9b 현황

| 조건 | abc_tattoo | rag_baseline | Δ(abc−rag) |
|------|-----------|-------------|-----------|
| 전체 | ~86.7% | ~83.3% | +3.3%p |
| 3-hop | 100% | 67% | +33%p |
| small | 67% | 100% | -33%p (Small Paradox) |

## 3. Subtask 요약

| # | 제목 | 유형 | parallel_group | depends_on |
|---|------|------|---------------|------------|
| 1 | v2 역행 진단 스크립트 | C | A | — |
| 2 | taskset expected_answer 전수 검증 | C | A | — |
| 3 | Exp09 추가 trial 실행 | B1 | A | — |
| 4 | Exp09 통계 검정 스크립트 | B1 | B | 3 |
| 5 | 문서 갱신 + 열린 질문 폐쇄 | C+B1 | C | 1, 2, 4 |

## 4. 제약

- Exp09 trial 실행은 Ollama + gemma4:e4b 모델 구동 필수
- v2 scoring 함수 자체 수정은 이 플랜 범위 밖 (진단 + 정책 결정까지)
- taskset.json 구조 변경 시 기존 실험 결과 호환성 유지

## 5. Non-goals

- v2 scoring 함수 코드 수정 (별도 플랜)
- Exp09 외 실험 v3 재채점
- 크로스 모델 재현 (후순위)
- Phase 2 (Mixed Intelligence + Small Paradox 해결) 설계
