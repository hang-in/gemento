---
type: plan
status: in_progress
updated_at: 2026-04-25
slug: experiments
version: 1
---

# experiments 디렉토리 모듈화 + 인덱스 체계 + 오프라인 정적 검증

## Description

`experiments/run_experiment.py` 한 파일에 응축된 14개 실험 함수(1474 라인)와 평면적 `experiments/results/` 결과 27개 JSON + 4개 report.md를 **실험 단위 디렉토리 구조**로 재편한다. 새 실험 추가·논문 작성 시 인용·재현이 한 디렉토리만 보면 끝나도록 한다.

### 핵심 설계 원칙

- **순수 이동 — 로직 변경 0**. 함수 본문, 상수 값, 호출 시그니처 그대로 옮김. 로직 수정·리팩토링은 본 plan 범위 밖.
- **공용 모듈 이동 금지**. `orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `experiment_logger.py`, `config.py`, `tools/`, `tasks/` 는 현재 위치 유지 (모든 실험에서 import).
- **LLM 호출 0의 정적 검증만**. 사용자 환경(Windows + LM Studio, gemma4:e4b)에서 본격 회귀 가능, 본 plan은 Mac/오프라인에서 import·dispatch·파일 위치만 검증. **Reviewer/Developer가 실증(LLM) 테스트 시도 시 plan 위반 — 토큰 낭비 가드.**
- **CLI 호환성 보존**. `python run_experiment.py exp08b` 등 기존 호출 명세 그대로 동작.
- **단계 분할**. 한 번에 14개 옮기지 않음. 정적 검증 인프라 → 결과 파일 분류 → exp00 패턴 잡기 → 그룹별 순차 이동 → dispatcher 슬림화 + INDEX 완성.

### 검증 대상 함수 (라인 번호 검증)

`experiments/run_experiment.py`의 14개 `run_*()` 함수와 dispatcher dict:

| 함수 | 라인 | dispatcher 키 | 새 디렉토리 |
|------|------|---------------|-------------|
| `run_baseline` | 56 | `baseline` | `exp00_baseline/` |
| `run_assertion_cap` | 99 | `assertion-cap` | `exp01_assertion_cap/` |
| `run_multiloop` | 154 | `multiloop` | `exp02_multiloop/` |
| `run_error_propagation` | 214 | `error-propagation` | `exp03_error_propagation/` |
| `run_cross_validation` | 306 | `cross-validation` | `exp035_cross_validation/` |
| `run_abc_pipeline` | 438 | `abc-pipeline` | `exp04_abc_pipeline/` |
| `run_prompt_enhance` | 545 | `prompt-enhance` | `exp05a_prompt_enhance/` |
| `run_tool_separation` | 661 | `tool-separation` | `_archived/exp04_tool_separation_deprecated/` |
| `run_handoff_protocol` | 684 | `handoff-protocol` | `exp045_handoff_protocol/` |
| `run_solo_budget` | 777 | `solo-budget` | `exp06_solo_budget/` |
| `run_loop_saturation` | 889 | `loop-saturation` | `exp07_loop_saturation/` |
| `run_tool_use` | 1012 | `tool-use` | `exp08_tool_use/` |
| `run_tool_use_refined` | 1126 | `tool-use-refined` | `exp08b_tool_use_refined/` |
| `run_longctx` | 1365 | `longctx` | `exp09_longctx/` |

`EXPERIMENTS` dict는 line 1442에 정의되어 있다. `run_tool_separation`은 결과 파일이 0개로 deprecated 상태이며, `_archived/`로 격리하고 dispatcher에서 제거한다.

### 결과 파일 분류 (verified)

`experiments/results/` 안의 27개 JSON + 4개 report.md를 prefix 매칭으로 분류:

- exp00_baseline_*.json (3) → `exp00_baseline/results/`
- exp01_assertion_cap*.json (7, partial 포함) → `exp01_assertion_cap/results/`
- exp02_multiloop_*.json (2) + `exp02_report.md` → `exp02_multiloop/results/`
- exp03_error_propagation_*.json (1) → `exp03_error_propagation/results/`
- exp035_cross_validation_*.json (1) → `exp035_cross_validation/results/`
- exp04_abc_pipeline_*.json (1) → `exp04_abc_pipeline/results/`
- exp045_handoff_protocol_*.json (3) → `exp045_handoff_protocol/results/`
- exp05a_prompt_enhance_*.json (1) → `exp05a_prompt_enhance/results/`
- exp06_solo_budget_*.json (1) → `exp06_solo_budget/results/`
- exp07_loop_saturation_*.json (1) + `exp07_report.md` → `exp07_loop_saturation/results/`
- exp08_tool_use_*.json (1) + `exp08_report.md` → `exp08_tool_use/results/`
- exp08b_tool_use_refined_*.json (1) + `exp08b_report.md` → `exp08b_tool_use_refined/results/`
- exp09_longctx_*.json (1) + `exp09_report.md` → `exp09_longctx/results/`

`experiments/exp01_run.log`(top-level)는 `exp01_assertion_cap/`로 이동.

## Expected Outcome

1. `experiments/exp00_baseline/`, `experiments/exp01_assertion_cap/` ... 13개 활성 실험 디렉토리 + `experiments/_archived/exp04_tool_separation_deprecated/` 1개. 각 활성 디렉토리는 `run.py` (이전 함수 본문), `INDEX.md` (개요·결과·report 링크), `results/*.json` (해당 실험 결과만) 보유.
2. 최상위 `experiments/INDEX.md` — 13 활성 + 1 archived 표 + 메트릭 + 디렉토리 링크.
3. `experiments/run_experiment.py` 슬림화 (~80라인 이하의 dispatcher만). 14개 `run_*()` 함수 본문 0개. EXPERIMENTS dict는 각 실험 모듈 import + 매핑.
4. `experiments/tests/test_static.py` 신규 — 정적 테스트 모음 (import 무결성, dispatcher 매핑, 결과 파일 위치, INDEX 링크 무결성). unittest 스타일, LLM 호출 0.
5. CLI 표면 보존. `python run_experiment.py --help` 가 13개 active 실험 choices 출력. 기존 `python run_experiment.py baseline` 호출 그대로 동작 (실 실행은 사용자 Windows 환경에서 검증).
6. 결과 JSON·report 31개 모두 `git mv`로 이동되어 history 보존. `git log --follow`로 추적 가능.
7. 기존 `experiments/exp01-04*/설명.md`는 새 디렉토리의 `INDEX.md`로 흡수 (또는 INDEX.md가 설명.md를 link).

## Subtask Index

1. [task-01](./experiments-task-01.md) — 정적 검증 인프라 + 디렉토리 템플릿 + 최상위 INDEX 골격 (parallel_group A, depends_on: [])
2. [task-02](./experiments-task-02.md) — 결과 JSON 30+개 → 실험별 `results/` 분류 (parallel_group A, depends_on: [01])
3. [task-03](./experiments-task-03.md) — exp00 분리 (단독, 패턴 확립) (parallel_group B, depends_on: [01, 02])
4. [task-04](./experiments-task-04.md) — ABC 계열 5개 분리 (parallel_group C, depends_on: [03])
5. [task-05](./experiments-task-05.md) — handoff·prompt·solo·deprecated 계열 4개 분리 (parallel_group C, depends_on: [04])
6. [task-06](./experiments-task-06.md) — 후속 실험 4개 분리 (parallel_group C, depends_on: [05])
7. [task-07](./experiments-task-07.md) — dispatcher 슬림화 + INDEX 완성 (parallel_group D, depends_on: [06])

순차 실행. 각 단계는 `experiments/tests/test_static.py` 통과를 게이트로 사용.

## Constraints

- **로직 수정 금지** — 본 plan은 순수 파일 이동·dispatcher 재구성만. `run_*()` 함수 내부 로직, 상수 값, 호출 시그니처 일체 변경 금지.
- **공용 모듈 이동 금지** — `experiments/orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `experiment_logger.py`, `config.py`, `tools/`, `tasks/` 는 현재 위치 유지.
- **LLM 호출 검증 일체 금지** — Reviewer/Developer가 `python run_experiment.py exp08b` 식의 실증 실행으로 검증 시도 시 plan 위반. 모든 verification은 import·dispatch·파일 위치 같은 정적 체크만. 본격 실행 검증은 사용자 Windows 환경에서 직접.
- **CLI 호환성 유지** — 기존 `python run_experiment.py <name>` 호출 표면 그대로. argparse choices 변경 시 ② run_tool_separation 만 제거(deprecated). 나머지 13개 키 보존.
- **결과 JSON history 보존** — 모든 결과 파일 `git mv`로 이동. `git rm` + `git add` 분리 사용 금지 (history 끊김).
- **`experiments/results/` 디렉토리 폐지** — 이동 후 비어있으면 제거.
- **deprecated 실험 명시적 격리** — `run_tool_separation` (구 exp04, 폐기됨)은 `_archived/exp04_tool_separation_deprecated/`로 옮기고 dispatcher에서 제거.
- **__init__.py 추가 허용** — 각 실험 디렉토리·`tests/` 디렉토리에 `__init__.py` 추가 가능 (패키지 import 필요 시).
- **abandoned 처리된 plan 문서 손대지 않음** — `docs/plans/role-adapter-*`, `docs/plans/exp0*-*` 등 기존 plan 문서는 본 plan 범위 밖.

## Non-goals

- **실험 로직 개선·리팩토링·버그 수정** — 별도 plan으로.
- **새 실험 추가** — exp10+ 같은 신규 실험은 본 plan 범위 밖.
- **회귀 게이트 실행** — pre.json 대비 post.json 비교 같은 LLM 기반 검증은 본 plan에서 안 함. (사용자 Windows 환경에서 별도 진행)
- **결과 데이터 schema 변경** — JSON 구조·키 그대로 유지.
- **공용 모듈(`orchestrator.py` 등) 인터페이스 변경** — `run_*()` 함수가 호출하는 함수 시그니처 일체 손대지 않음.
- **role-adapter Phase 1 재시도** — abandoned 처리됐고 본 plan과 무관 (`archive/role-adapter-phase-1-2026-04-25` 브랜치에 격리).
- **`tools/`, `tasks/`, `agents/` 디렉토리 재구성** — 본 plan은 `run_*()` 함수 분리만. 공용 디렉토리 구조 변경은 별도.
