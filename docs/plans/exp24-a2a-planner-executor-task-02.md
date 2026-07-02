---
type: plan-task
status: pending
updated_at: 2026-07-03
parent_plan: exp24-a2a-planner-executor
parallel_group: B
depends_on: [01]
---

# Task 02 — 회귀 게이트

## Changed files

- `experiments/tests/test_a2a_proposer_optin.py` (신규) — 기본 False 시 A-stage 경로 불변 + a2a 파라미터/가드/헬퍼 정적 검증. LLM 무.

요약: 신규 1, 수정 0.

## Change description

### 배경
Stage 8/10 opt-in 게이트 패턴 계승. `a2a_proposer=False`(기본) 시 A-stage 가 기존 `run_loop` 경로임을 소스 정적 검증 + Planner/Executor 빌더 shape + 기존 프롬프트(SYSTEM_PROMPT) 무변경.

### Step 1 — 테스트 파일 작성

```python
"""Stage 12 회귀 게이트 — a2a_proposer opt-in 정적 검증.

LLM 없음. 불변식: a2a_proposer=False(기본) 시 A-stage = 기존 run_loop 경로.
True 시 _a2a_propose 로 분기. Planner/Executor 빌더 shape + 기존 프롬프트 불변.
"""
from __future__ import annotations
import inspect, sys, unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestA2AProposerOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_param_default_false(self):
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["a2a_proposer"]
        self.assertIs(p.default, False)

    def test_branch_guarded_in_source(self):
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn("if a2a_proposer:", src)
        self.assertIn("_a2a_propose", src)
        self.assertIn("run_loop(", src)                    # else 경로 보존

    def test_helper_returns_4tuple_shape(self):
        """_a2a_propose 소스가 run_loop 와 동일 4-tuple 반환."""
        src = inspect.getsource(__import__("orchestrator")._a2a_propose)
        self.assertIn("return", src)
        self.assertIn("apply_llm_response", src)           # 기존 적용 재사용
        self.assertIn("extract_json_from_response", src)   # 기존 파서 재사용

    def test_prompt_builders(self):
        from system_prompt import (A2A_PLANNER_SYSTEM,
                                    build_a2a_planner_prompt, build_a2a_executor_prompt)
        self.assertIn("PLANNER", A2A_PLANNER_SYSTEM)
        pm = build_a2a_planner_prompt("{}")
        self.assertEqual(pm[0]["role"], "system")
        em = build_a2a_executor_prompt("unit X is failing", "{}")
        etxt = " ".join(m["content"] for m in em)
        self.assertIn("Do NOT call tools", etxt)           # probe 조건
        self.assertIn("new_assertion", etxt)

    def test_existing_prompt_unchanged(self):
        """기존 proposer SYSTEM_PROMPT 무변경 (Exp15~23 보존)."""
        from system_prompt import SYSTEM_PROMPT, build_prompt
        self.assertTrue(len(SYSTEM_PROMPT) > 0)
        self.assertEqual(build_prompt("{}")[0]["role"], "system")


if __name__ == "__main__":
    unittest.main()
```

## Dependencies

- Task 01 완료.
- 외부: `unittest`, `inspect` (표준).
- 기존 파일 (read-only): `tests/test_mandatory_optin.py`/`test_retrieval_discipline_optin.py` (미러 패턴).

## Verification

```bash
# 1. 신규 테스트 통과
python -m unittest experiments.tests.test_a2a_proposer_optin -v
```

```bash
# 2. 전체 스위트 회귀 없음 (66 OK + 신규)
python -m unittest discover -s experiments/tests -t .
```

```bash
# 3. 기존 opt-in 게이트 재통과
python -m unittest experiments.tests.test_mandatory_optin experiments.tests.test_retrieval_discipline_optin -v
```

## Risks

1. **소스 문자열 과결합** — 헬퍼/가드 이름 변경 시 깨짐. → 핵심 토큰(`if a2a_proposer:`, `_a2a_propose`, `apply_llm_response`)만 검사.
2. **cwd 아티팩트** — repo root 실행.
3. **_a2a_propose 가 모듈 레벨 아님** — Task 01 이 run_abc_chain 내부 def 로 두면 `inspect.getsource(orchestrator._a2a_propose)` 실패. → Task 01 은 헬퍼를 **모듈 레벨**에 두거나, 내부일 경우 test_helper_returns_4tuple_shape 를 run_abc_chain 소스 검사로 대체. (Task 01 Developer 와 정합 확인.)

## Scope boundary

**수정 금지**: `system_prompt.py`/`orchestrator.py`(Task 01), 기존 테스트, 드라이버. 신규 테스트 1개만.
