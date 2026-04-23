---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: B
depends_on: []
---

# Task 02 — Tool 런타임 모듈 (calculator / linalg / linprog)

## Changed files

- `experiments/tools/__init__.py` — **신규 파일**. `TOOL_FUNCTIONS`, `TOOL_SCHEMAS` 공개.
- `experiments/tools/math_tools.py` — **신규 파일**. 3개 함수 + OpenAI tool schema 정의.
- `experiments/tools/test_math_tools.py` — **신규 파일**. 표준 라이브러리 `unittest` 기반 단위 테스트.

## Change description

### 1. `experiments/tools/math_tools.py` — 3개 도구 함수

#### Step 1: `calculator(expression: str) -> float`

- **목적**: 사칙연산·거듭제곱·괄호만 지원하는 안전한 수식 계산기.
- **구현 원칙**: `eval()` 직접 호출 금지. `ast.parse(expression, mode='eval')`로 파싱 후 노드 화이트리스트로만 평가.
- **허용 노드**: `ast.Expression`, `ast.BinOp`, `ast.UnaryOp`, `ast.Num`, `ast.Constant`(숫자만)
- **허용 연산자**: `ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`, `ast.Pow`, `ast.Mod`, `ast.USub`, `ast.UAdd`
- **금지**: `Name`, `Call`, `Attribute`, `Subscript` 등. 발견 시 `ValueError` raise.
- **반환**: `float` (정수 결과도 float로 통일).
- **에러 처리**: `ValueError`로 재raise. silent fallback 금지.

```python
import ast
import operator as op

_ALLOWED_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
    ast.USub: op.neg, ast.UAdd: op.pos,
}

def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Non-numeric constant: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.BinOp):
        return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Disallowed AST node: {type(node).__name__}")

def calculator(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _eval(tree)
```

#### Step 2: `solve_linear_system(A: list[list[float]], b: list[float]) -> list[float]`

- **목적**: n×n 연립방정식 Ax = b 해를 반환.
- **구현**: `numpy.linalg.solve` 래퍼.
- **에러**: 특이 행렬은 `numpy.linalg.LinAlgError` → `ValueError("Singular matrix; no unique solution")`로 재raise.
- **반환**: 순수 `list[float]` (numpy array 아님 — JSON 직렬화 가능해야 함).

#### Step 3: `linprog(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None) -> dict`

- **목적**: 선형계획법 최소화. `scipy.optimize.linprog(method='highs')`.
- **반환**: `{"x": [...], "fun": float, "status": int, "success": bool, "message": str}`.
- **참고**: math-04 같은 "최대화" 문제는 모델이 c의 부호를 반전시켜 호출하도록 system prompt에서 안내 (Task 03).
- **bounds 기본값**: `None`이면 `(0, None)` 사용 — 비음수 제약이 수학 문제의 기본 관례.

### 2. OpenAI tool schema

`math_tools.py` 하단에 `TOOL_SCHEMAS: list[dict]`를 정의. OpenAI Chat Completions 형식:

```python
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a simple arithmetic expression with +, -, *, /, **, %, and parentheses. Numbers only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Arithmetic expression, e.g. '(3+4)*2'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_linear_system",
            "description": "Solve the linear system Ax = b where A is an n×n matrix and b is a length-n vector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "A": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "b": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["A", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "linprog",
            "description": "Solve a linear program: minimize c·x subject to A_ub·x ≤ b_ub, A_eq·x = b_eq, bounds. For maximization, negate c.",
            "parameters": {
                "type": "object",
                "properties": {
                    "c": {"type": "array", "items": {"type": "number"}},
                    "A_ub": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "b_ub": {"type": "array", "items": {"type": "number"}},
                    "A_eq": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "b_eq": {"type": "array", "items": {"type": "number"}},
                    "bounds": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": ["number", "null"]}},
                        "description": "List of [lower, upper] per variable. null means unbounded. Default [0, null] if omitted.",
                    },
                },
                "required": ["c"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "solve_linear_system": solve_linear_system,
    "linprog": linprog,
}
```

### 3. `experiments/tools/__init__.py`

```python
from .math_tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, calculator, solve_linear_system, linprog

__all__ = ["TOOL_FUNCTIONS", "TOOL_SCHEMAS", "calculator", "solve_linear_system", "linprog"]
```

