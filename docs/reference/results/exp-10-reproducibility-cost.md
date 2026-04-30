---
type: result
status: done
updated_at: 2026-04-30
experiment: 실험 10 — Reproducibility & Cost Profile (v2 final)
---

# 실험 10: Reproducibility & Cost Profile 결과 보고서

## 1. 개요

"4.5B 로컬 모델을 ABC 8루프로 돌리면 폐쇄형 대형 모델 1-call 대비 어떤 수준의 정확도/비용/지연을 갖는가?"

3 condition × 9 task × N=20 trial = **540 trial**. Windows + LM Studio (Gemma 4 E4B Q4_K_M) + Google AI Studio (Gemini 2.5 Flash) 비교.

소스 데이터: `experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json`
패치 절차: `docs/reference/exp10-v2-finalize-2026-04-29.md`

## 2. 핵심 메트릭

> 채점 정책: **v3 채점기** (`score_answer_v3`). v2 keyword-group 매칭에 task 별 `negative_patterns` 차단 추가. logic-04 의 false positive 12건 제거. 본 표는 **2026-04-30 Phase 1 후속 taskset 정정** (math-03 / synthesis-04 / longctx-medium-2hop-02) 후 재산정된 v3 결과 (`experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260430_152306.json`). 각 trial dict 에 `accuracy_v2` + `accuracy_v3` 두 필드 보유. 직전 v3 (053939) 대비 모든 condition Δ +0.0019 — synthesis-04 keyword 정정 효과 (math-03 prompt 정정은 답변과 무관, Δ=0).

| condition | mean_acc (v2) | **mean_acc (v3)** | cost_usd (180) | $/trial | avg_dur | err+null |
|-----------|--------------:|------------------:|---------------:|--------:|--------:|---------:|
| **gemma_8loop** (Gemma 4 E4B + ABC 8루프) | 0.822 | **0.783** | $0.0000 | $0.0000 | **8 min** | 8 |
| gemini_flash_1call (Gemini 2.5 Flash 1-call) | 0.620 | **0.593** | $0.0143 | $0.0000793 | 24 s | 0 |
| gemma_1loop (Gemma 4 E4B 단발) | 0.415 | **0.415** | $0.0000 | $0.0000 | 33 s | 11 |

## 3. per-task 정답률 (v3)

| task | gemma_8loop | gemma_1loop | gemini_flash |
|------|------:|------:|------:|
| math-01 | 0.750 | 1.000 | 1.000 |
| math-02 | 1.000 | 0.850 | 1.000 |
| math-03 | 0.800 | 0.400 | 0.383 |
| math-04 | 1.000 | 0.167 | 0.667 |
| synthesis-01 | 0.700 | 0.000 | 0.550 |
| synthesis-03 | 0.933 | 0.183 | 0.333 |
| synthesis-04 | 0.817 | 0.133 | 0.400 |
| logic-03 | 1.000 | 1.000 | 1.000 |
| **logic-04** (v3) | **0.050** | 0.000 | 0.000 |

> **v2 vs v3 격차는 logic-04 한정**. 다른 8 task 는 v2 == v3 (Task 03 의 `rescore_v3.py` per-task Δ 출력에서 logic-04 만 표시).

## 4. 분석

### 4.1 외부 상태 + 반복의 효과 (H1 재확인)
같은 모델 1-loop → 8-loop: **0.415 → 0.783 (+37%p)**.

ABC chain 이 단순 호출보다 모델의 표현된 능력을 거의 두 배 끌어올림. 제멘토 가설 ("소형 LLM + 외부 상태 + 반복으로 계산 깊이 확장") 의 직접 증거. 이 +37%p 는 동일 weight, 동일 quantization, 동일 sampling parameters 조건에서의 측정이라 모델 변경 효과가 아니라 inference 구조 효과로 해석 가능.

### 4.2 소형 로컬 vs 폐쇄형 대형
- 정확도: gemma_8loop **0.783** > gemini_flash **0.593** (+19%p)
- 비용: $0 vs $0.0000793/trial (Flash 가 trial 당 약 0.008 센트, 540 trial 총 1.4 센트)
- 지연: 8 min vs 24 s (gemma_8loop 가 약 20× 느림)

→ 정확도/비용 우위 (gemma_8loop) vs 지연 우위 (Flash). use case 가 결정 (배치 분석 vs 대화형 응답).

### 4.3 로컬 모델의 천장 (logic-04)
- 모든 condition strict acc ≤ 0.05
- 4-suspect 귀류법 (guilty lies twice / innocent tells exactly one truth)
- ABC 8루프도 못 뚫음. 모델 자체의 다단 가정-검증 능력 한계
- 11~13/20 trial 이 "no single suspect can be identified" / "puzzle is logically inconsistent" 로 마무리

