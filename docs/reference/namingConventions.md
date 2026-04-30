---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# 제멘토 표기 / 용어 규약 (Naming Conventions)

> 모든 plan / handoff / reference / commit message 에 적용되는 canonical 규약.
> 기존 문서의 retroactive 변경은 의무 아님 (§9 적용 범위 참조). 신규 문서부터 본 규약 따름.

본 reference 의 목적: 표기 (`(a)` vs `(i)` vs `1`) 와 용어 (`task` vs `Task` vs `trial`) 의 충돌을 해소하여 plan / commit / 보고서 의 의미를 명료하게 한다.

---

## 1. Plan / Stage / Subtask / Group 표기

### 1.1 Stage (큰 시퀀스 단위)

핸드오프의 큰 시퀀스 (Mac handoff `d61e8ef` 의 Stage 1~5) 를 가리킬 때:

- **Stage N** — 단일 stage (Stage 1, Stage 2, ..., Stage 5)
- **Stage NX** — 같은 stage 내 병렬 plan 분기 (X = 대문자 A, B, C, ...)
  - 예: `Stage 2A` (안정화), `Stage 2B` (scorer/label), `Stage 2C` (H4 재검증)
  - 같은 X 는 같은 plan 단위 — plan slug 와 의미상 1-1 대응

### 1.2 Plan slug + 파일명

- **slug**: `kebab-case` (영문 소문자 + hyphen)
  - 예: `stabilization-healthcheck-abort-meta-pre-exp11`
- **parent 파일**: `<slug>.md`
- **subtask 파일**: `<slug>-task-NN.md` (NN = zero-padded 두자리)

### 1.3 Subtask 표기 (plan 내부)

- 본문 표기: **Task NN** (대문자 T, zero-padded 두자리)
  - 예: "Task 01 — helper 신규", "Task 02 마감 후 Task 03 진행"
- 파일명 prefix: `task-NN` (소문자)
- frontmatter 의 `depends_on`: `[01, 02]` (zero-padded string)

> **⚠ 주의**: plan 내부의 "Task NN" (대문자) 는 experiment 의 "task ID" (소문자, kebab-case) 와 의미가 다름. §6 참조.

### 1.4 Group (parallel_group)

한 plan 안에서 병렬 가능한 subtask 묶음:

- **Group X** — prefix `Group` 의무 (X = 대문자 A, B, C, ...)
  - 예: `Group A: task-01 → task-02`
- **prefix 의무 이유**: Stage NX 의 X 와 표기 충돌 방지
  - 잘못된 표기: `A 그룹`, `(A)`, `Group A 의 Stage 2A` — 모두 모호
  - 정합 표기: `Group A`, `Stage 2C 의 Group A`

### 1.5 Step (subtask 내 단계)

- **Step N** — sequential 진행 단계 (N = 1, 2, 3, ...)
- sub-step: **Step Na** (Step 2a, Step 2b, ...) — 알파벳 소문자 suffix
  - 예: `Step 1 — helper 신규`, `Step 2a — import 추가`, `Step 2b — trial loop 보강`

---

## 2. 옵션 / 후보 / 강도 표기

**의미별 분리**:

| 의미 | 표기 | 예 |
|------|------|---|
| **순서 있는 진행 / 단계** | `1.`, `2.`, `3.` 또는 `Step N` | "1. validate 실행 → 2. abort 정책 적용" |
| **병렬 후보 / 선택지** (order 무관) | `(a)`, `(b)`, `(c)`, `(d)` | "(a) experiments/run_helpers.py / (b) _health.py / (c) utils/" |
| **강도 / 정도 / level** (order 의미 있음) | `(i)`, `(ii)`, `(iii)`, `(iv)` | "Solo 정의 — (i) loop=1 단발 / (ii) loop=N 반복 / (iii) 둘 다 측정" |

**충돌 회피 룰**:
- 같은 절 안에서 (a)/(b)/(c) 와 (i)/(ii)/(iii) 둘 다 사용 시 의미 차이 명시 — 후보 (a) 안에 강도 (i)/(ii) 가 있는 nested 구조
- 단순 list 는 `-` (bullet) 권장. 옵션 표기는 사용자 선택이 필요한 곳에 한정

---

## 3. Decision (사용자 결정) 표기

### 3.1 Plan 본문의 결정

- **결정 N** — plan 단위 일관 numbering (1부터). 한 plan 안의 결정은 1, 2, 3, ... 누적
  - 예: `결정 1 — healthcheck 정책 (b)+(d) 확정`
- 확정 표시: `결정 N — <answer> 확정` (값 명시)
- 검토 대기: `결정 N — <후보> 권장. 사용자 검토 대기`

### 3.2 임시 prefix 금지

