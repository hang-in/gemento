---
type: plan
status: done
completed_at: 2026-04-27  # auto-set 2026-05-03 stale cleanup
updated_at: 2026-04-27
---

# Plan: Exp10 복구 & 재실행 (Recovery & Re-run)

## Goal

Exp10 첫 실행 결과가 540 trials 중 360개 무효(null)로 나왔다. 근본 원인(Windows `run.py` 손상)을 해결하고 **540개 모두 유효한 결과로 재실행** 완료.

## Root Cause

Windows 로컬 작업 트리 상태:
- `run.py` 에서 `trial_gemma_1loop()` 와 `trial_gemini_flash()` 함수의 return 블록이 제거됨
- `gemma_1loop` 와 `gemini_flash_1call` condition 이 `None` 반환 → 360개 trial 이 `null` 기록됨

Mac 버전 검증: 정상 (return 블록 양호)

## Solution

1. **Task 01** (Windows/Codex): `origin/main` 에서 `run.py` 복원 → 재실행 → 540 유효 결과 확보
2. **Task 02** (Mac/Architect): 재실행 결과로 cost/reproducibility analysis 생성

## Phase Breakdown

### Phase 1: Recovery (Task 01, Codex/Windows)

- git checkout origin/main 로 run.py 복원
- partial checkpoint 삭제
- 재실행 (--trials 20, 약 2-3시간)
- 결과 유효성 검증

**예상 완료**: 2026-04-27 야간 또는 2026-04-28 오전 (실행 시간에 따라)

### Phase 2: Analysis (Task 02, Architect/Mac)

- 540 valid trials 로 cost/reproducibility 분석 생성
- experiments/measure.py 기반 summary report
- H3 (reproducibility/cost profile) 결과 도출

**예상 완료**: Phase 1 완료 후 즉시

## Acceptance Criteria

### Task 01 Complete

✅ 540 trials 모두 valid (null=0)  
✅ 3 conditions mean accuracy 모두 유효한 숫자  
✅ 신규 result JSON 생성됨  
✅ 기존 invalid result 파일 또는 partial 체크포인트는 정리됨  

### Overall Plan Complete

✅ Task 01 완료  
✅ Task 02 분석 리포트 생성  
✅ Notebook 또는 README 에 Exp10 결과 추가됨  

## Related Documents

- `docs/reference/handoff-to-opus-exp10-2026-04-27.md` — Codex 분석 (root cause)
- `docs/reference/handoff-from-opus-exp10-recovery-2026-04-27.md` — Architect 체크리스트
- `experiments/measure.py` — analysis 함수 (Task 02 사용)
- `experiments/exp10_reproducibility_cost/run.py` — dispatcher (복원 대상)

## Timeline & Ownership

| Task | Owner | Status | Due | Notes |
|------|-------|--------|-----|-------|
| Task 01 | Codex (Windows) | todo | 2026-04-27/28 | Windows re-run, 2-3h |
| Task 02 | Architect (Mac) | pending | 2026-04-28 | After Task 01 |
| Overall | Joint | in_progress | 2026-04-28 | Review & merge |

## Rollback Plan

Task 01 중 심각한 오류 발생 시:
- 이전 invalid result 파일 보관 (현재도 존재)
- git reflog 로 commit history 복원 가능
- 최악: Codex 가 이전 Windows checkpoint 재로드 후 clean run 재시도

## Next Steps After Completion

1. Exp10 유효 결과 → 한국어 커뮤니티 리드미 반영 ("무려 540개 trial...")
2. H3 (reproducibility) 검증 완료 → 주요 논문 결과 업데이트
3. Exp11 (ablation) 설계 시작
