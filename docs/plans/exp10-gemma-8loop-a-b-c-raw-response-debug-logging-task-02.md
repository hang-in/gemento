---
type: plan-task
status: todo
updated_at: 2026-04-27
parent_plan: exp10-gemma-8loop-a-b-c-raw-response-debug-logging
parallel_group: B
depends_on: [01]
---

# Task 02 — test_static 에 schema 정합성 테스트 추가

## Changed files

- `experiments/tests/test_static.py` — **수정**. 파일 끝 (`if __name__ == "__main__":` 직전) 에 `TestExp10DebugLoggingSchema` 신규 클래스 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

task-01 의 `_serialize_abc_logs` / `_truncate_raw` helper 가 향후 누가 정정해도 `_debug.abc_logs` schema 가 깨지지 않도록 정적 검증 추가. v2 재실행 후 결과 JSON 의 `_debug.abc_logs` 필드를 사후 분석 (예: 한국어 응답 패널티 사후 rescoring) 하는 코드 의존성을 고정.

본 task 는 LLM 호출 0 — dummy `ABCCycleLog` fixture 로 helper 함수 검증.

### 검증 항목

1. **(존재)** `_truncate_raw`, `_serialize_abc_logs`, `DEBUG_RAW_TRUNCATE_LIMIT` 모두 import 가능.
2. **(truncate 정책)** `DEBUG_RAW_TRUNCATE_LIMIT == 4096`. truncate 발생 시 끝에 `... (truncated, original_len=N)` 표시.
3. **(schema)** `_serialize_abc_logs` 의 출력 dict 가 9 필드 (`cycle`, `phase`, `a_raw`, `a_error`, `b_raw`, `b_error`, `c_raw`, `c_error`, `phase_transition`) 모두 보유.
4. **(error 보존)** ABCCycleLog 의 `b_error` / `c_error` 가 None 또는 str 일 때 모두 보존됨.
5. **(빈 list)** `_serialize_abc_logs([])` → `[]`.
6. **(LoopLog None 처리)** `a_log` 가 None 인 비정상 케이스 — 빈 string 또는 안전한 default. (단 ABCCycleLog 정의상 a_log 는 LoopLog 필수라 본 case 는 방어 코드 검증)

### Step 1 — TestExp10DebugLoggingSchema 클래스 추가

`experiments/tests/test_static.py` 의 마지막 클래스 (`TestSamplingParamsCentralization`) 다음, `if __name__ == "__main__":` 블록 직전에 추가:

```python
class TestExp10DebugLoggingSchema(unittest.TestCase):
    """exp10-gemma-8loop-a-b-c-raw-response-debug-logging plan — _debug.abc_logs schema 검증.

    - _truncate_raw: 4KB 정책, edge case (None, 빈 문자열, exact limit)
    - _serialize_abc_logs: 9 필드 dict 반환, error 보존, 빈 list
    """

    EXPECTED_FIELDS = {
        "cycle", "phase",
        "a_raw", "a_error",
        "b_raw", "b_error",
        "c_raw", "c_error",
        "phase_transition",
    }

    def _make_dummy_log(self, cycle: int = 1, b_error=None, c_error=None):
        """dummy ABCCycleLog 생성 헬퍼."""
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from orchestrator import ABCCycleLog, LoopLog
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))
        a_log = LoopLog(
            loop_index=cycle,
            tattoo_in={},
            raw_response="A" * 100,
            parsed_response={"foo": "bar"},
            tattoo_out={},
            duration_ms=500,
            error=None,
        )
        return ABCCycleLog(
            cycle=cycle,
            phase="DECOMPOSE",
            a_log=a_log,
            b_judgments={"verdict": "APPROVE"},
            b_raw="B" * 100,
            b_duration_ms=300,
            b_error=b_error,
            c_decision={"next_phase": "INVESTIGATE"},
            c_raw="C" * 100,
            c_duration_ms=200,
            c_error=c_error,
            phase_transition="DECOMPOSE→INVESTIGATE",
        )

    def test_truncate_limit_constant(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp10_reproducibility_cost.run import DEBUG_RAW_TRUNCATE_LIMIT
            self.assertEqual(DEBUG_RAW_TRUNCATE_LIMIT, 4096)
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_truncate_raw_edge_cases(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp10_reproducibility_cost.run import _truncate_raw
            self.assertEqual(_truncate_raw(""), "")
            self.assertEqual(_truncate_raw(None), "")
            self.assertEqual(_truncate_raw("short"), "short")
            long_text = "A" * 5000
            result = _truncate_raw(long_text)
            self.assertTrue(result.startswith("A" * 4096))
            self.assertIn("truncated", result)
            self.assertIn("original_len=5000", result)
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_serialize_single_log_schema(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp10_reproducibility_cost.run import _serialize_abc_logs
            log = self._make_dummy_log()
            result = _serialize_abc_logs([log])
            self.assertEqual(len(result), 1)
            self.assertEqual(set(result[0].keys()), self.EXPECTED_FIELDS)
            self.assertEqual(result[0]["cycle"], 1)
            self.assertEqual(result[0]["phase"], "DECOMPOSE")
            self.assertEqual(result[0]["a_raw"], "A" * 100)
            self.assertEqual(result[0]["b_raw"], "B" * 100)
            self.assertEqual(result[0]["c_raw"], "C" * 100)
            self.assertEqual(result[0]["phase_transition"], "DECOMPOSE→INVESTIGATE")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_serialize_error_preservation(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp10_reproducibility_cost.run import _serialize_abc_logs
            log = self._make_dummy_log(b_error="json parse failed", c_error=None)
            result = _serialize_abc_logs([log])
            self.assertEqual(result[0]["b_error"], "json parse failed")
            self.assertIsNone(result[0]["c_error"])
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_serialize_empty_list(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp10_reproducibility_cost.run import _serialize_abc_logs
            self.assertEqual(_serialize_abc_logs([]), [])
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))
```

