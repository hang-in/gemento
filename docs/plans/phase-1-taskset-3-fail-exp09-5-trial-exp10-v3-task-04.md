---
type: plan-task
status: done
updated_at: 2026-04-30
parent_plan: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
parallel_group: C
depends_on: [02, 03]
readme_branch: "|Δ| < 0.01 → README 본문 변경 0 (사소)"
---

# Task 04 — 문서 갱신 통합

## Changed files

- `docs/reference/results/exp-10-reproducibility-cost.md` — **수정**. §2/§3 mean_acc / per-task 표 → Task 03 의 새 v3 결과로 갱신 + Δ disclosure ("Phase 1 후속 taskset 정정 반영").
- `docs/reference/results/exp-09-longctx.md` — **수정**. Task 02 의 5-trial 분석 결론 추가 (별도 섹션).
- `docs/reference/researchNotebook.md` — **수정**. Exp09 섹션 (5-trial 분석 결론) + Exp10 섹션 (v3 재산정 결과) + Taskset 3 FAIL 정정 disclosure.
- `docs/reference/researchNotebook.en.md` — **수정** (추가만). Exp09 5-trial drop note + Exp10 v3 rescore (taskset patched) note 추가. 기존 영문 수치 변경 0 (Closed 추가만 정책).
- `README.md` / `README.ko.md` — **조건부 수정**. Task 03 의 Exp10 v3 변동이 외부 노출에 의미 있으면 Headline / H1 evidence 갱신. 사소하면 disclosure 만.

신규 파일 0.

## Change description

### 입력

- Task 02 결과: `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` 의 원인 후보 결정 + 함의
- Task 03 결과: 새 `exp10_v3_rescored_<TS>.json` 의 condition aggregate + per-task Δ (math-03 / synthesis-04 변동)

### Step 1 — `exp-10-reproducibility-cost.md` 갱신

§2 핵심 메트릭 표:
- 새 v3 mean_acc 로 갱신 (3 condition)
- 직전 v3 (053939) Δ disclosure 한 줄 — "Phase 1 후속 taskset 정정 (math-03 / synthesis-04) 반영, Δ <FILL>"

§3 per-task 정답률 표:
- math-03 / synthesis-04 의 새 mean 으로 갱신 (3 condition × 2 task = 6 셀)
- 다른 task 보존

§5 또는 §6 또는 §7 어느 한 섹션에 sub-bullet 추가:
- "**2026-04-30 Phase 1 후속**: Taskset 3 FAIL 정정 (math-03 prompt 옵션 A or B / synthesis-04 keyword / longctx-medium-2hop-02 expected). Exp10 v3 재산정 결과 condition mean Δ <FILL>. 정정 절차: `phase-1-taskset-3-fail-exp09-5-trial-exp10-v3` plan."

### Step 2 — `exp-09-longctx.md` 갱신

Exp09 result.md 의 적절한 섹션 (있으면 §reliability 또는 §discussion) 에 5-trial 분석 결론 한 단락 추가:

```markdown
### 5-trial 점수 하락 분석 (2026-04-30 Phase 1 후속)

3-trial → 5-trial 시 양 arm (abc 0.883→0.530, rag 0.850→0.510) 동시 0.353/0.340 하락.
원인 분석 (`docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`): <FILL — Task 02 결과>.
H9b verdict 영향: <FILL — Task 02 함의>.
```

### Step 3 — `researchNotebook.md` (한국어) 갱신

Exp09 섹션 — 5-trial 분석 결론 한 줄 disclosure (위 §5-trial 점수 하락 분석 보고서 가리킴).

Exp10 섹션 — v3 재산정 결과:
- "**2026-04-30 Phase 1 후속 v3 재산정**: Taskset 3 FAIL (math-03 / synthesis-04 / longctx-medium-2hop-02) 정정 후 v3 rescored. 새 mean: gemma_8loop <FILL> / flash <FILL> / gemma_1loop <FILL>. Δ <FILL>."

채점 시스템 변천 표 옆에 "v3 재산정 (2026-04-30, taskset patched)" 행 또는 한 줄.

### Step 4 — `researchNotebook.en.md` 갱신 (Closed 추가만)

Exp09 섹션 끝 또는 적절 위치에 "5-trial drop analysis note (2026-04-30)" 단락 추가 (영문). 기존 5-trial 결과 표 / verdict 변경 0.

Exp10 섹션 끝의 "v3 rescore note (2026-04-29)" 다음에 "v3 rescore note 2 (2026-04-30, taskset patched)" 단락 추가. 기존 v3 (2026-04-29) note 변경 0.

### Step 5 — README 조건부 갱신

**조건 분기**:

| Δ 크기 | 처리 |
|--------|------|
| 작음 (\|Δ\| < 0.01) | README 본문 변경 0. 별도 disclosure 미추가 (사소) |
| 중간 (0.01 ≤ \|Δ\| < 0.03) | Headline 의 78.1% / 41.3% 등 수치 갱신 (한·영). H1 evidence 의 +37pp 도 영향받으면 갱신 |
| 큼 (\|Δ\| ≥ 0.03) | Headline + H1 evidence + Roadmap (필요 시) 갱신. 외부 노출 약속 회수 명시 |

