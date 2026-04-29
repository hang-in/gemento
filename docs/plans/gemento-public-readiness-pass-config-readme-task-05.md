---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: B
depends_on: [04]
---

# Task 05 — README "What this is / is not" 박스 한·영 추가 + 직전 reviewer finding 해결

## Changed files

- `README.md` — **수정**. Core idea 섹션 전후 (line 13~22 부근) 에 "What this is / is not" 박스 신규 추가.
- `README.ko.md` — **수정**. 한국어 동기화 — 동일 사실의 박스 추가 + line 146 의 Exp10 bullet 끝에 4 trial JSON parse fail / early-stop disclosure 한 줄 추가 (직전 reviewer finding 해결, Task 03 한·영 동기화 계약 충족).

신규 파일 0.

## Change description

### 배경 1 — "What this is / is not" 박스 부재

README 첫인상에서 과장 리스크 제거 필요. 사용자 정책 명시:
- "ABC+Tattoo universally beats RAG" 명시 부정
- 4B 모델이 frontier 모델 대체 주장 부정
- 새 모델 architecture / 학습 방법 부정

### 배경 2 — 직전 reviewer finding (한·영 동기화 미충족)

직전 plan (`exp10-readme-v2-abc-4-fail-v3-disclosure`) 의 Task 03 의 계약: "한·영 README 가 같은 사실 가리킴". 그러나:
- `README.md:51` Headline 단락에 "ABC infrastructure had 4 trial-level JSON parse fails (early-stop pattern, see docs/reference/exp10-v3-abc-json-fail-diagnosis.md)" 추가됨
- `README.ko.md:146` Exp10 bullet 끝은 "비용 \$0, 시간은 약 20× (8min vs 24s)." — 4 fail / early-stop disclosure 누락

→ Task 03 한·영 동기화 미충족. reviewer finding 정당. 본 Task 05 에서 함께 해결.

### Step 1 — README.md 상단 "What this is / is not" 박스 추가

`README.md` 의 "Why I built this" / "Core idea" 섹션 사이 (line 13~22 부근) 에 신규 섹션 추가:

```markdown
## What this is / is not

This is:

- a reproducible experiment harness for small local LLM workflows
- a measured notebook about externalized state, tools, roles, and control
- a public baseline for reproduction and disagreement

This is not:

- a new model architecture
- a training method
- a claim that 4B models replace frontier models
- a claim that ABC+Tattoo universally beats RAG
```

요구사항:
- 정확한 위치는 grep 으로 "Core idea" / "Why I built this" 위치 확인 후 결정 — Core idea 직전 또는 직후 권장
- 사용자 정책 그대로 (4 항목 / 4 항목)
- 기존 README 의 보수적 톤과 충돌하지 않도록 톤 일관

### Step 2 — README.ko.md 동일 박스 한국어 동기화

`README.ko.md` 의 동일 위치 (Core idea 또는 "왜 만들었나" 직전/직후) 에 한국어 박스:

```markdown
## What this is / is not — 본 repo 는 무엇이고 무엇이 아닌가

이 repo 는:

- 소형 로컬 LLM workflow 의 재현 가능한 실험 하네스
- 외부화된 상태 / 도구 / 역할 / 제어를 측정한 연구 노트
- 재현·반박을 위한 공개 baseline

이 repo 는 아니다:

- 새로운 모델 architecture
- 학습 기법
- 4B 모델이 frontier 모델을 대체한다는 주장
- ABC+Tattoo 가 RAG 를 보편적으로 능가한다는 주장
```

요구사항:
- 영문판과 동일 사실 4/4 매핑
- 한국어 어순/표현 자연스럽게

### Step 3 — README.ko.md:146 Exp10 bullet 끝 동기화 (직전 reviewer finding 해결)

`README.ko.md:146` 의 Exp10 bullet 의 마지막 마침표 앞에 한 줄 추가:

기존:
```markdown
- **소형 로컬 + ABC 가 폐쇄형 대형 1-call 을 능가한다** — Exp10 의 9-task / 540-trial cost-aware 비교에서 같은 Gemma 4 E4B 가 1-loop 41.3% → 8-loop ABC 78.1% (+37%p, H1 추가 evidence). 동일 ABC 조건이 Gemini 2.5 Flash 1-call 의 59.1% 를 +19%p 능가, 비용 \$0, 시간은 약 20× (8min vs 24s).
```

