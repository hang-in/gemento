---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: C
depends_on: [03, 05]
---

# Task 06 — result.md / 노트북 갱신

## Changed files

- `docs/reference/results/exp-10-reproducibility-cost.md` — **수정**. §2/§3 표에 v3 column 추가, §4.5 reliability 의 ABC 4 fail 진단 결과 반영, §6 표 v2 vs v3 갱신, §7 v3 우선순위 항목 정리 (이미 완료된 것 표시).
- `docs/reference/researchNotebook.md` — **수정**. Exp10 섹션의 결과 표에 v3 mean column 추가, 채점 시스템 변천 표에 "v2 → v3 (2026-04-29)" 행 추가.
- `docs/reference/researchNotebook.en.md` — **수정**. Exp10 섹션 끝 (key findings 6번 다음, "Detail report" 직전 또는 직후) 에 "v3 rescore note" 단락 추가. 기존 v2 final 수치 변경 금지.

신규 파일 0.

## Change description

### 배경

Task 03 (v3 rescore) + Task 05 (orchestrator patch) 결과를 정식 보고 문서에 반영. 한·영 노트북 정책 차이:

- 한국어 `researchNotebook.md` — Closed/Active 모두 갱신 가능. v3 column 추가 + 채점 시스템 변천 표 갱신.
- 영문 `researchNotebook.en.md` — **추가만 허용·수정 금지**. 기존 v2 final 수치 그대로 두고 v3 rescore note 만 추가.

### Step 1 — `docs/reference/results/exp-10-reproducibility-cost.md` 갱신

**§2 핵심 메트릭 표** — v2/v3 column 추가:

```markdown
| condition | mean_acc (v2 strict heuristic) | mean_acc (v3) | cost_usd (180) | $/trial | avg_dur | err+null |
|-----------|-------------------------------:|--------------:|---------------:|--------:|--------:|---------:|
| **gemma_8loop** | 0.781 | <FILL_v3> | $0.0000 | $0.0000 | **8 min** | 8 |
| gemini_flash_1call | 0.591 | <FILL_v3> | $0.0143 | $0.0000793 | 24 s | 0 |
| gemma_1loop | 0.413 | <FILL_v3> | $0.0000 | $0.0000 | 33 s | 11 |
```

`<FILL_v3>` 자리는 Task 03 의 rescore_v3.py 출력에서 가져옴.

> Footnote 갱신: "v2 strict heuristic" 은 Architect 측 logic-04 한정 사후 점검, "v3" 은 `score_answer_v3` (taskset 의 logic-04 negative_patterns 적용) 의 540 trial 전수 재산정. v3 가 정식 채점.

**§3 per-task 정답률 표** — gemma_8loop / gemma_1loop / gemini_flash 각 column 의 logic-04 행을 v3 mean 으로 갱신. logic-04 외 task 는 v2 == v3 이면 그대로.

**§4.5 reliability 단락** — Task 04 의 진단 결과 반영:

```markdown
- gemma_8loop: 4 trial JSON parse fail (math-03 t13, synthesis-01 t14, logic-04 t2/t6) — `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` 진단 결과: <FILL kind 분류>. orchestrator patch 는 v3 plan task-05 에서 처리됨 (미래 run 부터 적용).
```

**§6 채점 false positive 분석 표** — v3 적용 후 표:

```markdown
| condition | v2 logic-04 acc | v2 strict (사후 점검) | v3 logic-04 acc | false positive 제거 |
|-----------|---:|---:|---:|---:|
| gemma_8loop | 0.400 | 0.050 | <FILL_v3> | <FILL_count> |
| gemini_flash_1call | 0.250 | 0.000 | <FILL_v3> | <FILL_count> |
| gemma_1loop | 0.000 | 0.000 | <FILL_v3> | 0 |
```

