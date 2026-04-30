---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: stabilization-healthcheck-abort-meta-pre-exp11
parallel_group: B
depends_on: [03]
---

# Task 04 — analyze 스크립트 backward-compat (schema_version v1.0 + v0 동시 지원)

## Changed files

- `experiments/run_helpers.py` — **수정 (추가만)**. `parse_result_meta` 함수 추가
- `experiments/exp09_longctx/analyze_stats.py` — **수정**. `parse_result_meta` 사용으로 전환 (옵션)
- `experiments/exp09_longctx/analyze_5trial_drop.py` — **수정**. 동일 (옵션)
- `experiments/exp10_reproducibility_cost/rescore_v3.py` — **수정**. 동일 (옵션)
- 다른 analyze 스크립트 — **정찰 후 결정**

수정 multi (정찰 후 결정), 신규 0.

## Change description

### 배경

Subtask 03 에서 신규 결과 JSON 은 schema_version="1.0" + 표준 top-level meta. 단 기존 결과 (Exp00~10) 는 schema_version 부재 + 도구별 ad-hoc meta. analyze 스크립트가 양쪽 모두를 호환해야 회귀 0.

본 task 는 **호환 helper 추가 + analyze 스크립트의 점진적 전환** 까지. 기존 analyze 로직 자체는 변경 0 (호환 layer 만 삽입).

### Step 1 — `experiments/run_helpers.py` 의 `parse_result_meta` 추가

```python
def parse_result_meta(result_data: dict) -> dict:
    """결과 JSON dict 의 top-level meta 를 표준 dict 로 정규화.

    schema_version="1.0" 이면 그대로 반환 (build_result_meta 출력 호환).
    schema_version 부재 (v0) 면 도구별 ad-hoc 키에서 가능한 만큼 추출하고
    부재 필드는 None.

    Returns:
        {schema_version, experiment, model{name,engine,endpoint},
         sampling_params, scorer_version, taskset_version, started_at, ended_at}
    """
    schema = result_data.get("schema_version")
    if schema == "1.0":
        # 신규 — 그대로 추출 (필수 필드 검증)
        return {
            "schema_version": "1.0",
            "experiment": result_data.get("experiment"),
            "model": result_data.get("model") or {"name": None, "engine": None, "endpoint": None},
            "sampling_params": result_data.get("sampling_params") or {},
            "scorer_version": result_data.get("scorer_version"),
            "taskset_version": result_data.get("taskset_version"),
            "started_at": result_data.get("started_at"),
            "ended_at": result_data.get("ended_at"),
        }

    # v0 (구 결과) — 도구별 ad-hoc 키 보수적 추출
    return {
        "schema_version": "0",
        "experiment": result_data.get("experiment"),
        "model": {
            "name": result_data.get("model"),
            "engine": None,
            "endpoint": None,
        },
        "sampling_params": result_data.get("sampling_params") or {},
        "scorer_version": None,
        "taskset_version": None,
        "started_at": result_data.get("started_at"),
        "ended_at": result_data.get("ended_at"),
    }
```

이 함수를 `run_helpers.py` 에 **추가만**. 기존 함수 변경 금지.

### Step 2 — analyze 스크립트 정찰

```bash
.venv/Scripts/python -c "
import glob
patterns = ('experiments/exp*/analyze_*.py', 'experiments/exp*/rescore*.py', 'experiments/exp*/diagnose_*.py')
all_files = []
for p in patterns:
    all_files.extend(glob.glob(p))
for f in sorted(set(all_files)):
    print(f)
"
```

결과 파일 목록 정리. **각 파일이 결과 JSON 의 top-level 키를 직접 참조하는지** 수동 확인.

### Step 3 — 호환 layer 적용 (필요한 경우만)

각 analyze 스크립트가 결과 JSON 의 top-level meta 를 사용하는지 분류:

#### 분류 A — top-level meta 직접 참조 안 함 (대부분)

대부분의 analyze 스크립트는 `result_data["trials"]` / `result_data["results_by_arm"]` 같은 결과 본체만 본다. 본 task 의 호환 layer 적용 **불필요** — Subtask 04 의 변경 영역 0.

#### 분류 B — top-level meta 참조함 (소수)

특정 스크립트가 `result_data["model"]` / `result_data["scorer_version"]` 등을 참조하면, `parse_result_meta(result_data)` 로 우회:

```python
# Before:
model = result_data.get("model")  # v0 면 str, v1.0 이면 dict {name, engine, endpoint}

# After:
from experiments.run_helpers import parse_result_meta
meta = parse_result_meta(result_data)
model_name = meta["model"]["name"]
```

분류 B 에 해당하는 스크립트가 **0~3 개 정도** 예상. 정찰 결과로 확정.

### Step 4 — 직전 결과 JSON 으로 회귀 검증

다음 결과 JSON 에 대해 정찰된 analyze 스크립트가 **변경 후에도 동일 출력** 을 내는지 검증:

```bash
# 4a) Exp09 5-trial drop 분석 회귀 (직전 plan 의 핵심 분석)
.venv/Scripts/python -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo > /tmp/after.txt 2>&1
# (또는 git stash + before 추출 + diff)

# 4b) Exp10 v3 rescore 회귀
# rescore_v3.py 는 직전 결과 (053939, 152306) 를 read-only 사용 — 변경 0 라면 회귀 0
```

