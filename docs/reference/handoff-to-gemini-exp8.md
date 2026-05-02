---
type: reference
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-24
author: Architect Claude
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 8 — Math Tool-Use (calculator + linalg + linprog)

## 1. 목적

E4B의 수학 계산 한계(특히 math-04 LP 50% 정체)를 외부 도구로 돌파하는지 검증.
가설 H7: math 태스크 평균 정답률이 +15%p 이상 상승, math-04는 50% → ≥80%.

## 2. 환경

- 파이썬: `.venv` (프로젝트 루트)
- 서버: `http://yongseek.iptime.org:8005` (llama.cpp, gemma4-e4b, Q8_0)
- 추가 패키지: `scipy`, `numpy` ← pip 설치 필요

## 3. 사전 준비 (1회)

```powershell
cd C:\path\to\gemento
.\.venv\Scripts\Activate.ps1
pip install scipy numpy

# 서버 연결 확인
curl.exe -s http://yongseek.iptime.org:8005/v1/models
```

## 4. 실행 순서

### 4.1 로컬 smoke test (실험 착수 전 관문)

```powershell
cd experiments
python tools\smoke_test.py
# 기대: "SMOKE TEST PASSED: tool_calls=N, answer_close=True"
# 실패 시: 실험 중단, 핸드오프 문서 업데이트 후 Architect에게 보고
```

### 4.2 본 실험 실행

```powershell
cd experiments
python run_experiment.py tool-use
# 체크포인트 기능 있음 — 중단되어도 동일 명령으로 이어서 실행 가능
```

### 4.3 분석 보고서 생성 (UTF-8)

```powershell
python measure.py "results\exp08_tool_use_*.json" --markdown --output "results\exp08_report.md"
# --output 옵션을 반드시 사용 — PowerShell > 리다이렉트는 UTF-16 LE로 저장됨
```

## 5. 결과 기록 및 커밋

```powershell
git add experiments\results\exp08_tool_use_*.json experiments\results\exp08_report.md
git commit -m "feat: 실험 8 결과 — Math Tool-Use 측정"
git push origin main
```

## 6. 문제 발생 시

- **smoke test 실패** → `tools\smoke_test.py` 출력 전체 복사하여 보고.
- **tool_calls이 한 번도 관측되지 않음** → `experiments\results\exp08_*.json`에서 `total_tool_calls` 합 확인. 0이면 SYSTEM_PROMPT의 tool-use 섹션이 제대로 적용되지 않은 것.
- **수렴률 급락 (< 80%)** → response_format 해제(tools 사용 시)로 JSON 파싱 실패 가능성. `cycle_details[*].a_error`, `b_error`에서 "JSON parse failed" 빈도 확인.

## 7. 예상 소요 시간

- 40 runs × 평균 7 cycle × (A+B+C) ≈ 840 모델 호출.
- tool round 포함 시 tooluse arm은 1.5~2배. 총 2~4시간 예상 (서버 상태에 따라).
