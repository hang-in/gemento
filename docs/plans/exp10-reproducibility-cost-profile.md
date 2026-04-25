---
type: plan
status: in_progress
updated_at: 2026-04-26
slug: exp10-reproducibility-cost-profile
version: 1
---

# Exp10 — Reproducibility & Cost Profile

## Description

지금까지 9차례 실험으로 H1, H7, H8, H9 가설을 채택했지만, 각 실험은 N=3~5 trial로 **정답률 평균만 보고**되었고 **분산은 측정되지 않았다**. 또한 "Externalization 프레임"이 2026-04 arXiv에 이미 등장한 상황에서, 제멘토의 차별 자산은 정확도가 아니라 **"외부화로 비용·시간이 얼마나 줄었나"** 라는 데이터다. 본 plan은 그 두 가지를 묶어 답한다.

### 핵심 질문 두 가지

1. **재현성 (Q1)**: 같은 입력 N=20 trial 돌리면 정답률 표준편차는? 상위·하위 outlier 어떤 양상?
2. **비용·시간 (Q2)**: Gemma 4 E4B + 8루프 (loop_saturation baseline_phase15 동등) vs Gemini 2.5 Flash 1회 호출 — 토큰·달러·벽시계 시간 trade-off는?

### 차별화 포인트

- 9개 실험은 정확도 검증, **Exp10은 외부 평가용 데이터**.
- 본 plan 결과로 다모앙·트위터 공유 시 "왜 이게 의미 있는가"의 정면 답이 됨.
- 학술적으로도 "재현성 데이터 부재"라는 약점 보강.

### 9 task subset (확정)

`experiments/tasks/taskset.json` 의 12 task 중 9개 (math-01~04 + synthesis-01·03·04 + logic-03·04). logic-01·02 와 synthesis-02 는 prior 실험에서 JSON 파싱 불안정 / final_answer=None 이력 있어 제외.

| Task | 카테고리 | 비고 |
|------|---------|------|
| math-01 | Math | Exp08/08b 검증 |
| math-02 | Math | Exp08/08b 검증 |
| math-03 | Math | Exp08/08b 검증 |
| math-04 | Math | Exp08b 100% 도달 |
| synthesis-01 | Synthesis | Exp04~06 검증 |
| synthesis-03 | Synthesis | Exp04~06 검증 |
| synthesis-04 | Synthesis | Exp04~06 검증 |
| logic-03 | Logic | Exp08b 검증 (logic-01·02 와 다른 카테고리) |
| logic-04 | Logic | Exp08b 검증 |

### 3 condition

| Label | 설명 | 예상 시간/호출 | 비용 |
|-------|------|----------------|------|
| `gemma_8loop` | Gemma 4 E4B + 8루프 (loop_saturation baseline_phase15 동등) | ~3-5분/trial × 180 = 9-15시간 | $0 (로컬) |
| `gemma_1loop` | Gemma 4 E4B 단일 추론 | ~30초/trial × 180 = 1.5시간 | $0 |
| `gemini_flash_1call` | Gemini 2.5 Flash 1회 직접 호출 (rate limit 1초 sleep) | ~5초/trial × 180 + 180s sleep = 18분 | ~$0.05-0.20 추정 (Google AI Studio 가격, 사용자 $300 무료 크레딧 기간) |

3 condition × 9 task × 20 trial = **540 trial 총합**. 사용자 Windows 환경에서 본격 실행.

### API 키 정책 (사용자 결정 사항 반영)

- 키 저장: `gemento/.env` 파일 (사용자 직접 생성). `GEMINI_API_KEY=...` 또는 `SECALL_GEMINI_API_KEY=...` 둘 다 인식.
- fallback: 형제 디렉토리 `../secall/.env` 도 자동 시도.
- `.gitignore` 에 `.env` 추가 (task-01 처리).
- rate limit: 호출당 1초 sleep (Google AI Studio 무료 tier 안전 마진). $300 크레딧 paid tier 면 빠르게 가능 — 본 plan 은 보수적 1초.

## Expected Outcome

