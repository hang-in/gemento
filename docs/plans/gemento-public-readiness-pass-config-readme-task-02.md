---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: A
depends_on: []
---

# Task 02 — conceptFramework.md evidence_ref 상태 수정

## Changed files

- `docs/reference/conceptFramework.md` — **수정**. line 77 / 95 / 111 / 115 / 126 부근의 `evidence_ref` 관련 표현 점검. 미래형 ("포함해야 한다", "후속 과제") 표현을 현재 구현 사실 반영하도록 수정.

신규 파일 0, 다른 파일 수정 0.

## Change description

### 배경

`docs/reference/conceptFramework.md` 의 evidence_ref 표현 (정찰 결과):
- line 77: `| 폴라로이드 사진 | **evidence_ref (스냅샷 포인터)** | 특정 사실의 출처 |` (개념 표 — 정상)
- line 95: `| 예시 | JSON 스키마 검증, evidence_ref 존재 확인, citation resolve, AST 화이트리스트 | ...` (Evidence Tool 의 예시 — 정상)
- line 111: `Tattoo 는 상태 자체뿐 아니라 환경 포인터 (evidence_ref) 를 포함해야 한다` (미래형 표현 — 실제는 구현됨)
- line 115: `Tattoo 의 assertion.evidence_ref 필드는 "이 주장의 출처는 어디인가" 를 기록.` (구현 사실 — 정상)
- line 126: `evidence_ref` JSON 예시 (정상)

실제 코드:
- `experiments/schema.py` 의 `Assertion` 클래스에 `evidence_ref: Optional[dict] = None` 필드가 이미 존재 (정찰로 확인)
- `experiments/tools/` 하위에 Evidence Tool / citation resolver / validator 자체는 미구현

### Step 1 — line 111 부근 미래형 표현 점검 + 수정

기존 (line 111 부근, 정확한 라인 번호는 grep 으로 재확인):
```markdown
Tattoo는 **상태 자체뿐 아니라 환경 포인터**(evidence_ref)를 포함해야 한다. Evidence Tool은 이 포인터를 resolve하여 원문 근거를 재확인한다. 이 두 요소는 독립이 아니라 **결합 쌍**으로 설계되어야 한다.
```

수정 (구현 상태 명확):
```markdown
Tattoo는 **상태 자체뿐 아니라 환경 포인터**(evidence_ref)를 포함한다 — Assertion.evidence_ref 필드가 `experiments/schema.py` 에 이미 구현됨. Evidence Tool 은 이 포인터를 resolve / validate 하는 역할이며, citation resolver / validator 자체는 아직 미구현 (별도 후속 과제). 두 요소는 독립이 아니라 **결합 쌍**으로 설계되어야 한다.
```

요구사항:
- "포함해야 한다" → "포함한다" (현재형)
- 구현된 부분 (schema-level pointer) 와 미구현 부분 (Evidence Tool / resolver / validator) 명확히 분리
- "후속 과제" 표현 유지 (별도 plan 으로 미구현 영역 명시)

### Step 2 — 표 / 본문 점검

`docs/reference/conceptFramework.md` 전체 grep 으로 다른 미래형 표현 검색:

```bash
grep -n "포함해야\|구현해야\|미구현\|후속\|TBD\|TODO" docs/reference/conceptFramework.md
```

evidence_ref 관련 미래형 표현 발견 시 동일 패턴으로 수정 (구현된 부분 / 미구현 부분 분리).

기타 (Evidence Tool / citation resolver / validator) 의 미구현 표기는 그대로 유지 — 사실이 정확하므로.

### Step 3 — 4-axis 핵심 모델 변경 금지

본 task 는 evidence_ref 의 implementation status disclosure 만. 4-axis (Tattoo / Tools / Role / Orchestrator) 핵심 개념 변경 금지. 표 행 / 다이어그램 / 가설 매핑 그대로 유지.

## Dependencies

- 패키지: 없음 (마크다운 편집)
- 다른 subtask: 없음. parallel_group A.

## Verification

```bash
# 1) line 111 부근 미래형 표현 제거
grep -n "evidence_ref.*포함해야 한다\|포함해야 한다.*evidence_ref" docs/reference/conceptFramework.md
# 기대: 0 라인

# 2) 구현 사실 명시 (schema.py 참조 또는 "이미 구현" 표현)
grep -n "schema.py\|이미 구현\|evidence_ref 필드.*구현" docs/reference/conceptFramework.md | head -5
# 기대: 1+ 라인 (구현 사실 명시)

# 3) schema.py 의 Assertion.evidence_ref 가 실제 존재
grep -n "evidence_ref" experiments/schema.py
# 기대: 1+ 라인 (Optional[dict] 필드)

# 4) 4-axis 표 / 핵심 다이어그램 보존
grep -c "^| \*\*[A-Z]" docs/reference/conceptFramework.md
# 기대: 1+ (표 행 보존, 정확한 카운트는 변경 전후 동일)

# 5) git diff 의 변경 라인이 모두 evidence_ref 영역
git diff docs/reference/conceptFramework.md | grep -E '^[\+\-][^+\-]' | grep -v "evidence_ref\|Evidence Tool\|resolver\|validator\|구현됨\|schema.py"
# 기대: 0 라인 (변경이 모두 본 task 영역 내)
```

5 명령 모두 정상.

## Risks

- **다른 미래형 표현 우발 변경**: conceptFramework.md 에는 evidence_ref 외에도 다른 4-axis 영역의 미래형 표현이 있을 수 있음. 본 task 는 evidence_ref 한정 — Step 2 의 grep 결과 검토 시 evidence_ref 외 항목은 본 task 범위 외 (별도 plan).
- **schema.py 의 Optional 의미**: `evidence_ref: Optional[dict] = None` 가 "구현됨" 인지 "선택적 필드" 인지 모호. 실제로는 schema-level 에서 정의됨 (구현됨), 다만 default None — 사용 자체는 채워야. 표현 정확화: "schema-level pointer 로 정의됨, 실제 채움/resolve 는 별도".
- **표 행 카운트 변경**: 본 task 가 표 본문 변경 없이 단락 텍스트만 수정. 변경 후 표 카운트 동일 검증.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/schema.py` — 본 task 는 schema 변경 0, 단순 사실 참조
- `experiments/config.py` / `requirements.txt` / `README.md` / `README.ko.md` — Task 01/04/05/06 영역
- `experiments/exp10_reproducibility_cost/INDEX.md` — Task 03 영역
- `docs/reference/researchNotebook.md` / `.en.md` — 직전 plan 영역
- `docs/reference/results/exp-10-reproducibility-cost.md` — 직전 plan 영역
- conceptFramework.md 의 4-axis 핵심 표 / 다이어그램 / H 가설 매핑 — 본 task 는 evidence_ref 단락만
