---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-readme-v2-abc-4-fail-v3-disclosure
parallel_group: A
depends_on: []
---

# Task 01 — v2 ABC 4 fail 사후 분석 (모든 cycle × phase)

## Changed files

- `experiments/exp10_reproducibility_cost/diagnose_json_fails.py` — **수정**. 기존 `diagnose()` 가 마지막 cycle 의 fail phase raw 만 점검 (line 70-100 부근). `--full-cycles` 옵션 추가하여 모든 cycle × 모든 phase (a/b/c) 의 raw 를 v3 patch 적용된 `extract_json_from_response` 에 통과시키는 분기 추가.
- `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` — **수정**. 기존 "rework r2" 절 다음에 "v2 final 4 fail 사후 분석 (full cycles)" 절 신규 추가. 결과 표 + retry 권고.

신규 파일 0.

## Change description

### 배경

직전 plan (`exp10-v3-scorer-false-positive-abc-json-parse`) 의 Task 04 진단:

| trial | fail_phase | kind | original_len |
|-------|-----------|------|-------------:|
| math-03 t13 | A | fence_unclosed | 930 |
| synthesis-01 t14 | B | fence_unclosed | 500 |
| logic-04 t2 | A | fence_unclosed | 870 |
| logic-04 t6 | A | empty | (raw 없음) |

orchestrator v3 patch (`_recover_partial_json` + fence_unclosed fallback) 적용 후 **마지막 cycle 의 fail phase raw 만** 시도 → 1/4 사후 복구 (synthesis-01 t14 만).

본 task 는 **모든 cycle × 모든 phase 의 raw** 를 점검:
- 각 trial 의 `_debug.abc_logs` 가 cycle 1~10+ 보유
- 각 cycle 마다 a/b/c 3개 phase 의 raw 보유
- 마지막 cycle 의 fail phase 외 다른 위치에 살릴 raw 가 있는지 확인
- 살릴 raw 가 final_answer 단서를 가지고 있는지 점검

### Step 1 — `diagnose_json_fails.py` 에 `--full-cycles` 옵션 추가

기존 `diagnose()` 함수 (line 70-110) 다음 또는 분기 추가. 신규 함수 또는 옵션 분기:

```python
def diagnose_full_cycles(input_path: Path) -> list[dict]:
    """모든 cycle × 모든 phase 의 raw 를 v3 patch 된 extract_json_from_response 에 통과."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from orchestrator import extract_json_from_response

    with open(input_path, encoding="utf-8") as f:
        d = json.load(f)
    by_key = {(t["condition"], t["task_id"], t["trial"]): t for t in d["trials"]}
    rows = []
    for key in TARGETS:
        t = by_key.get(key)
        if t is None:
            continue
        debug = t.get("_debug") or {}
        logs = debug.get("abc_logs") or []
        recoverable: list[dict] = []
        for log in logs:
            for phase in ("a", "b", "c"):
                raw = log.get(f"{phase}_raw") or ""
                if "... (truncated" in raw:
                    raw = raw.split("... (truncated")[0]
                parsed = extract_json_from_response(raw)
                if isinstance(parsed, dict):
                    final_candidate = parsed.get("final_answer") or parsed.get("answer") or parsed.get("conclusion")
                    recoverable.append({
                        "cycle": log.get("cycle"),
                        "phase_name": log.get("phase"),
                        "phase_role": phase.upper(),
                        "keys": list(parsed.keys())[:5],
                        "final_candidate": str(final_candidate)[:120] if final_candidate else None,
                    })
        rows.append({
            "key": list(key),
            "trial_error": t.get("error"),
            "total_cycles": len(logs),
            "recoverable_count": len(recoverable),
            "recoverable": recoverable,
        })
    return rows
```

`main()` 에 `--full-cycles` 인자 추가:

```python
parser.add_argument("--full-cycles", action="store_true",
                    help="모든 cycle × 모든 phase 의 raw 점검 (기본은 마지막 cycle fail phase 만)")
...
if args.full_cycles:
    rows = diagnose_full_cycles(Path(args.input))
else:
    rows = diagnose(Path(args.input))
```

### Step 2 — 진단 실행 + 결과 분석

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails --full-cycles
```

stdout 결과를 분석하여 각 trial 별로:
- `total_cycles`: 진단된 cycle 수
- `recoverable_count`: 복구 가능 raw 개수
- `recoverable[]`: 각 복구 가능 raw 의 cycle, phase, 추출 키, final_candidate (있으면)

→ 4 trial 별 retry 권고 결정:
- `recoverable_count > 0` + `final_candidate` 있음 → "복구 가능 — final_answer 후보 X" 보고
- `recoverable_count > 0` 이지만 final_candidate 없음 (assertion 등 중간 단계만) → "부분 복구 — 최종 답 미확정"
- `recoverable_count == 0` → "복구 불가 — 윈도우 측 retry 만 가능"

### Step 3 — `exp10-v3-abc-json-fail-diagnosis.md` 끝에 절 추가

기존 "### r2 출력" 절 다음에 추가:

```markdown
## v2 final 4 fail 사후 분석 (full cycles, 2026-04-29)

