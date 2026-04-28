---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: B
depends_on: [04]
---

# Task 05 — orchestrator JSON 추출 강화

## Changed files

- `experiments/orchestrator.py` — **수정**. `_loads_json_lenient` (line 155) 와 `extract_json_from_response` (line 167) 사이 또는 후방에 partial recovery helper 추가. `extract_json_from_response` 의 본문에 fence 미닫힘 / partial JSON 복구 fallback 추가.
- `experiments/tests/test_static.py` — **수정**. `TestExtractJsonFromResponseV3` 클래스 신규. Task 04 의 진단 결과 케이스로 검증.

신규 파일 0.

## Change description

### 배경

Task 04 진단 결과 (`docs/reference/exp10-v3-abc-json-fail-diagnosis.md`) 의 분류에 따라 patch 방향이 결정됨. 가장 가능성 높은 시나리오:

- **(a) truncate 다수**: `original_len > 4096` 라 raw 원본 손실. orchestrator 자체 patch 는 미래 run 의 max_tokens 한계 응답 처리 — partial JSON brace 균형 복구 fallback 필요.
- **(b) fence_unclosed 다수**: ``` 시작 후 닫는 fence 못 만남. 현재 정규식 `r"```(?:json)?\s*([\s\S]*?)\s*```"` 는 닫힘 fence 필수 → 매칭 실패. fence 시작 다음부터 raw 끝까지 잘라 lenient parse 시도 필요.

본 task 는 두 시나리오 모두 처리하는 fallback 추가. Task 04 진단 결과가 어느 쪽이든 patch 가 동작.

### Step 1 — Helper 함수 추가

`experiments/orchestrator.py:_loads_json_lenient` (line 155) 다음에 partial JSON 복구 helper 추가:

```python
def _recover_partial_json(candidate: str) -> dict | None:
    """Brace 가 짝 안 맞는 partial JSON 을 복구 시도.

    전략:
    1. 앞에서 첫 '{' 찾고, 거기서부터 brace count 추적.
    2. depth 가 1 이상으로 끝나면 응답이 짤린 것 → 부족한 만큼 '}' 추가.
    3. 마지막 미완성 key/value 의 trailing comma 또는 partial string 은 제거.
    4. _loads_json_lenient 재시도.
    """
    if not candidate:
        return None
    start = candidate.find("{")
    if start == -1:
        return None
    body = candidate[start:]
    depth = 0
    in_string = False
    escaped = False
    last_complete_close = -1
    for i, ch in enumerate(body):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    last_complete_close = i
    # 1) 마지막으로 depth=0 으로 닫힌 위치까지 자른 본을 lenient parse 시도
    if last_complete_close != -1:
        parsed = _loads_json_lenient(body[: last_complete_close + 1])
        if parsed:
            return parsed
    # 2) 그래도 안 되면 부족한 만큼 '}' 채워서 시도
    if depth > 0:
        # 마지막 trailing comma 제거 (간단 정리)
        trimmed = body.rstrip().rstrip(",")
        # 미완성 string (홀수 따옴표) 안전 처리: 마지막 '"' 찾아 그 앞까지 자름
        if trimmed.count('"') % 2 == 1:
            trimmed = trimmed[: trimmed.rfind('"')]
            trimmed = trimmed.rstrip().rstrip(",")
        candidate2 = trimmed + ("}" * depth)
        return _loads_json_lenient(candidate2)
    return None
```

### Step 2 — `extract_json_from_response` 보강

기존 `extract_json_from_response` (line 167-191) 의 3 단계 다음에 4·5 단계 추가:

```python
def extract_json_from_response(raw: str) -> dict | None:
    """LLM 응답에서 JSON 블록을 추출한다. (JSON Mode 대응)"""
    if not raw:
        return None

    # 1. JSON Mode일 경우 응답 자체가 JSON 문자열일 가능성이 높음
    parsed = _loads_json_lenient(raw)
    if parsed:
        return parsed

    # 2. 마크다운 블록이 포함된 경우 fence 내부 전체를 추출
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE):
        parsed = _loads_json_lenient(match.group(1))
        if parsed:
            return parsed

    # 3. 텍스트 중간에 JSON이 섞인 경우
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        parsed = _loads_json_lenient(raw[start:end + 1])
        if parsed:
            return parsed

    # --- v3 patch (Exp10 v3 plan, 2026-04-29) ---

    # 4. 마크다운 fence 시작은 발견됐으나 닫힘 fence 가 없는 경우 (응답 짤림):
    #    fence 시작 다음부터 raw 끝까지 잘라 lenient parse 시도.
    fence_open = re.search(r"```(?:json)?\s*\n", raw, re.IGNORECASE)
    if fence_open and "```" not in raw[fence_open.end():]:
        parsed = _loads_json_lenient(raw[fence_open.end():])
        if parsed:
            return parsed
        # 5. partial JSON 복구 시도
        parsed = _recover_partial_json(raw[fence_open.end():])
        if parsed:
            return parsed

    # 6. 마지막 fallback — 전체 raw 를 partial JSON 복구
    parsed = _recover_partial_json(raw)
    if parsed:
        return parsed

    return None
