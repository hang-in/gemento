"""실험 과정 실시간 로거.

실험 실행 중 각 단계를 파일과 콘솔에 동시 출력한다.
윈도우에서 실험 돌릴 때 터미널 + 로그 파일 양쪽에서 진행 확인 가능.
"""

from __future__ import annotations

import time
from pathlib import Path

from config import LOGS_DIR


class ExperimentLogger:
    """실험 과정을 파일과 콘솔에 동시 기록."""

    def __init__(self, experiment_name: str):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_path = LOGS_DIR / f"{experiment_name}_{timestamp}.log"
        self.file = open(self.log_path, "w", encoding="utf-8")
        self.experiment_name = experiment_name
        self._start_time = time.time()

        header = f"═══ {experiment_name} ═══ {time.strftime('%Y-%m-%d %H:%M:%S')}"
        self._write(header)
        self._write("")

    def _write(self, line: str):
        elapsed = time.time() - self._start_time
        timestamp = f"[{elapsed:7.1f}s]"
        formatted = f"{timestamp} {line}"
        print(formatted)
        self.file.write(formatted + "\n")
        self.file.flush()

    def task_start(self, task_id: str, trial: int, objective: str = ""):
        self._write("")
        self._write(f"{'─' * 60}")
        self._write(f"TASK: {task_id} | Trial {trial}")
        if objective:
            self._write(f"  목표: {objective[:80]}")
        self._write(f"{'─' * 60}")

    def cycle_start(self, cycle: int, phase: str, assertions: int, confidence: float):
        self._write("")
        self._write(f"  ┌─ Cycle {cycle} | Phase: {phase}")
        self._write(f"  │  assertions={assertions}, confidence={confidence:.2f}")

    def agent_a(self, duration_ms: int, new_assertions: int, final_answer: bool, error: str | None):
        status = "✓" if not error else f"⚠ {error}"
        self._write(f"  │  A(제안): {duration_ms}ms | new_assertions={new_assertions} | final_answer={'YES' if final_answer else 'no'} | {status}")

    def agent_a_reasoning(self, reasoning: str):
        if reasoning:
            # 첫 100자만 표시
            short = reasoning[:100].replace("\n", " ")
            if len(reasoning) > 100:
                short += "..."
            self._write(f"  │    └ \"{short}\"")

    def agent_b(self, duration_ms: int, total: int, invalid: int, suspect: int, error: str | None):
        if error:
            self._write(f"  │  B(비판): {duration_ms}ms | ⚠ {error}")
        else:
            self._write(f"  │  B(비판): {duration_ms}ms | {total} judged → {invalid} invalid, {suspect} suspect")

    def agent_b_details(self, judgments: list[dict]):
        for j in judgments:
            if j.get("status") in ("invalid", "suspect"):
                aid = j.get("assertion_id", "?")
                reason = j.get("reason", "")[:60]
                self._write(f"  │    └ [{j['status']}] {aid}: {reason}")

    def agent_c(self, duration_ms: int, converged: bool, next_phase: str | None, error: str | None):
        if error:
            self._write(f"  │  C(판정): {duration_ms}ms | ⚠ {error}")
        elif converged:
            self._write(f"  │  C(판정): {duration_ms}ms | ✓ CONVERGED → {next_phase}")
        else:
            self._write(f"  │  C(판정): {duration_ms}ms | ✗ not converged")

    def agent_c_reasoning(self, reasoning: str):
        if reasoning:
            short = reasoning[:100].replace("\n", " ")
            if len(reasoning) > 100:
                short += "..."
            self._write(f"  │    └ \"{short}\"")

    def phase_transition(self, old_phase: str, new_phase: str, by: str = "C"):
        self._write(f"  │  ──► Phase: {old_phase} → {new_phase} (by {by})")

    def safety_limit(self, old_phase: str, new_phase: str):
        self._write(f"  │  ⚠ SAFETY: {old_phase} → {new_phase} (Python 안전장치)")

    def cycle_end(self, cycle: int):
        self._write(f"  └─ Cycle {cycle} done")

    def trial_result(self, task_id: str, trial: int, converged: bool, final_answer: str | None, cycles: int):
        self._write("")
        status = "✅ PASS" if converged and final_answer else "❌ FAIL"
        self._write(f"  결과: {status} | cycles={cycles} | answer={'있음' if final_answer else '없음'}")
        if final_answer:
            short = str(final_answer)[:80]
            self._write(f"  답변: {short}")

    def summary(self, total: int, converged: int, correct: int):
        self._write("")
        self._write(f"{'═' * 60}")
        self._write(f"  수렴률: {converged}/{total} ({converged/total:.0%})" if total else "  No data")
        self._write(f"  정답률: {correct}/{total} ({correct/total:.0%})" if total else "")
        self._write(f"{'═' * 60}")

    def close(self):
        elapsed = time.time() - self._start_time
        self._write("")
        self._write(f"총 소요 시간: {elapsed:.0f}초 ({elapsed/60:.1f}분)")
        self._write(f"로그 저장: {self.log_path}")
        self.file.close()
