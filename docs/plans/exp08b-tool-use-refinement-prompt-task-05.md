---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08b-tool-use-refinement-prompt
parallel_group: C
depends_on: [03]
---

# Task 05 — Gemini 핸드오프 문서

## Changed files

- `docs/reference/handoff-to-gemini-exp8b.md` — **신규**. 정식 핸드오프 문서.
- `docs/prompts/2026-04-24/run-exp8b.md` — **신규**. Gemini 세션 복붙용 단일 프롬프트.
- `docs/reference/index.md` — **조건부**. 파일이 존재할 경우만 새 핸드오프 링크 1줄 추가.

## Change description

### 1. `docs/reference/handoff-to-gemini-exp8b.md` 신설

템플릿은 `docs/reference/handoff-to-gemini-exp8.md` 재사용. 섹션 구성:

```markdown
---
type: reference
status: in_progress
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
```

### 2. `docs/prompts/2026-04-24/run-exp8b.md` 신설

Gemini가 자신의 세션에 복붙할 단일 프롬프트. `docs/prompts/2026-04-24/run-exp8.md` 패턴 재사용:

```markdown
---
type: prompt
status: draft
updated_at: 2026-04-24
recipient: Gemini CLI (Windows)
---

# Exp08b 실행 프롬프트

당신은 제멘토 실험 8b runner입니다.

## 참조 문서
먼저 `docs/reference/handoff-to-gemini-exp8b.md`를 읽어 전체 맥락을 파악하세요.

## 작업 순서
1. Section 3 (사전 준비) 실행
2. Section 4.1 (본 실험) 실행 — 완료까지 대기
3. Section 4.2 (분석 보고서) 실행
4. Section 4.3 (Exp08 대비 비교) 수동 확인 — 결과를 사용자에게 보고
5. Section 5 (커밋·푸시)

## 중단/실패 대응
- 실행 중단 시 재실행으로 이어가기
- 에러 발생 시 Section 6 참조, 로그 원문을 사용자에게 전달

## 보고 언어
- 한국어로 진행 상황 보고.
- 코드·경로·명령어·지표명은 원문 그대로 유지.
```

### 3. `docs/reference/index.md` 조건부 업데이트

파일이 존재할 경우만 다음 1줄 append:

```markdown
- [handoff-to-gemini-exp8b.md](handoff-to-gemini-exp8b.md) — 실험 8b Gemini 핸드오프 (Tool-Use Refinement)
```

파일 부재 시 **생성하지 않음** (범위 외).

## Dependencies

- **Task 03 완료**: `tool-use-refined` 커맨드가 실제로 동작해야 핸드오프 지시가 유효.
- **Task 01, 02 완료**: calculator·prompt 개선이 반영된 상태에서만 실험 의미. 핸드오프 문서 작성은 03 완료 후.
- 외부 패키지 추가 없음 (문서만).

## Verification

```bash
# 1. 핸드오프 문서 생성 확인
test -f docs/reference/handoff-to-gemini-exp8b.md && echo "handoff: OK"
# 기대: "handoff: OK"

# 2. 프롬프트 문서 생성 확인
test -f docs/prompts/2026-04-24/run-exp8b.md && echo "prompt: OK"
# 기대: "prompt: OK"

# 3. 핵심 키워드 포함 확인
grep -cE "tool-use-refined|tool_neglect_rate|--output|Exp08 대비" docs/reference/handoff-to-gemini-exp8b.md
# 기대: 3 이상

# 4. 명령어 무결성 — 핸드오프 문서 내 커맨드가 실제 등록된 커맨드와 일치
grep -c "run_experiment.py tool-use-refined" docs/reference/handoff-to-gemini-exp8b.md
# 기대: 1 이상

# 5. 프롬프트가 실제 핸드오프 문서를 참조
grep -c "handoff-to-gemini-exp8b" docs/prompts/2026-04-24/run-exp8b.md
# 기대: 1 이상

# 6. (조건부) 인덱스 파일이 있으면 링크 추가
if [ -f docs/reference/index.md ]; then
  grep -c "handoff-to-gemini-exp8b" docs/reference/index.md
fi
# 기대: 있으면 1, 없으면 출력 없음 (둘 다 허용)
```

## Risks

- **복붙 시 PowerShell 경로 구분자**: 문서 내 경로는 Windows 스타일(`\`). macOS/Linux에서 예제 실행 시 실패 — Windows 전용 문서임을 Section 2에서 명시.
- **인덱스 파일 오인**: `docs/reference/index.md`가 존재하는지 `test -f`로 먼저 확인. 없으면 생성 금지 (Task 범위 외).
- **Task 03 의존**: Task 03이 늦으면 Gemini가 `tool-use-refined` 커맨드 실행 시 KeyError. Task 03이 반드시 먼저 병합되어야 함.
- **Gemini 해석 일관성**: 이전 Exp07, Exp08 핸드오프와 동일 패턴을 유지 — 학습 곡선 최소화.

## Scope boundary

**Task 05에서 절대 수정 금지**:
- `experiments/` 하위 모든 코드 파일 (다른 Task 영역)
- 기존 `docs/reference/handoff-to-gemini-exp7*.md`, `handoff-to-gemini-exp8*.md` 본문 — 본 Task는 신규 문서만.
- `docs/plans/` 하위 다른 plan/task 파일.
- `docs/prompts/` 하위의 다른 날짜 폴더.

**허용 범위**:
- 신규: `docs/reference/handoff-to-gemini-exp8b.md`, `docs/prompts/2026-04-24/run-exp8b.md`
- 조건부: `docs/reference/index.md`에 1줄 link 추가 (파일 존재 시에만)
