---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: A
depends_on: []
---

# Task 01 — 정적 검증 인프라 + 디렉토리 템플릿 + 최상위 INDEX 골격

## Changed files

- `experiments/tests/__init__.py` — **신규** (빈 파일, 패키지 표지).
- `experiments/tests/test_static.py` — **신규**. unittest 기반 정적 검증 모음.
- `experiments/INDEX.md` — **신규**. 최상위 실험 인덱스 골격 (이번 task에서는 표 헤더 + 빈 행만, 후속 task에서 채움).
- `experiments/_template/INDEX.md.tpl` — **신규**. 각 실험 디렉토리의 INDEX.md 템플릿.
- `experiments/_template/run.py.tpl` — **신규**. 각 실험 디렉토리의 run.py 골격 (docstring + `def run():` 시그니처).

신규 외 다른 파일 수정 금지. 본 task에서 `run_experiment.py` 본문에는 손대지 않는다.

## Change description

### 배경

본 plan의 핵심 가드: **모든 후속 verification이 LLM 호출 0의 정적 테스트로 통과 가능해야 한다.** Task-01은 그 인프라를 깐다. test_static.py는 본 plan의 모든 task에서 실행되는 단일 게이트.

### Step 1 — `experiments/tests/__init__.py` 생성

빈 파일. unittest discover가 `experiments.tests` 패키지를 인식하도록.

### Step 2 — `experiments/tests/test_static.py` 신규 작성

unittest 기반. 4개 TestCase, 약 12개 메소드. 본 task에서는 모든 테스트가 **현재 상태에서 PASS** 하도록 작성 (이미 존재하는 파일·dispatcher 검증). 후속 task가 구조를 바꾸면 그에 맞춰 테스트가 자동으로 더 까다로워지는 게 아니라, 후속 task가 테스트를 **확장**하는 식.

본 task 시점에서 검증할 항목:

```python
"""experiments 디렉토리 모듈화 정적 검증.

LLM 호출 없이 import·dispatcher·파일 위치만 점검한다.
Reviewer/Developer는 본 테스트 외 실증 검증을 시도하지 말 것.
"""
import unittest
from pathlib import Path
import re
import sys

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = EXPERIMENTS_DIR.parent


class TestImportInfra(unittest.TestCase):
    """공용 모듈 import 무결성 — 모든 실험이 의존하는 base"""

    def test_orchestrator_imports(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import orchestrator
            self.assertTrue(hasattr(orchestrator, "run_abc_chain"))
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_run_experiment_module_imports(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            self.assertTrue(hasattr(run_experiment, "EXPERIMENTS"))
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))


class TestDispatcherIntegrity(unittest.TestCase):
    """EXPERIMENTS dict ↔ argparse choices 일관성"""

    EXPECTED_KEYS_INITIAL = {
        # 본 task 작성 시점: 14개 모두 활성. task-05 후 13개로 줄어듦.
        "baseline", "assertion-cap", "multiloop", "error-propagation",
        "cross-validation", "abc-pipeline", "prompt-enhance",
        "tool-separation",  # task-05에서 제거 예정
        "handoff-protocol", "solo-budget", "loop-saturation",
        "tool-use", "tool-use-refined", "longctx",
    }

    def test_dispatcher_keys_match_expected(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            self.assertEqual(set(run_experiment.EXPERIMENTS.keys()),
                             self.EXPECTED_KEYS_INITIAL)
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_each_dispatcher_value_is_callable(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            for k, v in run_experiment.EXPERIMENTS.items():
                self.assertTrue(callable(v), f"dispatcher[{k}] not callable")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))


class TestResultFileInventory(unittest.TestCase):
    """결과 파일 개수·prefix 매핑 무결성"""

    EXPECTED_TOTAL_RESULTS = 31  # 27 JSON + 4 report.md

    def test_result_files_present(self):
        # task-01 시점: 모두 results/ 평면. task-02 후엔 분류됨.
        flat_results = list((EXPERIMENTS_DIR / "results").glob("*"))
        per_dir_results = list(EXPERIMENTS_DIR.glob("exp*/results/*"))
        total = len(flat_results) + len(per_dir_results)
        self.assertGreaterEqual(total, self.EXPECTED_TOTAL_RESULTS,
                                f"expected ≥{self.EXPECTED_TOTAL_RESULTS} files, got {total}")


class TestIndexLinkIntegrity(unittest.TestCase):
    """INDEX.md 의 [text](path) 링크 모두 실재"""

    def test_top_level_index_links(self):
        index = EXPERIMENTS_DIR / "INDEX.md"
        if not index.exists():
            self.skipTest("INDEX.md not yet created (task-01 in progress)")
        text = index.read_text(encoding="utf-8")
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+\.md)\)", text):
            link = m.group(2)
            if link.startswith("http"):
                continue
            target = (index.parent / link).resolve()
            self.assertTrue(target.exists(), f"broken link: {link}")


if __name__ == "__main__":
    unittest.main()
```

