---
type: handoff
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-30
from: Mac (Architect Claude · Architect / Coder Claude · Implementer)
to: Windows (Architect/Developer)
scope: Phase 1 후속 정리 마무리 + Exp11 이전 전략 합의 + 당분간 윈도우 주도
related_handoff: handoff-to-windows-2026-04-30-rescore-v3.md
related_plan: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
---

# Handoff — Phase 1 마무리 + Exp11 이전 전략 (Mac → Windows, 당분간 윈도우 주도)

## 0. 사용자 지시

> 이후 작업은 당분간 윈도우(오퍼스)에 다 넘기자.

→ 본 핸드오프 이후 **plan 진행, 작은 안정화 plan 작성, Exp11 주제 결정 분석** 까지 윈도우 Architect 가 주도. Mac 은 daemon 대기. 사용자 의사결정이 필요한 분기점만 사용자 호출.

---

## 1. 합의된 전략 — "작은 B"

GPT (gpt) ↔ Architect Claude (Mac) 두 라운드 토론 결론:

```text
Exp11 전에 큰 DB 인프라(SQLite full ledger / FTS / CJK / tool registry / 결과 import)를
한꺼번에 구축하지 않는다.

대신 (1) 직전 사고 재발 방지를 위한 작은 안정화만 선처리하고,
(2) Exp11 주제를 결정한 뒤,
(3) 그 실험이 실제로 요구하는 최소 인프라만 plan 내 sub-task 로 포함한다.
```

핵심 근거:
- 직전 신뢰성 결함 (Exp09 5-trial 0점 폭락) 의 원인은 **DB 부재가 아니라 `WinError 10061` + 빈 trial 저장**. healthcheck/abort 정책 부재가 원인.
- GPT 의 "최소 인프라" 는 사실 3~4 plan 규모 (실험 0건). ROI 부족.
- Vector/Graph/LLM diary/sync server/tattoo lifecycle 등은 **명시적 배제**.

상세 검토: 본 commit 의 대화 turn (Architect 검토 + GPT 정정) 참조 — 별도 문서화 불필요.

---

## 2. 진행 순서 (전체 시퀀스)

```text
[Stage 1] 현재 Phase 1 후속 plan 마무리 (이미 진행 중)
   ├── Task 02 (Exp10 v3 재산정)         ← rescore_v3 실행
   └── Task 03 (문서 갱신 통합)            ← 5개 문서

[Stage 2] 작은 안정화 plan (Architect 작성, Developer 구현)
   ├── multi-trial 실행 도구 healthcheck
   ├── 서버 연결 실패 시 retry/abort 정책
   ├── 빈 trial 저장 방지
   ├── 결과 JSON top-level meta 표준화
   └── scorer version / failure label 기록 정리

[Stage 3] Exp11 주제 결정 (사용자 + Architect)
   ├── Mixed Intelligence (Judge C 강한 모델 교체) — 인프라 거의 0
   └── Search Tool Externalization — 인프라 큼 (FTS, retrieval trace 등)

[Stage 4] Exp11 plan 작성 (주제 확정 후)
   └── 해당 실험에 필요한 최소 인프라만 plan 내부 sub-task

[Stage 5] (Exp11 후) SQLite ledger / FTS / Vector / Graph 재검토
```

---

## 3. Stage 1 — 즉시 작업 (Phase 1 마무리)

직전 핸드오프 `handoff-to-windows-2026-04-30-rescore-v3.md` 의 §2-§4 그대로. 요약:

- **Task 02** (file `task-03.md`): rescore_v3 사용자 직접 실행 → condition Δ + per-task Δ 식별 (math-03 / synthesis-04 만 변동, 다른 task v2==v3 보존)
- **Task 03** (file `task-04.md`): 5개 문서 갱신 (`exp-10-reproducibility-cost.md` / `exp-09-longctx.md` / `researchNotebook.md` / `researchNotebook.en.md` / README ko·en 조건부)
- 영문 노트북 **Closed 추가만** 정책 위반 금지
- README 갱신은 Δ 분기 (\|Δ\|<0.01 / 0.01~0.03 / ≥0.03) 적용

---

## 4. Stage 2 — 작은 안정화 plan 후보

직전 사고 재발 방지 + 즉시 ROI. **Stage 1 완료 후 윈도우 Architect 가 plan 화 권고**. 범위:

### 4.1 multi-trial 실행 도구 healthcheck + abort

**대상**: `experiments/exp09_longctx/run_append_trials.py` + 향후 모든 multi-trial 도구.

