"""제멘토 실험 설정."""

from pathlib import Path

# ── 경로 ──
PROJECT_ROOT = Path(__file__).parent.parent
EXPERIMENTS_DIR = Path(__file__).parent
TASKS_DIR = EXPERIMENTS_DIR / "tasks"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
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