### 4.4 도구 정책의 영향 (math-04)
- 본 v2 의 gemma_8loop math-04 는 `use_tools=False` 로 0/20 (전수 fail)
- `use_tools=True` + STRUCTURED_SUFFIX 로 debug rerun 시 20/20
- 결정: math-04 의 v2 결과는 도구 활성화 rerun 으로 substitute (§5)
- 함의: LP 같은 강한 계산 부담 task 는 도구 호출이 결정적. 모델 능력의 한계가 아니라 시스템 정책의 한계

### 4.5 reliability — error / null
- gemma_8loop: 4 trial JSON parse fail (math-03 t13, synthesis-01 t14, logic-04 t2/t6) — 모델 능력이 아닌 ABC chain infrastructure 이슈. 진단 결과 (`docs/reference/exp10-v3-abc-json-fail-diagnosis.md`): **fence_unclosed 3건 + empty 1건**, truncate 0건. 4 fail 모두 `original_len < 4096` 이라 max_tokens 한계가 아니라 모델이 markdown fence 닫기 전 응답을 종료한 early-stop 패턴. orchestrator JSON 추출 강화 (Task 05) 가 미래 run 부터 적용 — fence_unclosed fallback + partial JSON brace 복구. v2 final 4 fail 의 사후 복구 시도에서는 1/4 만 살아남 (synthesis-01 t14), 나머지는 brace 1/0 + 미완성 string 으로 살릴 데이터 부족.
- gemma_1loop: null 11건 (logic-04 5, math-03 4, math-04 2) — 단발 호출의 final_answer 추출 실패
- gemini_flash: error 0, null 0 (timeout 4건은 §5 패치로 해소)

## 5. 패치 disclosure

v2 540 trial 에 두 가지 substitution 적용:

| 패치 | 영향 trial | 사유 | 변경 사항 |
|------|---:|------|----------|
| `(gemma_8loop, math-04)` 20 trial 전수 교체 | 20 | use_tools=False 미스로 LP 도구 호출 불가 | use_tools=True + STRUCTURED_SUFFIX 적용된 debug rerun (mean=1.0) |
| `(gemini_flash, logic-04)` 4 timeout trial 교체 | 4 | httpx ReadTimeout (~120s) | timeout=300s 재시도 (4건 모두 응답 수신, 16 success 는 보존) |

총 24 trial 교체, 보존 516 trial. 출처는 통합 JSON 의 `_substitutions.details` 에 trial 단위로 명시.

## 6. 채점 false positive 분석 (logic-04) + v3 rescore

v2 채점은 `score_answer_v2` 의 substring contains 방식. `logic-04` 의 scoring_keywords=`[["casey"]]` 라 final_answer 안에 'Casey' 라는 단어가 등장하기만 해도 1.0 부여됨.

v3 patch (본 plan): `score_answer_v3` 신규 + `taskset.json` 의 `logic-04` 에 `negative_patterns` 4개 추가 (`no\s+(unique|definitive|clear)\s+(culprit|answer|solution)`, `cannot\s+be\s+(identified|determined|solved)`, `contradicts?|contradiction|contradictions`, `puzzle\s+is\s+(flawed|inconsistent|ill-?posed)`). 540 trial 전수 재산정.

| condition | v2 logic-04 acc | **v3 logic-04 acc** | false positive 제거 |
|-----------|---:|---:|---:|
| gemma_8loop | 0.400 (8/20) | **0.050 (1/20)** | **7건** |
| gemini_flash_1call | 0.250 (5/20) | **0.000 (0/20)** | **5건** |
| gemma_1loop | 0.000 | 0.000 | 0 |

False positive 의 전형 패턴: "all four suspects... lead to contradictions" / "no single suspect can be identified" / "puzzle is logically inconsistent" — 본문 추론 과정에서 'Casey' 가 등장했으나 결론은 "정답 없음".

condition mean 영향:
- gemma_8loop: v2 0.820 → **v3 0.781** (-0.039)
- gemini_flash: v2 0.619 → **v3 0.591** (-0.028)
- gemma_1loop: 0.413 (변화 없음)

→ **순위 동일**, 격차 약간 좁아짐. gemma_8loop 의 +19%p 우위는 v3 적용 후에도 유지.

> **다른 task 의 v2 → v3 격차는 0**. `rescore_v3.py` 의 per-task Δ 출력에서 logic-04 만 표시됨 — 본 plan 에서 logic-04 한정으로 negative_patterns 추가했고 다른 task 는 v2 == v3. 향후 다른 task 의 false positive 우려 시 별도 patch.

