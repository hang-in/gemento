---
type: handoff
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
direction: architect → executor
updated_at: 2026-04-27
author: Architect Opus (macOS)
recipient: Codex CLI / Gemini CLI (Windows)
prior_handoff: handoff-to-opus-exp10-2026-04-27.md (commit 8797f71)
---

# 핸드오프: Exp10 재실행 — clean tree + run.py origin 복구

## 1. 배경

이전 Windows 실행 (`exp10_reproducibility_cost_20260427_013421.json`) 은 `experiments/exp10_reproducibility_cost/run.py` 의 dirty 상태로 인해 540 trial 중 360 trial 이 `null` — **무효**.

원인 (handoff-to-opus-exp10-2026-04-27.md 에서 식별):
- `trial_gemma_1loop()` / `trial_gemini_flash()` 의 result-dict return 블록이 로컬에서 누락된 채 실행됨.
- 두 함수가 `None` 을 반환 → `all_results.append(result)` 가 `null` 360개를 JSON 에 누적.

본 repo (`origin/main`, commit 8797f71) 의 `run.py` 는 정상 — `trial_gemma_1loop()` (line 117) / `trial_gemini_flash()` (line 149) 모두 dict return 보유.

## 2. 재실행 절차 (Windows PowerShell)

### Step 1 — 작업 트리 clean + run.py 복구

```powershell
cd path\to\gemento
git fetch origin
git status                                              # dirty 영역 확인
git restore experiments\exp10_reproducibility_cost\run.py   # dirty 파일 복구
git pull origin main                                    # origin 동기화
```

### Step 2 — clean 확인 + 실행 commit 기록

```powershell
git status --short                                      # 빈 출력 (clean) 이어야 진행
git rev-parse HEAD                                      # 실행 commit 기록 (예: 8797f71)
```

`git status` 가 clean 이 아니면 **재실행 중단**. 다른 dirty 파일이 있으면 별도 검토 필요.

### Step 3 — 재실행 (commit hash 를 log 첫 줄에 기록)

```powershell
cd experiments
$commit = git rev-parse HEAD
$startedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
"=== Exp10 rerun start: commit=$commit, started_at=$startedAt" | Out-File exp10_reproducibility_cost\rerun.log -Encoding utf8
..\.venv\Scripts\python run_experiment.py reproducibility-cost 2>&1 | Tee-Object -FilePath exp10_reproducibility_cost\rerun.log -Append
```

예상 시간: 5-12 시간 (이전 실행과 동일).

### Step 4 — 결과 push

```powershell
cd path\to\gemento
git status                                              # 변경 파일 확인
# 신규 결과 JSON: exp10_reproducibility_cost_<NEW_TIMESTAMP>.json
# rerun.log 도 함께 push
git add experiments\exp10_reproducibility_cost\results\exp10_reproducibility_cost_*.json
git add experiments\exp10_reproducibility_cost\rerun.log
git commit -m "exp10: rerun on clean tree (commit 8797f71)"
git push origin main
```

기존 무효 JSON (`exp10_reproducibility_cost_20260427_013421.json`) 은 그대로 둡니다 (timestamp 자연 분리). 향후 archive 처리는 architect 가 분석 단계에서 별도 결정.

## 3. 안전장치 / 위험

- **dirty 영역 잔존 위험**: Step 1 의 `git status` 가 clean 이 아니면 `run.py` 외 다른 파일도 영향 가능. 이 경우 재실행 중단 + Architect 에 보고.
- **Gemini API 키 검증**: 재실행 전 `$env:GEMINI_API_KEY` 또는 `gemento/.env` 의 `GEMINI_API_KEY=AIza...` 가 유효한지 확인. 이전 실행에서 정상이었으므로 동일 환경이면 OK.
- **LM Studio serving 확인**: `gemma4-e4b` 모델이 LM Studio 에서 로드된 상태인지 확인 (`http://yongseek.iptime.org:8005/v1/models` 응답).
- **체크포인트 보존**: 이전 실행의 `partial_exp10_reproducibility_cost.json` 이 남아있으면 resume 시도 위험. 재실행 전 삭제 권고:
  ```powershell
  Remove-Item experiments\exp10_reproducibility_cost\results\partial_exp10_reproducibility_cost.json -ErrorAction SilentlyContinue
  ```
- **Rate limit 위험**: Gemini 2.5 Flash 호출 1초 sleep 보유. 540 trial 안 180 만 Gemini 호출 → ~3 분 추가 wallclock.

## 4. 권고 사항 (handoff-to-opus 의 권고 3·4 처리)

- **권고 3 (raw response logging)**: v1 재실행 끝나기 전까지는 미적용. 본 재실행에서 만약 또 JSON parse fail 다수 발생하면 v2 재실행 전에 logging 추가 plan 진행.
- **권고 4 (한국어 응답 채점 패널티)**: 별도 plan 영역. 본 재실행과 무관. v1 결과 받은 후 Architect 가 한국어 trial 비율 분석 후 결정.

## 5. 재실행 완료 후 Architect 측 작업

Codex/Gemini 가 push 완료 보고하면 Architect (본 chat) 가:
1. 신규 결과 JSON 540 trial dict 모두 채워졌는지 검증 (`null` 0건)
2. `analyze.py` 실행 → `exp10_report.md` 생성
3. mean accuracy / cost / wallclock 표 정리
4. researchNotebook 의 Exp10 섹션 갱신
5. Codex 권고 3·4 별도 plan 진행 여부 사용자 결정 요청

## 6. 관련 산출물

- 본 핸드오프: `docs/reference/handoff-to-gemini-exp10-rerun-2026-04-27.md`
- 이전 분석: `docs/reference/handoff-to-opus-exp10-2026-04-27.md` (Codex 작성)
- 실행 코드: `experiments/exp10_reproducibility_cost/run.py` (origin/main 기준 정상)
- analyze: `experiments/exp10_reproducibility_cost/analyze.py`

---

**작성**: Architect Opus (macOS, 2026-04-27)
**수신**: Codex CLI / Gemini CLI (Windows)
**상위 목표**: Exp10 결과 정상 산출 → arXiv preprint v1 의 통계 신뢰도 input
