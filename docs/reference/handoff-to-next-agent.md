# Handoff to Next Agent — 로그분석가 처리량 레버 확증 (Exp25b/25c 완료)

- **인계 시점**: 2026-07-03 (v2, Exp25b/25c 추가)
- **push**: origin/main `bb3abaa`까지 (아래 §커밋 참조). tracked 미커밋 없음.
- **먼저 읽을 것**: `docs/reference/logAnalystDesign.md`(방향·아키텍처·로드맵, §4 최신) + `MEMORY.md`(recall v7) + 본 문서.

---

## 0. 한 줄 요약

per-attempt 3중 음성(H22/H23/H24) 후 **"로그 분석 어시스턴트"로 전환**. Exp25=fail-safe 확증(wrong 0). **Exp25b=처리량 병목 원인 규명(premature CONVERGED, 핸드오프 3가설 반증)**. **Exp25c=게이트 검증(opt-in `converged_requires_answer`, A/B 13→87%, wrong 0)**. **Exp25d=productive-no-emit 진단(empty_final 노이즈=retry 커버, wrong 0 → A-stage 레버 불필요)**. **Exp26 v1=일반화(2추출기×2실패모드, 양 cell finalized/correct 100%/wrong 0)**. 다음 = **Exp26 v2(추출기 폭 확장, plan-first)** 또는 Exp27(기권 층).

## 1. 이번 세션 달성

| 실험 | verdict | 핵심 |
|---|---|---|
| Exp25 det_planner_retry | 척추 확증 | wrong 0%(n=30 누적), correct 67%@K=5, 병목=C-수렴 |
| **Exp25b C-수렴 진단** (`6a795e8`) | **원인 규명** | 순수계측 n=15. **핸드오프 3가설 전부 반증**(confidence 게이트 코드에 없음·termination under-gated). 진짜 원인=**premature CONVERGED**(C 가 답 없이 DECOMPOSE/INVESTIGATE→CONVERGED 조기월반, orchestrator.py:1021 이 어느 phase서든 CONVERGED 직행 허용→답 쓰는 SYNTHESIZE 스킵→null). 비-finalized 89%. finalize된 소수는 C 조기수렴 *안 한* chain(safety-crawl→SYNTHESIZE→emit). |
| **Exp25c CONVERGED 게이팅** (`bb3abaa`) | **레버 확증** | orchestrator opt-in `converged_requires_answer`(off byte-identical): 답 없는 CONVERGED 월반을 SYNTHESIZE 로 redirect. **A/B n=15/arm: finalized 13→87%, reached_productive 20→100%, wrong 0%(양 arm)**, Wilson95=(0.62,0.96). fail-safe 완전 보존. 회귀게이트 **75 OK**. |
| **Exp25d productive-no-emit 진단** (`767719c`) | **천장 특성화** | 게이트 ON n=25 계측. no-emit 실패(5/25)의 productive A 유형 = **empty_final 100%**(final_answer 필드는 넣되 값이 빔), wrong_content 0. = 순수 emit 노이즈(일부 GPU 경합 truncation) → **retry 커버**(87%+K=3→~99.8%). "단발 A-stage 레버" 불필요 확인. |
| **Exp26 v1 추출기·모드 일반화** (이 세션) | **커버리지 첫 교차 증거** | 기존 추출기 2개 × 태스크 2개, 게이트 ON, n=12/cell: list_failed_units×crashloop + **aggregate_context×brute-force(신규)** 모두 **finalized/correct 100%, wrong 0%**. fail-safe·처리량이 2추출기×2실패모드 일반화. |

- 노트북 §20~23 + H22~H25 기록(한/영 append-only). README ko/en Stage 10~13(단 README 는 collaborator d9ng 가 rewrite — H25 보존됨). index Recently Done Stage 13.
- 회귀게이트 **75 OK**. opt-in 플래그 **4개**(`retrieval_discipline_prompt`/`list_failed_units`/`a2a_proposer` 앞 3개 off 비추천, **`converged_requires_answer` 는 Exp25c 효과 입증 — 로그분석가 경로 ON 권장**).

## 2. 핵심 결론 (방향 전환의 논리)