- conversation 의 turn-level 임시 prefix (예: `C1`, `Q1`, `D1`) 는 **plan 본문에 등장 금지**
- turn 내 사용자 답변 받은 후, plan 작성 시 `결정 N` 형식으로 통합
- handoff / commit message 에서도 `결정 N` 형식 우선

### 3.3 결정의 sub-option

`결정 N` 의 후보 옵션은 §2 의 (a)/(b)/(c) 또는 (i)/(ii)/(iii) 룰 따름.

---

## 4. Hypothesis (가설) 표기

- **HN** — 단일 가설 (H1, H2, ...)
- **HNa / HNb / HNc** — 같은 H 의 sub-claim (H9a, H9b, H9c)
- 새 가설 도입: H10, H11, ... (순차)

frontmatter / commit message: `H4 verdict ⚠ 미결` 형식.

---

## 5. Experiment 표기

- **ExpNN** — zero-padded 두자리 (Exp00, Exp01, ..., Exp10)
- **ExpNNx** — 변종 / 부분 실험 (Exp08b, Exp045)
  - x = 영문 소문자 (a, b, ...) 또는 0.5 위치는 `045` (Exp045 = Exp04.5 의 줄임)
- 새 실험: Exp11, Exp12, ... (순차)

---

## 6. Task ID (experiment-level) — Plan Subtask 와 구분

### 6.1 Experiment task ID

- 형식: `<category>-<NN>` (소문자 + hyphen + zero-padded NN)
- 예: `math-01`, `logic-04`, `synthesis-04`, `longctx-medium-2hop-02`, `planning-01`
- ID 의 카테고리 alias: `synthesis-XX` 의 정식 카테고리는 `information_synthesis` — ID 단축은 historical (변경 0)

### 6.2 Plan Subtask 와의 구분

| 의미 | 표기 |
|------|------|
| **Plan 의 subtask** (행 단위 작업) | **Task NN** (대문자 T, zero-padded) |
| **Experiment 의 task** (질문 / 문제) | **task ID** (소문자, `<category>-<NN>`) |

- plan 본문: "Task 01 에서 task `math-01` 의 정답을 검증한다" — 두 용어 동시 사용 가능
- 약어 사용 금지: 두 의미 모두 "task" 로 줄여 쓰지 말 것
- 한국어 표기: "본 plan 의 Task 01 은 새 experiment task (math, logic, planning) 를 정의한다" — 명료

---

## 7. Category (experiment task category)

- 영문 snake_case (현재 패턴 보존):
  - `math`
  - `logic`
  - `information_synthesis` (task ID 는 `synthesis-XX`)
  - `longctx` (task ID 는 `longctx-<size>-<hop>-<NN>`)
  - `planning` (Stage 2C 신규 — task ID `planning-01` 등)
- 새 카테고리 추가 시: 본 reference 의 §7 에 등재

---

## 8. trial / run / cycle / loop 용어

| 용어 | 정의 |
|------|------|
| **trial** | 한 task × 한 condition 의 **1 회** 실행. result.json 의 trials[] 의 한 entry |
| **run** | 전체 실험 1 회의 batch (예: 540 trial run). result.json 1 파일 단위 |
| **cycle** | ABC chain 의 한 round (A→B→C 1 회). `max_cycles` = 한 trial 의 최대 cycle 수 |
| **loop** | 일반 용어 — trial loop / cycle loop / orchestrator loop 등 문맥 의존. technical 명세에는 cycle 우선 |

**ABC 의 cycle 정의** (canonical):
- 1 cycle = A 1회 + B 1회 + C 1회 = 3 model call
- `max_cycles=8` → 최대 24 model call / trial (단 C 의 수렴 결정 시 조기 종료)

**Solo 의 cycle 정의** (Stage 2C 본 turn 신규):
- Solo-1call: cycle 0 (단일 호출)
- Solo-budget: max_cycles=N, A 만 자기 반복 (B/C 호출 없음). 1 cycle = A 1회 = 1 model call

---

## 9. Metric / Result 명명

### 9.1 정확도 (accuracy)

- `accuracy_v2` / `accuracy_v3` — trial 단위 (0.0~1.0)
- `mean_acc` — aggregate (condition 또는 task 단위 평균)
- `acc_v3_mean` — analyze helper 의 dict key (snake_case)

### 9.2 assertion turnover (Stage 2C 신규)

- `turnover_added` / `turnover_modified` / `turnover_deleted`
- `turnover_final_count`
- `_mean` / `_sum` suffix — aggregate 형식

### 9.3 Error mode (Stage 2C 신규)

- `ErrorMode` enum (Python class)
- enum value: `SCREAMING_SNAKE_CASE` (NONE, FORMAT_ERROR, WRONG_SYNTHESIS, EVIDENCE_MISS, NULL_ANSWER, CONNECTION_ERROR, PARSE_ERROR, TIMEOUT, OTHER)
- analyze dict key: `error_modes` (소문자 snake_case, value 는 enum.value 문자열)

