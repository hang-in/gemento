---
type: reference
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-12
author: Claude Sonnet 4.6 (macOS)
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 5b — 태스크 난이도 스케일업

## 1. 현재 상태 요약

실험 4.5 (Handoff Protocol)까지 완료되었습니다.

### 완료된 실험 목록

| 실험 | 주요 결과 |
|------|----------|
| 실험 0: Baseline | 정답률 50%, 단순 태스크만 가능 |
| 실험 1: Assertion Cap | JSON 안정성 확인, soft cap 8 |
| 실험 2: 다단계 루프 | 정답률 94.4%, H1 채택 |
| 실험 3: 오류 전파 | 자가 검증 불가 (0%), H2 기각 |
| 실험 3.5: 교차 검증 | 역할 분리 시 감지율 80% |
| 실험 4: A-B-C 파이프라인 | 수렴 100%, 정답 83.3%, synthesis-02 실패 |
| 실험 5a: 프롬프트 강화 | 효과 없음 — 구조 문제로 확인 |
| **실험 4.5: Handoff Protocol** | **수렴 100%, 정답 100%** (6 태스크, 18 트라이얼) |

### 실험 4.5 핵심 수치 (measure.py 실측)

- **정답률: 18/18 (100%)** — 이전 실험 4 대비 +16.7%p
- **수렴률: 18/18 (100%)**
- **평균 사이클: 7.2** (실험 4의 5.8 대비 증가 — 품질 향상 대가)
- **Handoff Loss Rate: 26.4%** — A2B 제약 조건 중 26%가 B2C에서 누락
- **Backprop Accuracy: 9.5%** — C의 RejectMemo가 A에 거의 반영 안됨

### 핵심 발견

- **Handoff Protocol이 synthesis-02 문제를 완전 해결**: `final_answer=None` 패턴 사라짐
- **역설**: Backprop Accuracy 9.5%에도 불구하고 100% 정확도 달성
  - 시스템이 피드백 전파가 아니라 **반복 수렴**으로 작동함을 의미
- **프롬프트 강화 < 스키마 강제**: 지시 강조보다 출력 형식 구조화가 더 효과적

---

## 2. 실험 5b 목표

**"Handoff Protocol 환경에서 100% 정확도의 한계선을 탐색한다"**

현재 6개 태스크는 모두 통과했습니다. 더 어려운 태스크를 추가하여 시스템이 어디서 실패하는지 찾아야 합니다.

### 추가할 태스크 (3개 권장)

#### `math-03`: 연립방정식 + 정수 제약 (난이도: hard)

```
A school has 3 types of tables: round (seats 4), square (seats 6), rectangular (seats 8).
Total tables: 15. Total seats: 96.
The number of rectangular tables equals the number of round tables minus 1.
How many of each type of table are there?
```

- **expected_answer**: `round=6, square=4, rectangular=5`
- **constraints**: `["연립방정식을 세워야 한다", "모든 값은 양의 정수여야 한다", "검산 필수"]`
- 이전 math 태스크보다 변수가 3개 — 시스템이 더 많은 방정식을 관리해야 함

#### `logic-03`: 시간 순서 추론 (난이도: hard)

```
Five events (A, B, C, D, E) happened on different days of the week (Mon-Fri).
Clues:
1. Event A happened before Event C, with exactly one day between them.
2. Event D happened on Wednesday.
3. Event B happened after Event D.
4. Event E happened on the day immediately before Event A.
5. Event C did not happen on Friday.
What day did each event occur?
```

- **expected_answer**: `E=Monday, A=Tuesday, C=Thursday, D=Wednesday, B=Friday`
- **constraints**: `["모든 단서를 활용해야 한다", "모순 없이 배치해야 한다"]`
- logic-01보다 시간 축이 추가되어 추론 복잡도 증가

#### `synthesis-03`: 5가지 선택지 + 복합 조건 (난이도: very hard)

```
A startup needs to hire a CTO. Five candidates with different profiles:
- Alice: 10yr exp, asks $180k, knows Python+Go, available in 2 weeks
- Bob: 7yr exp, asks $140k, knows Python+JS, available immediately
- Carol: 12yr exp, asks $200k, knows Go+Rust, available in 1 month
- David: 8yr exp, asks $160k, knows Python+Go+JS, available in 1 week
- Eve: 6yr exp, asks $130k, knows JS+Rust, available immediately

Requirements:
(1) Must know Python OR Go, (2) Salary budget: max $170k,
(3) Available within 2 weeks, (4) At least 8 years experience.

Which candidates qualify? Rank qualified ones by experience.
```

