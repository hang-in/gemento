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
        # exp10-task-05 후: reproducibility-cost 추가, 14개 active
        "baseline", "assertion-cap", "multiloop", "error-propagation",
        "cross-validation", "abc-pipeline", "prompt-enhance",
        "handoff-protocol", "solo-budget", "loop-saturation",
        "tool-use", "tool-use-refined", "longctx",
        "reproducibility-cost",
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
        ("exp10_reproducibility_cost", "run", "run"),
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


class TestSamplingParamsCentralization(unittest.TestCase):
    """sampling-params-config-exp10 plan — config.py SAMPLING_PARAMS 일원화 검증.

    - SAMPLING_PARAMS 가 config.py 에 정의되고 4 필드 존재
    - orchestrator.py·lmstudio_client.py 가 모두 SAMPLING_PARAMS 참조
    - 두 파일 본문에 sampling literal 직접 하드코딩 0건
    """

    EXPECTED_FIELDS = {"temperature", "max_tokens", "top_p", "seed"}
    EXPECTED_VALUES = {"temperature": 0.1, "max_tokens": 4096, "top_p": None, "seed": None}

    def test_sampling_params_exists_with_expected_fields(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from config import SAMPLING_PARAMS
            self.assertEqual(set(SAMPLING_PARAMS.keys()), self.EXPECTED_FIELDS)
            for k, v in self.EXPECTED_VALUES.items():
                self.assertEqual(SAMPLING_PARAMS[k], v,
                                 f"SAMPLING_PARAMS[{k!r}] expected {v}, got {SAMPLING_PARAMS[k]}")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_orchestrator_references_sampling_params(self):
        text = (EXPERIMENTS_DIR / "orchestrator.py").read_text(encoding="utf-8")
        self.assertIn("SAMPLING_PARAMS", text,
                      "orchestrator.py must reference SAMPLING_PARAMS")

    def test_lmstudio_client_references_sampling_params(self):
        text = (EXPERIMENTS_DIR / "_external" / "lmstudio_client.py").read_text(encoding="utf-8")
        self.assertIn("SAMPLING_PARAMS", text,
                      "lmstudio_client.py must reference SAMPLING_PARAMS")

    def test_no_hardcoded_sampling_literals(self):
        """orchestrator.py·lmstudio_client.py 본문에 sampling 키:리터럴 직접 매핑 금지."""
        targets = [
            EXPERIMENTS_DIR / "orchestrator.py",
            EXPERIMENTS_DIR / "_external" / "lmstudio_client.py",
        ]
        # "temperature": 0.1 또는 "max_tokens": 4096 같은 직접 매핑
        pattern = re.compile(r'"(temperature|max_tokens|top_p|seed)"\s*:\s*[0-9]')
        for path in targets:
            text = path.read_text(encoding="utf-8")
            matches = pattern.findall(text)
            self.assertEqual(matches, [],
                             f"{path.name} has hardcoded sampling literals: {matches}")


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


class TestScoreAnswerV3(unittest.TestCase):
    """exp10-v3-scorer plan — score_answer_v3 의 negative_patterns 차단 + conclusion_required 검증."""

    def setUp(self):
        self.task = {
            "id": "logic-04-mock",
            "scoring_keywords": [["casey"]],
            "negative_patterns": [
                r"no\s+(unique|definitive|clear)\s+(culprit|answer|solution)",
                r"cannot\s+be\s+(identified|determined|solved)",
                r"contradicts?|contradiction|contradictions",
                r"puzzle\s+is\s+(flawed|inconsistent|ill-?posed)",
            ],
        }

    def _import_v3(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from measure import score_answer_v3
            return score_answer_v3
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_v2_match_no_negative(self):
        score_answer_v3 = self._import_v3()
        response = "Casey committed the crime. The other three are innocent."
        self.assertEqual(score_answer_v3(response, self.task), 1.0)

    def test_negative_pattern_blocks_substring_match(self):
        score_answer_v3 = self._import_v3()
        response = (
            "Assuming Casey is guilty leads to a contradiction. "
            "All four suspects lead to similar contradictions, so the puzzle is inconsistent."
        )
        self.assertEqual(score_answer_v3(response, self.task), 0.0)

    def test_no_keyword_returns_zero(self):
        score_answer_v3 = self._import_v3()
        response = "Dana committed the crime."
        self.assertEqual(score_answer_v3(response, self.task), 0.0)

    def test_empty_response(self):
        score_answer_v3 = self._import_v3()
        self.assertEqual(score_answer_v3("", self.task), 0.0)
        self.assertEqual(score_answer_v3(None, self.task), 0.0)

    def test_no_negative_patterns_falls_back_to_v2(self):
        score_answer_v3 = self._import_v3()
        task = {"id": "x", "scoring_keywords": [["casey"]]}
        response = "Casey did it."
        self.assertEqual(score_answer_v3(response, task), 1.0)

    def test_conclusion_required_match_at_tail(self):
        score_answer_v3 = self._import_v3()
        task = {
            "id": "x",
            "scoring_keywords": [["casey"]],
            "conclusion_required": [r"casey\s+(committed|is\s+(the|guilty))"],
        }
        response = (
            "After analysis of all suspects, the conclusion is that Casey committed the crime."
        )
        self.assertEqual(score_answer_v3(response, task), 1.0)

    def test_conclusion_required_miss_at_tail(self):
        score_answer_v3 = self._import_v3()
        task = {
            "id": "x",
            "scoring_keywords": [["casey"]],
            "conclusion_required": [r"casey\s+(committed|is\s+(the|guilty))"],
        }
        response = (
            "Casey was one of the suspects. After analysis, no clear answer can be derived."
            + (" filler." * 30)
        )
        self.assertEqual(score_answer_v3(response, task), 0.0)


class TestExtractJsonFromResponseV3(unittest.TestCase):
    """exp10-v3-scorer plan task-05 — fence 미닫힘 / partial JSON 복구 케이스 검증."""

    def _import(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from orchestrator import extract_json_from_response
            return extract_json_from_response
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_existing_fenced_json(self):
        extract = self._import()
        raw = '```json\n{"final_answer": "Casey"}\n```'
        self.assertEqual(extract(raw), {"final_answer": "Casey"})

    def test_unclosed_fence_lenient(self):
        extract = self._import()
        raw = '```json\n{"final_answer": "Casey", "reasoning": "complete"}'
        self.assertEqual(
            extract(raw),
            {"final_answer": "Casey", "reasoning": "complete"},
        )

    def test_partial_json_brace_recovery(self):
        extract = self._import()
        # 응답 도중 짤린 partial JSON — last complete close 까지 복구
        raw = (
            '{"reasoning": "step 1", '
            '"final_answer": "Casey"} extra trailing text "incomp'
        )
        result = extract(raw)
        self.assertIsNotNone(result)
        assert result is not None  # mypy hint
        self.assertEqual(result.get("final_answer"), "Casey")

    def test_partial_json_depth_close(self):
        extract = self._import()
        # depth > 0 으로 끝나는 partial JSON — 부족한 '}' 채움 + 미완성 string trim
        raw = '{"final_answer": "Casey", "reasoning": "incomplete'
        result = extract(raw)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.get("final_answer"), "Casey")

    def test_no_json_returns_none(self):
        extract = self._import()
        raw = "This is plain text with no JSON."
        self.assertIsNone(extract(raw))

    def test_empty_returns_none(self):
        extract = self._import()
        self.assertIsNone(extract(""))
        self.assertIsNone(extract(None))

    def test_unclosed_fence_with_partial_brace(self):
        """v2 final synthesis-01 t14 패턴 — fence 미닫힘 + brace 4/3."""
        extract = self._import()
        raw = (
            '```json\n'
            '{\n'
            '  "verdict": "FAIL",\n'
            '  "reason": "B critique partial",\n'
            '  "details": {\n'
            '    "step1": "ok",\n'
            '    "step2": "the stated hourly cost for Provider B."\n'
            '  },\n  '
        )
        result = extract(raw)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.get("verdict"), "FAIL")


if __name__ == "__main__":
    unittest.main()
