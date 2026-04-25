---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: A
depends_on: []
---

# Task 04 — Tattoo 스키마 확장 (`Assertion.evidence_ref`)

## Changed files

- `experiments/schema.py`
  - `Assertion` dataclass (line 119-150): `evidence_ref: Optional[dict] = None` 필드 추가
  - `Assertion.to_dict()` 메서드: `evidence_ref`가 None 아닐 때만 직렬화
  - `Assertion.from_dict()` 클래스메서드: `evidence_ref=d.get("evidence_ref")` 로드

## Change description

### Step 1 — 배경

`conceptFramework.md § 5 "Tattoo–Evidence Tool 결합 쌍"`에서 정의된 결합 쌍의 Assertion 측 구현. Long-context 실험(Exp09)에서 assertion이 **어느 chunk의 어느 위치로부터 나왔는지** 추적하기 위함. 역할:

- A(Proposer)가 chunk를 읽고 assertion 생성 시 `evidence_ref` 첨부
- B(Critic)가 검증 시 원본 참조 가능
- Measure analyzer가 "evidence가 gold_evidence_chunks와 일치하는가"로 retrieval 품질 측정

### Step 2 — `evidence_ref` 스키마 정의 (dict)

```python
# Assertion.evidence_ref 필드 스키마 (dict | None):
{
    "chunk_id": int,          # 필수. chunker.Chunk.chunk_id
    "span": [int, int] | None # 선택. chunk 내 word 범위 [start, end)
}
```

**왜 dict인가**: `Assertion.from_dict()`와의 상호운용성을 위해 dataclass 중첩보다 dict가 단순. JSON 직렬화 시 그대로 보존.

**왜 Optional인가**: 기존 math/logic 실험에서는 `evidence_ref`가 의미 없음. 역호환을 위해 기본 `None`.

### Step 3 — `Assertion` 클래스 수정

**현재 구조** (line 119-150):

```python
@dataclass
class Assertion:
    """확정된 사실 하나. 문신의 핵심 단위."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    content: str = ""
    source_loop: int = 0
    confidence: float = 0.0
    status: AssertionStatus = AssertionStatus.ACTIVE
    invalidated_by: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "content": self.content,
            "source_loop": self.source_loop,
            "confidence": self.confidence,
            "status": self.status.value,
        }
        if self.invalidated_by:
            d["invalidated_by"] = self.invalidated_by
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Assertion:
        return cls(
            id=d["id"],
            content=d["content"],
            source_loop=d["source_loop"],
            confidence=d["confidence"],
            status=AssertionStatus(d["status"]),
            invalidated_by=d.get("invalidated_by"),
        )
```

**수정 후**:

```python
@dataclass
class Assertion:
    """확정된 사실 하나. 문신의 핵심 단위."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    content: str = ""
    source_loop: int = 0
    confidence: float = 0.0
    status: AssertionStatus = AssertionStatus.ACTIVE
    invalidated_by: Optional[str] = None
    # Long-context 실험용 — Optional, 기본 None. 기존 실험 역호환 보장.
    # dict 구조: {"chunk_id": int, "span": [int, int] | None}
    evidence_ref: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "content": self.content,
            "source_loop": self.source_loop,
            "confidence": self.confidence,
            "status": self.status.value,
        }
        if self.invalidated_by:
            d["invalidated_by"] = self.invalidated_by
        if self.evidence_ref is not None:
            d["evidence_ref"] = self.evidence_ref
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Assertion:
        return cls(
            id=d["id"],
            content=d["content"],
            source_loop=d["source_loop"],
            confidence=d["confidence"],
            status=AssertionStatus(d["status"]),
            invalidated_by=d.get("invalidated_by"),
            evidence_ref=d.get("evidence_ref"),
        )
```

### Step 4 — 기존 실험 회귀 없음 확인

- 기본값 `None`: `Assertion()` 호출이 깨지지 않음
- `to_dict()`: `if self.evidence_ref is not None` 분기로 None이면 key 자체가 생략 — 기존 JSON 구조 보존
- `from_dict()`: `d.get("evidence_ref")`로 없으면 None — 기존 저장된 결과 파일 파싱 문제 없음

### Step 5 — 다른 스키마 영향 여부 확인

`Tattoo` dataclass의 `assertions: list[Assertion]` 필드가 있다면, `Tattoo.to_dict()`/`from_dict()`가 assertion을 리스트 순회로 직렬화할 때 새 필드를 자동으로 상속. 즉 `Tattoo` 직접 수정 불필요.