**§7 v3 우선순위 갱신** — 5개 항목 중:
- 1번 (채점기 강화) → ✅ 완료 (본 plan)
- 2번 (ABC JSON parse 안정성) → ✅ 완료 (본 plan)
- 3번 (logic 카테고리 도구화) → 별도 실험 후보로 유지
- 4번 (use_tools 정책 통일) → 별도 plan 후보로 유지
- 5번 (다른 task strict 채점 전수 재산정) → 본 plan Task 03 결과로 부분 완료. logic-04 외 격차 있는 task 가 발견되면 별도 patch.

### Step 2 — `docs/reference/researchNotebook.md` 갱신

**Exp10 섹션 결과 표** (line 671 부근, "결과 (strict 채점, 540 trial)") — v3 mean column 추가:

```markdown
| condition | mean_acc (strict heuristic) | mean_acc (v3) | cost / 180 trial | avg_dur | err+null |
|-----------|----------------------------:|--------------:|-----------------:|--------:|---------:|
| **gemma_8loop** | 0.781 | <FILL> | $0.0000 | 8 min | 8 |
| gemini_flash_1call | 0.591 | <FILL> | $0.0143 | 24 s | 0 |
| gemma_1loop | 0.413 | <FILL> | $0.0000 | 33 s | 11 |
```

**핵심 발견 3번** (false positive 발견) 갱신: v3 이후 false positive 제거 결과 + 채점 시스템 변천 행 가리키도록.

**채점 시스템 변천 표** (line 720 부근 `## 채점 시스템 변천`) — `## v2 → v3 전환 (2026-04-29)` 신규 subsection:

```markdown
### v2 → v3 전환 (2026-04-29)

| 항목 | v2 (substring contains) | v3 (negative_patterns 보강) |
|------|-------------------------|----------------------------|
| 방식 | scoring_keywords 그룹 매칭 (substring) | v2 + task 별 negative_patterns 차단 + 옵션 conclusion_required |
| 문제점 | "no solution / contradiction" 류 결론 답을 정답으로 잡음 (logic-04 13/60) | — |
| 도입 동기 | — | Exp10 v2 final 의 false positive 발견 |

**Exp10 v2 final 재채점 결과:**

| condition | v2 mean | v3 mean | Δ |
|-----------|--------:|--------:|--:|
| gemma_8loop | 0.820 | <FILL> | <FILL> |
| gemini_flash_1call | 0.619 | <FILL> | <FILL> |
| gemma_1loop | 0.413 | <FILL> | <FILL> |
```

### Step 3 — `docs/reference/researchNotebook.en.md` 갱신 (추가만)

Exp10 섹션 끝 (key findings 6번 다음, "Detail report" 직후) 에 새 단락:

```markdown
**v3 rescore note (2026-04-29):**

After publishing the v2 final results above, a follow-up scorer (`score_answer_v3`)
was introduced to address logic-04 false positives caused by substring-only matching.
The v3 scorer adds optional `negative_patterns` per task to block "no solution / contradiction"
type answers from being scored as correct. Re-scoring the same 540-trial v2 final dataset:

| condition | v2 mean | v3 mean |
|-----------|--------:|--------:|
| gemma_8loop | 0.820 | <FILL> |
| gemini_flash_1call | 0.619 | <FILL> |
| gemma_1loop | 0.413 | <FILL> |

Ranking unchanged. The v2 final dataset itself is preserved; only the scoring layer changed.
Detail: `docs/reference/results/exp-10-reproducibility-cost.md` §6.
```

기존 §1~6 의 v2 final 수치는 그대로. v3 note 만 추가.

### `<FILL>` placeholders

위 3 step 의 모든 `<FILL>` / `<FILL_v3>` / `<FILL kind 분류>` 자리는 Task 03 의 stdout 출력 + Task 04 의 진단 문서에서 가져와 채움. 본 task 진행 시 두 출력을 함께 보고 일관된 수치 입력.

## Dependencies

