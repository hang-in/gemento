---
type: reference
status: done
updated_at: 2026-04-29
author: Architect Claude (developer mode)
---

# Exp10 v2 final ABC JSON parse 4 fail 진단

## 배경

v2 final 540 trial (`experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json`) 중 gemma_8loop 의 4 trial 이 `experiments/orchestrator.py:extract_json_from_response` 실패. 본 문서는 각 trial 의 `_debug.abc_logs` 마지막 cycle 의 raw 분석 결과.

진단 스크립트: `experiments/exp10_reproducibility_cost/diagnose_json_fails.py`

## 진단 결과

| condition | task | trial | fail_phase | kind | original_len | brace open/close | tail50 (raw 끝) |
|-----------|------|------:|-----------:|------|-------------:|------------------|-----------------|
| gemma_8loop | math-03 | 13 | A | **fence_unclosed** | 930 | 1 / 0 | `$T = R - 1$ and the total table count ($R + S + T` |
| gemma_8loop | synthesis-01 | 14 | B | **fence_unclosed** | 500 | 4 / 3 | `the stated hourly cost for Provider B."\n    },\n  ` |
| gemma_8loop | logic-04 | 2 | A | **fence_unclosed** | 870 | 1 / 0 | `$), then $\neg A, \neg B, \neg C$.\n*   A: ($\neg A` |
| gemma_8loop | logic-04 | 6 | A | **empty** | — | — / — | (raw 자체 빈 문자열) |

## 분류 요약

- **truncate**: 0
- **fence_unclosed**: 3
- **empty**: 1

## 함의 (Task 05 patch 방향)

