# Handoff to Next Agent — per-attempt 트랙 종결 + 로그 분석가 방향 전환 (Exp25 완료)

- **인계 시점**: 2026-07-03
- **전 세션 전부 push 완료** (origin/main `5408ce8`까지). tracked 미커밋 없음.
- **먼저 읽을 것**: `docs/reference/logAnalystDesign.md`(방향·아키텍처·로드맵) + `MEMORY.md`(recall) + 본 문서.

---

## 0. 한 줄 요약

per-attempt 신뢰성을 프롬프트(H22)·도구(H23)·구조분할(H24)로 못 올림을 3중 확인 → **가치 명제를 "로그 분석 어시스턴트"로 전환**. det_planner_probe/Exp25가 **fail-safe(결정론 finding→정답 아니면 침묵, wrong 0% @ n=30)** 확증. 다음 = **Exp25b(C-수렴 병목 완화)**.

## 1. 이번 세션 달성 (Stage 10~12 + 방향전환)

| Stage | 실험 | verdict | 핵심 |
|---|---|---|---|
| 10 | Exp22 retrieval-discipline nudge | H22 ⚠ 미결/기각 | 레버 +50pp가 소표본 착시, 재검증 미재현 |
| (10 후속) | §20 분산진단+retry K-sweep | (H16 재검증) | per-attempt ≈49% 노이즈, retry K=5→95% |
| 11 | Exp23 list_failed_units 도구 | H23 ⚠ 미결/기각 | retrieval 우회 성공·85~94% 사용해도 무개선 |
| 12 | Exp24 a2a Planner→Executor | H24 ⚠ 미결/기각 | emit 고쳤으나(empty 9→0) 실패 Planner 이동, correct 47→13% |
| (전환) | scoped_emit_probe | — | 답 clean 주입 시 emit 100% → a2a green-light(했으나 planner가 발목) |
| (전환) | **det_planner_probe** | — | **결정론 finding→correct==finalized, confident-wrong 0 = fail-safe** |
| (전환) | **Exp25 det_planner_retry** | — | **wrong 0%(n=30 누적) 확증, correct 67%@K=5, 병목=C-수렴** |

- 노트북 §20/§21/§22 + H22/H23/H24 기록(한/영 append-only). README ko/en Stage 10~12. index Recently Done.
- 회귀게이트 **71 OK**. opt-in 플래그 3개(`retrieval_discipline_prompt`/`list_failed_units`(FAILED_UNITS_TOOL)/`a2a_proposer`) 전부 기본 False byte-identical, 켜기 비추천.

## 2. 핵심 결론 (방향 전환의 논리)

- **외재화는 reach(데이터·계산 접근)를 확장하나 judgment(노이즈 속 판별)를 확장하지 않는다.** per-attempt 3중 음성이 그 경계.
- **confident-wrongness 근원 = LLM judgment in noise.** Exp24 a2a(LLM planner)는 틀린 finding→confident-wrong 14%. det_planner(결정론 추출기)는 정답 finding→**wrong 0%(fail-safe)**.
- **로그 분석가 아키텍처** = 결정론 추출기 배터리 + clean executor(e4b 언어화) + retry(throughput) + 기권(안전). "틀린 진단이 절대 안 나오는" 트리아지. 상세 `logAnalystDesign.md`.
- **병목 이동**: per-attempt 트랙 내내 A-stage(emit) 문제로 봤으나, Exp25가 **C(판정자) 수렴**으로 국소화 — 정답 assertion 줘도 C가 ~20-33%만 수렴.

## 3. 다음 세션 최우선 — Exp25b (C-수렴 병목)

**질문**: 정답 assertion 을 clean 하게 줬는데 왜 C(판정자)가 2/3 수렴 거부하나?
- 가설 A: C 가 도구 없이 "검증 못 해서" confidence<0.8 로 남음(termination 미충족).
- 가설 B: termination 조건("open_questions 해결 + confidence≥0.8")이 과엄격.
- 가설 C: C 가 단일 assertion 을 불충분하다고 판단(더 많은 증거 요구).
- **접근**: det_planner_probe/retry 의 실패 chain 의 C 결정(c_parsed: converged/reasoning/confidence) 로깅. C-stage 프롬프트/termination 이 처리량 레버. **per-attempt 는 A-stage 였고 이제 C-stage** — 새 진단.
- 주의: 이건 orchestrator 공유코드(C 경로) 손댈 수 있음 → **plan-first + 회귀게이트**. 단 진단(로깅)은 diagnostics 스크립트로 먼저.

