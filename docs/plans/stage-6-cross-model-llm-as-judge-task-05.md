---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: stage-6-cross-model-llm-as-judge
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + Stage 6 verdict + paper v0.4 + 문서 갱신

## Changed files

- `docs/reference/stage6-cross-model-analysis-<TS>.md` — **신규**. 분석 보고서
- `docs/reference/all-hypotheses-statistics.md` — **신규** (P1-4). H1/H7/H8/H9a Bootstrap CI 재산정 + 5 가설 통일 5튜플 표
- `docs/reference/results/exp-stage6-cross-model.md` — **신규**. Stage 6 result.md
- `docs/reference/researchNotebook.md` — **수정**. H14 (cross-model) + H15 (LLM-as-judge) entry + Stage 6 섹션 append + frontmatter
- `docs/reference/researchNotebook.en.md` — **수정 (Closed-append-only)**. ## Stage 6 섹션 + frontmatter `updated_at`. 표 / 기존 entry 무변경
- `docs/plans/index.md` — **수정**. Active → Recently Done — Stage 6 이동
- `docs/plans/stage-6-cross-model-llm-as-judge.md` + task-NN — **수정**. status: done
- `docs/paper/draft.md` — **수정**. **v0.4 갱신** — §4.3 cross-model 본문 + §4.6.2 / §4.7.2 의 LLM-as-judge 결과 통합 + §7 Conclusion 작성
- `README.md` / `README.ko.md` — **사용자 결정** 후 갱신
- `docs/reference/paper-review-action-items-2026-05-05.md` — **수정**. P1-1/P1-3/P1-4/P1-5 status 갱신

신규 3, 수정 7+ (사용자 결정 시).

## Change description

### 활용 권장 — `gemento-verdict-record` 스킬

본 task = `gemento-verdict-record` 스킬의 두 번째 본격 활용 (Exp14 task-05 다음). 영문 노트북 Closed-append-only 정책 + 한국어 노트북 동시 갱신 + index.md 이동 일괄 처리.

### Step 1 — 결과 정합성 확인

```bash
.venv/Scripts/python -c "
import json, os
from collections import defaultdict
results_dir = 'experiments/cross_model/results'
files = [f for f in os.listdir(results_dir) if f.endswith('.json') and f.startswith('stage6_')]
print(f'Stage 6 result files: {files}')
for f in files:
    with open(os.path.join(results_dir, f)) as fh:
        d = json.load(fh)
    # model + hypothesis + trial 수 확인
    print(f'  {f}: {len(d.get(\"trials\", []))} trials')
"
```

### Step 2 — Cross-model 분석 (per-model × per-hypothesis)

각 모델 × 가설의 Δ + Cohen's d + p-value + Bootstrap CI 산출. Stage 5 baseline (Gemma 4 E4B) 과 비교.

```python
# stage6_analysis.py (인라인 또는 별도 helper)

results = {}
for model_key in ('qwen_25_7b_local', 'llama_3_1_8b_groq', 'llama_3_3_70b_groq'):
    for hyp in ('h10', 'h11', 'h12', 'h13'):
        if not has_data(model_key, hyp):
            continue
        # paired stats
        delta, cohen_d, p_wilcoxon, p_t, ci = compute_stats(model_key, hyp)
        # Stage 5 baseline 비교
        gemma_delta = STAGE5_DELTAS[hyp]
        direction_match = (delta * gemma_delta > 0)  # sign 일치 여부
        results[(model_key, hyp)] = {
            "delta": delta, "cohen_d": cohen_d, "p": p_wilcoxon,
            "ci": ci, "direction_match_with_gemma": direction_match,
        }
```

핵심 표 (Stage 6 분석 보고서의 main contribution):

| Hypothesis | Gemma Δ | Qwen 7B Δ | Llama 8B Δ | Llama 70B Δ | Direction match |
|---|---|---|---|---|---|
| H10 (Mixed) | −0.081 | ? | ? | ? | ? |
| H11 (Extractor +) | +0.050 | ? | ? | ? | ? |
| H12 (Reducer −) | −0.053 | ? | ? | ? | ? |
| H13 (Search SIG−) | −0.220 | ? | ? | ? | ? |

→ H14 verdict: direction-consistent across models?

### Step 3 — LLM-as-judge 분석 (H12 + H13 의미적 채점)

```python
# H12 / H13 의 trial 별 judge_verdict 집계
judge_results = {
    "h12": {
        "keyword_acc_delta": ...,  # 본 plan 의 새 측정
        "judge_acc_delta": ...,    # 본 plan 의 새 측정
        "delta_difference": judge - keyword,  # scorer artifact 의 양
    },
    "h13": {...},
}
```

**핵심 질문**:
- H12 의 keyword Δ=−0.053 vs judge Δ=? — judge 가 Δ ≈ 0 이면 *keyword scorer artifact 다수*. judge 도 음수면 *real abstraction loss*
- H13 의 keyword Δ=−0.220 vs judge Δ=? — 단답형 task 라 차이 작을 가능성 높음

