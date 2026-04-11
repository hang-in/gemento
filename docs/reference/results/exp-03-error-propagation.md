---
type: result
status: done
updated_at: 2026-04-09
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
| 대상 태스크 | math-01, math-02, synthesis-01, synthesis-02 |
| 제외 태스크 | logic-01, logic-02 (JSON 파싱 불안정) |
| 유효 실행 | exp03_error_propagation_20260409_135411.json |
| 실행일 | 2026-04-09 |

## 결과

| 결함 유형 | 시행 | 수렴률 | 최종 confidence | 감지율 |
|-----------|------|--------|----------------|--------|
| corrupt_content | 9 | 100% | 1.0 (전부) | 0% |
| inflate_confidence | 3 | 100% | 1.0 (전부) | 0% |
| contradiction | 3 | 100% | 1.0 (전부) | 0% |
| **전체** | **15** | **100%** | **1.0** | **0%** |

### Confidence 궤적

- corrupt_content (9건): 전부 [1.0] — 즉시 수렴, 변동 없음
- inflate_confidence (3건): 전부 [1.0] — 즉시 수렴, 변동 없음
- contradiction (3건): [1.0], [0.95, 1.0], [1.0, 0.95, 1.0, 1.0, 1.0] — 미미한 변동 후 즉시 회복

## 가설 판정

**H2: 기각 — 그러나 예상과 다른 방향으로**

- 오류가 증폭되지 않았음 (H2 기각)
- 오류가 감지되지도 않았음 (self_correction_rate = 0%)
- **모델은 결함을 포함한 assertion을 그대로 신뢰하고 수렴**

## 핵심 메트릭

| 메트릭 | 값 | 판정 |
|--------|-----|------|
| contamination_ratio | 측정 불가 (final_answer 미기록) | — |
| self_correction_rate | 0/15 = 0% | **오케스트레이터 보호 필수** |
| error_half_life | N/A (감지 자체 안 됨) | — |

## 핵심 발견

1. **E4B는 naive executor** — 문신의 assertion을 무조건 참으로 취급. 검증 능력 없음
2. **VERIFY phase 무의미** — "Check all assertions for correctness"라는 directive를 받아도 실제 검증하지 않음
3. **confidence 자가 보고 신뢰 불가** — 결함 주입 후에도 confidence 1.0 유지
4. **contradiction 유형만 미미한 반응** — 0.95로 잠깐 하락 후 즉시 1.0 복귀. 감지라고 보기 어려움

## 설계 시사점

실험 3의 결론은 실험 2의 성공과 결합하여 **제멘토의 역할 분리를 확정**:

| 역할 | 담당 | 근거 |
|------|------|------|
| 추론 실행 (fact 추가, 질문 해결, 종합) | **모델** | 실험 2에서 94.4% 정답률 |
| 구조 관리 (phase 전이, 수렴 판단) | **오케스트레이터** | 실험 2 v1→v2에서 증명 |
| 무결성 보장 (assertion 검증, 일관성) | **오케스트레이터** | 실험 3에서 모델 검증 불가 증명 |

### 필요한 오케스트레이터 기능 (v3)

- 규칙 기반 assertion 검증 (수식 검산, 단위 체크 등)
- confidence를 assertion 변화율 기반으로 외부 계산
- assertion 간 일관성 체크 (모순 감지)
- 도구 결과 교차 검증
