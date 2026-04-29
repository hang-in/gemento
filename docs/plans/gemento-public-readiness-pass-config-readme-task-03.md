---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: A
depends_on: []
---

# Task 03 — Exp10 INDEX.md 최신화

## Changed files

- `experiments/exp10_reproducibility_cost/INDEX.md` — **수정**. "결과 파일 (task-06 후 채워짐)" 류 TBD / 상태 표현을 현재 결과 파일 (실제 results/ 디렉토리의 v2 final / v3 rescored / logic04 retry / math04 debug) 로 갱신.

신규 파일 0, 다른 파일 수정 0.

## Change description

### 배경

`experiments/exp10_reproducibility_cost/INDEX.md` (정찰 결과):

```markdown
## 결과 파일 (task-06 후 채워짐)

- `results/exp10_reproducibility_cost_*.json` — 540 trial 원본
- `results/exp10_report.md` — analyze.py 가 생성한 markdown report
```

문제:
- "task-06 후 채워짐" 은 Exp10 의 원래 plan (`exp10-reproducibility-cost`) 의 task 번호 — 이미 완료된 plan 의 잔재
- 실제 results/ 디렉토리에는 다음 파일들 존재 (직전 plan 산출물):
  - `exp10_reproducibility_cost_20260427_130235.json` (v1, 무효, archive)
  - `exp10_reproducibility_cost_20260428_175247.json` (v2 본 run)
  - `exp10_logic04_flash_retry_20260429_033743.json` (logic-04 retry)
  - `exp10_math04_8loop_debug_20260428_205650.json` (math-04 debug)
  - `exp10_v2_final_20260429_033922.json` (v2 통합 — canonical)
  - `exp10_v3_rescored_20260429_053939.json` (v3 재산정 — canonical)

### Step 1 — INDEX.md 의 결과 파일 섹션 갱신

기존 섹션:
```markdown
## 결과 파일 (task-06 후 채워짐)

- `results/exp10_reproducibility_cost_*.json` — 540 trial 원본
- `results/exp10_report.md` — analyze.py 가 생성한 markdown report
```

수정 (실제 산출물 명시):
```markdown
## 결과 파일

- `results/exp10_reproducibility_cost_20260428_175247.json` — v2 본 run 540 trial (Windows 측 산출)
- `results/exp10_logic04_flash_retry_20260429_033743.json` — gemini_flash logic-04 4 timeout 재시도 (timeout=300s)
- `results/exp10_math04_8loop_debug_20260428_205650.json` — gemma_8loop math-04 use_tools=True debug rerun (20 trial)
- `results/exp10_v2_final_20260429_033922.json` — math-04 + logic-04 patch 통합 v2 final (canonical)
- `results/exp10_v3_rescored_20260429_053939.json` — score_answer_v3 적용 540 trial 재산정 (canonical)
- 정식 보고서: `docs/reference/results/exp-10-reproducibility-cost.md`
- 패치 절차 disclosure: `docs/reference/exp10-v2-finalize-2026-04-29.md`, `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`
```

요구사항:
- "task-06 후 채워짐" 제거
- 실제 파일명 6개 (v1 archive 1 + v2 본 run 1 + retry 1 + debug 1 + v2 final 1 + v3 rescored 1 — 단 v1 은 무효라 archive 표기 또는 제외)
- canonical 파일 명시 (v2 final, v3 rescored)
- 정식 보고서 / 패치 절차 문서 포인터

### Step 2 — 다른 TBD 표현 점검

INDEX.md 전체 grep 으로 다른 TBD / 미정 표현 검색:

```bash
grep -n "TBD\|task-..*\s*후\|미정\|채워짐" experiments/exp10_reproducibility_cost/INDEX.md
```

evidence_ref 외 미정 표현 발견 시 동일 패턴으로 정리 (또는 "in progress" / "completed" 명확화).

### Step 3 — 하이퍼파라미터 / dispatcher key 보존

INDEX.md 의 다른 영역 (개요, dispatcher key, 하이퍼파라미터) 변경 금지 — 본 task 는 결과 파일 섹션만 갱신.

## Dependencies

- 패키지: 없음 (마크다운 편집)
- 다른 subtask: 없음. parallel_group A.

## Verification

```bash
# 1) "task-06 후 채워짐" / TBD 제거
grep -E "task-..\s*후|TBD|채워짐" experiments/exp10_reproducibility_cost/INDEX.md
# 기대: 0 라인

# 2) 실제 결과 파일명 명시 (v2 final + v3 rescored)
grep -c "exp10_v2_final_20260429_033922\|exp10_v3_rescored_20260429_053939" experiments/exp10_reproducibility_cost/INDEX.md
# 기대: 2 (둘 다 포함)

# 3) 정식 보고서 포인터 존재
grep "exp-10-reproducibility-cost.md\|exp10-v2-finalize\|exp10-v3-abc-json-fail-diagnosis" experiments/exp10_reproducibility_cost/INDEX.md
# 기대: 1+ 라인

# 4) 다른 영역 (개요 / dispatcher / 하이퍼파라미터) 보존
grep -c "dispatcher key\|하이퍼파라미터\|## 개요" experiments/exp10_reproducibility_cost/INDEX.md
# 기대: 변경 전과 동일 카운트
```

4 명령 모두 정상.

## Risks

- **실제 파일 존재 확인 안 됨**: INDEX.md 갱신 시 명시한 파일명이 실제 존재하지 않으면 사용자가 헷갈림. Verification 2 직전에 `ls experiments/exp10_reproducibility_cost/results/` 로 실제 존재 확인.
- **v1 archive 표기**: v1 (`exp10_reproducibility_cost_20260427_130235.json`) 은 Windows dirty state 로 무효 — INDEX 에서 제외 vs "(무효, archive)" 표기 둘 중 결정. 본 task 는 후자 권장 (이력 보존, 단 canonical 아님 명시).
- **다른 plan 의 산출물 포인터**: 본 task 는 직전 plan 의 산출물을 가리키는 포인터 추가. 직전 plan 의 result.md / disclosure 문서 경로가 정확한지 검증.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/exp10_reproducibility_cost/results/*.json` — read-only
- `experiments/exp10_reproducibility_cost/run.py` / `rescore_v3.py` / `merge_v2_final.py` / `run_logic04_flash_retry.py` / `diagnose_json_fails.py` / `run_math04_8loop_debug.py` — 직전 plan 영역
- `experiments/config.py` / `requirements.txt` — Task 01 영역
- `docs/reference/conceptFramework.md` — Task 02 영역
- `README.md` / `README.ko.md` — Task 04/05/06 영역
- INDEX.md 의 개요 / dispatcher key / 하이퍼파라미터 섹션 — 결과 파일 섹션만 갱신
- 다른 실험 디렉토리의 INDEX.md — 본 task 범위 밖
