---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: D
depends_on: [05]
---

# Task 06 — 본격 실행 + report 작성 (다단 워크플로)

## Changed files

- `experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json` — **신규 (사용자 Windows 실행 후 생성)**. 540 trial 원본 데이터
- `experiments/exp10_reproducibility_cost/results/exp10_report.md` — **신규**. analyze.py 출력
- `experiments/exp10_reproducibility_cost/INDEX.md` — **수정**. 메트릭 표·결과 파일 링크 갱신
- `docs/reference/researchNotebook.md` — **수정**. Exp10 섹션 추가 (5W1H, 핵심 발견, Externalization 비교)

신규 외 다른 파일 수정 금지.

## Change description

### 배경 — 본 task 는 "다단 워크플로"

본 plan 의 핵심 가드: **agent turn 내에서 실증 LLM 호출 금지**. 540 호출은 agent 1 turn (최대 ~10분) 으로 불가능. 따라서 다음 워크플로:

```
[Agent turn N — 사전 안내]
  - task-05 까지 완료된 상태 확인
  - 사용자에게 Windows 실행 명령 + 예상 시간 보고
  → 사용자 offline 실행 안내

[사용자 Windows offline 실행 — 4-12시간]
  cd experiments
  # API 키는 (1) gemento/.env 파일에 GEMINI_API_KEY=... 입력하거나
  # (2) 다음 명령으로 env 변수 설정:
  $env:GEMINI_API_KEY = "AIza..."   # 또는 SECALL_GEMINI_API_KEY
  ..\.venv\Scripts\python run_experiment.py reproducibility-cost --trials 20
  # 진행 stdout 으로 표시됨 — 540회 호출, gemini_flash 호출 후 1초 sleep
  # 결과: experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json

[Agent turn N+1 — 사용자가 실행 완료 보고 후]
  - results/*.json 존재 확인
  - python -m exp10_reproducibility_cost.analyze <json> > results/exp10_report.md
  - INDEX.md 메트릭 표 갱신
  - researchNotebook.md 에 Exp10 섹션 추가
  → impl-complete 마커
```

**Reviewer/Developer 가드**: Subtask 1~5 만 본 turn 에서 처리. Subtask 6 의 **본격 실행은 사용자 Windows 환경**, 본 turn 에서는 **사전 안내 + 후속 turn 보고용 placeholder**. role-adapter rev-1 task-02 의 다단 워크플로 패턴 재사용.

### Step 1 — 사전 안내 (agent turn 내, 코드 변경 0)

본 task 시작 시 agent 가 사용자에게 다음을 명시 보고:

```
=== Exp10 본격 실행 안내 ===

준비:
  1. Gemini API 키 보유 (Google AI Studio https://aistudio.google.com/apikey)
     - gemento/.env 에 `GEMINI_API_KEY=AIza...` 입력 (권장)
     - 또는 ../secall/.env 의 SECALL_GEMINI_API_KEY 자동 fallback (코드 처리)
  2. LM Studio 가 Gemma 4 E4B 모델 로드 + serving 중

실행 (Windows PowerShell):
  cd path\to\gemento\experiments
  # 옵션 1: gemento/.env 에 키 미리 입력해두면 별도 export 불필요
  # 옵션 2: env 변수로 직접 export
  $env:GEMINI_API_KEY = "AIza..."
  ..\.venv\Scripts\python run_experiment.py reproducibility-cost --trials 20

예상 시간:
  - gemma_8loop:        4-10시간 (180 trial × ABC chain)
  - gemma_1loop:        0.5-1시간 (180 trial × 단일 호출)
  - gemini_flash_1call: 15-25분  (180 trial × API + 1초 sleep)
  - 합계: 약 5-12시간

체크포인트:
  - 매 trial 후 partial JSON 자동 저장 (중단 시 resume)
  - 위치: experiments/exp10_reproducibility_cost/results/partial_exp10_reproducibility_cost.json

비용:
  - Gemini 2.5 Flash ~$0.05-0.20 예상 (180 호출, $0.075/M input + $0.30/M output)
  - 사용자 $300 Google Cloud 무료 크레딧 기간 내 무료
  - $1 초과 시 사용자 즉시 중단 권장
  - 429 (rate limit) 발생 시 GEMINI_CALL_SLEEP_SEC 늘리기 (기본 1초 → 2초)

완료 후 사용자 보고:
  - exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json 파일 경로 + git push
  - 후속 agent turn 에서 analyze.py 로 report.md 생성
```

