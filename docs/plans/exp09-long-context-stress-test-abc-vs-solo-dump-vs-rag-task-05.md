---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: B
depends_on: [02, 04]
---

# Task 05 — ABC chunked 오케스트레이터 (`run_abc_chunked`)

## Changed files

- `experiments/orchestrator.py`
  - `run_abc_chain()` (line 481~) 뒤에 `run_abc_chunked()` 신규 함수 추가
  - 기존 `run_abc_chain` 로직을 **최대한 재사용** — 복제보다 유틸 함수 호출
- `experiments/system_prompt.py`
  - `SYSTEM_PROMPT` 하단에 "Long-context chunked processing" 섹션 추가 (A에게 chunk 기반 처리 안내)
  - 또는 신규 `build_prompt_chunked(tattoo_json, current_chunk)` 함수 추가

## Change description

### Step 1 — 설계 — chunk-by-chunk iteration

```
For each chunk in chunks:
    1. A (Proposer): 현재 chunk 내용 + 질문 + 누적 Tattoo를 보고
       - chunk에서 새 증거가 나오면 evidence_ref={"chunk_id": idx} 첨부한 assertion 생성
       - 증거 없으면 skip (새 assertion 0개)
    2. B (Critic): 모든 assertion 교차 검증 (매 chunk마다가 아닌, 마지막 chunk 이후 1회)
    3. C (Judge): 수렴 판단 (마지막 chunk 이후)

변형: 매 chunk마다 B·C 돌리는 "full cycle per chunk" 방식도 있으나 비용이 N배
→ MVP는 "A per chunk, B+C 1회 최종"
```

### Step 2 — `run_abc_chunked()` 함수 시그니처

```python
def run_abc_chunked(
    task_id: str,
    question: str,
    chunks: list[dict],  # chunker.Chunk.to_dict() 리스트
    constraints: list[str] | None = None,
    termination: str = "모든 증거가 종합되고 최종 답변이 확정되면 종료",
    logger=None,
    max_final_cycles: int = 5,  # 모든 chunk 처리 후 B→C→재수정 루프 상한
) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
    """Long-context ABC: chunk별로 A 호출하며 증거 누적, 최종 B+C 수렴.
    
    반환: (tattoo, cycle_logs, final_answer) — 기존 run_abc_chain과 동일
    """
```

### Step 3 — 구현 골격

```python
def run_abc_chunked(task_id, question, chunks, constraints=None,
                   termination="...", logger=None, max_final_cycles=5):
    from system_prompt import build_prompt_chunked, build_critic_prompt, build_judge_prompt
    
    # 초기 Tattoo (objective에 question 포함, chunk 정보는 loop별 user content에)
    tattoo = create_initial_tattoo(
        task_id=task_id,
        objective=f"{question}",
        constraints=constraints,
        termination=termination,
    )
    
    logs: list[ABCCycleLog] = []
    
    # Phase 1: Chunk iteration — A per chunk
    for chunk in chunks:
        tattoo.phase = Phase.INVESTIGATE
        tattoo.next_directive = (
            f"Read the CURRENT CHUNK (id={chunk['chunk_id']}) and extract any NEW "
            f"assertions that help answer the question. Attach evidence_ref="
            f"{{\"chunk_id\": {chunk['chunk_id']}}} to each new assertion. "
            f"If the chunk contains nothing relevant, produce zero new assertions."
        )
        # A 호출 — 기존 run_loop 변형
        messages = build_prompt_chunked(
            tattoo_json=json.dumps(tattoo.to_dict(), ensure_ascii=False),
            current_chunk=chunk["content"],
            chunk_id=chunk["chunk_id"],
        )
        raw, _ = call_model(messages)
        parsed = extract_json_from_response(raw)
        if parsed:
            # 기존 apply_llm_response 재사용 — assertion 내부에 evidence_ref 포함
            tattoo, answer = apply_llm_response(tattoo, parsed, loop_index=chunk["chunk_id"])
        # 각 chunk의 cycle log 기록 — logger.chunk_processed() 등 확장
    
    # Phase 2: 최종 종합 — 기존 B→C 루프를 max_final_cycles 만큼 실행
    tattoo.phase = Phase.SYNTHESIZE
    final_answer = None
    
    for cycle in range(1, max_final_cycles + 1):
        # B (Critic) — 모든 active assertion에 대해
        b_messages = build_critic_prompt(
            question,
            [a.to_dict() for a in tattoo.active_assertions],
            handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
        )
        b_raw, _ = call_model(b_messages)
        b_parsed = extract_json_from_response(b_raw)
        # apply_critique_response(tattoo, b_parsed)
        
        # C (Judge) — 수렴 판단 + 최종 답변
        c_messages = build_judge_prompt(
            question,
            [a.to_dict() for a in tattoo.active_assertions],
            handoff_b2c=tattoo.handoff_b2c.to_dict() if tattoo.handoff_b2c else None,
        )
        c_raw, _ = call_model(c_messages)
        c_parsed = extract_json_from_response(c_raw)
        # apply_judge_response(tattoo, c_parsed)
        
        if c_parsed and c_parsed.get("converged"):
            tattoo.phase = Phase.CONVERGED
            final_answer = c_parsed.get("final_answer") or final_answer
            break
    
    return tattoo, logs, final_answer
```

