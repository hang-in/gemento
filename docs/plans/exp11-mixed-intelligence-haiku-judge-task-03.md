---
type: plan-task
status: done
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — `exp11_mixed_intelligence/run.py` + condition 정의 + tattoo_history fix

## Changed files

- `experiments/exp11_mixed_intelligence/__init__.py` — **신규**
- `experiments/exp11_mixed_intelligence/run.py` — **신규**. 2 condition (baseline_abc + **mixed_flash_judge**) + cycle-by-cycle tattoo_history 저장 + Gemini Flash c_caller
- `experiments/exp11_mixed_intelligence/results/.gitkeep` — **신규**

신규 3. **v2 (2026-05-02)**: condition 명 `mixed_haiku_judge` → `mixed_flash_judge`. import 변경 (anthropic_client → `experiments._external.gemini_client`).

## Change description

### 배경

task-01 의 anthropic_client + task-02 의 c_caller 인자 위에서 Mixed Intelligence 실험 도구 작성. Stage 2C `exp_h4_recheck/run.py` 패턴 + Stage 2C 의 tattoo_history 결함 fix.

### Step 1 — 디렉토리 신규

```bash
mkdir -p experiments/exp11_mixed_intelligence/results
touch experiments/exp11_mixed_intelligence/__init__.py
touch experiments/exp11_mixed_intelligence/results/.gitkeep
```

### Step 2 — `experiments/exp11_mixed_intelligence/run.py` 신규

다음 구조:

