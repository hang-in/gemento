---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: phase-1-v2-exp09
task_number: 3
title: "Exp09 추가 trial 실행"
depends_on: []
parallel_group: A
---

# Task 03: Exp09 추가 trial 실행

## Changed files

- `experiments/exp09_longctx/run.py` — 기존 파일 수정
  - line 26: `LONGCTX_TRIALS = 3` → `5`
  - lines 156-231: `run()` 함수 내 체크포인트 로직이 기존 trial을 skip하므로 추가 코드 불필요 가능 — 아래 접근법 참조
- `experiments/exp09_longctx/run_append_trials.py` — **신규 생성** (추가 trial 전용 러너)
- `experiments/exp09_longctx/results/` — 결과 JSON 1건 추가 (5-trial 병합본)

## Change description

### 3.1 목적

현재 3 trial/condition을 5 trial로 확대하여 H9b 통계 검정(Task 04)에 충분한 데이터를 확보한다.
추가 분량: 2 trial × 10 tasks × 3 arms = **60 runs**.

### 3.2 접근법 선택

**방법 A (권장): 별도 append 스크립트**

`run_append_trials.py`를 신규 생성:
1. 기존 결과 JSON(`exp09_longctx_20260425_144412.json`) 로드
2. 각 (arm, task) 조합에 대해 trial 4, 5만 실행
3. 기존 `_run_longctx_trial()` 함수를 import하여 동일 인프라 사용
4. 기존 trials + 신규 trials를 병합한 5-trial JSON을 새 타임스탬프로 저장
5. 원본 3-trial JSON은 보존 (삭제 금지)

이 방법의 장점:
- 원본 `run.py` 수정 최소화 (import 가능하도록 `_run_longctx_trial` 을 모듈 레벨에서 접근 가능하게만 확인)
- 기존 3-trial 결과와의 비교 가능
- 실행 중단 시 체크포인트 지원

**방법 B (대안): run.py LONGCTX_TRIALS 변경**

`LONGCTX_TRIALS = 5`로 변경 후 전체 재실행. 체크포인트(`partial_longctx.json`) 로직이 (arm, task) 단위로 skip하므로 이미 완료된 (arm, task)는 건너뜀. 단, 기존 결과의 trial 수(3)와 새 설정(5) 사이의 불일치를 처리해야 함.

**→ 방법 A 권장**: 기존 결과 보존 + 명확한 append 의미론.

### 3.3 `run_append_trials.py` 구현 단계

**단계 1: 기존 결과 로드**
```python
EXISTING_RESULT = RESULTS_DIR / "exp09_longctx_20260425_144412.json"
existing = json.load(open(EXISTING_RESULT))
results_by_arm = existing["results_by_arm"]
```

**단계 2: task/document 로드**
- `longctx_taskset.json` 로드
- 각 task의 document 본문 로드 (`_document` 키)

**단계 3: 추가 trial 실행**
```python
for arm in LONGCTX_ARMS:
    label = arm["label"]
    for task_entry in results_by_arm[label]:
        existing_trials = len(task_entry["trials"])  # 3
        for trial_idx in range(existing_trials, 5):  # trial 3, 4 (0-indexed)
            task_obj = task_map[task_entry["task_id"]]
            result = _run_longctx_trial(arm, task_obj, trial_idx)
            task_entry["trials"].append(result)
```

**단계 4: 체크포인트**
- 각 (arm, task) 완료 후 partial JSON 저장
- 스크립트 재실행 시 이미 5 trial인 (arm, task)는 skip

**단계 5: 최종 저장**
- `exp09_longctx_5trial_<timestamp>.json` 으로 저장
- `trials_per_task: 5` 메타데이터 갱신
- 원본 3-trial JSON 보존

### 3.4 `_run_longctx_trial` 접근성

현재 `run.py`의 `_run_longctx_trial`은 모듈 레벨 함수(line 60~153). `run_append_trials.py`에서 import 가능:
```python
from run import _run_longctx_trial, LONGCTX_ARMS, LONGCTX_CHUNK_SIZE, ...
```
단, `sys.path` 설정 필요 (run.py:16과 동일 패턴).

### 3.5 실행 전제

- **Ollama gemma4:e4b 모델 구동 필수**
- LM Studio API 엔드포인트: `config.py`의 `API_BASE_URL` 참조
- 예상 소요 시간: 60 runs × ~2-5분/run = 약 2-5시간

## Dependencies

- Python 패키지: `httpx`, `numpy`, `bm25s` (기존 의존성)
- 런타임: Ollama gemma4:e4b 또는 LM Studio API 가동
- 다른 subtask: 없음 (parallel_group A — Task 1, 2와 병렬 가능)

## Verification

```bash
# 1. 스크립트 문법 체크
python -c "import ast; ast.parse(open('experiments/exp09_longctx/run_append_trials.py').read()); print('Syntax OK')"
# 기대: Syntax OK

# 2. 5-trial 결과 파일 존재 확인
ls experiments/exp09_longctx/results/exp09_longctx_5trial_*.json 2>/dev/null | wc -l
# 기대: 1 이상

# 3. 모든 (arm, task)가 5 trial인지 확인
python -c "
import json, glob
files = sorted(glob.glob('experiments/exp09_longctx/results/exp09_longctx_5trial_*.json'))
if not files:
    print('No 5-trial result file'); exit(1)
d = json.load(open(files[-1]))
for arm, tasks in d['results_by_arm'].items():
    for t in tasks:
        n = len(t['trials'])
        if n != 5:
            print(f'FAIL: {arm}/{t[\"task_id\"]} has {n} trials')
            exit(1)
print('All (arm, task) pairs have 5 trials')
print('OK')
"
# 기대: All (arm, task) pairs have 5 trials, OK

# 4. 원본 3-trial 결과 보존 확인
ls experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json
# 기대: 파일 존재
```

## Risks

- **모델 가용성**: Ollama/LM Studio가 구동 중이어야 함. 미구동 시 연결 에러 발생 — 스크립트에서 첫 trial 실행 전 health check 추가 권장.
- **결과 일관성**: 추가 trial은 다른 시점에 실행되므로 모델 버전, temperature, sampling params가 기존과 동일한지 확인 필요. `config.py:SAMPLING_PARAMS` 확인.
- **디스크 공간**: 결과 JSON이 55KB(3-trial) → ~90KB(5-trial) 예상. 문제 없음.
- **중단 복구**: 60 runs 중간에 중단 시 체크포인트에서 이어서 실행 가능해야 함.
- **trial 인덱싱**: 기존 trial은 1-indexed (`"trial": 1, 2, 3`). 추가 trial은 `"trial": 4, 5`로 이어야 함. 0-indexed trial_idx와 혼동 주의.

## Scope boundary

수정 금지 파일:
- `experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json` — 원본 보존 (읽기만)
- `experiments/tasks/longctx_taskset.json` — 읽기만 허용
- `experiments/tasks/longctx_docs/` — 읽기만 허용
- `experiments/measure.py` — 이 task에서 수정 불필요
- `docs/` 하위 모든 파일 — Task 5 영역

수정 허용 (최소):
- `experiments/exp09_longctx/run.py` — import 편의를 위한 최소 변경만 허용 (예: `if __name__` 가드 확인). 로직 변경 금지.
