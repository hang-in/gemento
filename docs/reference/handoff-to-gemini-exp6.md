---
type: reference
status: in_progress
updated_at: 2026-04-15
author: Claude Opus 4.6 (macOS)
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 6 — Solo vs ABC 시너지 측정

## 1. 연구 질문

**"A-B-C 역할 분리(E4B×3)가 단일 E4B의 반복(E4B×1)을 단순히 더 많이 돌린 것보다 명확히 우월한가?"**

현재까지의 결과:
- **실험 5b (handoff-protocol, E4B×3)**: 9 태스크 × 5 trials = **88.9% 정답**, 평균 7.2 사이클 × 3 에이전트 = **~21.6 Ollama 호출/trial**
- 실험 2 결과만으로는 판별 불가 (태스크셋이 6개로 적고, 난이도 낮음)

실험 6은 **동일 태스크셋(9개) × 동일 trial 수(5) × 동일 compute 예산(≈21 호출)**에서 단일 에이전트(run_chain)가 얼마나 성능을 내는지 측정한다.

### 해석 프레임
| 결과 | 해석 |
|------|------|
| solo ≈ ABC (±3%p) | 역할 분리는 compute를 재포장한 것. 설계 단순화 가능 |
| solo << ABC (>5%p 열위) | 역할 분리가 실질적 시너지 생성. 다음 단계(대형 모델 혼합) 정당성 확보 |
| solo >> ABC | **반전 결과** — 오케스트레이션 오버헤드가 성능을 깎고 있음. 구조 재설계 필요 |

---

## 2. 환경 및 실행

### 2.1. 사전 확인

```powershell
cd <repo-root>
git pull origin main
cd experiments
.venv\Scripts\activate

ollama list   # gemma4:e4b 있어야 함
ollama ps     # GPU 올라가 있으면 이상적
```

### 2.2. 실험 실행

```powershell
python run_experiment.py solo-budget
```

**예상 소요시간**: 3-6시간 (9 태스크 × 5 trials × 최대 21 loops, 조기 수렴 시 단축)

**설정**:
- `SOLO_MAX_LOOPS = 21` (run_experiment.py 내부 상수)
- 동일 `taskset.json` 9개 태스크 사용
- `DEFAULT_REPEAT = 5`

### 2.3. 체크포인트

중단 시 `results/partial_solo_budget.json`이 저장됨. 재실행 시 자동 이어하기.

```powershell
# 중단 후 재시작
python run_experiment.py solo-budget
```

### 2.4. 결과 확인

```powershell
python measure.py "results/exp06_solo_budget_*.json"
```

---

## 3. 관찰 포인트

1. **태스크별 수렴 여부**: solo가 MAX_LOOPS(21)에 도달해도 CONVERGED 못 가는 태스크가 어디인가?
2. **final_answer 제출률**: ABC에서는 44/45였음. solo는?
3. **조기 수렴 패턴**: 쉬운 태스크(math-01, synthesis-01)에서 solo는 몇 루프만에 수렴하는가? 
4. **logic-02 (모순 태스크)**: ABC는 2/5 성공. solo는 더 잘 할까, 더 못 할까? 
   - 가설: 단일 에이전트가 모순을 더 못 볼 수 있음 (B의 교차 검증이 없으므로)
5. **synthesis-03 (5후보 × 4조건)**: ABC는 5/5 성공. solo도 가능한가?
   - 가설: 복잡도 높은 태스크에서 역할 분리 이점이 드러날 가능성

---

## 4. 결과 기록 및 푸시

실험 완료 후:

```powershell
git add experiments/results/exp06_solo_budget_*.json
git commit -m "feat: 실험 6 solo-budget 결과 추가"
git push origin main
```

---

## 5. 참고: 비교할 직전 결과

`results/exp045_handoff_protocol_20260414_135634.json` (실험 5b)

| 태스크 | ABC 정답 (5회 중) | 평균 사이클 |
|--------|-------------------|-------------|
| math-01 | 5/5 | 7.0 |
| logic-01 | 5/5 | 7.6 |
| synthesis-01 | 5/5 | 8.2 |
| math-02 | 5/5 | 7.2 |
| logic-02 | **2/5** | 7.8 |
| synthesis-02 | 4/5 | 7.0 |
| math-03 | 4/5 | 6.2 |
| logic-03 | 5/5 | 7.0 |
| synthesis-03 | 5/5 | 7.0 |

이 숫자들이 solo 결과와의 비교 기준선이다.

---

## 6. 트러블슈팅

- **httpx 미설치**: `.venv\Scripts\activate` 후 `pip install httpx`
- **Ollama 타임아웃**: `config.py`의 `OLLAMA_TIMEOUT = 600` 이미 설정됨
- **너무 느림 (CPU 모드)**: `ollama ps`로 GPU 확인. VRAM 부족 시 다른 앱 종료

---

**macOS Claude Opus 4.6 작성 — 2026-04-15**
