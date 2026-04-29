---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: B
depends_on: []
---

# Task 04 — README H4 보수화 한·영

## Changed files

- `README.md` — **수정**. line 35 의 H4 행. evidence 컬럼에 v1/v2 caveat 추가.
- `README.ko.md` — **수정**. line 132 의 H4 행. 한국어 동기화.

신규 파일 0.

## Change description

### 배경

`README.md:35`:
```markdown
| **H4** | [Role externalization synergy] A-B-C role separation outperforms repeated single-agent iteration | ✅ Supported (+22.6pp) | Exp06 |
```

`README.ko.md:132`:
```markdown
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ✅ 채택 (+22.6%p) | Exp06 |
```

문제:
- "+22.6pp" 는 Exp06 v1 채점 기준 ABC 우위. v2 채점 적용 시 Solo 가 약간 우위 가능성 (사용자 정찰 — 표본 비대칭, 채점 artifact 가능성)
- 연구노트와 README 사이 해석 불일치 (사용자 명시 정책)

### Step 1 — README.md:35 H4 행 보수화

기존:
```markdown
| **H4** | [Role externalization synergy] A-B-C role separation outperforms repeated single-agent iteration | ✅ Supported (+22.6pp) | Exp06 |
```

변경:
```markdown
| **H4** | [Role externalization synergy] A-B-C role separation may outperform repeated single-agent iteration under some scoring conditions | ⚠ Conditionally supported (Exp06 v1: +22.6pp ABC; v2: slightly favors Solo under asymmetric sample — needs balanced rerun) | Exp06 |
```

요구사항:
- "outperforms" → "may outperform ... under some scoring conditions"
- "✅ Supported (+22.6pp)" → "⚠ Conditionally supported"
- evidence 컬럼에 v1 +22.6pp ABC + v2 caveat (Solo 약간 우위 가능성, 비대칭 표본, balanced rerun 필요) 한 줄
- v1 +22.6pp 수치 보존 — 삭제 금지

### Step 2 — README.ko.md:132 H4 행 한국어 동기화

기존:
```markdown
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ✅ 채택 (+22.6%p) | Exp06 |
```

변경:
```markdown
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 (일부 채점 조건에서) 우수할 수 있다 | ⚠ 조건부 채택 (Exp06 v1: +22.6%p ABC 우위; v2: 비대칭 표본 하에서 Solo 약간 우위 가능성 — balanced rerun 필요) | Exp06 |
```

요구사항:
- 영문판과 동일 사실 표기
- "✅ 채택" → "⚠ 조건부 채택"
- v1/v2 caveat 동일 한 줄 evidence 컬럼

### Step 3 — H4 caveat 단락 추가는 본 task 범위 외

README 본문 (table 외 영역) 에 H4 의 자세한 caveat 단락 추가는 별도 plan 후보. 본 task 는 H 표 행만 보수화.

### Step 4 — 다른 H 행 / 표 보존

H1, H2, H3, H5~H9c 행은 변경 0. 표의 column 수, row 순서, 다른 셀 내용 모두 보존.

## Dependencies

- 패키지: 없음 (마크다운 편집)
- 다른 subtask: 없음. parallel_group B 의 시작점 — Group B 는 README 직렬 수정.

## Verification

```bash
# 1) README.md H4 행 변경 확인
grep "^| \*\*H4\*\*" README.md
# 기대: "Conditionally supported" + "v1: +22.6pp" + "v2" + "balanced rerun" 모두 포함

# 2) README.ko.md H4 행 변경 확인
grep "^| \*\*H4\*\*" README.ko.md
# 기대: "조건부 채택" + "v1: +22.6%p" + "v2" + "balanced rerun" 모두 포함

# 3) "✅ Supported" / "✅ 채택" 의 H4 표기 제거 확인
grep -E "\*\*H4\*\*.*✅" README.md README.ko.md
# 기대: 0 라인

# 4) 다른 H 행 보존 (H1, H9c 등)
grep -c "^| \*\*H[0-9]" README.md README.ko.md
# 기대: 두 파일 모두 동일 카운트 (변경 전후), H4 외 행 변경 0

# 5) +22.6pp 수치 보존 (삭제 금지)
grep "22.6" README.md README.ko.md
# 기대: 두 파일 모두 1+ 라인 (수치 보존)
```

5 명령 모두 정상 + 한·영 동일 사실 표기.

## Risks

- **표 형식 깨짐**: H4 행에 새 텍스트 추가 시 pipe 카운트 변경 위험. 표 헤더와 동일 카운트 유지 필요. Verification 4 의 카운트 검사로 보장.
- **caveat 표현의 정확성**: "v2 slightly favors Solo" 는 사용자 정찰 표현 그대로. 실제 Exp06 v2 채점 결과의 정확한 수치는 noteboook 참조 필요 — 본 task 는 caveat 한 줄만, 정확한 수치 인용은 별도 (수치는 result.md 에).
- **한·영 동기화**: 영어판의 "may outperform under some scoring conditions" 와 한국어 "(일부 채점 조건에서) 우수할 수 있다" 의 의미 일치 — 사용자 시각 검토 권장.
- **balanced rerun 표현**: README 가 balanced rerun 을 promise 하면 사용자 부담. "needs balanced rerun" / "balanced rerun 필요" 정도로 — caveat 만, 약속 아님.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `README.md` 의 H4 외 다른 H 행 / 다른 섹션 (Headline / What this is is not / Related work / Roadmap 등) — 본 task 는 H4 행만
- `README.ko.md` 의 H4 외 다른 H 행 / 다른 섹션
- `experiments/config.py` / `requirements.txt` / `docs/reference/conceptFramework.md` / `experiments/exp10_reproducibility_cost/INDEX.md` — Task 01/02/03 영역
- `docs/reference/researchNotebook.md` / `.en.md` — 직전 plan 영역
- Task 05/06 영역의 README 다른 위치 (What this is / is not 박스, ko Exp10 disclosure, Related work footnote) — 직렬 진행
