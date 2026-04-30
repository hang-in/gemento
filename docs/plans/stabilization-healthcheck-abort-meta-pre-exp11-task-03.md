---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: stabilization-healthcheck-abort-meta-pre-exp11
parallel_group: B
depends_on: []
---

# Task 03 — 결과 JSON top-level meta 표준화 (helper + reference 문서)

## Changed files

- `experiments/run_helpers.py` — **수정 (subtask 01 의 신규 파일에 함수 1개 추가만)**. `build_result_meta` 가 subtask 01 에 이미 정의되어 있으면 read-only. 단 본 task 는 helper 가 client 별 sampling_params 정규화를 추가 처리해야 할 가능성 있어 helper 내부 보강
- `docs/reference/resultJsonSchema.md` — **신규**. 결과 JSON top-level meta schema reference

신규 1, 수정 1 (subtask 01 의 helper 보강).

## Change description

### 배경

직전 결과 JSON (Exp00~10) 의 top-level meta 가 도구별로 분산되어 있어 향후 분석 / 비교 / (장기) DB import 시 정규화 비용 큼. 본 task 는 **신규 run 만 적용** 하는 schema_version="1.0" 표준 정의 + 각 도구 적용은 **subtask 02 와 병렬 진행** (group B).

본 task 는 schema 정의 + reference 문서 + helper 보강까지. **기존 결과 JSON 에 meta 를 retroactive 추가 금지** (사용자 명시 배제, 본 plan Non-goals).

### Step 1 — schema_version="1.0" 정의

표준 top-level 필드 (subtask 01 의 `build_result_meta` 시그니처 참조):

```json
{
  "schema_version": "1.0",
  "experiment": "exp10_reproducibility_cost",
  "started_at": "2026-04-30T15:23:06+09:00",
  "ended_at": "2026-04-30T15:25:42+09:00",
  "model": {
    "name": "gemma-4-e4b",
    "engine": "lm_studio",
    "endpoint": "http://localhost:1234/v1"
  },
  "sampling_params": {
    "temperature": 0.1,
    "top_p": 1.0,
    "max_tokens": 4096,
    "seed": null
  },
  "scorer_version": "v3",
  "taskset_version": "6206c3b",
  "conditions": [...],
  "trials": [...]
}
```

각 필드 의미:

| 필드 | 타입 | 의미 | 부재 시 처리 |
|------|------|------|-------------|
| `schema_version` | str | 본 표준 버전. v1.0 시작. 후속 변경 시 v1.1 / v2.0 | 부재 = "0" (구 결과) |
| `experiment` | str | 실험 식별자 (`exp10_reproducibility_cost` 등) | 필수 |
| `started_at` / `ended_at` | ISO 8601 str | run 시작/종료 시각 | 선택 (있으면 도구가 채움) |
| `model.name` | str | 모델 이름 (`gemma-4-e4b`, `gemini-2.5-flash`, `claude-haiku-4-5` 등) | 필수 |
| `model.engine` | str | inference engine (`ollama`, `lm_studio`, `gemini`, `anthropic`, ...) | 필수 |
| `model.endpoint` | str \| null | API endpoint URL. 로컬은 `http://localhost:1234/v1` 등, 클라우드는 null 또는 base URL | 선택 |
| `sampling_params.temperature` | float | sampling temperature | 필수 |
| `sampling_params.top_p` | float | nucleus sampling | 선택 |
| `sampling_params.max_tokens` | int | 응답 최대 토큰 | 선택 |
| `sampling_params.seed` | int \| null | sampling seed (재현성) | 선택 |
| `scorer_version` | str | 채점기 버전 (`v0`, `v2`, `v3`) | 필수 |
| `taskset_version` | str | `experiments/tasks/taskset.json` 의 commit 시점 git short hash | 선택 |
| `conditions` / `trials` / `results_by_arm` 등 | array \| object | 도구별 결과 본체 | 도구별 |

### Step 2 — `experiments/run_helpers.py` 의 `build_result_meta` 보강

subtask 01 에서 정의된 `build_result_meta` 가 본 task 의 schema 와 일치하는지 확인. 일치하면 변경 0. 불일치 시 다음만 보강:

- `taskset_version` 자동 추출 helper:

```python
def get_taskset_version() -> str | None:
    """taskset.json 의 git short hash 반환. 깨지면 None.

    git 미설치 / 변경된 파일 등 경계 상황은 None 반환 (silent fallback).
    """
    import subprocess
    from pathlib import Path

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h", "experiments/tasks/taskset.json"],
            capture_output=True, text=True, cwd=Path(__file__).resolve().parent.parent,
            timeout=5,
        )
        h = (result.stdout or "").strip()
        return h or None
    except Exception:
        return None
```

이 함수를 `run_helpers.py` 에 **추가만** (기존 함수 변경 금지).

- `sampling_params` 정규화 helper:

```python
def normalize_sampling_params(raw: dict) -> dict:
    """client 별 sampling_params 표현 차이를 표준 dict 로 정규화.

    표준 키: temperature, top_p, max_tokens, seed.
    raw 의 다른 키는 보존하되 표준 키 우선.
    """
    standard = ("temperature", "top_p", "max_tokens", "seed")
    out: dict = {k: raw.get(k) for k in standard if k in raw}
    for k, v in raw.items():
        if k not in standard:
            out[k] = v
    return out
```

이것도 **추가만**.

### Step 3 — 도구별 적용은 subtask 02 의 healthcheck 와 함께

각 도구의 결과 저장 직전:

```python
from experiments.run_helpers import build_result_meta, get_taskset_version, normalize_sampling_params
from experiments.config import SAMPLING_PARAMS  # 도구별 import 경로
import datetime as _dt

started = _dt.datetime.now().astimezone().isoformat()
# ... run ...
ended = _dt.datetime.now().astimezone().isoformat()

meta = build_result_meta(
    experiment="exp10_reproducibility_cost",  # 도구별 고정값
    model_name="gemma-4-e4b",                  # 도구별 / condition 별
    model_engine="lm_studio",                   # 도구별
    model_endpoint=os.environ.get("LM_STUDIO_BASE", "http://localhost:1234/v1"),
    sampling_params=normalize_sampling_params(SAMPLING_PARAMS),
    scorer_version="v3",                        # 도구별 - measure.py 호출 시 사용한 버전
    taskset_version=get_taskset_version(),
    started_at=started,
    ended_at=ended,
)
result_data = {**meta, ...existing_fields...}
```

**중요**: `result_data = {**meta, ...}` 로 unpack 하여 top-level 에 meta 가 spread. `result_data["meta"] = meta` 처럼 nested 화 금지 (analyze 호환성).

도구별 적용은 **subtask 02 의 patch 와 함께 진행** — Developer 가 한 commit 으로 묶음.

### Step 4 — `docs/reference/resultJsonSchema.md` 신규

본 task 가 정의한 schema 를 reference 문서로 작성:

```markdown
---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# 결과 JSON top-level Schema (v1.0)

## 의도

향후 모든 신규 실험 (Exp11+) 의 결과 JSON top-level 에 본 schema 를 적용한다.
기존 Exp00~10 결과 JSON 의 retroactive 보강은 명시 배제.
analyze 스크립트는 schema_version 부재 시 v0 호환 처리 (subtask 04).

## 표준 필드

(Step 1 의 표 그대로 복사)

## 도구별 적용 예

(Step 3 의 코드 stub 그대로 복사 + 도구별 model_name / engine 매핑 표)

## 확장 정책

- v1.0 → v1.1: 필드 추가만 (backward compat 유지)
- v2.0: 기존 필드 변경 / 제거 시 (analyze 스크립트 동시 갱신 필수)

## 부재 처리 (analyze 측, subtask 04)

- `schema_version` 부재 = "0" 으로 처리
- v0 결과 JSON 의 도구별 ad-hoc meta (`results_by_arm`, `_substitutions`, `_v3_rescore` 등) 는 보존
```

## Dependencies

- 패키지: 표준만 (`subprocess`, `datetime`)
- 다른 subtask: 없음 (parallel_group B, 첫 노드)
- 출력: helper 는 subtask 02 가 사용, schema 문서는 subtask 04 의 호환성 분기 근거

## Verification