```

### Step 3 — Unit 테스트 추가

`experiments/tests/test_static.py` 에 추가:

```python
class TestExtractJsonFromResponseV3:
    """v3 patch — fence 미닫힘 / partial JSON 복구 케이스 검증."""

    def test_existing_fenced_json(self):
        """기존 동작 회귀 검증."""
        from experiments.orchestrator import extract_json_from_response
        raw = '```json\n{"final_answer": "Casey"}\n```'
        assert extract_json_from_response(raw) == {"final_answer": "Casey"}

    def test_unclosed_fence_lenient(self):
        from experiments.orchestrator import extract_json_from_response
        raw = '```json\n{"final_answer": "Casey", "reasoning": "complete"}'
        # 닫힘 fence 없지만 JSON 자체는 완전
        assert extract_json_from_response(raw) == {
            "final_answer": "Casey",
            "reasoning": "complete",
        }

    def test_partial_json_brace_recovery(self):
        from experiments.orchestrator import extract_json_from_response
        # 응답이 짤린 partial JSON — last complete '}' 까지 복구
        raw = (
            '{"reasoning": "step 1", '
            '"final_answer": "Casey"}, '
            '"extra_field": "this is incomp'
        )
        result = extract_json_from_response(raw)
        # last complete close 는 첫 } — final_answer 까지 복구
        assert result is not None
        assert result.get("final_answer") == "Casey"

    def test_partial_json_depth_close(self):
        from experiments.orchestrator import extract_json_from_response
        # depth > 0 으로 끝나는 partial JSON — 부족한 '}' 채움
        raw = '{"final_answer": "Casey", "reasoning": "incomplete'
        result = extract_json_from_response(raw)
        # 미완성 string 제거 후 depth 채움 → final_answer 라도 살림
        assert result is not None
        assert result.get("final_answer") == "Casey"

    def test_no_json_returns_none(self):
        from experiments.orchestrator import extract_json_from_response
        raw = "This is plain text with no JSON."
        assert extract_json_from_response(raw) is None

    def test_empty_returns_none(self):
        from experiments.orchestrator import extract_json_from_response
        assert extract_json_from_response("") is None
        assert extract_json_from_response(None) is None  # type: ignore[arg-type]
```

## Dependencies

- Task 04 — 진단 결과 (`exp10-v3-abc-json-fail-diagnosis.md`) 가 patch 방향 결정의 입력. 결과 카테고리에 따라 fence_unclosed / partial_recovery 테스트 비중 조정.
- 패키지: 표준 `re`. 신규 의존성 0.

## Verification

```bash
# 1) 정적 import + 기존 호출자 회귀 없음
.venv/bin/python -c "from experiments.orchestrator import extract_json_from_response, _recover_partial_json; print('ok')"

# 2) 신규 테스트 + 기존 테스트 통과
.venv/bin/python -m pytest experiments/tests/test_static.py::TestExtractJsonFromResponseV3 -v
.venv/bin/python -m pytest experiments/tests/test_static.py -v

# 3) Task 04 의 4 fail trial 진단 결과 케이스를 patch 적용 후 재시도 (가능한 경우만)
.venv/bin/python -c "
import json, glob
from experiments.orchestrator import extract_json_from_response
v2 = json.load(open(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v2_final_*.json')[-1]))
fails = [t for t in v2['trials'] if t['condition']=='gemma_8loop' and t.get('error') and 'JSON parse' in str(t.get('error'))]
recovered = 0
for t in fails:
    debug = t.get('_debug', {})
    last = (debug.get('abc_logs') or [{}])[-1]
    raw = last.get('a_raw') or last.get('b_raw') or last.get('c_raw') or ''
    # truncate 표시 제거 후 시도 (저장된 4KB 본만 사용)
    raw = raw.split('... (truncated')[0] if '... (truncated' in raw else raw
    r = extract_json_from_response(raw)
    if r is not None:
        recovered += 1
        print(f'  recovered: {t[\"task_id\"]} t{t[\"trial\"]} keys={list(r.keys())[:3]}')
print(f'recovered: {recovered}/{len(fails)}')
# 기대: 0 이상. 4 trial 모두 truncate 인 경우 0 이어도 정상 (constraint).
"
```

세 명령 모두 정상 + pytest 모두 PASSED. 마지막 명령은 진단 결과에 따라 0~4 가능 (모두 truncate 면 0, fence_unclosed 면 1+).

## Risks

- **`_recover_partial_json` 의 false recovery**: 짤린 응답에서 부족한 brace 만 채우면 의도 다른 JSON 이 나올 수 있음. last_complete_close 우선 정책으로 위험 최소화. unit test 에 의도된 케이스만 검증.
- **기존 호출자 회귀**: `extract_json_from_response` 는 orchestrator 의 7+ 위치에서 호출 (`grep -n "extract_json_from_response" experiments/orchestrator.py`). 본 patch 는 기존 1~3 단계 동작을 그대로 두고 fallback 만 추가 — 회귀 위험 낮음. 기존 test 가 PASSED 면 정상.
- **fence_open 정규식의 매칭 위치**: `re.search` 가 첫 fence 만 잡음. 본문에 ``` 가 다른 용도로 등장하면 false positive — 4 단계는 닫힘 fence 부재 + 시작 fence 존재 조건이라 영향 작음.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` — Task 01 영역.
- `experiments/tasks/taskset.json` — Task 02 영역.
- v2 final JSON — read-only.
- `docs/reference/results/exp-10-reproducibility-cost.md` / `researchNotebook*` — Task 06 영역.
- `experiments/exp10_reproducibility_cost/run.py` 의 `_truncate_raw` (line 44) / `_serialize_abc_logs` (line 53) — 본 plan 범위 밖 (debug logging 영역).
- `experiments/orchestrator.py` 의 다른 함수 (`run_abc_chain`, `_escape_control_chars_in_json_strings` 등) — 본 task 는 `_recover_partial_json` 추가 + `extract_json_from_response` 본문 후미만 변경.
