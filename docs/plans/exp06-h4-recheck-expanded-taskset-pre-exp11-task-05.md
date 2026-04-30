---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: exp06-h4-recheck-expanded-taskset-pre-exp11
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + H4 verdict 갱신 + 문서 통합

## Changed files

- `docs/reference/h4-recheck-analysis-2026-MM-DD.md` — **신규**. 분석 보고서 (placeholder 0)
- `docs/reference/results/exp-06-solo-budget.md` — **수정**. §6 (또는 새 §) 에 H4 재검증 결과 추가 + verdict 갱신
- `docs/reference/researchNotebook.md` (한국어) — **수정**. Exp06 후속 분석 섹션 추가 + H4 verdict 표 갱신
- `docs/reference/researchNotebook.en.md` — **수정 (Closed 추가만)**. "H4 recheck note (2026-MM-DD)" 신규 단락. 기존 영문 수치 변경 0
- (조건부) `README.md` / `README.ko.md` — H4 verdict 변경 시 H 표 갱신 (사용자 결정 의존)

신규 1, 수정 4 (README 조건부).

## Change description

### 배경

Task 04 의 실험 결과 (225 trial × 3 condition) 를 분석하여 H4 verdict 갱신. 본 task 가 Stage 2C 의 마무리 + Stage 3 (Exp11 의제) 진입 신호.

### Step 1 — Task 03 의 analyze.py 실행

```bash
# 옵션 A 사용 시 (분할) — 3 결과 파일 각각
.venv/Scripts/python -m experiments.exp_h4_recheck.analyze \
    --result experiments/exp_h4_recheck/results/h4_recheck_solo_1call.json
.venv/Scripts/python -m experiments.exp_h4_recheck.analyze \
    --result experiments/exp_h4_recheck/results/h4_recheck_solo_budget.json
.venv/Scripts/python -m experiments.exp_h4_recheck.analyze \
    --result experiments/exp_h4_recheck/results/h4_recheck_abc.json

# 또는 통합 (3 파일 merge 후 단일 분석) — 본 task 의 Step 1b 로 helper 추가
```

#### Step 1b — 분할 결과 merge helper (옵션 A 사용 시)

```python
# experiments/exp_h4_recheck/analyze.py 에 추가 함수 (subtask 03 의 영역이지만 본 task 에서 small extension)
def merge_results(*paths) -> dict:
    """여러 결과 JSON 의 trials 를 merge 하여 단일 분석 입력으로."""
    merged = None
    for p in paths:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        if merged is None:
            merged = dict(d)
            merged["trials"] = list(d["trials"])
        else:
            merged["trials"].extend(d["trials"])
    return merged
```

이 helper 는 Task 05 작성 시 Task 03 의 analyze.py 에 추가 (예외적 — Task 03 의 scope 외이지만 분석 통합 의무). 또는 Task 05 의 보고서 작성 script 안에 inline.

### Step 2 — 분석 결과 산출 (3 축 × 3 condition × 15 task)

다음 표를 분석 보고서에 포함:

#### 2a — condition aggregate

| condition | n | mean_acc_v3 | turnover_added (mean) | turnover_modified (mean) | NULL_ANSWER | WRONG_SYNTHESIS | CONNECTION_ERROR | OTHER |
|-----------|---|------------:|----------------------:|------------------------:|------------:|----------------:|----------------:|------:|
| solo_1call | 75 | <FILL> | 0 | 0 | <FILL> | <FILL> | <FILL> | <FILL> |
| solo_budget | 75 | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> |
| abc | 75 | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> | <FILL> |

#### 2b — ablation

| 비교 | Δ acc | 의미 |
|------|------:|------|
| solo_budget − solo_1call | <FILL> | 다단계 효과 (H1 재확인) |
| **abc − solo_budget** | **<FILL>** | **역할 분리 단독 효과 (H4 본 가설)** |
| abc − solo_1call | <FILL> | 합산 효과 |

#### 2c — task 별 break-down (15 task × 3 condition × acc)