### Step 2 — 사용자 실행 완료 후 (후속 agent turn)

(2-1) 결과 JSON 존재 확인:
```bash
ls /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json
```

(2-2) analyze.py 실행:
```bash
cd /Users/d9ng/privateProject/gemento/experiments
LATEST=$(ls -t exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json | head -1)
_ZO_DOCTOR=0 ../.venv/bin/python -m exp10_reproducibility_cost.analyze "$LATEST" -o exp10_reproducibility_cost/results/exp10_report.md
```

(2-3) `exp10_reproducibility_cost/INDEX.md` 핵심 메트릭 표를 report.md 의 Q2 표 값으로 채움:

```markdown
## 핵심 메트릭

| condition | accuracy mean ± std | total cost USD | total wallclock (s) |
|-----------|--------------------:|---------------:|--------------------:|
| gemma_8loop | (analyze.py 출력에서 복사) | $0 | TBD |
| gemma_1loop | ... | $0 | ... |
| gemini_flash_1call | ... | $... | ... |
```

(2-4) `docs/reference/researchNotebook.md` 에 Exp10 섹션 추가 (다른 실험과 동일 5W1H 형식):

```markdown
### Exp10: Reproducibility & Cost Profile (Q1·Q2 검증)

| 항목 | 내용 |
|------|------|
| 누가 | Gemma 4 E4B (LM Studio) + Gemini 2.5 Flash (Google AI Studio API) |
| 언제 | 2026-04-26 ~ (사용자 실행 시점 기록) |
| 어디서 | Windows + LM Studio (gemma4-e4b) + OpenAI API |
| 무엇을 | 9 task × 3 condition × N=20 trial = 540 trial |
| 왜 | Q1 (재현성: 분산 측정) + Q2 (비용·시간 trade-off) |
| 어떻게 | gemma_8loop / gemma_1loop / gemini_flash_1call 비교 |

### 핵심 발견 (3-5개)

1. (report.md 의 Q1 결과 기반)
2. (report.md 의 Q2 결과 기반)
3. (report.md 의 Externalization 비교 기반)

### Externalization 프레임 비교

(2026-04 arXiv 기준 Externalization 프레임은 학술계 등장. 본 실험은 그 프레임의
"비용·재현성" 구체 데이터를 제공한다는 점에서 차별 자산.)

- gemma_8loop accuracy vs gemini_flash: ...
- cost ratio: ...
- wallclock 차이: ...

### 결론

(채택/기각 또는 정량 보고)
```

(2-5) git add + commit (사용자 결정 — 단일 commit 권장):
```bash
git add experiments/exp10_reproducibility_cost/results/ \
        experiments/exp10_reproducibility_cost/INDEX.md \
        docs/reference/researchNotebook.md
git commit -m "feat(exp10): Reproducibility & Cost Profile — 540 trial 결과 + report"
git push origin main
```

### Step 3 — Verification 두 그룹 분리

본 plan 본문 Constraints 의 "Reviewer 가드" 와 일치:

- **Group A (agent turn 내, 즉시 실행 가능)** — 1, 2, 3.
- **Group B (사용자 Windows 실행 후, 후속 turn 에서 실행)** — 4, 5, 6, 7.

agent turn 내에서는 Group A 만. Group B 는 사용자 실행 보고 후 별도 turn.

## Dependencies

- **Task 05 완료** — dispatcher key `reproducibility-cost` 가 `EXPERIMENTS` dict 에 등록되어야 본격 실행 가능.
- **사용자 Windows 환경** — LM Studio gemma4-e4b serving + OPENAI_API_KEY env.
- 외부 패키지: 없음 (task-01·03·04 의존성 그대로).

## Verification

### Group A — agent turn 내 즉시 실행 (LLM 호출 0)

```bash
# 1. task-05 까지 완료 상태 — dispatcher 14 키
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
assert 'reproducibility-cost' in run_experiment.EXPERIMENTS
print('OK Exp10 dispatcher ready')
"

# 2. analyze.py import + dummy report 동작 (task-04 verification 재확인)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.analyze import build_report
print('OK analyze.py ready')
"

# 3. test_static.py 모두 PASS — task-05 후 상태 유지
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static 2>&1 | tail -3
# 기대: "OK"
```

### Group B — 사용자 Windows 실행 후 후속 agent turn

