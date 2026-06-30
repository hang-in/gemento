---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: exp21-facet-aggregate-tool
parallel_group: B
depends_on: [01]
---

# Task 02 — facet 단위 테스트 + 회귀 게이트

## Changed files

- `experiments/tests/test_facet_tool.py` (신규) — `aggregate_context` 정확성 + 글로벌 도구 표면 불변 + caller default 동치.

> 신규 1, 수정 0.

## Change description

### 배경
facet 도구는 opt-in 이어야 한다(parent 결정 2). 본 테스트가 ① 집계 정확성, ② 글로벌 `CONTEXT_TOOL_*` byte-identical, ③ caller default 경로 동치를 회귀 게이트로 고정한다. 기존 테스트(`test_static` 등)와 동일한 위치/스타일(`experiments/tests/`).

### Step 1 — fixture 기반 집계 정확성 테스트
`unittest.TestCase` 스타일(repo 표준 `test_static.py` 와 동일). Redis 에 알려진 분포를 SET 하고 검증:
- top IP: `1.1.1.1`×3 > `2.2.2.2`×2 > `3.3.3.3`×1 → `aggregate_context(..., group_by="from (\\d+\\.\\d+\\.\\d+\\.\\d+)")` 의 `top[0]=={'value':'1.1.1.1','count':3}`, `total_matches==6`, `unique_groups==3`.
- systemd unit: `foo.service` fail×4 vs `bar.service`×1 → group_by `"(\\S+\\.service)"` top[0] 검증.
- group_by 생략: `total_matches` + `sample`(≤5) 반환, `truncated==False`.
- 미존재 handle → `{"error": ...}`.
- 잘못된 group_by regex(`"("`) → `{"error": ...}` (예외 아님).
- 각 테스트 후 `r.delete(key)` 정리.

### Step 2 — 회귀 게이트: 글로벌 도구 표면 불변
```python
def test_global_tool_surface_unchanged():
    from tools import CONTEXT_TOOL_SCHEMAS, CONTEXT_TOOL_FUNCTIONS
    assert [s["function"]["name"] for s in CONTEXT_TOOL_SCHEMAS] == ["read_context", "grep_context"]
    assert list(CONTEXT_TOOL_FUNCTIONS.keys()) == ["read_context", "grep_context"]

def test_facet_is_separate():
    from tools import FACET_TOOL_SCHEMAS, FACET_TOOL_FUNCTIONS
    assert [s["function"]["name"] for s in FACET_TOOL_SCHEMAS] == ["aggregate_context"]
    assert list(FACET_TOOL_FUNCTIONS.keys()) == ["aggregate_context"]
```

### Step 3 — caller default 동치(구성 레벨)
`make_ollama_native_caller(..., extra_tool_schemas=None, extra_tool_fns=None)` 가 예외 없이 caller 를 만들고, extra 주입 caller 도 구성됨을 확인(네트워크 호출 없이 closure 구성만). 가능하면 `inspect.signature` 로 신규 파라미터 존재 + default None 확인:
```python
def test_caller_optin_signature_default_none():
    import inspect
    from exp15_context_router.native_ollama_caller import make_ollama_native_caller
    sig = inspect.signature(make_ollama_native_caller)
    assert sig.parameters["extra_tool_schemas"].default is None
    assert sig.parameters["extra_tool_fns"].default is None
```

## Dependencies

- task-01 완료(facet 함수/스키마 + caller 파라미터 존재).
- 외부: `redis`(로컬 6379 가동 — 기존 테스트와 동일 전제). **테스트는 `unittest.TestCase` 스타일**(repo 표준 = `test_static.py`; pytest 미설치). 실행은 `python -m unittest`.

## Verification

```bash
# 1) syntax
cd experiments && python -c "import ast; ast.parse(open('tests/test_facet_tool.py',encoding='utf-8').read()); print('test syntax OK')"

# 2) facet 테스트 단독 (unittest)
cd experiments && python -m unittest tests.test_facet_tool -v

# 3) 전체 회귀 — 기존 테스트가 facet 추가로 깨지지 않는지
cd experiments && python -m unittest discover -s tests -q
```

## Risks

1. 로컬 Redis 미가동 → 집계 테스트 ERROR. 대응: 기존 테스트와 동일 전제(6379), 미가동 시 skip 마커 또는 사용자에 안내.
2. 기존 `test_static` 의 결과-인벤토리 카운트가 신규 결과 JSON 으로 흔들릴 수 있음 — 본 task 는 결과 JSON 미생성이므로 무관(드라이버 task-03 이후 주의).
3. caller import 경로(`exp15_context_router.native_ollama_caller`)가 sys.path 의존 → 테스트가 `experiments/` 를 cwd 로 실행해야 함. 대응: Verification 의 `cd experiments` 준수, 필요시 conftest 의 path 설정 확인.

## Scope boundary

- **수정 금지**: `context_tools.py`(task-01 영역), `orchestrator.py`, 기존 테스트 파일, 드라이버.
- 본 task 는 신규 테스트 파일만.