Task 03 의 Δ 결과로 분기 결정. 사용자 시각 검토 권고.

### Step 6 — 한·영 동기화 + 외부 노출 톤 검사

```bash
.venv/bin/python -c "
import re
banned = (r'\bOperating System\b', r'\bnovel framework\b', r'\bAGI\b')
for path in ('README.md', 'README.ko.md'):
    text = open(path).read()
    for pat in banned:
        if re.search(pat, text):
            raise SystemExit(f'{path}: banned {pat}')
print('금지 명칭 검사 ok')
"
```

## Dependencies

- Task 02 — `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` 의 결론 입력
- Task 03 — 새 `exp10_v3_rescored_<TS>.json` 의 condition aggregate + per-task Δ 입력
- 패키지: 없음 (마크다운 편집 + 한 python assertion)

## Verification

```bash
# 1) result.md 의 §2 mean_acc 가 새 v3 결과와 일치
.venv/bin/python -c "
import json, glob, re
latest = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))[-1]
d = json.load(open(latest))
from collections import defaultdict
agg = defaultdict(lambda: {'n':0,'v3':0.0})
for t in d['trials']:
    agg[t['condition']]['n'] += 1
    agg[t['condition']]['v3'] += t.get('accuracy_v3', 0)
result_md = open('docs/reference/results/exp-10-reproducibility-cost.md').read()
for cond, stat in agg.items():
    mean = stat['v3'] / stat['n']
    rounded = f'{mean:.3f}'  # 3-decimal
    # 또는 4-decimal
    if rounded not in result_md and f'{mean:.4f}' not in result_md:
        print(f'MISMATCH {cond}: {mean:.4f} not in result.md')
print('result.md 수치 일치 검증 ok')
"

# 2) 5-trial 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/exp09-5trial-drop-analysis-2026-04-30.md | wc -l
# 기대: 0

# 3) 영문 노트북 추가만 검증 (기존 v3 rescore note 보존, 새 note 추가)
grep -c "v3 rescore note" docs/reference/researchNotebook.en.md
# 기대: 2 (2026-04-29 + 2026-04-30)

# 4) 한·영 README 핵심 수치 동기화 (변동 시)
.venv/bin/python -c "
en = open('README.md').read()
ko = open('README.ko.md').read()
import re
banned = (r'\bOperating System\b', r'\bnovel framework\b', r'\bAGI\b')
for path, text in (('README.md', en), ('README.ko.md', ko)):
    for pat in banned:
        if re.search(pat, text):
            raise SystemExit(f'{path}: banned {pat}')
print('한·영 README 외부 노출 톤 검사 ok')
"

# 5) Markdown table 정합 (본 task 변경 영역)
.venv/bin/python -c "
in_table = False
hp = 0
issues = 0
for path in ('docs/reference/results/exp-10-reproducibility-cost.md', 'docs/reference/researchNotebook.md'):
    text = open(path).read()
    in_table = False; hp = 0
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            pipes = s.count('|')
            if not in_table:
                hp = pipes; in_table = True
            elif pipes != hp and i not in (480,):
                print(f'{path}:{i} pipe mismatch'); issues += 1
        else:
            in_table = False
print(f'table check {\"ok\" if issues==0 else f\"{issues} issues\"}')
"
```

5 명령 모두 정상 + 한·영 동기화.

## Risks

- **Task 03 의 Δ 가 README 갱신 임계값 결정에 의존**: Δ 작으면 README 변경 0, 크면 Headline / H1 갱신. 사용자 시각 검토 권고.
- **영문 노트북 정책 위반 위험**: 본 task 가 영문에 추가만, 수정 0 — Verification 3 의 grep 카운트로 검증.
- **researchNotebook 의 line 480 Exp08 표 사전 존재 mismatch**: 본 plan 영역 외, fail 사유 아님 — Verification 5 에서 disclosure.
- **placeholder 누락**: 본 task 의 모든 `<FILL>` 자리는 Task 02/03 결과로 채워짐 — Verification 2/4 의 grep 으로 검증.
- **한·영 동기화 실수**: README 한쪽만 갱신 시 차이. Verification 4 의 핵심 수치 일치 + 사용자 시각 검토.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/tasks/taskset.json` / `longctx_taskset.json` — Task 01 영역
- `experiments/exp09_longctx/analyze_5trial_drop.py` — Task 02 영역
- `experiments/exp10_reproducibility_cost/rescore_v3.py` — Task 03 영역, 재실행만
- 모든 결과 JSON — read-only
- `experiments/measure.py` / `experiments/orchestrator.py` / `experiments/schema.py` — 다른 영역
- 다른 result.md (`exp-00-baseline.md` ~ `exp-08*.md`, `exp-06-solo-budget.md`) — 본 plan 영역 외 (Exp10 / Exp09 만)
- README / 노트북의 H 표 외 영역 (Roadmap, Acknowledgements 등) 변경 — 본 task 는 H 표 / Headline / Exp 섹션 만
- conceptFramework.md 등 — 직전 plan 의 검증된 영역
