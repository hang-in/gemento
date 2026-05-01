---
type: plan-task
status: todo
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: D
depends_on: [03]
---

# Task 04 — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial

## Changed files

- `experiments/exp11_mixed_intelligence/results/exp11_baseline_abc.json` — **신규 출력** (사용자 실행)
- `experiments/exp11_mixed_intelligence/results/exp11_mixed_flash_judge.json` — **신규 출력**

신규 2 파일 (사용자 실행 결과). v2 (2026-05-02): condition 명 변경 (`mixed_haiku_judge` → `mixed_flash_judge`) — Anthropic Haiku 에서 Gemini Flash 로 전환.

## Change description

### 배경

본 task = **사용자 직접 실행** (메모리 정책 `feedback_agent_no_experiment_run.md`). Sonnet 직접 실행 금지.

### Step 1 — 사전 체크

```powershell
$env:GEMENTO_API_BASE_URL = "http://192.168.1.179:1234"
# GEMINI_API_KEY 는 이미 사용자 환경 (env 또는 gemento/.env 또는 secall/.env) 보유
# resolve_gemini_key() 가 자동 탐색

# 1a) Stage 2A + 2B + task-01/02/03 마감 검증
.\.venv\Scripts\python.exe -c "
from experiments.run_helpers import classify_trial_error, build_result_meta, parse_result_meta
from experiments.schema import FailureLabel
from experiments._external import resolve_gemini_key
from experiments._external.gemini_client import call_with_meter, DEFAULT_MODEL
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
assert 'c_caller' in sig.parameters, 'c_caller 인자 부재 — task-02 미마감'
assert resolve_gemini_key(), 'GEMINI_API_KEY 미발견'
print('ok: 모든 prerequisite 마감')
print(f'  GEMINI_FLASH_MODEL = {DEFAULT_MODEL}')
"

# 1b) lmstudio 서버 가용성
curl -s http://192.168.1.179:1234/v1/models | head -3

# 1c) Gemini API 가용성 (실제 호출, 짧은 prompt, ~\$0.0001)
.\.venv\Scripts\python.exe -c "
from experiments._external.gemini_client import call_with_meter
r = call_with_meter([{'role':'user','content':'Reply with just OK.'}], response_mime_type=None)
print(f'  text={r.raw_response!r}')
print(f'  tokens=in:{r.input_tokens} out:{r.output_tokens}')
print(f'  cost=\${r.cost_usd:.6f} err={r.error}')
assert not r.error, f'Gemini API fail: {r.error}'
"
```

위 3 모두 통과 시 Step 2 진행.

### Step 2 — 짧은 dry-run (1 task × 1 trial × 1 condition)

```powershell
# 2a) baseline_abc dry-run
.\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
  --conditions baseline_abc --trials 1 --max-cycles 8 `
  --out-name dryrun_baseline.json

# 2b) mixed_flash_judge dry-run (Gemini Flash 비용 ~\$0.001~0.003 예상)
.\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
  --conditions mixed_flash_judge --trials 1 --max-cycles 8 `
  --out-name dryrun_mixed.json
```

기대:
- 2a: cycles ≥ 1, tattoo_history len ≥ 2 (cycle-by-cycle 검증), Gemini 호출 0
- 2b: cycles ≥ 1, tattoo_history len ≥ 2, Gemini 호출 ≥ 1, flash_cost > 0

dry-run 통과 시 폐기 후 Step 3.

```powershell
Remove-Item experiments\exp11_mixed_intelligence\results\dryrun_baseline.json -ErrorAction SilentlyContinue
Remove-Item experiments\exp11_mixed_intelligence\results\dryrun_mixed.json -ErrorAction SilentlyContinue
Remove-Item experiments\exp11_mixed_intelligence\results\partial_*.json -ErrorAction SilentlyContinue
```

### Step 3 — 본 실행 (분할 권장)

**시간 예상**:
- baseline_abc: 15 task × 5 trial × 8 cycles × 3 model call (Gemma) ≈ 1800 model call. ABC trial 당 ~12 min → ~15 시간
- mixed_flash_judge: 15 task × 5 trial × 8 cycles × (Gemma 2 + Flash 1) ≈ 1800 call (Gemma 1200 + Flash 600). Flash API 빠름 (~수 초/call) → ~10 시간

총 ~25 시간. **분할 권장 (옵션 A)**:

```powershell
# 1) baseline_abc (~15h, 밤 동안)
.\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
  --conditions baseline_abc --trials 5 --max-cycles 8 `
  --out-name exp11_baseline_abc.json

# 2) mixed_flash_judge (~10h, 다음 시점)
.\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
  --conditions mixed_flash_judge --trials 5 --max-cycles 8 `
  --out-name exp11_mixed_flash_judge.json
```

