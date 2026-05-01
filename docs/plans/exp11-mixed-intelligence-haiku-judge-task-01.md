---
type: plan-task
status: todo
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: A
depends_on: []
---

# Task 01 — `anthropic_client.py` 신규 + cost meter

## Changed files

- `experiments/anthropic_client.py` — **신규**. Claude Haiku 4.5 호출 + 토큰 카운트 + 비용 계산
- `experiments/config.py` — **수정 (추가만)**. `ANTHROPIC_API_KEY` env + Haiku model id + 가격 dict

신규 1, 수정 1 (추가만).

## Change description

### 배경

Mixed Intelligence 의 Judge C 호출은 Claude Haiku 4.5 (`claude-haiku-4-5-20251001`). 기존 LM Studio (Gemma) 호출과 다른 client 필요. cost-aware 측정 위한 토큰 카운트 + 비용 계산 helper.

### Step 1 — Anthropic SDK 또는 httpx 결정

**결정**: `anthropic` Python SDK 사용 권장 (설치: `pip install anthropic`). httpx 직접도 가능하지만 SDK 의 retry / streaming / typing 이점.

```bash
.venv/Scripts/pip install anthropic
```

`anthropic` 패키지가 이미 설치되어 있는지 확인:

```bash
.venv/Scripts/python -c "import anthropic; print(anthropic.__version__)"
```

미설치 시 위 pip 명령 실행 후 다음 Step.

### Step 2 — Haiku 4.5 가격 정확한 확인

