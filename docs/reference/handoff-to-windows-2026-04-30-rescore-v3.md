---
type: handoff
status: pending
updated_at: 2026-04-30
from: Mac (Coder Claude · Implementer)
to: Windows (Architect/Developer)
plan_slug: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
---

# Handoff — Phase 1 후속 정리 (Mac → Windows, rescore_v3 재실행)

**Plan**: `phase-1-taskset-3-fail-exp09-5-trial-exp10-v3` (4 subtask)
**Mac 완료**: Task 00 (Taskset 3 FAIL 수정) + Task 01 (Exp09 5-trial 분석)
**Windows 진행**: Task 02 (Exp10 v3 재산정) + Task 03 (문서 갱신)
**플랜 경로**: `docs/plans/phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md`

---

## 1. Mac 측 완료 사항 (이번 commit 에 push)

### Task 00 — Taskset 3 FAIL 수정 ✅

| 파일 | 변경 |
|------|------|
| `experiments/tasks/taskset.json` | math-03 prompt: 96→88 + "round = square + 2" 추가 / synthesis-04 keywords: `[["reports","5","6"]]` |
| `experiments/tasks/longctx_taskset.json` | longctx-medium-2hop-02 expected: `"500 horsepower (500 hp)"` |
| `experiments/validate_taskset.py` | `_validate_math_03` 의 88 + r=s+2 constraint 동기화 |

**Verification**: `python -m experiments.validate_taskset` → **22 PASS / 0 FAIL / 0 WARN / 0 SKIP**

### Task 01 — Exp09 5-trial 점수 하락 원인 분석 ✅

| 파일 | 용도 |
|------|------|
| `experiments/exp09_longctx/analyze_5trial_drop.py` | 분석 스크립트 (정적, LLM 호출 0) |
| `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` | 분석 보고서 (placeholder 0) |

**핵심 결론**: **(c) 시스템 결함 단독**.
- rag/solo trial 4-5: `[WinError 10061] 대상 컴퓨터에서 연결을 거부했으므로` (20/20)
- abc trial 4-5: `num_assertions=0, final_answer=null` (error swallowed, 20/20)
- **검산 정확 일치**: `3-trial mean × 3/5 = 5-trial mean` (0.883×0.6=0.530 ✓ / 0.850×0.6=0.510 ✓)
- 모델 비결정성 / sampling 변동 0. trial 1-3 의 답변은 3-trial JSON 과 5-trial JSON 에서 10/10 task 일치.
- **H9b 함의**: 5-trial 통계로 `Inconclusive` 강등은 부당한 강등. 3-trial 결과 (Δ=+0.033) 가 여전히 가장 정확. verdict 환원 또는 disclosure 추가 권고. (verdict 환원은 Architect 결정 — 본 plan Task 03 의 영문 노트북 / researchNotebook 갱신 시 반영)

### Plan 문서 (5개, 이번 commit)

- `docs/plans/phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md`
- `phase-1-taskset-3-fail-exp09-5-trial-exp10-v3-task-01.md` ~ `-task-04.md`

---

## 2. Windows 측 진행 작업

### Task 02 (file `task-03.md`) — Exp10 v3 재산정

**의존성**: Task 00 완료 (이번 commit pull 후 자동 충족) + `validate_taskset` 22/22 PASS.

#### Step 1 — pull + validate 사전 검사

```powershell
git pull --ff-only
.venv\Scripts\python -m experiments.validate_taskset
# 기대: 22 PASS / 0 FAIL
```

#### Step 2 — rescore_v3 재실행 (사용자 직접, 메모리 정책)

```powershell
.venv\Scripts\python -m experiments.exp10_reproducibility_cost.rescore_v3
```

- 정적 채점, LLM 호출 0, 짧은 실행 시간
- 새 출력: `experiments\exp10_reproducibility_cost\results\exp10_v3_rescored_<TS>.json`
- **직전 canonical**: `exp10_v3_rescored_20260429_053939.json` (이번 결과와 비교 대상)

#### Step 3 — Δ 식별 (Task 03 입력)

```powershell
.venv\Scripts\python -c "
import json, glob
files = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))
prev = json.load(open([f for f in files if '053939' in f][0]))
curr = json.load(open(files[-1]))
from collections import defaultdict
def agg(d):
    a = defaultdict(lambda: {'n':0,'v3':0.0})
    for t in d['trials']:
        a[t['condition']]['n'] += 1
        a[t['condition']]['v3'] += t.get('accuracy_v3', 0)
    return {c: x['v3']/x['n'] for c, x in a.items()}
p, c = agg(prev), agg(curr)
for cond in ('gemma_8loop','gemini_flash_1call','gemma_1loop'):
    print(f'{cond:24} prev={p[cond]:.4f}  curr={c[cond]:.4f}  Δ={c[cond]-p[cond]:+.4f}')
"
```

