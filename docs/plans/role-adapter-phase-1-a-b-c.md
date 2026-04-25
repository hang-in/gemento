---
type: plan
status: abandoned
updated_at: 2026-04-25
version: 1
---

# Role Adapter 리팩토링 (Phase 1) — A/B/C 어댑터 분리 + 회귀 게이트

## Description

`experiments/orchestrator.py`의 `run_abc_chain()` (L485~약 L780)과 `run_abc_chunked()` (L792~)가 A/B/C 3역할의 호출·파싱·retry·에러 처리·상태 갱신을 **인라인으로 펼쳐** 비대해진 상태다 (`run_abc_chain` 단일 함수가 약 300줄). B(L549~) 와 C(L629~) 블록은 **동일한 retry 패턴**(`call_model → extract_json_from_response → 1회 retry → parse 실패 처리`)을 가지면서 같은 함수 내에서 두 번 펼쳐져 있다.

브랜치 토론(b20)에서 4개 검토 축(A. LLM Client 추상화 / B. Role Adapter / C. Handoff Validator / D. Layered Storage)을 평가한 결과, **B (Role Adapter)만 Phase 1로 채택**:
- A는 불필요 — `call_model`이 이미 충분히 추상화됨
- C는 Phase 1에 최소 형태만 (기존 `HandoffA2B`/`HandoffB2C` 유지)
- D는 Exp11 후보로 보류 — Layered Storage 도입 자체가 실험 가설

### 핵심 원칙 — 동작 동치(behavior-preserving)

이 리팩토링은 **구조 개선만**이고 **기능·성능·결과 변화 0**을 목표로 한다. 어댑터 도입 전후로 실험 결과 수치(`final_answer`, `accuracy`, `num_assertions`)가 변하면 Phase 1 미통과 — merge 금지.

회귀 게이트로 Exp08b math-04 (5 trial × 2 arm = **10 runs**)를 사용한다. 이유:
- 분산 적음 (baseline 0%, tooluse 100%로 극명)
- 실행 빠름 (수 분 단위)
- Exp09는 아직 Gemini 측 실행 중이라 안정적 baseline 없음

### 용어 일관성

브랜치 토론에서 등장한 "Author / Buddy / Critic" 명칭은 **사용하지 않는다**. conceptFramework § 2 / system_prompt.py 상수명과 일치하는 **Proposer / Critic / Judge**를 canonical로 유지:
- `ProposerAgent` (A) — 추론 실행자, `SYSTEM_PROMPT` 사용
- `CriticAgent` (B) — 교차 검증자, `CRITIC_PROMPT` 사용
- `JudgeAgent` (C) — 수렴 판단·phase 전이 결정자, `JUDGE_PROMPT` 사용

## Expected Outcome

1. **`experiments/agents/` 디렉터리 신설**:
   - `__init__.py` — `RoleAgent`, `ProposerAgent`, `CriticAgent`, `JudgeAgent` export
   - `base.py` — `RoleAgent` 추상 베이스. `call(...)` 메소드, `_build_messages`, `_parse_response`, `_on_error` 공통 인터페이스
   - `proposer.py` — A 역할. 기존 `run_loop()`의 인라인 A 처리를 어댑터로 추출
   - `critic.py` — B 역할. 기존 line 549~624 인라인 B 블록을 어댑터로 추출
   - `judge.py` — C 역할. 기존 line 629~ 인라인 C 블록을 어댑터로 추출
2. **`run_abc_chain()` 리팩토링** — A/B/C 인라인 블록을 어댑터 호출로 교체. 함수 시그니처·반환 튜플·로깅 포인트 모두 유지. 라인 수 약 300 → 약 100~150 예상.
3. **`run_abc_chunked()` 리팩토링** — chunk iteration 안의 A 호출 + 최종 B·C 수렴을 동일 어댑터 사용. 시그니처·반환값·`assertion_soft_cap`/`hard_cap` 파라미터 유지.
4. **단위 테스트** — `experiments/agents/test_role_agents.py`. `unittest.mock.patch`로 `call_model` mocking. 각 어댑터당 최소 5 케이스(정상, retry, parse fail, empty response, error 전파).
5. **회귀 게이트 (필수)** — Exp08b math-04 10 runs 재실행. 리팩토링 전후 4개 기준 동치 확인:
   - 각 trial의 `final_answer` 문자열 동일
   - `num_assertions` 개수 ±1 허용
   - arm별 v2 accuracy 동일
   - tool_calls 총합 ±2 허용
