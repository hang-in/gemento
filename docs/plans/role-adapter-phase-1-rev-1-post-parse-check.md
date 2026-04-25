---
type: plan
status: abandoned
updated_at: 2026-04-25
slug: role-adapter-phase-1-rev-1-post-parse-check
parent_plan: role-adapter-phase-1-a-b-c
version: 1
---

# Role Adapter 리팩토링 (Phase 1) rev.1 — 회귀 게이트 + `_post_parse_check` 동작 동치 복원

## Description

`role-adapter-phase-1-a-b-c` (rev.0) 리뷰 실패의 두 근본 원인을 해결하는 후속 plan이다. rev.0의 Task 01~04는 이미 main에 머지된 상태이고, 본 plan은 **그 결과물 위에 patch만 추가**한다.

### 실패 원인 A — 회귀 게이트 미완 (rev.0 Task 05)

`role_adapter_regression_post.json`이 생성되지 않아 회귀 비교가 미실행됐다. Developer 보고에 따르면 `python run_experiment.py tool-use-refined` 전체 40 runs는 단일 agent turn(1~2시간) 내 완료 불가능하다. 추가로 Developer가 `HEAD^` worktree로 baseline pre를 재실행하려다 더 시간을 낭비했다 — 그러나 pre.json은 이미 commit `2d42ce4` 시점 Exp08b 결과에서 추출되어 있고, 이를 기준선으로 사용해야 한다.

해결책:

- **pre.json은 그대로 사용** — `experiments/results/role_adapter_regression_pre.json` (이미 검증·보존됨).
- **post 생성을 위한 격리 스크립트 신설** — `experiments/run_regression_gate.py`. `run_abc_chain`을 직접 호출해 math-04 한 task만 baseline_refined/tooluse_refined 5 trials = 10 runs 실행. 출력 형식은 기존 pre.json·`regression_check.py extract` 모드와 호환.
- **다단 워크플로 채택** — agent turn 내에서는 스크립트 작성 + smoke import 검증만. **사용자가 offline에서 스크립트 1회 실행**해 post.json을 생성한 뒤, 후속 turn에서 `regression_check.py`로 비교. tunaFlow의 "no background execution" 규칙과 양립.
- **`run_experiment.py` 수정 금지** — rev.0 Non-goals 유지 (`run_experiment.py` 분기 추가 금지). 별도 스크립트로 우회.

### 실패 원인 B — `_post_parse_check` 동작 동치 위반 (rev.0 Task 01 잔여 결함)

리뷰 findings:

- `experiments/agents/critic.py:39-42` — `_post_parse_check`가 `"missing judgments"` 반환. rev.0 task-01 명세는 *"단 Phase 1 동작 동치 보장을 위해 이 체크는 일단 None 반환 (기존 동작 유지)"* 명시.
- `experiments/agents/judge.py:48-51` — `_post_parse_check`가 `"missing converged"` 반환. rev.0 task-01 명세에 정의 없음 (base 클래스 None 반환이 기준).

두 메소드는 B/C 응답에서 해당 키가 없을 때 `base.py:62-66`의 retry 루프를 1회 추가 발동시킨다. 결과적으로 동일 입력에 대해 LLM 호출 횟수가 증가해 회귀 게이트의 4가지 동치 기준(`final_answer`, `num_assertions`, `accuracy`, `tool_calls`) 중 `tool_calls`/`num_assertions` 편차를 키울 수 있다. **반드시 회귀 게이트 실행 전에 수정.**

### 핵심 원칙

- **rev.0 successful subtasks(01·02·03·04) 수정 금지** — `_post_parse_check` 두 메소드 외에 일체 변경 없음.
- **다단 워크플로** — agent turn 내 작업과 사용자 offline 실행을 명시적으로 분리. 결과 검증은 사용자 실행 완료 후 후속 turn에서.

## Expected Outcome

1. `experiments/agents/critic.py:CriticAgent._post_parse_check` 본문이 `return None`만 수행. 의도 명시 코멘트 1줄 추가.
2. `experiments/agents/judge.py:JudgeAgent._post_parse_check` 본문이 `return None`만 수행. 의도 명시 코멘트 1줄 추가.
3. `experiments/run_regression_gate.py` 신규 — math-04 격리 실행 스크립트:
   - `run_abc_chain`을 직접 호출
   - `--trials N` (기본 `TOOL_USE_REFINED_REPEAT`=5), `--out PATH` (기본 `results/role_adapter_regression_post.json`) flag 지원
   - 출력 형식이 `regression_check.py`의 `compare()`가 직접 읽을 수 있는 형태 (pre.json과 동일 구조: `{arm: {task_id, expected_answer, trials: [...]}}`)
