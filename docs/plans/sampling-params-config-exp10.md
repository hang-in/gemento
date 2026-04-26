---
type: plan
status: in_progress
updated_at: 2026-04-26
slug: sampling-params-config-exp10
version: 1
---

# SAMPLING_PARAMS config 일원화 (Exp10 본격 실행 전 필수 인프라)

## Description

현재 LLM sampling 설정이 코드베이스에 분산되어 있다.

- `experiments/orchestrator.py:71` — `temperature=0.1`, `max_tokens=4096` 가 `call_model()` payload 안에 하드코딩.
- `experiments/_external/lmstudio_client.py:40` — `call_with_meter()` 는 sampling param 을 아예 전달하지 않아 LM Studio 기본값 사용 (값 미지정 → 비결정성).
- seed 정책 부재 — 재현성 평가가 비결정적 sampling 위에서 이루어지고 있음.

이 분산 상태에서 향후 `tools/env_snapshot.py` 가 env.json 을 자동 작성하면 "어디 값이 진실인가" 가 모호해져 reproducibility appendix 의 신뢰도가 깨진다. 본 plan 은 **`config.py:SAMPLING_PARAMS` 단일 source-of-truth** 를 도입하고 모든 호출 지점이 이를 참조하도록 정리한다.

본 plan 은 **probe (`docs/reference/handoff-to-gemini-env-probe.md`) 회신과 독립적** 으로 진행 가능하다. seed 는 필드만 추가하고 기본값 `None` 유지하여 결과 변동 0 을 확보한다.

상위 목표: arXiv preprint v1 reproducibility appendix 인프라.

## Expected Outcome

1. `experiments/config.py` 끝에 `SAMPLING_PARAMS: dict` 추가 — 4 필드 (`temperature`, `max_tokens`, `top_p`, `seed`).
2. `experiments/orchestrator.py:call_model()` 의 payload 구성 (line 67-72) 이 하드코딩 대신 `SAMPLING_PARAMS` 참조.
3. `experiments/_external/lmstudio_client.py:call_with_meter()` 가 `SAMPLING_PARAMS` default 사용 + 옵션 override 가능.
4. `experiments/tests/test_static.py` 에 `TestSamplingParamsCentralization` 추가 — 정합성 정적 검증.
5. `docs/reference/researchNotebook.md` 의 프로젝트 개요 영역에 sampling 한 줄 명시 — 부록 자동 생성 시 인용.
6. 기존 14 실험 결과 동일성 유지 — `temperature=0.1`, `max_tokens=4096` 값 그대로, `top_p=None`, `seed=None`.

## Subtask Index

1. [task-01](./sampling-params-config-exp10-task-01.md) — config.py 에 SAMPLING_PARAMS 추가 (parallel_group A, depends_on: [])
2. [task-02](./sampling-params-config-exp10-task-02.md) — orchestrator.py 가 SAMPLING_PARAMS 참조 (parallel_group B, depends_on: [01])
3. [task-03](./sampling-params-config-exp10-task-03.md) — lmstudio_client.py 가 SAMPLING_PARAMS 참조 (parallel_group B, depends_on: [01])
4. [task-04](./sampling-params-config-exp10-task-04.md) — 정합성 정적 테스트 추가 (parallel_group C, depends_on: [01, 02, 03])
5. [task-05](./sampling-params-config-exp10-task-05.md) — researchNotebook 메모 (parallel_group B, depends_on: [01])

### 의존성 (Stage 기반)

```
Stage 1 (단독):
  task-01 (config 추가)
       │
       ▼
Stage 2 (병렬 3개, task-01 완료 후):
  task-02 (orchestrator)
  task-03 (lmstudio_client)
  task-05 (researchNotebook)
       │
       ▼ (task-02, task-03 완료 후 — task-05 는 막지 않음)
Stage 3 (단독):
  task-04 (정합성 정적 테스트)
```

- Task 02·03·05 모두 task-01 후 동시 시작 가능 (group B).
- Task 04 는 02·03 완료 후. 05 는 04 의 게이트가 아님 (researchNotebook 메모는 코드 정합성과 무관).

## Constraints

- **결과 동일성 보장**: `temperature=0.1`, `max_tokens=4096` 값 변경 금지. 기존 14 실험 재현성 유지가 본 plan 의 1 차 기준.
- **gemini_client.py 변경 금지**: 본 plan 범위는 LM Studio + orchestrator 호출 경로. Gemini API 의 sampling 표준화는 별도 plan.
- **seed 기본값 None 유지**: 결과 분포 변경 방지. seed 정책은 Exp10 본격 실행 전 별도 결정.
- **probe 와 독립**: 본 plan 은 `handoff-to-gemini-env-probe.md` 회신과 무관하게 진행 가능. probe 결과로 plan 변경되지 않음.
- **Reviewer 가드**: LLM 호출 0. 정적 테스트만으로 충분.

## Non-goals

- env.json 자동 작성·lab.md helper — 별도 큰 plan (probe 회신 후 작성).
- llama.cpp commit hash 추출 — LM Studio 미노출 항목.
- Gemini API sampling 표준화 — 별도 plan.
- 14 실험 재실행 — 결과 동일성 보장하므로 불필요.
- arXiv appendix 자동 생성 (`tools/build_appendix.py`) — 별도 큰 plan 의 task.
- seed 활성화 — 본 plan 은 필드만 추가, 활성 시점은 Exp10 시작 전 별도 결정.

## 변경 이력

- 2026-04-26 v1: 초안. probe 와 독립적 mini plan.
