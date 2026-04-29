---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-readme-v2-abc-4-fail-v3-disclosure
parallel_group: B
depends_on: [01, 02]
---

# Task 03 — README 갱신 (한·영 동시)

## Changed files

- `README.md` — **수정** (영문 메인). "What I measured" 의 H 표 (line 30 부근) 에 Exp10 행 추가, "Headline numbers" (line 44 부근) 에 Exp10 결과 한 줄 추가, "Short-term" Roadmap (line 154 부근) 의 Exp10 candidate 항목 갱신.
- `README.ko.md` — **수정** (한국어). 영문 메인과 동일 사실 가리키도록 동기화.

신규 파일 0.

## Change description

### 배경

현 README 가 Exp09 까지 반영. Exp10 v2 final + v3 patch 결과는 `docs/reference/results/exp-10-reproducibility-cost.md` 와 `researchNotebook` 에는 반영됐으나 README (외부 노출 면) 에는 미반영. Reddit/r/LocalLLaMA 청중 대상 외부 문서이므로 정확성 + 신중한 톤 필수.

이전 plan (`readme-memento-acknowledgement`) 의 정책 준수:
- "Operating System" / "novel framework" / "AGI" 같은 과적재 명칭 금지
- 본 적 없는 외부 논문 인용 금지
- 한·영 같은 사실 가리킴
- Memento 메타포 + Nolan acknowledgement 보존

### Step 1 — H 표에 Exp10 행 추가 결정 (새 H 코드 vs H1 추가 evidence)

현 README.md 의 H 표 (line 30~42 부근):

```markdown
| **H1** | [Orchestrator externalization] Multi-step loops outperform single-pass reasoning | ✅ Supported (+44.4pp) | Exp02 v2 |
...
| **H9c** | [Error mode difference] ABC fails differently from Solo and RAG | ✅ Supported (...) | Exp09 |
```

Exp10 의 핵심 발견 = 동일 모델 1-loop → 8-loop 가 +37%p (0.413 → 0.781). 이는 **H1 (Multi-step loops outperform single-pass) 의 가장 강력한 추가 evidence**. 새 H 코드 부여보다 H1 의 evidence 컬럼 보강이 정직.

또 추가 발견: 4.5B 로컬 + ABC 가 Gemini 2.5 Flash 1-call 을 +19%p 능가 (cost $0). 이건 H4 (role separation 시너지) + H1 의 결합 결과. 이를 별도 행 (H10 또는 anchor 형태) 로 두기 보다는 본문 단락에서 강조.

**결정 (본 task 권고)**:
- H1 의 evidence 컬럼에 `Exp02 v2, Exp10 (1-loop→8-loop, +37%p)` 형태로 보강 추가
- 새 H 코드 부여 안 함 — 기존 가설 체계 유지

### Step 2 — `README.md` (영문) 갱신

기존 line 32 (H1 행):

```markdown
| **H1** | [Orchestrator externalization] Multi-step loops outperform single-pass reasoning | ✅ Supported (+44.4pp) | Exp02 v2 |
```

→ 변경:

```markdown
| **H1** | [Orchestrator externalization] Multi-step loops outperform single-pass reasoning | ✅ Supported (+44.4pp Exp02; +37pp Exp10) | Exp02 v2, Exp10 |
```

기존 "Headline numbers" 단락 (line 44-50 부근) 끝에 한 줄 추가:

```markdown
- Exp10: same Gemma 4 E4B model went from 41.3% (1-loop) to 78.1% (8-loop ABC) on a 9-task / 540-trial cost-aware comparison. The same ABC condition matched Gemini 2.5 Flash 1-call by +19pp (78.1% vs 59.1%) at zero per-trial API cost, trading off ~20× wall time.
```

기존 "Short-term" Roadmap (line 154 부근):

```markdown
| Short-term | Choose one Exp10 candidate: Small Paradox, parallel chunk traversal, or stronger statistics for Exp09 |
```

→ 변경:

```markdown
| Short-term | Exp10 (cost-aware reproducibility) completed — see `docs/reference/results/exp-10-reproducibility-cost.md`. Next candidates: math-* `use_tools=True` policy unification + v3 re-run, logic category multi-stage / tooling, scorer extension to Exp00–09 (low priority — logic-04 absent in those task subsets). |
```

### Step 3 — `README.ko.md` 갱신 (한국어)

영문 메인과 동일 사실 가리키도록 동기화:

H 표 H1 행:
- 한국어 README 의 해당 행 위치 확인 후 evidence 컬럼 동일 보강

