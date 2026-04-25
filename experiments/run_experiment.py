"""제멘토 실험 실행기.

Usage:
    python run_experiment.py baseline          # 실험 0: 기준선
    python run_experiment.py assertion-cap     # 실험 1: assertion 상한
    python run_experiment.py multiloop         # 실험 2: 다단계 루프
    python run_experiment.py error-propagation # 실험 3: 오류 전파
    python run_experiment.py cross-validation  # 실험 3.5: 교차 검증 게이트
    python run_experiment.py abc-pipeline      # 실험 4: A-B-C 직렬 파이프라인
    python run_experiment.py prompt-enhance    # 실험 5a: 프롬프트 강화
    python run_experiment.py handoff-protocol  # 실험 4.5/5b: Handoff Protocol
    python run_experiment.py solo-budget       # 실험 6: Solo 단일 에이전트 (ABC 시너지 비교군)
    python run_experiment.py tool-separation   # (보류) 도구 분리
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# experiments/ 디렉토리를 기준으로 import
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    RESULTS_DIR, DEFAULT_REPEAT, MODEL_NAME,
    API_CHAT_URL, API_TIMEOUT,
)
from schema import Tattoo, Phase, create_initial_tattoo
from orchestrator import run_chain, call_model, LoopLog, run_abc_chain, ABCCycleLog


def load_tasks() -> list[dict]:
    """태스크셋을 로드한다."""
    tasks_path = Path(__file__).parent / "tasks" / "taskset.json"
    with open(tasks_path) as f:
        return json.load(f)["tasks"]


def save_result(experiment_name: str, result: dict) -> Path:
    """실험 결과를 저장한다."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


# ── 실험 0: Baseline ──

