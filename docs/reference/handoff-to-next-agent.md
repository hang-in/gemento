# Handoff to Next Agent — 로그분석가 처리량 레버 확증 (Exp25b/25c 완료)

- **인계 시점**: 2026-07-03 (v2, Exp25b/25c 추가)
- **push**: origin/main `bb3abaa`까지 (아래 §커밋 참조). tracked 미커밋 없음.
- **먼저 읽을 것**: `docs/reference/logAnalystDesign.md`(방향·아키텍처·로드맵, §4 최신) + `MEMORY.md`(recall v7) + 본 문서.

---

## 0. 한 줄 요약

per-attempt 3중 음성(H22/H23/H24) 후 **"로그 분석 어시스턴트"로 전환**. Exp25=fail-safe 확증(wrong 0). **Exp25b=처리량 병목 원인 규명(premature CONVERGED: C 가 답 없이 조기 CONVERGED 월반→답 phase 스킵, 핸드오프 3가설 반증)**. **Exp25c=게이트 검증(orchestrator opt-in `converged_requires_answer`, A/B finalized 13→87%, reached_productive 20→100%, wrong 0% 양 arm)**. 다음 = **productive-no-emit 천장(A-stage)** 또는 Exp26.

## 1. 이번 세션 달성

| 실험 | verdict | 핵심 |
|---|---|---|
| Exp25 det_planner_retry | 척추 확증 | wrong 0%(n=30 누적), correct 67%@K=5, 병목=C-수렴 |
| **Exp25b C-수렴 진단** (`6a795e8`) | **원인 규명** | 순수계측 n=15. **핸드오프 3가설 전부 반증**(confidence 게이트 코드에 없음·termination under-gated). 진짜 원인=**premature CONVERGED**(C 가 답 없이 DECOMPOSE/INVESTIGATE→CONVERGED 조기월반, orchestrator.py:1021 이 어느 phase서든 CONVERGED 직행 허용→답 쓰는 SYNTHESIZE 스킵→null). 비-finalized 89%. finalize된 소수는 C 조기수렴 *안 한* chain(safety-crawl→SYNTHESIZE→emit). |
| **Exp25c CONVERGED 게이팅** (`bb3abaa`) | **레버 확증** | orchestrator opt-in `converged_requires_answer`(off byte-identical): 답 없는 CONVERGED 월반을 SYNTHESIZE 로 redirect. **A/B n=15/arm: finalized 13→87%, reached_productive 20→100%, wrong 0%(양 arm)**, Wilson95=(0.62,0.96). fail-safe 완전 보존. 회귀게이트 **75 OK**. |

- 노트북 §20/§21/§22 + H22/H23/H24 기록(한/영 append-only). README ko/en Stage 10~12. index Recently Done.
- 회귀게이트 **71 OK**. opt-in 플래그 3개(`retrieval_discipline_prompt`/`list_failed_units`(FAILED_UNITS_TOOL)/`a2a_proposer`) 전부 기본 False byte-identical, 켜기 비추천.

## 2. 핵심 결론 (방향 전환의 논리)

- **외재화는 reach(데이터·계산 접근)를 확장하나 judgment(노이즈 속 판별)를 확장하지 않는다.** per-attempt 3중 음성이 그 경계.
- **confident-wrongness 근원 = LLM judgment in noise.** Exp24 a2a(LLM planner)는 틀린 finding→confident-wrong 14%. det_planner(결정론 추출기)는 정답 finding→**wrong 0%(fail-safe)**.
- **로그 분석가 아키텍처** = 결정론 추출기 배터리 + clean executor(e4b 언어화) + retry(throughput) + 기권(안전). "틀린 진단이 절대 안 나오는" 트리아지. 상세 `logAnalystDesign.md`.
- **병목 이동 (확정)**: A-stage(emit) → Exp25 C-수렴 → **Exp25b premature CONVERGED 로 국소화 → Exp25c 게이트로 매입(13→87%)**. C 조기수렴이 답 쓰는 phase 를 스킵한 것이 원흉이었고, 게이트가 그것을 막아 reached_productive 20→100%. 이제 남은 병목은 **productive-no-emit**(게이트 ON 에서 SYNTHESIZE 도달 후 A 가 emit 실패, 잔여 13%) = C 아닌 A-stage.

## 3. 다음 세션 최우선 — productive-no-emit 천장 (A-stage) 또는 Exp26

**질문**: 게이트 ON 으로 모든 chain 이 SYNTHESIZE 도달(100%)인데 왜 13%는 거기서 final_answer 를 emit 안 하나?
- **접근 A (레버)**: `converged_requires_answer=True` 켠 상태의 실패 chain(final=False, prod=True)의 SYNTHESIZE cycle A 응답(final_answer 필드 유무·reasoning) 로깅 → emit 실패 원인(파싱? 지시 미준수? confidence 부족?). SYNTHESIZE emit-nudge 또는 A-stage retry 가 레버 후보. exp25b_c_convergence_probe.py 계열에 게이트 켜고 진단.
- **접근 B (로드맵 진행)**: Exp26 추출기 다종화 + 다실패모드(crashloop 아닌 task) — fail-safe·커버리지 일반화. 게이트가 이미 확증됐으니 다음 축으로 진행 가능.
- 주의: 접근 A 의 레버가 orchestrator/system_prompt 면 **plan-first + 회귀게이트**. 진단(로깅)은 diagnostics 스크립트로 먼저. 로그분석가 경로에선 `converged_requires_answer=True` 를 기본 ON 으로 쓰는 게 맞음(Exp25c 입증).

