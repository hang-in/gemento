---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: sampling-params-config-exp10
parallel_group: B
depends_on: [01]
---

# Task 05 — researchNotebook 메모 추가

## Changed files

- `docs/reference/researchNotebook.md` — **수정**. 프로젝트 개요 영역에 sampling 한 줄 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

`docs/reference/researchNotebook.md` 의 "프로젝트 개요" 표 (또는 인접 영역) 에 sampling 정보가 없다. 향후 `tools/build_appendix.py` 가 reproducibility appendix 를 자동 생성할 때 본 한 줄을 인용 가능하도록 명시한다.

또한 본 plan task-03 의 risk 항목에서 식별된 "도입 전 LM Studio 기본값과 명시값 차이로 결과 변동 가능성" 을 메모로 남긴다 — 향후 비교 시 baseline 이 어디서 끊기는지 명확화.

### Step 1 — sampling 한 줄 추가

`docs/reference/researchNotebook.md` 의 "프로젝트 개요" 표 (현재 4 행: 프로젝트명/핵심 질문/대상 모델/기간) 에 sampling 행 1 개 추가하거나, 표 아래에 별도 한 줄.

권장 위치: "프로젝트 개요" 표 안 마지막 행으로 추가 (구조적 일관성).

추가 행 예시:

```markdown
| Sampling | `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` unset (`config.py:SAMPLING_PARAMS` 단일 source — 2026-04-26 도입, sampling-params-config-exp10 plan 결과) |
```

### Step 2 — baseline 변동 가능성 메모

researchNotebook 의 "열린 질문" 또는 "변경 이력" 섹션에 한 줄 추가:

```markdown
- 2026-04-26: `config.py:SAMPLING_PARAMS` 일원화로 lmstudio_client.py 가 sampling 명시 시작.
  도입 전 LM Studio 기본값과 본 명시값 (`temperature=0.1`, `max_tokens=4096`) 차이로 Exp10 결과가
  Exp00~09 과 미세한 차이 가능. baseline 비교 시 본 시점 이전·이후 분리.
```

위치: researchNotebook 의 "변경 이력" 섹션 (있으면 거기), 없으면 "열린 질문" 또는 마지막에 새 "## 변경 이력" 섹션 추가.

### Step 3 — researchNotebook.en.md 동기화

`docs/reference/researchNotebook.en.md` 가 한국어 버전의 영문 미러로 존재. 동일 내용을 영문으로 추가:

```markdown
| Sampling | `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` unset (single source: `config.py:SAMPLING_PARAMS` — introduced 2026-04-26 via sampling-params-config-exp10 plan) |
```

및

```markdown
- 2026-04-26: `config.py:SAMPLING_PARAMS` centralization — lmstudio_client.py now explicitly sends sampling params.
  Pre-centralization LM Studio default may have differed from `temperature=0.1`/`max_tokens=4096`,
  so Exp10 results may show micro-variance vs Exp00~09. Treat the introduction date as a baseline boundary.
```

### Step 4 — 파일 무결성 — 기존 섹션 미손상

다른 섹션 (실험 5W1H, 핵심 발견 등) 은 변경 금지. 본 task 는 **추가 only**.

## Dependencies

- **task-01 완료** — sampling 값이 확정되어야 메모 작성 가능 (값 0.1/4096/None/None).
- 외부 패키지: 없음.

## Verification

```bash
# 1. researchNotebook.md 에 SAMPLING_PARAMS 키워드 등장
cd /Users/d9ng/privateProject/gemento && grep -q "SAMPLING_PARAMS" docs/reference/researchNotebook.md && echo "OK SAMPLING_PARAMS in researchNotebook.md"

# 2. researchNotebook.en.md 동기화
cd /Users/d9ng/privateProject/gemento && grep -q "SAMPLING_PARAMS" docs/reference/researchNotebook.en.md && echo "OK SAMPLING_PARAMS in researchNotebook.en.md"

# 3. baseline 변동 메모 등장 (한국어/영문)
cd /Users/d9ng/privateProject/gemento && grep -q "2026-04-26" docs/reference/researchNotebook.md && echo "OK changelog entry in researchNotebook.md"
cd /Users/d9ng/privateProject/gemento && grep -q "2026-04-26" docs/reference/researchNotebook.en.md && echo "OK changelog entry in researchNotebook.en.md"

# 4. 기존 섹션 미손상 — Exp00~09 섹션 헤더 모두 존재 (sample check)
cd /Users/d9ng/privateProject/gemento && grep -cE "^### (Exp0|Exp1)" docs/reference/researchNotebook.md
# 기대: 9 이상 (Exp00 ~ Exp09 각 섹션 존재)

# 5. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^(experiments/config\.py|docs/reference/researchNotebook\.(md|en\.md))$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **researchNotebook 의 표 구조 변경**: 4 행 → 5 행 추가 시 markdown 표 정합성 (column count 일관성) 주의. Developer 가 직접 read 후 정확히 삽입.
- **researchNotebook.en.md 누락**: 한국어만 작성하면 부록 자동 생성이 영문판에서 필드 미발견. 본 task 는 두 파일 모두 변경.
- **다른 plan 과의 동시 수정 충돌**: researchNotebook 은 "프로젝트 단일 진실 문서" — 다른 plan 진행 중이면 conflict 위험. 본 plan 진행 중 다른 plan 의 researchNotebook 수정 금지. (단, 현재 다른 active plan 없음 — 최근 commit `e8da005`.)
- **단순 메모인데 task 단위 분리?**: 메모 한 줄이라 task-04 검증 안에 흡수 가능했음. 단 plan structure 일관성 + Reviewer 추적성 위해 별도 task 로 둠. 비용 무시 가능.

## Scope boundary

**Task 05 에서 절대 수정 금지**:

- `experiments/` 의 모든 파일 (config.py 포함). task-01 결과물에 의존하나 본 task 는 docs 변경만.
- `docs/reference/researchNotebook.md` 의 기존 섹션 본문 (Exp00~09 5W1H, 핵심 발견, 결론 등).
- `docs/reference/researchNotebook.en.md` 의 동일 섹션.
- `docs/plans/` 의 모든 파일 (본 plan 의 task 문서 포함).
- README, CLAUDE.md, 다른 docs/reference/ 파일.

**허용 범위**:

- `docs/reference/researchNotebook.md` 의 "프로젝트 개요" 표에 sampling 행 1 추가 + "변경 이력" 영역에 한 줄 추가.
- `docs/reference/researchNotebook.en.md` 동일 위치 영문 동기화.