**현 동작**:
```python
result = _run_longctx_trial(arm, task_obj, trial_idx)
task_entry["trials"].append(result)  # error 여부 무관, 그대로 append
```

**문제**: connection refused → `result.error = "..."` + `final_answer=None` 인 빈 trial 그대로 append. 평균 score dilute.

**보강 후보**:
- (a) 매 N (예: 10) trial 마다 healthcheck (모델 서버 ping 또는 sentinel task 1건)
- (b) 단일 trial 의 error 가 connection refused / network 류면 즉시 abort + 부분 결과 유지 + 사용자 알림
- (c) 연속 K (예: 3) 회 error 시 abort
- (d) 결과 저장 직전 trial 별 `error is not None` 비율 검사 → 임계값 초과 시 저장 거부 + warning

권장: (b)+(d) 조합. (a)/(c) 는 후순위.

### 4.2 결과 JSON top-level meta 표준화

**현재 결과 JSON 메타 분산**:
- exp00~exp08: `model`, `experiment` 만 일관 — sampling_params / api_base 부재
- exp09: `model`, `arms`, `trials_per_task`, `chunk_size` 등
- exp10: `conditions`, `trials_per_condition`, `_substitutions`, `_v3_rescore` 등 — 다양

**제안 표준 필드** (top-level):
```json
{
  "experiment": "...",
  "schema_version": "1.0",
  "started_at": "...",
  "ended_at": "...",
  "model": {"name": "...", "engine": "ollama|lm_studio|gemini|...", "endpoint": "..."},
  "sampling_params": {"temperature": 0.7, "top_p": 0.9, "max_tokens": 2048, "seed": null},
  "scorer_version": "v2|v3",
  "taskset_version": "<git_short_hash>",
  "conditions": [...],
  "trials": [...]
}
```

→ analyze 스크립트 / 향후 SQLite import 시 정규화 비용 감소.

### 4.3 scorer version / failure label 기록 정리

- `experiments/measure.py` 의 score_answer_v0/v2/v3 의 변천 + 적용 범위 단일 reference 문서로 통합
- failure label (json_parse_fail / evidence_miss / wrong_synthesis / format_error 등) 명시적 enum 정의 — 현재는 ad-hoc 라벨링 (Exp10 v3 ABC JSON parse 분석 등에서 부분 사용)

### 4.4 plan 작성 시 주의

- **명시 배제**: SQLite ledger, FTS, vector, graph, diary 등은 본 안정화 plan 에 포함 금지
- **scope creep 방지**: healthcheck / meta 표준화 / scorer 정리 까지. 그 이상은 별도 plan
- **변경 영향**: 기존 결과 JSON 의 backward compat 유지 — 새 schema_version 도입 시 기존은 v0/암묵 처리

---

## 5. Stage 3 — Exp11 주제 결정 의제

**사용자 의사결정 필요**. 윈도우 Architect 가 의제 정리 후 사용자 호출.

### 후보 비교 (Architect 분석 입력)

| 항목 | Mixed Intelligence | Search Tool Externalization |
|------|-------------------|----------------------------|
| 정의 | Judge C 만 강한 모델 (Gemini Pro / Claude Sonnet 등) 로 교체. A/B 는 Gemma E4B 유지 | 외부 검색 도구 (BM25/FTS) 를 도입. no-search / context-dump / FTS / ABC+search 비교 |
| 자연 후속 | Exp08 (Tool) → Exp09 (RAG) → Exp10 (cost) → **외재화의 "검증자 분리" 축** | Exp08/09 의 retrieval 라인 연속 |
| 인프라 비용 | 거의 0 (이미 multi-model 호출 가능) | 큼 — FTS 라이브러리 / tool registry / retrieval_trace / (선택) CJK |
| Hypothesis | H10 후보: "강한 Judge 가 약한 Proposer 의 한계를 보완" | H11 후보: "Search 외재화가 context dump 보다 효율" |
| 사용자 의도 (현재 plan Non-goals) | "Plan #1 결과 보고 후 별도 큰 plan" 으로 명시 | 미언급 |
| 의사결정 비용 | 낮음 (모델만 교체) | 높음 (검색 라이브러리 / tokenizer 선정) |

### 권장 (Architect Mac)

**Mixed Intelligence 우선**. 이유:
1. 사용자 명시 의도와 일치
2. 인프라 추가 0 — Stage 2 안정화만 끝나면 즉시 가능
3. Exp11 결과 후 Search 는 Exp12 로 자연 연속