이후 로드맵: Exp26(추출기 다종화+다실패모드) → Exp27(기권 층) → Exp28(GB 백엔드 ripgrep/인덱스) → 크로스모델 O(1)(논문 핵). `logAnalystDesign §4`.

## 4. 인프라 / 접속 (필수)

- **boxie**(외부 GPU, gemma4:e4b): SSH `ssh -p 2232 -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`. 터널 `ssh -p 2232 -N -L 11435:127.0.0.1:11434 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`. healthcheck `curl -s http://127.0.0.1:11435/api/tags`.
- **⚠ boxie GPU 를 지인 secall 임베딩이 간헐 점유** → 긴 run(도구+megalog, arm 순차) 반복 kill. 대응: (a) **짧은 호출 probe(도구 없는 체인)는 kill 회피** — det_planner_probe/Exp25 무사 완주. (b) 긴 A/B 는 단독 arm 러너(`run_v23_mandatory_only.py` 패턴) + 증분 저장. (c) 사용자에게 GPU 여유 확인.
- **Redis 메가로그** 키 `ctx:test9ng_journal_30d:stdout`(111MB/1.1M줄) — **재부팅 안 했으면 생존**, 있으면 재pull 불필요(`_load_megalog_to_redis`가 reuse). 없으면: `ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw` + `EXP20_LOG_PATH` env.
- 실험은 cloud/boxie면 **에이전트 직접 실행 가능**(이번 세션 전부 직접). 로컬 LLM 은 사용자만. 메모리 [[reference-remote-gemma-ssh-tunnel]].

## 5. 규약 / 워크플로

- **테스트**: repo root `python -m unittest discover -s experiments/tests -t .` (**75 OK**, pytest 미설치). `python`=`C:\Python\Python314\python.exe`. (현 환경서 redis-tool 테스트가 117MB 스캔으로 느려 전체 ~21분 소요 — 정상.)
- **공유코드**(`orchestrator.py`/`system_prompt.py`/`context_tools.py`) 변경 = **plan-first(gemento-plan-create) + 회귀게이트(off byte-identical)**. **verdict** = gemento-verdict-record(영문 노트북 Closed-append-only 강제, 표 row 무변경 검증).
- **Sonnet 위임 잘 작동**: `Agent(subagent_type=general-purpose, model=sonnet)`로 Task 코드 위임 → Architect diff 리뷰(특히 else-분기 byte-identical, 모듈레벨 헬퍼) → 커밋. 실험 실행은 Architect.
- **진단 스크립트 durable**: `experiments/exp15_context_router/diagnostics/` — phase0/micro/lever/variance/retry_capstone(+K5)/per_attempt/scoped_emit/**det_planner_probe/det_planner_retry** + v22~v24 결과. 전부 커밋됨.
- **드라이버**: `run_v2[2-4]_*.py`(+ `run_v23_mandatory_only.py`). native caller `native_ollama_caller.py`(num_ctx+내부 tool-loop, `extra_tool_schemas/fns`). stdout block-buffered → `python -u` 또는 결과 JSON polling.
- **scorer caveat**: keyword 채점이 finalization↔accuracy 혼동. Exp25 교훈: **correct==finalized 인지 확인**(confident-wrong 감지). non-null≠correct.

## 6. 미해결 / 보류

- **productive-no-emit 천장 미착수**(게이트 ON 잔여 13%, A-stage). 로그분석가 로드맵 Exp26~28 미착수.
- a2a 심화(구조화 planner+verification), 도메인 facet 다종화(H21 후속), 크로스모델, Stage 8~12 arc 논문화 — 전부 보류(로그분석가 우선).
- **opt-in 플래그 4개**: retrieval_discipline/list_failed_units/a2a_proposer(앞 3개 off 유지·비추천), **converged_requires_answer(Exp25c 로 효과 입증 — 로그분석가 경로에선 ON 권장)**. 롤백 X.

## 7. 다음 세션 시작 순서 (권장)

1. `git log --oneline -5`로 `bb3abaa` 확인. `logAnalystDesign.md`(§4) + `MEMORY.md` recall v7 + 본 문서.
2. 터널 healthcheck(`curl`) + Redis 키 확인. GPU 여유 사용자 확인(secall). **주의: 현 환경서 `import tools`/전체 회귀게이트가 수 분~20분 느림(경합) — 데드락 아님, nohup+Monitor 로 인내.**
3. **접근 A(레버)**: exp25c 실패 chain(final=False,prod=True)의 SYNTHESIZE A 응답 로깅 → productive-no-emit 원인 규명. 또는 **접근 B**: Exp26 추출기 다종화로 로드맵 진행.
4. 레버가 공유코드면 plan-first + 회귀게이트(75, off byte-identical). 진단만이면 바로.
