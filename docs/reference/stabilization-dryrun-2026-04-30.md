---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# Stage 2A 통합 dry-run 결과 (2026-04-30)

**Plan**: `stabilization-healthcheck-abort-meta-pre-exp11`

## 1a — 정상 path 실행 확인

명령:
```powershell
# exp00_baseline 은 __main__ 블록 없음 → -c 방식으로 실행
$env:GEMENTO_API_BASE_URL = "http://192.168.1.179:1234"
.\.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, 'experiments')
from exp00_baseline.run import run; run()
"
```

결과:
```
[Baseline] Task: math-01 — 주어진 수학 문제를 단계적으로 풀어라.
  Trial 1: 13783ms  Trial 2: 13791ms  Trial 3: 13638ms  Trial 4: 12917ms  Trial 5: 13764ms
  → Result saved: experiments/exp00_baseline/results/exp00_baseline_20260430_171428.json
TOP-LEVEL KEYS: ['experiment', 'model', 'results']
schema_version: (absent)
experiment: baseline
model: gemma4-e4b
```

**gap**: `schema_version="1.0"` 미출력 — exp00 save 호출에 `build_result_meta` 미적용.
신규 실험(Exp11+)에만 적용 예정이므로 기존 실험 retroactive 보강은 의도적으로 배제.

## 1b — healthcheck abort (fatal error path)

명령:
```powershell
$env:GEMENTO_API_BASE_URL = "http://localhost:9999"
.\.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, 'experiments')
from exp00_baseline.run import run; run()
"
```

결과:
```
[Baseline] Task: math-01 — 주어진 수학 문제를 단계적으로 풀어라.
  Trial 1: 4370ms
[ABORT] task=math-01 trial=0 fatal=connection_error: [WinError 10061] 대상 컴퓨터에서 연결을 거부했으므로 연결하지 못했습니다
[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.
[REJECT] error 비율 100.0% ≥ 30%. 저장 거부 + warning
[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고
EXIT_CODE: 1
```

**판정**: ✓ connection_error → abort → rate_check → reject → SystemExit(1) 전 경로 정상 동작

## 1c — error 비율 검사 단위 테스트

명령:
```powershell
.\.venv\Scripts\python.exe -c "
from experiments.run_helpers import check_error_rate
trials = (
    [{'error': '[WinError 10061] connection refused', 'final_answer': None}] * 5
    + [{'error': None, 'final_answer': 'ok'}] * 5
)
ok, rate = check_error_rate(trials, threshold=0.30)
assert not ok, f'expected reject, got ok with rate={rate}'
assert abs(rate - 0.5) < 0.01
print('check 1c ok: error rate 50% rejected')
"
```

결과:
```
check 1c ok: error rate 50% rejected
```

**판정**: ✓ error_rate 50% → reject 정상

## 1d — backward-compat 회귀

명령:
```powershell
.\.venv\Scripts\python.exe -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.\.venv\Scripts\python.exe -m experiments.exp10_reproducibility_cost.rescore_v3
```

| 명령 | 변경 전 출력 (직전 plan commit) | 변경 후 출력 (본 plan) | 동일 여부 |
|------|--------------------------------|------------------------|----------|
| analyze_5trial_drop --arm abc_tattoo | early mean=0.8833, late mean=0.0000, Δ=-0.8833 | 동일 | ✓ 동일 |
| rescore_v3 | gemma_8loop v3=0.7833, gemma_1loop v3=0.4148, gemini_flash v3=0.5926 | 동일 | ✓ 동일 |

**판정**: ✓ 회귀 없음

## 결정

**ok** — 1b/1c/1d 전 항목 정상. 1a gap(schema_version 미출력)은 의도된 설계 범위:
- `resultJsonSchema.md` 기준: 기존 Exp00~10 retroactive 보강 명시 배제
- Exp11+ 신규 실험부터 `build_result_meta` 적용

Stage 2A plan 완료. Exp11 진행 가능 상태.

## 사용 명령 archive

위 1a~1d 명령 그대로. 실행 환경: Windows 11, LM Studio `http://192.168.1.179:1234` (gemma-4-e4b), 2026-04-30.
