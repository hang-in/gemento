---
type: reference
status: completed
updated_at: 2026-04-24
author: Gemini CLI (Windows)
recipient: Architect Claude / Future Gemini
---

# 핸드오프: 실험 7 종료 — Loop Saturation & Phase Prompting

## 1. 실험 요약
- **목적**: ABC 파이프라인의 루프 한계수익 포화점 식별 및 단계별(Phase) 프롬프트 효과 검증.
- **환경**: 외부 llama.cpp 서버 (yongseek.iptime.org:8005) 사용.
- **설계**: 2(프롬프트: baseline/phase) × 4(MAX_CYCLES: 8/11/15/20) 요인 설계.
- **데이터**: 총 288회 실행 완료.

## 2. 핵심 발견 (Key Findings)
- **포화점 식별**: MAX_CYCLES 15 지점에서 정답률 88.0%로 최고점을 기록하며, 20 사이클로 늘려도 성능 향상이 정체되거나 소폭 하락함. (E4B 모델의 추론 한계점 도달)
- **Phase 프롬프트 효과**: 
    - 고 루프(15, 20) 환경에서 baseline 대비 **+5~6%의 성능 우위**를 점함.
    - 루프가 길어질 때 모델이 길을 잃지 않도록 잡아주는 '가이드라인' 역할을 성공적으로 수행.
- **고난도 태스크(04급)**: `logic-04`와 `synthesis-04`는 100% 정답률을 보였으나, `math-04`는 50% 수준에 머무름. 수학적 추론에서는 여전히 루프만으로는 해결하기 어려운 벽이 존재함.

## 3. 작업 내용
- **코드 전환**: Ollama 전용 API에서 OpenAI 호환 API(`v1/chat/completions`)로 `orchestrator.py` 및 `config.py` 전면 수정.
- **데이터 확보**: `experiments/results/exp07_loop_saturation_*.json` 결과 파일 생성.
- **분석 보고서**: `experiments/results/exp07_report.md` 작성.

## 4. 다음 단계 제언 (Next Steps)
- **실험 8 후보**: `math-04`의 한계를 돌파하기 위해 특정 도메인에 특화된 프롬프트나 MoE(Mixture of Experts) 방식 도입 검토.
- **최적화**: 실험 7에서 확인된 포화점(15 사이클)을 기본값으로 고정하여 운영 효율화.

---
**Gemini CLI (Windows) 작성 — 2026-04-24**

---

## 5. 사후 정정 (Architect Claude, 2026-04-24)

### 5.1 포화점 해석 재검토

원시 데이터(`exp07_loop_saturation_20260424_015343.json`)를 288 trial 전체로 분석한 결과:

| 조건 | 평균 actual_cycles |
|------|-------------------|
| baseline_8 ~ baseline_20 | 6.86 ~ 7.00 |
| phase_8 ~ phase_20 | 6.97 ~ 7.11 |

**모든 조건에서 실제 사용된 cycle 수는 약 7**로 수렴했다. 즉 `MAX_CYCLES`를 15, 20으로 올려도 내부 수렴 판정(C)이 먼저 CONVERGED를 찍어 상한이 사용되지 않는다.

### 5.2 정정 결론

- **포화점은 "MAX_CYCLES 15"가 아니라 "actual_cycles ≈ 7"** — 상한은 안전장치일 뿐.
- 정답률 차이(79~88%)는 같은 7 cycle 안에서 **phase 프롬프트가 추론 품질**을 다르게 만든 결과.
- **운영 기본값 권장**: `MAX_CYCLES=11, use_phase_prompt=True` — 저비용·고안정.

### 5.3 인코딩 이슈 해결

`experiments/results/exp07_report.md`는 UTF-16 LE로 저장되었다. Windows PowerShell의 `>` 기본 인코딩이 원인. 향후 Exp08부터는 `python measure.py ... --output 파일경로` 경로를 사용할 것 (UTF-8 직접 기록, measure.py Task 01에서 추가).
