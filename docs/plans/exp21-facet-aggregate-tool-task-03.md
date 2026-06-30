---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: exp21-facet-aggregate-tool
parallel_group: B
depends_on: [01]
---

# Task 03 — A/B 드라이버 `run_v21_facet_ab.py`

## Changed files

- `experiments/exp15_context_router/run_v21_facet_ab.py` (신규) — grep-only vs grep+facet A/B 드라이버. 결과 `results/exp21_facet_ab_gemma4_e4b.json`.

> 신규 1, 수정 0.

## Change description

### 배경
`run_v20_megalog.py`(2-task megalog 로더) 패턴을 복제하되, **arm 차원**을 추가한다. 두 arm 의 유일 차이는 native caller 에 facet 도구(`FACET_TOOL_SCHEMAS`/`FACET_TOOL_FUNCTIONS`)를 주입하느냐다.

### Step 1 — 메가로그 로더 재사용
`run_v20_megalog.py` 의 `_load_megalog_to_redis()`/`LOG_PATH`(env `EXP20_LOG_PATH`)/`REDIS_KEY='ctx:test9ng_journal_30d:stdout'`/sanity 카운트 그대로. (scratchpad 재pull 필요.)

### Step 2 — 2 task 정의 (run_v20 의 TASKS 그대로)
- A: gohttpserver 크래시루프, keywords `[["gohttpserver"],["failed"]]`.
- B: SSH brute-force top-IP, keywords `[["45.144.212.75"]]`.

### Step 3 — arm 정의
```python
from tools import FACET_TOOL_SCHEMAS, FACET_TOOL_FUNCTIONS
ARMS = [
    {"id": "grep_only",  "extra_schemas": None,              "extra_fns": None},
    {"id": "grep_facet", "extra_schemas": FACET_TOOL_SCHEMAS, "extra_fns": FACET_TOOL_FUNCTIONS},
]
```
`_run_with_retry(task, arm)`:
```python
caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX,
            extra_tool_schemas=arm["extra_schemas"], extra_tool_fns=arm["extra_fns"])
tt, logs, ans = run_abc_chain(..., max_cycles=8, model_caller=caller,
            context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
            mandatory_tool_prompt=True)
```
나머지(retry K=2, `_score`, `_synth`)는 run_v20 동일.

### Step 4 — 측정 (1차 지표 = non-null ans rate)
trial 별 `ans is not None` 기록. arm×task 별로:
- `non_null_rate` = non-null ans 수 / n  ← **1차 지표**
- `mean_score` (keyword) ← 2차
- `mean_attempts`, `facet_used`(arm=grep_facet 시 aggregate_context 호출 횟수 — `stats` dict 또는 tool 로깅으로 캡처)

### Step 5 — 결과 JSON 구조
```json
{ "experiment":"exp21_facet_ab", "model":"gemma4:e4b", "approx_tokens":..., "n_lines":...,
  "n_trials":5, "max_cycles":8, "max_retries":2,
  "arms": { "grep_only": { "exp21a_crashloop": {"non_null_rate":.., "mean_score":.., "answers":[..]},
                            "exp21b_bruteforce": {...} },
            "grep_facet": { ... "facet_calls": N ... } } }
```
trial 마다 디스크 flush(중단 내성). healthcheck(터널+gemma4:e4b) 선행, ABORT-on-fail.

### Step 6 — 실행 가이드(드라이버 주석)
- boxie 원격 → 에이전트 직접 실행 가능. `python -u run_v21_facet_ab.py` (stdout block-buffer 회피) 또는 결과 JSON polling.
- 순서: arm × task × n=5 = 4 cell × 5 = 20 chain(각 ≤3 attempt). megalog grep ~2-3초/호출 → cell 당 수 분.

## Dependencies

- task-01(facet + caller opt-in). task-02 와 병렬(테스트는 실행 전 통과 권장).
- 기존(read-only): `run_v20_megalog.py`(로더 패턴), `native_ollama_caller.py`(opt-in caller), `orchestrator.run_abc_chain`.
- 데이터: megalog 재pull(`ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw`), boxie 터널 11435.

## Verification

```bash
# 1) syntax + import (네트워크 없이)
cd experiments && python -c "import ast; ast.parse(open('exp15_context_router/run_v21_facet_ab.py',encoding='utf-8').read()); print('driver syntax OK')"
cd experiments/exp15_context_router && python -c "import run_v21_facet_ab as m; print('arms:', [a['id'] for a in m.ARMS], 'tasks:', [t['id'] for t in m.TASKS])"

# 2) healthcheck (터널 + 모델) — 실행 전 사전 점검
curl -s http://127.0.0.1:11435/api/tags | python -c "import sys,json; print([x['name'] for x in json.load(sys.stdin)['models']])"

# 3) (에이전트/사용자) 실행 — megalog Redis 적재 후
cd experiments/exp15_context_router && python -u run_v21_facet_ab.py
# 진척: results/exp21_facet_ab_gemma4_e4b.json 의 arms.*.* non_null_rate 확인
```

## Risks

1. **양 arm 0v0**(parent Risk 1) → 즉시 사용자 호출, harness 수렴 사안으로 회부.
2. grep_facet arm 이 facet 을 한 번도 호출 안 함 → `facet_calls==0` 면 "도구 제공≠사용" finding(arm 차이 무의미). description/예시 보강은 task-01 범위라 사용자 호출.
3. 117MB Redis 키가 LRU 로 mid-run 축출(타 프로젝트 부하) → grep "handle not found". 대응: 로더 reuse-or-respool, 발생 시 재적재.
4. stdout block-buffer 로 진척 안 보임 → `python -u` 또는 결과 JSON polling(드라이버가 trial 마다 flush).
5. `test_static` 결과-인벤토리 카운트가 신규 `exp21_*.json` 으로 흔들릴 수 있음 → 결과 생성 후 `test_static` 카운트 갱신 필요(task-04 또는 후속 위생 커밋에서).

## Scope boundary

- **수정 금지**: `context_tools.py`, `native_ollama_caller.py`(task-01 영역), `orchestrator.py`, `run_v20_megalog.py`, 테스트.
- 본 task 는 신규 드라이버만. 분석/verdict 는 task-04.