```bash
# 4. 결과 JSON 존재 + 540 trial 모두 기록
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import json
from pathlib import Path
results = sorted(Path('exp10_reproducibility_cost/results').glob('exp10_reproducibility_cost_*.json'))
assert results, 'no result JSON found'
latest = results[-1]
with open(latest) as f:
    data = json.load(f)
assert len(data['trials']) == 540, f\"expected 540 trials, got {len(data['trials'])}\"
print(f'OK {latest.name} has {len(data[\"trials\"])} trials')
"

# 5. report.md 생성 + 핵심 섹션 포함
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/results/exp10_report.md && \
grep -q "Q1. Reproducibility" /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/results/exp10_report.md && \
grep -q "Q2. Cost & Time" /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/results/exp10_report.md && \
echo "OK report.md has Q1+Q2 sections"

# 6. INDEX.md 메트릭 표 갱신 (TBD 가 실제 숫자로)
cd /Users/d9ng/privateProject/gemento/experiments && \
grep -E "gemma_8loop \| [0-9]" exp10_reproducibility_cost/INDEX.md && \
echo "OK INDEX.md metrics filled"

# 7. researchNotebook.md 에 Exp10 섹션 추가됨
cd /Users/d9ng/privateProject/gemento && \
grep -q "Exp10:" docs/reference/researchNotebook.md && \
grep -q "Reproducibility" docs/reference/researchNotebook.md && \
echo "OK researchNotebook.md has Exp10 section"
```

## Risks

- **사용자 Windows 환경 미준비**: OPENAI_API_KEY 없거나 LM Studio off. → trial dispatcher 의 `meter.error` 가 발생, 540 trial 모두 error 로 채워질 수 있음. analyze.py 가 error 카운트 표시 — 이상 발견 시 재실행 필요.
- **체크포인트 파일 손상**: 540 호출 중 IO 오류로 partial JSON 손상. fresh restart 필요. 비용·시간 손실. 사전 권고: 100 trial 마다 partial JSON 별도 백업.
- **LM Studio JSON mode 미지원** (task-03 risk 와 동일): `response_format` 거부 시 trial_gemma_1loop 결과 비신뢰. hotfix: response_format 빼기.
- **OpenAI 비용 폭주**: 9 task × 20 trial = 180 호출. 평균 input ~500 tokens, output ~200 tokens 가정 시 ~$0.03 정도. 1$ 초과 시 즉시 중단 권장 — Constraints 명시.
- **결과 파일 너무 큼**: 540 trial × ~2KB each = ~1MB. git 에 OK.
- **Exp10 결과가 "Externalization 한계" 보여줄 가능성**: gemma_8loop 가 Gemini 2.5 Flash 보다 못한 결과 나올 수도. 본 plan 은 "차별 자산을 비용·재현성 데이터로 답한다" 이므로 정확도 차이 자체가 핵심. 결과 방향 무관하게 가치.
- **researchNotebook.md 섹션 추가의 conflict 위험**: 동시에 다른 plan 이 노트북 갱신 중이면 conflict. 본 task 진행 중 다른 plan 동시 진행 금지.
- **사용자 환경 vs Mac 의 LM Studio endpoint 차이**: config.py 의 `API_BASE_URL = "http://yongseek.iptime.org:8005"` 가 Windows 환경에서 도달 가능한지 확인 필요. 도달 불가 시 LM Studio 서빙 주소 변경 또는 config.py 수정 (별도 task).

## Scope boundary

**Task 06 에서 절대 수정 금지**:

- `experiments/exp10_reproducibility_cost/__init__.py`, `tasks.py`, `run.py`, `analyze.py` — task-02·03·04 결과물 그대로.
- `experiments/_external/` — task-01 결과물 그대로.
- `experiments/run_experiment.py` — task-05 결과물 그대로.
- `experiments/INDEX.md` — task-05 결과물 그대로.
- `experiments/orchestrator.py`, `config.py`, `schema.py`, `system_prompt.py`, `measure.py`.
- `experiments/tests/test_static.py` — task-05 결과물 그대로.
- 다른 expXX/ 디렉토리.
- `experiments/tasks/taskset.json`.

**허용 범위**:

- `experiments/exp10_reproducibility_cost/results/*` 신규 (사용자 실행 후 자동 생성 + report.md).
- `experiments/exp10_reproducibility_cost/INDEX.md` 메트릭 표 부분만 수정 (TBD → 실제 값).
- `docs/reference/researchNotebook.md` 에 Exp10 섹션 추가 (다른 실험 섹션 손대지 않음).
