---
type: plan
status: in_progress
updated_at: 2026-04-15
slug: scoring-v2
---

# Plan: 채점 시스템 통일 (Scoring V2)

## Description

현재 `measure.py`의 `score_answer` 함수는 substring 매칭에 의존하여 포맷 차이, 긴 expected 문자열, JSON 래핑 등의 경우에 false negative가 발생한다.
이를 keyword-group 기반 채점으로 교체하여 실험 0~6 전체를 일관된 기준으로 재채점한다.

## Problem

| 실패 유형 | 예시 |
|-----------|------|
| expected가 긴 문장 | `"Only Provider A meets all three requirements."` — 모델이 같은 내용을 다른 표현으로 답변 |
| 포맷 차이 | `"E=Monday"` vs `"Monday: Event E"` |
| JSON 래핑 | `{'shortest_route': ...}` 안에 정답 포함 |
| 설명 삽입 | 정답 앞뒤에 풀이 과정 삽입으로 substring 불일치 |

실험 6 기준: Gemini 보고서 주장 66.3% vs 실제 substring 채점 31.1% — 35%p 불일치.

## Expected Outcome

- `experiments/tasks/taskset.json` 각 태스크에 `scoring_keywords` 필드 추가
- `measure.py`에 `score_answer_v2` 함수 구현, 기존 함수는 fallback으로 유지
- `python experiments/measure.py --rescore` 로 모든 실험 결과 일괄 재채점 및 v1/v2 비교표 출력

## Subtasks

| # | 제목 | 파일 | 병렬 그룹 |
|---|------|------|----------|
| 1 | taskset.json에 scoring_keywords 추가 | `experiments/tasks/taskset.json` | A |
| 2 | score_answer_v2 구현 및 교체 | `experiments/measure.py` | B (depends: 1) |
| 3 | rescore 명령 추가 및 전체 재채점 | `experiments/measure.py` | B (depends: 2) |

## Constraints

- 기존 결과 JSON 파일은 수정하지 않음 (읽기 전용)
- LLM 호출 없이 순수 Python 로직으로만 채점
- 기존 `score_answer` (v1)는 삭제하지 않고 비교용으로 유지

## Non-goals

- LLM 기반 채점
- 결과 문서(exp-0X-*.md) 자동 재생성
- 새 실험 실행