진단 결과 4 fail 모두 4096 char 미만 (`original_len` 가 500~930) — `_truncate_raw` 의 4KB limit 한계가 원인이 아님. 즉 **모델이 markdown fence 시작 후 닫는 ` ``` ` 까지 도달하기 전에 응답을 종료**한 것. max_tokens 한계가 아니라 LM Studio + Gemma 4 E4B 의 early stopping 또는 응답 폭주 후 abort.

Task 05 의 patch 우선순위:

1. **fence_unclosed fallback** — 닫는 fence 없이 시작 fence 만 발견된 경우, fence 시작 다음부터 raw 끝까지 잘라 lenient parse 시도. 3 trial 의 다수 케이스 처리.
2. **partial JSON brace 복구** — synthesis-01 t14 의 `brace_open=4, brace_close=3` 같은 거의 완성된 partial 의 경우, last_complete_close 까지 잘라 시도 + 부족한 `}` 채우기. fence_unclosed fallback 만으로 풀리지 않는 케이스 보강.
3. **empty 케이스 처리** — logic-04 t6 의 raw 자체 빈 문자열은 patch 로 살릴 수 없음. extract_json_from_response 의 `if not raw: return None` 가드 그대로 둠.

## 본 v2 final 의 4 fail 재산정 가능 여부

- 3 trial (`fence_unclosed`) 은 raw 가 4KB 미만이라 `_debug.abc_logs[-1].a_raw` (또는 b_raw) 가 곧 모델 원본 응답. Task 05 patch 적용 후 `extract_json_from_response` 재호출로 partial JSON 복구 가능 여부 점검 가치 있음.
- 1 trial (`empty`) 은 `_debug` 자체에 raw 가 비어 있어 복구 불가 — orchestrator patch 무관.
- 다만 본 plan 의 success 기준은 미래 run 적용. v2 final 4 fail 의 사후 복구는 별도 후속 결정 (raw 가 a/b/c 중 fail phase 본만 검사된 상태라 다른 phase raw 도 살펴볼 가치 있음).

## 비고

- LM Studio 의 `max_tokens=4096` 설정 (`experiments/config.py:SAMPLING_PARAMS`) 은 진단 4건 모두 한참 안 넘김. 모델 자체의 응답 종료 트리거가 별도 — 향후 디버깅 항목.
- 4 fail 중 3 건이 phase A (Assertion 생성), 1 건이 phase B (Critique). C 단계 fail 0 — Cycle 후반부의 ABC 실행이 더 안정적이라는 정황.
- 마지막 cycle phase_name 이 모두 `VERIFY` 단계 — phase 전이 후 LLM 재호출이 fail 위치. `VERIFY` phase 의 prompt 길이 또는 컨텍스트 누적이 모델 응답 종료 트리거와 관련 있을 가능성 (별도 후속).

---

## 부록: logic-04 채점 정책 검증 (rework r1, 2026-04-29)

리뷰어 finding (`experiments/measure.py:83`): 초기 v3 patch 의 `negative_patterns` 가 응답 전체에서 `contradicts?|contradiction|contradictions` 를 즉시 차단해, 정상 귀류법 풀이의 추론 본문에 'contradiction' 단어가 등장하기만 해도 0.0 처리 위험. plan 의도 ("모순 결론 답 차단") 보다 과도하게 넓은 차단.

### 패치 (Task 01 영역)

`experiments/tasks/taskset.json` 의 logic-04 정의:
- `negative_patterns` 에서 본문 추론 단어 (`contradicts?|contradiction|contradictions`) 제거
- `negative_patterns` 를 **명시적 결론 표현** 만 유지 + 보강:
  - `no\s+(\w+\s+)?(solution|answer|culprit|suspect)` (no _ solution/answer/culprit/suspect)
  - `cannot\s+be\s+(identified|determined|solved)`
  - `puzzle\s+is\s+(flawed|inconsistent|ill-?posed)`
  - `puzzle.{0,40}is\s+logically\s+inconsistent`
  - `impossible\s+to\s+(definitively\s+)?(identify|determine|solve)`
- `conclusion_required` 신규 추가 (tail 200 char 검사 — `score_answer_v3` 의 2단계):
  - `^\s*casey\b` (단답 'Casey')
  - `casey\s+(committed|killed|murdered|did\s+it)`
  - `casey\s+is\s+(\w+\s+){0,3}(culprit|criminal|murderer|killer|guilty)`
  - `(culprit|criminal|murderer|killer)\s+is\s+casey`

### 케이스 검증

다음 시뮬레이션으로 새 정책의 false negative / false positive 부재 검증.

| # | 케이스 | 답안 | 새 정책 점수 | 의도 |
|---|--------|------|------------:|------|
| 1 | 단답 | `Casey` | **1.0** | true positive ✓ |
| 2 | 짧은 결론 | `Casey committed the crime.` | **1.0** | true positive ✓ |
| 3 | 귀류법 + 명시적 결론 (본문에 'contradiction') | `Assuming Alex is guilty leads to a contradiction. Same for Blake and Dana. Therefore, Casey is the culprit.` | **1.0** | **finding 해소 — 정상 귀류법 답안 false negative 없음** ✓ |
| 4 | 긴 분석 + 결론 | `... Alex, Blake, and Dana each lead to inconsistencies. Casey is the only consistent culprit.` | **1.0** | true positive ✓ |
| 5 | 동사 형태 | `... the conclusion is that Casey did it.` | **1.0** | true positive ✓ |
| 6 | 역순 표현 | `... the murderer is Casey.` | **1.0** | true positive ✓ |
| 7 | false positive (retry t17 실제 답) | `... contradiction ... If Alex, Blake, or Casey are guilty ... a definitive culprit cannot be identified.` | **0.0** | false positive 차단 ✓ |

### 60 trial 전수 재검증

새 정책을 v2 final 의 logic-04 60 trial 에 적용한 결과:

| condition | new logic-04 acc | 기존 v3 logic-04 acc | 일치 여부 |
|-----------|---:|---:|:-:|
| gemma_8loop | 0.050 (1/20) | 0.050 (1/20) | ✓ |
| gemini_flash_1call | 0.000 (0/20) | 0.000 (0/20) | ✓ |
| gemma_1loop | 0.000 (0/20) | 0.000 (0/20) | ✓ |

→ **차단력 동일 보존**, 60 trial 분류 결과 100% 일치. 새 정책은 정상 귀류법 답안의 false negative 위험만 제거하고 false positive 차단력은 유지.

### 출력

- 새 결과 JSON: `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260429_052748.json` (rework r1 재산정)
- 이전 결과 JSON `exp10_v3_rescored_20260429_045819.json` 은 archive 로 유지 (수치 동일이라 substantive 차이 없음)
- condition aggregate (v3): gemma_8loop 0.7815 / gemini_flash 0.5907 / gemma_1loop 0.4130 (불변)

### rework r2 (2026-04-29): negative_patterns 첫 정규식 좁힘

리뷰어 finding 2차 (`taskset.json:254`): 첫 `negative_patterns` 가 `no\s+(\w+\s+)?(solution|answer|culprit|suspect)` 로 'suspect' 단어를 포함하면 **"No other suspect fits the rules. Casey is the culprit."** 같은 정상 결론 답안에서 `'no other suspect'` 부분이 매칭돼 0.0 처리되는 false negative 위험.

**패치**: `suspect` 를 첫 정규식에서 제거하고, '명시적 부정 결론' 표현인 `"no single _"` 만 별도 정규식으로 추가:

| 항목 | r1 (이전) | r2 (현재) |
|------|-----------|-----------|
| `no\s+(\w+\s+)?(solution\|answer\|culprit\|suspect)` | 첫째 | — (좁힘) |
| `no\s+(\w+\s+)?(solution\|answer\|culprit)` | — | **첫째** ('suspect' 제거, 'no other suspect' false negative 차단) |
| `no\s+single\s+(culprit\|suspect\|answer)` | — | **둘째** (gemma t11 의 'no single culprit' 같은 명시적 부정 결론은 잡되, 'no other suspect' 같은 가정/구분 표현은 안 잡음) |
| `cannot\s+be\s+(identified\|determined\|solved)` | 둘째 | 셋째 (위치 변경, 내용 동일) |
| 나머지 3개 | 그대로 | 그대로 |

### 추가 검증 케이스 (rework r2)

| # | 케이스 | 답안 | r2 점수 | 의도 |
|---|--------|------|--------:|------|
| A | finding r2 케이스 (no other suspect + Casey 결론) | `No other suspect fits the rules. Casey is the culprit.` | **1.0** | **finding r2 해소** ✓ |
| B | 변형 (no one else fits + Casey 동사) | `After exhaustive analysis, no one else fits all constraints. Casey committed the crime.` | **1.0** | true positive ✓ |
| C | 1차 rework 케이스 (본문 contradiction + Casey 결론) | `... leads to a contradiction. Therefore, Casey is the culprit.` | **1.0** | rework r1 결과 보존 ✓ |
| D | 단답 | `Casey` | **1.0** | true positive 보존 ✓ |
| E | false positive (gemma t11 'no single culprit') | `... assuming any of the four suspects is guilty leads to a contradiction. Therefore, no single culprit can be identified under these conditions.` | **0.0** | 차단 유지 ✓ (`no\s+single\s+culprit` 매칭) |
| F | false positive (retry t17 'cannot be identified') | `... a definitive culprit cannot be identified.` | **0.0** | 차단 유지 ✓ |

### r2 60 trial 전수 재검증

새 정책 적용 후 logic-04 condition 별 결과:

| condition | r1 logic-04 acc | r2 logic-04 acc | 일치 |
|-----------|---:|---:|:-:|
| gemma_8loop | 0.050 (1/20) | 0.050 (1/20) | ✓ |
| gemini_flash_1call | 0.000 (0/20) | 0.000 (0/20) | ✓ |
| gemma_1loop | 0.000 (0/20) | 0.000 (0/20) | ✓ |

→ **r1 결과와 100% 동일**. 60 trial 의 실제 답안에는 'no other suspect' / 'no one else fits' 같은 표현이 등장하지 않아 (`grep` 결과 0/60 hits) 차단력에 영향 없음. r2 fix 는 가상 false negative 위험 제거 + plan 의도 ("최종 부정 결론 표현만 차단") 와의 정합성 확보.

### r2 출력

- 새 결과 JSON: `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260429_053939.json` (rework r2 재산정)
- condition aggregate: 변동 없음 (gemma_8loop 0.7815 / gemini_flash 0.5907 / gemma_1loop 0.4130)
- r1 결과 JSON `exp10_v3_rescored_20260429_052748.json` 도 archive 유지

---

## v2 final 4 fail 사후 분석 (full cycles, 2026-04-29)

직전 진단은 **마지막 cycle 의 fail phase raw** 만 점검 → 1/4 사후 복구 (synthesis-01 t14). 본 절은 plan `exp10-readme-v2-abc-4-fail-v3-disclosure` Task 01 의 결과로, **모든 cycle × 모든 phase (a/b/c)** 의 raw 를 v3 patch 된 `extract_json_from_response` 에 통과시킨 결과.

진단 명령:

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails --full-cycles
```

