# Subtask Template

`docs/plans/<slug>-task-NN.md` 의 본문 형식.

```markdown
---
type: plan-task
status: pending
updated_at: <YYYY-MM-DD>
parent_plan: <slug>
parallel_group: <A|B|C|...>
depends_on: [<NN>, ...]
---

# Task NN — <task 한 줄 제목>

## Changed files

- `<file path>` — **<신규|수정 (추가만)|수정>**. <한 줄 변경 요약>
- `<file path>` — **<...>**. <...>

신규 <N>, 수정 <M>.

## Change description

### 배경

<1-2 단락 — 왜 이 task 가 필요한가, parent plan 의 어느 결정/Risk 와 연결되는가>

### Step 1 — <단계 제목>

<설명 + 코드 블록>

\`\`\`python
<코드 예시>
\`\`\`

### Step 2 — <단계 제목>

<설명 + 코드>

<... Step N>

## Dependencies

- <다른 task NN> 마감 (해당 시)
- 패키지: <외부 패키지 또는 "없음">
- 기존 파일: `<path>` (read-only)

## Verification

\`\`\`bash
# 1) syntax + import
.venv/Scripts/python -m py_compile <file>
.venv/Scripts/python -c "from <module> import <symbol>; print('verification 1 ok')"

# 2) <behavior test>
.venv/Scripts/python -c "
<test code>
print('verification 2 ok: ...')
"

# 3) <integration test>
\`\`\`

<N> 명령 모두 정상.

## Risks

- **Risk 1 — <제목>**: <본문>. <대응>
- **Risk 2 — <제목>**: <본문>. <대응>
- **Risk 3 — <제목>**: <본문>. <대응>

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `<task 영역 외 파일 1>` (<다른 task 영역>)
- `<task 영역 외 파일 2>`
- `experiments/measure.py` / `score_answer_v*` (해당 시)
- `experiments/run_helpers.py` (Stage 2A — 해당 시)
- `experiments/schema.py` (해당 시)
- 모든 기존 `experiments/exp**/run.py` — 변경 금지 (read-only 참조만)
- 결과 JSON
```

## 작성 시 주의

- **Verification 명령은 사용자가 그대로 실행 가능해야 한다**. 환경 (`.venv/Scripts/python`) 명시. import 경로 정확히.
- **Step 의 코드 블록은 Sonnet 이 그대로 복사하지 않도록** — *패턴* 또는 *예시* 라고 명시. 임의 단순화 위험을 본문에서 경고.
- **Scope boundary** 의 list 는 parent plan 의 Constraints 와 일관. parent 의 변경 금지 영역을 task 별로 reuse 하되 *본 task 와 다른 task 의 영역* 이 명확히 구분되어야 함.
- **`status: pending`** 으로 시작. Sonnet 이 진행하면서 `in_progress` → `done` 으로 전환.
- **`depends_on: []`** 는 빈 list 로 명시. 빈 list 와 키 omit 은 다른 의미 — omit 금지.