**주의**: `apply_llm_response`, `apply_critique_response`, `apply_judge_response` 등 helper는 기존 `run_abc_chain`에 내장되어 있을 것 — **코드 복제 대신 private helper로 추출하거나 inline 호출**. Developer가 기존 구조를 보고 판단.

### Step 4 — `system_prompt.py` 변경

`build_prompt_chunked` 신규 함수 추가:

```python
def build_prompt_chunked(tattoo_json: str, current_chunk: str, chunk_id: int) -> list[dict]:
    """Long-context chunked 호출용 A 프롬프트.
    
    기존 build_prompt와 구조 동일하되 user content에 CURRENT CHUNK 섹션 주입.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_content = (
        f"## Current Tattoo\n\n```json\n{tattoo_json}\n```\n\n"
        f"## Current Chunk (id={chunk_id})\n\n{current_chunk}\n\n"
        f"Extract any NEW assertions from THIS chunk that help answer the objective. "
        f"Attach `evidence_ref`: {{\"chunk_id\": {chunk_id}}} to each new assertion. "
        f"If nothing relevant is in this chunk, return zero new_assertions."
    )
    messages.append({"role": "user", "content": user_content})
    return messages
```

### Step 5 — SYSTEM_PROMPT 확장 (선택적)

기존 SYSTEM_PROMPT에 별도 섹션 추가:

```
## Long-context chunked mode

When you receive a "Current Chunk" section in the user message, you are reading
one segment of a larger document. Your job is to:
1. Extract only NEW assertions relevant to the objective from THIS chunk.
2. Attach `evidence_ref`: {"chunk_id": N} to each new assertion — N matches the
   chunk id given in the user message.
3. Do not repeat assertions already present in the current Tattoo.
4. If this chunk contains no useful evidence, return `new_assertions: []`.
```

### Step 6 — Non-goals (본 Task 범위 외)

- "per-chunk B 검증" 모드 → MVP에서 제외. 비용 급증.
- 동적 chunk ordering (BM25 relevance 기반 chunk 순서 재배치) → RAG arm에서 처리, ABC arm은 자연 순서 고수.
- evidence_ref span [start, end] 자동 추출 → MVP는 chunk_id만. span 필드는 Optional로 None.

## Dependencies

- **Task 02 완료**: `tools.chunker.Chunk` 구조 필요 (chunk dict 인터페이스).
- **Task 04 완료**: `Assertion.evidence_ref` 필드 필요.
- Task 01 없어도 단위 테스트 가능 (mock chunks).
- Task 03(BM25) 없어도 됨 — ABC arm은 BM25 사용 안 함.

## Verification

