---
type: plan
status: in_progress
updated_at: 2026-04-21
version: 1
---

# 실험 7 — Loop Saturation + Loop-Phase 프롬프트

## 연구 질문

**"ABC 파이프라인에서 루프 한계수익이 0에 수렴하는 포화점은 어디이며, 루프 단계별 프롬프트 분화가 포화점을 이동시키는가?"**

### 배경

- 162 trials 전체에서 최대 10루프 관측, 11+ = 0건
- 현재 태스크셋(9종, 최대 난이도 very_hard)이 난이도 천장 → "태스크가 쉬운 건지, 시스템이 포화한 건지" 구분 불가
- ABC 프롬프트가 루프 번호에 무관 → OpenMythos loop-index embedding 아이디어 미적용

## 설계

### 2×4 요인 설계

| 요인 | 수준 |
|------|------|
| **프롬프트** | baseline (현재) / loop-phase (단계별 분화) |
| **MAX_CYCLES** | 8, 11, 15, 20 |

- 태스크: 기존 9개 + 고난도 3개(신규) = 12개
- Trial: 3회 (2×4×12×3 = 288 runs)
- 모델: gemma4:e4b (변경 없음)

### Loop-Phase 프롬프트 전략

| 구간 | 모드 | A 프롬프트 | B 프롬프트 | C 프롬프트 |
|------|------|-----------|-----------|-----------|
| Cycle 1–4 | 탐색 | 가설 확장, 다양한 접근법 탐색 | 논리적 허점 탐색에 집중 | 조기 수렴 방지, 더 탐색 권장 |
| Cycle 5–8 | 정제 | 증거 수렴, 약한 가설 제거 | 남은 불확실성 제거에 집중 | 진전 확인, 정체 시 전이 촉진 |
| Cycle 9+ | 커밋 | open_question 강제 종결, final_answer 산출 | 최종 검증, 잔여 오류 식별 | 적극적 수렴 판정 |

## Expected Outcome

1. MAX_CYCLES별 정답률 포화 곡선 → "N사이클이면 충분하다"의 데이터 기반 결론
2. Loop-Phase 프롬프트 효과 → 프롬프트 분화가 포화점을 이동시키는지 판정
3. 고난도 태스크(04급)에서 ABC 한계선 확인

## Subtask 요약

| # | 제목 | 대상 파일 | 의존 |
|---|------|----------|------|
| 1 | 고난도 태스크 3종 추가 | `experiments/tasks/taskset.json` | — |
| 2 | Loop-Phase 프롬프트 추가 | `experiments/system_prompt.py` | — |
| 3 | 오케스트레이터 파라미터화 | `experiments/orchestrator.py` | — |
| 4 | 실험 실행 함수 작성 | `experiments/run_experiment.py` | 1, 2, 3 |
| 5 | 분석 함수 작성 | `experiments/measure.py` | 4 |
| 6 | 핸드오프 문서 작성 | `docs/reference/handoff-to-gemini-exp7.md` | 1–5 |

## Non-goals

- Domain-MoE 라우팅 (실험 8 후보로 보류)
- Solo 에이전트 포화 곡선 (Exp06 + 이번 ABC 결과로 추후 비교)
- 채점 시스템 변경 (Scoring V2 유지)
- 모델 변경 (E4B 고정)
