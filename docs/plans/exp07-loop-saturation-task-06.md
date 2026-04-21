---
type: task
status: pending
plan: exp07-loop-saturation
task: 6
parallel_group: C
depends_on: [1, 2, 3, 4, 5]
updated_at: 2026-04-21
---

# Task 6: 핸드오프 문서 작성

## Changed files

- `docs/reference/handoff-to-gemini-exp7.md` — **신규 파일**
- `docs/reference/index.md` — 핸드오프 링크 추가

## Change description

Gemini CLI(Windows)가 실험 7을 실행할 수 있도록 완전한 핸드오프 문서를 작성한다.
기존 `handoff-to-gemini-exp6.md` 형식을 따른다.

### 문서 구조

```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-21
author: Claude Opus 4.6 (macOS)
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 7 — Loop Saturation + Loop-Phase 프롬프트

## 1. 연구 질문

"ABC 파이프라인에서 루프 한계수익이 0에 수렴하는 포화점은 어디이며,
루프 단계별 프롬프트 분화가 포화점을 이동시키는가?"

### 실험 설계
- 2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20)
- 12 태스크 (기존 9 + 고난도 3) × 3 trials × 8 조건 = 288 runs

### 해석 프레임
| 결과 | 해석 |
|------|------|
| phase > baseline 전 구간 | Loop-Phase 프롬프트가 일관된 개선 제공. 채택 |
| phase ≈ baseline | 프롬프트 분화 효과 없음. 현재 프롬프트 유지 |
| 15 → 20 정답률 변화 < 2%p | 포화점 ≈ 15. 15 이상은 불필요 |
| 20에서도 정답률 상승 중 | 포화점 미도달. MAX_CYCLES 더 높여야 함 |

## 2. 환경 및 실행

### 2.1. 사전 확인
- git pull, venv 활성화, ollama 확인

### 2.2. 실험 실행
python run_experiment.py loop-saturation

### 2.3. 예상 소요시간
- 288 runs × ~8분/run ≈ 38시간 (조기 수렴 시 20~30시간)
- 체크포인트: results/partial_loop_saturation.json (자동 저장/이어하기)

### 2.4. 결과 확인
python measure.py "results/exp07_loop_saturation_*.json"

## 3. 관찰 포인트
1. 포화 곡선: MAX_CYCLES 8→11→15→20에서 정답률이 평탄해지는 구간
2. Phase 프롬프트 효과: baseline과 phase의 정답률/수렴률 차이
3. 고난도 태스크(04급): 기존 9개와 비교하여 더 많은 사이클을 소모하는지
4. logic-04 (거짓말쟁이 퍼즐): logic-02(40%) 약점이 패턴 반복되는지
5. synthesis-04 (6소스 교차): 모순 식별 + 계산이 동시에 필요한 복합 태스크

## 4. 결과 기록 및 푸시
git add experiments/results/exp07_loop_saturation_*.json
git commit -m "feat: 실험 7 loop-saturation 결과 추가"
git push origin main

## 5. 비교 기준선
- exp045 (handoff_protocol, 5b): 88.9%, 평균 7.2 사이클, MAX=12
- exp06 (solo_budget): v2 기준 96.7%, MAX=21

## 6. 신규 태스크 정보
| ID | 난이도 | 핵심 도전 |
|----|--------|----------|
| math-04 | very_hard | 3변수 LP 최적화 (코너 포인트 탐색) |
| logic-04 | very_hard | 4인 거짓말쟁이 (4회 귀류법) |
| synthesis-04 | very_hard | 6개 보고서 교차 검증 + 모순 식별 |

## 7. 트러블슈팅
- 기존 exp6과 동일 (httpx, Ollama 타임아웃, GPU)
- 체크포인트 이어하기: 재실행만 하면 자동
- 특정 조건만 재실행: 현재 미지원 (partial JSON에서 해당 조건 수동 삭제 후 재실행)
```

### index.md 업데이트

핸드오프 섹션에 링크 추가:
```
- [handoff-to-gemini-exp7.md](handoff-to-gemini-exp7.md) — Gemini 인계: 실험 7 Loop Saturation + Loop-Phase
```

## Dependencies

- Task 1–5 모두 완료 (실험 코드가 완성되어야 정확한 실행 지침 작성 가능)

## Verification

```bash
# 파일 존재 확인
test -f /Users/d9ng/privateProject/gemento/docs/reference/handoff-to-gemini-exp7.md && echo "OK" || echo "MISSING"
```

```bash
# index.md에 링크 포함 확인
grep -c "handoff-to-gemini-exp7" /Users/d9ng/privateProject/gemento/docs/reference/index.md
# 1 이상이어야 함
```

## Risks

- 예상 소요시간이 실제와 다를 수 있음 → "조기 수렴 시 단축" 명시
- 체크포인트 이어하기 로직이 Task 4 구현에 따라 달라짐 → Task 4 완료 후 정확한 지침 작성

## Scope boundary

수정 금지:
- 기존 핸드오프 문서 (`handoff-to-gemini-exp5b.md`, `handoff-to-gemini-exp6.md`)
- `experiments/` 디렉토리 내 모든 파일 (이 task는 문서만 작성)
