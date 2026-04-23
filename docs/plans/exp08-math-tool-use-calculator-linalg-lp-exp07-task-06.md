---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: D
depends_on: [04]
---

# Task 06 — Gemini 핸드오프 문서

## Changed files

- `docs/reference/handoff-to-gemini-exp8.md` — **신규**. 정식 핸드오프 문서 (환경/설정/실행/결과 기록).
- `docs/prompts/2026-04-24/run-exp8.md` — **신규**. Gemini가 Windows 세션에서 복붙할 단일 프롬프트.
- `docs/reference/index.md` (있을 경우만): 새 핸드오프 문서 링크 1줄 추가.
- `docs/prompts/2026-04-21/resume-exp7-gemini.md` (있을 경우): Exp07 완주 후 후속 포인터 1줄 추가 고려 — **선택**.

## Change description

### 1. `docs/reference/handoff-to-gemini-exp8.md`

기존 `handoff-to-gemini-exp7.md`, `handoff-to-gemini-exp5b.md` 구조를 템플릿으로 사용. 섹션 구성:

```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-24
author: Architect Claude
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 8 — Math Tool-Use (calculator + linalg + linprog)

## 1. 목적
E4B의 수학 계산 한계(특히 math-04 LP 50% 정체)를 외부 도구로 돌파하는지 검증.
가설 H7: math 태스크 평균 정답률이 +15%p 이상 상승, math-04는 50% → ≥80%.

## 2. 환경
- 파이썬: .venv (프로젝트 루트)
- 서버: http://yongseek.iptime.org:8005 (llama.cpp, gemma4-e4b, Q8_0)
- 추가 패키지: scipy, numpy  ← pip 설치 필요

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
# 기대: "SMOKE TEST PASSED: math-04 answer=..., tool_calls=..."
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
# 결과 파일 중 최신 파일 찾기 (PowerShell glob은 Python 측이 처리)
python measure.py "results\exp08_tool_use_*.json" --markdown --output "results\exp08_report.md"
# `--output` 옵션을 반드시 사용 — PowerShell `>` 리다이렉트는 UTF-16 LE로 저장됨
```

## 5. 결과 기록 및 커밋
```powershell
git add experiments\results\exp08_tool_use_*.json experiments\results\exp08_report.md
git commit -m "feat: 실험 8 결과 — Math Tool-Use 측정"
git push origin main
```

## 6. 문제 발생 시
- smoke test 실패 → `tools\smoke_test.py` 출력 전체 복사하여 보고.
- tool_calls이 한 번도 관측되지 않음 → `experiments\results\exp08_*.json`에서 `total_tool_calls` 합 확인. 0이면 SYSTEM_PROMPT의 tool-use 섹션이 제대로 적용되지 않은 것.
- 수렴률 급락 (< 80%) → response_format 해제(tools 사용 시)로 JSON 파싱 실패 가능성. `cycle_details[*].a_error`, `b_error`에서 "JSON parse failed" 빈도 확인.

## 7. 예상 소요 시간
- 40 runs × 평균 7 cycle × (A+B+C) ≈ 840 모델 호출.
- tool round 포함 시 tooluse arm은 1.5~2배. 총 2~4시간 예상 (서버 상태에 따라).
```

### 2. `docs/prompts/2026-04-24/run-exp8.md`

Gemini가 자신의 세션에 복붙할 단일 프롬프트 — `resume-exp7-gemini.md` 패턴 재사용. 내용 요약:

- 역할: "제멘토 실험 8 runner"
- 참조 문서: `docs/reference/handoff-to-gemini-exp8.md` 먼저 읽을 것
- 작업 순서: Section 3 → 4.1 → 4.2 → 4.3 → 5 단계적 실행, 각 단계 결과 사용자에게 확인
- 실패 시: 4.1 smoke 실패하면 중단·보고, 그 외 에러는 로그 원문 전달
- 한국어로 진행 보고, 코드/경로/명령어는 원문 유지

### 3. `docs/reference/index.md` (있으면 1줄 추가)

```markdown
- [handoff-to-gemini-exp8.md](handoff-to-gemini-exp8.md) — 실험 8 Gemini 핸드오프 (Math Tool-Use)
```

파일이 없으면 **생성하지 말고 건너뛴다** (범위 외).

## Dependencies

- **Task 04 완료**: `run_experiment.py`에 `tool-use` 커맨드가 실제로 동작해야 핸드오프 지시가 유효.
- **Task 01 완료**: `--output` 옵션이 있어야 Section 4.3의 UTF-8 기록 절차가 작동.
- 외부 패키지 추가 없음 (핸드오프는 문서만).

## Verification

```bash
# 1. 핸드오프 문서 생성 확인
test -f docs/reference/handoff-to-gemini-exp8.md && echo "handoff: OK"
# 기대: "handoff: OK"

# 2. 프롬프트 문서 생성 확인
test -f docs/prompts/2026-04-24/run-exp8.md && echo "prompt: OK"
# 기대: "prompt: OK"

# 3. 핵심 키워드 포함 확인
grep -E "tool-use|linprog|smoke_test|--output" docs/reference/handoff-to-gemini-exp8.md | wc -l
# 기대: 4 이상

# 4. 명령어 무결성 — 핸드오프 문서 내 실행 명령이 실제 등록된 커맨드와 일치
grep -c "run_experiment.py tool-use" docs/reference/handoff-to-gemini-exp8.md
# 기대: 1 이상

# 5. (선택) 인덱스 파일이 있을 경우 링크 추가 확인
if [ -f docs/reference/index.md ]; then
  grep -c "handoff-to-gemini-exp8" docs/reference/index.md
fi
# 기대: 있으면 1, 없으면 출력 없음 (둘 다 허용)

# 6. 프롬프트가 실제 핸드오프 문서를 참조하는지
grep -c "handoff-to-gemini-exp8" docs/prompts/2026-04-24/run-exp8.md
# 기대: 1 이상
```

## Risks

- **복붙 시 PowerShell 경로 구분자**: 핸드오프 문서 안의 경로는 Windows 스타일(`\`) 사용. macOS/Linux에서 예제 실행 시 실패 — Windows 전용 문서임을 명시.
- **pip install 권한**: 사용자 환경이 venv 활성화 안 된 상태이면 system Python에 설치될 수 있음. 문서에서 `.venv\Scripts\Activate.ps1`를 먼저 호출하도록 강조.
- **인덱스 파일 오인**: `docs/reference/index.md`가 존재하는지 먼저 확인. 없으면 생성 금지 (Task 범위 외).
- **smoke_test 경로**: Task 07에서 생성되는 `experiments/tools/smoke_test.py`를 참조. Task 07 지연 시 핸드오프 문서는 작성 가능하나 실행은 대기.

## Scope boundary

**Task 06에서 절대 수정 금지**:
- `experiments/` 하위 모든 코드 파일 (다른 Task 영역)
- 기존 reference 문서 본문 (handoff-to-gemini-exp7*.md 등) — 본 Task는 신규 문서만 작성
- `docs/plans/` 하위 다른 plan/task 파일

**허용 범위**:
- 신규: `docs/reference/handoff-to-gemini-exp8.md`, `docs/prompts/2026-04-24/run-exp8.md`
- 조건부: `docs/reference/index.md`에 1줄 link 추가 (파일 존재 시에만)