또는 통합 실행:

```powershell
.\.venv\Scripts\python.exe -m experiments.exp11_mixed_intelligence.run `
  --conditions baseline_abc mixed_flash_judge --trials 5 --max-cycles 8 `
  --out-name exp11_full.json
```

### Step 4 — Gemini Flash 비용 모니터링

mixed condition 진행 중 누적 비용 stdout 확인:
- run.py 가 trial 별 `flash_cost` 출력
- 임계 (\$2+) 시 ctrl+C + 사용자 호출 — Architect 추정 (~\$0.18) 보다 10x 초과 시 비정상

**Architect 추정 총 비용**: 75 mixed trial × 평균 8 cycle × Gemini call 1/cycle × 평균 (input 2K + output 500) tok = 1.2M in + 0.3M out × (\$0.075 + \$0.30) per MTok ≈ **\$0.18**. 한도 여유 매우 큼.

### Step 5 — 결과 검증

```powershell
.\.venv\Scripts\python.exe -c "
import json, glob
for f in sorted(glob.glob('experiments/exp11_mixed_intelligence/results/exp11_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    print(f'{f}: trials={len(d[\"trials\"])}, schema={d.get(\"schema_version\")}')
    # flash_cost 합산 (mixed condition)
    flash_cost = sum((t.get('flash_cost') or {}).get('total_cost_usd', 0) for t in d['trials'])
    if flash_cost > 0:
        print(f'  total Flash cost: \${flash_cost:.4f}')
"
```

기대: 2 파일 (baseline 75 trial + mixed 75 trial), schema_version="1.0", mixed 의 총 Flash 비용 < \$1.

## Dependencies

- Stage 2A 마감 (helper)
- Stage 2B 마감 (FailureLabel)
- task-01 마감 (gemini_client 재사용 검증)
- task-02 마감 (run_abc_chain c_caller)
- task-03 마감 (run.py)
- 사용자: ANTHROPIC_API_KEY 발급 + 환경 변수 설정
- 모델 서버 (LM Studio + Google Gemini API) 가용성

## Verification

본 task 의 검증 = 결과 JSON schema + trial 수 + Flash 비용 임계 + condition aggregate. Step 5 의 명령 + 추가:

```powershell
# 1) trial 수 = 150 (75 + 75)
.\.venv\Scripts\python.exe -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp11_mixed_intelligence/results/exp11_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    total += len(d['trials'])
print(f'total trials: {total}')
assert total == 150, f'expected 150, got {total}'
"

# 2) condition 별 trial 수 = 75 each
.\.venv\Scripts\python.exe -c "
import json, glob
from collections import Counter
c = Counter()
for f in sorted(glob.glob('experiments/exp11_mixed_intelligence/results/exp11_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    for t in d['trials']: c[t['condition']] += 1
for cond, n in sorted(c.items()):
    print(f'  {cond:25} n={n}')
    assert n == 75
"

# 3) tattoo_history cycle-by-cycle 저장 검증 (Stage 2C 결함 fix 확인)
.\.venv\Scripts\python.exe -c "
import json, glob
for f in sorted(glob.glob('experiments/exp11_mixed_intelligence/results/exp11_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    multi_cycle = sum(1 for t in d['trials'] if (t.get('tattoo_history') or []) and len(t['tattoo_history']) >= 2)
    print(f'{f}: trials with cycle-by-cycle history >= 2 cycles: {multi_cycle}/{len(d[\"trials\"])}')
"
```

## Risks

- **Risk 1 — Gemini API 호출 fail (rate limit / network / quota)**: Stage 2A healthcheck/abort 패턴 — fatal classify 후 abort. 부분 결과 보존. Gemini Flash 의 free tier 또는 paid tier 한도 확인 권장
- **Risk 2 — 비용 임계 초과**: Step 4 의 모니터링. ctrl+C + 사용자 호출
- **Risk 3 — Flash 응답 schema mismatch (A/B 의 Tattoo JSON 과 호환 안 됨)**: dry-run 시 발견 → 즉시 사용자 호출. gemini_client 가 OpenAI 스타일 system 자동 분리하므로 호환 가능성 높음
- **Risk 4 — Sonnet 직접 실행 시도**: 본 task = 사용자 직접 실행. Sonnet 의 책임 = 명령 명세까지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 (`experiments/*.py`) — read-only
- 결과 JSON (본 task 의 신규 출력 외 모두 read-only)
- 분석 helper / 다른 plan / docs

## 사용자 호출 시점

- 분할 옵션 결정 (A 권장)
- API key 발급 / 환경 변수 설정
- dry-run 결과 검증
- fatal abort / 비용 임계 / schema mismatch 발생
- 본 실행 결과 받으면 task-05 진행 신호