### 9.4 Stage 2A meta v1.0 필드

- top-level 필드 (Stage 2A task-03 정의):
  - `schema_version: "1.0"`
  - `experiment` (str)
  - `started_at` / `ended_at` (ISO 8601)
  - `model.{name, engine, endpoint}` (nested dict)
  - `sampling_params.{temperature, top_p, max_tokens, seed}` (nested dict)
  - `scorer_version: "v3"` 등
  - `taskset_version` (git short hash)
- **모두 snake_case**

---

## 10. Role Agent 표기 (4축 외부화)

conceptFramework.md §2.3 / §10 그대로 보존:

- **A = Proposer** (답변 제안)
- **B = Critic Agent** (비결정론 비판)
- **C = Judge Role** (메타 판단, phase 전이)
- **Critic Tool** (결정론 검증 — Critic Agent 와 구분)
- **Python Orchestrator** (결정론 안전망 — Judge Role 과 구분)

표기 형식:
- 짧은 표기: `A`, `B`, `C` (단일 letter)
- 명시 표기: `Proposer (A)`, `Critic Agent (B)`, `Judge Role (C)`

---

## 11. condition 표기 (실험 비교군)

condition slug — 영문 소문자 snake_case:

- 단발 호출 패턴: `solo_1call`, `gemma_1loop`
- 자기 반복 패턴: `solo_budget` (Stage 2C 신규)
- ABC 패턴: `abc`, `gemma_8loop`, `abc_tattoo`
- 외부 모델: `gemini_flash_1call`, `claude_haiku_judge` (Stage 3 Mixed Intelligence 후보)
- RAG: `rag_baseline`
- Solo dump: `solo_dump`

result.json 의 `condition` 필드 = 위 slug 그대로.

---

## 12. Commit message 표기

### 12.1 Title prefix

- `docs(<scope>): ...` — 문서 변경
- `feat(<scope>): ...` — 신규 기능
- `fix(<scope>): ...` — 버그 fix
- `refactor(<scope>): ...` — 리팩토링

scope:
- `plan` — plan 문서
- `exp<NN>` — 특정 experiment (`exp10`, `exp06` 등)
- `phase-<N>-followup` — Phase 후속 정리
- `stage-<NX>-task-<NN>` — Stage 2A 의 subtask commit

### 12.2 Title 길이

70 자 이내 (영어/한국어 혼합 — 한국어 글자 1자 = 영문 1자로 간주)

### 12.3 Body

- "왜" 우선 ("무엇" 보다)
- 사용자 결정 / 외부 입력 / disclosure 명시
- Co-Authored-By 마지막 줄

---

## 13. 적용 범위

### 13.1 Hard rules (위반 금지)

- §1 의 prefix 의무 (Stage NX, task-NN, Group X)
- §2 의 옵션 의미별 분리 (a/i/1)
- §3 의 결정 N 단일 prefix (C1/Q1/D1 임시 prefix 금지)
- §6 의 Task NN vs task ID 구분

### 13.2 Soft rules (점진 정정)

- §11 의 condition slug — 기존 historical slug 보존 (`gemma_8loop` 등). 신규는 본 reference 따름
- §7 의 카테고리 — 새 카테고리 등재 시 본 reference 갱신
- 기존 reference (conceptFramework, researchNotebook) 의 영역 — 변경 0 (canonical)

### 13.3 점진 적용 (retroactive 변경 0)

- 본 reference 도입 (2026-04-30) 이전 plan / handoff / commit 의 표기 차이는 변경 의무 없음
- 신규 plan (Stage 2A 갱신, Stage 2C, Stage 2B 등) 부터 본 reference 따름
- 기존 plan 의 frontmatter / 본문에 본 reference 와 충돌하는 표기 발견 시 — 해당 plan 의 다음 갱신 commit 에 disclosure 추가하면서 정정

### 13.4 검증

신규 plan / 문서 작성 시 다음 checklist:

- [ ] Stage NX prefix
- [ ] task-NN (subtask) vs task ID (experiment) 구분
- [ ] Group X prefix
- [ ] (a)/(i)/1 의미 분리
- [ ] 결정 N 단일 prefix
- [ ] H / Exp / Task ID zero-padded
- [ ] condition slug snake_case
- [ ] commit message scope prefix

---

## 14. 변경 이력

- 2026-04-30 v1: 초안. Stage 2C plan 작성 + 본 turn 의 (a)/(i) 혼재 + Stage 2A vs Group A 충돌 식별을 계기로 정리. 기존 plan / 문서의 retroactive 변경 의무 없음 — 점진 적용.