본 클래스는 `sys`, `unittest` 사용 — 기존 import. `ABCCycleLog` / `LoopLog` 는 `orchestrator` 에서 import.

### Step 2 — 다른 클래스 미수정

기존 `TestImportInfra`, `TestDispatcherIntegrity`, ..., `TestSamplingParamsCentralization` 까지 10 클래스는 그대로. 본 task 는 11번째 클래스 추가.

## Dependencies

- **task-01 완료** — `_truncate_raw`, `_serialize_abc_logs`, `DEBUG_RAW_TRUNCATE_LIMIT` 모두 정의되어 있어야 import 통과.
- 외부 패키지: 없음 (stdlib `sys`, `unittest` 만 — 기존).

## Verification

```bash
# 1. test_static.py 모두 PASS — 24 → 29+ tests OK
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -10
# 기대: "Ran 29 tests" 이상 + "OK"

# 2. TestExp10DebugLoggingSchema 의 5 method 모두 통과
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static.TestExp10DebugLoggingSchema -v 2>&1 | tail -10
# 기대: "Ran 5 tests" + "OK"

# 3. 클래스 수 증가 — 10 → 11
cd /Users/d9ng/privateProject/gemento/experiments && grep -cE "^class Test" tests/test_static.py
# 기대: 11

# 4. 라인 수 — 318 → ~390 (~70 줄 추가)
wc -l /Users/d9ng/privateProject/gemento/experiments/tests/test_static.py

# 5. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/(exp10_reproducibility_cost/run\.py|tests/test_static\.py)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **task-01 의 helper 시그니처 변경**: 만약 task-01 이 `_truncate_raw` 의 limit 인자를 `_size` 같은 다른 이름으로 했으면 본 task 의 keyword arg 검증 깨짐. task-01 의 spec 은 `limit: int = DEBUG_RAW_TRUNCATE_LIMIT` 이므로 호환.
- **dummy `ABCCycleLog` 생성 — `a_log` 필수 인자**: ABCCycleLog 정의상 `a_log: LoopLog` 가 default 없는 필수 인자. dummy 생성 시 LoopLog 도 함께 만들어야 함 (본 task 의 `_make_dummy_log` 가 처리).
- **import path — `from orchestrator import ABCCycleLog`**: 본 test 가 `EXPERIMENTS_DIR` 을 sys.path 에 추가 후 import. 기존 다른 클래스들과 동일 패턴.
- **Test 수 변화 — `TestPerExperimentImports.SPLIT_EXPERIMENTS` 영향 없음**: 본 task 는 `exp10_reproducibility_cost` 등 디렉토리 list 변경 X. 기존 14 entry 그대로.
- **`_make_dummy_log` 의 module-level cache 문제**: `sys.path.insert` 와 `import` 를 매 method 마다 — `unittest` 가 method 단위 격리. 안전.

## Scope boundary

**Task 02 에서 절대 수정 금지**:

- `experiments/exp10_reproducibility_cost/run.py` — task-01 결과물 그대로.
- `experiments/orchestrator.py` — `LoopLog`, `ABCCycleLog` 정의 변경 금지.
- `experiments/tests/test_static.py` 의 기존 10 클래스 (`TestImportInfra` ~ `TestSamplingParamsCentralization`).
- `experiments/exp10_reproducibility_cost/analyze.py`, `tasks.py`, `INDEX.md`.
- `experiments/_external/` 의 모든 파일.
- 다른 expXX/ 디렉토리.
- `docs/plans/` 의 다른 plan 문서.

**허용 범위**:

- `experiments/tests/test_static.py` 의 마지막 클래스 (`TestSamplingParamsCentralization`) 다음, `if __name__ == "__main__":` 직전에 `TestExp10DebugLoggingSchema` 클래스 (~70 줄) 추가.