### Step 6 — 간이 단위 테스트 (선택)

`experiments/schema.py`에 단위 테스트가 없다면 task 04에서도 신규 파일 만들지 않음 (scope boundary 준수). Verification에서 inline Python으로 round-trip 확인.

단위 테스트 파일이 있다면 해당 파일에 케이스 2~3개 추가.

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. evidence_ref 필드 존재 확인
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from dataclasses import fields
from schema import Assertion
field_names = {f.name for f in fields(Assertion)}
assert 'evidence_ref' in field_names, f'evidence_ref missing: {field_names}'
# 기본값이 None인지 확인
a = Assertion(content='test')
assert a.evidence_ref is None
print('OK: evidence_ref field present, default None')
"

# 2. to_dict/from_dict round-trip (evidence_ref 있을 때)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from schema import Assertion, AssertionStatus
a = Assertion(
    content='test claim',
    evidence_ref={'chunk_id': 3, 'span': [120, 180]},
)
d = a.to_dict()
assert 'evidence_ref' in d and d['evidence_ref']['chunk_id'] == 3
b = Assertion.from_dict(d)
assert b.evidence_ref == a.evidence_ref
print('OK round-trip with evidence_ref')
"

# 3. to_dict/from_dict 역호환 (evidence_ref 없을 때)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from schema import Assertion
a = Assertion(content='legacy', source_loop=1, confidence=0.8)
d = a.to_dict()
# evidence_ref가 None이면 key 자체가 없어야 함 (기존 JSON 스키마 보존)
assert 'evidence_ref' not in d, f'unexpected evidence_ref in: {d}'
b = Assertion.from_dict(d)
assert b.evidence_ref is None
print('OK backward compat')
"

# 4. 기존 실험 import 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import schema, orchestrator, run_experiment, measure, system_prompt
print('all imports OK')
"

# 5. 기존 결과 JSON 로드 (evidence_ref 없는 파일 파싱)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys, json
sys.path.insert(0, 'experiments')
from schema import Assertion
# 최근 Exp08b 결과 파일 일부만 로드 테스트 (실제 파일 필요)
import glob
files = sorted(glob.glob('experiments/results/exp08b_tool_use_refined_*.json'))
if files:
    with open(files[-1]) as f:
        data = json.load(f)
    print(f'legacy result loaded: {files[-1].rsplit(chr(47),1)[-1]}')
else:
    print('no exp08b result to test (skip)')
"
# 기대: 로드 성공 또는 "skip"
```

## Risks

- **Tattoo/orchestrator에서 Assertion 사용 방식**: `run_abc_chain`은 `assertion["content"]`, `assertion["confidence"]` 같은 dict 인덱싱을 사용할 수 있음. `evidence_ref` 추가로 기존 코드에 영향 없음 — key 추가는 하위 호환.
- **JSON 결과 파일 schema migration**: 기존 결과 파일을 다시 읽어 Assertion으로 역직렬화할 일이 있다면, `from_dict`의 `d.get("evidence_ref")`가 None 반환 → 안전.
- **데이터 검증 부재**: evidence_ref dict의 schema가 `{"chunk_id": int, "span": [int, int] | None}`임을 런타임에 강제하지 않음. 잘못된 형태 주입 시 사용자(Task 05 이후) 책임. Exp09 범위에서는 orchestrator가 올바른 형태로만 주입하도록 제어.
- **`dataclass` 기본값 순서**: Python dataclass는 기본값 있는 필드 뒤에 기본값 없는 필드가 오면 에러. 기존 필드가 모두 기본값 있으므로 안전.

## Scope boundary

**Task 04에서 절대 수정 금지**:
- `Assertion` 외 모든 `schema.py` 내 다른 dataclass (`Tattoo`, `Phase`, `HandoffA2B`, `HandoffB2C`, `ABCCycleLog`, `AssertionStatus` 등) — 건드리지 않음
- `experiments/orchestrator.py`, `run_experiment.py`, `measure.py`, `system_prompt.py`
- `experiments/tools/` 내 모든 파일 (Task 02, 03 영역)
- `experiments/tasks/` (Task 01 영역)

**허용 범위**: `experiments/schema.py`의 `Assertion` dataclass 및 그 `to_dict`/`from_dict` 메서드에만 최소 추가.
