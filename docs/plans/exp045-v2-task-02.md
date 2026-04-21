---
type: task
status: todo
updated_at: 2026-04-15
plan: exp045-v2
depends_on: [exp045-v2-task-01]
---

# Task 2: exp045 v2 재채점 결과 기록

## Changed files

- `docs/plans/scoring-v2-result.md` — exp045 v2 수치 추가 및 "Solo vs ABC 동일 기준 비교" 섹션 삽입

신규 파일 없음.

## Change description

1. Task 1 완료 후 `python3 experiments/measure.py --rescore` 재실행.
2. `scoring-v2-result.md` 하단에 다음 섹션 추가:
   - **Rescore 전체 표** — 최신 `--rescore` 출력을 코드 블록으로 붙여넣기 (exp045 포함)
   - **Solo vs ABC 동일 기준 비교 (v2)** — 표 형식
     | 실험 | v2 평균 | 태스크 수 | 트라이얼 수 |
     |------|---------|-----------|-------------|
     | exp06 Solo | 0.xxx | 9 | N |
     | exp045 ABC | 0.xxx | 9 | N |
     | **Δ (ABC − Solo)** | ±0.xxx | | |
   - **한 줄 결론** — v2 기준으로 ABC가 Solo보다 높은지/낮은지/유사한지 사실만 기술 (해석은 3순위 플랜에서).
3. 문서 frontmatter의 `updated_at`을 오늘 날짜(2026-04-15)로 갱신.

## Dependencies

- **Task 1 완료 필수** — Task 1이 끝나지 않으면 exp045 v2 수치를 얻을 수 없음.

## Verification

```bash
# 1) --rescore 출력에서 exp045 숫자 확보
python3 experiments/measure.py --rescore | tee /tmp/rescore_out.txt
grep exp045 /tmp/rescore_out.txt

# 2) 결과 문서에 exp045와 Solo vs ABC 비교가 포함되었는지 확인
grep -E "exp045|Solo vs ABC" docs/plans/scoring-v2-result.md

# 3) 문서 frontmatter 갱신 확인
head -5 docs/plans/scoring-v2-result.md
```

기대 결과:
1. `/tmp/rescore_out.txt`에 exp045 v1/v2/diff 수치 포함
2. 결과 문서에 exp045 행과 "Solo vs ABC" 섹션 존재
3. `updated_at: 2026-04-15`

## Risks

- **Task 1 결과 의존**: Task 1에서 exp045 v2 값이 비정상(0.000 등)이면 Task 2도 블로킹됨 → Task 1 재작업 필요.
- **해석 과다**: 이 Task는 **수치 기록만** 담당. "Solo가 이겼다/ABC가 이겼다" 같은 해석은 3순위 플랜(실험 6 결론 재작성)에서 다룬다. 여기서는 단순 수치·차이만 기술.
- **기존 내용 덮어쓰기**: `scoring-v2-result.md`의 기존 섹션은 보존. **추가**만 하고 삭제·수정 금지.

## Scope boundary

수정 금지:
- `experiments/measure.py` (Task 1 영역)
- `experiments/tasks/taskset.json`
- `docs/plans/scoring-v2.md`, `docs/plans/scoring-v2-task-*.md` (완료된 플랜)
- `docs/plans/exp045-v2.md`, `docs/plans/exp045-v2-task-01.md` (별도 관리)
- `experiments/results/*.json` (읽기 전용)
