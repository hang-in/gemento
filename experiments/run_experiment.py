"""제멘토 실험 실행기 — dispatcher (experiments-task-07).

각 실험의 본문은 experiments/expXX_*/run.py 에 분리되어 있으며,
이 파일은 CLI dispatcher 역할만 수행한다.

Usage:
    python run_experiment.py baseline           # 실험 0: 기준선
    python run_experiment.py assertion-cap      # 실험 1: assertion 상한
    python run_experiment.py multiloop          # 실험 2: 다단계 루프 (H1)
    python run_experiment.py error-propagation  # 실험 3: 오류 전파 (H2)
    python run_experiment.py cross-validation   # 실험 3.5: 교차 검증 게이트
    python run_experiment.py abc-pipeline       # 실험 4: A-B-C 직렬 파이프라인
    python run_experiment.py prompt-enhance     # 실험 5a: 프롬프트 강화
    python run_experiment.py handoff-protocol   # 실험 4.5/5b: Handoff Protocol
    python run_experiment.py solo-budget        # 실험 6: Solo (ABC 시너지 비교군)
    python run_experiment.py loop-saturation    # 실험 7: Loop Saturation + Loop-Phase
    python run_experiment.py tool-use           # 실험 8: Math Tool-Use (H7)
    python run_experiment.py tool-use-refined   # 실험 8b: Tool-Use Refinement (H8)
    python run_experiment.py longctx            # 실험 9: Long-Context Stress Test (H9)

(deprecated) tool-separation — _archived/exp04_tool_separation_deprecated/ 로 격리됨.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# experiments/ 디렉토리를 import 경로에 추가 (각 실험 모듈이 공용 모듈을 import 하기 위함)
sys.path.insert(0, str(Path(__file__).parent))

from config import MODEL_NAME

# 분리된 실험 모듈 import (experiments-task-03~06)
from exp00_baseline.run import run as run_baseline
from exp01_assertion_cap.run import run as run_assertion_cap
from exp02_multiloop.run import run as run_multiloop
from exp03_error_propagation.run import run as run_error_propagation
from exp035_cross_validation.run import run as run_cross_validation
from exp04_abc_pipeline.run import run as run_abc_pipeline
from exp05a_prompt_enhance.run import run as run_prompt_enhance
from exp045_handoff_protocol.run import run as run_handoff_protocol
from exp06_solo_budget.run import run as run_solo_budget
from exp07_loop_saturation.run import run as run_loop_saturation
from exp08_tool_use.run import run as run_tool_use
from exp08b_tool_use_refined.run import run as run_tool_use_refined
from exp09_longctx.run import run as run_longctx


EXPERIMENTS = {
    "baseline": run_baseline,
    "assertion-cap": run_assertion_cap,
    "multiloop": run_multiloop,
    "error-propagation": run_error_propagation,
    "cross-validation": run_cross_validation,
    "abc-pipeline": run_abc_pipeline,
    "prompt-enhance": run_prompt_enhance,
    "handoff-protocol": run_handoff_protocol,
    "solo-budget": run_solo_budget,
    "loop-saturation": run_loop_saturation,
    "tool-use": run_tool_use,
    "tool-use-refined": run_tool_use_refined,
    "longctx": run_longctx,
}
# tool-separation: removed in experiments-task-05 (deprecated, see _archived/exp04_tool_separation_deprecated/)


def main():
    parser = argparse.ArgumentParser(description="제멘토 실험 실행기")
    parser.add_argument("experiment", choices=list(EXPERIMENTS.keys()), help="실행할 실험")
    args = parser.parse_args()

    print(f"═══ 제멘토 실험: {args.experiment} ═══")
    print(f"모델: {MODEL_NAME}")
    print()

    EXPERIMENTS[args.experiment]()
    print("\n═══ 완료 ═══")


if __name__ == "__main__":
    main()
