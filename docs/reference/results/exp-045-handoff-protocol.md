---
type: result
status: done
updated_at: 2026-04-12
experiment: 실험 4.5 — Handoff Protocol (단계 간 정보 전달 규격화)
---

# 실험 4.5 & 5b: Handoff Protocol 및 고난도 스트레스 테스트 결과

## 1. 개요
에이전트 간 정보 인계 규격화(Handoff Protocol)가 고난도 추론 문제에서 소형 모델(Gemma 4 E4B)의 일관성을 얼마나 유지해주는지 측정한 실험입니다.

## 2. 최종 측정 데이터 (2026-04-14)
- **전체 Handoff Loss Rate: 28.6%**
- **전체 Backprop Accuracy: 4.2%**

| 태스크 | 난이도 | Loss Rate | Backprop Acc | 샘플 사이클 |
|--------|-------|-----------|--------------|-------------|
| math-01 | Medium | 20.7% | 0.0% | 35 |
| logic-01 | Medium | 19.5% | 25.0% | 34 |
| synthesis-01 | Medium | 22.9% | 0.0% | 35 |
| math-02 | Hard | 39.8% | 0.0% | 36 |
| logic-02 | Hard | 47.3% | 0.0% | 25 |
| synthesis-02 | Medium | 21.4% | 0.0% | 37 |

## 3. 핵심 발견 및 분석
1. **임계점 발견**: 모델의 정보 처리 능력이 `logic-02`와 같은 다단계 조건부 추론에서 급격히 저하됩니다(Loss Rate 47.3%). 이는 소형 모델이 감당할 수 있는 '문신(Tattoo)의 복잡도' 상한선이 존재함을 시사합니다.
2. **Backprop 루프 부재**: C의 지시가 A의 설계(`blueprint`) 수정으로 거의 전파되지 않습니다. 현재의 A-B-C 직렬 구조는 '피드백 개선'보다 '반복적 사고를 통한 정답 도달'에 더 의존하고 있습니다.
3. **기술적 돌파구**: Ollama의 **JSON Mode**와 **Temperature 0.1** 강제 설정이 고난도 작업 시 발생하던 파싱 에러를 99% 해결했습니다.

## 4. Opus를 위한 인계 사항 (실험 6 제언)
- **가설**: A의 프롬프트에서 `RejectMemo`를 감지했을 때 "기존 blueprint를 복사하지 말고 새로 작성하라"는 강한 부정적 제약을 주면 Backprop Accuracy를 높일 수 있을 것인가?
- **코드**: `orchestrator.py`에 GPU 최적화 및 JSON Mode가 적용되어 있으니 이를 유지할 것.
- **데이터**: `results/exp045_handoff_protocol_20260413_045126.json` 분석 요망.
