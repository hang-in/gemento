# Handoff to Next Agent — Stage 9(Exp21 facet) 마감 + 오케스트레이터 신뢰성 트랙 착수

- **인계 시점**: 2026-07-01
- **⚠ 다음 세션 = 완전 재부팅(`/exit` 후 재시작, 새 파일 세션)** — 이 대화 컨텍스트 전무. 이 문서 + 메모리(`MEMORY.md`)로만 이어감.
- **⚠ scratchpad 소실**: 재부팅으로 이번 세션 scratchpad(세션 스코프)가 통째 사라짐 — 메가로그 파일(117MB), 레버 결과, 원본 진단 스크립트 포함. **durable 보존한 것은 §6 참조.**

---

## 0. 지금 진행 중 (재부팅 전 확인)

**레버 A/B가 백그라운드 실행 중이었음** (control vs nudge, task A, n=6씩). 이 세션에서 완료 후 결과를 아래 §4.3에 채우고 durable 보존 예정. **재부팅은 레버 완료 + 결과 보존 후.** (마지막 관측: control n=5 finalized 20%/empty 80%, nudge 미시작.)

✅ **LEVER 최종 결과** (task A, n=6/arm, 2026-07-01 완료):
```
             finalized   empty_tattoo   correct
  control      17%          83%          17%
  nudge        67%          33%          50%
  Δ           +50pp        -50pp        +33pp
```
**판정: narrow-query nudge 작동 확인 (채택 방향).** 포기(empty-tattoo)를 정확히 절반으로 감소 → finalized +50pp, correct +33pp. 겨냥한 메커니즘대로. 단 n=6 소표본 + nudge도 2/6 여전히 포기(sample 1,5) + sample6 assertion 5개 과잉생성으로 오답 → 완전 해결 아님, ~절반 개선.
→ **다음 세션 액션**: nudge 문구(§4.3)를 `system_prompt`(`MANDATORY_TOOL_RULES` 인근)에 **plan-first(gemento-plan-create) + 회귀 게이트(off byte-identical)**로 편입. 편입 후 재검증(n↑, task B도). 결과 durable: `diagnostics/lever_test_result.json`.

---

## 1. 이번 세션 달성 (요약)

### (A) Stage 9 — Exp21 Facet Aggregate Tool A/B **완료** (H21 ⚠ 조건부 채택)
핸드오프 이전 우선순위(① Exp20 megalog ② facet A/B)를 모두 소화:
- **Exp20 megalog 검증 → 진단**: test9ng 30일 저널(117MB/1.1M줄/~29.3M tok)을 boxie e4b router로 실행. task A(gohttpserver) 0.0의 원인이 스케일 아니라 **high-volume+16KB캡→finalization 실패**임을 단일 trial 정밀 진단으로 규명. (당시 결론은 §4에서 재정정됨.) 드라이버 `run_v20_megalog.py`.
- **Exp21 facet A/B** (Sonnet 위임 구현 task-01~03 + Architect task-04):
  - 단일 `aggregate_context(handle, pattern, group_by, top_n)` — 16KB 라인덤프 대신 untruncated 그룹별 top-N 카운트. **opt-in**(글로벌 `CONTEXT_TOOL_*` 불변, 별도 `FACET_TOOL_*` + caller `extra_tool_schemas/fns` default None=byte-identical). `orchestrator.py` 무변경.
  - 결과: **task B(집계)에서 facet이 score 0.0→0.8** (grep_only 5/5 confidently-wrong `174.138.8.10` — 16KB 캡이 시간순 앞부분만 노출; grep_facet 4/5 정답 `45.144.212.75`, facet 16 calls). **단일-needle task A엔 무효**(0.3→0.2). non-null rate는 task B에서 무력(양 arm 1.0) → 진짜 신호는 accuracy. **"more structure ≠ monotonically better" 실증**, failure-mode-specific.
  - **커밋**: `3c253b6`(plan+Exp20 드라이버) `5202991`(task-01) `9205b47`/`63d6c51`(task-02) `38f00c8`(테스트 repo-root 정정) `cdbcb6b`(task-03) `6905ca5`(결과) `b763f81`(task-04 verdict+분석). 전부 로컬 main, **push 안 함**.
  - verdict 기록: researchNotebook.md/.en.md(append-only) + index.md(Recently Done Stage 9) + `docs/reference/exp21-facet-ab-analysis-2026-06-30.md`(§18).

