---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-readme-v2-abc-4-fail-v3-disclosure
parallel_group: A
depends_on: []
---

# Task 02 — v3 적용 범위 disclosure

## Changed files

- `docs/reference/results/exp-10-reproducibility-cost.md` — **수정**. §7 의 v3 우선순위 #5 항목 (line 113-115 근처) 갱신: "logic-04 가 Exp00~09 의 task subset 에 미포함" 사실 + v3 적용 영향 0 disclosure (한 줄 추가).
- `docs/reference/researchNotebook.md` — **수정**. "v2 → v3 전환 (2026-04-29)" subsection (line 730 근처) 의 결과 표 다음에 v3 적용 범위 한 줄 추가.

신규 파일 0. 영문 노트북 (`researchNotebook.en.md`) 변경 0 (Closed 추가만 정책 — Exp10 v3 rescore note 는 직전 plan 에서 추가됨).

## Change description

### 배경

직전 plan 의 result.md §7 #5 항목:

> 5. **다른 task 의 v3 채점 결과**: 본 plan 의 `rescore_v3.py` 가 540 trial 전수 재산정한 결과, logic-04 외 8 task 는 v2 == v3 — 추가 false positive 식별 0. 단, 다른 task 의 negative_patterns 미정의 상태이므로 향후 false positive 가 발견되면 task 별 보강 patch.

이 항목은 **Exp10 540 trial 한정** 의 v2/v3 격차 분석. 그러나 사용자가 본 plan 직전 정찰에서 "Exp00~09 의 result JSON 들에 logic-04 가 포함되는지" 점검한 결과 **모두 미포함**. 즉:

- score_answer_v3 의 다른 실험 (Exp00~09) 적용 시 변동 0 예상 (logic-04 가 없으므로 negative_patterns 차단 발동 안 함)
- 다른 task 들은 v3 == v2 (negative_patterns 미정의 → fallback)
- 따라서 Exp00~09 채점 재산정의 의의 없음

이 사실을 정직하게 disclosure.

### Step 1 — `exp-10-reproducibility-cost.md` §7 #5 갱신

기존 (line 113-115 근처):

```markdown
5. **다른 task 의 v3 채점 결과**: 본 plan 의 `rescore_v3.py` 가 540 trial 전수 재산정한 결과, logic-04 외 8 task 는 v2 == v3 — 추가 false positive 식별 0. 단, 다른 task 의 negative_patterns 미정의 상태이므로 향후 false positive 가 발견되면 task 별 보강 patch.
```