```bash
# 1. 함수 존재 + 시그니처 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import inspect
from orchestrator import run_abc_chunked
sig = inspect.signature(run_abc_chunked)
required = {'task_id', 'question', 'chunks'}
assert required.issubset(sig.parameters), f'missing params: {required - set(sig.parameters)}'
print('OK signature:', list(sig.parameters))
"

# 2. build_prompt_chunked 존재
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from system_prompt import build_prompt_chunked
msgs = build_prompt_chunked('{\"test\": 1}', 'sample chunk content', chunk_id=7)
assert len(msgs) == 2 and msgs[0]['role'] == 'system'
assert 'Current Chunk' in msgs[1]['content']
assert 'chunk_id=7' in msgs[1]['content'] or 'id=7' in msgs[1]['content']
print('OK build_prompt_chunked')
"

# 3. SYSTEM_PROMPT에 chunked mode 섹션 추가됨
grep -c "Long-context chunked mode\|Current Chunk" experiments/system_prompt.py
# 기대: 2 이상 (SYSTEM_PROMPT + build_prompt_chunked 내부)

# 4. Mock chunks로 run_abc_chunked 드라이런 (실제 LLM 호출 없이 smoke)
# → 실제 LLM 호출은 Task 06 통합 실행 시점에 검증. 여기선 import + signature만.
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import orchestrator
# run_abc_chunked 호출 가능성만 확인 (실제 호출은 서버 의존이라 skip)
assert hasattr(orchestrator, 'run_abc_chunked')
assert hasattr(orchestrator, 'run_abc_chain')  # 기존 함수 회귀 없음
print('OK both functions present')
"

# 5. 기존 실험(run_abc_chain, run_tool_use) 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
assert 'tool-use' in EXPERIMENTS and 'tool-use-refined' in EXPERIMENTS
assert 'handoff-protocol' in EXPERIMENTS
print('OK existing experiments intact')
"
```

## Risks

- **코드 복제 유혹**: `run_abc_chain`을 통째로 복사하면 유지보수 이중화. 최대한 재사용 — 헬퍼 추출이 필요하면 **작고 명확한 단위로만** (예: `_run_single_a_call`, `_run_b_critique`, `_run_c_judge`).
- **Assertion 수 폭증**: 20K words / 500 words_per_chunk × ~5 assertions_per_chunk = **최대 200 assertions**. `ASSERTION_SOFT_CAP=8`이 크게 초과 → soft_cap 적용 방식 재검토 필요. 현재 코드는 "high confidence만 active"로 필터링하지만 long-context에서는 **chunk별 증거를 모두 active로 유지**해야 함. `select_assertions`의 cap을 ABC chunked에서는 훨씬 크게 (예: 64).
- **Prompt 길이**: 매 chunk 호출 시 Tattoo 전체(누적 assertions)를 포함하면 토큰이 급증. Assertion 직렬화 시 최소 표현(`id`, `content`, `evidence_ref`) 고려. n_ctx 8K 제약 필수 준수.
- **final_answer 미생성**: 마지막 C 루프에서 converged=False로 끝나면 `final_answer=None`. 기존 Exp08 유사 패턴이므로 동일 처리.
- **`build_prompt` 기존 호출부 영향**: `build_prompt_chunked`는 **신규 함수**이므로 기존 호출부에 영향 없음. `build_prompt` 자체는 건드리지 않음.
- **code-review-graph 영향**: `run_abc_chunked`는 `call_model`, `extract_json_from_response`, `apply_llm_response` 등 기존 함수 호출. 영향 범위 크므로 Task 06 실제 실행에서 회귀 감지.

## Scope boundary

**Task 05에서 절대 수정 금지**:
- `run_abc_chain()` 기존 함수 — 건드리지 않음. 복제·호출만.
- `run_loop()`, `run_chain()` 기존 함수.
- `experiments/tools/` 내 모든 파일 (chunker import만 허용)
- `experiments/schema.py` (Task 04 완료 후 import만 허용)
- `experiments/run_experiment.py` (Task 06 영역)
- `experiments/measure.py`, `experiments/tasks/`
- `CRITIC_PROMPT`, `JUDGE_PROMPT`, `build_critic_prompt*`, `build_judge_prompt*` — 건드리지 않음. 재사용만.

**허용 범위**:
- `experiments/orchestrator.py`에 `run_abc_chunked` 함수 추가 (+ 필요 시 private helper 2~3개 추출)
- `experiments/system_prompt.py`에 `build_prompt_chunked` 신규 함수 + `SYSTEM_PROMPT` 하단에 섹션 1개 추가
