---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: A
depends_on: []
---

# Task 01 — v3 채점기 설계 + 구현

## Changed files

- `experiments/measure.py` — **수정**. `score_answer_v2` (line 45) 다음에 `score_answer_v3` 함수 신규. 모듈 상단의 `import re` 그대로 활용 (이미 line 1 에서 import 됨).
- `experiments/tests/test_static.py` — **수정**. `TestScoreAnswerV3` 클래스 신규. 기존 `TestExp10DebugLoggingSchema` 패턴 따라감. LLM 호출 0.

신규 파일 0.

## Change description

### 배경

`experiments/measure.py:score_answer_v2` (line 45-62) 의 채점은:

```python
matched = sum(
    1 for group in keywords
    if all(token.lower() in response_lower for token in group)
)
return matched / len(keywords)
```

→ substring contains. 모델이 "Casey 가 정답이라고 가정하면 모순이다" 라고 결론냈어도 'casey' 라는 단어가 등장하기만 해서 1.0 부여됨.

logic-04 60 trial 의 false positive 패턴 분석 결과:
- `r"no\s+(unique|definitive|clear)\s+(culprit|answer|solution)"`
- `r"cannot\s+be\s+(identified|determined|solved)"`
- `r"contradicts?|contradiction|contradictions"`
- `r"puzzle\s+is\s+(flawed|inconsistent|ill-?posed)"`

이 정규식 4개로 9건 mismatch + 3건 ambiguous 를 모두 분류 가능 (Architect 측 사전 점검 완료).

### Step 1 — `score_answer_v3` 함수 추가

`experiments/measure.py:score_answer_v2` 함수 (line 45-62) 다음에 추가:

```python
def score_answer_v3(response: str, task_entry: dict) -> float:
    """
    v3 채점: v2 keyword-group 매칭에 negative_patterns + conclusion_required 옵션 결합.

    정책 (순서대로 평가):
    1. response 가 비어 있으면 0.0.
    2. task_entry 의 옵션 `negative_patterns: list[str]` (정규식, IGNORECASE) 중
       하나라도 response 전체에서 매칭되면 0.0 강제.
       → 모델이 "no solution / contradiction" 류 결론을 낸 경우 차단.
    3. task_entry 의 옵션 `conclusion_required: list[str]` (정규식, IGNORECASE) 가
       있으면 response 끝 200 char 안에 그 정규식 중 하나가 매칭돼야 함. 매칭 안 되면 0.0.
       → 핵심 결론이 본문 결론부에 있어야 정답.
    4. 위 두 차단을 통과하면 v2 채점 위임 (score_answer_v2).

    옵션 필드가 없는 task 는 v2 와 동일 결과.
    """
    if not response:
        return 0.0

    negative_patterns = task_entry.get("negative_patterns") or []
    for pat in negative_patterns:
        if re.search(pat, response, re.IGNORECASE):
            return 0.0

    conclusion_required = task_entry.get("conclusion_required") or []
    if conclusion_required:
        tail = response[-200:] if len(response) > 200 else response
        if not any(
            re.search(pat, tail, re.IGNORECASE)
            for pat in conclusion_required
        ):
            return 0.0

    return score_answer_v2(response, task_entry)
```

### Step 2 — `experiments/tests/test_static.py` 에 단위 테스트

기존 `TestExp10DebugLoggingSchema` 클래스 옆에 추가:

```python
class TestScoreAnswerV3:
    """score_answer_v3 의 negative_patterns 차단 + conclusion_required 검증."""

    def setup_method(self):
        # logic-04 와 동일 구조의 task_entry fixture
        self.task = {
            "id": "logic-04-mock",
            "scoring_keywords": [["casey"]],
            "negative_patterns": [
                r"no\s+(unique|definitive|clear)\s+(culprit|answer|solution)",
                r"cannot\s+be\s+(identified|determined|solved)",
                r"contradicts?|contradiction|contradictions",
                r"puzzle\s+is\s+(flawed|inconsistent|ill-?posed)",
            ],
        }

    def test_v2_match_no_negative(self):
        from experiments.measure import score_answer_v3
        response = "Casey committed the crime. The other three are innocent."
        assert score_answer_v3(response, self.task) == 1.0

    def test_negative_pattern_blocks_substring_match(self):
        from experiments.measure import score_answer_v3
        # 'casey' 등장하지만 결론은 contradiction
        response = (
            "Assuming Casey is guilty leads to a contradiction. "
            "All four suspects lead to similar contradictions, so the puzzle is inconsistent."
        )
        assert score_answer_v3(response, self.task) == 0.0

    def test_no_keyword_returns_zero(self):
        from experiments.measure import score_answer_v3
        response = "Dana committed the crime."
        assert score_answer_v3(response, self.task) == 0.0

    def test_empty_response(self):
        from experiments.measure import score_answer_v3
        assert score_answer_v3("", self.task) == 0.0
        assert score_answer_v3(None, self.task) == 0.0  # type: ignore[arg-type]

    def test_no_negative_patterns_falls_back_to_v2(self):
        from experiments.measure import score_answer_v3
        task = {"id": "x", "scoring_keywords": [["casey"]]}
        response = "Casey did it."
        assert score_answer_v3(response, task) == 1.0

    def test_conclusion_required_match_at_tail(self):
        from experiments.measure import score_answer_v3
        task = {
            "id": "x",
            "scoring_keywords": [["casey"]],
            "conclusion_required": [r"casey\s+(committed|is\s+(the|guilty))"],
        }
        # 본문 어디든 casey 들어가지만 결론부에 정답 명시
        response = (
            "After analysis of all suspects, the conclusion is that Casey committed the crime."
        )
        assert score_answer_v3(response, task) == 1.0

    def test_conclusion_required_miss_at_tail(self):
        from experiments.measure import score_answer_v3
        task = {
            "id": "x",
            "scoring_keywords": [["casey"]],
            "conclusion_required": [r"casey\s+(committed|is\s+(the|guilty))"],
        }
        # 본문 시작에서만 casey 등장하고 결론은 다른 내용
        response = (
            "Casey was one of the suspects. After analysis, no clear answer can be derived."
            + (" filler." * 30)
        )
        assert score_answer_v3(response, task) == 0.0
```

## Dependencies

- 패키지: 표준 라이브러리 `re` 만 사용 (이미 import). 신규 의존성 0.
- 다른 subtask: 없음. 본 task 가 plan 의 시작점.

## Verification

```bash
# 1) 정적 import 통과
.venv/bin/python -c "from experiments.measure import score_answer_v3; print('ok')"

# 2) 신규 단위 테스트 통과
.venv/bin/python -m pytest experiments/tests/test_static.py::TestScoreAnswerV3 -v

# 3) 기존 정적 테스트 회귀 없음
.venv/bin/python -m pytest experiments/tests/test_static.py -v
```

세 명령 모두 exit 0 + pytest 모두 PASSED.

## Risks

- **`re.search` 의 비탐욕 매칭**: `r"contradicts?"` 같은 패턴은 단어 경계 처리 안 하면 "contradistinguish" 같은 단어에서 false hit. 본 plan 의 negative_patterns 는 모두 `\b` 경계 명시 또는 정확한 단어 매칭으로 충분. test 에서 false positive 케이스 검증.
- **conclusion_required 의 200 char tail**: 응답 끝이 짧은 경우 (200 char 미만) 전체 응답 검사. 매우 긴 응답에서 결론이 더 앞에 있는 경우 누락 가능 — 본 plan 은 logic-04 에 conclusion_required 미사용 (negative_patterns 만), 옵션 필드는 future-proofing.
- **score_answer_v2 의 fallback 호환**: `scoring_keywords` 없는 task 는 v2 가 v1 (`score_answer`) 로 fallback. v3 도 동일 동작 — 별도 처리 불필요.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` 의 `score_answer` (line 24) / `score_answer_v2` (line 45) — 기존 함수 그대로 유지. 신규 함수만 추가.
- `experiments/tasks/taskset.json` — Task 02 영역.
- `experiments/orchestrator.py` — Task 04/05 영역.
- 다른 analyze_* 함수 (line 67+) — score_answer_v2 호출 그대로 두고, v3 적용은 Task 03 의 별도 rescore 스크립트에서 처리.
