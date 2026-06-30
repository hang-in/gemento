# Handoff to Next Agent — Stage 7/8 마감, 다음: test9ng 초대형 실로그 + facet 도구

- **인계 시점**: 2026-06-30
- **현재 단계**: Stage 7 Context Router 라인(Exp15~19) 완결 + Stage 8(mandatory opt-in) 완료 + test 위생 정리 완료. 모두 `origin/main` 푸시됨 (HEAD `ee604f9` 근처).
- **다음 세션 순서 (사용자 확정)**: ① **test9ng 초대형 실로그 router 검증(Exp20)** 먼저 → ② **facet 도구 프로토타입 + A/B**.

---

## 1. 이번 세션 달성 (요약)

이전 핸드오프(2026-06-28)의 과장(n=1, mock, H14 충돌)을 **검증·정정**하고, Context Router를 합성→실데이터로 끝까지 밀어붙였다.

- **(a) 과장 정정**: Stage 7 v1의 "35% latency"(n=1+num_ctx artifact) 철회, H14 충돌(cross-model vs context) → **Context 가설 H15로 재부호화**, n100 caddy는 mock(`is_fallback`)이었음을 명시. 영문 노트북은 append-only errata.
- **(b) Exp15 v2 (H15 ⚠ 조건부 채택)**: canonical gemma4:e4b, 5 task × 4 arm × num_ctx{4096,32768} × n=5. router 큰 로그 우위(0.908 vs 0.125), overflow서 유일 생존, 작은 로그엔 손해(입력 크기 의존).
- **(c) Exp15 v3 (push/pull capacity 분기)**: gemma4:**e2b**는 agent tool-use 미달(router 0.097) → push(ErrorBlocks)만 됨; **e4b**는 pull(agent 도구). **e2b archived**, 주력=e4b. (사용자: e2b·tps·ripgrep 교체는 의미 없다고 판단 — 추구 안 함.)
- **(d) Exp16/16b/16c**: retry 단독 50~70%(H16 부분) → **mandatory 프롬프트가 per-attempt 27→83%(H16b, 원인=전사 누락)** → mandatory+retry **100%(H16c)**.
- **(e) Exp17 (H17 부분)**: e4b+router가 multi-hop/집계/distractor 스케일(baseline 92%); 단 mandatory는 **failure-mode-specific**(hard task −3pp).
- **(f) Exp18 (H18 ✅ size invariance)**: 합성 ~245K tok(컨텍스트 7.5배)서도 92~100% 무저하. **router가 인지부하를 로그 크기와 분리(O(1))**.
- **(g) Exp19 (실데이터 검증)**: **n100 실 journald 1.15M tok → boxie e4b router가 실제 certbot 장애 5/5 정확 진단**. mock caddy 정직한 대체. mean 0.7은 keyword artifact("failing to renew"≠"failed to start"), 실정확도 5/5.
- **(h) Stage 8**: mandatory를 `run_abc_chain(mandatory_tool_prompt=False)` opt-in으로 정식 편입(`system_prompt.MANDATORY_TOOL_RULES`). 기본 False=거동 byte-identical(회귀 게이트 `tests/test_mandatory_optin.py` 5/5). 자동 게이트는 증거 부족으로 보류(plan: `docs/plans/mandatory-tool-opt-in.md`).
- **(i) test 위생**: Stage 7이 top-level `experiments/results/`에 쓴 tuna/caddy를 exp15 하위로 이동 + `TestResultFilesByExperiment` 카운트 갱신 → `test_static` 43 OK.

**인프라 사실**: RTX 5060Ti, gemma4:e4b Q4_K_M = 생성 ~95 tok/s, prefill ~1,620 tok/s. router가 prefill을 로그 크기서 분리(stuffing 1.15M tok ≈ ~12분 vs grep 결과 ~3초).

---

## 2. 핵심 인프라 / 접속 (다음 세션 필수)

- **boxie** (외부 GPU 서버, gemma4:e4b 실행기): SSH `ssh -p 2232 -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187`. Ollama OpenAI/native API.
  - **터널** (boxie ollama → 로컬 11435): `ssh -p 2232 -N -L 11435:127.0.0.1:11434 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -i C:/Users/사자/.ssh/id_ed25519 d9ng@14.58.110.187` (백그라운드). **터널/서버 불안정 — 끊기면 재수립 후 resume.**
  - gemma4:e4b + gemma4:e2b 둘 다 pull 됨.
- **n100** (내부 장기운영 서버, 진단 대상): `~/.ssh/config` alias **`n100`** (192.168.1.121:9207). journald 9.8M줄. Exp19에서 검증 완료.
- **test9ng** (≡ `test-server`, host `d9ng-i3-laptop`): `~/.ssh/config` alias **`test9ng.ddns.net`** (9207). **원격 셸이 fish** → bash 명령은 `ssh test9ng.ddns.net bash -s <<'EOF' ... EOF` 로 stdin 파이프. fish init이 stdout에 에러 찍을 수 있으니 `source:`/`openclaw.fish` 라인 필터.
- 실험 실행: cloud/SSH는 에이전트 직접 가능(로컬 VRAM 무관). 로컬 LLM 로딩은 사용자만(VRAM 경합). 메모리 [[reference-remote-gemma-ssh-tunnel]] 참조.

