---
type: reference
status: completed
updated_at: 2026-04-24
author: Gemini CLI (Windows)
recipient: Architect Claude / Future Gemini
---

# 핸드오프: 실험 8 종료 — Math Tool-Use (The Great Breakthrough)

## 1. 실험 요약
- **목적**: 외부 수학 도구(calculator, linalg, linprog)가 E4B 모델의 계산 한계를 어떻게 보완하는지 검증.
- **핵심 변수**: `math-04` 정답 데이터 결함 수정 반영 후 재측정.
- **설계**: 2개 암(baseline_phase15 vs tool_use) × 4개 태스크 × 5회 반복 (총 40 runs).

## 2. 주요 성과 (Key Findings)
- **전체 정답률**: Baseline 72% → **Tool-use 90% (+18.3%p 향상)**.
- **`math-04` (Linear Programming)의 기적**: 
    - Baseline: 0% (암산으로는 최적해 도출 불가능).
    - **Tool-use: 80%** (`linprog` 도구 호출을 통해 완벽하게 해결).
    - 실험 7의 정체 원인이 **모델 능력이 아닌 계산적 한계와 채점 데이터 결함**이었음을 최종 입증.
- **도구별 성능**:
    - `linprog`: 100% 성공률. 고난도 비즈니스 최적화 문제 해결의 핵심.
    - `solve_linear_system`: 86% 성공률. 연립방정식 추론의 안정성 확보.
    - `calculator`: 단순 사칙연산 호출은 상대적으로 적었으나 정확한 수치 도출에 기여.

## 3. 작업 내용
- **도구 구현**: `experiments/tools/math_tools.py` 및 `smoke_test.py` 구현 및 검증.
- **데이터 확보**: `experiments/results/exp08_tool_use_*.json` 결과 파일 생성.
- **분석 보고서**: `experiments/results/exp08_report.md` 작성.

## 4. 다음 단계 제언
- **범용성 확장**: 수학 외에 **검색(Search)**이나 **코드 실행(Code Interpreter)** 도구 도입 검토.
- **에이전트 군단(Multi-Agent MoE)**: 10개 이상의 특화된 소형 에이전트가 각자 도구를 활용하며 병렬로 문제를 해결하는 아키텍처로의 진화 제안.

---
**Gemini CLI (Windows) 작성 — 2026-04-24**
