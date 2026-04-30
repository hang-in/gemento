---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: phase-1-v2-exp09
task_number: 2
title: "taskset expected_answer 전수 검증"
depends_on: []
parallel_group: A
---

# Task 02: taskset expected_answer 전수 검증

## Changed files

- `experiments/validate_taskset.py` — **신규 생성**
- `experiments/validate_taskset_results/` — **신규 디렉토리** (검증 결과 저장)

## Change description

### 2.1 목적

math-04 사례(material 제약 위반, commit `6c6f198`에서 정정)를 계기로, 전체 12개 기본 태스크 + 10개 longctx 태스크의 expected_answer를 자동 검증하는 스크립트를 구축한다.

### 2.2 검증 전략 (카테고리별)

**Math 카테고리 (math-01 ~ math-04)**

| task_id | 검증 방법 |
|---------|----------|
| math-01 | sympy: 연립방정식 (apples + oranges = 20, 500a + 300o = 8600) |
| math-02 | sympy: 기하 계산 (넓이) |
| math-03 | sympy: 연립방정식 (round + square + rectangular = 15, 조건 3개) |
| math-04 | scipy.optimize.linprog: LP (목적함수 max profit, 2 제약 + 하한) |

각 math task에 대해:
1. 문제의 수학적 구조를 스크립트 안에 하드코딩 (task별 검증 함수)
2. 풀이 결과와 `expected_answer`의 핵심 수치 비교
3. PASS/FAIL + 계산 결과 출력

**Logic 카테고리 (logic-01 ~ logic-04)**

수학적 자동 검증 불가. 대안:
1. `scoring_keywords` ↔ `expected_answer` 일관성 체크: keywords의 모든 토큰이 expected_answer에 포함되는지
2. `negative_patterns` (있을 경우) 가 expected_answer 자체에 매칭되지 않는지 확인 (자기 모순 방지)
3. 결과: CONSISTENT / INCONSISTENT

**Synthesis 카테고리 (synthesis-01 ~ synthesis-04)**

Logic과 동일한 일관성 체크 적용.

**Longctx 카테고리 (longctx-small-needle-01 ~ longctx-large-3hop-01)**

1. `scoring_keywords` ↔ `expected_answer` 일관성 체크
2. `gold_evidence_text`에 expected_answer의 핵심 토큰이 포함되는지 확인

### 2.3 출력 형식

```
═══════════════════════════════════════════
  Taskset Validation Report
═══════════════════════════════════════════
  task_id           category    method         result    detail
  ─────────────────────────────────────────────────────────
  math-01           math        sympy_solve    PASS      13 apples, 7 oranges ✓
  math-02           math        sympy_geom     PASS      192 sq meters ✓
  math-03           math        sympy_solve    PASS      round=6, square=4, rect=5 ✓
  math-04           math        scipy_linprog  PASS      X=31, Y=10, Z=37, $3060 ✓
  logic-01          logic       consistency    PASS      keywords ⊂ expected ✓
  ...
  longctx-small-needle-01  longctx  consistency  PASS   keywords ⊂ expected ✓
  ...
═══════════════════════════════════════════
  Summary: 22 PASS / 0 FAIL / 0 SKIP
═══════════════════════════════════════════
```

JSON 저장: `experiments/validate_taskset_results/validation_<timestamp>.json`

### 2.4 코드 구조

```
experiments/validate_taskset.py
├── _validate_math_01() → dict(result, detail)
├── _validate_math_02() → dict
├── _validate_math_03() → dict
├── _validate_math_04() → dict  # scipy.optimize.linprog 사용
├── _validate_consistency(task_entry) → dict  # keywords ↔ expected_answer
├── _validate_longctx_consistency(task_entry) → dict
├── _print_report(results)
└── main()
```

### 2.5 의존성 주의

- `sympy`: 수학 검증에 필요. 프로젝트 .venv에 미설치 가능 — 스크립트 시작 시 import 실패 시 해당 math task를 SKIP 처리하고 경고 출력.
- `scipy`: math-04 LP 검증에 필요. 이미 프로젝트에 scipy 의존 있음 (`experiments/` 내 사용 확인).
- 둘 다 없으면 math 카테고리만 SKIP, 나머지 consistency 검증은 표준 라이브러리로 진행.

## Dependencies

- Python 패키지: `sympy` (선택), `scipy` (선택 — math-04 검증)
- 다른 subtask: 없음 (parallel_group A)

## Verification

```bash
# 1. 스크립트 실행
python -m experiments.validate_taskset 2>&1 | tail -5
# 기대: "Summary: N PASS / 0 FAIL" 포함, VALIDATION COMPLETE

# 2. math-04 검증 결과 확인 (scipy 가용 시)
python -c "
import json, glob
files = sorted(glob.glob('experiments/validate_taskset_results/validation_*.json'))
if not files:
    print('No result file'); exit(1)
d = json.load(open(files[-1]))
m04 = [t for t in d.get('results', []) if t.get('task_id') == 'math-04']
if m04:
    print(f'math-04: {m04[0][\"result\"]}')
    assert m04[0]['result'] in ('PASS', 'SKIP'), 'math-04 should PASS or SKIP'
print('OK')
"
# 기대: math-04: PASS, OK

# 3. 기본 taskset 전체 FAIL 없음 확인
python -c "
import json, glob
files = sorted(glob.glob('experiments/validate_taskset_results/validation_*.json'))
d = json.load(open(files[-1]))
fails = [t for t in d.get('results', []) if t.get('result') == 'FAIL']
print(f'Failures: {len(fails)}')
assert len(fails) == 0, f'Unexpected failures: {fails}'
print('OK')
"
# 기대: Failures: 0, OK

# 4. 문법 체크
python -c "import ast; ast.parse(open('experiments/validate_taskset.py').read()); print('Syntax OK')"
# 기대: Syntax OK
```

## Risks

- **sympy 미설치**: .venv에 sympy가 없을 수 있음. graceful skip으로 대응.
- **math-03 특수성**: "round, square, rectangular" 문제의 수학적 모델링이 prompt 텍스트 해석에 의존. 검증 함수의 수식이 prompt와 정확히 일치하는지 수동 대조 필요.
- **longctx 태스크 gold_evidence_text**: 일부 태스크에서 gold_evidence_text가 부분 인용이라 expected_answer 토큰이 포함되지 않을 수 있음 — WARN으로 처리, FAIL 아님.
- **false confidence**: 이 스크립트가 "수학적으로 맞다"고 보고해도 prompt 자체가 모호하면 답이 달라질 수 있음. 스크립트는 특정 수학 모델 하에서의 정합성만 보장.

## Scope boundary

수정 금지 파일:
- `experiments/tasks/taskset.json` — 읽기만 허용 (FAIL 발견 시 Task 5에서 정정 논의)
- `experiments/tasks/longctx_taskset.json` — 읽기만 허용
- `experiments/measure.py` — 이 task에서 사용하지 않음
- `docs/reference/researchNotebook.md` — Task 5 영역