---

## 3. 다음 세션 작업 ① — Exp20: test9ng 초대형 실로그 router 검증

**이미 준비됨**: test9ng 30일 저널을 로컬 스크래치패드에 복사 완료 (단, 스크래치패드는 세션별이라 **다음 세션엔 재pull 필요**):
```
ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.log 2>/dev/null
```
- **크기**: 112MB / 1,105,195줄 / **~29.3M tok** (n100의 25배, 컨텍스트의 ~900배). stuffing 절대 불가.
- **실 needle 2종**:
  1. **gohttpserver.service 크래시루프** ("Failed with result 'exit-code'" 반복). → 단일 needle, 16KB 캡 robust. 채점 `[["gohttpserver"],["failed"]]`.
  2. **SSH brute-force 5,093건**, 최다 IP **45.144.212.75(×286)**, 77.83.39.x 클러스터. → 집계 needle, **grep_context 16KB 캡 스트레스**. 채점 `[["45.144.212.75"]]`(+"failed password").

**설계 (Exp20, `run_v20_megalog.py` 신규)**: 로컬 파일 → Redis 스풀 → boxie e4b **router+mandatory+retry**, 두 task × n=5. `run_v19_n100_journald.py` 패턴 복제(SSH-pull 대신 로컬 파일 로드 + Redis SET).
- **확인 사항**: 112MB Redis SET(<512MB OK) + `grep_context`가 매 호출 112MB를 `splitlines()`+regex → **grep당 ~5-10초**(느리지만 가능). 너무 느리면 7d 윈도우로 축소.
- **판별**: (a) 29M tok서도 size-invariance 재확인(certbot류). (b) 5093 매치가 16KB 캡에 막히면 **그 자체가 facet 도구 필요성의 실증 데이터** → ②로 연결.

---

## 4. 다음 세션 작업 ② — facet 도구 프로토타입 + A/B

**동기**: gemento 약점=시간, 강점=긴 로그 완전탐색(단 **exhaustiveness는 grep(도구)의 것**, "질의한 패턴에 한해서만"). 약점은 **모델의 패턴 선택/recall**(Exp14 under-query) + **grep_context 16KB 출력 캡**(고매치-볼륨서 누락). ripgrep 교체는 **무의미**(속도 병목 아님, grep는 이미 Python regex).

**진짜 레버 = 구조화 facet 도구** (텍스트 패턴 추측 대신 결정론적 이상치 요약):
- 후보: `summarize_log_anomalies(handle)` / `list_failed_units(handle)` / `error_type_histogram(handle)` / `count_by_pattern(handle, pattern)` (캡 대신 카운트+샘플 반환).
- **A/B**: grep-only vs grep+facet, test9ng/n100 실 저널(특히 brute-force 집계 task)에서. under-query·16KB-캡 두 약점을 동시에 치는지 측정.
- **경고 (반드시 반영)**: 도구 추가 = 소형 모델 오용 여지 증가(e2b는 grep도 못 몰았고 Exp17은 mandatory가 추론 task에 −). **"more structure ≠ monotonically better"** — A/B 검증 후에만 채택. 공유 코드(`tools/context_tools.py`, `orchestrator.py`) 변경이면 **plan-first(gemento-plan-create) + 회귀 게이트**.

---

## 5. 워크플로 / 규약 메모

- **plan 문서 셋**: `gemento-plan-create` 스킬 (공유 코드/인프라 변경 시). **verdict 기록**: `gemento-verdict-record` (영문 노트북 **append-only** 강제 — 기존 entry 수정 금지, Change History 위 append). 둘 다 이번 세션에 사용함.
- **명명 규약 (2026-06-30 §5 개정)**: 신규 변종/간이 실험은 **letter suffix**(Exp20b), `0X5` half-notation 폐기. `Exp035`/`Exp045`는 historical alias(rename 안 함).
- **실험 드라이버 위치**: `experiments/exp15_context_router/run_v1x.py`. native caller `native_ollama_caller.py`(num_ctx 제어 + tool-loop 내장 — orchestrator의 model_caller 경로는 tool_calls 미실행이라 필요). 결과 JSON은 같은 dir `results/`. **stdout 로그는 `exp*_run*.log`로 .gitignore됨.**
- **scorer caveat**: keyword 채점이 의미 정답을 과소평가(Exp19 0.7 vs 실 5/5; H12/H13/Exp19). 보조 후보: LLM-as-judge(paper-review P1-3, 보류 중).
- **side 워크트리** `D:/privateProject/gemento-side-exp15`(브랜치 `side/exp15-crossmodel-ministral`)에 일부 구버전 드라이버 존재 — main이 canonical. 정리하려면 `git worktree remove`(단 .env 사본 있음).

---

## 6. 미해결 / 보류

- **자동 게이트(mandatory)**: 증거 부족(로그 크기≠신호) — facet/데이터 더 모은 뒤 재고.
- **LLM-as-judge 보조 채점**: keyword artifact 해소용, 보류.
- **e2b push-기반 외재화**: 사용자 판단 "의미 없음"(tool-use 불량) — 보류.
- **paper(draft.md/.ko.md)**: H15~H18·Exp19 실데이터·size-invariance(O(1)) 반영 미완 — 라인 정리되면 paper 갱신 후보.