- **외재화는 reach(데이터·계산 접근)를 확장하나 judgment(노이즈 속 판별)를 확장하지 않는다.** per-attempt 3중 음성이 그 경계.
- **confident-wrongness 근원 = LLM judgment in noise.** Exp24 a2a(LLM planner)는 틀린 finding→confident-wrong 14%. det_planner(결정론 추출기)는 정답 finding→**wrong 0%(fail-safe)**.
- **로그 분석가 아키텍처** = 결정론 추출기 배터리 + clean executor(e4b 언어화) + retry(throughput) + 기권(안전). "틀린 진단이 절대 안 나오는" 트리아지. 상세 `logAnalystDesign.md`.
- **병목 이동 (확정)**: A-stage(emit) → Exp25 C-수렴 → **Exp25b premature CONVERGED 로 국소화 → Exp25c 게이트로 매입(13→87%)**. C 조기수렴이 답 쓰는 phase 를 스킵한 것이 원흉이었고, 게이트가 그것을 막아 reached_productive 20→100%. 이제 남은 병목은 **productive-no-emit**(게이트 ON 에서 SYNTHESIZE 도달 후 A 가 emit 실패, 잔여 13%) = C 아닌 A-stage.

## 3. 다음 세션 최우선 — Exp26 v2 (추출기 폭 확장, plan-first) 또는 Exp27 (기권 층)

productive-no-emit(Exp25d)·일반화 v1(Exp26 v1) 둘 다 종결. 남은 로드맵:
- **접근 A — Exp26 v2 (커버리지 폭)**: 신규 결정론 추출기(`top_error_classes`/`freq_anomaly`/`timeline_gap`) 를 `context_tools.py` 에 구현 + 신규 실패모드 태스크(OOM/cert-expiry/disk-full). v1 은 2종만 확인 → 3종+·다양 모드로 fail-safe·커버리지 일반화 폭 확장. **공유코드(context_tools) 변경 → gemento-plan-create + 회귀게이트.** 추출기는 순수 함수라 Sonnet 위임 적합.
- **접근 B — Exp27 (기권 층)**: 결정론 추출기 근거 없을 때 "모른다" 반환 정확도 — confident-wrong 최종 차단. 아키텍처 4번째 구성요소.
- 이후: Exp28(GB 백엔드 ripgrep/인덱스, O(1) 실증) → 크로스모델 O(1)(논문 핵). `logAnalystDesign §4`.

권장: **Exp26 v2**(커버리지가 아키텍처 핵심 미검증 폭이고, v1 이 방법론·인프라 다 깔아둠). 추출기 finding 을 clean 주입 + 게이트 ON + n≥12/cell 패턴 그대로 재사용(`exp26_extractor_generalize.py`).

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

- **Exp26 v2(추출기 폭)·Exp27(기권 층)·Exp28(GB 백엔드) 미착수.** productive-no-emit(Exp25d)·일반화 v1(Exp26 v1) 종결.
- a2a 심화(구조화 planner+verification), 도메인 facet 다종화(H21 후속), 크로스모델, Stage 8~12 arc 논문화 — 전부 보류(로그분석가 우선).
- **opt-in 플래그 4개**: retrieval_discipline/list_failed_units/a2a_proposer(앞 3개 off 유지·비추천), **converged_requires_answer(Exp25c 로 효과 입증 — 로그분석가 경로에선 ON 권장)**. 롤백 X.

## 7. 다음 세션 시작 순서 (권장)

1. `git log --oneline -5`로 `bb3abaa` 확인. `logAnalystDesign.md`(§4) + `MEMORY.md` recall v7 + 본 문서.
2. 터널 healthcheck(`curl`) + Redis 키 확인. GPU 여유 사용자 확인(secall). **주의: 현 환경서 `import tools`/전체 회귀게이트가 수 분~20분 느림(경합) — 데드락 아님, nohup+Monitor 로 인내.**
3. **접근 A(레버)**: exp25c 실패 chain(final=False,prod=True)의 SYNTHESIZE A 응답 로깅 → productive-no-emit 원인 규명. 또는 **접근 B**: Exp26 추출기 다종화로 로드맵 진행.
4. 레버가 공유코드면 plan-first + 회귀게이트(75, off byte-identical). 진단만이면 바로.
