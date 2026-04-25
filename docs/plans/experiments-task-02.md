---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: A
depends_on: [01]
---

# Task 02 — 결과 JSON 30+개 → 실험별 `results/` 분류 (코드 변경 0)

## Changed files

- `experiments/exp00_baseline/results/` — **신규 디렉토리**. 3 JSON 이동.
- `experiments/exp01_assertion_cap/results/` — **신규 디렉토리** (이미 `experiments/exp01_assertion_cap/`은 존재). 7 JSON 이동.
- `experiments/exp02_multiloop/results/` — **신규 디렉토리**. 2 JSON + 1 report.md 이동.
- `experiments/exp03_error_propagation/results/` — **신규 디렉토리**. 1 JSON 이동.
- `experiments/exp035_cross_validation/results/` — **신규 디렉토리** (실험 디렉토리 자체도 신규). 1 JSON 이동.
- `experiments/exp04_abc_pipeline/results/` — **신규 디렉토리** (실험 디렉토리 자체도 신규). 1 JSON 이동.
- `experiments/exp045_handoff_protocol/results/` — **신규 디렉토리** (실험 디렉토리 자체도 신규). 3 JSON 이동.
- `experiments/exp05a_prompt_enhance/results/` — **신규 디렉토리** (실험 디렉토리 자체도 신규). 1 JSON 이동.
- `experiments/exp06_solo_budget/results/` — **신규 디렉토리** (실험 디렉토리 자체도 신규). 1 JSON 이동.
- `experiments/exp07_loop_saturation/results/` — **신규 디렉토리**. 1 JSON + 1 report.md 이동.
- `experiments/exp08_tool_use/results/` — **신규 디렉토리**. 1 JSON + 1 report.md 이동.
- `experiments/exp08b_tool_use_refined/results/` — **신규 디렉토리**. 1 JSON + 1 report.md 이동.
- `experiments/exp09_longctx/results/` — **신규 디렉토리**. 1 JSON + 1 report.md 이동.
- `experiments/exp01_assertion_cap/exp01_run.log` — top-level `exp01_run.log` 이동.
- `experiments/results/` — **삭제**. 모든 파일 이동 후 빈 디렉토리 제거.
- `experiments/tests/test_static.py` — **수정**. `TestResultFilesByExperiment` TestCase 추가.

신규 외 다른 파일 수정 금지. 본 task에서 코드(`*.py`)는 일절 수정하지 않는다 (test_static.py 제외).

## Change description

### 배경

현재 `experiments/results/` 안의 27 JSON + 4 report.md (총 31개) + top-level의 `exp01_run.log` 1개 = **32개 파일**이 평면적으로 섞여 있다. 본 task는 이를 실험 디렉토리별로 분류한다. **`git mv`만 사용** — history 끊김 방지.

본 task에서 코드는 일절 수정하지 않는다. `run_*()` 함수는 결과 저장 경로를 변경하지 않으므로, 분류 후에도 향후 실행이 일어나면 다시 `experiments/results/`(없으면 자동 생성)에 떨어진다. 이는 task-03~06에서 각 함수가 새 디렉토리로 옮겨지면서 자동 해결되거나, 또는 별도 후속 plan에서 각 `run_*()` 의 저장 경로를 `expXX/results/`로 바꾸는 식으로 처리. 본 plan 범위에서는 **현재 누적된 결과만 분류**.

### Step 1 — 신규 디렉토리 생성

`exp01_assertion_cap`, `exp02_multiloop`, `exp03_error_propagation`, `exp04_tool_separation`은 이미 존재 (껍데기). 이들에는 `results/` 하위 디렉토리만 추가. `exp035_cross_validation`, `exp04_abc_pipeline`, `exp045_handoff_protocol`, `exp05a_prompt_enhance`, `exp06_solo_budget`, `exp00_baseline`, `exp07_loop_saturation`, `exp08_tool_use`, `exp08b_tool_use_refined`, `exp09_longctx`는 신규 생성.

```bash
cd experiments
for d in exp00_baseline exp035_cross_validation exp04_abc_pipeline \
         exp045_handoff_protocol exp05a_prompt_enhance exp06_solo_budget \
         exp07_loop_saturation exp08_tool_use exp08b_tool_use_refined \
         exp09_longctx; do
  mkdir -p "$d/results"
done
for d in exp01_assertion_cap exp02_multiloop exp03_error_propagation; do
  mkdir -p "$d/results"
done
```

