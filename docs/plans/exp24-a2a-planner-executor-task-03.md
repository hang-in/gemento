---
type: plan-task
status: pending
updated_at: 2026-07-03
parent_plan: exp24-a2a-planner-executor
parallel_group: C
depends_on: [01]
---

# Task 03 — A/B 드라이버 (control vs a2a)

## Changed files

- `experiments/exp15_context_router/run_v24_a2a_ab.py` (신규) — control(monolithic A) vs a2a(Planner→Executor) × task A × n=15, single-attempt. 실행은 사용자/에이전트.

요약: 신규 1, 수정 0.

## Change description

### 배경
`run_v23_failed_units_ab.py` 인프라 재사용. arm 차이는 `run_abc_chain(a2a_proposer=...)` 플래그 하나. per-attempt 측정이므로 single-attempt, task A.

### Step 1 — 드라이버 작성
2 arm:
```python
ARMS = [
    {"id": "control", "a2a": False},
    {"id": "a2a",     "a2a": True},
]
```
- `run_v21_facet_ab.py` 인프라(`BASE_URL`/`MODEL`/`NUM_CTX`/`REDIS_KEY`/`TASKS`/`_healthcheck`/`_load_megalog_to_redis`) 모듈 import 재사용.
- caller: `make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)` (Planner 가 도구 씀 → context_router=True 로 도구 주입).
- `run_abc_chain(task_id=..., objective=..., prompt=..., constraints=TASK["constraints"], max_cycles=8, model_caller=caller, context_router=True, error_blocks=False, context_handles=[REDIS_KEY], mandatory_tool_prompt=True, a2a_proposer=arm["a2a"])`.
- task = `exp21a_crashloop`, N=15/arm.
- 측정: `finalized`(ans not None), `correct`("gohttpserver" in ans), `n_assertions`, `n_cycles`. 결과 `diagnostics/v24_a2a_result.json`, 증분 write.
- **GPU 부하 대비**: §21 교훈 — arm 순차 preempt 시 단독 arm 러너 필요할 수 있음. 드라이버는 arm 별 완주 후 다음 arm 진행하되, 증분 저장으로 부분 보존.

### Step 2 — 실행 안내 docstring
```
# 사용자/에이전트 실행 (boxie 터널 필요):
#   python -u experiments/exp15_context_router/run_v24_a2a_ab.py
```

## Dependencies

- Task 01 완료 (`a2a_proposer` 파라미터 존재 — 없으면 a2a arm 이 control 과 동일).
- 외부(실행 시점): boxie 터널 + Redis 메가로그.
- 기존 파일 (read-only): `run_v21_facet_ab.py`, `run_v23_failed_units_ab.py`(패턴), `orchestrator.py:run_abc_chain`.

## Verification

```bash
# 1. syntax
python -c "import ast; ast.parse(open(r'experiments/exp15_context_router/run_v24_a2a_ab.py',encoding='utf-8').read()); print('syntax OK')"
```

```bash
# 2. arm + a2a 플래그 정적 확인
python -c "s=open(r'experiments/exp15_context_router/run_v24_a2a_ab.py',encoding='utf-8').read(); assert 'a2a_proposer=' in s; assert \"'control'\" in s and \"'a2a'\" in s; assert 'exp21a_crashloop' in s; print('arms+flag+task OK')"
```

```bash
# 3. (사용자/에이전트 실행 — 터널) 실제 A/B
#   python -u experiments/exp15_context_router/run_v24_a2a_ab.py
#   → diagnostics/v24_a2a_result.json (2 arm × n=15)
```

## Risks

1. **에이전트 실수 실행** — 긴 실험. Verification 3 사용자/에이전트 명시.
2. **a2a arm 비용 2배 → GPU 부하 심화 kill** — §21 처럼 단독 arm 러너 대비. 증분 저장.
3. **결과 유실** — `diagnostics/` durable + 증분.
4. **control arm 재현성** — control 은 기존 Exp23 control(~47%)과 정합해야 — 첫 몇 trial 로 sanity.

## Scope boundary

**수정 금지**: `orchestrator.py`/`system_prompt.py`(Task 01), `run_v21`/`run_v23`(read-only), 테스트. 신규 드라이버 1개만. 실험 실행 금지(사용자/에이전트).
