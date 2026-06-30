---
type: reference
status: done
updated_at: 2026-06-30
---

# Exp21 — Facet Aggregate Tool A/B 분석 (grep-only vs grep+facet)

> 결과 JSON: `experiments/exp15_context_router/results/exp21_facet_ab_gemma4_e4b.json`
> 드라이버: `experiments/exp15_context_router/run_v21_facet_ab.py`
> 선행: Exp20 진단(megalog finalization), pilot(grep_facet task A n=2)

## 1. 결론 (findings-first)

**H21 ⚠ 조건부 채택 (aggregation-specific).** 결정론적 전수 집계 도구 `aggregate_context`(16KB 라인덤프 대신 untruncated 그룹별 top-N 카운트)는 **집계형 task에서 결정적**으로 정확도를 끌어올리지만(score 0.0→0.8), **단일-needle task엔 무효**(0.3→0.2, 거의 미사용)다. "more structure ≠ monotonically better" — facet은 failure-mode-specific 도구다(Exp17 mandatory와 동형 패턴).

## 2. 설정

- 대상 로그: test9ng 30일 journald, **117MB / 1,105,320줄 / ~29.3M tok**(컨텍스트 32K의 ~900배).
- 모델/실행: gemma4:e4b @ boxie(RTX 5060Ti), router+mandatory+retry, max_cycles=8, n=5.
- A/B: 두 arm의 유일 차이 = `aggregate_context` 도구 가용성(caller `extra_tool_schemas/fns` opt-in 주입). 글로벌 도구 표면 불변.
- 2 task: **A** gohttpserver 크래시루프(단일 needle), **B** SSH brute-force 최다 IP(top-N 집계, 정답 `45.144.212.75` ×286 / 총 5,093건).
- 지표: 1차 = non-null ans rate(finalization), 2차 = keyword score(정확도). elapsed ~2.4h.

## 3. 결과 매트릭스

| arm | task | non_null_rate | mean_score | mean_attempts | facet_calls |
|---|---|---|---|---|---|
| grep_only | A 크래시루프 | 0.4 | 0.3 | 2.2 | — |
| grep_only | B 집계 | **1.0** | **0.0** | 1.6 | — |
| grep_facet | A 크래시루프 | 0.2 | 0.2 | 3.0 | 3 |
| grep_facet | B 집계 | **1.0** | **0.8** | 1.4 | 16 |

## 4. 메커니즘 — "confidently-wrong" 집계 (task B)

facet의 가치는 task B 답변에서 결정적으로 드러난다:

- **grep_only: 5/5 전부 확신에 차서 틀림** → 모든 trial이 `174.138.8.10`을 "최다"로 단정. `grep_context('Failed password')`가 5,093 매치를 16KB(시간순 앞 ~100여 줄)로 절단 → 모델은 **그 윈도우에서 일찍·자주 보인 IP**를 전역 최다로 오인. **일관된 동일 오답 = 무작위가 아니라 16KB 캡의 체계적 아티팩트.** non_null_rate 1.0(항상 finalize)이지만 정확도 0.0.
- **grep_facet: 4/5 정답** → `aggregate_context('Failed password', group_by='from (IP)')`가 `truncated:False`로 전수 카운트를 반환 → 모델이 `45.144.212.75`를 정확히 식별. trial 1만 facet 미활용으로 오답. facet 16회 호출(채택 확인).

→ facet은 **그것이 설계된 실패모드(16KB 캡이 유발하는 집계 오류)를 정확히 교정**한다.

## 5. task A — facet 무효 + 수렴의 확률성

- grep_facet가 task A score를 못 올림(0.3→0.2, n=5 노이즈 내). 모델이 facet을 거의 안 씀(3 calls). 단일 needle(unit 이름)은 grep으로 찾히고, 절단이 **답 자체**를 막지 않는다("gohttpserver"+"failed"는 첫 16KB에 존재).
- task A finalization은 **양 arm 모두 확률적**(grep_only 0.4, grep_facet 0.2). pilot에서도 trial 1은 facet 없이 수렴, trial 2는 facet으로 수렴 — 수렴은 도구가 아니라 ABC judge의 run-to-run 변동에 좌우.

## 6. 방법론 교훈 — 1차 지표의 역전

- **non-null rate(1차 지표)가 task B에서 무력**(양 arm 1.0). 진짜 신호는 **score(정확도, 2차)**. grep_only는 "finalize는 하되 confidently-wrong". non-null rate만 봤다면 facet 가치를 완전히 놓쳤을 것.
- 향후 실험은 **finalization과 accuracy를 분리 측정**해야 한다. "답을 냈다"≠"맞다".

## 7. Exp20 진단의 재평가

Exp20 진단([[exp20-finalization-diagnosis]])은 task A finalization=None에 집착해 "16KB 캡→finalization 실패"로 결론했다. 전체 n=5는 이를 두 갈래로 정정한다:
- task A finalization은 **확률적**(grep_only 0.4)이고 facet도 못 고친다 — 진단의 결정론적-실패 프레이밍은 n=1 불운이 섞였다.
- facet의 **진짜 가치는 task B 정확도**였는데 진단이 과소평가. 핵심 실패모드는 task A의 "finalization 실패"가 아니라 task B의 **"16KB 캡→confidently-wrong 집계"**다.

## 8. Caveats

- n=5 소표본. keyword scorer(단, 여기선 IP 정답을 정확히 포착 — Exp19 artifact의 역전 사례).
- 단일 모델(e4b), 단일 facet 도구(aggregate_context), 2 task.
- task A의 약한 음수(0.3→0.2)는 노이즈 가능 — "무효"로 해석(유의한 해악 아님).
- grep_facet B trial 1 오답 = facet 미활용 → 도구 제공이 사용을 보장하진 않음(Risk 2 부분 잔존).

## 9. 함의 / 다음

- facet 도구는 **집계형 진단(top-N by field: 최다 IP, 최다 실패 unit, 에러 타입 분포)에 한해 채택 가치**. 단일 needle 검색엔 grep으로 충분.
- 후속 후보: 집계 task 전용 가치가 입증됐으니 `list_failed_units`/`error_type_histogram` 등 도메인 facet 다종화를 **집계 task 벤치에 한해** 재고. 단 도구 표면 증가의 오용 리스크(task A에서 보듯 무관 task엔 미사용/혼선) 경계.
- ABC judge의 task A 확률적 finalization은 별도 사안(orchestrator 수렴) — 본 실험 범위 밖.