4. `docs/plans/role-adapter-phase-1-rev-1-post-parse-check-result.md`(또는 자동 생성 result)에 사용자 offline 실행 절차 명시.
5. (사용자 offline 실행 후) `experiments/results/role_adapter_regression_post.json` 생성.
6. (사용자 offline 실행 후) `python regression_check.py results/role_adapter_regression_pre.json results/role_adapter_regression_post.json` exit 0.
7. 단위 테스트 19개 회귀 없음 (`agents.test_role_agents` 통과).

## Subtask Index

1. [task-01](./role-adapter-phase-1-rev-1-post-parse-check-task-01.md) — `_post_parse_check` 동작 동치 복원 (parallel_group A, depends_on: [])
2. [task-02](./role-adapter-phase-1-rev-1-post-parse-check-task-02.md) — 회귀 게이트 — math-04 격리 스크립트 + 다단 워크플로 (parallel_group B, depends_on: [01])

Task 02는 Task 01 완료 후 실행 (회귀 게이트는 수정된 어댑터로 돌려야 의미 있음).

## Constraints

- **rev.0 successful subtasks (01·02·03·04) 수정 금지** — `experiments/agents/critic.py:_post_parse_check`와 `experiments/agents/judge.py:_post_parse_check` 본문 외에 일체 변경 없음. 클래스 구조·import·다른 메소드·`base.py`·`proposer.py`·`__init__.py`·`test_role_agents.py`·`run_abc_chain`/`run_abc_chunked`/`run_loop`은 그대로.
- `experiments/run_experiment.py` 수정 금지 — rev.0 Non-goals 유지. math-04 격리는 별도 `run_regression_gate.py` 스크립트로 처리.
- `experiments/regression_check.py` 수정 금지 — 4가지 비교 기준(`final_answer` 일치, `num_assertions` ±1, `accuracy_v2` 일치, `total_tool_calls` ±2)과 데이터 형식 그대로 사용.
- `experiments/results/role_adapter_regression_pre.json` 수정 금지 — 기준선 stability 보존. commit `2d42ce4` 시점 Exp08b 결과에서 추출된 값 그대로.
- `experiments/system_prompt.py`, `experiments/schema.py` 수정 금지.
- 새 LLM 호출 추가 금지 — `_post_parse_check` 수정은 retry 횟수를 줄이는 방향(원본 인라인과 동치).
- `run_regression_gate.py`의 결과 형식은 `regression_check.py:compare()`가 그대로 읽을 수 있어야 함 (`{arm: {task_id, expected_answer, trials}}` 구조).
- 사용자 offline 실행은 명시적 책임 분리 — agent는 스크립트·문서 제공, 사용자는 실행. 회귀 비교(`regression_check.py`)만 후속 agent turn에서 수행.

## Non-goals

- A 어댑터(`ProposerAgent`)의 `run_loop()` 통합 — Phase 2.
- LLM Client 추상화, Layered Storage, 새 역할 추가 — rev.0과 동일 (Phase 2/Exp10+/Exp11).
- `run_experiment.py` 분기·flag 추가 — 별도 스크립트로 우회.
- 기존 `experiments/tools/test_*.py` 단위 테스트 추가/변경.
- `_post_parse_check`에서 semantic 검증 도입 — Phase 2 (현재는 caller 책임).
- `ProposerAgent`에 `tools` mock 단위 테스트 추가 — rev.0 review에서 fail 사유 아님 (각 어댑터 ≥5 케이스 충족).
- 회귀 게이트 baseline 재실행 — 기존 pre.json 그대로 사용.
- `experiments/agents/base.py` 수정 — `_post_parse_check`가 None 반환이면 기존 인라인과 결과적으로 동치이므로 base의 break 로직은 보존. 향후 Phase 2 코멘트 작업은 본 plan 범위 밖.
- math-04 외 다른 task 회귀 검증 — Phase 2.

## Version

- v1 (2026-04-25): 최초 작성. rev.0 리뷰 실패(post.json 미생성 + `_post_parse_check` 동치 위반) 대응 plan.
