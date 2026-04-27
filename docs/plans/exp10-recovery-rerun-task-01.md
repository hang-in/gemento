---
type: plan-task
status: todo
updated_at: 2026-04-27
parent_plan: exp10-recovery-rerun
parallel_group: A
depends_on: []
---

# Task 01 — Exp10 복구: run.py 복원 및 재실행 (Windows, Codex)

## Context

Exp10 첫 실행(2026-04-27 01:34:21) 결과 540건 중 360건이 null (invalid):
- gemma_8loop: 180건 유효 (정상)
- gemma_1loop: 180건 null (함수 미반환)
- gemini_flash_1call: 180건 null (함수 미반환)

근본 원인: Windows 로컬 `run.py` 손상 — `trial_gemma_1loop()` (line ~117)과 `trial_gemini_flash()` (line ~149)에서 return 블록이 제거되어 있음.

Mac 버전 확인 완료: `run.py` 정상 상태 (return 블록 양호).

## Recovery Plan

Codex (Windows) 가 수행할 작업:

### Step 1 — 현재 상태 검증 (Windows PowerShell)

```powershell
cd C:\Users\<username>\path\to\gemento  # 또는 적절한 경로
git status
git diff experiments/exp10_reproducibility_cost/run.py | head -20
```

예상: `trial_gemma_1loop()` 와 `trial_gemini_flash()` 함수 본체가 불완전해 보임.

### Step 2 — run.py 복원

```powershell
git checkout origin/main -- experiments/exp10_reproducibility_cost/run.py
```

검증:
```powershell
git diff experiments/exp10_reproducibility_cost/run.py
```

예상: 0 lines changed (즉, 파일이 현재 working tree 상태와 동일하면 no diff).

### Step 3 — 부분 체크포인트 제거

```powershell
rm experiments/exp10_reproducibility_cost/results/partial_exp10_reproducibility_cost.json
```

확인:
```powershell
ls experiments/exp10_reproducibility_cost/results/
```

예상: 오직 구 결과 파일(exp10_reproducibility_cost_20260427_*.json)만 남음.

### Step 4 — 작업 트리 clean 확인

```powershell
git status
```

예상 출력:
```
On branch main
nothing to commit, working tree clean
```

**이 상태 확인 후에만 재실행 진행.**

### Step 5 — Exp10 재실행 (약 2-3시간)

```powershell
cd C:\Users\<username>\path\to\gemento
..\.venv\Scripts\python experiments/exp10_reproducibility_cost/run.py --trials 20
```

진행 상황 모니터링:
- 첫 출력: `[1/540] gemma_8loop | math-01 | trial 1`
- 진행: `[2/540]`, `[3/540]`, ..., `[540/540]`
- 완료: `→ Result saved: experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json`

**중단되면 안 됨**: Keyboard interrupt (Ctrl+C) 시 partial checkpoint 보존 — Architect 에 알리면 `--resume` 방식으로 이어하기 가능 (현재 `run.py` 에 구현됨).

## Post-execution Validation (Codex)

실행 완료 후:

### 1️⃣ 결과 JSON 유효성 검증

```powershell
cd C:\Users\<username>\path\to\gemento
python -c "
import json
import os
from pathlib import Path

# 최신 결과 파일 찾기
results_dir = Path('experiments/exp10_reproducibility_cost/results')
result_files = list(results_dir.glob('exp10_reproducibility_cost_*.json'))
if not result_files:
    print('ERROR: No result file found')
    exit(1)
result_file = max(result_files, key=lambda p: p.stat().st_mtime)

with open(result_file) as f:
    data = json.load(f)

trials = data['trials']
valid = sum(1 for t in trials if t['final_answer'] is not None)
null_count = len(trials) - valid

print(f'Total: {len(trials)}, Valid: {valid}, Null: {null_count}')
if null_count == 0:
    print('✓ ALL TRIALS VALID')
else:
    print(f'✗ {null_count} trials still null — FAILURE')
    exit(1)
"
```

예상: `Total: 540, Valid: 540, Null: 0` + `✓ ALL TRIALS VALID`

**0 이 아니면 중단하고 Architect 에 보고.**

### 2️⃣ 샘플 accuracy sanity check

```powershell
python -c "
import json
from pathlib import Path
from statistics import mean

results_dir = Path('experiments/exp10_reproducibility_cost/results')
result_files = list(results_dir.glob('exp10_reproducibility_cost_*.json'))
result_file = max(result_files, key=lambda p: p.stat().st_mtime)

with open(result_file) as f:
    data = json.load(f)

for cond in ['gemma_8loop', 'gemma_1loop', 'gemini_flash_1call']:
    trials = [t for t in data['trials'] if t['condition'] == cond]
    if not trials:
        print(f'{cond}: (no trials)')
        continue
    acc = mean(t['accuracy'] for t in trials if t['accuracy'] is not None)
    print(f'{cond}: {acc:.4f} (N={len(trials)})')
"
```

예상 범위 (참고용 — 절대값 아님):
- gemma_8loop: ~0.25–0.70 (Korean penalty 있음)
- gemma_1loop: ~0.20–0.65
- gemini_flash_1call: ~0.60–0.85 (일반적으로 더 높음)

**극단적 이상(0.0 또는 1.0 반복, NaN 등)이 보이면 Architect 에 보고.**

### 3️⃣ 파일 목록 최종 확인

```powershell
ls experiments/exp10_reproducibility_cost/results/
```

예상:
- `exp10_reproducibility_cost_20260427_*.json` (구 invalid 파일 — 삭제해도 됨)
- `exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json` (신규 valid 파일)
- `partial_exp10_reproducibility_cost.json` 은 없어야 함

## Completion Criteria

✅ 모두 만족할 때 Task 01 완료:

1. ✅ `git checkout origin/main -- experiments/exp10_reproducibility_cost/run.py` 성공
2. ✅ `git status` → `nothing to commit, working tree clean`
3. ✅ `partial_*` 체크포인트 파일 제거됨
4. ✅ 540 trials 전부 valid (null=0)
5. ✅ 3 condition 평균 accuracy 모두 유효한 숫자 (NaN 아님)
6. ✅ 신규 result JSON 파일 생성됨

## Abort Conditions

❌ 다음 중 하나 발생 시 **STOP** 및 Architect 통보:

- `git checkout` 명령 실패 (conflict 등)
- `git status` 에서 uncommitted changes 남음 (checkout 실패)
- 540 trials 중 일부가 여전히 null
- final_answer 가 null 인 trials 가 많음 (비정상)
- API 인증 오류 (Gemini key / LM Studio 연결 불가)
- 디스크 공간 부족 (결과 파일 저장 불가)
- Python 호환성 오류

## Handoff Documents

관련 문서:
- `docs/reference/handoff-to-opus-exp10-2026-04-27.md` — Codex 의 Exp10 invalidity 분석
- `docs/reference/handoff-from-opus-exp10-recovery-2026-04-27.md` — Architect 의 복구 전 체크리스트

## Dependencies

- `origin/main` branch 가 Mac 에서 최신 (run.py clean)
- Windows 로컬 `.venv` 가 기능함 (python, httpx, 기타 의존성)
- Gemini API key 및 LM Studio 가 이전처럼 구성됨