- **expected_answer**: `Only David qualifies (8yr, $160k, Python+Go+JS, 1 week). Alice fails budget ($180k > $170k).`
- **constraints**: `["모든 후보를 모든 조건에 대해 체크해야 한다", "자격 미달 이유를 명시해야 한다"]`
- synthesis-01보다 선택지가 5개, 조건 간 상호작용 복잡

---

## 3. 실험 5b 실행 방법

### 3.1. 환경 확인

```powershell
# 프로젝트 루트에서
git pull origin main
cd experiments
.venv\Scripts\activate

# Ollama 확인
ollama list   # gemma4:e4b 있어야 함
```

### 3.2. 태스크 확인 (이미 추가됨)

`experiments/tasks/taskset.json`에 3개 태스크가 이미 추가되어 있습니다:
- `math-03` — 3변수 연립방정식 (테이블 문제)
- `logic-03` — 시간 순서 추론 (요일 배치)
- `synthesis-03` — 5명 후보 다중 조건 선별

### 3.3. 실험 실행

**중요**: `handoff-protocol` 실험을 실행합니다 (실험 4.5와 동일한 코드, 태스크만 확장).

```powershell
python run_experiment.py handoff-protocol
# 예상 소요: 6-10시간 (9 태스크 × 5 트라이얼, 사이클 상한 15)
```

> **설정 변경 사항** (`config.py`): `DEFAULT_REPEAT` 3→**5**, `MAX_LOOPS` 12→**15**
> 이터레이션이 늘어도 신뢰성 높은 결과를 얻기 위한 조정입니다.

실험 중 체크포인트가 자동으로 저장됩니다:
```
results/partial_handoff_protocol.json  ← 중단 시 이어하기 가능
```

중단 후 재시작:
```powershell
python run_experiment.py handoff-protocol
# 기존 partial 파일 감지 → "이어하기 (y/n)?" 프롬프트
```

### 3.4. 결과 확인

```powershell
python measure.py "results/exp045_handoff_protocol_*.json"
```

실험 완료 후 최신 파일에 대해 실행합니다.

---

## 4. 관찰해야 할 포인트

실험 실행 중 다음 패턴에 주목하세요:

1. **새 태스크에서 CONVERGED 도달 여부** — 수렴하지 못하면 MAX_CYCLES에 걸림
2. **final_answer 제출 여부** — `final_answer=None`이면 구조적 실패
3. **평균 사이클 수** — 어려운 태스크일수록 더 많은 사이클 필요할 것
4. **synthesis-03의 Alice 처리** — Alice가 budget 초과로 탈락하는지, 아니면 통과로 오판하는지

---

## 5. 결과 기록 및 푸시

실험 완료 후:

```powershell
# 결과 JSON이 results/ 폴더에 저장됨
git add experiments/results/exp045_handoff_protocol_*.json
git add experiments/tasks/taskset.json
git commit -m "feat: 실험 5b 결과 추가 및 태스크 확장"
git push origin main
```

---

## 6. 트러블슈팅

### JSON 파싱 오류 반복 시

`experiments/orchestrator.py`의 방어 로직이 이미 적용되어 있습니다.
콘솔에 `⚠ JSON parse failed, using deepcopy` 메시지가 나와도 실험은 계속됩니다.
단, 해당 사이클에서 `final_answer`가 None이 될 수 있습니다.

### 메모리 부족 / 느린 응답

```powershell
ollama ps   # GPU 사용 여부 확인
# VRAM이 부족하면 CPU 모드로 전환 → 사이클당 10분+ 소요 가능
```

### synthesis-03가 계속 실패할 경우

Alice를 제거하고 4명으로 줄이거나, 조건을 단순화하여 재시도해도 됩니다.
목표는 한계선 탐색이므로, 실패 자체가 유의미한 데이터입니다.

---

## 7. 이전 결과 데이터 위치

```
experiments/results/
├── exp045_handoff_protocol_20260412_004441.json  ← 실험 4.5 (6 태스크)
├── exp04_abc_pipeline_20260409_182751.json        ← 실험 4
├── exp05a_prompt_enhance_20260410_145033.json     ← 실험 5a
└── (기타 이전 실험들)
```

---

**macOS Claude Sonnet 4.6 작성 — 2026-04-12**