### 결과 표

| trial | total_cycles | recoverable_count | final_candidate 발견 | retry 권고 |
|-------|-------------:|------------------:|---------------------:|-----------|
| math-03 t13 | 10 | 13 | **0** | 윈도우 측 retry 만 (사후 복구 불가) |
| synthesis-01 t14 | 10 | 15 | **0** | 윈도우 측 retry 만 (사후 복구 불가) |
| logic-04 t2 | 12 | 17 | **0** | 윈도우 측 retry 만 (사후 복구 불가) |
| logic-04 t6 | 11 | 5 | **0** | 윈도우 측 retry 만 (사후 복구 불가) |

**총 50개 raw 가 lenient parse 통과** — 그러나 모두 ABC chain 의 중간 단계 (`DECOMPOSE`/`INVESTIGATE`/`SYNTHESIZE`/`VERIFY` phase 의 A/C raw, 또는 SYNTHESIZE-B 1건). 추출된 키는 `reasoning` / `handoff_a2b` / `new_assertions` / `invalidated_assertions` / `judgments` / `converged` / `next_phase` 등 — `final_answer` / `answer` / `conclusion` 키는 **0 hit**.

### 함의

1. **ABC 중간 단계는 안정적**: 4 trial 모두 cycle 1~12 동안 다수 raw 가 v3 patch 후 정상 parse. orchestrator 의 `_recover_partial_json` + fence_unclosed fallback 가 actual 데이터에서 동작 확인.
2. **최종 답 (final_answer) 만 일관되게 fail**: VERIFY phase 의 마지막 cycle 의 fail phase raw 가 모델의 early-stop 으로 fence 미닫힘 + final_answer 키 미생성. 즉 **모델이 답을 결론낼 때마다 응답을 끝내는 LM Studio + Gemma 4 E4B 의 패턴**일 가능성.
3. **사후 복구 불가**: 4 trial 모두 final_answer 단서 부재 → orchestrator patch 만으로는 복구 안 됨. 윈도우 측 retry 만 결정적 경로 (단, 같은 패턴이 재발할 위험 있음).

### retry 결정

본 plan (`exp10-readme-v2-abc-4-fail-v3-disclosure`) 의 success 기준 = **복구 가능 여부 판정** (Non-goals 에 retry 실행 제외 명시). 위 결과는:

- **재실행 가치 vs 비용 trade-off**: 4 trial 재실행은 윈도우 측 ~30 min~1h. v3 mean 변동 영향: 4 trial 모두 정답이라도 `gemma_8loop` mean 0.7815 → 0.7926 (+0.011, 약 +1.1%p). 외부 보고에 의미 있는 차이는 아님.
- **재발 위험**: VERIFY phase 의 early-stop 이 모델/환경 패턴이라면 재실행해도 같은 trial 들이 또 fail 할 가능성. 진정한 fix 는 ABC chain 의 prompt/sampling/max_tokens 조정 (별도 plan).

→ **윈도우 측 retry 의 우선순위 낮음 권고**. result.md / README 에 "ABC infrastructure 4 fail 의 사후 복구 불가 — 모델 early-stop 패턴, 별도 plan 후보" disclosure 로 충분.