이후 로드맵: Exp26(추출기 다종화+다실패모드) → Exp27(기권 층) → Exp28(GB 백엔드 ripgrep/인덱스) → 크로스모델 O(1)(논문 핵). `logAnalystDesign §4`.

## 4. 인프라 / 접속 (필수)

- **boxie**(외부 GPU, gemma4:e4b): SSH `ssh -p 2232 -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`. 터널 `ssh -p 2232 -N -L 11435:127.0.0.1:11434 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`. healthcheck `curl -s http://127.0.0.1:11435/api/tags`.
- **⚠ boxie GPU 를 지인 secall 임베딩이 간헐 점유** → 긴 run(도구+megalog, arm 순차) 반복 kill. 대응: (a) **짧은 호출 probe(도구 없는 체인)는 kill 회피** — det_planner_probe/Exp25 무사 완주. (b) 긴 A/B 는 단독 arm 러너(`run_v23_mandatory_only.py` 패턴) + 증분 저장. (c) 사용자에게 GPU 여유 확인.
- **Redis 메가로그** 키 `ctx:test9ng_journal_30d:stdout`(111MB/1.1M줄) — **재부팅 안 했으면 생존**, 있으면 재pull 불필요(`_load_megalog_to_redis`가 reuse). 없으면: `ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw` + `EXP20_LOG_PATH` env.
- 실험은 cloud/boxie면 **에이전트 직접 실행 가능**(이번 세션 전부 직접). 로컬 LLM 은 사용자만. 메모리 [[reference-remote-gemma-ssh-tunnel]].

## 5. 규약 / 워크플로

- **테스트**: repo root `python -m unittest discover -s experiments/tests -t .` (**71 OK**, pytest 미설치). `python`=`C:\Python\Python314\python.exe`.
- **공유코드**(`orchestrator.py`/`system_prompt.py`/`context_tools.py`) 변경 = **plan-first(gemento-plan-create) + 회귀게이트(off byte-identical)**. **verdict** = gemento-verdict-record(영문 노트북 Closed-append-only 강제, 표 row 무변경 검증).
- **Sonnet 위임 잘 작동**: `Agent(subagent_type=general-purpose, model=sonnet)`로 Task 코드 위임 → Architect diff 리뷰(특히 else-분기 byte-identical, 모듈레벨 헬퍼) → 커밋. 실험 실행은 Architect.
- **진단 스크립트 durable**: `experiments/exp15_context_router/diagnostics/` — phase0/micro/lever/variance/retry_capstone(+K5)/per_attempt/scoped_emit/**det_planner_probe/det_planner_retry** + v22~v24 결과. 전부 커밋됨.
- **드라이버**: `run_v2[2-4]_*.py`(+ `run_v23_mandatory_only.py`). native caller `native_ollama_caller.py`(num_ctx+내부 tool-loop, `extra_tool_schemas/fns`). stdout block-buffered → `python -u` 또는 결과 JSON polling.
- **scorer caveat**: keyword 채점이 finalization↔accuracy 혼동. Exp25 교훈: **correct==finalized 인지 확인**(confident-wrong 감지). non-null≠correct.

## 6. 미해결 / 보류

- Exp25b(C 병목) 미착수. 로그분석가 로드맵 Exp26~28 미착수.
- a2a 심화(구조화 planner+verification), 도메인 facet 다종화(H21 후속), 크로스모델, Stage 8~12 arc 논문화 — 전부 보류(로그분석가 우선).
- opt-in 플래그 3개 유지(롤백 X, 켜기 비추천).

## 7. 다음 세션 시작 순서 (권장)

1. `git log --oneline -5`로 `5408ce8` 확인. `logAnalystDesign.md` + `MEMORY.md` recall + 본 문서.
2. 터널 healthcheck(`curl`) + Redis 키 확인. GPU 여유 사용자 확인(secall).
3. **Exp25b 진단**: det_planner 실패 chain 의 C 결정 로깅 스크립트(diagnostics) → C 수렴 거부 원인 규명 → 레버 식별.
4. 레버가 C-stage 공유코드면 plan-first. 진단만이면 바로.