기대: math-03 / synthesis-04 변동만 반영된 condition mean Δ 출력. 다른 task 보존.

#### Step 4 — task-level Δ break-down

`task-03.md` 의 Step 4 명령 실행 → `math-03` 와 `synthesis-04` 의 condition × task 별 Δ 출력. 다른 task 의 Δ ≈ 0 확인.

### Task 03 (file `task-04.md`) — 문서 갱신 통합

Task 02 의 Δ 결과를 5개 문서에 반영:

1. **`docs/reference/results/exp-10-reproducibility-cost.md`** — §2/§3 mean_acc · per-task 표 갱신 + Δ disclosure ("Phase 1 후속 taskset 정정 반영, Δ <FILL>")
2. **`docs/reference/results/exp-09-longctx.md`** — `### 5-trial 점수 하락 분석 (2026-04-30 Phase 1 후속)` 섹션 추가. 본 handoff 의 Task 01 결론 + `exp09-5trial-drop-analysis-2026-04-30.md` 인용
3. **`docs/reference/researchNotebook.md`** (한국어) — Exp09 (5-trial 분석 결론) + Exp10 (v3 재산정 결과) + Taskset 3 FAIL 정정 disclosure
4. **`docs/reference/researchNotebook.en.md`** — **Closed 추가만**. `5-trial drop analysis note (2026-04-30)` + `v3 rescore note 2 (2026-04-30, taskset patched)`. 기존 영문 수치 변경 0.
5. **`README.md` / `README.ko.md`** — **조건부**:

   | Δ 크기 | 처리 |
   |--------|------|
   | \|Δ\| < 0.01 | README 본문 변경 0 (사소) |
   | 0.01 ≤ \|Δ\| < 0.03 | Headline 의 78.1% / 41.3% 등 수치 갱신 (한·영) |
   | \|Δ\| ≥ 0.03 | Headline + H1 evidence + Roadmap 갱신, 외부 노출 약속 회수 명시 |

### Verification (Task 03 마무리)

`task-04.md` 의 5개 명령:
1. result.md 의 §2 mean_acc 가 새 v3 결과와 일치 (Python assertion)
2. 5-trial 분석 보고서 placeholder 0 (`grep -E '<FILL[^>]*>' ... | wc -l` → 0)
3. 영문 노트북에 "v3 rescore note" 카운트 = 2 (2026-04-29 + 2026-04-30)
4. 한·영 README 외부 노출 톤 검사 (banned 명칭 부재)
5. Markdown table pipe 정합 (변경 영역)

---

## 3. 환경 차이 / 주의사항

- **WinError 10061 재발 위험**: Task 02 의 rescore_v3 는 정적 채점이라 모델 서버 호출 없음. 그러나 이전 5-trial 작업에서 `http://yongseek.iptime.org:8005` 연결 거부가 발생한 사실 — Phase 2 / Mixed Intelligence 등 후속 LLM 호출 작업 전 서버 healthcheck 권고.
- **메모리 정책**: rescore_v3 는 사용자 직접 실행 (LLM 호출 0 이지만 task-03.md 명시).
- **영문 노트북**: Closed 추가만 정책. 기존 v3 rescore note (2026-04-29) 변경 절대 금지.
- **scope boundary**: Task 03 가 손대면 안 되는 파일 목록은 `task-04.md` 의 `## Scope boundary` 섹션 참조.
- **Untracked 유지 파일**: `exp10_v3_rescored_20260429_045819.json` / `_052748.json` 은 직전 plan (Exp10 v3 patch) 의 시도 잔여물. canonical 인 053939 만 추적 — 직전 commit `8477981` 의 정책 일관성. 이번에도 untracked 유지.

---

## 4. 빠른 시작 (요약)

```powershell
# 1. pull
git pull --ff-only

# 2. validate (Task 00 검증)
.venv\Scripts\python -m experiments.validate_taskset

# 3. rescore_v3 재실행 (Task 02)
.venv\Scripts\python -m experiments.exp10_reproducibility_cost.rescore_v3

# 4. Δ 식별 (Task 02 보고)
# (handoff §2 Step 3 / Step 4 명령)

# 5. 문서 갱신 (Task 03 — 5개 문서, Δ 분기 적용)

# 6. push
git add ... ; git commit -m "..." ; git push
```

---

## 5. 참조

- **현재 plan**: `docs/plans/phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md`
- **Mac 분석 보고서**: `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`
- **이전 v3 canonical**: `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260429_053939.json`
- **이전 v2 final** (rescore 입력): `experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json`
