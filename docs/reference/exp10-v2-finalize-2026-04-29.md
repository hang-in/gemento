---
type: reference
status: in_progress
updated_at: 2026-04-29
author: Architect Claude
---

# Exp10 v2 Finalize — 작업 절차 및 패치 디스클로저

## 1. 배경

Exp10 v2 540-trial 본 run (`experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_20260428_175247.json`) 에 두 가지 known artifact 가 있다.

| # | 영역 | 현상 | 원인 | 결정 |
|---|------|------|------|------|
| 1 | `(gemma_8loop, math-04)` 20 trial | 19/20 fail (mean acc 0.0000) | `run_abc_chain(...)` 가 `use_tools=False` 로 호출됨. LP 문제이지만 `linprog` 도구 호출 불가 | 도구 활성화 debug rerun 결과 (20/20, mean=1.0000) 채택 |
| 2 | `(gemini_flash_1call, logic-04)` 20 trial 중 4건 | 4건 `httpx.ReadTimeout` (~120s) | gemini_client `DEFAULT_TIMEOUT=120` | timeout=300s 로 4건만 재시도, 나머지 16건 보존 |

본 결정 출처: 사용자 결정 (2026-04-28) — `config.py 미푸시 의도`, `math-04 19 오류는 설정 미스, 디버그 결과 채택`, `gemini logic-04 4건 재시도`.

## 2. 인프라 구성

다음 두 스크립트가 추가됨.

### 2.1 `experiments/exp10_reproducibility_cost/run_logic04_flash_retry.py`
- 본 v2 result JSON 에서 `(gemini_flash_1call, logic-04, error != None)` trial 자동 추출
- 추출된 trial 번호 (`v2` 기준 2, 11, 17, 20) 를 동일 trial 번호로 재실행
- `gemini_client.call_with_meter(..., timeout=300)` 명시 전달
- 결과는 별도 파일 `experiments/exp10_reproducibility_cost/results/exp10_logic04_flash_retry_<timestamp>.json` 에 저장
- 본 v2 result 는 수정하지 않음

### 2.2 `experiments/exp10_reproducibility_cost/merge_v2_final.py`
- 입력 3개: 본 v2 (540), math-04 debug rerun (20), logic-04 retry (4)
- substitution 정책:
  - `(gemma_8loop, math-04)` 20 trial 전체 교체
  - `(gemini_flash_1call, logic-04)` 의 `error != None` 인 trial 만 교체 (success 16건 보존)
- 출력 JSON 에 `_substitutions` 메타 추가 (각 trial 의 출처 file 명 + 사유 명시)
- 출력 파일: `experiments/exp10_reproducibility_cost/results/exp10_v2_final_<timestamp>.json`

## 3. 실행 절차 (사용자 직접 실행)

### 3.1 logic-04 flash retry

Mac 환경, 프로젝트 루트에서:

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.run_logic04_flash_retry \
  --timeout 300
```

기대 출력:
```
  -> retry targets in exp10_reproducibility_cost_20260428_175247.json: trials=[2, 11, 17, 20]
  [2/20] gemini_flash_1call | logic-04 | trial 2 (timeout=300s)
    -> error=None  acc=...  final='...'
  ... (총 4 trial)
  → Result saved: .../exp10_logic04_flash_retry_<TS>.json
```

검증:
- 4 trial 모두 `error=None` 이면 retry 정상
- 또 timeout 나면 사용자에게 보고 → β 안 (전체 20 재실행 또는 timeout 추가 증가) 별도 결정

### 3.2 v2 merge

retry 결과 파일 경로를 손에 잡은 뒤:

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.merge_v2_final \
  --logic04 experiments/exp10_reproducibility_cost/results/exp10_logic04_flash_retry_<TS>.json
```

기대 출력:
```
  → Result saved: .../exp10_v2_final_<TS>.json
  -> merge done: math04_replaced=20  logic04_replaced=4
```

검증:
- 출력 JSON `len(trials) == 540`
- `_substitutions.math04_replaced == 20`, `logic04_replaced == 4`
- `(gemma_8loop, math-04)` 20 trial 모두 `_substituted_from` 메타 보유

### 3.3 분석 (다음 단계)

`exp10_v2_final_<TS>.json` 이 손에 잡히면 result.md 작성 및 분석으로 진행. 이 단계는 본 문서 범위 밖.

## 4. 패치 디스클로저 (정식 result.md 에 옮길 항목)

### 4.1 math-04 (gemma_8loop) 패치
- **substitution**: 본 v2 의 20 trial → debug rerun 의 20 trial
- **차이점**:
  - `use_tools`: False → **True**
  - prompt: 원본 + `STRUCTURED_SUFFIX` (final answer 의 X/Y/Z/profit 구조화 요구)
  - 두 실행 환경: 본 v2 = Windows + LM Studio, debug rerun = Windows + LM Studio (동일 머신, 다른 시점)
- **영향**: gemma_8loop 의 mean accuracy 가 0.7093 (math-04 19 fail 포함) → 패치 후 더 높아짐 (실제 수치는 merge 후 확인)
- **공정 비교 측면**: prompt 가 다르므로 strict 비교는 아니다. result.md 에 명시 disclosure 필요. "use_tools 정책 통일" vs "prompt 통일" 둘 중 어디까지 v3 에서 통제할지 별도 결정.

### 4.2 logic-04 (gemini_flash_1call) 패치
- **substitution**: 본 v2 의 4 timeout trial → retry 의 4 trial (timeout=300s)
- **차이점**: timeout 만 다름. prompt / system prompt / model 모두 동일. retry 는 reliability 측정 보강용.
- **영향**: logic-04 의 valid sample 수 16 → 20 으로 확장. 정답률 자체는 task 난이도가 모델 능력 한계라 별로 안 변할 가능성.

### 4.3 본 v2 result JSON 보존
- `exp10_reproducibility_cost_20260428_175247.json` 은 수정 금지. 이전 무효 파일 `exp10_reproducibility_cost_20260427_130235.json` 도 archive 상태로 유지.
- 정식 분석은 항상 `exp10_v2_final_<TS>.json` 기반.

## 5. logic-04 채점 메모 (분석 단계 확인 필요)

본 v2 의 logic-04 success 16건 답을 샘플링하면 'Dana', 'Alex' 가 보이는데 정답은 'Casey' (`experiments/tasks/taskset.json` 의 `scoring_keywords=[["casey"]]`). 즉 success=valid 이지만 정확도는 낮은 것 정상. retry 4건이 'Casey' 를 맞출지 / 그래도 틀릴지 가 추가 관전 포인트. result.md 에서 condition 별 logic-04 정답률 함께 보고.

## 6. 미해결/추후 결정 항목

result.md 작성 시 함께 정리할 항목:

1. **use_tools 정책**: math-04 만 True 로 한 채 비교 유지 vs 모든 math 태스크 use_tools=True 로 통일 후 v3 재실행
2. **math-04 정답 키 확장**: 현 채점이 `{X:31, Y:10, Z:37, profit:3060}` 단일 키. 같은 profit=3060 의 다른 vertex 도 인정할지
3. **gemma_1loop**: error=0 이지만 null=11. 이 11건 원인 진단 (final_answer parse 실패 vs 모델 빈 답)
4. **reproducibility 변동성**: 본 v2 가 N=20 trial 인데 condition × task 별 std 가 어느 정도인지 보고