def run_baseline():
    """문신 없이 단일 추론으로 답변 품질을 측정한다."""
    tasks = load_tasks()
    results = []

    for task in tasks:
        print(f"\n[Baseline] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial in range(DEFAULT_REPEAT):
            messages = [
                {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer."},
                {"role": "user", "content": task["prompt"]},
            ]
            start = time.time()
            try:
                raw = call_model(messages)
                error = None
            except Exception as e:
                raw = ""
                error = str(e)
            duration_ms = int((time.time() - start) * 1000)

            task_results.append({
                "trial": trial + 1,
                "response": raw,
                "duration_ms": duration_ms,
                "error": error,
            })
            print(f"  Trial {trial + 1}: {duration_ms}ms")

        results.append({
            "task_id": task["id"],
            "objective": task["objective"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

    save_result("exp00_baseline", {"experiment": "baseline", "model": MODEL_NAME, "results": results})


# ── 실험 1: Assertion Cap ──

def run_assertion_cap():
    """assertion 수 변화에 따른 추론 품질 변곡점을 탐색한다."""
    tasks = load_tasks()
    cap_values = [2, 4, 6, 8, 10, 12]
    results = []

    for task in tasks:
        if not task.get("prefab_assertions"):
            continue
        print(f"\n[Assertion Cap] Task: {task['id']}")

        for cap in cap_values:
            assertions_to_use = task["prefab_assertions"][:cap]
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                # 사전 제작된 assertion이 포함된 문신 생성
                # objective에 실제 문제(prompt)를 포함하여 모델이 맥락을 알 수 있게 한다
                tattoo = create_initial_tattoo(
                    task_id=f"{task['id']}_cap{cap}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    termination="답변이 완성되면 수렴",
                )
                tattoo.phase = Phase.SYNTHESIZE
                tattoo.next_directive = "주어진 assertions를 종합하여 최종 답을 작성하라."
                for i, a_text in enumerate(assertions_to_use):
                    tattoo.add_assertion(content=a_text, confidence=0.8, source_loop=i + 1)
                tattoo.finalize_integrity()

                from orchestrator import run_loop
                _, log = run_loop(tattoo, cap)
                task_results.append({
                    "trial": trial + 1,
                    "cap": cap,
                    "response": log.raw_response,
                    "parsed": log.parsed_response,
                    "duration_ms": log.duration_ms,
                    "error": log.error,
                })
                print(f"  Cap {cap}, Trial {trial + 1}: {log.duration_ms}ms")

            results.append({
                "task_id": task["id"],
                "cap": cap,
                "trials": task_results,
            })

        # 태스크 완료 후 중간 저장 (크래시 방어)
        save_result("exp01_assertion_cap_partial", {"experiment": "assertion_cap", "model": MODEL_NAME, "results": results})

    save_result("exp01_assertion_cap", {"experiment": "assertion_cap", "model": MODEL_NAME, "results": results})


# ── 실험 2: Multi-loop Quality ──

def run_multiloop():
    """다단계 루프에서 품질이 누적되는지 검증한다."""
    tasks = load_tasks()
    loop_counts = [1, 2, 4, 8]
    results = []

    for task in tasks:
        print(f"\n[Multiloop] Task: {task['id']}")

        for max_loops in loop_counts:
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                final_tattoo, logs, final_answer = run_chain(
                    task_id=f"{task['id']}_loops{max_loops}_t{trial}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    constraints=task.get("constraints", []),
                    max_loops=max_loops,
                )

                task_results.append({
                    "trial": trial + 1,
                    "max_loops": max_loops,
                    "actual_loops": len(logs),
                    "final_phase": final_tattoo.phase.value,
                    "final_confidence": final_tattoo.confidence,
                    "total_assertions": len(final_tattoo.active_assertions),
                    "final_answer": final_answer,
                    "loop_details": [
                        {
                            "loop": l.loop_index,
                            "phase": l.tattoo_out["state"]["phase"],
                            "assertions": len([
                                a for a in l.tattoo_out["state"]["assertions"]
                                if a["status"] == "active"
                            ]),
                            "confidence": l.tattoo_out["integrity"]["confidence"],
                            "duration_ms": l.duration_ms,
                            "error": l.error,
                        }
                        for l in logs
                    ],
                })
                print(f"  Loops={max_loops}, Trial {trial + 1}: "
                      f"phase={final_tattoo.phase.value}, "
                      f"conf={final_tattoo.confidence:.2f}, "
                      f"assertions={len(final_tattoo.active_assertions)}")

            results.append({
                "task_id": task["id"],
                "max_loops": max_loops,
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

    save_result("exp02_multiloop", {"experiment": "multiloop", "model": MODEL_NAME, "results": results})


# ── 실험 3: Error Propagation ──

def run_error_propagation():
    """결함 주입 후 오류 전파를 측정한다."""
    tasks = load_tasks()
    results = []

    # logic 태스크 제외 (JSON 파싱 불안정)
    skip_tasks = {"logic-01", "logic-02"}
    for task in tasks:
        if task["id"] in skip_tasks:
            print(f"\n[Error Propagation] Task: {task['id']} — SKIPPED (unstable JSON)")
            continue
        print(f"\n[Error Propagation] Task: {task['id']}")
        fault_types = task.get("fault_injections", [])
        if not fault_types:
            continue

        for fault in fault_types:
            task_results = []
            for trial in range(DEFAULT_REPEAT):
                # 정상 체인 2루프 실행
                tattoo, pre_logs, _ = run_chain(
                    task_id=f"{task['id']}_fault_{fault['type']}_t{trial}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    max_loops=fault.get("inject_at_loop", 2),
                )

                # 결함 주입
                if fault["type"] == "corrupt_content" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.content = fault.get("corrupted_value", "CORRUPTED: incorrect fact")
                elif fault["type"] == "inflate_confidence" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.confidence = 0.95
                elif fault["type"] == "contradiction":
                    tattoo.add_assertion(
                        content=fault.get("contradicting_assertion", "This contradicts everything."),
                        confidence=0.85,
                        source_loop=tattoo.loop_index,
                    )

                tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

                # 결함 주입 후 추가 루프 실행 (run_chain과 동일한 로직)
                from orchestrator import run_loop, decide_phase_transition, PHASE_DIRECTIVES
                post_logs: list[LoopLog] = []
                loops_in_current_phase = 0
                current_phase = tattoo.phase
                for i in range(tattoo.loop_index + 1, tattoo.loop_index + 7):
                    tattoo.next_directive = PHASE_DIRECTIVES.get(tattoo.phase, "Continue reasoning.")
                    tattoo, log, _ = run_loop(tattoo, i)
                    post_logs.append(log)

                    if tattoo.phase == current_phase:
                        loops_in_current_phase += 1
                    else:
                        current_phase = tattoo.phase
                        loops_in_current_phase = 1

                    if tattoo.phase == Phase.CONVERGED:
                        break

                    new_phase = decide_phase_transition(tattoo, loops_in_current_phase)
                    if new_phase and new_phase != tattoo.phase:
                        tattoo.phase = new_phase
                        loops_in_current_phase = 0
                        current_phase = new_phase
                        if new_phase == Phase.CONVERGED:
                            break

                task_results.append({
                    "trial": trial + 1,
                    "fault_type": fault["type"],
                    "inject_at_loop": fault.get("inject_at_loop", 2),
                    "post_injection_loops": len(post_logs),
                    "final_confidence": tattoo.confidence,
                    "final_phase": tattoo.phase.value,
                    "confidence_trajectory": [
                        l.tattoo_out["integrity"]["confidence"] for l in post_logs
                    ],
                })

            results.append({
                "task_id": task["id"],
                "fault": fault,
                "trials": task_results,
            })

    save_result("exp03_error_propagation", {"experiment": "error_propagation", "model": MODEL_NAME, "results": results})


# ── 실험 3.5: Cross-Validation Gate ──

def run_cross_validation():
    """B(비판자)가 A의 결함 assertion을 교차 검증으로 감지할 수 있는지 테스트한다.

    게이트 실험: A-B-C 파이프라인 구축 전에 B 단독 능력을 확인.
    """
    from system_prompt import build_critic_prompt
    from orchestrator import call_ollama, extract_json_from_response

    tasks = load_tasks()
    skip_tasks = {"logic-01", "logic-02"}
    results = []

    for task in tasks:
        if task["id"] in skip_tasks:
            print(f"\n[Cross-Validation] Task: {task['id']} — SKIPPED")
            continue
        if not task.get("fault_injections"):
            continue
        if not task.get("prefab_assertions"):
            continue

        print(f"\n[Cross-Validation] Task: {task['id']}")

        for fault in task["fault_injections"]:
            # prefab assertion 목록에서 결함 주입
            clean_assertions = []
            for i, a_text in enumerate(task["prefab_assertions"][:8]):
                clean_assertions.append({
                    "id": f"a{i+1:02d}",
                    "content": a_text,
                    "confidence": 0.8,
                })

            # 결함 주입할 대상 assertion 결정
            corrupted_assertions = [dict(a) for a in clean_assertions]
            corrupted_id = None

            if fault["type"] == "corrupt_content":
                # 첫 번째 관련 assertion을 오염
                target_idx = min(2, len(corrupted_assertions) - 1)
                corrupted_id = corrupted_assertions[target_idx]["id"]
                corrupted_assertions[target_idx]["content"] = fault["corrupted_value"]
            elif fault["type"] == "inflate_confidence":
                target_idx = 0
                corrupted_id = corrupted_assertions[target_idx]["id"]
                corrupted_assertions[target_idx]["confidence"] = 0.99
            elif fault["type"] == "contradiction":
                corrupted_id = "a_injected"
                corrupted_assertions.append({
                    "id": corrupted_id,
                    "content": fault["contradicting_assertion"],
                    "confidence": 0.85,
                })

            task_results = []
            for trial in range(DEFAULT_REPEAT):
                print(f"  Fault={fault['type']}, Trial {trial + 1}: ", end="", flush=True)

                # B(비판자)에게 오염된 assertions 전달
                messages = build_critic_prompt(
                    problem=task["prompt"],
                    assertions=corrupted_assertions,
                )

                start = time.time()
                error = None
                parsed = None
                raw = ""
                detected = False

                for attempt in range(2):
                    try:
                        raw = call_ollama(messages)
                        parsed = extract_json_from_response(raw)
                    except Exception as e:
                        raw = ""
                        error = str(e)
                    if parsed:
                        error = None
                        break
                    if attempt == 0:
                        print("↻ ", end="", flush=True)

                duration_ms = int((time.time() - start) * 1000)

                # 감지 여부 판정
                if parsed and "judgments" in parsed:
                    for j in parsed["judgments"]:
                        if j.get("assertion_id") == corrupted_id:
                            if j.get("status") in ("suspect", "invalid"):
                                detected = True
                                break

                status_str = "✓ DETECTED" if detected else "✗ missed"
                print(f"{duration_ms}ms — {status_str}")

                task_results.append({
                    "trial": trial + 1,
                    "fault_type": fault["type"],
                    "corrupted_id": corrupted_id,
                    "detected": detected,
                    "judgments": parsed.get("judgments") if parsed else None,
                    "raw_response": raw[:500],
                    "duration_ms": duration_ms,
                    "error": error,
                })

            results.append({
                "task_id": task["id"],
                "fault": fault,
                "corrupted_id": corrupted_id,
                "trials": task_results,
            })

    # 요약 출력
    total = sum(len(r["trials"]) for r in results)
    detected_count = sum(
        1 for r in results for t in r["trials"] if t["detected"]
    )
    print(f"\n{'═' * 50}")
    print(f"  교차 검증 감지율: {detected_count}/{total} = {detected_count/total:.1%}" if total else "  No data")
    print(f"{'═' * 50}")

    save_result("exp035_cross_validation", {
        "experiment": "cross_validation",
        "model": MODEL_NAME,
        "results": results,
    })


# ── 실험 4: A-B-C Pipeline ──

def run_abc_pipeline():
    """A-B-C 직렬 구조로 전체 파이프라인을 검증한다.

    비교군: 실험 2 v2 (Python 오케스트레이터)와 동일한 태스크를 A-B-C로 실행.
    """
    tasks = load_tasks()
    skip_tasks = {"logic-01", "logic-02"}
    results = []

    for task in tasks:
        if task["id"] in skip_tasks:
            print(f"\n[ABC Pipeline] Task: {task['id']} — SKIPPED")
            continue

        print(f"\n[ABC Pipeline] Task: {task['id']} — {task['objective']}")

        task_results = []
        for trial in range(DEFAULT_REPEAT):
            print(f"\n  --- Trial {trial + 1} ---")

            final_tattoo, cycle_logs, final_answer = run_abc_chain(
                task_id=f"{task['id']}_abc_t{trial}",
                objective=task["objective"],
                prompt=task["prompt"],
                constraints=task.get("constraints", []),
            )

            # 사이클별 상세 기록
            cycle_details = []
            for cl in cycle_logs:
                detail = {
                    "cycle": cl.cycle,
                    "phase": cl.phase,
                    "a_duration_ms": cl.a_log.duration_ms,
                    "a_error": cl.a_log.error,
                    "b_duration_ms": cl.b_duration_ms,
                    "b_error": cl.b_error,
                    "b_invalid_count": 0,
                    "b_suspect_count": 0,
                    "c_duration_ms": cl.c_duration_ms,
                    "c_error": cl.c_error,
                    "c_converged": None,
                    "phase_transition": cl.phase_transition,
                }
                if cl.b_judgments and "judgments" in cl.b_judgments:
                    detail["b_invalid_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "invalid"
                    )
                    detail["b_suspect_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "suspect"
                    )
                if cl.c_decision:
                    detail["c_converged"] = cl.c_decision.get("converged")
                cycle_details.append(detail)

            task_results.append({
                "trial": trial + 1,
                "total_cycles": len(cycle_logs),
                "final_phase": final_tattoo.phase.value,
                "final_confidence": final_tattoo.confidence,
                "total_assertions": len(final_tattoo.active_assertions),
                "final_answer": str(final_answer) if final_answer else None,
                "phase_transitions": [
                    cl.phase_transition for cl in cycle_logs
                    if cl.phase_transition
                ],
                "c_decisions": [
                    cl.c_decision.get("converged") if cl.c_decision else None
                    for cl in cycle_logs
                ],
                "cycle_details": cycle_details,
            })

            status = "✓" if final_tattoo.phase == Phase.CONVERGED else "✗"
            print(f"  {status} Trial {trial + 1}: "
                  f"phase={final_tattoo.phase.value}, "
                  f"cycles={len(cycle_logs)}, "
                  f"assertions={len(final_tattoo.active_assertions)}, "
                  f"answer={'yes' if final_answer else 'no'}")

        results.append({
            "task_id": task["id"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

    # 요약 출력
    total = sum(len(r["trials"]) for r in results)
    converged = sum(
        1 for r in results for t in r["trials"]
        if t["final_phase"] == "CONVERGED"
    )
    print(f"\n{'═' * 50}")
    print(f"  수렴률: {converged}/{total} = {converged/total:.1%}" if total else "  No data")
    print(f"{'═' * 50}")

    save_result("exp04_abc_pipeline", {
        "experiment": "abc_pipeline",
        "model": MODEL_NAME,
        "results": results,
    })


# ── 실험 5a: Prompt Enhancement ──

def run_prompt_enhance():
    """A의 프롬프트 강화 후 A-B-C 파이프라인을 재실행한다.

    변경점: SYNTHESIZE/VERIFY의 next_directive에서 final_answer 필수 제출 강조.
    비교군: 실험 4 (동일 태스크, 동일 구조, 프롬프트만 변경).
    통과 기준: synthesis-02 정답률 33%→66%+, 전체 정답률 ≥ 90%, 퇴행 없음.
    """
    from experiment_logger import ExperimentLogger

    logger = ExperimentLogger("exp05a_prompt_enhance")
    tasks = load_tasks()
    skip_tasks = {"logic-01", "logic-02"}
    results = []

    for task in tasks:
        if task["id"] in skip_tasks:
            logger._write(f"\n[Prompt Enhance] Task: {task['id']} — SKIPPED")
            continue

        task_results = []
        for trial in range(DEFAULT_REPEAT):
            logger.task_start(task["id"], trial + 1, task["objective"])

            final_tattoo, cycle_logs, final_answer = run_abc_chain(
                task_id=f"{task['id']}_5a_t{trial}",
                objective=task["objective"],
                prompt=task["prompt"],
                constraints=task.get("constraints", []),
                logger=logger,
            )

            # 사이클별 상세 기록
            cycle_details = []
            for cl in cycle_logs:
                detail = {
                    "cycle": cl.cycle,
                    "phase": cl.phase,
                    "a_duration_ms": cl.a_log.duration_ms,
                    "a_error": cl.a_log.error,
                    "b_duration_ms": cl.b_duration_ms,
                    "b_error": cl.b_error,
                    "b_invalid_count": 0,
                    "b_suspect_count": 0,
                    "c_duration_ms": cl.c_duration_ms,
                    "c_error": cl.c_error,
                    "c_converged": None,
                    "phase_transition": cl.phase_transition,
                }
                if cl.b_judgments and "judgments" in cl.b_judgments:
                    detail["b_invalid_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "invalid"
                    )
                    detail["b_suspect_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "suspect"
                    )
                if cl.c_decision:
                    detail["c_converged"] = cl.c_decision.get("converged")
                cycle_details.append(detail)

            task_results.append({
                "trial": trial + 1,
                "total_cycles": len(cycle_logs),
                "final_phase": final_tattoo.phase.value,
                "final_confidence": final_tattoo.confidence,
                "total_assertions": len(final_tattoo.active_assertions),
                "final_answer": str(final_answer) if final_answer else None,
                "phase_transitions": [
                    cl.phase_transition for cl in cycle_logs
                    if cl.phase_transition
                ],
                "c_decisions": [
                    cl.c_decision.get("converged") if cl.c_decision else None
                    for cl in cycle_logs
                ],
                "cycle_details": cycle_details,
            })

            logger.trial_result(
                task["id"], trial + 1,
                final_tattoo.phase == Phase.CONVERGED,
                str(final_answer) if final_answer else None,
                len(cycle_logs),
            )

        results.append({
            "task_id": task["id"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

    # 요약
    total = sum(len(r["trials"]) for r in results)
    converged = sum(
        1 for r in results for t in r["trials"]
        if t["final_phase"] == "CONVERGED"
    )
    with_answer = sum(
        1 for r in results for t in r["trials"]
        if t["final_answer"] is not None
    )
    logger.summary(total, converged, with_answer)
    logger.close()

    save_result("exp05a_prompt_enhance", {
        "experiment": "prompt_enhance",
        "model": MODEL_NAME,
        "change": "SYNTHESIZE/VERIFY directive에 final_answer 필수 제출 강조",
        "baseline": "exp04_abc_pipeline (정답률 83.3%, synthesis-02 1/3)",
        "results": results,
    })


# ── (보류) Tool Loop Separation ──

def run_tool_separation():
    """도구 호출을 같은 루프/분리 루프에서 처리할 때의 품질 차이를 측정한다."""
    tasks = load_tasks()
    results = []

    for task in tasks:
        if not task.get("requires_tool"):
            continue
        print(f"\n[Tool Separation] Task: {task['id']}")

        # 이 실험은 실험 2 이후에 구현을 완성한다.
        # 현재는 구조만 잡아둔다.
        results.append({
            "task_id": task["id"],
            "status": "not_implemented_yet",
            "note": "실험 2 결과 이후 구현 예정",
        })

    save_result("exp04_tool_separation", {"experiment": "tool_separation", "model": MODEL_NAME, "results": results})


# ── 실험 4.5: Handoff Protocol ──

def run_handoff_protocol():
    """실험 4.5: A-B-C 직렬 파이프라인 + Handoff Protocol 메트릭 측정.
    
    체크포인트 기능 포함: 중간 실패 시 이어서 시작 가능.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_handoff_protocol.json"
    
    # 이어하기 시도
    results = []
    finished_task_ids = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results = partial_data.get("results", [])
                finished_task_ids = {r["task_id"] for r in results}
                print(f"  → Resuming from checkpoint: {len(finished_task_ids)} tasks already finished.")
        except Exception:
            print("  ⚠ Failed to load checkpoint, starting from scratch.")

    for task in tasks:
        if task["id"] in finished_task_ids:
            continue

        print(f"\n[Handoff Protocol] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial_idx in range(DEFAULT_REPEAT):
            print(f"  Trial {trial_idx + 1}/{DEFAULT_REPEAT}...")
            
            tattoo, abc_logs, final_answer = run_abc_chain(
                task_id=task["id"],
                objective=task["objective"],
                prompt=task["prompt"],
                constraints=task.get("constraints"),
                termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            )

            cycle_details = []
            for cl in abc_logs:
                detail = {
                    "cycle": cl.cycle,
                    "phase": cl.phase,
                    "tattoo_in": cl.a_log.tattoo_in,
                    "tattoo_out": cl.a_log.tattoo_out,
                    "b_handoff": cl.b_judgments.get("handoff_b2c") if cl.b_judgments else None,
                    "c_reject": cl.c_decision.get("reject_memo") if cl.c_decision else None,
                }
                cycle_details.append(detail)

            task_results.append({
                "trial": trial_idx + 1,
                "final_answer": str(final_answer) if final_answer else None,
                "total_cycles": len(abc_logs),
                "final_phase": tattoo.phase.value,
                "total_assertions": len(tattoo.assertions),
                "cycle_details": cycle_details,
            })

        results.append({
            "task_id": task["id"],
            "objective": task["objective"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

        # 태스크 완료 시마다 중간 저장
        with open(partial_path, "w") as f:
            json.dump({
                "experiment": "handoff_protocol",
                "model": MODEL_NAME,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Task {task['id']} saved to checkpoint.")

    # 최종 결과 저장
    final_path = save_result("exp045_handoff_protocol", {
        "experiment": "handoff_protocol",
        "model": MODEL_NAME,
        "results": results
    })
    
    # 완료 후 체크포인트 파일 삭제 (깔끔하게 정리)
    if partial_path.exists():
        partial_path.unlink()
        print(f"  → Checkpoint cleared.")


# ── 실험 6: Solo Budget (ABC 시너지 비교군) ──

SOLO_MAX_LOOPS = 21  # ABC 평균 7.2 사이클 × 3 에이전트 ≈ 21 Ollama 호출

def run_solo_budget():
    """실험 6: 단일 E4B 에이전트가 ABC와 동일한 총 compute 예산을 받았을 때의 성능.

    비교군: exp 5b (handoff-protocol, 9 태스크 × 5 trials, 88.9%, 평균 21.6 Ollama calls)
    목적: A-B-C 역할 분리가 단순히 반복 횟수 증가로 환원 가능한지 판별.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_solo_budget.json"

    results = []
    finished_task_ids = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results = partial_data.get("results", [])
                finished_task_ids = {r["task_id"] for r in results}
                print(f"  → Resuming: {len(finished_task_ids)} tasks already finished.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting fresh.")

    for task in tasks:
        if task["id"] in finished_task_ids:
            continue

        print(f"\n[Solo Budget] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial_idx in range(DEFAULT_REPEAT):
            print(f"  Trial {trial_idx + 1}/{DEFAULT_REPEAT}...")

            final_tattoo, logs, final_answer = run_chain(
                task_id=f"{task['id']}_solo_t{trial_idx}",
                objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                constraints=task.get("constraints", []),
                max_loops=SOLO_MAX_LOOPS,
            )

            loop_details = []
            for l in logs:
                loop_details.append({
                    "loop": l.loop_index,
                    "phase": l.tattoo_out["state"]["phase"],
                    "assertions": len([
                        a for a in l.tattoo_out["state"]["assertions"]
                        if a["status"] == "active"
                    ]),
                    "confidence": l.tattoo_out["integrity"]["confidence"],
                    "duration_ms": l.duration_ms,
                    "error": l.error,
                })

            task_results.append({
                "trial": trial_idx + 1,
                "max_loops": SOLO_MAX_LOOPS,
                "actual_loops": len(logs),
                "final_phase": final_tattoo.phase.value,
                "final_confidence": final_tattoo.confidence,
                "total_assertions": len(final_tattoo.active_assertions),
                "final_answer": str(final_answer) if final_answer else None,
                "loop_details": loop_details,
            })

            status = "✓" if final_tattoo.phase == Phase.CONVERGED else "✗"
            print(f"    {status} loops={len(logs)} phase={final_tattoo.phase.value} "
                  f"answer={'yes' if final_answer else 'no'}")

        results.append({
            "task_id": task["id"],
            "objective": task["objective"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

        # 체크포인트 저장
        with open(partial_path, "w") as f:
            json.dump({
                "experiment": "solo_budget",
                "model": MODEL_NAME,
                "max_loops": SOLO_MAX_LOOPS,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Task {task['id']} saved to checkpoint.")

    save_result("exp06_solo_budget", {
        "experiment": "solo_budget",
        "model": MODEL_NAME,
        "max_loops": SOLO_MAX_LOOPS,
        "baseline_comparison": "exp045_handoff_protocol (5b): 9 tasks × 5 trials, 88.9% accuracy, ~21.6 Ollama calls/trial",
        "results": results
    })

    if partial_path.exists():
        partial_path.unlink()


# ── 실험 7: Loop Saturation + Loop-Phase 프롬프트 ──

LOOP_SAT_REPEAT = 3

CONDITIONS = [
    {"max_cycles": 8,  "use_phase_prompt": False, "label": "baseline_8"},
    {"max_cycles": 11, "use_phase_prompt": False, "label": "baseline_11"},
    {"max_cycles": 15, "use_phase_prompt": False, "label": "baseline_15"},
    {"max_cycles": 20, "use_phase_prompt": False, "label": "baseline_20"},
    {"max_cycles": 8,  "use_phase_prompt": True,  "label": "phase_8"},
    {"max_cycles": 11, "use_phase_prompt": True,  "label": "phase_11"},
    {"max_cycles": 15, "use_phase_prompt": True,  "label": "phase_15"},
    {"max_cycles": 20, "use_phase_prompt": True,  "label": "phase_20"},
]


def run_loop_saturation():
    """실험 7: Loop Saturation + Loop-Phase 프롬프트.

    2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20).
    12 태스크 × 3 trials × 8 조건 = 288 runs.
    체크포인트 기능 포함: 중단 후 재실행 시 자동으로 이어서 시작.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_loop_saturation.json"

    results_by_condition: dict[str, list] = {}
    finished: set[tuple[str, str]] = set()

    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results_by_condition = partial_data.get("results_by_condition", {})
                for label, task_list in results_by_condition.items():
                    for tr in task_list:
                        finished.add((label, tr["task_id"]))
            print(f"  → Resuming from checkpoint: {len(finished)} (condition, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting from scratch.")

    for cond in CONDITIONS:
        label = cond["label"]

        for task in tasks:
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Loop Saturation] Condition={label} | Task={task['id']}")
            task_results = []

            for trial_idx in range(LOOP_SAT_REPEAT):
                print(f"  Trial {trial_idx + 1}/{LOOP_SAT_REPEAT}...")

                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=cond["max_cycles"],
                    use_phase_prompt=cond["use_phase_prompt"],
                )

                cycle_details = []
                for cl in abc_logs:
                    cycle_details.append({
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "phase_transition": cl.phase_transition,
                        "b_error": cl.b_error,
                        "c_error": cl.c_error,
                    })

                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": cond["max_cycles"],
                    "use_phase_prompt": cond["use_phase_prompt"],
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": str(final_answer) if final_answer else None,
                    "cycle_details": cycle_details,
                })

                status = "✓" if tattoo.phase.value == "CONVERGED" else "✗"
                print(f"    {status} cycles={len(abc_logs)} phase={tattoo.phase.value} "
                      f"answer={'yes' if final_answer else 'no'}")

            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

            # 태스크 완료 시마다 체크포인트 저장
            with open(partial_path, "w") as f:
                json.dump({
                    "experiment": "loop_saturation",
                    "model": MODEL_NAME,
                    "conditions": CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved checkpoint: {label}/{task['id']}")

    save_result("exp07_loop_saturation", {
        "experiment": "loop_saturation",
        "model": MODEL_NAME,
        "conditions": CONDITIONS,
        "results_by_condition": results_by_condition,
    })

    if partial_path.exists():
        partial_path.unlink()
        print("  → Checkpoint cleared.")


TOOL_USE_REPEAT = 5
TOOL_USE_MAX_CYCLES = 15
TOOL_USE_PHASE_PROMPT = True
TOOL_USE_CONDITIONS = [
    {"label": "baseline_phase15", "use_tools": False},
    {"label": "tooluse_phase15", "use_tools": True},
]
TOOL_USE_TASK_IDS = ["math-01", "math-02", "math-03", "math-04"]

# ── Exp08b (tool-use refined) ──
TOOL_USE_REFINED_REPEAT = TOOL_USE_REPEAT
TOOL_USE_REFINED_MAX_CYCLES = TOOL_USE_MAX_CYCLES
TOOL_USE_REFINED_PHASE_PROMPT = TOOL_USE_PHASE_PROMPT
TOOL_USE_REFINED_CONDITIONS = [
    {"label": "baseline_refined", "use_tools": False},
    {"label": "tooluse_refined", "use_tools": True},
]
TOOL_USE_REFINED_TASK_IDS = TOOL_USE_TASK_IDS


def run_tool_use():
    """실험 8: Math Tool-Use.

    A(제안자)에게 calculator/solve_linear_system/linprog 도구를 제공하고
    math 태스크의 정답률 향상을 측정한다. B·C는 도구 없음.
    2 arm(baseline/tooluse) × 4 math 태스크 × 5 trial = 40 runs.
    체크포인트 기능(partial_tool_use.json)으로 중단 후 재실행 가능.
    """
    all_tasks = load_tasks()
    tasks = [t for t in all_tasks if t["id"] in TOOL_USE_TASK_IDS]
    assert len(tasks) == len(TOOL_USE_TASK_IDS), f"missing tasks: expected {TOOL_USE_TASK_IDS}"

    partial_path = RESULTS_DIR / "partial_tool_use.json"
    results_by_condition: dict[str, list] = {}
    finished: set[tuple[str, str]] = set()

    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results_by_condition = partial_data.get("results_by_condition", {})
                for label, task_list in results_by_condition.items():
                    for tr in task_list:
                        finished.add((label, tr["task_id"]))
            print(f"  → Resuming from checkpoint: {len(finished)} (condition, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting from scratch.")

    for cond in TOOL_USE_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]

        for task in tasks:
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Tool Use] arm={label} | task={task['id']}")
            task_results = []

            for trial_idx in range(TOOL_USE_REPEAT):
                print(f"  Trial {trial_idx + 1}/{TOOL_USE_REPEAT}...")

                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=TOOL_USE_MAX_CYCLES,
                    use_phase_prompt=TOOL_USE_PHASE_PROMPT,
                    use_tools=use_tools,
                )

                cycle_details = []
                total_tool_calls = 0
                tool_errors = 0
                for cl in abc_logs:
                    cd = {
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "a_error": cl.a_log.error if cl.a_log else None,
                        "b_error": cl.b_error,
                        "c_error": cl.c_error,
                    }
                    tc_list = getattr(cl, "tool_calls", []) or []
                    total_tool_calls += len(tc_list)
                    tool_errors += sum(1 for tc in tc_list if tc.get("error"))
                    cd["tool_calls"] = tc_list
                    cycle_details.append(cd)

                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": TOOL_USE_MAX_CYCLES,
                    "use_phase_prompt": TOOL_USE_PHASE_PROMPT,
                    "use_tools": use_tools,
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": final_answer,
                    "total_tool_calls": total_tool_calls,
                    "tool_errors": tool_errors,
                    "cycle_details": cycle_details,
                })

            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "tool_use",
                    "model": MODEL_NAME,
                    "conditions": TOOL_USE_CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, ensure_ascii=False, indent=2)

    result = {
        "experiment": "tool_use",
        "model": MODEL_NAME,
        "conditions": TOOL_USE_CONDITIONS,
        "task_ids": TOOL_USE_TASK_IDS,
        "repeat": TOOL_USE_REPEAT,
        "results_by_condition": results_by_condition,
    }
    save_result("exp08_tool_use", result)

    if partial_path.exists():
        partial_path.unlink()


def run_tool_use_refined():
    """실험 8b: Tool-Use Refinement.

    Exp08의 2개 부작용(calculator ^ 혼동, tool neglect)을 프롬프트·에러
    메시지 개선으로 보완한 재측정. 태스크·파라미터는 Exp08과 동일.
    """
    all_tasks = load_tasks()
    tasks = [t for t in all_tasks if t["id"] in TOOL_USE_REFINED_TASK_IDS]
    assert len(tasks) == len(TOOL_USE_REFINED_TASK_IDS), \
        f"missing tasks: expected {TOOL_USE_REFINED_TASK_IDS}"

    partial_path = RESULTS_DIR / "partial_tool_use_refined.json"
    results_by_condition: dict[str, list] = {}
    finished: set[tuple[str, str]] = set()

    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results_by_condition = partial_data.get("results_by_condition", {})
                for label, task_list in results_by_condition.items():
                    for tr in task_list:
                        finished.add((label, tr["task_id"]))
            print(f"  → Resuming from checkpoint: {len(finished)} (condition, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting from scratch.")

    for cond in TOOL_USE_REFINED_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]

        for task in tasks:
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Tool Use Refined] arm={label} | task={task['id']}")
            task_results = []

            for trial_idx in range(TOOL_USE_REFINED_REPEAT):
                print(f"  Trial {trial_idx + 1}/{TOOL_USE_REFINED_REPEAT}...")

                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=TOOL_USE_REFINED_MAX_CYCLES,
                    use_phase_prompt=TOOL_USE_REFINED_PHASE_PROMPT,
                    use_tools=use_tools,
                )

                cycle_details = []
                total_tool_calls = 0
                tool_errors = 0
                for cl in abc_logs:
                    cd = {
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "a_error": cl.a_log.error if cl.a_log else None,
                        "b_error": cl.b_error,
                        "c_error": cl.c_error,
                    }
                    tc_list = getattr(cl, "tool_calls", []) or []
                    total_tool_calls += len(tc_list)
                    tool_errors += sum(1 for tc in tc_list if tc.get("error"))
                    cd["tool_calls"] = tc_list
                    cycle_details.append(cd)

                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": TOOL_USE_REFINED_MAX_CYCLES,
                    "use_phase_prompt": TOOL_USE_REFINED_PHASE_PROMPT,
                    "use_tools": use_tools,
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": final_answer,
                    "total_tool_calls": total_tool_calls,
                    "tool_errors": tool_errors,
                    "cycle_details": cycle_details,
                })

            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "tool_use",
                    "model": MODEL_NAME,
                    "conditions": TOOL_USE_REFINED_CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, ensure_ascii=False, indent=2)

    result = {
        "experiment": "tool_use",
        "variant": "refined",
        "model": MODEL_NAME,
        "conditions": TOOL_USE_REFINED_CONDITIONS,
        "task_ids": TOOL_USE_REFINED_TASK_IDS,
        "repeat": TOOL_USE_REFINED_REPEAT,
        "results_by_condition": results_by_condition,
    }
    save_result("exp08b_tool_use_refined", result)

    if partial_path.exists():
        partial_path.unlink()


# ── CLI ──

# ── Exp09 (longctx) ──
_TASKS_DIR = Path(__file__).parent / "tasks"

LONGCTX_TRIALS = 3  # MVP
LONGCTX_TASKSET_PATH = _TASKS_DIR / "longctx_taskset.json"
LONGCTX_ARMS = [
    {"label": "solo_dump",    "description": "document 전체를 A에 단일 투입"},
    {"label": "rag_baseline", "description": "BM25 top-K chunks만 A에 투입"},
    {"label": "abc_tattoo",   "description": "ABC + Tattoo + chunk iteration"},
]
LONGCTX_CHUNK_SIZE = 500
LONGCTX_CHUNK_OVERLAP = 50
LONGCTX_RAG_TOP_K = 5
LONGCTX_MAX_FINAL_CYCLES = 5


def _extract_answer(raw: str) -> str | None:
    """solo_dump / rag_baseline 용 final_answer 파싱."""
    from orchestrator import extract_json_from_response
    parsed = extract_json_from_response(raw)
    if parsed and isinstance(parsed, dict):
        return parsed.get("final_answer")
    return raw.strip() if raw else None


def _run_longctx_trial(arm: dict, task: dict, trial_idx: int) -> dict:
    """단일 arm × task × trial 실행. arm label에 따라 분기."""
    from tools.chunker import chunk_document
    from tools.bm25_tool import bm25_retrieve
    from orchestrator import run_abc_chunked, call_model, log_detail

    label = arm["label"]
    question = task["question"]
    document = task["_document"]
    
    log_detail(f"  > Trial {trial_idx + 1} START | Arm: {label}")

    if label == "solo_dump":
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the provided document."},
            {"role": "user", "content": f"## Document\n\n{document}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        final_answer = None
        error = None
        try:
            raw, _ = call_model(messages)
            parsed = extract_json_from_response(raw)
            final_answer = _extract_answer(raw)
            log_detail(f"    Solo-dump Response: {raw[:500]}...")
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ Solo-dump Error: {error}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "doc_word_count": len(document.split()),
        }

    elif label == "rag_baseline":
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        top = bm25_retrieve(question, chunks, top_k=LONGCTX_RAG_TOP_K)
        top_text = "\n\n---\n\n".join(f"[chunk {c['chunk_id']}]\n{c['content']}" for c in top)
        log_detail(f"    RAG retrieved chunk IDs: {[c['chunk_id'] for c in top]}")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the retrieved chunks."},
            {"role": "user", "content": f"## Retrieved Chunks\n\n{top_text}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        final_answer = None
        error = None
        try:
            raw, _ = call_model(messages)
            final_answer = _extract_answer(raw)
            log_detail(f"    RAG Response: {raw[:500]}...")
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ RAG Error: {error}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "retrieved_chunk_ids": [c["chunk_id"] for c in top],
            "top_k": LONGCTX_RAG_TOP_K,
        }

    elif label == "abc_tattoo":
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        tattoo = None
        logs = []
        final_answer = None
        evidence_refs_used = []
        error = None
        try:
            tattoo, logs, final_answer = run_abc_chunked(
                task_id=f"{task['id']}_t{trial_idx}",
                question=question,
                chunks=chunks,
                max_final_cycles=LONGCTX_MAX_FINAL_CYCLES,
            )
            evidence_refs_used = [
                a.evidence_ref for a in tattoo.active_assertions if a.evidence_ref
            ]
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ ABC Error: {error}")
        
        log_detail(f"    ABC Result: Answer={str(final_answer)[:100]}..., Evidence Count={len(evidence_refs_used)}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "num_chunks": len(chunks),
            "num_assertions": len(tattoo.active_assertions) if tattoo else 0,
            "evidence_refs_used": evidence_refs_used,
        }

    raise ValueError(f"unknown arm label: {label}")


def run_longctx():
    """실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG).

    3 arm × 10 tasks × 3 trials = 90 runs. 체크포인트 지원.
    """
    print(f"Taskset: {LONGCTX_TASKSET_PATH}")

    with open(LONGCTX_TASKSET_PATH) as f:
        d = json.load(f)
    tasks = d["tasks"]

    # document 본문 로드 (_document 키에 저장, 결과 JSON에는 저장 안 함)
    for t in tasks:
        doc_path = _TASKS_DIR / t["document_path"]
        with open(doc_path) as f:
            t["_document"] = f.read()

    partial_path = RESULTS_DIR / "partial_longctx.json"
    results: dict = {"solo_dump": [], "rag_baseline": [], "abc_tattoo": []}
    finished: set[tuple[str, str]] = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial = json.load(f)
                results = partial.get("results_by_arm", results)
                for arm_label, task_list in results.items():
                    for tr in task_list:
                        finished.add((arm_label, tr["task_id"]))
            print(f"  → Resuming: {len(finished)} (arm, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")

    for arm in LONGCTX_ARMS:
        label = arm["label"]
        for task in tasks:
            if (label, task["id"]) in finished:
                print(f"  [skip] arm={label} task={task['id']}")
                continue
            print(f"\n[LongCtx] arm={label} | task={task['id']} ({task['size_class']}, {task['hop_type']})")
            task_results = []
            for trial in range(LONGCTX_TRIALS):
                print(f"  Trial {trial + 1}/{LONGCTX_TRIALS}...")
                trial_result = _run_longctx_trial(arm, task, trial)
                task_results.append(trial_result)

            results.setdefault(label, []).append({
                "task_id": task["id"],
                "size_class": task["size_class"],
                "hop_type": task["hop_type"],
                "expected_answer": task["expected_answer"],
                "scoring_keywords": task.get("scoring_keywords", []),
                "gold_evidence_chunks": task.get("gold_evidence_chunks", []),
                "trials": task_results,
            })
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "longctx",
                    "model": MODEL_NAME,
                    "arms": LONGCTX_ARMS,
                    "results_by_arm": results,
                }, f, ensure_ascii=False, indent=2)

    final = {
        "experiment": "longctx",
        "model": MODEL_NAME,
        "arms": LONGCTX_ARMS,
        "trials_per_task": LONGCTX_TRIALS,
        "chunk_size": LONGCTX_CHUNK_SIZE,
        "chunk_overlap": LONGCTX_CHUNK_OVERLAP,
        "rag_top_k": LONGCTX_RAG_TOP_K,
        "results_by_arm": results,
    }
    save_result("exp09_longctx", final)
    if partial_path.exists():
        partial_path.unlink()


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
    "tool-separation": run_tool_separation,
    "loop-saturation": run_loop_saturation,
    "tool-use": run_tool_use,
    "tool-use-refined": run_tool_use_refined,
    "longctx": run_longctx,
}


def main():
    parser = argparse.ArgumentParser(description="제멘토 실험 실행기")
    parser.add_argument("experiment", choices=EXPERIMENTS.keys(), help="실행할 실험")
    args = parser.parse_args()

    print(f"═══ 제멘토 실험: {args.experiment} ═══")
    print(f"모델: {MODEL_NAME}")
    print()

    EXPERIMENTS[args.experiment]()
    print("\n═══ 완료 ═══")


if __name__ == "__main__":
    main()