→ H15 verdict: keyword scorer 가 H12 / H13 의 음수 결과를 얼마나 *artificially 만든* 것인지 정량화.

### Step 4 — 통계 5튜플 통일 (P1-4)

기존 Stage 1-4 의 H1 / H7 / H8 / H9a 의 결과 JSON 에서 Bootstrap CI 재산정 + 통일 표 작성:

`docs/reference/all-hypotheses-statistics.md`

| H | Δ | n | p (Wilcoxon) | Cohen's d | 95% CI |
|---|---|---|---|---|---|
| H1 | +0.367 (Exp10) | 9 task × 60 trial | (재산정) | (재산정) | (재산정) |
| H7 | +0.183 (math-04 0→80%) | 1 task × 50 trial | (재산정) | (재산정) | (재산정) |
| H8 | +0.233 | 1 task × 50 trial | (재산정) | (재산정) | (재산정) |
| H9a | +0.683 | 3 large × 5 trial | (재산정) | (재산정) | (재산정) |
| H10~H13 | (Stage 4-5 기존) | 15 / 10 task | 이미 5튜플 | | |

### Step 5 — 분석 보고서 신규

`docs/reference/stage6-cross-model-analysis-<TS>.md`. Exp14 분석 보고서 형식 정확 복제 — 단 다음 추가:

- §1-2 cross-model aggregate (per-model × per-hypothesis)
- §3 direction consistency 분석 (Stage 5 baseline 과의 sign 일치율)
- §4 LLM-as-judge 보조 결과 (H12 / H13)
- §5 keyword vs semantic scoring 차이 (artifact 정량화)
- §6 Stage 5 통합 narrative cross-model 검증
- §7 paper §4.3 채울 수 있는 핵심 표 + 단락

### Step 6 — paper draft v0.4 갱신

- §4.3 Cross-model held-out: 본 plan 결과로 본문 채움. direction consistency / LLM-as-judge 결과 통합
- §4.6.2 caveat 갱신: H12 의 LLM-as-judge 결과로 keyword scorer artifact 정량화 (또는 보강)
- §4.7.2 caveat 갱신: H13 동일
- §5.3 Implications: cross-model 결과 통합
- §7 Conclusion: 2 단락 작성 (사용자 결정 — 신중 표현)
- Abstract: 최종 수치 확정 + 갱신
- §6 Limitations: 단일 시도 vs 다중 시도 차이 명시

### Step 7 — researchNotebook 갱신 (한·영)

**한국어** (`researchNotebook.md`):
- frontmatter `updated_at` → 마감일
- 핵심 가설 표 H14 + H15 row 추가 (cross-model + LLM-as-judge)
- 축 매트릭스 Stage 6 row 추가
- `### Stage 6: Cross-model + LLM-as-judge` 섹션 append

**영문** (`researchNotebook.en.md`, **Closed-append-only**):
- frontmatter `updated_at` → 마감일
- `## Stage 6 — Cross-model + LLM-as-judge note (<date>)` 섹션을 `## Change History` 직전에 insert
- 본문 마지막 boilerplate: `The hypothesis table above (H1~H13) remains unchanged (Closed-append-only policy). H14/H15's entries are new additions only.`

### Step 8 — index.md + plan status

- `docs/plans/index.md`: Active 의 stage-6 라인 제거 + Recently Done 에 추가 (Δ + verdict + 한 줄 요약 + 날짜)
- `docs/plans/stage-6-*.md` + task-NN: status: done

### Step 9 — README 갱신 (사용자 결정 의무)

- README.md / README.ko.md 의 핵심 가설 표 H14 + H15
- "What worked / What didn't" 섹션 cross-model 단락
- Roadmap entry
- Last updated

### Step 10 — paper review action items 갱신

`docs/reference/paper-review-action-items-2026-05-05.md`:
- P1-1 (Related Work 차별화) — Stage 6 마감 시 함께 또는 후속
- P1-3 (LLM-as-judge) — **done**
- P1-4 (통계 5튜플 통일) — **done** (`all-hypotheses-statistics.md`)
- P1-5 (논문 구조 reorder) — paper v0.4 에서 적용 여부 결정

### Step 11 — 통합 commit (분할 권장 — scope 큼)

```bash
# commit 1: 결과 데이터
git add experiments/cross_model/results/stage6_*.json
git commit -m "data(stage-6-task-04): cross-model + LLM-as-judge 결과"

# commit 2: 분석 보고서 + 문서
git add docs/reference/stage6-cross-model-analysis-*.md \
        docs/reference/all-hypotheses-statistics.md \
        docs/reference/results/exp-stage6-cross-model.md \
        docs/reference/researchNotebook.md \
        docs/reference/researchNotebook.en.md \
        docs/plans/index.md \
        docs/plans/stage-6-*.md
git commit -m "docs(stage-6-task-05): Stage 6 verdict + 문서 통합"

# commit 3: paper v0.4
git add docs/paper/draft.md docs/reference/paper-review-action-items-2026-05-05.md
git commit -m "docs(paper): v0.4 — cross-model + LLM-as-judge 통합"

# commit 4 (사용자 결정 후): README
git add README.md README.ko.md
git commit -m "docs(readme): Stage 6 H14/H15 entry"
```