`exp04_tool_separation/`은 본 task에서 손대지 않음 (task-05에서 `_archived/` 로 이동 예정).

### Step 2 — 결과 파일 분류 이동 (`git mv`)

prefix 매칭으로 각 결과 파일을 적절한 `expXX/results/` 로 이동:

```bash
cd experiments

# exp00_baseline_*.json (3)
for f in results/exp00_baseline_*.json; do
  git mv "$f" exp00_baseline/results/
done

# exp01_assertion_cap*.json (7, partial 포함)
for f in results/exp01_assertion_cap*.json; do
  git mv "$f" exp01_assertion_cap/results/
done

# exp02_multiloop_*.json (2) + exp02_report.md
for f in results/exp02_multiloop_*.json results/exp02_report.md; do
  git mv "$f" exp02_multiloop/results/
done

# exp03_error_propagation_*.json (1)
git mv results/exp03_error_propagation_20260409_135411.json exp03_error_propagation/results/

# exp035_cross_validation_*.json (1)
git mv results/exp035_cross_validation_20260409_150703.json exp035_cross_validation/results/

# exp04_abc_pipeline_*.json (1)
git mv results/exp04_abc_pipeline_20260409_182751.json exp04_abc_pipeline/results/

# exp045_handoff_protocol_*.json (3)
for f in results/exp045_handoff_protocol_*.json; do
  git mv "$f" exp045_handoff_protocol/results/
done

# exp05a_prompt_enhance_*.json (1)
git mv results/exp05a_prompt_enhance_20260410_145033.json exp05a_prompt_enhance/results/

# exp06_solo_budget_*.json (1)
git mv results/exp06_solo_budget_20260415_114625.json exp06_solo_budget/results/

# exp07_loop_saturation_*.json (1) + exp07_report.md
git mv results/exp07_loop_saturation_20260424_015343.json exp07_loop_saturation/results/
git mv results/exp07_report.md exp07_loop_saturation/results/

# exp08_tool_use_*.json (1) + exp08_report.md
git mv results/exp08_tool_use_20260424_125350.json exp08_tool_use/results/
git mv results/exp08_report.md exp08_tool_use/results/

# exp08b_tool_use_refined_*.json (1) + exp08b_report.md
git mv results/exp08b_tool_use_refined_20260424_234043.json exp08b_tool_use_refined/results/
git mv results/exp08b_report.md exp08b_tool_use_refined/results/

# exp09_longctx_*.json (1) + exp09_report.md
git mv results/exp09_longctx_20260425_144412.json exp09_longctx/results/
git mv results/exp09_report.md exp09_longctx/results/
```

### Step 3 — top-level `exp01_run.log` 이동

```bash
cd experiments
git mv exp01_run.log exp01_assertion_cap/
```

### Step 4 — 빈 `experiments/results/` 디렉토리 제거

```bash
cd experiments
rmdir results
```

빈 디렉토리는 git이 자동으로 추적 안 함. 만약 다른 untracked 파일 남으면 명령이 실패하므로 확인 후 진행.

### Step 5 — `tests/test_static.py` 확장 — `TestResultFilesByExperiment`

다음 TestCase를 `tests/test_static.py` 끝에 추가 (TestIndexLinkIntegrity 다음):