변경:
```markdown
- **소형 로컬 + ABC 가 폐쇄형 대형 1-call 을 능가한다** — Exp10 의 9-task / 540-trial cost-aware 비교에서 같은 Gemma 4 E4B 가 1-loop 41.3% → 8-loop ABC 78.1% (+37%p, H1 추가 evidence). 동일 ABC 조건이 Gemini 2.5 Flash 1-call 의 59.1% 를 +19%p 능가, 비용 \$0, 시간은 약 20× (8min vs 24s). ABC chain 인프라 4 trial 의 JSON parse fail (early-stop 패턴, 상세는 `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`).
```

요구사항:
- 영문판 (`README.md:51`) 의 disclosure 와 동일 사실
- 한국어 자연스러운 어순

### Step 4 — 다른 영역 보존

README 의 다른 섹션 (H 표, Headline, What worked / What didn't, Why this matters, Related work, Roadmap 등) 변경 0.

## Dependencies

- Task 04 — H4 보수화 가 README 두 파일 수정 직전 — 본 task 는 그 다음 직렬
- 패키지: 없음 (마크다운 편집)

## Verification

```bash
# 1) README.md "What this is / is not" 박스 추가 확인
grep -A3 "What this is / is not" README.md | head -10
# 기대: "This is:" + "This is not:" + 8 항목 (4+4) 모두 출력

# 2) README.ko.md 한국어 박스 추가
grep "What this is / is not" README.ko.md
# 기대: 1+ 라인 (헤더 등장)

# 3) 사용자 정책 4 항목 명시 ("ABC+Tattoo universally beats RAG" 부정)
grep -c "universally beats RAG" README.md
# 기대: 1 (영문판에 명시 부정)
grep -c "보편적으로 능가" README.ko.md
# 기대: 1 (한국어판 동일)

# 4) README.ko.md:146 Exp10 bullet 끝 disclosure 동기화
grep "early-stop\|4 trial" README.ko.md
# 기대: 1+ 라인 (4 trial JSON parse fail / early-stop 동기화)

# 5) 한·영 동기화 검증
.venv/bin/python -c "
en = open('README.md').read()
ko = open('README.ko.md').read()
# What this is / is not 박스
assert 'What this is / is not' in en and 'What this is / is not' in ko
# Exp10 4 fail disclosure
assert 'early-stop pattern' in en and 'early-stop' in ko
print('한·영 What/is_not 박스 + Exp10 disclosure 동기화 ok')
"

# 6) 외부 노출 톤 검사 (금지 명칭 미사용)
.venv/bin/python -c "
import re
banned = (r'\bOperating System\b', r'\bnovel framework\b', r'\bAGI\b')
for path in ('README.md', 'README.ko.md'):
    text = open(path).read()
    for pat in banned:
        if re.search(pat, text):
            print(f'{path}: banned {pat}'); raise SystemExit(1)
print('금지 명칭 검사 ok')
"
```

6 명령 모두 정상 + assertion 통과.

## Risks

- **박스 위치 결정**: "Core idea" 직전 vs 직후 — 직전 권장 (첫인상 가드). Step 1 의 grep 으로 정확한 위치 확인.
- **한·영 표기 미세 차이**: 영문판 "ABC+Tattoo universally beats RAG" 와 한국어 "ABC+Tattoo 가 RAG 를 보편적으로 능가한다는 주장" — 의미 일치 검증 (사용자 시각 권장).
- **`README.ko.md:146` 라인 번호 변동**: Task 04 의 H4 행 변경 + Step 1·2 의 박스 추가로 line 번호가 밀릴 수 있음 — grep 으로 정확한 위치 확인 후 sed/edit.
- **disclosure 의 외부 링크**: `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` 가 git 에 commit 됐는지 확인. 직전 plan 의 푸시 결과 (`8477981 feat(exp10): v2 finalize + v3 scorer/abc-json patch`) 에 포함됨 — 정상.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `README.md` 의 H 표 / Related work / Headline / Roadmap — Task 04/06 영역 또는 직전 plan 영역
- `README.ko.md` 의 H 표 / Related work / Roadmap — Task 04/06 영역
- `experiments/config.py` / `requirements.txt` / `docs/reference/conceptFramework.md` / `experiments/exp10_reproducibility_cost/INDEX.md` — Task 01/02/03 영역
- `docs/reference/researchNotebook.md` / `.en.md` — 직전 plan 영역
- `docs/reference/results/exp-10-reproducibility-cost.md` — 직전 plan 영역
- README 의 Why I built this / Core idea 본문 — 박스 추가만, 기존 텍스트 변경 0
