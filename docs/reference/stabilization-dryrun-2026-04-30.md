---
type: reference
status: in_progress
updated_at: 2026-04-30
canonical: true
---

# Stage 2A 통합 dry-run 결과 (2026-04-30)

**Plan**: `stabilization-healthcheck-abort-meta-pre-exp11`

## 1a — schema_version="1.0" 출력 (정상 path)

명령:
```powershell
.\.venv\Scripts\python.exe -m experiments.exp00_baseline.run
```

결과: <FILL — 출력 JSON 의 top-level 키 목록 + meta 값>

## 1b — healthcheck abort (fatal error path)

명령:
```powershell
$env:LM_STUDIO_BASE = "http://localhost:9999"
.\.venv\Scripts\python.exe -m experiments.exp00_baseline.run
```

> **참고**: exp00_baseline 은 `call_model` 을 import. 환경 변수 우회가 동작하지 않으면 `config.py` 의 BASE_URL 또는 orchestrator 의 endpoint 참조 경로 확인 후 무효 endpoint 로 교체.

결과: <FILL — stdout 의 [ABORT] 라인 + exit code>

## 1c — error 비율 검사 단위 테스트

명령:
```powershell
.\.venv\Scripts\python.exe -c @"
from experiments.run_helpers import check_error_rate
trials = (
    [{'error': '[WinError 10061] connection refused', 'final_answer': None}] * 5
    + [{'error': None, 'final_answer': 'ok'}] * 5
)
ok, rate = check_error_rate(trials, threshold=0.30)
assert not ok, f'expected reject, got ok with rate={rate}'
assert abs(rate - 0.5) < 0.01
print('check 1c ok: error rate 50% rejected')
"@
```

결과: <FILL — `check 1c ok` 출력 또는 실패 사유>

## 1d — backward-compat 회귀

명령:
```powershell
.\.venv\Scripts\python.exe -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.\.venv\Scripts\python.exe -m experiments.exp10_reproducibility_cost.rescore_v3
```

| 명령 | 변경 전 출력 (직전 plan commit) | 변경 후 출력 (본 plan) | 동일 여부 |
|------|--------------------------------|------------------------|----------|
| analyze_5trial_drop --arm abc_tattoo | <FILL> | <FILL> | <FILL> |
| rescore_v3 | <FILL — condition aggregate> | <FILL> | <FILL> |

## 결정

<FILL — ok / 회귀 발견 여부>

## 사용 명령 archive

(위 1a~1d 명령 그대로 + 결과 raw 출력 일부를 사용자가 채움)