본 task 의 변경 영역이 분류 B 의 스크립트 한정이라 회귀 위험 작음. 그러나 검증 의무.

### Step 5 — Backward-compat 정책 disclosure (resultJsonSchema.md 갱신)

subtask 03 의 `docs/reference/resultJsonSchema.md` 의 `## 부재 처리` 절을 보강:

```markdown
## 부재 처리 (analyze 측)

`run_helpers.parse_result_meta(result_data)` 를 호출하면 v0 / v1.0 을 자동 정규화한다.
- schema_version="1.0": 표준 필드 그대로
- schema_version 부재 (v0): 도구별 ad-hoc 키에서 보수적 추출, 부재 필드는 None

신규 analyze 스크립트는 본 helper 사용을 권장 (기존 v0 호환 의무).
기존 스크립트는 분류 B (top-level meta 참조) 에 한해 본 helper 로 전환 — 분류 A 는 변경 불필요.
```

## Dependencies

- subtask 03 완료 (`build_result_meta` + `resultJsonSchema.md`)
- 패키지: 표준만
- 입력: 직전 결과 JSON (Exp09 5-trial / Exp10 v3) — read-only

## Verification

```bash
# 1) parse_result_meta - 신규 schema 정규화
.venv/Scripts/python -c "
from experiments.run_helpers import parse_result_meta
v1 = {
    'schema_version': '1.0',
    'experiment': 'test',
    'model': {'name': 'gemma-4-e4b', 'engine': 'lm_studio', 'endpoint': None},
    'sampling_params': {'temperature': 0.1},
    'scorer_version': 'v3',
}
m = parse_result_meta(v1)
assert m['schema_version'] == '1.0'
assert m['model']['name'] == 'gemma-4-e4b'
print('verification 1 ok: v1.0 정규화')
"

# 2) parse_result_meta - v0 호환
.venv/Scripts/python -c "
from experiments.run_helpers import parse_result_meta
v0 = {'experiment': 'old', 'model': 'gemma-4-e4b'}
m = parse_result_meta(v0)
assert m['schema_version'] == '0'
assert m['model']['name'] == 'gemma-4-e4b'
assert m['scorer_version'] is None
print('verification 2 ok: v0 호환')
"

# 3) 직전 결과 JSON 으로 정규화 dry-run
.venv/Scripts/python -c "
import json, glob
from experiments.run_helpers import parse_result_meta
samples = (
    'experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json',
    'experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260430_152306.json',
)
for s in samples:
    d = json.load(open(s, encoding='utf-8'))
    m = parse_result_meta(d)
    assert m['schema_version'] in ('0', '1.0')
    print(f'{s}: schema={m[\"schema_version\"]}, exp={m[\"experiment\"]!r}, model={m[\"model\"][\"name\"]!r}')
print('verification 3 ok: 직전 결과 호환')
"

# 4) 회귀 검증 - analyze_5trial_drop 변경 전후 동일 출력 (분류 B 영향 시에만)
# 변경 0 이면 skip
```

3 명령 모두 정상 + 회귀 검증.

## Risks

- **Risk 1 — 도구 별 v0 ad-hoc 키 누락**: `parse_result_meta` 의 v0 분기가 도구별 ad-hoc 메타를 모두 흡수하지 못함. 대응: 분류 B 의 스크립트가 직접 ad-hoc 키 fallback (helper 의 None 반환 시).
- **Risk 2 — `result_data["model"]` 의 타입 변경 (v0 str → v1.0 dict)** 으로 기존 코드 깨짐: 분류 B 의 스크립트에서 발견. 본 task 가 helper 로 전환하는 영역이 그곳이므로 직접 영향 0. 단 helper 로 전환되지 않은 분류 A 의 스크립트가 후속 plan 에서 v1.0 결과를 처리하면 깨짐 — 그 시점에 helper 로 전환.
- **Risk 3 — Developer 가 분류 A 스크립트를 임의로 helper 로 전환**: scope creep. 본 task 는 분류 B 한정. 임의 확장 금지.
- **Risk 4 — `parse_result_meta` 의 v0 분기 출력의 `scorer_version` None 처리**: analyze 측에서 None 인지 체크 필요. helper 사용처에 명시 — `if meta["scorer_version"] is None: meta_v = "v0_unknown"` 같은 fallback.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/run_helpers.py` 의 기존 함수 (`classify_trial_error` / `is_fatal_error` / `check_error_rate` / `build_result_meta` / `get_taskset_version` / `normalize_sampling_params`) — subtask 01/03 영역. 본 task 는 `parse_result_meta` 만 추가
- `experiments/orchestrator.py` / `experiments/measure.py` — 본 plan 영역 외
- 모든 `experiments/exp**/run.py` — subtask 02 영역
- `experiments/schema.py` — 변경 금지
- `experiments/tasks/*.json` — Phase 1 후속 영역
- 결과 JSON (모두 read-only)
- 분류 A analyze 스크립트 — 본 task 영역 외
- README / researchNotebook
- 다른 reference 문서 (resultJsonSchema.md 의 부재 처리 절만 갱신)