다음으로 갱신 (한 줄 추가 + 새 #6 분리도 가능, 본 plan 은 #5 본문 보강):

```markdown
5. **다른 task 의 v3 채점 결과**: 본 plan 의 `rescore_v3.py` 가 540 trial 전수 재산정한 결과, logic-04 외 8 task 는 v2 == v3 — 추가 false positive 식별 0. 단, 다른 task 의 negative_patterns 미정의 상태이므로 향후 false positive 가 발견되면 task 별 보강 patch.
   - **Exp00~09 적용 범위**: 본 plan (`exp10-readme-v2-abc-4-fail-v3-disclosure`) 정찰 결과 logic-04 task 는 Exp00~09 의 result JSON 에 미포함 (직접 grep 확인). 따라서 `score_answer_v3` 를 Exp00~09 에 적용해도 변동 0 예상 — 별도 재산정 plan 의 우선순위 낮음.
```

### Step 2 — `researchNotebook.md` 채점 시스템 변천 표 부근 갱신

기존 (line 730 부근):

```markdown
**Exp10 v2 final 재채점 결과:**

| condition | v2 mean | v3 mean | Δ |
|-----------|--------:|--------:|--:|
| gemma_8loop | 0.820 | 0.781 | -0.039 |
| gemini_flash_1call | 0.619 | 0.591 | -0.028 |
| gemma_1loop | 0.413 | 0.413 | 0.000 |

→ v2 → v3 격차는 logic-04 한정 (다른 8 task 는 v2 == v3). 본 v3 patch 는 Exp10 만 적용. 다른 실험 (Exp00~09) 적용은 별도 plan.
```

다음으로 갱신 (마지막 한 줄을 좀 더 정확하게):

```markdown
→ v2 → v3 격차는 logic-04 한정 (다른 8 task 는 v2 == v3). 본 v3 patch 는 Exp10 만 적용. 다른 실험 (Exp00~09) 의 result JSON 에 logic-04 task 가 포함되지 않음 (정찰 grep 확인) — `score_answer_v3` 적용 시 변동 0 예상. 다른 task 의 false positive 발견 시 task 별 negative_patterns 보강 별도 plan.
```

### Step 3 — 영문 노트북 변경 없음 확인

`docs/reference/researchNotebook.en.md` 는 변경 0. 직전 plan 에서 Exp10 v3 rescore note 가 이미 추가됨 (Closed 추가만 정책). 본 plan 의 disclosure 는 Active 영역 (개발 중 결정/정찰) 이므로 영문판에 옮기지 않음.

## Dependencies

- 패키지: 없음 (마크다운 편집만)
- 다른 subtask: 없음. Task 01 과 병렬 가능 (parallel_group A).

## Verification

```bash
# 1) result.md §7 #5 가 새 disclosure 포함
grep -A3 "Exp00~09 적용 범위" docs/reference/results/exp-10-reproducibility-cost.md
# 기대: 새 sub-bullet 출력 (logic-04 미포함 + 변동 0 예상)

# 2) researchNotebook.md 의 v2→v3 표 부근 갱신
grep -B0 -A1 "정찰 grep 확인" docs/reference/researchNotebook.md
# 기대: 새 디스클로저 줄 출력

# 3) 영문 노트북 변경 0
git diff docs/reference/researchNotebook.en.md
# 기대: 빈 출력 (변경 없음)

# 4) 마크다운 형식 정합 (테이블/리스트 깨짐 없음)
.venv/bin/python -c "
for path in ('docs/reference/results/exp-10-reproducibility-cost.md', 'docs/reference/researchNotebook.md'):
    with open(path) as f:
        text = f.read()
    in_table = False
    header_pipes = 0
    issues = 0
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            pipes = s.count('|')
            if not in_table:
                header_pipes = pipes
                in_table = True
            elif pipes != header_pipes:
                # 본 plan 영역 외 사전 존재 issue 는 제외 — line 480 (Exp08 표) 등
                if i not in (480,):
                    print(f'{path}:{i} table row pipes mismatch')
                    issues += 1
        else:
            in_table = False
    print(f'{path}: {\"ok\" if issues == 0 else f\"{issues} issues\"}')
"
```

4 명령 모두 정상 + 영문 노트북 git diff 빈 출력 + 본 plan 변경 영역 의 마크다운 정합 ok.

## Risks

- **§7 #5 사이드 효과**: 본 항목 갱신이 result.md 의 다른 절 (table 정렬 등) 에 영향 줄 수 있음. 차분히 한 줄 추가만 (numbered list 의 sub-bullet) → table 영향 없음.
- **노트북 표 변경**: "v2 → v3 전환" 표 다음 한 줄 변경. 표 자체 변경 없음.
- **영문 노트북 우발적 변경**: editor/linter 가 무관 줄 자동 수정할 위험. git diff 로 검증.
- **disclosure 톤 정확성**: "변동 0 예상" 은 추정 — 실제 적용 시 다른 schema 의 result JSON 에서 미스매치 가능. "예상" 단어 명시로 추정 표기.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `docs/reference/researchNotebook.en.md` — 변경 0 (영문 노트북 정책)
- `experiments/measure.py` / `experiments/orchestrator.py` / `experiments/tasks/taskset.json` — 직전 plan 영역
- v2 final / v3 rescored JSON — read-only
- `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` — Task 01 영역
- `experiments/exp10_reproducibility_cost/diagnose_json_fails.py` — Task 01 영역
- `README.md` / `README.ko.md` — Task 03 영역