단 사용자 의사결정 필수 — 윈도우 Architect 는 위 표와 권장을 사용자에게 제출 + 확정 후 plan 작성.

### Exp11 plan 작성 시 (어느 주제든) 공통 사항

- 본 plan 의 Constraint (메인 단일 흐름 / 영문 노트북 Closed 추가만 / measure.py 변경 0 등) 일관 적용
- 결과 JSON 은 Stage 2 의 새 schema_version 표준 따름

---

## 6. 명시 배제 (Stage 1~4 어디에도 포함 금지)

- **SQLite full ledger** — 10 테이블 schema 통합
- **기존 Exp00~10 결과 import** — JSON → DB 마이그레이션
- **FTS / CJK / 형태소 분석** — Exp11 주제가 Search 로 확정된 *후* 의 plan 에서만
- **Vector DB / Chroma / 의미 검색**
- **Graph connection / graph memory**
- **LLM diary / 제품화 / sync server / cross-device sync**
- **Tattoo lifecycle manager** — 현재 tattoo 는 단일 trial 내 임시. lifecycle 미정의.
- **Tool registry 일반화** — Mixed/Search 어느 쪽이든 직접 의존 아님
- **score_answer_v4 도입** — score_v3 보존
- **README 외부 노출 톤 변경** — public-readiness 정책 보존

---

## 7. 사용자 결정 호출 시점

**Mac 호출 불필요** (당분간 윈도우 주도) — 단 다음 분기에서만 사용자 (오빠) 호출:

| 분기 | 호출 사유 |
|------|----------|
| Stage 1 Task 02 의 Exp10 Δ 가 큼 (\|Δ\|≥0.03) | README Headline / H1 evidence 갱신은 외부 노출 약속 회수 — 사용자 시각 검토 |
| Stage 2 healthcheck/abort 정책 옵션 (a)/(b)/(c)/(d) 결정 | 사용자 선호 (보수적 abort vs 관대한 retry) |
| Stage 3 Exp11 주제 (Mixed vs Search) | 사용자 의사결정 필수 |
| 메인 단일 흐름 / 메모리 정책 / Closed 추가만 정책 위반 가능성 발생 | 즉시 사용자 호출 |

그 외 plan 작성 / 코드 변경 / commit / push 는 윈도우 Architect/Developer 권한 내.

---

## 8. 환경 / 운영 메모

- **Mac 마지막 commit**: `6206c3b feat(plan-phase-1-followup): ...` (push 완료, origin/main 동기)
- **Mac → Windows 동기**: `git pull --ff-only` 한 번이면 충분
- **Untracked 파일** (Mac 잔여, 정책상 보존):
  - `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260429_045819.json`
  - `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_20260429_052748.json`
  → 직전 plan 시도 잔여물. canonical 053939 만 추적. 이번에도 untracked 유지.
- **메모리 정책**:
  - 메인 단일 흐름 (브랜치 분기 금지, archive 예외)
  - Architect/Developer/Reviewer/사용자 분리
  - 본격 분석/실험 실행 = 사용자 직접 (rescore_v3 같은 정적 채점은 task 명시 따름)
- **Windows 환경 주의**: Exp09 5-trial 사고 (`yongseek.iptime.org:8005` connection refused) 재발 위험. Stage 1 의 rescore_v3 는 LLM 호출 0 — 영향 없음. 그러나 Stage 3 이후 Exp11 실행 시 healthcheck 필수.

---

## 9. 참조

- **현재 plan**: `docs/plans/phase-1-taskset-3-fail-exp09-5-trial-exp10-v3.md` (Task 01~04)
- **직전 핸드오프**: `docs/reference/handoff-to-windows-2026-04-30-rescore-v3.md` (Task 02/03 작업 지시)
- **Exp09 분석 보고서**: `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`
- **Mac 커밋 이력**:
  - `6206c3b` (Phase 1 후속 정리 — Mac 산출)
  - `3ed255a windows` (직전 Windows commit)
  - `8477981 feat(exp10): v2 finalize + v3 scorer/abc-json patch`

---

## 10. 다음 응답 형식 (윈도우 Architect 에게)

윈도우 Architect 가 본 핸드오프 수신 후 첫 응답에 포함 권고:

```text
1. 본 전략 합의 ack
2. Stage 1 (Task 02/03) 진행 의사 + 소요 예상
3. Stage 2 plan 초안 (작은 안정화) 의 plan-proposal — Stage 1 마무리 후
4. Stage 3 의제 정리 (Mixed vs Search 비교 표) — Stage 2 plan 시점 또는 그 후
```