후속 task에서 추가될 테스트 (이 task에서는 작성 안 함, 단지 hook만 남겨둠):

- `TestPerExperimentImports`: 각 `experiments/exp*/run.py` 가 import 가능한지 (task-03 부터 추가).
- `TestResultFilesByExperiment`: 각 `experiments/exp*/results/` 디렉토리에 정확한 prefix의 JSON만 들어있는지 (task-02 후 추가).
- `TestNoLegacyRunFunctions`: `run_experiment.py` 본문에 `^def run_` 매칭이 0건인지 (task-07 후 추가).

**본 task에서는 위 4개 TestCase의 12개 메소드만 작성하고 PASS 시킴.**

### Step 3 — `experiments/INDEX.md` 골격 작성

```markdown
# Experiments — Index

이 디렉토리는 gemento 프로젝트의 모든 실험을 단위로 관리한다. 각 실험은
독립 디렉토리(`expXX_<slug>/`)로 구성되며 `run.py` (실행 함수), `results/`
(결과 JSON·리포트), `INDEX.md` (개요) 를 보유한다.

## 실험 목록 (13 active + 1 archived)

| # | 디렉토리 | dispatcher key | 핵심 가설 | 결과 |
|---|---------|---------------|-----------|------|
| 00 | TBD | `baseline` | - | TBD |
| 01 | TBD | `assertion-cap` | TBD | TBD |
| 02 | TBD | `multiloop` | H1 | TBD |
| 03 | TBD | `error-propagation` | H2 | TBD |
| 03.5 | TBD | `cross-validation` | TBD | TBD |
| 04 | TBD | `abc-pipeline` | TBD | TBD |
| 05a | TBD | `prompt-enhance` | TBD | TBD |
| 04.5 | TBD | `handoff-protocol` | TBD | TBD |
| 06 | TBD | `solo-budget` | TBD | TBD |
| 07 | TBD | `loop-saturation` | TBD | TBD |
| 08 | TBD | `tool-use` | H7 | TBD |
| 08b | TBD | `tool-use-refined` | H8 | TBD |
| 09 | TBD | `longctx` | H9 | TBD |
| (deprecated) | `_archived/exp04_tool_separation_deprecated/` | (제거됨) | - | - |

> 표의 TBD 열은 task-03~07 진행 중에 채워진다. 본 INDEX는 plan
> `experiments`의 task-07 종료 시점에 완성된다.

## 디렉토리 구조 표준

각 활성 실험 디렉토리는 다음 파일을 가진다:

- `run.py` — `def run():` 실행 함수. `experiments/run_experiment.py`가 import.
- `INDEX.md` — 실험 개요, 하이퍼파라미터, 메트릭, 결과 파일 링크.
- `results/` — 해당 실험의 모든 JSON·report.md. 다른 실험 결과 혼입 금지.
- (선택) `config.py` — 실험별 상수.

공용 모듈(`orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`,
`experiment_logger.py`, `tools/`, `tasks/`)는 `experiments/` 최상위에 유지.

## 검증

오프라인 정적 검증:

```
cd experiments
../.venv/bin/python -m unittest tests.test_static -v
```

실증(LLM) 검증은 사용자 환경에서 별도 진행. 본 디렉토리 검증 가이드는
LLM 호출을 동반하지 않는다.
```

### Step 4 — 템플릿 파일 작성

`experiments/_template/INDEX.md.tpl`:

```markdown
# 실험 NN: <제목>

## 개요

<1-2문단: 가설, 검증 목적, 결과 요약>

## dispatcher key

`<key>` (`python run_experiment.py <key>` 호출)

## 하이퍼파라미터

- max_cycles: TBD
- repeat: TBD
- 기타 상수: `run.py` 또는 `config.py` 참조

## 결과

- `results/<file>.json` (실행 N회)
- `results/<report>.md` (있다면)

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| TBD | TBD | TBD | TBD |

## 변경 이력

- YYYY-MM-DD: 신규
```

`experiments/_template/run.py.tpl`:

```python
"""실험 <NN>: <제목>.

dispatcher key: <key>
원본 함수: experiments/run_experiment.py:<func_name> (line <N>)
"""

# 본 함수 본문은 task-03~06에서 원본 run_experiment.py 의 해당 함수에서
# 그대로 옮겨온다. 로직 수정 금지.

def run():
    raise NotImplementedError("populate from run_experiment.py")
```

### Step 5 — 본 task에서 절대 안 하는 것

- `run_experiment.py` 본문 수정.
- 실제 실험 디렉토리(`exp00_baseline/` 등) 생성.
- 결과 파일 이동.
- INDEX.md 표 채우기 (task-07에서).

