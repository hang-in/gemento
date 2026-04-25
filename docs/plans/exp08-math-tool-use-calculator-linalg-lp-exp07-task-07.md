---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: —
depends_on: [03]
---

# Task 07 — 로컬 도구 검증 (smoke test)

## Changed files

- `experiments/tools/smoke_test.py` — **신규**. llama.cpp 서버 실제 호출로 end-to-end round-trip 1회 검증.

## Change description

### 목적

Exp08 본 실행에 앞서, 다음 경로가 **실제 서버와 맞물려 동작**하는지 한 번 증명:

1. E4B(Q8_0 / llama.cpp)가 OpenAI tool schema를 인식하고 `tool_calls`를 반환.
2. orchestrator의 tool 루프가 tool_call을 파싱 → `TOOL_FUNCTIONS`로 실행 → 결과를 tool role로 재주입.
3. 모델이 tool result를 읽고 최종 숫자 답을 생성.
4. A-B-C 전체 파이프라인과 독립적으로 A 경로 단독으로 완결 가능.

**운영 제약**: 실제 서버 호출이므로 CI에서 실행 금지. 개발자가 수동으로 한 번 실행하여 관문 통과.

### `experiments/tools/smoke_test.py` 구현

```python
"""llama.cpp 서버로 실제 tool round-trip 검증.

- math-04 문제를 A 단독 호출로 풀도록 지시
- tools 주입 → tool_calls → linprog 실행 → 결과 재주입 → 최종 답변
- 정답(X=30, Y=30, Z=10, profit=2800)과 근접한지 확인

실행:
  python tools/smoke_test.py

CI 금지: 외부 서버 호출.
"""
import json
import sys

# experiments 디렉토리를 sys.path에 추가하여 orchestrator/tools import 가능하게
sys.path.insert(0, str(__file__.rsplit("/", 2)[0] if "/" in __file__ else __file__.rsplit("\\", 2)[0]))

from orchestrator import call_model
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS


MATH04_PROMPT = """\
A factory produces three products X, Y, Z. Each unit of X requires 2 hours of labor and 3 kg of material.
Each unit of Y requires 3 hours of labor and 2 kg of material. Each unit of Z requires 4 hours of labor
and 1 kg of material. Available: 240 hours of labor and 150 kg of material per week.
Profit per unit: X=$50, Y=$40, Z=$30. Additionally, the factory must produce at least 10 units of each product.
What production plan maximizes weekly profit? Find the exact quantities.

Respond with a JSON object: {"x": int, "y": int, "z": int, "profit": int}.
"""

SYSTEM = """\
You are a problem solver. For numeric work, you MUST use the available tools:
- `calculator(expression)` for arithmetic verification
- `linprog(c, A_ub, b_ub, bounds)` for LP (minimize c·x). For maximization, negate c.
Round LP outputs to integers. Always output a final JSON answer after tool calls.
"""


def main() -> int:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": MATH04_PROMPT},
    ]

    try:
        final_content, tool_log = call_model(
            messages,
            tools=TOOL_SCHEMAS,
            tool_functions=TOOL_FUNCTIONS,
            max_tool_rounds=5,
        )
    except Exception as e:
        print(f"SMOKE TEST FAILED: call_model raised {type(e).__name__}: {e}")
        return 1

    print("── Tool call log ──")
    for i, tc in enumerate(tool_log, 1):
        err = tc.get("error")
        print(f"  [{i}] name={tc['name']} args={json.dumps(tc['arguments'], ensure_ascii=False)[:120]}")
        if err:
            print(f"      ERROR: {err}")
        else:
            print(f"      result={str(tc.get('result'))[:120]}")

    print("\n── Final content ──")
    print(final_content[:500])

    # 정답 근접도 확인 (JSON 파싱되면 정량 검증, 실패하면 substring만)
    expected = {"x": 30, "y": 30, "z": 10, "profit": 2800}
    try:
        parsed = json.loads(final_content.strip().splitlines()[-1] if "{" in final_content else "{}")
    except Exception:
        parsed = {}

    # substring 폴백
    close = all(str(v) in final_content for v in expected.values())

    tool_was_called = len(tool_log) > 0
    tool_had_no_errors = all(tc.get("error") is None for tc in tool_log)

    if tool_was_called and tool_had_no_errors and (close or parsed == expected):
        print(f"\nSMOKE TEST PASSED: tool_calls={len(tool_log)}, answer_close={close}")
        return 0
    else:
        print(f"\nSMOKE TEST FAILED: tool_called={tool_was_called}, "
              f"tool_errors={sum(1 for tc in tool_log if tc.get('error'))}, answer_close={close}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

### 설계 포인트

- **A 경로 단독**: orchestrator의 `run_abc_chain`이 아닌 `call_model` 직접 호출 — tool 루프만 증명하는 것이 목적. B/C 동작은 본 실험에서 별도 검증.
- **명시적 종료 코드**: 0=PASS, 1=서버/호출 예외, 2=tool 미호출 또는 정답 부정합.
- **검증 기준 느슨**: smoke test는 "tool이 실제로 호출되고 에러 없이 완료되는가"가 핵심. 정답 근접도는 substring 폴백도 허용 (JSON 포맷 차이 때문에 too strict하면 실패율 높음).
- **외부 서버 의존**: 서버 중단·지연 시 실패 — CI에 포함 금지. 가이드 문서에 명시.

## Dependencies

- **Task 03 완료**: `call_model`이 tools 루프를 지원해야 호출 가능.
- **Task 02 완료**: `TOOL_SCHEMAS`, `TOOL_FUNCTIONS` import 가능.
- 외부: llama.cpp 서버 (`yongseek.iptime.org:8005`)가 응답 중이어야 함.

## Verification

```bash
# 1. 파일 존재
test -f experiments/tools/smoke_test.py && echo "file: OK"
# 기대: "file: OK"