```python
class TestResultFilesByExperiment(unittest.TestCase):
    """task-02 후 — 결과 파일이 실험별 results/ 디렉토리에 정확히 배치됨"""

    EXPECTED = {
        "exp00_baseline": {"prefix": "exp00_baseline_", "json_count": 3, "extras": []},
        "exp01_assertion_cap": {"prefix": "exp01_assertion_cap", "json_count": 7, "extras": []},
        "exp02_multiloop": {"prefix": "exp02_multiloop_", "json_count": 2,
                            "extras": ["exp02_report.md"]},
        "exp03_error_propagation": {"prefix": "exp03_error_propagation_", "json_count": 1, "extras": []},
        "exp035_cross_validation": {"prefix": "exp035_cross_validation_", "json_count": 1, "extras": []},
        "exp04_abc_pipeline": {"prefix": "exp04_abc_pipeline_", "json_count": 1, "extras": []},
        "exp045_handoff_protocol": {"prefix": "exp045_handoff_protocol_", "json_count": 3, "extras": []},
        "exp05a_prompt_enhance": {"prefix": "exp05a_prompt_enhance_", "json_count": 1, "extras": []},
        "exp06_solo_budget": {"prefix": "exp06_solo_budget_", "json_count": 1, "extras": []},
        "exp07_loop_saturation": {"prefix": "exp07_loop_saturation_", "json_count": 1,
                                  "extras": ["exp07_report.md"]},
        "exp08_tool_use": {"prefix": "exp08_tool_use_", "json_count": 1,
                          "extras": ["exp08_report.md"]},
        "exp08b_tool_use_refined": {"prefix": "exp08b_tool_use_refined_", "json_count": 1,
                                    "extras": ["exp08b_report.md"]},
        "exp09_longctx": {"prefix": "exp09_longctx_", "json_count": 1,
                          "extras": ["exp09_report.md"]},
    }

    def test_results_dir_per_experiment(self):
        for exp_name, spec in self.EXPECTED.items():
            results_dir = EXPERIMENTS_DIR / exp_name / "results"
            self.assertTrue(results_dir.is_dir(), f"missing {results_dir}")
            json_files = sorted(results_dir.glob("*.json"))
            self.assertEqual(len(json_files), spec["json_count"],
                             f"{exp_name}: expected {spec['json_count']} JSONs, got {len(json_files)}")
            for j in json_files:
                self.assertTrue(j.name.startswith(spec["prefix"]),
                                f"{exp_name}: foreign file {j.name}")
            for extra in spec["extras"]:
                self.assertTrue((results_dir / extra).exists(),
                                f"{exp_name}: missing {extra}")

    def test_top_level_results_dir_removed(self):
        self.assertFalse((EXPERIMENTS_DIR / "results").exists(),
                         "experiments/results/ should be removed after task-02")

    def test_no_misplaced_top_level_logs(self):
        self.assertFalse((EXPERIMENTS_DIR / "exp01_run.log").exists(),
                         "exp01_run.log should be moved to exp01_assertion_cap/")

    def test_total_result_count_preserved(self):
        # 32 = 27 JSON + 4 report.md + 1 log
        all_results = []
        for exp in self.EXPECTED.keys():
            all_results.extend(list((EXPERIMENTS_DIR / exp / "results").glob("*")))
        log = EXPERIMENTS_DIR / "exp01_assertion_cap" / "exp01_run.log"
        if log.exists():
            all_results.append(log)
        # 27 JSON + 4 report.md = 31, + 1 log = 32
        self.assertEqual(len(all_results), 32,
                         f"expected 32 result files preserved, got {len(all_results)}")
```

또한 `TestResultFileInventory.test_result_files_present`의 `EXPECTED_TOTAL_RESULTS`를 다시 점검 (현재 31 → 32 유지 가능, 단순히 `>=` 조건이라 문제 없음).

### Step 6 — git status 확인

```bash
git status --short
```

기대: 모든 변경이 `R` (rename) 으로 표시되어야 함. `D` + `A` 쌍이 보이면 `git mv` 가 아닌 `mv` 로 이동된 것 → history 끊김. 그 경우 되돌리고 `git mv` 재실행.

## Dependencies

- **Task 01 완료** — `tests/test_static.py` 가 존재하고 12 tests PASS 상태여야 본 task가 그 위에 추가.
- 외부 패키지: 없음.
- git 워킹 트리 깨끗해야 함 (이전 변경 stash 또는 commit 권장).

## Verification

