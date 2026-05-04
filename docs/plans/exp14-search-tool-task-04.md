---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: exp14-search-tool
parallel_group: D
depends_on: [03]
---

# Task 04 — 실험 실행 (사용자 직접) — 10 task × 2 condition × 5 trial = 100 trial

## Changed files

- `experiments/exp14_search_tool/results/exp14_baseline_abc_chunked_<TS>.json` — **신규 (사용자 실행)**
- `experiments/exp14_search_tool/results/exp14_search_tool_abc.json` — **신규 (사용자 실행)**

신규 2 (자동 생성).

## Change description

### 책임

- **Sonnet (Developer)**: 본 task **직접 실행 금지**. 책임 = 명령 정합성 확인 + 사용자 안내
- **사용자**: 직접 실행 + 결과 보고
- **Architect**: 결과 받으면 task-05 진행

### Step 1 — Sonnet 사전 검증

```bash
# 1) Stage 2A healthcheck 가 작동하는지 확인 (LM Studio 서버 응답)
.venv/Scripts/python -c "
from experiments.run_helpers import classify_trial_error
print('Stage 2A import ok')
"

# 2) task-01/02/03 마감 검증
.venv/Scripts/python -c "
from experiments.tools import SEARCH_TOOL_SCHEMA, make_search_chunks_tool
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'search_tool' in sig.parameters
assert 'corpus' in sig.parameters
from experiments.exp14_search_tool.run import CONDITION_DISPATCH
assert 'baseline_abc_chunked' in CONDITION_DISPATCH
assert 'abc_search_tool' in CONDITION_DISPATCH
print('task-01/02/03 마감 검증 ok')
"

# 3) longctx_taskset.json 의 10 task 정합 확인
.venv/Scripts/python -c "
import json
with open('experiments/tasks/longctx_taskset.json', 'r', encoding='utf-8') as f:
    ts = json.load(f)
assert len(ts['tasks']) == 10
print(f'longctx_taskset 10 task ok')
"
```

### Step 2 — dry-run (1 task × 1 trial × abc_search_tool)

사용자에게 dry-run 명령 제시:

```bash
cd D:/privateProject/gemento
.venv/Scripts/python -m experiments.exp14_search_tool.run \
    --conditions abc_search_tool \
    --trials 1 \
    --tasks longctx-small-needle-01 \
    --out-name dry_run_search_tool
```

(`--tasks` 옵션은 run.py 에서 task_id filter 로 1 task 만 실행. 미구현 시 `--limit 1` 등 대안)

dry-run 결과 검증 항목:
- `tool_call_log` 가 비어있지 않음 (search_chunks 호출 발생)
- `final_answer` 생성 (None 또는 빈 문자열 아님)
- `tattoo_history` cycle-by-cycle 저장
- 시간 ~10-15min

### Step 3 — A-1 본 실행 (baseline_abc_chunked, 50 trial)

```bash
cd D:/privateProject/gemento
.venv/Scripts/python -m experiments.exp14_search_tool.run \
    --conditions baseline_abc_chunked \
    --trials 5 \
    --out-name exp14_baseline_abc_chunked
```

예상 시간: 50 trial × ~10-15min = ~8-13h. context overflow 발생 시 healthcheck/abort 발화 가능 — 그 경우 사용자 보고 후 검토.

### Step 4 — A-2 본 실행 (abc_search_tool, 50 trial)

```bash
cd D:/privateProject/gemento
.venv/Scripts/python -m experiments.exp14_search_tool.run \
    --conditions abc_search_tool \
    --trials 5 \
    --out-name exp14_search_tool_abc
```

예상 시간: 50 trial × ~10-15min = ~8-13h.

### Step 5 — 결과 정합성 확인

A-1/A-2 마감 후 사용자 또는 Sonnet 이 다음 빠른 확인:

```bash
.venv/Scripts/python -c "
import json
from collections import defaultdict

def load(p):
    with open(p, 'r', encoding='utf-8') as f: return json.load(f)

base = load('experiments/exp14_search_tool/results/exp14_baseline_abc_chunked_*.json')
search = load('experiments/exp14_search_tool/results/exp14_search_tool_abc.json')

for label, d in (('baseline', base), ('search', search)):
    ts = d['trials']
    accs = [t.get('accuracy_v3', 0) or 0 for t in ts]
    errs = sum(1 for t in ts if t.get('error'))
    print(f'{label}: n={len(ts)} mean_acc={sum(accs)/len(ts):.4f} err={errs}')
"
```

이 시점에서 사용자가 Architect 호출 → task-05 진행.

## Dependencies

- task-03 마감 (run.py + CONDITION_DISPATCH + main)
- LM Studio 서버 (`http://192.168.1.179:1234`) 운영 중 — Gemma 4 E4B Q8_0 로드
- `bm25s` 패키지 설치됨 (Exp09 검증)

## Verification

본 task = 사용자 직접 실행. Sonnet 의 책임 = 명령 정합성 + 사전/사후 검증만.

```bash
# 사전: task-03 마감 + import 검증 (Step 1 위)

# 사후 (사용자 결과 받은 후): trial 수 + 결과 파일 정합성
.venv/Scripts/python -c "
import json
import os
results_dir = 'experiments/exp14_search_tool/results'
files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
print(f'결과 파일: {files}')
for f in files:
    with open(os.path.join(results_dir, f), 'r', encoding='utf-8') as fh:
        d = json.load(fh)
    print(f'  {f}: {len(d.get(\"trials\", []))} trials, conditions={d.get(\"conditions\")}')
"
```

## Risks

- **Risk 1 — context overflow (longctx-large baseline)**: 20K word + ABC + Tattoo = LM Studio context 한계 (~16K~32K). overflow 시 healthcheck/abort 또는 model 의 truncate. 사용자 보고 후 Architect 검토 — 가능한 대응:
  - large size class 만 baseline 비교 제외 (Exp09 와 정합)
  - chunked baseline 으로 대체 (Exp09 의 abc_chunked 함수 import)
- **Risk 2 — Search Tool 미호출 (tool_neglect)**: dry-run 시 tool_call_log 가 비어있으면 본 task 진입 보류. 사용자/Architect 협의 — prompt 강화 (task-01/02 영역 retroactive) 또는 별도 plan
- **Risk 3 — search_chunks 가 빈 결과 반환**: stop-words filter 로 query 가 모든 token 제거 시 ValueError. 본 task 영역 외 (task-01 의 stop-words 의 부작용). dry-run 에서 발견 시 사용자 보고
- **Risk 4 — 시간 초과**: ~17-25h 추정. 사용자 환경 (Windows + LM Studio) 안정성 고려. 분할 실행 (A-1 / A-2 별도 세션) 권장
- **Risk 5 — partial JSON checkpoint corruption**: Stage 2A 의 checkpoint resume 기능. Exp13 와 동일 — 부분 실행 후 재시작 가능. 단 직전 trial 의 cycles=0 등 부분 결과 발견 시 partial JSON 삭제 후 재시작
- **Risk 6 — Sonnet 직접 실행 시도**: 본 task = 사용자 직접 실행 *전용*. Sonnet 이 모델 호출 / dry-run / 결과 JSON 생성 절대 금지

## Scope boundary

본 task 에서 **변경 금지**:
- 모든 코드 파일 (task-01/02/03 영역)
- 모든 plan 문서
- 다른 실험의 결과 JSON

본 task 에서 **생성 가능**:
- `experiments/exp14_search_tool/results/exp14_*.json` (자동, run.py 출력)
- `experiments/exp14_search_tool/results/partial_*.json` (자동, checkpoint)

**Sonnet 절대 금지**:
- LM Studio API 호출
- run.py 실행 (`python -m experiments.exp14_search_tool.run`)
- dry-run / 검증 외 모델 호출
- 결과 JSON 임의 작성 / 편집