## Dependencies

- task-04 마감 (사용자 직접 실행 결과 JSON N 종)
- 기존 분석 보고서 (Exp11/12/13/14) — 패턴 참조
- `gemento-verdict-record` 스킬 — 영문 노트북 정책 강제
- `scipy` — 통계 검정

## Verification

```bash
# 1) 분석 보고서 + result.md + 통계 통일 표 신규
ls docs/reference/stage6-cross-model-analysis-*.md
ls docs/reference/all-hypotheses-statistics.md
ls docs/reference/results/exp-stage6-cross-model.md

# 2) 영문 노트북 정책 검증
.venv/Scripts/python -c "
import re
with open('docs/reference/researchNotebook.en.md', 'r', encoding='utf-8') as f:
    content = f.read()
assert '## Stage 6 — Cross-model' in content
assert 'H1~H13' in content  # 기존 boilerplate 패턴
table_rows = [l for l in content.split('\n') if re.match(r'^\| H[0-9]', l)]
print(f'H## table rows (Closed): {len(table_rows)} — 기존 11 row 그대로')
"

# 3) paper draft v0.4 갱신
.venv/Scripts/python -c "
with open('docs/paper/draft.md', 'r', encoding='utf-8') as f:
    content = f.read()
# §4.3 의 [TBD] placeholder 가 채워졌는지
assert '[TBD: replication of H1' not in content, '§4.3 still placeholder'
print('paper draft v0.4 ok')
"

# 4) plan status
.venv/Scripts/python -c "
import re
for p in ['docs/plans/stage-6-cross-model-llm-as-judge.md',
          'docs/plans/stage-6-cross-model-llm-as-judge-task-04.md',
          'docs/plans/stage-6-cross-model-llm-as-judge-task-05.md']:
    with open(p) as f: c = f.read()
    assert re.search(r'^status: done', c, re.MULTILINE), f'{p} status'
print('plan status ok')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — cross-model 결과 의 direction inconsistency**: Stage 5 (Gemma) 와 sign 다를 시 paper main claim 약화. *honest reporting* 의무 — direction consistency 의 % 명시 + cause 분석
- **Risk 2 — LLM-as-judge 의 self-bias**: GPT-OSS 가 baseline 또는 treatment 답변 스타일 선호 가능. order randomization 결과 보존 + bias 분석 (50% A/B swap 의 winner 분포 검증)
- **Risk 3 — paper draft v0.4 의 over-claim 회귀**: P0 톤다운 정신 (action items 의 GPT 피드백) 적용 의무 — *direction consistent* / *partial replication* 표기, "validated" / "confirmed" 사용 금지
- **Risk 4 — Sonnet 의 영문 노트북 정책 위반**: 표 / 기존 entry 변경 금지. `gemento-verdict-record` 스킬 안전 패턴 적용
- **Risk 5 — README 갱신 임의 진행**: 사용자 결정 의무. 명시 동의 없이 변경 금지
- **Risk 6 — placeholder 0 의무**: 모든 분석 보고서의 `<TS>`, `<file>`, 수치 placeholder 채움. 빈 곳 없음
- **Risk 7 — paper v0.4 의 §7 Conclusion 작성 부담**: 본 task 의 가장 큰 작업. 사용자 검토 후 final 이전 *draft only* 권장

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/**/*.py` (코드)
- `experiments/**/results/*.json` (결과 데이터, Stage 5 + Stage 6)
- `experiments/tasks/*.json` (taskset)
- `docs/reference/conceptFramework.md` (별도 plan 영역)
- 다른 실험의 분석 보고서 / result.md (Stage 1-5 영역)

본 task 에서 **변경 가능**:
- `docs/reference/stage6-cross-model-analysis-<TS>.md` (신규)
- `docs/reference/all-hypotheses-statistics.md` (신규, P1-4)
- `docs/reference/results/exp-stage6-cross-model.md` (신규)
- `docs/reference/researchNotebook.md` (한국어, 표 + 매트릭스 + 섹션 + frontmatter)
- `docs/reference/researchNotebook.en.md` (영문, **append-only**)
- `docs/plans/index.md`
- `docs/plans/stage-6-*.md` + task-NN (status: done)
- `docs/paper/draft.md` (v0.4 갱신)
- `docs/reference/paper-review-action-items-2026-05-05.md` (P1 status)
- `README.md` / `README.ko.md` (**사용자 결정 후만**)
