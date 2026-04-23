"""llama.cpp 서버로 실제 tool round-trip 검증.

- math-04 문제를 A 단독 호출로 풀도록 지시
- tools 주입 → tool_calls → linprog 실행 → 결과 재주입 → 최종 답변
- 정답과 근접한지 확인 (실제 최적해: X=31, Y=10, Z=37, profit=3060)

실행:
  python tools/smoke_test.py

CI 금지: 외부 서버 호출.
"""
import json
import sys

sys.path.insert(0, str(__file__).rsplit("/tools/", 1)[0] if "/tools/" in str(__file__) else
                str(__file__).rsplit("\\tools\\", 1)[0])

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

    # 실제 최적해: profit=3060 (x=31, y=10, z=37)
    expected_profit = 3060
    expected_values = [31, 10, 37, 3060]

    try:
        stripped = final_content.strip()
        start = stripped.rfind("{")
        end = stripped.rfind("}") + 1
        parsed = json.loads(stripped[start:end]) if start >= 0 else {}
    except Exception:
        parsed = {}

    close = all(str(v) in final_content for v in expected_values)

    tool_was_called = len(tool_log) > 0
    tool_had_no_errors = all(tc.get("error") is None for tc in tool_log)

    if tool_was_called and tool_had_no_errors and close:
        print(f"\nSMOKE TEST PASSED: tool_calls={len(tool_log)}, answer_close={close}")
        return 0
    else:
        print(f"\nSMOKE TEST FAILED: tool_called={tool_was_called}, "
              f"tool_errors={sum(1 for tc in tool_log if tc.get('error'))}, answer_close={close}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