```python
"""Exp11 Mixed Intelligence — Haiku Judge C 와 Gemma A/B 비교.

H10 후보 가설: 강한 Judge C 가 약한 Proposer/Critic 의 한계를 보완.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.run_helpers import (
    classify_trial_error, is_fatal_error, check_error_rate,
    build_result_meta, get_taskset_version, normalize_sampling_params,
)
from experiments.config import SAMPLING_PARAMS, MODEL_NAME, API_BASE_URL
from experiments.measure import score_answer_v3
from experiments.orchestrator import run_abc_chain
from experiments._external.gemini_client import (
    call_with_meter as call_gemini,
    DEFAULT_MODEL as GEMINI_FLASH_MODEL,
)


RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8


@dataclass
class FlashCostAccumulator:
    """trial 단위 비용 누적 (Gemini Flash)."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    errors: list[str] = field(default_factory=list)

    def add_meter(self, meter) -> None:
        """gemini_client.CallMeter 을 누적."""
        self.total_input_tokens += meter.input_tokens
        self.total_output_tokens += meter.output_tokens
        self.total_cost_usd += meter.cost_usd
        self.call_count += 1
        if meter.error:
            self.errors.append(meter.error)

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "call_count": self.call_count,
            "errors": self.errors,
        }


def _flash_c_caller(cost_acc: FlashCostAccumulator):
    """Gemini Flash 호출 wrapper — run_abc_chain 의 c_caller 시그니처 호환.

    c_caller signature: (messages: list[dict]) -> tuple[str, dict]
    cost_acc = trial 단위 누적 (closure binding).
    gemini_client.call_with_meter 가 OpenAI 스타일 messages 를 자동 변환 + system 분리.
    """
    def _caller(messages: list[dict]) -> tuple[str, dict]:
        meter = call_gemini(
            messages,
            model=GEMINI_FLASH_MODEL,
            response_mime_type=None,  # Judge 응답은 자유 형식 (text), JSON 강제 안 함
        )
        cost_acc.add_meter(meter)
        # call_model 호환 meta dict
        meta = {
            "model": meter.model,
            "duration_ms": meter.duration_ms,
            "input_tokens": meter.input_tokens,
            "output_tokens": meter.output_tokens,
            "cost_usd": meter.cost_usd,
            "error": meter.error,
        }
        return meter.raw_response, meta
    return _caller


def run_baseline_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma — Stage 2C abc 와 정합 + tattoo_history fix."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo_history = []  # ⭐ cycle-by-cycle (Stage 2C 결함 fix)
    try:
        # run_abc_chain 의 c_caller 미지정 → 기존 call_model 사용 (모두 Gemma)
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_baseline_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
        )
        actual_cycles = len(abc_logs)
        # ⭐ Stage 2C 결함 fix: cycle 별 tattoo snapshot 저장
        # abc_logs 에 cycle 별 tattoo 가 있다면 그대로, 부재면 abc_logs 의 schema 정찰 후 추출
        for log_entry in abc_logs:
            if hasattr(log_entry, "tattoo_snapshot"):
                tattoo_history.append(log_entry.tattoo_snapshot.to_dict() if hasattr(log_entry.tattoo_snapshot, "to_dict") else log_entry.tattoo_snapshot)
            elif hasattr(log_entry, "tattoo_out"):
                tattoo_history.append(log_entry.tattoo_out.to_dict() if hasattr(log_entry.tattoo_out, "to_dict") else log_entry.tattoo_out)
            elif isinstance(log_entry, dict) and "tattoo" in log_entry:
                tattoo_history.append(log_entry["tattoo"])
        if not tattoo_history and tattoo:
            # fallback: final tattoo 1 개만 (Stage 2C 와 동일 — 결함 disclosure)
            tattoo_history = [tattoo.to_dict()]

        if not final_answer:
            error = f"baseline_abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }


def run_mixed_flash_judge(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B = Gemma, C = Gemini 2.5 Flash. Mixed Intelligence."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo_history = []
    cost_acc = FlashCostAccumulator()
    try:
        flash_c = _flash_c_caller(cost_acc)
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_mixed_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            c_caller=flash_c,  # ⭐ Mixed: Gemini Flash C 주입
        )
        actual_cycles = len(abc_logs)
        # cycle-by-cycle tattoo (baseline 과 동일 추출 로직)
        for log_entry in abc_logs:
            if hasattr(log_entry, "tattoo_snapshot"):
                tattoo_history.append(log_entry.tattoo_snapshot.to_dict() if hasattr(log_entry.tattoo_snapshot, "to_dict") else log_entry.tattoo_snapshot)
            elif hasattr(log_entry, "tattoo_out"):
                tattoo_history.append(log_entry.tattoo_out.to_dict() if hasattr(log_entry.tattoo_out, "to_dict") else log_entry.tattoo_out)
            elif isinstance(log_entry, dict) and "tattoo" in log_entry:
                tattoo_history.append(log_entry["tattoo"])
        if not tattoo_history and tattoo:
            tattoo_history = [tattoo.to_dict()]

        if not final_answer:
            error = f"mixed_flash_judge: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
        "flash_cost": cost_acc.to_dict(),  # Mixed 한정 — cost-aware 측정
    }


CONDITION_DISPATCH = {
    "baseline_abc": run_baseline_abc,
    "mixed_flash_judge": run_mixed_flash_judge,
}


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = DEFAULT_TRIALS,
    conditions: tuple[str, ...] = ("baseline_abc", "mixed_haiku_judge"),
    max_cycles: int = DEFAULT_MAX_CYCLES,
    out_name: str | None = None,
) -> dict:
    """Stage 2C run_experiment 패턴 + Mixed condition 추가."""
    # ... (Stage 2C run.py 의 run_experiment 패턴 그대로 — checkpoint resume + condition loop +
    #     trial loop + healthcheck/abort + meta v1.0 + 저장)
    raise NotImplementedError(
        "Step 2 의 run_experiment 본체는 Stage 2C exp_h4_recheck/run.py 의 run_experiment 그대로 패턴 재사용. "
        "차이: CONDITION_DISPATCH 의 dispatch 로 baseline_abc / mixed_haiku_judge 호출. "
        "Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2A meta v1.0 모두 적용."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp11 Mixed Intelligence")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--conditions", nargs="+",
                        default=["baseline_abc", "mixed_flash_judge"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()
    # ... (Stage 2C 의 main 패턴 그대로)
    raise NotImplementedError("Step 2 의 main 은 Stage 2C exp_h4_recheck/run.py 의 main 그대로 — out_name 별 저장 + condition aggregate stdout")


if __name__ == "__main__":
    raise SystemExit(main())
```

**중요**: Step 2 의 코드 stub 의 `run_experiment` / `main` 은 Stage 2C `exp_h4_recheck/run.py` 의 동일 함수를 그대로 재사용하라는 의미. Sonnet 가 Stage 2C run.py 를 read 하여 패턴 그대로 적용 + CONDITION_DISPATCH 만 본 plan 의 baseline_abc / mixed_haiku_judge 로 변경.

### Step 3 — Stage 2C tattoo_history 결함 fix

baseline_abc + mixed_haiku_judge 모두 cycle-by-cycle 저장:
- `abc_logs` 의 각 entry 에서 tattoo snapshot 추출
- abc_logs 의 정확한 schema 는 `experiments/orchestrator.py` 의 `run_abc_chain` 정찰 결과로 (`abc_logs[i].tattoo_snapshot` 또는 `abc_logs[i].tattoo_out` 또는 다른 필드명)
- 추출 fail 시 fallback: final tattoo 1 개만 (Stage 2C 와 동일, 결함 disclosure)