| task_id | category | difficulty | solo_1call | solo_budget | abc | abc - solo_budget |
|---------|----------|-----------|----------:|-----------:|---:|------------------:|
| math-01 | math | medium | <FILL> | <FILL> | <FILL> | <FILL> |
| ... | ... | ... | ... | ... | ... | ... |

#### 2d — 통계적 검정 (paired Wilcoxon, n=15)

```python
from scipy.stats import wilcoxon
# task 별 mean acc paired
abc_per_task = [...]   # n=15
sb_per_task = [...]    # n=15
W, p = wilcoxon(abc_per_task, sb_per_task)
```

| 검정 | 통계량 | p-value | 판정 |
|------|--------|---------|------|
| Wilcoxon (abc vs solo_budget) | W=<FILL> | <FILL> | <FILL> |
| Paired t-test (abc vs solo_budget) | t=<FILL> | <FILL> | <FILL> |
| Bootstrap 95% CI Δ(abc−solo_budget) | <FILL> | — | <FILL> |

### Step 3 — H4 verdict 결정 트리

분석 결과로 H4 verdict 변경:

```
if abc - solo_budget ≥ +0.05 AND p < 0.05:
    verdict = "✅ 채택" (역할 분리 단독 효과 확인)
elif abc - solo_budget ≥ +0.05 AND p ≥ 0.05:
    verdict = "⚠️ 조건부 채택" (격차 있으나 통계적 유의성 미달)
elif |abc - solo_budget| < 0.05:
    if turnover_modified(abc) >= 1.5 × turnover_modified(solo_budget):
        verdict = "⚠️ 미결 — 정확도 격차는 작으나 질적 차이 (turnover) 확인"
    else:
        verdict = "❌ 기각 — 역할 분리 단독 효과 0"
elif abc - solo_budget < -0.05:
    verdict = "❌ 기각 — Solo-budget 가 ABC 보다 우수 (Exp06 정합 비교 동일 결론)"
else:
    verdict = "⚠️ 미결 — 추가 검증 필요"
```

**Architect 사전 예측** (확률):
- ✅ 채택: 30% (만약 새 planning task 에서 ABC 가 명확한 우위)
- ⚠️ 조건부 채택: 30%
- ⚠️ 미결: 20%
- ❌ 기각: 20% (Exp06 정합 비교 결과 패턴 지속)

→ 어느 결론이든 의미 있음. **기각** 도 Stage 3 의제 재검토 신호 (Mixed Intelligence 가설 동기 흔들림 — Search Tool 우선순위 상향).

### Step 4 — `docs/reference/h4-recheck-analysis-<TS>.md` 신규 보고서

날짜 stamp 사용 (`2026-MM-DD` — Task 04 실행일 기준). 형식:

```markdown
---
type: reference
status: done
updated_at: 2026-MM-DD
canonical: true
---

# Exp06 H4 재검증 분석 (확대 task set, 15 × 3 × 5)

**plan**: `exp06-h4-recheck-expanded-taskset-pre-exp11`
**실행일**: 2026-MM-DD
**조건**: Solo-1call / Solo-budget / ABC × 15 task × 5 trial = 225 trial

## 1. condition aggregate
(Step 2a 표 그대로)

## 2. ablation 결과 (3 비교)
(Step 2b 표 + 해석)

## 3. task 별 break-down
(Step 2c 표)

## 4. 통계적 검정
(Step 2d 표)

## 5. H4 verdict
(Step 3 의 트리 결과)

## 6. 함의
- Stage 3 (Exp11 의제) 영향: <FILL>
- Mixed Intelligence (Role 축 강화) 가설 정합성: <FILL>
- Search Tool / 다른 미외부화 축 우선순위 변경 후보: <FILL>

## 7. 비교 — Exp06 정합 비교 (2026-04-29) 와 본 결과
| 메트릭 | Exp06 (9 task × 5 trial) | 본 결과 (15 task × 5 trial) | Δ |
|--------|------------------------:|----------------------------:|--:|
| Solo (loop=N) acc | 0.967 (v2/v3) | <FILL> | <FILL> |
| ABC acc | 0.900 (v2/v3) | <FILL> | <FILL> |
| Δ (Solo − ABC) | +0.067 | <FILL> | <FILL> |

## 8. 한계
- 5 trial × 15 task = 75 paired data points/condition. Exp09 H9b 와 비슷한 검정력 한계 가능
- assertion turnover 의 evidence_ref 측정은 미구현 (heuristic 만)
- planning category 신규 — 기존 4 카테고리와 직접 비교 한계
```