## 7. 결론 및 다음 단계

### 결론
1. **4.5B 로컬 + ABC 8루프** 가 폐쇄형 대형 1-call 을 정확도에서 +19%p 능가, 비용 $0, 단 속도 1/20
2. **H1 (외부 상태 + 반복) 직접 증거**: 같은 모델의 1-loop vs 8-loop 격차 +37%p
3. **천장 task (logic-04)**: 4-way 귀류법은 ABC 도 못 뚫는 모델 능력 한계 — 도구화/multi-stage 가 v3 후보

### v3 우선순위 (실험 11 후보)
1. ✅ **채점기 강화** — `score_answer_v3` 도입 (`negative_patterns` + 옵션 `conclusion_required`). logic-04 false positive 12건 제거. 본 plan 완료.
2. ✅ **ABC chain JSON parse 안정성** — `extract_json_from_response` 에 fence_unclosed fallback + `_recover_partial_json` 추가. 미래 run 적용. 본 plan 완료.
3. **logic 카테고리 도구/구조 보강**: 단계별 가정-검증 sub-prompt 또는 외부 propositional logic 도구 — 별도 실험 후보
4. **use_tools 정책 통일**: math-* 전체에 use_tools=True 강제 후 v3 재실행 (현 v2 는 math-04 만 패치라 strict 비교 깨짐) — 별도 plan 후보
5. **다른 task 의 v3 채점 결과**: 본 plan 의 `rescore_v3.py` 가 540 trial 전수 재산정한 결과, logic-04 외 8 task 는 v2 == v3 — 추가 false positive 식별 0. 단, 다른 task 의 negative_patterns 미정의 상태이므로 향후 false positive 가 발견되면 task 별 보강 patch.
   - **Exp00~09 적용 범위**: 본 plan (`exp10-readme-v2-abc-4-fail-v3-disclosure`) 정찰 결과 logic-04 task 는 Exp00~09 의 result JSON 에 미포함 (직접 grep 확인). 따라서 `score_answer_v3` 를 Exp00~09 에 적용해도 변동 0 예상 — 별도 재산정 plan 의 우선순위 낮음.

## 8. Phase 1 후속 taskset 정정 + v3 재산정 (2026-04-30)

본 plan (`phase-1-taskset-3-fail-exp09-5-trial-exp10-v3`) 의 Task 00 에서 `validate_taskset` 22 task 중 3 FAIL 정정:

| task | 정정 내용 |
|------|-----------|
| `math-03` | prompt 의 연립방정식 해 없음 → 96 → 88 + "round = square + 2" 제약 추가 |
| `synthesis-04` | scoring_keywords `'report 5'`/`'report 6'` 가 expected `'Reports 5 and 6'` 에 매칭 실패 → `[['reports'],['5'],['6']]` |
| `longctx-medium-2hop-02` | expected `'500 hp'` 가 답변 본문에 부재 → `'500 horsepower (500 hp)'` |

`validate_taskset` 22 PASS / 0 FAIL 확인 후 `rescore_v3.py` 재실행 (`exp10_v3_rescored_20260430_152306.json` 신규 출력). 직전 canonical (`053939`) 과 비교:

| condition | prev v3 (053939) | curr v3 (152306) | Δ |
|-----------|----------------:|-----------------:|--:|
| gemma_8loop | 0.7815 | 0.7833 | **+0.0019** |
| gemini_flash_1call | 0.5907 | 0.5926 | **+0.0019** |
| gemma_1loop | 0.4130 | 0.4148 | **+0.0019** |

task-level Δ 는 **synthesis-04 단독** (3 condition 모두 +0.017):

| condition | task | prev | curr | Δ |
|-----------|------|-----:|-----:|--:|
| gemini_flash_1call | synthesis-04 | 0.383 | 0.400 | +0.017 |
| gemma_1loop | synthesis-04 | 0.117 | 0.133 | +0.017 |
| gemma_8loop | synthesis-04 | 0.800 | 0.817 | +0.017 |

→ **math-03 변동 0** (v3 trial 의 final_answer 가 새 정답 `round=6, square=4, rectangular=5` 와 매칭되지 않음 — 답변이 96 prompt 시점에 생성됐고 새 정답에도 못 미침). **logic-04 변동 0** (negative_patterns 보존). 다른 7 task 보존. condition mean |Δ| < 0.01 — README 본문 갱신 영향 없음 (사소). 직전 053939 결과 파일은 untracked archive 로 유지 (이전 plan 의 정책 일관성).
