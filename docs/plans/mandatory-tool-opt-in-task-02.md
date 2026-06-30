---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: mandatory-tool-opt-in
parallel_group: B
depends_on: [01]
---

# Task 02 — 회귀 게이트 + opt-in 동작 검증

## Changed files

- `experiments/tests/test_mandatory_optin.py` (신규) — 정적 동치 + 가드 단위 테스트.
- (검증 산출, 선택) `experiments/exp15_context_router/results/exp18_optin_verify_gemma4_e4b.json` — tunnel A/B 소규모 확인 결과.

> 신규 1 (+ 선택 검증 결과 1).

## Change description

### 배경
공유 코드 변경의 최우선 불변식: **`mandatory_tool_prompt=False` (기본) 시 거동이 변경 전과 동일**. 정적 테스트로 못박고, 선택적으로 tunnel A/B 로 mandatory=True 가 드라이버 주입 방식과 동일 효과인지 확인.

### Step 1 — 정적 동치 테스트 (필수)
`build_prompt` 또는 주입 로직 단위로, mandatory=False 시 prompt 가 원본과 동일, True 시 `MANDATORY_TOOL_RULES` 가 정확히 1회 append 됨을 검증. run_abc_chain 전체를 돌리지 않고 주입 함수/분기만 테스트 (LLM 호출 없음).

```python
# test_mandatory_optin.py (개념)
from system_prompt import MANDATORY_TOOL_RULES
# 주입 로직을 작은 helper 로 분리했다면 그것을 직접 테스트;
# 아니면 run_abc_chain 의 주입 분기를 모사한 assert:
def _inject(prompt, mandatory): return f"{prompt}{MANDATORY_TOOL_RULES}" if mandatory else prompt
base = "PROMPT"
assert _inject(base, False) == base                      # False = byte-identical
assert _inject(base, True) == base + MANDATORY_TOOL_RULES # True = exactly one append
assert _inject(base, True).count("MANDATORY TOOL-USE RULES") == 1  # 멱등 (이중 주입 없음)
```

### Step 2 — 정적 테스트 통과 확인
`tools.test_*` 패턴으로 unittest 등록 (기존 `experiments/tests/test_static.py` 구조 참고).

### Step 3 — (선택) tunnel A/B 동치 확인
cloud 터널 (지인 서버 e4b) 로, 1-needle 큰 로그 1개 task 에 대해:
- (i) 드라이버가 prompt 에 직접 주입 (기존 run_v16b 방식)
- (ii) `run_abc_chain(mandatory_tool_prompt=True)` (새 파라미터)
두 경로의 결과가 동등(둘 다 정답 산출)함을 n=3 정도로 확인. **검증 실행은 cloud 라 Architect 가능** (로컬 LLM 로딩 아님).

## Dependencies
- Task 01 완료 (파라미터 + 상수).
- 기존 파일: `experiments/tests/test_static.py` (구조 참고, read-only).
- (Step 3) SSH 터널 + 지인 서버 e4b.

## Verification

```bash
# 1. 정적 테스트 통과
cd experiments && D:/privateProject/gemento/.venv/Scripts/python.exe -m unittest tests.test_mandatory_optin -v
```

```bash
# 2. 기본 False 불변식 — 기존 정적 테스트 회귀 없음
cd experiments && D:/privateProject/gemento/.venv/Scripts/python.exe -m unittest tests.test_static -v
```

```bash
# 3. (선택, Step 3) tunnel A/B — 사용자/Architect 가 cloud 로 실행
#   결과: 드라이버-주입 vs 파라미터-주입 동일 정답률
echo "tunnel A/B verify — run only if tunnel up"
```

## Risks
1. **주입 로직이 inline 이라 단위 테스트 어려움** — Task 01 에서 주입을 작은 helper 로 뽑으면 테스트 용이. 단 helper 추출도 shared 코드 변경이니 최소화.
2. **정적 테스트가 실제 run_abc_chain 경로를 안 탐** — 정적은 주입 분기만 검증. 실제 경로 동치는 Step 3 tunnel A/B (선택) 또는 사용자 회귀 실행으로 보완.
3. **tunnel 불안정** — 끊기면 Step 3 skip (정적만으로도 불변식 충분). 선택 단계라 blocking 아님.

## Scope boundary
**수정 금지**: orchestrator 의 다른 경로, 결과 JSON (Step 3 산출 제외), 기존 test_static.py 의 기존 케이스. 새 테스트 파일만 추가.