1. `experiments/exp10_reproducibility_cost/` 신규 디렉토리 (모듈화 표준 따름: `__init__.py`, `run.py`, `INDEX.md`, `results/`, `tasks.py`, `analyze.py`)
2. `experiments/_external/` 신규 디렉토리 — `gemini_client.py`, `lmstudio_client.py`, `__init__.py` (`load_env_file` + `resolve_gemini_key` helper, metering 포함)
3. `experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json` — 540 trial 원본 응답 + accuracy + token + duration_ms
4. `experiments/exp10_reproducibility_cost/results/exp10_report.md` — 평균·표준편차·신뢰구간, 비용 비교 표
5. `experiments/run_experiment.py` 의 EXPERIMENTS dict 에 `"reproducibility-cost"` 키 추가 → 14 active
6. `experiments/INDEX.md` 갱신 (14 active + 1 archived 표)
7. `experiments/tests/test_static.py` 의 `SPLIT_EXPERIMENTS`·`EXPECTED_KEYS_AFTER_TASK_05` 갱신
8. `docs/reference/researchNotebook.md` 에 Exp10 섹션 추가 (5W1H 형식, 핵심 발견 3-5개, Externalization 비교 단락)

## Subtask Index

1. [task-01](./exp10-reproducibility-cost-profile-task-01.md) — 외부 API 클라이언트 + metering wrapper (parallel_group A, depends_on: [])
2. [task-02](./exp10-reproducibility-cost-profile-task-02.md) — 9 핵심 task subset 확정 + 채점 spec (parallel_group A, depends_on: [])
3. [task-03](./exp10-reproducibility-cost-profile-task-03.md) — Exp10 dispatcher (run.py) 작성 (parallel_group B, depends_on: [01, 02])
4. [task-04](./exp10-reproducibility-cost-profile-task-04.md) — 채점·집계 스크립트 (analyze.py) (parallel_group B, depends_on: [03])
5. [task-05](./exp10-reproducibility-cost-profile-task-05.md) — INDEX.md + tests 갱신 + smoke 실행 (parallel_group C, depends_on: [01, 02, 03, 04])
6. [task-06](./exp10-reproducibility-cost-profile-task-06.md) — 본격 실행 + report 작성 (parallel_group D, depends_on: [05])

Task 01·02 는 병렬 가능. 03 은 둘 모두 완료 후. 04 는 03 후. 05 는 모두 통합 후. 06 은 마지막 실증 단계.

## Constraints

- **외부 API 비용 제한**: Gemini 2.5 Flash 9 task × 20 trial = 180 호출, ~$0.20 미만 예상 (사용자 $300 Google Cloud 무료 크레딧 보유). 그 이상 발생 시 plan 일시정지. `GEMINI_API_KEY` 또는 `SECALL_GEMINI_API_KEY` (gemento/.env 또는 ../secall/.env 또는 env 변수) 필수.
- **Windows 측에서 본격 실행** (Subtask 6) — Mac에서 LM Studio endpoint 도달 가능하면 Mac도 OK. 하지만 LM Studio 가 Windows 라 Windows 권장.
- **모듈화 표준 준수** — 각 expXX/run.py 가 자체 `RESULTS_DIR` 정의. config.py 수정 금지. experiments-task-07 rev 패턴 따름.
- **기존 task set 재사용** — `experiments/tasks/taskset.json` 의 검증된 task만 사용. 새 task 추가는 별도 plan.
- **체크포인트 필수** — 540 호출은 중간 실패 가능성 큼. partial JSON 자동 저장 + resume 동작 검증.
- **Reviewer 가드 (강조)**: 본 plan은 실증(LLM) 실행이 본질이므로 Subtask 1~5 는 정적 검증만, **Subtask 6 만 실제 LLM 호출**. Subtask 6 의 verification 은 "사용자가 실행 후 결과 보고" 형태 (다단 워크플로 — `role-adapter-phase-1-rev-1-post-parse-check-task-02` 패턴 재사용). Reviewer/Developer 가 Subtask 1~5 단계에서 실증 호출 시 plan 위반.
- **공용 모듈 보존** — `experiments/orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `config.py`, `tools/`, `tasks/` 수정 금지.

## Non-goals

- **다른 모델과의 비교** (Gemma 외 7B, 13B 등) — 별도 plan.
- **Gemma 외 다른 소형 모델** (Phi, Qwen) 비교 — 별도 plan.
- **새 task 카테고리** (코딩, 한국어, retrieval) — 본 plan 은 검증된 9 task 만.
- **fine-tuning** — Gemma 는 baseline 그대로 사용.
- **다른 외부 API** (GPT-4o-mini, Claude, etc.) — 본 plan 은 Gemini 2.5 Flash 만. 다른 모델 비교는 별도 plan.
- **Gemini Pro / Ultra** — 본 plan 은 Flash 만 (저비용·고속). Pro 비교는 별도.
- **streaming API metering** — 본 plan은 batch 호출만.
- **Tier/Layer wrapping (옵션 C)** — secall 영역과 겹쳐 본 plan과 분리.
