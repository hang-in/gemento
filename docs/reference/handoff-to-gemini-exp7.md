---
type: reference
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-21
author: Claude Sonnet 4.6 (macOS)
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 7 — Loop Saturation + Loop-Phase 프롬프트

## 1. 연구 질문

"ABC 파이프라인에서 루프 한계수익이 0에 수렴하는 포화점은 어디이며,
루프 단계별 프롬프트 분화가 포화점을 이동시키는가?"

### 실험 설계

- **요인 설계**: 2×4 (프롬프트 유형 × MAX_CYCLES)
- **프롬프트 유형**: baseline (기존) / phase (탐색→정제→커밋 단계별 지시문)
- **MAX_CYCLES**: 8 / 11 / 15 / 20
- **태스크**: 12개 (기존 9 + 고난도 04급 3개)
- **총 실행**: 12 태스크 × 3 trials × 8 조건 = **288 runs**

### 해석 프레임

| 결과 | 해석 |
|------|------|
| phase > baseline 전 구간 | Loop-Phase 프롬프트 효과 있음. 채택 권고 |
| phase ≈ baseline | 프롬프트 분화 효과 없음. 현재 프롬프트 유지 |
| 15→20 정답률 변화 < 2%p | 포화점 ≈ 15. 15 이상은 낭비 |
| 20에서도 정답률 상승 중 | 포화점 미도달. MAX_CYCLES 더 높여야 함 |

### 비교 기준선

| 실험 | 정답률 | 평균 사이클 | MAX |
|------|--------|------------|-----|
| exp045 (handoff_protocol, 5b) | 88.9% | 7.2 사이클 | 12 |
| exp06 (solo_budget) | 96.7% | 21 루프 (단일 에이전트) | 21 |

---

## 2. 환경 및 실행

### 2.1. 사전 확인

```powershell
# Windows PowerShell
git pull origin main
.venv\Scripts\Activate.ps1
ollama list  # gemma4:e4b 확인
```

### 2.2. 실험 실행

```powershell
python experiments\run_experiment.py loop-saturation
```

- 8개 조건을 순서대로 실행 (baseline_8 → baseline_11 → ... → phase_20)
- 조건별로 12 태스크 × 3 trials = 36 runs

### 2.3. 예상 소요시간

- 288 runs × ~8분/run ≈ **38시간** (조기 수렴 시 20~30시간)
- 체크포인트 자동 저장: `experiments/results/partial_loop_saturation.json`
- 중단 후 재실행하면 자동으로 이어서 시작

### 2.4. 결과 확인

```powershell
python experiments\measure.py "experiments/results/exp07_loop_saturation_*.json"
```

---

## 3. 관찰 포인트

1. **포화 곡선**: MAX_CYCLES 8→11→15→20에서 정답률이 평탄해지는 구간 식별
2. **Phase 프롬프트 효과**: baseline vs phase 정답률/수렴률 차이 (델타)
3. **고난도 태스크(04급)**: 기존 9개 대비 사이클 소모량 및 정답률 비교
4. **logic-04 (거짓말쟁이 퍼즐)**: logic-02(40% 정답률) 약점이 더 어려운 버전에서도 반복되는지
5. **synthesis-04 (6소스 교차)**: 모순 식별 + 수치 계산이 동시에 필요한 복합 태스크

---

## 4. 신규 태스크 정보

| ID | 난이도 | 핵심 도전 | 예상 정답률 |
|----|--------|----------|------------|
| math-04 | very_hard | 3변수 LP 최적화 (코너 포인트 탐색) | 40~60% |
| logic-04 | very_hard | 4인 거짓말쟁이 (4회 귀류법 필요) | 50~70% |
| synthesis-04 | very_hard | 6개 보고서 교차 검증 + 모순 식별 | 30~50% |

scoring_keywords (채점 기준):
- math-04: `["30"]`, `["2800"]`
- logic-04: `["casey"]`
- synthesis-04: `["270"]`, `["contradict", "zone c"]`, `["report 5", "report 6"]`

---

## 5. 결과 기록 및 푸시

```powershell
git add experiments/results/exp07_loop_saturation_*.json
git commit -m "feat: 실험 7 loop-saturation 결과 추가"
git push origin main
```

---

## 6. 트러블슈팅

### 공통 (exp6과 동일)

- **httpx 타임아웃**: `experiments/config.py`에서 `TIMEOUT` 값 증가 (기본 180s)
- **Ollama 연결 오류**: `ollama serve` 실행 후 재시도
- **GPU 메모리 부족**: 다른 모델 언로드 후 재시도 (`ollama rm <model>`)

### 실험 7 특이사항

- **체크포인트 이어하기**: 재실행만 하면 자동. `partial_loop_saturation.json`이 있으면 완료된 (label, task_id) 쌍을 건너뜀
- **특정 조건만 재실행**: 현재 미지원. `partial_loop_saturation.json`에서 해당 조건 데이터를 수동 삭제 후 재실행
- **MAX_CYCLES=20에서 과도한 소요시간**: `baseline_20`, `phase_20` 조건은 수렴 없이 20 사이클을 모두 사용할 수 있음 → 조건별 예상 시간 편차 큼