### (B) 오케스트레이터 신뢰성 트랙 착수 (§4에 상세)
사용자가 "다음 방향"으로 **오케스트레이터 신뢰성**(확률적 finalization) 선택 → 진단 진행.

### (C) tunaRound a2a 교차프로젝트 문서 전달 (별 트랙, §7)

---

## 2. 핵심 인프라 / 접속 (다음 세션 필수)

- **boxie** (외부 GPU 서버, gemma4:e4b 실행기): SSH `ssh -p 2232 -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`.
  - **터널** (boxie ollama → 로컬 11435): `ssh -p 2232 -N -L 11435:127.0.0.1:11434 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187` (백그라운드). **불안정 — 끊기면 재수립.** healthcheck: `curl -s http://127.0.0.1:11435/api/tags`.
- **test9ng** (≡ `test-server`): `~/.ssh/config` alias **`test9ng.ddns.net`** (9207). 원격 셸 fish — `source:`/`openclaw.fish` 라인 필터.
- **메가로그 재pull 필수** (재부팅으로 소실): `ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw` (117MB/1.1M줄/~29.3M tok, ~2분). 드라이버는 `EXP20_LOG_PATH` env로 경로 오버라이드 가능.
- **Redis**: 로컬 6379. 메가로그 키 `ctx:test9ng_journal_30d:stdout` (드라이버 `_load_megalog_to_redis`가 파일에서 재적재). Docker Desktop 또는 WSL redis-server. 재부팅 후 키 없음 → 드라이버가 재적재.
- 실험 실행: cloud/원격(boxie)은 에이전트 직접 가능. 메모리 [[reference-remote-gemma-ssh-tunnel]].

---

## 3. 테스트 실행 규약 (중요 — 이번 세션 교훈)

- **pytest 미설치**. repo 표준 = `unittest`.
- **반드시 repo root에서 실행**: `python -m unittest discover -s experiments/tests -t .` (56 OK 기대). `experiments/`를 cwd로 두면 `test_static`이 `experiments` 패키지 import 실패 = **경로 아티팩트, 회귀 아님**.
- `test_static`의 결과-인벤토리 exact-count(36/56)는 exp00~09만 검사 — exp15_context_router 신규 파일은 무영향.
- `python` = `C:\Python\Python314\python.exe`.

---

## 4. 오케스트레이터 신뢰성 트랙 — 진단 상세 (다음 세션 핵심)

**동기**: Exp21에서 task A finalization이 확률적(0.2~0.4)이라는 게 드러남 — judge가 정답을 tattoo에 갖고도 수렴 못 하는 것처럼 보였음. 이걸 정면 공략. **단 orchestrator.py = 심장부 → 반드시 "진단 → plan-first + 회귀 게이트(off byte-identical)".**

### 4.1 Phase 0 특성화 진단 (완료) — 메모리 [[phase0-finalization-rootcause]]
`run_abc_chain` 반환값(tattoo/logs/final_answer) 계측, 공유코드 무변경. megalog task A n=8 + task B n=3, single-attempt.
- **결과 (이진적)**: 수렴 chain = assertions 2~3, cycle 4~7, judge converged → finalize. 실패 chain = **assertions=0(empty tattoo)**, cycle 8 소진, judge 한 번도 converged 안 함.
- `judge_ever_converged`가 `n_assertions>0`과 **1:1 상관**. → **judge는 멀쩡**(신호 있으면 cycle4 수렴). 원래 "judge가 수렴 거부"는 **n=1 착시**.
- 근본 원인 = **상류 A(제안자)가 ~50% chain에서 assertion 0개 emit(empty tattoo)** → B 비판대상 없음 → judge 굶음 → None.