직전 plan 의 Task 04 진단은 **마지막 cycle 의 fail phase raw** 만 점검. 본 절은 모든 cycle × 모든 phase (a/b/c) 의 raw 를 v3 patch 된 `extract_json_from_response` 에 통과시킨 결과.

### 결과 표

| trial | total_cycles | recoverable_count | retry 권고 |
|-------|-------------:|------------------:|-----------|
| math-03 t13 | <FILL> | <FILL> | <FILL> |
| synthesis-01 t14 | <FILL> | <FILL> | <FILL> |
| logic-04 t2 | <FILL> | <FILL> | <FILL> |
| logic-04 t6 | <FILL> | <FILL> | <FILL> |

### 함의

(diagnose 결과에 따라 작성)
- "X trial 은 cycle N 의 phase Y 에서 final_answer 후보 발견 — 추가 ABC infrastructure patch 후 재실행 가치 있음"
- 또는 "4 trial 모두 복구 불가 — 모든 cycle 의 raw 도 fence_unclosed 또는 부분 데이터. 윈도우 측 retry 가 유일한 방법"
- 또는 mixed
```

`<FILL>` 자리는 진단 실행 결과로 대체.

## Dependencies

- 직전 plan 의 산출물 의존: `experiments/orchestrator.py` 의 `_recover_partial_json` + `extract_json_from_response` v3 patch (이미 commit 됨)
- v2 final JSON: 이미 commit 됨 (`exp10_v2_final_20260429_033922.json`)
- 패키지: 표준 `json`, `argparse`. 신규 의존성 0.
- 다른 subtask: 없음. parallel_group A 의 시작점.

## Verification

```bash
# 1) 정적 import + 도움말 출력 (신규 옵션 보유)
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails --help
# 기대: '--full-cycles' 옵션 표시

# 2) 기존 동작 회귀 없음 (옵션 없이 실행)
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails 2>&1 | tail -10
# 기대: 4 trial 분류 (kind=fence_unclosed/empty), summary 출력 — 직전 plan 결과와 동일

# 3) 신규 --full-cycles 실행
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails --full-cycles 2>&1 | tee /tmp/diag_full.log
# 기대: 4 trial 별 total_cycles + recoverable_count + recoverable[] 출력

# 4) 진단 문서에 신규 절 + placeholder 0개
grep -c "v2 final 4 fail 사후 분석 (full cycles" docs/reference/exp10-v3-abc-json-fail-diagnosis.md
# 기대: 1
grep -E '<FILL[^>]*>' docs/reference/exp10-v3-abc-json-fail-diagnosis.md | wc -l
# 기대: 0 (모든 placeholder 채워짐)
```

4 명령 모두 정상 + grep 카운트 일치.

## Risks

- **`_debug.abc_logs` 의 raw 가 4KB truncate 본**: original 4KB 초과 trial 은 끝이 잘려 fence_unclosed 분류만 가능. 사후 복구 한계 — disclosure 명시.
- **다른 phase (b_raw, c_raw) 가 빈 문자열일 가능성**: orchestrator 의 `_serialize_abc_logs` 가 phase 미실행 시 빈 raw 저장. 빈 raw 는 자동으로 `extract_json_from_response` 가 None 반환 → recoverable_count 에서 자동 제외.
- **final_answer 키 명 다양성**: 모델이 `final_answer` / `answer` / `conclusion` 중 어느 키를 쓸지 cycle 마다 다를 수 있음. Step 1 의 코드에서 3 키 모두 시도.
- **diagnose() 와 diagnose_full_cycles() 출력 schema 다름**: stdout 파서가 두 모드 구분 필요 — 기본 모드는 직전 plan 패턴 유지, 신규는 별도 schema. 사용자 검수 시 모드 명시.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` — 직전 plan 영역. v3 patch 그대로 사용.
- `experiments/measure.py` / `experiments/tasks/taskset.json` — 직전 plan 영역.
- v2 final JSON — read-only.
- `docs/reference/results/exp-10-reproducibility-cost.md` — Task 02 영역.
- `docs/reference/researchNotebook.md` / `.en.md` — Task 02/03 영역.
- `README.md` / `README.ko.md` — Task 03 영역.
- `experiments/exp10_reproducibility_cost/rescore_v3.py` / `merge_v2_final.py` / `run_logic04_flash_retry.py` — 직전 plan 영역, 변경 0.
