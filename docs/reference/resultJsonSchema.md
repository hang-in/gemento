---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# 결과 JSON top-level Schema (v1.0)

## 의도

**Stage 2A 마감 (2026-04-30) 후 신규 작성되는 도구** 의 결과 JSON top-level 에 본 schema 를 적용한다.
- 적용 대상: Stage 2C 의 `experiments/exp_h4_recheck/run.py`, Stage 4 의 Exp11 도구, 그 이후 신규 도구
- 적용 제외: 기존 도구 (`experiments/exp00_baseline/run.py` ~ `experiments/exp10_reproducibility_cost/run.py`) 의 신규 run — v0 (schema_version 부재) 유지
- 명시 배제: 기존 Exp00~10 결과 JSON 의 retroactive 보강

근거: 사용자 합의 "작은 B" 전략 — 기존 도구는 healthcheck/abort 만 patch (Stage 2A task-02 적용 완료), meta v1.0 retrofit 은 ROI 부족.
analyze 스크립트는 `schema_version` 부재 시 v0 호환 처리 (`experiments/run_helpers.py:parse_result_meta` — Stage 2A task-04).

## 표준 필드

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

## 예시 (v1.0)

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
  "conditions": ["..."],
  "trials": ["..."]
}
```

## 도구별 적용 코드 stub

신규 도구의 결과 저장 직전에 적용한다:

```python
from experiments.run_helpers import build_result_meta, get_taskset_version, normalize_sampling_params
import datetime as _dt

started = _dt.datetime.now().astimezone().isoformat()
# ... run ...
ended = _dt.datetime.now().astimezone().isoformat()

meta = build_result_meta(
    experiment="exp11_xxx",                # 도구별 고정값
    model_name="gemma-4-e4b",              # 도구별 / condition 별
    model_engine="lm_studio",
    model_endpoint="http://localhost:1234/v1",
    sampling_params=normalize_sampling_params(SAMPLING_PARAMS),
    scorer_version="v3",
    taskset_version=get_taskset_version(),
    started_at=started,
    ended_at=ended,
)
result_data = {**meta, **existing_fields}  # top-level 에 unpack — nested 화 금지
```

## 도구별 model_name / engine 매핑

| 도구 | model_name | engine | endpoint |
|------|-----------|--------|---------|
| LM Studio (로컬) | `gemma-4-e4b` (또는 실제 로드된 모델명) | `lm_studio` | `http://localhost:1234/v1` |
| Ollama (로컬) | `gemma4:e4b` | `ollama` | `http://localhost:11434` |
| Gemini API | `gemini-2.5-flash` | `gemini` | null |
| Anthropic API | `claude-haiku-4-5` | `anthropic` | null |

## 확장 정책

- v1.0 → v1.1: 필드 추가만 (backward compat 유지)
- v2.0: 기존 필드 변경 / 제거 시 (analyze 스크립트 동시 갱신 필수)

## 부재 처리 (analyze 측)

`run_helpers.parse_result_meta(result_data)` 를 호출하면 v0 / v1.0 을 자동 정규화한다.
- `schema_version="1.0"`: 표준 필드 그대로
- `schema_version` 부재 (v0): 도구별 ad-hoc 키에서 보수적 추출, 부재 필드는 None

신규 analyze 스크립트는 본 helper 사용을 권장 (기존 v0 호환 의무).
기존 스크립트는 분류 B (top-level meta 참조) 에 한해 본 helper 로 전환 — 분류 A 는 변경 불필요.