### 4.2 마이크로 진단 (완료) — ⚠ 계측 보정 포함
A raw_response/parsed_response 검사로 empty-tattoo 원인 세분화 시도. **중요 보정**:
- **내 grep 카운터는 무효였음**: `orchestrator.py:526` — `model_caller`(native caller) 경로에선 `tool_call_log=[]` 하드코딩. native caller는 도구를 *내부*에서 실행하므로 `a_tool_calls`는 항상 0. → "no-grep" 분류 폐기. (native 도구 관측하려면 pilot처럼 도구 wrap 또는 caller stats dict 사용.)
- **유효 증거(raw 추론)**: 실패 chain의 A가 `"initial search for 'error' returned large volume of unrelated errors... impossible to pinpoint"`라며 **넓게 grep→노이즈→좁히지 않고 포기**. parsed는 매번 성공(스키마 실패 아님).
- **최종 근본 원인**: **under-query + 조기 포기** — 넓은 패턴('error', gohttpserver 로그엔 없음)으로 검색→노이즈→구체 패턴(`Failed with result`/`.service`)으로 안 좁히고 assertion 없이 종료. **= Exp14(H13 insufficient retrieval iterations) + under-query 약점의 finalization 렌즈 재출현.** judge/tool-channel/schema 문제 아님.
- **재프레이밍**: "오케스트레이터 신뢰성" = **검색 견고성(retrieval robustness)** 문제. gemento가 이미 다뤄온 약점.

### 4.3 레버 A/B (이 세션에서 완료 예정) — narrow-query nudge
가장 싼 레버 falsify: constraints에 anti-give-up+narrow-query 지시 주입(프롬프트 only, 공유코드 무변경). control vs nudge, task A, n=6씩. 스크립트 `diagnostics/lever_test.py`.
- **NUDGE 문구**: "넓은 검색은 노이즈. 포기 말고 `Failed with result`/`Main process exited`/`.service`로 좁혀라. finalize 전 후보 unit을 new_assertion으로 최소 1개 기록. 빈손 cycle 종료 금지."
- 측정: finalized_rate(1차), empty_tattoo_rate(메커니즘), correct_rate.
- **결과는 위 §0 ⏳블록에 기입.** 판정: nudge가 empty↓/finalized↑ 유의미 → **싼 레버 확보** → system_prompt(`MANDATORY_TOOL_RULES` 인근)에 plan-first+회귀게이트로 편입. 미미 → 레버 조정/facet-강제/다른 레버.

### 4.4 후보 레버들 (같은 뿌리=retrieval robustness)
1. **narrow-query nudge** (레버 A/B 중) — 프롬프트만.
2. **강제 iteration** — no-assertion 시 "좁혀라" 재프롬프트.
3. **facet 강제** (Exp21 aggregate_context 이미 있음) — `list_failed_units`류가 노이즈 grep을 깨끗한 히스토그램으로. 단 Exp21서 task A엔 모델이 facet 거의 안 씀 → "사용 강제"가 관건.
- **a2a(planner→executor 분리)는 가장 비싼 옵션** — 싼 레버 부족할 때의 다음 카드. 지금 X.

---

## 5. 워크플로 / 규약 메모

