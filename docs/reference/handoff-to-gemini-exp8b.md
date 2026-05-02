---
type: reference
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-24
author: Architect Claude
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 8b — Tool-Use Refinement (에러 메시지 + Prompt 강화)

## 1. 목적

Exp08에서 발견된 2개 부작용을 완화한 뒤 재측정:

- Calculator `^` 혼동 (3 errors) → 에러 메시지에 `**` 힌트 추가
- Tool neglect (math-04 trial 2에서 tc=0으로 실패) → SYSTEM_PROMPT 강화

가설 H8:
- Calculator 성공률 50% → ≥85%
- Tool neglect 비율 20%(1/5) → 0%
- Tooluse arm 정답률 90% → ≥95%

## 2. 환경

- 파이썬: .venv (프로젝트 루트)
- 서버: http://yongseek.iptime.org:8005 (llama.cpp, gemma4-e4b, Q8_0)
- 추가 패키지: scipy, numpy (Exp08에서 이미 설치됨)

## 3. 사전 준비 (Exp08 진행 완료 가정)

```powershell
cd C:\path\to\gemento
git pull origin main

.\.venv\Scripts\Activate.ps1
# scipy, numpy 이미 설치된 경우 생략. 확인:
python -c "import scipy, numpy; print(scipy.__version__, numpy.__version__)"

# 서버 연결 확인
curl.exe -s http://yongseek.iptime.org:8005/v1/models
```

## 4. 실행 순서

### 4.1 본 실험 실행

```powershell
cd experiments
python run_experiment.py tool-use-refined
# 체크포인트 기능 있음 — 중단되어도 동일 명령으로 이어서 실행 가능.
# partial_tool_use_refined.json에 진행 상황 저장.
```

### 4.2 분석 보고서 생성 (UTF-8)

```powershell
python measure.py "results\exp08b_tool_use_refined_*.json" --markdown --output "results\exp08b_report.md"
# `--output` 옵션 필수 — PowerShell `>` 리다이렉트는 UTF-16 LE로 저장됨.
```

### 4.3 Exp08 대비 비교 (수동 확인)

보고서에서 다음 지표 확인:

- Tooluse arm accuracy — Exp08 0.90 대비 변화
- Calculator 성공률 — Exp08 0.50 대비 변화
- Tool Neglect Rate — Exp08에서는 측정 안 됐지만 이번 보고서에 신규 표시됨
- math-04 tooluse accuracy — Exp08 0.80 대비 변화

## 5. 결과 기록 및 커밋

```powershell
git add experiments\results\exp08b_tool_use_refined_*.json experiments\results\exp08b_report.md
git commit -m "feat: 실험 8b 결과 — Tool-Use Refinement 재측정"
git push origin main
```

## 6. 문제 발생 시

- 실행 중단 → `python run_experiment.py tool-use-refined` 재실행 (partial 자동 이어가기)
- tool_calls가 여전히 관측되지 않음 → `cycle_details[*].tool_calls`와 `a_error` 빈도 확인 보고
- calculator `BitXor` 에러가 여전히 많음 → Task 01이 반영됐는지 `git log` 확인
- math-04 tooluse accuracy가 오히려 하락 → Task 02 SYSTEM_PROMPT 변경이 다른 태스크에 역효과. 원시 데이터 송부 요청

## 7. 예상 소요 시간

- 40 runs × 평균 7 cycle × (A+B+C) + tool rounds
- 총 2~4시간 (Exp08과 유사)