Anthropic 공식 페이지 (https://www.anthropic.com/pricing) 또는 SDK doc 에서 `claude-haiku-4-5-20251001` 의 정확한 가격 확인:

- input: ? USD / 1M tokens
- output: ? USD / 1M tokens

**Architect default 추정** (정확한 값 task-01 진행 시 갱신):
- input: $1 / MTok
- output: $5 / MTok

본 가격은 `experiments/config.py` 의 `HAIKU_PRICING` dict 에 명시 (Step 4).

### Step 3 — `experiments/anthropic_client.py` 신규

```python
"""Anthropic Claude Haiku 4.5 client + cost meter.

Mixed Intelligence (Exp11) 의 Judge C 호출용. 기존 LM Studio (Gemma) 와 별개.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from anthropic import Anthropic
from experiments.config import HAIKU_MODEL_ID, HAIKU_PRICING


@dataclass
class HaikuCallResult:
    """Haiku 호출 결과 + 비용 메타."""

    text: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    error: str | None = None


def _calc_cost(input_tokens: int, output_tokens: int) -> float:
    """Haiku 토큰 → USD."""
    return (
        input_tokens * HAIKU_PRICING["input_per_mtok"] / 1_000_000
        + output_tokens * HAIKU_PRICING["output_per_mtok"] / 1_000_000
    )


def call_haiku(
    messages: list[dict],
    *,
    system: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    timeout_s: int = 60,
) -> HaikuCallResult:
    """Claude Haiku 4.5 호출.

    messages: [{"role": "user|assistant", "content": "..."}, ...]
    system: optional system prompt
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return HaikuCallResult(
            text="", input_tokens=0, output_tokens=0,
            duration_ms=0, cost_usd=0.0,
            error="ANTHROPIC_API_KEY 환경 변수 미설정",
        )

    client = Anthropic(api_key=api_key, timeout=timeout_s)
    start = time.time()
    try:
        kwargs = {
            "model": HAIKU_MODEL_ID,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system is not None:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
        return HaikuCallResult(
            text=text,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=_calc_cost(resp.usage.input_tokens, resp.usage.output_tokens),
        )
    except Exception as e:
        return HaikuCallResult(
            text="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0,
            error=str(e),
        )


@dataclass
class HaikuCostAccumulator:
    """trial 단위 비용 누적."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    errors: list[str] = field(default_factory=list)

    def add(self, result: HaikuCallResult) -> None:
        self.total_input_tokens += result.input_tokens
        self.total_output_tokens += result.output_tokens
        self.total_cost_usd += result.cost_usd
        self.call_count += 1
        if result.error:
            self.errors.append(result.error)

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "call_count": self.call_count,
            "errors": self.errors,
        }
```

### Step 4 — `experiments/config.py` 추가

config.py 의 끝에 추가:

```python
# ── Anthropic (Exp11 Mixed Intelligence) ──
HAIKU_MODEL_ID = "claude-haiku-4-5-20251001"
HAIKU_PRICING = {
    # 2026-05-02 시점 추정 — task-01 진행 시 정확한 가격으로 갱신
    "input_per_mtok": 1.0,   # USD per 1M input tokens
    "output_per_mtok": 5.0,  # USD per 1M output tokens
}
```

**중요**: Step 2 의 정확한 가격 확인 후 `HAIKU_PRICING` 갱신. disclosure 주석 명시.

## Dependencies

- 패키지: `anthropic` (Step 1 에서 설치 검증)
- 다른 subtask: 없음 (parallel_group A, 첫 노드)
- 환경 변수: `ANTHROPIC_API_KEY` (사용자 직접 설정 — Task 04 시점)

## Verification

```bash
# 1) anthropic SDK 설치 확인
.venv/Scripts/python -c "import anthropic; print(f'anthropic SDK: {anthropic.__version__}')"

# 2) 신규 client import + 시그니처
.venv/Scripts/python -c "
from experiments.anthropic_client import call_haiku, HaikuCallResult, HaikuCostAccumulator, _calc_cost
from experiments.config import HAIKU_MODEL_ID, HAIKU_PRICING
assert HAIKU_MODEL_ID == 'claude-haiku-4-5-20251001'
assert 'input_per_mtok' in HAIKU_PRICING
print('verification 1 ok: import + config')
"

# 3) cost 계산 단위 테스트
.venv/Scripts/python -c "
from experiments.anthropic_client import _calc_cost
# 1000 input + 500 output: 1000/1M × 1 + 500/1M × 5 = 0.001 + 0.0025 = 0.0035
cost = _calc_cost(1000, 500)
assert abs(cost - 0.0035) < 1e-6, f'cost: {cost}'
print(f'verification 2 ok: cost calc ({cost})')
"

# 4) API key 부재 시 graceful fallback (실제 호출 안 함)
.venv/Scripts/python -c "
import os
os.environ.pop('ANTHROPIC_API_KEY', None)
from experiments.anthropic_client import call_haiku
result = call_haiku([{'role':'user','content':'test'}])
assert result.error and 'ANTHROPIC_API_KEY' in result.error
print('verification 3 ok: graceful fallback')
"

# 5) (사용자 직접) 실제 API 호출 dry-run — 본 plan 의 Task 04 직전에 사용자 실행
# .\.venv\Scripts\python.exe -c "
# import os
# # ANTHROPIC_API_KEY 사전 설정 가정
# from experiments.anthropic_client import call_haiku
# r = call_haiku([{'role':'user','content':'Say OK in one word.'}], max_tokens=10)
# print(f'  text={r.text!r} tokens={r.input_tokens}/{r.output_tokens} cost=${r.cost_usd:.6f} err={r.error}')
# "
```

5 명령 (1-4 본 task 검증, 5 는 Task 04 직전 사용자).

## Risks

- **Risk 1 — anthropic SDK 미설치**: `pip install anthropic` 가 실패 시 (네트워크 / 권한) 사용자 호출. fallback: httpx 직접 (별도 turn)
- **Risk 2 — Haiku 가격 정확성**: Step 2 의 사용자 / Architect 확인 의무. 추정 가격으로 진행 시 비용 산정 ±2x 범위 변동 가능 — disclosure 명시
- **Risk 3 — API key 없이 import 시도**: graceful fallback (Step 3 의 코드 — error message 반환). import 자체는 환경 변수 확인 안 함
- **Risk 4 — Anthropic SDK 의 message format 변경**: SDK 의 `messages.create` API 안정 — 단 향후 SDK 업그레이드 시 호환성 검증

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/measure.py` / `score_answer_v0/v2/v3` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A 영역)
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- 결과 JSON / 분석 helper / docs/reference 의 다른 reference