`<FILL>` 자리는 Step 1-3 의 결과로 대체.

### Step 5 — `exp-06-solo-budget.md` 갱신

§6 (또는 새 §7) 에 H4 재검증 결과 추가:

```markdown
## 6. H4 재검증 (2026-MM-DD, Stage 2C)

확대 task set (12 → 15) + 3 condition (Solo-1call / Solo-budget / ABC) ablation:

| 비교 | Δ acc |
|------|------:|
| solo_budget − solo_1call (다단계 효과) | <FILL> |
| **abc − solo_budget (역할 분리 단독)** | **<FILL>** |
| abc − solo_1call (합산) | <FILL> |

H4 verdict (Step 3 트리): **<FILL>**.

상세: `docs/reference/h4-recheck-analysis-2026-MM-DD.md`.
plan: `exp06-h4-recheck-expanded-taskset-pre-exp11`.
```

기존 §1~§5 변경 0 (Exp06 원본 결과 보존).

### Step 6 — `researchNotebook.md` (한국어) 갱신

H4 verdict 표 갱신 + Exp06 섹션에 후속 분석 disclosure:

```markdown
| H4 | **[Role 외부화 시너지]** A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | <NEW VERDICT> (재검증 2026-MM-DD: <FILL>) | Exp06 + Stage 2C |
```

Exp06 섹션 끝에 disclosure 단락:

```markdown
**2026-MM-DD H4 재검증 (Stage 2C):** 확대 task set (15 task) + 3 condition ablation 결과 verdict <FILL>. 상세: `docs/reference/h4-recheck-analysis-2026-MM-DD.md`.
```

### Step 7 — `researchNotebook.en.md` 갱신 (Closed 추가만)

기존 영문 수치 / verdict 변경 절대 금지. **추가만**:

```markdown
**H4 recheck note (2026-MM-DD):**

A follow-up plan (`exp06-h4-recheck-expanded-taskset-pre-exp11`) re-evaluated H4 with an expanded task set (12 → 15 tasks, adding 2 planning tasks + 1 synthesis task) and a 3-condition ablation (Solo-1call / Solo-budget / ABC, max_cycles=8). 225 trials total.

Ablation results:
- Multi-loop effect (solo_budget − solo_1call): <FILL>
- Role-separation effect (abc − solo_budget): <FILL>  ← **H4 본 가설**
- Combined (abc − solo_1call): <FILL>

H4 verdict (post-recheck): **<FILL>**. Detail: `docs/reference/h4-recheck-analysis-2026-MM-DD.md`.

The original Exp06 H4 ⚠ 미결 entry above remains unchanged (Closed 추가만 정책).
```

### Step 8 — README 조건부 갱신 (사용자 결정)

H4 verdict 변경 영향:

| H4 변화 | README 영향 |
|---------|-----------|
| ⚠ 미결 → ✅ 채택 | H 표 갱신 (한·영) + 외부 노출 톤 강화 가능 |
| ⚠ 미결 → ❌ 기각 | H 표 갱신 (한·영) + 외부 노출 톤 약화 (Mixed Intelligence 가설 동기 흔들림 disclosure) |
| ⚠ 미결 → ⚠ 조건부 채택 | H 표 갱신 (한·영) — 본문 변경 작음 |
| ⚠ 미결 → ⚠ 미결 (재검 후 동일) | H 표의 verdict 부연 갱신 ("재검증 2026-MM-DD: 통계적 유의성 미달") |

**사용자 결정 의존**. Task 05 가 자동 진행 안 함 — 사용자 호출 후 진행.

## Dependencies

