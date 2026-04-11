# gemento (제멘토)

> "소형 모델의 제한된 추론 능력을 구조적 기법으로 커버한다."

제멘토(gemento)는 **Gemma 4 E4B**와 같은 저사양/소형 LLM 에이전트가 복잡한 태스크를 수행할 때 발생하는 성능 한계를 극복하기 위해, **'상태 전이 시스템'**과 **'A-B-C 직렬 파이프라인'**이라는 구조적 접근법을 실험하고 검증하는 R&D 프로젝트입니다.

## 🚀 프로젝트 핵심 개념

### 1. 문신(Tattoo) 규약
에이전트의 상태를 추적하고 제어하기 위한 상태 저장/전이 메커니즘입니다. 에이전트는 자신의 추론 결과와 확정된 사실을 `Tattoo`라는 구조화된 상태(JSON)로 관리하며, 이는 다음 추론의 유일한 입력이 됩니다.

### 2. A-B-C 직렬 파이프라인
태스크를 역할별로 분리하여 단계적으로 처리합니다.
- **A (Architect)**: 문제 분석 및 구조 설계
- **B (Developer)**: 설계 기반 실제 구현 및 로직 작성
- **C (Reviewer)**: 최종 검증 및 반려/승인 결정

## 🧪 실험 현황 (Current Progress)

- **실험 0**: 단일 추론 베이스라인 측정 (Baseline) `done`
- **실험 1**: Assertion Soft Cap (무한 루프 방지 임계값) 확정 `done`
- **실험 2**: Multi-loop를 통한 추론 품질 향상 검증 (H1 채택) `done`
- **실험 3**: 단일 에이전트의 오류 전파 한계 확인 `done`
- **실험 3.5**: 교차 검증 게이트(Cross Validation Gate) 유효성 확인 `done`
- **실험 4**: A-B-C 직렬 파이프라인 최종 구조 성립 `done`
- **실험 4.5 (준비 중)**: 단계 간 정보 전달 규격(Handoff Protocol) 고도화

## 🛠 기술 스택
- **모델**: Ollama `gemma4:e4b` (Q4_K_M)
- **언어**: Python 3.14 (venv 필수)
- **핵심 도구**: `orchestrator.py` (실험 제어), `measure.py` (품질 측정)

## 🏁 시작하기 (Windows/Linux 공통)
1. Python 3.14 환경 구축 및 venv 활성화
2. Ollama 설치 및 `gemma4:e4b` 모델 다운로드
3. `pip install -r requirements.txt` (필요 시)
4. `python experiments/run_experiment.py` 실행
