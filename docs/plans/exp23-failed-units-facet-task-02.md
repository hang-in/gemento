---
type: plan-task
status: pending
updated_at: 2026-07-02
parent_plan: exp23-failed-units-facet
parallel_group: B
depends_on: [01]
---

# Task 02 — 회귀 게이트

## Changed files

- `experiments/tests/test_failed_units_tool.py` (신규) — `test_facet_tool.py` 미러. 글로벌 CONTEXT_TOOL_* 불변 + FAILED_UNITS_* 분리 + fixture 집계 정확성 (LLM 무).

요약: 신규 1, 수정 0.

## Change description

### 배경
Stage 9 `test_facet_tool.py`(글로벌 불변 + FACET 분리 검증)와 동일 계약을 FAILED_UNITS 도구에 건다. Redis 는 mock — LLM/네트워크 무.

### Step 1 — 테스트 파일 작성
`test_facet_tool.py` 구조 복제, 대상만 교체 + fixture 집계:

```python
"""Stage 11 회귀 게이트 — list_failed_units opt-in 정적 검증.

글로벌 CONTEXT_TOOL_*(read/grep) 불변 + FAILED_UNITS_* 분리 + fixture 집계 정확성.
LLM/네트워크 없음 (Redis mock).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestFailedUnitsTool(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_globals_unchanged(self):
        """글로벌 CONTEXT_TOOL_* / FACET_TOOL_* 불변 (Exp15~22 byte-identical)."""
        from tools import (CONTEXT_TOOL_SCHEMAS, CONTEXT_TOOL_FUNCTIONS,
                           FACET_TOOL_FUNCTIONS)
        names = [s["function"]["name"] for s in CONTEXT_TOOL_SCHEMAS]
        self.assertEqual(names, ["read_context", "grep_context"])
        self.assertEqual(list(CONTEXT_TOOL_FUNCTIONS.keys()), ["read_context", "grep_context"])
        self.assertEqual(list(FACET_TOOL_FUNCTIONS.keys()), ["aggregate_context"])

    def test_failed_units_separate(self):
        """FAILED_UNITS_TOOL_* 에 list_failed_units 만 — 글로벌에서 분리."""
        from tools import FAILED_UNITS_TOOL_SCHEMAS, FAILED_UNITS_TOOL_FUNCTIONS
        names = [s["function"]["name"] for s in FAILED_UNITS_TOOL_SCHEMAS]
        self.assertEqual(names, ["list_failed_units"])
        self.assertEqual(list(FAILED_UNITS_TOOL_FUNCTIONS.keys()), ["list_failed_units"])
        # required 는 handle 만 (top_n optional) — 쿼리 formulate 불필요가 핵심
        self.assertEqual(FAILED_UNITS_TOOL_SCHEMAS[0]["function"]["parameters"]["required"],
                         ["handle"])

    def test_aggregation_correct(self):
        """fixture: 실패 신호 unit 별 카운트 top-N (untruncated)."""
        import tools.context_tools as ct
        fake = [
            "gohttpserver.service: Main process exited, code=exited",
            "gohttpserver.service: Failed with result 'exit-code'",
            "gohttpserver.service: start-limit hit",
            "sshd.service: Started",                      # 실패 신호 아님 → 제외
            "nginx.service: Failed to start",
        ]

        class R:
            def get(self, k):
                return "\n".join(fake)

        with mock.patch.object(ct, "get_redis_client", lambda: R()):
            out = ct.list_failed_units("h")
        self.assertFalse(out.get("truncated"))
        self.assertEqual(out["top"][0]["unit"], "gohttpserver.service")
        self.assertEqual(out["top"][0]["failure_signals"], 3)
        units = [u["unit"] for u in out["top"]]
        self.assertIn("nginx.service", units)
        self.assertNotIn("sshd.service", units)           # Started 는 실패 아님

    def test_handle_missing(self):
        import tools.context_tools as ct

        class R:
            def get(self, k):
                return None

        with mock.patch.object(ct, "get_redis_client", lambda: R()):
            out = ct.list_failed_units("nope")
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
```

## Dependencies

- Task 01 완료 (`list_failed_units` + `FAILED_UNITS_TOOL_*` 존재).
- 외부: `unittest`, `unittest.mock` (표준).
- 기존 파일 (read-only): `experiments/tests/test_facet_tool.py` (미러 원본).

## Verification

```bash
# 1. 신규 테스트 통과 (repo root)
python -m unittest experiments.tests.test_failed_units_tool -v
```

```bash
# 2. 전체 스위트 회귀 없음 (62 OK + 신규)
python -m unittest discover -s experiments/tests -t .
```

```bash
# 3. 기존 facet 게이트도 통과 (글로벌 불변 재확인)
python -m unittest experiments.tests.test_facet_tool -v
```

## Risks

1. **테스트가 실패 신호 문구에 과결합** — Task 01 정규식과 fixture 문구 일치 필요. → fixture 를 Task 01 정규식(`Failed with result`/`Main process exited`/`start-limit`/`Failed to start`)에 맞춰 작성.
2. **cwd 아티팩트** — repo root 실행 (핸드오프 규약).
3. **글로벌 목록 순서 의존** — read/grep 순서 고정 가정. 기존 test_facet_tool 과 동일 가정이라 안전.

## Scope boundary

**수정 금지**: `context_tools.py`, `tools/__init__.py`(Task 01), 기존 `test_facet_tool.py`, 드라이버. 본 task 는 신규 테스트 1개만.