- Task 04 마감 (사용자 직접 실행)
- Task 03 의 analyze.py
- Task 01 의 새 task set
- 패키지: `scipy.stats` (Wilcoxon / t-test) — 미설치 시 설치 필요 (or numpy 기반 자체 구현 fallback)

## Verification

```bash
# 1) 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/h4-recheck-analysis-*.md | wc -l
# 기대: 0

# 2) result.md exp-06 의 H4 verdict 갱신 확인
.venv/Scripts/python -c "
text = open('docs/reference/results/exp-06-solo-budget.md', encoding='utf-8').read()
assert '재검증' in text or 'H4 재검증' in text
print('verification 2 ok')
"

# 3) researchNotebook 한·영 동기화
grep -c "H4 recheck note" docs/reference/researchNotebook.en.md
# 기대: 1 (Closed 추가만 — 새 단락 1)

# 4) 영문 노트북 기존 H4 entry 변경 0
.venv/Scripts/python -c "
text = open('docs/reference/researchNotebook.en.md', encoding='utf-8').read()
# H4 의 기존 verdict 표 entry 의 ⚠ 미결 텍스트가 그대로 보존
assert '⚠ 미결' in text or 'Inconclusive' in text or '미결' in text
print('verification 4 ok: 영문 H4 entry 보존')
"

# 5) Markdown table pipe 정합 (변경 영역)
.venv/Scripts/python -c "
files = (
    'docs/reference/results/exp-06-solo-budget.md',
    'docs/reference/researchNotebook.md',
    'docs/reference/h4-recheck-analysis-2026-MM-DD.md',  # 실제 파일명으로 치환
)
# (Stage 2A 의 Phase 1 후속 verification 5 와 동일 패턴)
print('pipe check — 직접 grep 또는 Python check')
"
```

5 명령 모두 정상.

## Risks

- **Risk 1 — H4 verdict 가 기각이면 Mixed Intelligence (Stage 3 Exp11 후보) 가설 동기 흔들림**: 사용자 + Architect 가 Stage 3 의제 재검토 — Search Tool 우선순위 상향 가능. 본 task 의 §함의 절에서 명시
- **Risk 2 — assertion turnover 의 측정 결함**: Tattoo history 가 Solo / ABC 에 일관 저장 안 되면 Δ 측정 불가. Task 02 의 Risk 4 와 연관 — 본 task 에서 발견 시 Task 02 보강 plan 별도
- **Risk 3 — 통계적 검정력 부족** (15 task × 5 trial paired Wilcoxon n=15): Exp09 H9b 와 비슷한 한계 가능. verdict 가 ⚠ 미결 결론이면 추가 task / trial 확대 plan 별도 — 본 plan 영역 외
- **Risk 4 — 영문 노트북 정책 위반**: 기존 H4 entry 의 영문 verdict 가 절대 변경되면 안 됨. Verification 4 의 grep 으로 검증 + 사용자 시각 검토
- **Risk 5 — Step 8 의 README 갱신 임의 진행**: 사용자 결정 의존. Developer 가 임의 README 수정 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/*` — 모두 read-only
- 결과 JSON (모두 read-only)
- 본 plan 의 다른 subtask 영역 (taskset / run.py / analyze.py / 결과 JSON) — read-only
- 다른 result.md (`exp-00-baseline.md` ~ `exp-10-reproducibility-cost.md` 중 exp-06 외) — 본 plan 영역 외
- 다른 reference 문서 (h4-recheck-analysis 만 신규)
- conceptFramework.md / experimentDesign.md — 변경 금지 (canonical 영역, H4 verdict 변경 disclosure 만 result.md / researchNotebook 에)

## 사용자 호출 시점

- Step 3 의 verdict 결정 트리에서 ⚠ 미결 결론 시 — 추가 검증 결정
- Step 8 의 README 갱신 — 사용자 결정 의무
- Risk 1 (Mixed Intelligence 가설 흔들림) 발생 시 — Stage 3 의제 재검토
- Risk 4 의 영문 노트북 정책 위반 발견 시
