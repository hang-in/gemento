---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: sampling-params-config-exp10
parallel_group: C
depends_on: [01, 02, 03]
---

# Task 04 — 정합성 정적 테스트 추가

## Changed files

- `experiments/tests/test_static.py` — **수정**. 파일 끝 (현재 `if __name__ == "__main__":` 블록 직전) 에 `TestSamplingParamsCentralization` 클래스 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

task-01·02·03 의 변경이 누적되어도, 향후 누군가 다시 `temperature=0.1` 을 호출 지점에 하드코딩하면 일원화가 깨질 수 있다. 본 task 는 이를 정적 검증으로 강제하는 테스트를 추가한다.

### 검증 항목

1. **(존재)** `from config import SAMPLING_PARAMS` 통과 + 4 필드 (`temperature`, `max_tokens`, `top_p`, `seed`) 모두 존재.
2. **(값)** `temperature=0.1`, `max_tokens=4096`, `top_p=None`, `seed=None` — 결과 동일성 보장.
3. **(참조)** `experiments/orchestrator.py` 와 `experiments/_external/lmstudio_client.py` 둘 다 `SAMPLING_PARAMS` 문자열 참조.
4. **(magic number 부재)** 두 파일에 `"temperature": 0.1` 또는 `"max_tokens": 4096` 같은 정규식 매칭 0건 (직접 하드코딩 차단).

### Step 1 — TestSamplingParamsCentralization 클래스 추가

`experiments/tests/test_static.py` 의 마지막 클래스 (`TestRunExperimentSlim`) 다음, `if __name__ == "__main__":` 블록 직전에 추가:

```python
class TestSamplingParamsCentralization(unittest.TestCase):
    """sampling-params-config-exp10 plan — config.py SAMPLING_PARAMS 일원화 검증.

    - SAMPLING_PARAMS 가 config.py 에 정의되고 4 필드 존재
    - orchestrator.py·lmstudio_client.py 가 모두 SAMPLING_PARAMS 참조
    - 두 파일 본문에 sampling literal 직접 하드코딩 0건
    """

    EXPECTED_FIELDS = {"temperature", "max_tokens", "top_p", "seed"}
    EXPECTED_VALUES = {"temperature": 0.1, "max_tokens": 4096, "top_p": None, "seed": None}

    def test_sampling_params_exists_with_expected_fields(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from config import SAMPLING_PARAMS
            self.assertEqual(set(SAMPLING_PARAMS.keys()), self.EXPECTED_FIELDS)
            for k, v in self.EXPECTED_VALUES.items():
                self.assertEqual(SAMPLING_PARAMS[k], v,
                                 f"SAMPLING_PARAMS[{k!r}] expected {v}, got {SAMPLING_PARAMS[k]}")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_orchestrator_references_sampling_params(self):
        text = (EXPERIMENTS_DIR / "orchestrator.py").read_text(encoding="utf-8")
        self.assertIn("SAMPLING_PARAMS", text,
                      "orchestrator.py must reference SAMPLING_PARAMS")

    def test_lmstudio_client_references_sampling_params(self):
        text = (EXPERIMENTS_DIR / "_external" / "lmstudio_client.py").read_text(encoding="utf-8")
        self.assertIn("SAMPLING_PARAMS", text,
                      "lmstudio_client.py must reference SAMPLING_PARAMS")

    def test_no_hardcoded_sampling_literals(self):
        """orchestrator.py·lmstudio_client.py 본문에 sampling 키:리터럴 직접 매핑 금지."""
        targets = [
            EXPERIMENTS_DIR / "orchestrator.py",
            EXPERIMENTS_DIR / "_external" / "lmstudio_client.py",
        ]
        # "temperature": 0.1 또는 "max_tokens": 4096 같은 직접 매핑
        pattern = re.compile(r'"(temperature|max_tokens|top_p|seed)"\s*:\s*[0-9]')
        for path in targets:
            text = path.read_text(encoding="utf-8")
            matches = pattern.findall(text)
            self.assertEqual(matches, [],
                             f"{path.name} has hardcoded sampling literals: {matches}")
```

본 클래스는 `re` 와 `sys` 모듈을 사용하나 파일 상단에서 이미 import 됨 (existing test_static.py 확인됨).

### Step 2 — 다른 테스트 클래스 미수정

기존 `TestImportInfra`, `TestDispatcherIntegrity`, `TestResultFileInventory` 등 9 클래스는 그대로 유지. 본 task 는 새 클래스 1 개 추가만.

## Dependencies

- **task-01 완료** — `SAMPLING_PARAMS` import 가능해야 함.
- **task-02 완료** — orchestrator.py 가 SAMPLING_PARAMS 참조해야 test 통과.
- **task-03 완료** — lmstudio_client.py 가 SAMPLING_PARAMS 참조해야 test 통과.
- 외부 패키지: 없음 (stdlib `re`, `sys`, `unittest`, `pathlib` 만 사용 — 기존 import).

## Verification

```bash
# 1. test_static.py 모두 PASS — 기존 20 + 신규 4 tests = 24+ tests OK
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -15
# 기대: "Ran 24 tests" + "OK"

# 2. TestSamplingParamsCentralization 의 4 method 모두 통과 — 개별 실행
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static.TestSamplingParamsCentralization -v 2>&1 | tail -10
# 기대: "Ran 4 tests" + "OK"

# 3. test_static.py 라인 수 — 기존 269 → ~310 (40 줄 추가)
wc -l /Users/d9ng/privateProject/gemento/experiments/tests/test_static.py

# 4. 기존 클래스 수 9 → 10
cd /Users/d9ng/privateProject/gemento/experiments && grep -cE "^class Test" tests/test_static.py
# 기대: 10

# 5. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/(config\.py|orchestrator\.py|_external/lmstudio_client\.py|tests/test_static\.py)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **regex false positive**: pattern `"(temperature|max_tokens|top_p|seed)"\s*:\s*[0-9]` 가 우연 매칭 가능 (예: 주석 안 `"temperature": 0.5` 예시 텍스트). 본 paterrn 은 실제 코드 의도 매칭에 충분히 보수적. 발생 시 task 보강 (rework).
- **기존 테스트 위치 충돌**: `test_static.py` 의 마지막 클래스 다음 `if __name__ == "__main__":` 직전 삽입 — 만약 여러 trailing 라인 있으면 정확한 위치 찾기 필요. Developer 가 직접 read 후 삽입.
- **import 의존성**: 신규 테스트가 `re` 사용. test_static.py:8 에 이미 `import re` 있음 (검증됨).
- **EXPERIMENTS_DIR 사용**: 기존 클래스들이 module-level 변수 `EXPERIMENTS_DIR` 사용. 본 신규 클래스도 동일 변수 사용. 이미 line 13 에 정의됨 (검증됨).

## Scope boundary

**Task 04 에서 절대 수정 금지**:

- `experiments/config.py` — task-01 결과물 그대로.
- `experiments/orchestrator.py` — task-02 결과물 그대로.
- `experiments/_external/lmstudio_client.py` — task-03 결과물 그대로.
- `experiments/_external/gemini_client.py`, `__init__.py` — 본 plan 범위 밖.
- `experiments/tests/test_static.py` 의 기존 9 클래스 (`TestImportInfra` ~ `TestRunExperimentSlim`).
- `docs/reference/researchNotebook.md` — task-05 영역.
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/tests/test_static.py` 마지막 클래스 다음 `if __name__ == "__main__":` 직전에 `TestSamplingParamsCentralization` 클래스 (~40 줄) 추가.
