---
type: result
status: in-progress
updated_at: 2026-04-12
experiment: 실험 4.5 — Handoff Protocol (단계 간 정보 전달 규격화)
---

# 실험 4.5: Handoff Protocol 핸드오프 리포트

## 1. 개요
소형 LLM(Gemma 4 E4B)의 추론 과정에서 발생하는 '주의력 분산'과 '지시 무시' 현상을 억제하기 위해, 에이전트 간(A-B-C) 인계되는 정보를 엄격한 데이터 구조로 규격화한 실험입니다.

## 2. 주요 구현 사항

### 2.1. Handoff 스키마 도입 (`schema.py`)
- **HandoffA2B (Architect → Developer)**: 구현 명세(`blueprint`), 제약 조건(`constraints`), 핵심 집중 요소(`prioritized_focus`)를 명시.
- **HandoffB2C (Developer → Reviewer)**: 구현 요약, 설계와의 차이점(`deviations`), 자체 검증 결과(`self_test_results`) 전달.
- **RejectMemo (Reviewer → A/B)**: 반려 시 수정 대상 단계(`target_phase`), 실패한 제약 조건 목록, 수정 가이드(`remediation_hint`) 포함.

### 2.2. 오케스트레이터 통합 (`orchestrator.py`)
- `run_abc_chain` 루프 내에서 각 단계의 Handoff 객체를 파싱하고 다음 에이전트의 프롬프트 빌더에 주입.
- 모델의 불완전한 응답(null 값, 데이터 타입 불일치 등)에 대한 **강력한 방어 로직** 적용.

### 2.3. 안정성 및 운영 기능 (`run_experiment.py`)
- **태스크 단위 체크포인트**: 실험 중 중단되어도 `partial_handoff_protocol.json`을 통해 마지막 태스크부터 이어하기 가능.
- **방어 로직**: `resolved_questions` 등에서 모델이 문자열 대신 딕셔너리를 출력하는 경우에 대한 예외 처리.

## 3. 측정 지표 (`measure.py`)
- **handoff_loss_rate**: A2B의 `constraints`가 B2C 결과물에서 얼마나 누락되었는지 측정 (키워드/LLM 기반).
- **backprop_accuracy**: C의 `RejectMemo` 지시가 다음 턴 A의 `blueprint` 수정에 반영되었는지 여부(Boolean).

## 4. 현재 진행 상태 및 인계 사항
- **코드 상태**: 모든 핵심 파일(`schema`, `orchestrator`, `system_prompt`, `measure`, `run_experiment`)이 4.5 규격으로 업데이트됨.
- **데이터 상태**: 초기 실험 결과(`exp045_handoff_protocol_*.json`)가 깃헙에 푸시됨.
- **디렉토리 정리**: 루트 디렉토리의 중복 파일들을 제거하고 `experiments/` 폴더로 단일화함.

### 다음 단계 가이드 (Opus 분석용)
1. 깃헙에서 최신 코드를 pull 받은 후, `experiments/results/`에 있는 4.5 결과 데이터를 분석할 것.
2. `python measure.py results/exp045_*.json`을 실행하여 규격화된 지표 확인.
3. Handoff Protocol 도입 전(실험 4)과 도입 후(실험 4.5)의 수렴 속도 및 논리적 정합성 비교 분석 필요.

---
**Windows Agent (Gemini CLI) 작성**
