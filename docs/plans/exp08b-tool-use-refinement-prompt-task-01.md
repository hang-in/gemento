---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08b-tool-use-refinement-prompt
parallel_group: A
depends_on: []
---

# Task 01 — Calculator 에러 메시지 개선

## Changed files

- `experiments/tools/math_tools.py`
  - `_eval()` 함수 내 `BinOp` 분기 (line 30~34): `BitXor` 연산자의 경우 특수 메시지로 분기.
- `experiments/tools/test_math_tools.py`
  - 기존 `test_unsafe_expression_blocked` 또는 유사 위치에 BitXor 에러 **메시지 내용**을 검증하는 테스트 1건 추가.

## Change description

### Step 1 — BitXor 전용 에러 메시지

`_eval()`의 `BinOp` 분기는 현재:

```python
if isinstance(node, ast.BinOp):
    op_type = type(node.op)
    if op_type not in _ALLOWED_OPS:
        raise ValueError(f"Disallowed operator: {op_type.__name__}")
    return _ALLOWED_OPS[op_type](_eval(node.left), _eval(node.right))
```

`op_type not in _ALLOWED_OPS` 분기 안에서 `ast.BitXor` 여부를 먼저 확인하여 힌트 메시지를 제공:

```python
if isinstance(node, ast.BinOp):
    op_type = type(node.op)
    if op_type not in _ALLOWED_OPS:
        if op_type is ast.BitXor:
            raise ValueError(
                "Disallowed operator: BitXor "
                "(use '**' for power; Python '^' is bitwise XOR)"
            )
        raise ValueError(f"Disallowed operator: {op_type.__name__}")
    return _ALLOWED_OPS[op_type](_eval(node.left), _eval(node.right))
```

**근거**:
- 이 에러가 호출 loop의 tool role 메시지로 다시 모델에 전달되므로, 힌트가 포함되면 모델이 다음 tool round에서 `**`로 재시도할 가능성이 높아짐.
- `_ALLOWED_OPS`에 BitXor를 추가(즉 XOR로 수락)하는 것은 금지 — 모델이 기대한 의미(거듭제곱)와 다르므로 silent failure가 될 수 있음. 명시적 거절이 옳은 설계.

### Step 2 — UnaryOp는 변경 없음

`UnaryOp` 분기의 에러 메시지는 현상 유지. BitXor는 이항 연산자라 `BinOp` 분기만 영향.

### Step 3 — 테스트 추가

`experiments/tools/test_math_tools.py`의 `TestCalculator` 클래스에 신규 테스트:

```python
def test_bitxor_hint_message(self):
    """BitXor 에러는 '**' 사용 힌트를 포함해야 한다."""
    with self.assertRaises(ValueError) as ctx:
        calculator("2^10")
    msg = str(ctx.exception)
    self.assertIn("BitXor", msg)
    self.assertIn("**", msg)
    self.assertIn("XOR", msg)
```

기존 `test_unsafe_expression_blocked` 또는 `test_call_node_blocked` 테스트는 변경 금지. 새 테스트만 추가.

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음 (ast, operator 표준 라이브러리만).

## Verification

```bash
# 1. 단위 테스트 전체 통과 (신규 테스트 포함)
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_math_tools -v
# 기대: "OK" 종료, 기존 8개 + 신규 1개 = 9개 테스트 pass

# 2. 힌트 메시지 실제 생성 확인
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from tools import calculator
try:
    calculator('2^10')
except ValueError as e:
    msg = str(e)
    assert 'BitXor' in msg and '**' in msg and 'XOR' in msg, f'missing hint: {msg}'
    print('OK hint:', msg)
"
# 기대: "OK hint: Disallowed operator: BitXor (use '**' for power; Python '^' is bitwise XOR)"

# 3. 기존 허용 수식은 여전히 동작
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from tools import calculator
assert calculator('2**10') == 1024.0
assert calculator('(3+4)*2') == 14.0
print('OK regression')
"
# 기대: "OK regression"
```

## Risks

- **메시지 포맷 의존성**: 만약 이후 Task 또는 외부 시스템이 에러 메시지 문자열을 파싱하는 경우, 문구 변경이 회귀를 일으킬 수 있음. 현재 코드베이스에 `"Disallowed operator"` 문자열 매칭 의존은 없음으로 확인 — `grep -rn "Disallowed operator"` 로 교차 확인 필요.
- **다른 disallowed 연산자 노출**: BitAnd(`&`), BitOr(`|`), LShift(`<<`), RShift(`>>`) 등은 여전히 일반 메시지. 모델이 이들로도 수학 연산을 의도할 가능성은 낮으나, 실제 관측되면 후속 Task에서 추가 힌트 고려.
- **테스트 배치 위치**: `test_math_tools.py`의 다른 테스트를 깨지 않도록 새 테스트는 **클래스 내 메서드 추가**만. 모듈 레벨 변경 금지.

## Scope boundary

**Task 01에서 절대 수정 금지**:
- `experiments/system_prompt.py` (Task 02 영역)
- `experiments/run_experiment.py` (Task 03 영역)
- `experiments/measure.py` (Task 04 영역)
- `experiments/orchestrator.py` — 본 Task는 도구 모듈만.
- `experiments/tools/__init__.py`, `smoke_test.py` — 터치 금지.
- `_ALLOWED_OPS` 딕셔너리 — BitXor를 허용 목록에 추가 금지(설계 의도).

**허용 범위**: `experiments/tools/math_tools.py`, `experiments/tools/test_math_tools.py`만.