→ Stage 2C 의 결함 fix 는 본 plan 의 신규 결과에 적용. Stage 2C 의 기존 결과 보존 (재처리 안 함).

### Step 4 — Judge prompt schema 강제 (Risk 1 차단)

Mixed condition 의 Haiku Judge prompt 가 reasoning 흡수 안 하도록 강제. `experiments/system_prompt.py` 의 `JUDGE_PROMPT` 가 이미 "verdict + brief justification 만, proposer 답안 재작성 금지" 류라면 그대로. 부재면 task-03 에서 추가 검증 (또는 후속 plan).

본 task 영역: `system_prompt.py` 변경 0. 기존 JUDGE_PROMPT 그대로 사용 (검증만).

```bash
.venv/Scripts/python -c "
from experiments.system_prompt import JUDGE_PROMPT
# Judge prompt 가 'verdict' / 'phase 전이' / 'accept|reject|retry' 류 키워드 포함 확인
assert 'verdict' in JUDGE_PROMPT.lower() or 'phase' in JUDGE_PROMPT.lower() or 'judge' in JUDGE_PROMPT.lower()
print(f'JUDGE_PROMPT length: {len(JUDGE_PROMPT)} chars')
"
```

검증 통과 시 진행. 부족 시 사용자 호출 (별도 plan 후보).

## Dependencies

- task-01 (anthropic_client + cost meter)
- task-02 (run_abc_chain c_caller 인자)
- 기존 `experiments/run_helpers.py` (Stage 2A) — read-only 사용
- 기존 `experiments/measure.py:score_answer_v3` — read-only 호출
- 기존 `experiments/system_prompt.py` — read-only 검증

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/exp11_mixed_intelligence/run.py
.venv/Scripts/python -m experiments.exp11_mixed_intelligence.run --help

# 2) condition dispatch 정상
.venv/Scripts/python -c "
from experiments.exp11_mixed_intelligence.run import CONDITION_DISPATCH
assert 'baseline_abc' in CONDITION_DISPATCH
assert 'mixed_flash_judge' in CONDITION_DISPATCH
print('verification 2 ok: 2 condition dispatch')
"

# 3) c_caller 주입 검증 (실제 호출 안 함)
.venv/Scripts/python -c "
from experiments.exp11_mixed_intelligence.run import _flash_c_caller, FlashCostAccumulator
acc = FlashCostAccumulator()
caller = _flash_c_caller(acc)
assert callable(caller)
print('verification 3 ok: flash c_caller closure')
"

# 4) tattoo_history cycle-by-cycle 저장 로직 — abc_logs schema 정찰
# (사용자 직접 dry-run 시 검증 — Step 5)

# 5) (사용자 직접) dry-run 1 task × 1 trial
# .\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
#   --conditions baseline_abc --trials 1 --max-cycles 8 `
#   --out-name dryrun_baseline.json
# 기대: cycles ≥ 1, tattoo_history len ≥ 2 (cycle-by-cycle 검증)
```

## Risks

- **Risk 1 — abc_logs 의 tattoo schema 정찰 실패**: log entry 가 `tattoo_snapshot` / `tattoo_out` / 다른 필드 — 정찰 후 패턴 결정. fallback 으로 final tattoo 1 개만 저장 (Stage 2C 와 동일, disclosure)
- **Risk 2 — Mixed condition 의 Haiku 비용 폭증**: dry-run 시 1 trial 비용 측정. 임계 ($1+ per trial) 시 사용자 호출
- **Risk 3 — System prompt 호환** (Gemma A/B → Haiku C): JUDGE_PROMPT 가 한국어 / 영어 어느 쪽이든 Haiku 가 처리. 단 prompt 길이 / format 차이로 Haiku 응답이 ABC schema 와 mismatch 가능. dry-run 시 검증
- **Risk 4 — `run_abc_chain` 의 abc_logs schema 가 본 plan 작성 시점과 다름**: orchestrator.py 변경 후 schema 변경 가능. dry-run 시 즉시 발견
- **Risk 5 — Stage 2C run.py 의 `run_experiment` 패턴 복사 실패**: Sonnet 이 Stage 2C 의 run.py 를 정확히 read 한 후 변형. 임의 단순화 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/anthropic_client.py` (task-01 영역)
- `experiments/orchestrator.py` (task-02 영역) — c_caller 인자 사용만
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — read-only
- `experiments/schema.py` / `system_prompt.py` — 변경 금지
- `experiments/config.py` (task-01 영역)
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- `experiments/exp_h4_recheck/run.py` (Stage 2C 영역) — read-only 패턴 참조만
- 결과 JSON
