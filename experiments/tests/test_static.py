"""experiments 디렉토리 모듈화 정적 검증.

LLM 호출 없이 import·dispatcher·파일 위치만 점검한다.
Reviewer/Developer는 본 테스트 외 실증 검증을 시도하지 말 것.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

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

    EXPECTED_KEYS_AFTER_TASK_05 = {
        # task-05 후: tool-separation 제거됨, 13개 active
        "baseline", "assertion-cap", "multiloop", "error-propagation",
        "cross-validation", "abc-pipeline", "prompt-enhance",
        "handoff-protocol", "solo-budget", "loop-saturation",
        "tool-use", "tool-use-refined", "longctx",
    }

    def test_dispatcher_keys_match_expected(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            self.assertEqual(set(run_experiment.EXPERIMENTS.keys()),
                             self.EXPECTED_KEYS_AFTER_TASK_05)
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

    EXPECTED_TOTAL_RESULTS = 29  # 24 JSON + 5 report.md (task-02 후, .gitkeep 제거됨, log는 results/ 외부)

    def test_result_files_present(self):
        # task-01 시점: 모두 results/ 평면. task-02 후엔 분류됨.
        flat_results = list((EXPERIMENTS_DIR / "results").glob("*")) \
            if (EXPERIMENTS_DIR / "results").exists() else []
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
        # 24 JSON + 5 report.md = 29, + 1 log = 30
        all_results = []
        for exp in self.EXPECTED.keys():
            all_results.extend(list((EXPERIMENTS_DIR / exp / "results").glob("*")))
        log = EXPERIMENTS_DIR / "exp01_assertion_cap" / "exp01_run.log"
        if log.exists():
            all_results.append(log)
        self.assertEqual(len(all_results), 30,
                         f"expected 30 result files preserved, got {len(all_results)}")


class TestPerExperimentImports(unittest.TestCase):
    """task-03~06 — 각 실험 디렉토리의 run.py 가 import 가능한가"""

    SPLIT_EXPERIMENTS = (
        # task-03 후 추가될 항목. task-04~06이 확장. task-06 후 13 active 모두.
        ("exp00_baseline", "run", "run"),  # (dir, module, attr)
        ("exp01_assertion_cap", "run", "run"),
        ("exp02_multiloop", "run", "run"),
        ("exp03_error_propagation", "run", "run"),
        ("exp035_cross_validation", "run", "run"),
        ("exp04_abc_pipeline", "run", "run"),
        ("exp05a_prompt_enhance", "run", "run"),
        ("exp045_handoff_protocol", "run", "run"),
        ("exp06_solo_budget", "run", "run"),
        ("exp07_loop_saturation", "run", "run"),
        ("exp08_tool_use", "run", "run"),
        ("exp08b_tool_use_refined", "run", "run"),
        ("exp09_longctx", "run", "run"),
    )

    def test_each_split_experiment_imports(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            for exp_dir, module_name, attr in self.SPLIT_EXPERIMENTS:
                full_module = f"{exp_dir}.{module_name}"
                mod = __import__(full_module, fromlist=[attr])
                self.assertTrue(hasattr(mod, attr),
                                f"{full_module} has no `{attr}`")
                self.assertTrue(callable(getattr(mod, attr)),
                                f"{full_module}.{attr} not callable")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_split_dir_has_index_md(self):
        for exp_dir, _, _ in self.SPLIT_EXPERIMENTS:
            index = EXPERIMENTS_DIR / exp_dir / "INDEX.md"
            self.assertTrue(index.exists(), f"{exp_dir}/INDEX.md missing")

    def test_split_dir_has_results(self):
        for exp_dir, _, _ in self.SPLIT_EXPERIMENTS:
            results = EXPERIMENTS_DIR / exp_dir / "results"
            self.assertTrue(results.is_dir(), f"{exp_dir}/results missing")


class TestArchivedExperiments(unittest.TestCase):
    """task-05 — _archived/ 격리 정합성"""

    def test_archived_dir_exists(self):
        archived = EXPERIMENTS_DIR / "_archived"
        self.assertTrue(archived.is_dir())
        self.assertTrue((archived / "__init__.py").exists())

    def test_deprecated_tool_separation_importable_but_not_in_dispatcher(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from _archived.exp04_tool_separation_deprecated.run import run
            self.assertTrue(callable(run))
            import run_experiment
            self.assertNotIn("tool-separation", run_experiment.EXPERIMENTS,
                             "tool-separation should be removed from dispatcher")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_old_exp04_tool_separation_dir_removed(self):
        old_dir = EXPERIMENTS_DIR / "exp04_tool_separation"
        self.assertFalse(old_dir.exists(),
                         "old exp04_tool_separation/ should be removed (content absorbed)")


class TestNoLegacyRunFunctions(unittest.TestCase):
    """task-06 후 — run_experiment.py 본문에 def run_* 가 0개"""

    def test_no_legacy_run_functions_in_dispatcher(self):
        run_exp = EXPERIMENTS_DIR / "run_experiment.py"
        text = run_exp.read_text(encoding="utf-8")
        legacy = re.findall(r"^def run_\w+\s*\(", text, flags=re.M)
        self.assertEqual(legacy, [],
                         f"run_experiment.py still has legacy run_* defs: {legacy}")


class TestRunExperimentSlim(unittest.TestCase):
    """task-07 — run_experiment.py 가 dispatcher 모듈 수준으로 슬림"""

    MAX_LINES = 200  # 14 import + EXPERIMENTS dict + main 가정. 보수적 한계.

    def test_run_experiment_slim(self):
        run_exp = EXPERIMENTS_DIR / "run_experiment.py"
        lines = run_exp.read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), self.MAX_LINES,
                        f"run_experiment.py has {len(lines)} lines, expected < {self.MAX_LINES}")

    def test_dispatcher_keys_match_split_experiments(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            from tests.test_static import TestPerExperimentImports as TPEI
            split_dirs = {exp_dir for exp_dir, _, _ in TPEI.SPLIT_EXPERIMENTS}
            for k, v in run_experiment.EXPERIMENTS.items():
                module_name = v.__module__  # e.g. "exp00_baseline.run"
                top_dir = module_name.split(".")[0]
                self.assertIn(top_dir, split_dirs,
                              f"dispatcher[{k}] from unknown module {module_name}")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_template_dir_removed(self):
        tpl = EXPERIMENTS_DIR / "_template"
        self.assertFalse(tpl.exists(),
                         "_template/ should be removed in task-07")


if __name__ == "__main__":
    unittest.main()