## Dependencies

- 선행 Task 없음 (`depends_on: []`).
- 외부 패키지: 없음 (Python 표준 라이브러리 unittest, pathlib, re만 사용).
- `.venv` Python: `../.venv/bin/python` (PEP 668 venv).

## Verification

```bash
# 1. 신규 파일 5개 모두 존재
test -f experiments/tests/__init__.py && \
test -f experiments/tests/test_static.py && \
test -f experiments/INDEX.md && \
test -f experiments/_template/INDEX.md.tpl && \
test -f experiments/_template/run.py.tpl && \
echo "OK 5 files exist"

# 2. test_static.py 단독 실행 통과 (LLM 호출 0)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -10
# 기대: "Ran 12 tests" 와 "OK"

# 3. test_static.py 가 LLM 호출 안 함을 코드 레벨 확인 (httpx·requests 미사용)
grep -E "import (httpx|requests)|from (httpx|requests)" experiments/tests/test_static.py
# 기대: 출력 0 라인 (exit code 1)

# 4. test_static.py 의 EXPECTED_KEYS_INITIAL 가 현재 dispatcher 와 일치
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
from tests.test_static import TestDispatcherIntegrity as T
assert set(run_experiment.EXPERIMENTS.keys()) == T.EXPECTED_KEYS_INITIAL, \
    f'mismatch: {set(run_experiment.EXPERIMENTS.keys()) ^ T.EXPECTED_KEYS_INITIAL}'
print('OK dispatcher keys match expected initial set')
"

# 5. INDEX.md 가 valid markdown (간단한 검증 — 헤더 존재 + Active 섹션 표가 있는지)
grep -q "^# Experiments" experiments/INDEX.md && \
grep -q "| 00 | TBD" experiments/INDEX.md && \
echo "OK INDEX skeleton present"

# 6. 다른 파일이 변경 안 됨 (Task 01 범위 검증)
cd /Users/d9ng/privateProject/gemento && git diff --name-only HEAD experiments/ | grep -vE '^experiments/(tests/|INDEX\.md$|_template/)' || echo "OK no extra modifications"
# 기대: "OK no extra modifications"

# 7. test_static.py 가 unittest discover 로도 발견됨
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest discover -s tests -v 2>&1 | tail -5
# 기대: 발견된 12 tests, 모두 OK
```

## Risks

- **unittest 환경 변수 의존**: `_ZO_DOCTOR=0` 미설정 시 zoxide 경고가 stdout 섞임. Verification 명령에 명시.
- **sys.path 조작**: test_static.py가 `sys.path.insert/remove`로 `experiments/`를 추가. test 격리 안 되면 다른 모듈 import 부작용. 본 task에서는 try/finally로 cleanup.
- **EXPECTED_KEYS_INITIAL의 짧은 수명**: 14개 키 중 `tool-separation` 은 task-05에서 제거됨. 그 시점에 task-05가 본 상수를 갱신. 본 task에서는 14개 그대로 유지.
- **INDEX.md 의 TBD 가 보이는 문제**: 사용자 검토 시 "왜 다 TBD?" 질문 가능. INDEX.md 본문에 *"task-03~07 진행 중에 채워진다"* 명시.
- **`_template/`의 noise**: 본 디렉토리는 코드 베이스에는 안 쓰이는 보조 파일. 후속 task 6에서 사용 후 삭제 가능. 본 task 범위 밖.
- **PYTHONPATH 누락 환경**: `python -m unittest tests.test_static` 호출 시 CWD가 `experiments/` 인지 확인. 다른 위치에서 호출하면 import 실패. Verification 명령에 `cd experiments` 명시.

## Scope boundary

**Task 01에서 절대 수정 금지**:

- `experiments/run_experiment.py` (본문, EXPERIMENTS dict 모두) — task-07까지 손대지 않음.
- `experiments/orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `experiment_logger.py`, `config.py` — 공용 모듈.
- `experiments/exp01_assertion_cap/`, `exp02_multiloop/`, `exp03_error_propagation/`, `exp04_tool_separation/` — 기존 빈 껍데기 디렉토리. 본 task에서는 손대지 않음 (task-04/05 영역).
- `experiments/results/` — 결과 파일 이동은 task-02 영역.
- `experiments/tools/`, `experiments/tasks/` — 공용 디렉토리.
- `docs/plans/*` (본 task 외 plan 문서) — 손대지 않음.

**허용 범위**:

- `experiments/tests/__init__.py`, `experiments/tests/test_static.py` 신규.
- `experiments/INDEX.md` 신규 (골격만).
- `experiments/_template/INDEX.md.tpl`, `experiments/_template/run.py.tpl` 신규.
