---
type: plan
status: in_progress
updated_at: 2026-04-29
plan_title: "Exp06 H4 Scoring Reconciliation — 채점 정합성 정리 + H4 verdict 갱신"
version: 1
---

# Exp06 H4 Scoring Reconciliation — 채점 정합성 정리 + H4 verdict 갱신

## 1. 배경

직전 plan (`gemento-public-readiness-pass-config-readme`, Task 04)에서 README H4를
`⚠ Conditionally supported (needs balanced rerun)`으로 낮춤 — 외부 노출 약속.
본 plan으로 그 약속을 회수한다.

### 정찰 결과 (2026-04-29, Windows Architect)

Mac 측 plan의 전제 3개가 사실과 불일치:

| # | Mac 측 전제 | 실제 | 판정 |
|---|------------|------|------|
| 1 | Solo 9 sample vs ABC 45 sample (5x 차이) | Solo = 9 task × 5 trial = **45 trial** (ABC와 동일) | ❌ 표본 이미 대칭 |
| 2 | v1 기준 ABC 88.9% > Solo 66.3% | 현재 `score_answer` v1로 재현 불가 (어떤 threshold에서도 40/45 미재현) | ❌ 원본 수치 재현 불가 |
| 3 | balanced rerun 필요 | 표본 이미 대칭 → rerun 불필요, 채점 정합성 정리가 핵심 | ❌ 방향 수정 |

### 재현 가능한 비교 결과 (45 vs 45)

| 채점법 | Solo | ABC | Δ (Solo−ABC) | 우위 |
|--------|------|-----|-------------|------|
| v1 (partial) | 0.663 | 0.649 | +0.015 | Solo |
| v2 (keyword) | 0.967 | 0.900 | +0.067 | Solo |
| v3 (neg+kw) | 0.967 | 0.900 | +0.067 | Solo |

task-level `v2 mean ≥ 0.75` → 8/9 = 88.9% — 원본 "88.9%"의 task-level 유래 가능성.

## 2. 목적

- Exp06 비교를 동일 채점법 × 동일 표본(45 vs 45)으로 재정리
- researchNotebook의 "Solo 표본 9" 오류 + "88.9%" 재현 불가 disclosure 기록
- README H4 행을 데이터 기반 verdict로 갱신 (한·영 동일)

## 3. Subtasks

| # | 제목 | 의존성 | parallel_group |
|---|------|--------|----------------|
| 1 | Exp06 scoring reconciliation 분석 스크립트 | 없음 | A |
| 2 | researchNotebook 정정 + disclosure | Task 1 (분석 결과 필요) | B |
| 3 | result.md + README H4 갱신 | Task 1, Task 2 | B |

## 4. Constraints

- ABC 결과 (Exp045) 변경 금지 — read-only 재사용
- score_answer_v3 / taskset.json 변경 0
- Solo run.py 변경 0 — 추가 실험 실행 없음
- 영문 노트북: Exp06 Closed 추가만 — 기존 수치 변경 0
- v2 final / v3 rescored / Exp10 결과 JSON 모두 read-only
- "88.9%" 원출처 불명 — "재현 불가" disclosure만, 추측 금지
- 과장 금지 (Solo ≥ ABC → "ABC 무효" / "역할 분리 불필요" 주장 금지)

## 5. Non-goals

- Solo 추가 trial 실행 (이미 45 = 대칭)
- v3 채점기 변경
- 다른 실험 (Exp00~05, Exp07~10) 재산정
- 새 H 가설 추가
- README H4 외 다른 영역 변경
- logic/math 카테고리 도구화/multi-stage (별도 plan)
- 채점 해상도 개선 (LLM-judge 등 — 별도 plan)
