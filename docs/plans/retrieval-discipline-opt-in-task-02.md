---
type: plan-task
status: pending
updated_at: 2026-07-01
parent_plan: retrieval-discipline-opt-in
parallel_group: B
depends_on: [01]
---

# Task 02 — 회귀 게이트 + opt-in 동작 검증

## Changed files

- `experiments/tests/test_retrieval_discipline_optin.py` (신규) — Stage 8 `test_mandatory_optin.py` 미러. 기본 False byte-identical + True 1회 append + 두 플래그 조합 순서·멱등 검증.

요약: 신규 1, 수정 0.

## Change description

### 배경
Stage 8 회귀 게이트(`test_mandatory_optin.py`)와 동일 계약을 discipline 플래그에 대해 건다. **LLM 호출 없음** — 정적 검증. 추가로 두 플래그(mandatory + discipline) 동시 True 시 **결정 4 순서(mandatory 먼저)** 와 멱등을 assert.

### Step 1 — 테스트 파일 작성
`test_mandatory_optin.py` 구조를 복제하되 대상 상수/파라미터를 discipline 으로 교체하고 조합 테스트를 추가:

```python
"""Stage 10 회귀 게이트 — retrieval_discipline_prompt opt-in 정적 검증.

LLM 호출 없음. 불변식: `retrieval_discipline_prompt=False`(기본) 시 prompt byte-identical,
True 시 RETRIEVAL_DISCIPLINE_RULES 정확히 1회 append. 두 플래그 조합 순서=mandatory→discipline.
"""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestRetrievalDisciplineOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_constant_exists_and_shape(self):
        from system_prompt import RETRIEVAL_DISCIPLINE_RULES as R
        self.assertTrue(R.startswith("\n\n"))                 # append 용
        self.assertIn("RETRIEVAL DISCIPLINE", R)
        for phrase in ("Failed with result", "Main process exited",
                       ".service", "new_assertion", "empty-handed"):
            self.assertIn(phrase, R, f"검증 문구 {phrase!r} drift")

    def test_param_default_false(self):
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["retrieval_discipline_prompt"]
        self.assertIs(p.default, False)

    def test_injection_guarded_in_source(self):
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn("if retrieval_discipline_prompt:", src)
        self.assertIn("RETRIEVAL_DISCIPLINE_RULES", src)

    def test_injection_contract(self):
        """False=동일, True=정확히 1회 append, 멱등."""
        from system_prompt import RETRIEVAL_DISCIPLINE_RULES as R

        def inject(prompt, on):
            return f"{prompt}{R}" if on else prompt

        base = "TASK PROMPT BODY"
        self.assertEqual(inject(base, False), base)
        self.assertEqual(inject(base, True), base + R)
        self.assertEqual(inject(base, True).count("RETRIEVAL DISCIPLINE"), 1)

    def test_two_flags_order_and_independence(self):
        """결정 4: mandatory 먼저, discipline 나중. 독립 상수(중복/오염 없음)."""
        from system_prompt import MANDATORY_TOOL_RULES as M, RETRIEVAL_DISCIPLINE_RULES as R
        self.assertNotEqual(M, R)                              # 별도 상수
        base = "TASK PROMPT BODY"
        # 코드 주입 순서와 동일한 식: mandatory 먼저, discipline 나중
        combined = base
        combined = f"{combined}{M}"
        combined = f"{combined}{R}"
        self.assertTrue(combined.endswith(R))                 # discipline 이 맨 끝
        self.assertLess(combined.index("MANDATORY TOOL-USE RULES"),
                        combined.index("RETRIEVAL DISCIPLINE"))  # mandatory 가 앞
        self.assertEqual(combined.count("RETRIEVAL DISCIPLINE"), 1)
        self.assertEqual(combined.count("MANDATORY TOOL-USE RULES"), 1)

    def test_mandatory_constant_untouched(self):
        """Risk 2: 기존 MANDATORY 상수 무변경 (Exp16b 보존)."""
        from system_prompt import MANDATORY_TOOL_RULES as M
        self.assertTrue(M.startswith("\n\n"))
        self.assertIn("MANDATORY TOOL-USE RULES", M)
        self.assertIn("transcribe", M)


if __name__ == "__main__":
    unittest.main()
```

## Dependencies

- Task 01 완료 (`RETRIEVAL_DISCIPLINE_RULES` 상수 + `retrieval_discipline_prompt` 파라미터 존재).
- 외부 패키지: 없음 (`unittest` 표준).
- 기존 파일 (read-only): `experiments/tests/test_mandatory_optin.py` (미러 원본).

## Verification

```bash
# 1. 신규 테스트 단독 통과 (repo root)
python -m unittest experiments.tests.test_retrieval_discipline_optin -v
```

```bash
# 2. 전체 스위트 회귀 없음 (56 OK + 신규, repo root)
python -m unittest discover -s experiments/tests -t .
```

```bash
# 3. 기존 Stage 8 게이트도 여전히 통과 (MANDATORY 무변경 재확인)
python -m unittest experiments.tests.test_mandatory_optin -v
```

## Risks

1. **테스트가 상수 내부 문구에 과결합** — 문구 정형화 시 깨질 수 있음. → 검증 문구는 lever 핵심 어휘(Risk 4 목록)로 한정, 전체 문자열 비교는 안 함.
2. **cwd 아티팩트** — `experiments/` 를 cwd 로 두면 import 실패. → 반드시 repo root 실행 (핸드오프 §3).
3. **조합 테스트가 코드 실행이 아닌 식 재현** — 실제 `run_abc_chain` 주입과 drift 가능. → `test_injection_guarded_in_source` 가 소스에 두 가드 존재를 확인하여 보완.

## Scope boundary

**수정 금지**: `system_prompt.py`, `orchestrator.py` (Task 01 영역), 기존 `test_mandatory_optin.py`, 실험 드라이버. 본 task 는 신규 테스트 파일 1개만.