```bash
# 1) build_result_meta + 신규 helper signature
.venv/Scripts/python -c "
from experiments.run_helpers import (
    build_result_meta, get_taskset_version, normalize_sampling_params,
)
m = build_result_meta(
    experiment='dry_run',
    model_name='test',
    model_engine='test',
    model_endpoint=None,
    sampling_params={'temperature': 0.1, 'top_p': 1.0, 'max_tokens': 100, 'seed': None},
    scorer_version='v3',
)
assert m['schema_version'] == '1.0'
assert m['model']['name'] == 'test'
assert m['sampling_params']['temperature'] == 0.1
assert m['scorer_version'] == 'v3'
norm = normalize_sampling_params({'temperature': 0.1, 'extra_field': 'preserved'})
assert norm['temperature'] == 0.1
assert norm['extra_field'] == 'preserved'
print('verification 1 ok: meta helper + normalize')
"

# 2) get_taskset_version 동작
.venv/Scripts/python -c "
from experiments.run_helpers import get_taskset_version
v = get_taskset_version()
print(f'taskset_version: {v!r}')
assert v is None or len(v) >= 4
print('verification 2 ok: taskset_version')
"

# 3) schema 문서 존재 + canonical 표시
.venv/Scripts/python -c "
text = open('docs/reference/resultJsonSchema.md', encoding='utf-8').read()
assert 'schema_version' in text
assert 'canonical: true' in text or 'canonical:true' in text
print('verification 3 ok: schema 문서')
"
```

3 명령 모두 정상.

## Risks

- **Risk 1 — `get_taskset_version` 의 git 호출 비용**: subprocess 호출이 5s timeout. 대량 trial 환경에서 병목 가능성. 대응: 도구가 한 번 호출 후 변수에 캐시.
- **Risk 2 — 도구별 sampling_params 표현 차이**: `lmstudio_client.py` 가 `SAMPLING_PARAMS` 를 그대로 forward 하지만, `gemini_client.py` 는 `generation_config` 형태일 가능성. `normalize_sampling_params` 로 1차 흡수 — 부족하면 client 별 분기.
- **Risk 3 — `model_endpoint` 의 PII 위험**: 사용자 사설 endpoint (`http://yongseek.iptime.org:8005`) 가 결과 JSON 에 노출되면 README 외부 공개 시 부주의 노출 가능. 대응: endpoint 는 host 부분만 (e.g. `lmstudio_local` 또는 `<masked>`) — 기본 동작은 raw URL 그대로 + Risk 항목으로 disclosure. 사용자 결정 의존 (parent plan §사용자 결정 의존 사항 의 결정 4 후보 — 현재 plan 에서는 raw URL 기본).
- **Risk 4 — schema_version 의 도구간 불일치**: 일부 도구만 v1.0 적용하면 mixed 상태. 대응: subtask 02 와 병렬 진행 + subtask 05 의 dry-run 검증에서 모든 도구의 신규 출력이 v1.0 인지 확인.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/schema.py` — 신규 meta 는 helper 의 dict 반환만. dataclass / TypedDict 추가 금지 (over-engineering)
- `experiments/orchestrator.py` / `experiments/measure.py` — 본 plan 영역 외
- 모든 `experiments/exp**/run.py` — subtask 02 영역 (본 task 는 helper 만)
- 모든 client (`lmstudio_client.py`, `gemini_client.py`, ...) — 변경 금지
- `experiments/config.py` — 변경 금지 (`SAMPLING_PARAMS` 정의 보존)
- 모든 analyze 스크립트 — subtask 04 영역
- 결과 JSON (모두 read-only)
- README / researchNotebook
- docs/reference 의 다른 reference 문서 (resultJsonSchema.md 만 신규)

## Risk 4 사용자 결정 호출 필요 여부

`model_endpoint` 의 raw URL 노출 정책은 **사용자 결정**:
- 옵션 A: raw URL 그대로 (기본). 향후 README 공개 commit 시 별도 마스킹 절차
- 옵션 B: helper 가 자동 마스킹 (`http://localhost:*`/`http://127.0.0.1:*` 외는 host 만 남김)

본 task 의 default 는 **옵션 A**. 사용자가 옵션 B 결정 시 helper 보강 추가 (Architect 가 plan 수정 후 진행).