# 2. 실제 smoke test 실행 — 외부 서버 호출, 수 초~수 분 소요
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python tools/smoke_test.py
# 기대: 마지막 줄에 "SMOKE TEST PASSED: tool_calls=N, answer_close=True"
# 예상 소요: 10~90초 (tool round-trip 2~4회)
# 실패 시: 출력 전체(tool log + final content + 실패 이유)를 Architect에게 보고

# 3. 종료 코드 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python tools/smoke_test.py; echo "exit=$?"
# 기대: "exit=0" (재실행. 이미 2번에서 통과했다면 스킵 가능)
```

## Risks

- **서버 의존**: `yongseek.iptime.org:8005`가 다운되면 smoke test 자체가 실행 불가. 실패가 **smoke 로직 결함인지 서버 이슈인지** 구분 위해 `/v1/models` 응답 먼저 확인 권장.
- **모델의 tool 이해도 편차**: Q8_0 E4B가 tool_calls 포맷을 한 번에 반환하지 못하고 plain text JSON으로 응답할 수 있음 — 이 경우 tool_log가 비며 SMOKE FAIL. 즉시 Task 03의 SYSTEM_PROMPT 가이드를 강화해야 함.
- **llama.cpp response_format 제약**: tools와 json_object 동시 사용 시 서버 에러 가능성. Task 03에서 tools 주입 시 response_format 제거하는 것이 이 risk의 대응.
- **max_tool_rounds 초과**: 모델이 무한히 tool_calls만 반복하는 경우. Task 03에서 `max_tool_rounds=5` 상한이 이를 차단하지만, smoke에서 도달하면 설정 재검토 필요.
- **정답 substring 폴백의 false-positive**: 긴 설명에 '30', '10', '2800'이 우연히 포함된 경우 pass로 잡힐 수 있음. 설계상 허용 범위이나, 본 실험의 `score_v2`가 keyword group 매칭이므로 최종 정답률은 더 엄격하게 나올 것.

## Scope boundary

**Task 07에서 절대 수정 금지**:
- `experiments/tools/math_tools.py`, `__init__.py`, `test_math_tools.py` (Task 02 영역)
- `experiments/orchestrator.py` (Task 03 영역)
- `experiments/run_experiment.py` (Task 04 영역)
- `experiments/measure.py` (Task 05 영역)
- `docs/` 전체 (Task 01/06 영역)

**허용 범위**: `experiments/tools/smoke_test.py` 신규 파일만.