### 4. `experiments/tools/test_math_tools.py`

`unittest` 기반 최소 테스트 (외부 의존성 회피):
- `calculator("2+3*4")` == 14.0
- `calculator("(10-4)**2")` == 36.0
- `calculator("1/0")` → `ZeroDivisionError`
- `calculator("__import__('os')")` → `ValueError` (안전성 테스트)
- `solve_linear_system([[2,1],[1,3]], [5,10])` ≈ [1.0, 3.0] (허용오차 1e-9)
- `solve_linear_system([[1,2],[2,4]], [3,6])` → `ValueError` (특이 행렬)
- math-04 LP 검증: `linprog(c=[-50,-40,-30], A_ub=[[2,3,4],[3,2,1]], b_ub=[240,150], bounds=[[10,None],[10,None],[10,None]])` → x ≈ [30, 30, 10], fun ≈ -2800

### 5. 의존성 추가

프로젝트 루트에 `requirements.txt`가 있으면 `scipy>=1.11`, `numpy>=1.24` 추가. 없으면 신규 생성은 범위 외(사용자가 .venv 기반 관리). Task 파일에는 "pip install" 지시만 Verification에 포함.

## Dependencies

- 선행 Task 없음.
- **Python 패키지**: `scipy`, `numpy` (Windows/.venv에서 설치 필요). 현재 프로젝트 의존성은 `httpx`만 확인됨 (CLAUDE.md § 9).

## Verification

```bash
# 0. 의존성 설치 확인 (없으면 먼저 설치)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "import scipy, numpy; print(scipy.__version__, numpy.__version__)"
# 기대: 버전 문자열 2개 출력

# 1. 단위 테스트 전체 통과
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_math_tools -v
# 기대: "OK" 로 종료, 모든 테스트 pass

# 2. 임포트 및 schema 로딩
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
assert set(TOOL_FUNCTIONS.keys()) == {'calculator', 'solve_linear_system', 'linprog'}
assert len(TOOL_SCHEMAS) == 3
for s in TOOL_SCHEMAS:
    assert s['type'] == 'function' and 'name' in s['function']
print('OK')
"
# 기대: "OK"

# 3. math-04 LP 문제 직접 해결 가능성 검증
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from tools import linprog
r = linprog(c=[-50,-40,-30], A_ub=[[2,3,4],[3,2,1]], b_ub=[240,150], bounds=[[10,None],[10,None],[10,None]])
assert r['success'], r
x, fun = r['x'], r['fun']
assert abs(x[0]-30) < 1e-4 and abs(x[1]-30) < 1e-4 and abs(x[2]-10) < 1e-4, x
assert abs(fun - (-2800)) < 1e-3, fun
print('math-04 solvable via linprog:', x, fun)
"
# 기대: "math-04 solvable via linprog: [30.0, 30.0, 10.0] -2800.0" 계통 출력
```

## Risks

- **AST 화이트리스트 누락**: 새 Python 버전에서 추가되는 AST 노드 타입이 화이트리스트 바깥에 있으면 정상 수식도 `ValueError`가 될 수 있음. 완전 실패가 silent보다 낫다 (의도된 설계).
- **scipy 설치 무게**: scipy는 수십 MB. 개발 환경만 영향, 런타임 모델 호출에는 무관.
- **`linprog`의 maximize 혼동**: 모델이 c를 negate하지 않고 호출할 수 있음 → Task 03 system prompt에서 명시적으로 안내.
- **실수-정수 경계**: math-04의 정답은 정수(30, 30, 10)지만 HiGHS는 float 반환. 문신이 final_answer에 담을 때 반올림 필요 — 이는 A 프롬프트 가이드로 처리 (Task 03).

## Scope boundary

**Task 02에서 절대 수정 금지**:
- `experiments/orchestrator.py` (Task 03 영역 — tool 통합)
- `experiments/system_prompt.py` (Task 03 영역 — A 프롬프트 가이드)
- `experiments/run_experiment.py` (Task 04 영역)
- `experiments/measure.py` (Task 01/05 영역)
- `experiments/config.py` — 본 Task에서는 touch 금지

**허용 범위**: `experiments/tools/` 하위 신규 파일 3개 + 프로젝트 루트 `requirements.txt` append (이미 존재할 경우만).
