"""제멘토 실험 설정."""

from pathlib import Path

# ── 경로 ──
PROJECT_ROOT = Path(__file__).parent.parent
EXPERIMENTS_DIR = Path(__file__).parent
TASKS_DIR = EXPERIMENTS_DIR / "tasks"
# RESULTS_DIR removed in experiments-task-07 rev — 각 expXX/run.py 가 자체 RESULTS_DIR 정의 사용
LOGS_DIR = EXPERIMENTS_DIR / "logs"

# ── 모델 ──
MODEL_NAME = "gemma4-e4b"
API_BASE_URL = "http://yongseek.iptime.org:8005"
API_CHAT_URL = f"{API_BASE_URL}/v1/chat/completions"
API_TIMEOUT = 600

# ── 문신 제약 ──
ASSERTION_SOFT_CAP = 8
ASSERTION_HARD_CAP = 10
TOKEN_BUDGET_TATTOO = 2048  # 문신에 할당할 최대 토큰 수 (실험 1에서 조정)
CONFIDENCE_FLOOR = 0.3  # 이 이하면 긴급 VERIFY 전환
CONFIDENCE_PROMOTION_MIN = 0.5  # assertion 승격 최소 confidence
CONFIDENCE_CAP_NO_TOOL = 0.7  # 외부 도구 없이 도출된 주장의 confidence 상한

# ── 실험 ──
DEFAULT_REPEAT = 5  # 각 조건 반복 횟수 (3→5: 통계적 신뢰도 향상)
MAX_LOOPS = 15  # 루프 상한 (12→15: 어려운 태스크 조기 종료 방지)


# ── Sampling (LLM 추론 결정성 통제) ──
# 본 dict 가 모든 LLM 호출의 sampling source-of-truth.
# orchestrator.call_model() 와 _external/lmstudio_client.call_with_meter() 가 참조한다.
# 값이 None 이면 payload 에 미포함 (LM Studio 기본 동작).
# 결과 동일성 보장 — 기존 14 실험 재현성 유지를 위해 temperature/max_tokens 변경 금지.
SAMPLING_PARAMS: dict = {
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": None,    # 미지정 — LM Studio 기본값 사용
    "seed": None,     # 비결정성 유지 — Exp10 본격 실행 전 별도 결정
}