- **plan-first**: 공유코드(`orchestrator.py`/`context_tools.py`/`system_prompt.py`) 변경은 `gemento-plan-create` 스킬 + 회귀 게이트. **verdict**: `gemento-verdict-record`(영문 노트북 append-only 강제).
- **Sonnet 위임 잘 작동**: 이번 세션 task-01~03을 `Agent(subagent_type=general-purpose, model=sonnet)`로 위임, 각 단계 코드리뷰로 승인. 위임 시 (a) 금지파일 명시 (b) pytest 미설치→unittest (c) git stash 금지 (d) 실행은 Architect가(긴 실험).
- **명명 규약**: 신규 변종 = letter suffix(Exp21b). Stage 9까지 진행됨.
- **드라이버 위치**: `experiments/exp15_context_router/run_v1x~v21.py`. native caller `native_ollama_caller.py`(num_ctx + 내부 tool-loop). 결과 JSON은 `results/`. stdout은 block-buffered → `python -u` 또는 결과 JSON polling.
- **scorer caveat**: keyword 채점이 finalization과 accuracy를 혼동시킴(Exp21 교훈: non-null rate ≠ correct). LLM-judge 보조는 보류.

---

## 6. Durable 보존물 (재부팅 생존 — scratchpad 아님)

`experiments/exp15_context_router/diagnostics/` (git untracked, 디스크에 존재):
- `phase0_diag.py` + `phase0_diag_result.json` — Phase 0 특성화(§4.1).
- `micro_diag.py` + `micro_diag_result.json` — A-stage 세분(§4.2, grep 카운터 무효 주의).
- `lever_test.py` — 레버 A/B 하네스(§4.3). **결과 JSON은 scratchpad라 소실 → §0에 수치 보존.**
- ⚠ 스크립트들이 scratchpad OUT 경로 + 메가로그 `_DEFAULT_LOG`(구 session UUID) 하드코딩 → 다음 세션 재사용 시 OUT 경로 수정 + `EXP20_LOG_PATH` env로 메가로그 지정.
- 커밋 여부는 사용자 판단(현재 untracked). 진단 툴이라 미폴리시.

---

## 7. tunaRound a2a 교차프로젝트 (별 트랙, gemento와 무관)

사용자 요청으로 gemento 세션 논의를 tunaRound(`D:/privateProject/tunaRound`, a2a 지향 멀티에이전트 토론 앱)에 전달. **신규 2파일, tunaRound 정본 무수정, 미커밋**:
- `docs/design/a2a-comm-layer-crossproject-note_2026-07-01.md` — 참고 노트(정본 아님 표시).
- `docs/prompts/a2a-comm-layer-architect-review_2026-07-01.md` — tunaRound 아키텍트용 검토 프롬프트.
- 핵심: ① "a2a=통신레이어" 직관은 tunaRound 정본 §6에 이미 분해됨(SSH터널=boxie 무인증-localhost artifact / outbound 무터널 / inbound=tailscale). ② gemento verifiable-diagnosis = tunaRound (B) full-a2a 경제조건 #2 실물 후보(방향 수렴). ③ 잔여 리스크=codex MCP read_transcript 실호출(Stage 1).
- **다음 세션 액션 아님** — 사용자가 tunaRound 세션에서 아키텍트에게 프롬프트 전달 예정.

---

## 8. 다음 세션 시작 순서 (권장)

1. `git pull --ff-only`(불필요, 로컬 main) + `git log --oneline -5`로 `b763f81` 확인. 이 문서 + `MEMORY.md` recall.
2. **§0 레버 결과** 확인 → nudge 효과 판정.
3. 효과 있으면: narrow-query nudge를 `system_prompt`에 **plan-first(gemento-plan-create) + 회귀 게이트**로 편입. 효과 없으면: §4.4 다른 레버.
4. (인프라) boxie 터널 재수립 + 메가로그 재pull(§2).
5. **미해결/보류**: push(로컬만), README/conceptFramework에 Stage9/H21 반영(사용자 결정), LLM-judge 채점, e2b push-외재화.

---

## 9. 재부팅 타이밍 (사용자 질문 답)

**레버 완료 → 내가 결과를 §0에 기입 + durable 보존 + "재부팅 안전" 신호 → 그때 재부팅.** 레버 실행 중 재부팅하면 (a) 백그라운드 프로세스 kill (b) scratchpad 레버결과 소실. **레버 완료 신호 대기 후 재부팅.**