```bash
# 1. 모든 결과 파일이 실험별 디렉토리로 이동됨 — 32개 보존
cd experiments && find . -path './_template' -prune -o -path './tests' -prune -o \
  -path './tools' -prune -o -path './tasks' -prune -o \
  -name "exp*_*.json" -print -o -name "*_report.md" -print -o -name "exp01_run.log" -print | wc -l
# 기대: 32

# 2. experiments/results/ 디렉토리 제거됨
test ! -d experiments/results && echo "OK results dir removed"

# 3. test_static.py 가 새 TestCase 포함하여 PASS
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -15
# 기대: 12 + 4 = 16 tests Ran, OK (TestResultFilesByExperiment 4 메소드 추가됨)

# 4. git history 보존 확인 — git log --follow 로 한 파일 추적
cd experiments && git log --follow --oneline exp08b_tool_use_refined/results/exp08b_tool_use_refined_20260424_234043.json | head -3
# 기대: 최소 2 commit 이상 (원본 commit + 본 task commit) — rename 추적

# 5. git status 가 모두 R (rename) 인지
cd /Users/d9ng/privateProject/gemento && git status --short experiments/ | grep -E "^[ MD]" | grep -vE "^R" | head
# 기대: 출력 0 라인 (모두 R로 추적됨)

# 6. 코드 파일 변경 0 (test_static.py 제외)
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ | grep "\.py$" | grep -v "test_static.py"
# 기대: 출력 0 라인

# 7. EXPERIMENTS dict (run_experiment.py:1442) 변경 안 됨
cd /Users/d9ng/privateProject/gemento && git diff HEAD experiments/run_experiment.py | wc -l
# 기대: 0

# 8. 각 실험 디렉토리에 results/ 와 정확한 prefix 의 JSON 만 들어있음 (Python 검증)
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from tests.test_static import TestResultFilesByExperiment
from pathlib import Path
EXP = Path('.').resolve()
for exp_name, spec in TestResultFilesByExperiment.EXPECTED.items():
    results = EXP / exp_name / 'results'
    assert results.is_dir(), f'missing {results}'
    json_files = sorted(results.glob('*.json'))
    assert len(json_files) == spec['json_count'], f\"{exp_name}: expected {spec['json_count']} JSON, got {len(json_files)}\"
    for j in json_files:
        assert j.name.startswith(spec['prefix']), f\"{exp_name}: foreign {j.name}\"
print('OK results-by-experiment classification')
"
```

## Risks

- **`git mv` vs `mv`**: 일반 `mv` 사용 시 git이 rename 추적 못 하고 `D` + `A` 로 처리 → history 끊김. 본 task에서는 반드시 `git mv` 사용. Verification 5번이 catch.
- **기존 빈 껍데기 디렉토리**: `experiments/exp01_assertion_cap/`, `exp02_multiloop/`, `exp03_error_propagation/`, `exp04_tool_separation/` 는 이미 존재하고 안에 `설명.md` 있음. `mkdir -p $d/results` 로 results/ 만 추가. 설명.md 는 task-03~06에서 INDEX.md로 흡수.
- **`exp04_tool_separation/`은 손대지 않음**: deprecated 처리는 task-05 영역. 본 task에서는 결과 파일 매핑에서도 제외 (애초에 결과 파일 0개).
- **partial 파일 7개 (`exp01_assertion_cap_partial_*`)**: glob `exp01_assertion_cap*.json` 으로 매칭. exclude 안 함 (history 보존 목적).
- **report.md 가 results/ 안에 들어가는 게 어색**: `expXX/report.md` 와 `expXX/results/report.md` 중 후자 선택 — INDEX 표에서 일관된 결과 디렉토리만 보면 되도록. 단점: report 가 results 안에 있는 게 의미상 어긋남. 본 plan 범위 밖 (별도 plan에서 재배치 가능).
- **rmdir 실패**: 이동 누락 시 `experiments/results/` 가 비어있지 않아 rmdir 실패. Verification 1번 (32개 카운트) 으로 사전 catch.
- **Python `__pycache__`**: 일부 디렉토리에 `__pycache__/` 가 untracked로 들어있을 수 있음 (gitignore 처리). Verification 2번에 영향 없음 (test ! -d).

## Scope boundary

**Task 02에서 절대 수정 금지**:

- `experiments/run_experiment.py` — 본문 일체. EXPERIMENTS dict (line 1442), 14개 `run_*()` 함수.
- `experiments/orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `experiment_logger.py`, `config.py`.
- `experiments/exp01_assertion_cap/설명.md` 등 기존 파일 (results/ 만 추가).
- `experiments/exp04_tool_separation/` — task-05 영역.
- `experiments/tools/`, `experiments/tasks/`, `experiments/tests/__init__.py`.
- `experiments/INDEX.md` (task-07 에서 갱신).
- `docs/plans/*` — 본 task 외 plan 문서.

**허용 범위**:

- 결과 파일 32개 `git mv`로 이동.
- 신규 `expXX_*/results/` 디렉토리 13개 생성.
- 빈 `experiments/results/` 제거.
- `experiments/tests/test_static.py` 에 `TestResultFilesByExperiment` TestCase 추가 (1 클래스, 4 메소드).