- Task 03 — v3 rescore 결과 JSON + stdout aggregate 표가 모든 `<FILL>` 입력
- Task 05 — orchestrator patch 가 미래 run 적용 표시 (직접 v3 final acc 영향 없지만 §7 갱신에 필요)
- Task 04 — `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` 가 §4.5 의 진단 결과 입력
- 패키지: 없음 (마크다운 편집만)

## Verification

```bash
# 1) 모든 placeholder 가 채워졌는지
grep -E '<FILL[^>]*>|TBD' docs/reference/results/exp-10-reproducibility-cost.md docs/reference/researchNotebook.md docs/reference/researchNotebook.en.md
# 기대: 0 라인 (출력 없음)

# 2) v3 mean 수치가 Task 03 의 rescore 출력과 일치하는지
.venv/bin/python -c "
import json, glob, re
latest = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))[-1]
d = json.load(open(latest))
for cond in ('gemma_8loop', 'gemini_flash_1call', 'gemma_1loop'):
    trials = [t for t in d['trials'] if t['condition'] == cond]
    v3 = sum(t['accuracy_v3'] for t in trials) / len(trials)
    print(f'{cond}: v3_mean={v3:.4f}')
" | tee /tmp/v3_means.txt
# Manual: result.md / 노트북의 v3 mean 수치와 위 출력의 4-decimal 값이 (반올림 후) 일치하는지

# 3) 영문 노트북의 기존 v2 수치 변경 없음 — git diff
git diff docs/reference/researchNotebook.en.md | grep -E '^\+|\-' | grep -v '^[+-]{3}' | head -50
# Manual: '- ' (삭제) 라인이 모두 빈 라인 또는 placeholder 영역이고, 기존 결과 표 / key findings 의 v2 수치가 변경되지 않았는지

# 4) 한국어 노트북 / result.md 의 마크다운 형식 정합 (테이블 셀 수 일치 등)
.venv/bin/python -c "
import re
for path in ('docs/reference/results/exp-10-reproducibility-cost.md', 'docs/reference/researchNotebook.md'):
    with open(path) as f:
        text = f.read()
    # 테이블 row 의 | 개수 일관성 — 헤더와 데이터 row
    in_table = False
    header_pipes = 0
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            pipes = stripped.count('|')
            if not in_table:
                header_pipes = pipes
                in_table = True
            elif pipes != header_pipes:
                print(f'{path}:{i} table row pipes mismatch: {pipes} vs {header_pipes}')
        else:
            in_table = False
print('table check ok')
"
```

4 명령 모두 정상 + grep 출력 0 라인 + table check ok.

## Risks

- **`<FILL>` 누락**: Task 03/04 결과를 손에 잡지 않고 본 task 진행 시 placeholder 가 그대로 남음. Verification step 1 의 grep 으로 차단.
- **영문 노트북 정책 위반**: 기존 v2 수치 우발적 수정 시 정책 위반. Verification step 3 의 git diff 로 검증.
- **Markdown 테이블 깨짐**: 새 column 추가 시 separator (`---:`) 도 같이 수정 필요. Verification step 4 의 pipe 개수 일관성 검사.
- **v3 우선순위 #5 의 부분 완료**: logic-04 외 task 의 v2/v3 격차 발견되면 §7 에 별도 patch 후보로 명시 — 단, 격차 없으면 단순 "logic-04 만 영향, 다른 task v2==v3 확인" 으로 완료.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` / `experiments/orchestrator.py` / `experiments/tasks/taskset.json` — 다른 task 영역.
- v2 final JSON / v3 rescored JSON — read-only (단순 read 만, 갱신 안 함).
- `docs/reference/exp10-v2-finalize-2026-04-29.md` (작업 절차 문서) — 본 task 에서 변경 안 함. v3 plan 별도 흐름.
- `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` — Task 04 영역 (read 만).
- 다른 result.md (`exp-00-baseline.md` ~ `exp-09-longctx.md` 등) — 본 plan 범위 밖.
