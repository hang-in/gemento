---
type: reference
status: completed
updated_at: 2026-04-27
author: Codex CLI (Windows)
recipient: Architect Opus
---

# 핸드오프: Exp10 실행 완료 후 간단 리뷰 — 결과 JSON 무효, 재실행 필요

## 1. 결론
- **실행 자체는 끝까지 진행됨**: `run.log` 기준 `gemma_8loop`, `gemma_1loop`, `gemini_flash`가 마지막 `logic-04 | trial 20`까지 도달함.
- **하지만 최종 결과 JSON은 무효**: `experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_20260427_013421.json`의 `trials` 540개 중 **180개만 dict**, **360개는 `null`**.
- 따라서 **이번 Exp10은 공식 비교 결과로 사용하면 안 됨**. 재실행이 필요함.

## 2. 확인된 원인
- Windows 로컬 작업 트리가 `main` clean 상태가 아니었음.
- 특히 `experiments/exp10_reproducibility_cost/run.py`가 로컬에서 수정되어 있었고, `trial_gemma_1loop()` / `trial_gemini_flash()`의 기존 결과 파싱·`return` 블록이 `# ... (중략)`으로 대체되어 있었음.
- 그 결과:
  - `gemma_8loop`는 정상적으로 dict 결과를 반환
  - `gemma_1loop`, `gemini_flash_1call`는 함수가 `None`을 반환
  - `all_results.append(result)`에 의해 `null` 360개가 최종 JSON에 저장됨
- `run.log`의 condition 시작 횟수도 이를 뒷받침함:
  - `gemma_8loop`: 181 start (`math-01 trial 1` 중복 시작 1회 포함)
  - `gemma_1loop`: 180 start
  - `gemini_flash`: 180 start

## 3. 이번 런에서 의미 있게 볼 수 있는 것
- **부분적으로는 `gemma_8loop` 180건만 유효**.
- 해당 subset 요약:
  - mean accuracy: `0.2611`
  - mean duration: `304.13s`
  - median duration: `231.26s`
  - mean cycles: `10.46`
- 다만 이것도 **한국어 응답이 영어 키워드 채점에서 0점 처리되는 문제**가 섞여 있어, 절대 수치 해석에는 주의가 필요함.

## 4. 부가 관찰
- `orchestrator.py` Safe Mode (`model: ""`, `response_format` 제거) 때문에 A/B/C 내부에서 `JSON parse failed`가 간헐적으로 발생했지만, 이는 trial-level 실패와 동일하지 않았음. 여러 케이스가 retry 또는 다음 cycle에서 회복되어 최종 `error=null`로 종료됨.
- `gemma_8loop`는 최종 `final_answer`만 checkpoint에 남고 raw A/B/C 응답은 저장하지 않아 malformed JSON 사후 분석은 어려움.
- Exp10 analyzer도 현재 결과 파일의 `null` 360개 때문에 바로 실패함.

## 5. 권고 사항
1. `run.py`를 `origin/main` 기준 정상 반환 로직으로 복구한 뒤 **Exp10 전체 재실행**.
2. 재실행 전 작업 트리 clean 여부를 먼저 고정하고, 실행 브랜치/커밋을 로그 첫 줄에 남기기.
3. 선택 옵션으로 `gemma_8loop` A/B/C raw response debug logging 추가. 현재는 parse fail 원인 분석이 어려움.
4. 채점 해석 시 한국어 응답 패널티를 별도 플래그로 분리하거나 사후 rescoring 절차를 준비하기.

## 6. 관련 산출물
- 최종 결과 파일: `experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_20260427_013421.json`
- 실행 로그: `run.log`
- 참고용 Windows 운영 메모: `docs/reference/handoff-from-gemini-to-codex-win.md`

---
**Codex CLI (Windows) 작성 — 2026-04-27**