"What I measured" 의 한국어 단락:
- 영문과 같은 Exp10 한 줄 추가 (4.5B 모델 1-loop 41.3% → 8-loop 78.1%, Gemini Flash 대비 +19%p, 비용 \$0, 시간 약 20×)

"Short-term" Roadmap 한국어 표기:
- "Exp10 (cost-aware reproducibility) 완료. 다음 후보: math-* use_tools 통일 + v3 재실행 / logic 카테고리 multi-stage / Exp00~09 채점 확장 (낮은 우선순위 — logic-04 미포함)"

### Step 4 — Task 01 결과 반영 (선택)

Task 01 의 v2 ABC 4 fail 사후 분석 결과가:
- 복구 가능 trial 발견 → README Roadmap 에 "ABC infrastructure 안정성 추가 patch 후 4 fail 사후 복구 가능" 한 줄 가능
- 모두 복구 불가 → README 본문에는 영향 없음 (내부 detail), Roadmap 에서 언급 안 함

본 plan 의 success 기준 측면에서 Step 4 는 선택. Task 01 결과가 외부 노출에 의미 있는 경우만 반영.

## Dependencies

- Task 01 결과: 4 fail 사후 분석 결정 (Step 4 의 입력)
- Task 02 결과: v3 적용 범위 disclosure (Roadmap 의 "scorer extension to Exp00–09" 우선순위 표기 입력)
- 패키지: 없음 (마크다운 편집)

## Verification

```bash
# 1) README.md 의 H1 행에 Exp10 추가 확인
grep "^\| \*\*H1\*\*" README.md
# 기대: 'Exp02 v2, Exp10' 포함

# 2) 영문/한국어 README 둘 다 Exp10 결과 한 줄 보유
grep -c "78.1\|0.781\|41.3\|0.413\|+19pp\|+19%p" README.md README.ko.md
# 기대: 양쪽 1+ 라인

# 3) Roadmap 의 'Choose one Exp10 candidate' 가 갱신됨 (완료 표시 + 다음 후보)
grep -E "Choose one Exp10 candidate|use_tools|multi-stage" README.md README.ko.md
# 기대: Exp10 candidate 미존재 (제거됨), use_tools/multi-stage 포함

# 4) 한·영 동기화 — 핵심 사실 (Exp10 결과 수치) 양쪽 일치
.venv/bin/python -c "
import re
en = open('README.md').read()
ko = open('README.ko.md').read()
# Exp10 핵심 수치 셋 (78.1, 41.3, 19) 양쪽 모두 등장 확인
for n in ('78.1', '41.3'):
    assert n in en, f'README.md missing {n}'
    assert n in ko, f'README.ko.md missing {n}'
print('한·영 핵심 수치 동기화 ok')
"

# 5) 외부 노출 톤 검사 — 금지 명칭 미사용
.venv/bin/python -c "
import re
banned = (r'\bOperating System\b', r'\bnovel framework\b', r'\bAGI\b')
for path in ('README.md', 'README.ko.md'):
    text = open(path).read()
    for pat in banned:
        if re.search(pat, text):
            print(f'{path}: banned term {pat} found')
            raise SystemExit(1)
print('금지 명칭 검사 ok')
"
```

5 명령 모두 정상 + assertion 통과.

## Risks

- **H 표 라인 카운트 변동**: 새 H 코드 부여 안 함 + H1 행만 evidence 보강이라 표 크기/형태 영향 없음
- **한·영 동기화 실수**: 한쪽만 갱신 시 차이 발생. Verification 4 의 핵심 수치 일치 검증 + 사용자 시각 검토
- **외부 노출 톤**: 과적재 명칭/논문 인용 우발 위험. Verification 5 의 정규식 검사 + 단락 추가 시 Reddit 청중 시각으로 1차 자체 검토
- **Roadmap 의 다음 후보 선택**: "math use_tools 통일 + v3 재실행" 과 "logic multi-stage" 둘 다 미정. README 에서 "candidates" 복수 형태로 표기하여 우선순위 강제 안 함
- **README.ko.md 의 위치 일관성**: 한국어 파일의 H 표 / Headline / Roadmap 위치가 영문과 다를 수 있음 — 변경 전 grep 으로 위치 확인 후 진행

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `docs/reference/results/exp-10-reproducibility-cost.md` — Task 02 영역
- `docs/reference/researchNotebook.md` / `.en.md` — Task 02 영역 + 직전 plan 결과
- `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` — Task 01 영역
- `experiments/` 디렉토리 전체 — 직전 plan + Task 01 영역
- `docs/plans/` 의 다른 plan 문서 — 본 plan 외 변경 0
- 외부 링크 / 이미지 / 다이어그램 — 본 plan 범위 밖