6. **Exp09 진행 영향 없음** — 리팩토링은 `run_longctx` 자체를 건드리지 않으므로 Gemini의 Windows 실행과 충돌 없음.

## Subtasks (Summary)

| # | Title | parallel_group | depends_on |
|---|-------|----------------|------------|
| 01 | RoleAgent 베이스 + 3 어댑터 클래스 | A | — |
| 02 | `run_abc_chain()` 리팩토링 | B | 01 |
| 03 | `run_abc_chunked()` 리팩토링 | B | 01 |
| 04 | 어댑터 단위 테스트 | B | 01 |
| 05 | 회귀 게이트 (Exp08b math-04 동치 확인) | C | 02, 03, 04 |

Task 02·03·04는 Task 01 완료 후 병렬 가능. Task 05는 마지막 게이트 — 모든 코드 변경 후 실행.

## Constraints

- **동작 동치 보장** — 실험 결과 수치 변경 금지. 회귀 게이트가 game-over.
- **용어 일관성** — Proposer/Critic/Judge (conceptFramework § 2, system_prompt.py 상수명 일치). Author/Buddy 등 브랜치 토론 명칭 사용 금지.
- 기존 함수 **수정 금지**: `build_prompt`, `build_critic_prompt`, `build_judge_prompt` 및 `_with_phase` 변형, `apply_llm_response`, `extract_json_from_response`, `call_model`, `select_assertions`, `create_initial_tattoo`, `run_loop`. 어댑터가 호출만.
- `experiments/schema.py`, `experiments/system_prompt.py`의 상수·클래스 **수정 금지**.
- `run_abc_chain` / `run_abc_chunked` 함수 **시그니처·반환 튜플 형태 유지**. 호출부(`run_experiment.py`의 모든 분기) 영향 없어야 함.
- 새 LLM 호출 추가 금지 — 호출 횟수가 변하면 동치 깨짐.
- Exp09 실행과 **병렬 진행** — `run_longctx` 함수는 어댑터 도입 안 함 (Phase 1 범위 외).
- 테스트는 `experiments/agents/test_role_agents.py` 위치 — 기존 `tools/test_*.py`와 같은 package import 스타일 (`from agents.proposer import ProposerAgent` 같은 형태로 통일).

## Non-goals

- LLM Client 추상화 (모델 교체 추상화) — 4축 A, 불필요.
- Handoff Validator 강화 (스키마 fail-fast) — 4축 C 중 Phase 2.
- Layered Storage (raw/compressed/distilled) — 4축 D, Exp11 후보.
- 새 역할 추가 (Reducer, Extractor, Sub-Critic 등) — Exp10+ 범위.
- Tattoo 스키마 확장 — 금지.
- 실험 결과·성능 개선 — Phase 1 목표 아님. 개선은 Phase 2 별도 실험.
- 정보 누출 강제 차단 (역할 간 정보 접근 제한 런타임 강제) — Phase 1은 인터페이스 명시만.
- `run_abc_chain`/`run_abc_chunked` 외 다른 실험 분기 리팩토링 (`run_tool_use`, `run_tool_use_refined`, `run_loop_saturation`, `run_longctx` 등) — 범위 외.
- Critic Tool (결정론적 검증기) 도입 — conceptFramework § 4의 Critic Agent와 별개, Exp09 이후.

## Version

- v1 (2026-04-25): 최초 작성. 5 서브태스크, 회귀 게이트 = Exp08b math-04 10 runs.
