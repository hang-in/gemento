---
type: task
status: todo
updated_at: 2026-04-15
plan: exp045-v2
---

# Task 1: rescore_all에서 handoff_protocol v2 채점 지원

## Changed files

- `experiments/measure.py`
  - `rescore_all()` 내부 `SKIP_TYPES` (measure.py:245)
  - `_score_trials()` 루프 (measure.py:261-271) — handoff_protocol 결과에서도 `trials[].final_answer` 채점 가능한지 검증 및 필요 시 수정

수정 대상 파일은 1개.

## Change description

1. `SKIP_TYPES = {"handoff_protocol"}` → `SKIP_TYPES = set()`로 변경 (또는 해당 분기 제거).
2. `_score_trials` 내부에서 `exp_type == "baseline"` 외 분기는 `trial.get("final_answer", "")`를 사용 중. handoff_protocol 결과의 `trials[]` 원소에 `final_answer` 키가 존재하는지 확인. 만약 이름이 다르다면(`final_response` 등) 분기 추가.
   - 확인 명령: `python3 -c "import json; d=json.load(open('experiments/results/exp045_handoff_protocol_20260414_135634.json')); print(list(d['results'][0]['trials'][0].keys()))"`
3. `task_map` lookup은 이미 `tr["task_id"]` 키로 동작하므로 그대로 재사용.
4. v1 채점은 `tr.get("expected_answer", "")` 사용 — 현재 handoff_protocol 결과에 `expected_answer`가 result 레벨에 있는지 확인. 없으면 `task_map` 값에서 fallback 경로 추가.
5. 기존 `analyze_handoff_protocol` 함수는 **건드리지 않는다**. rescore 경로에만 v2 accuracy 채점 추가.

## Dependencies

- 선행 작업 없음 (Scoring V2 Plan은 이미 완료).
- Python 3.14, 표준 라이브러리만 필요.

## Verification

```bash
# 1) handoff_protocol이 더 이상 skip되지 않는지 확인
python3 experiments/measure.py --rescore | grep exp045_handoff_protocol

# 2) 출력 행에 숫자(v1/v2/diff)가 있고 '(skip)'이 없어야 함
python3 experiments/measure.py --rescore | grep -v "(skip)" | grep exp045

# 3) 다른 실험의 rescore 수치에 회귀가 없는지(exp06 등) 확인
python3 experiments/measure.py --rescore | grep -E "exp00|exp02|exp04|exp06"

# 4) 단일 파일 분석(기존 경로)이 정상 동작하는지 확인
python3 experiments/measure.py experiments/results/exp045_handoff_protocol_20260414_135634.json
```

각 명령의 기대 결과:
1. exp045 행이 존재하고 v1/v2 숫자 포함
2. `(skip)` 문자열이 포함되지 않음
3. exp06=0.967, exp00/02/04 기존 값과 동일
4. 기존 `analyze_handoff_protocol` 출력(Loss Rate, Backprop Acc) 정상

## Risks

- **키 이름 불일치**: handoff_protocol 결과의 trial 구조가 abc_pipeline과 미묘히 다를 수 있음. Verification 명령 #1/#2에서 v2=0.000 같은 비정상 수치가 나오면 trial 키 이름 재확인 필요.
- **expected_answer 위치**: handoff_protocol 결과는 top-level result에 `expected_answer`가 있음(확인됨: results[0] keys에 포함). v1 채점은 그대로 작동해야 함.
- **사이드이펙트**: `analyze_handoff_protocol`은 건드리지 않으므로 기존 Loss Rate/Backprop 수치는 영향 없음.
- **회귀**: rescore 테이블 다른 실험 수치는 코드 변경 범위(SKIP_TYPES, _score_trials)만 건드리므로 변경 없어야 함.

## Scope boundary

수정 금지:
- `experiments/tasks/taskset.json` (Scoring V2 Plan에서 이미 확정)
- `experiments/orchestrator.py`, `experiments/run_experiment.py` (실험 실행 로직)
- `experiments/results/*.json` (읽기 전용)
- `score_answer`, `score_answer_v2` 함수 시그니처 (analyzer들이 의존)
- `analyze_handoff_protocol`, `analyze_baseline`, `analyze_multiloop`, `analyze_abc_pipeline`, `analyze_solo_budget` 함수 본체
- `docs/plans/scoring-v2-*.md` (완료된 플랜)
