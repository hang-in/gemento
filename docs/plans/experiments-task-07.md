---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: experiments
parallel_group: D
depends_on: [06]
---

# Task 07 — dispatcher 슬림화 + 인덱스 완성

## Changed files

- `experiments/run_experiment.py` — **수정**. 본문 슬림화 (이상적 ≤ 100라인): 상단 14개 import + EXPERIMENTS dict (13개) + main() (argparse + dispatcher 호출) 만. 잔여 헬퍼 함수가 있다면 별도 모듈 분리 또는 그대로 보존 결정.
- `experiments/INDEX.md` — **수정**. task-01 의 골격에서 13 active 행 + 1 archived 행 모두 채움. 메트릭 placeholder 포함.
- `experiments/exp*/INDEX.md` × 13 — **수정**. 본 task에서 메트릭 표·하이퍼파라미터·인용 가능 결과 채움 (task-03~06이 placeholder만 남겼으면).
- `experiments/_archived/exp04_tool_separation_deprecated/INDEX.md` — **수정** (필요 시 보강).
- `experiments/tests/test_static.py` — **수정**. `TestRunExperimentSlim` TestCase 추가 — `run_experiment.py` 의 라인 수·함수 정의 갯수 한계 검증.
- `experiments/_template/` — **삭제** (작업 완료 후 정리). 향후 신규 실험 추가 시 기존 INDEX.md 복사하면 충분.

신규 외 다른 파일 수정 금지. 본 task는 코드 추가/이동이 아닌 **정리·완성** 단계.

## Change description

### Step 1 — `experiments/run_experiment.py` 슬림화 검토

task-06 종료 시점에서 `run_experiment.py` 는 다음 영역으로 구성:
- 상단 import (~30줄) — 14개 실험 모듈 + 공용 (json, argparse 등)
- (가능) 잔여 헬퍼 함수 — task-03~06 에서 옮기지 않은 공용 함수
- `EXPERIMENTS = {...}` (~16줄) — 13개 키
- `def main():` 와 argparse (~15줄)
- `if __name__ == "__main__": main()` (1줄)

**잔여 헬퍼 함수 처리 결정**:

| 시나리오 | 처리 |
|----------|------|
| 헬퍼 0개 | 그대로 슬림. |
| 헬퍼 1-2개, 단순 (e.g. `_print_summary`) | 그대로 dispatcher 모듈에 보존. |
| 헬퍼 3개 이상 또는 복잡 | `experiments/_helpers.py` 로 분리. 단 본 plan 범위 밖일 수 있음 — 필요 시 후속 plan 으로. |

본 task 작업자는 task-06 종료 시점의 잔여 함수 수를 grep 으로 확인:

```bash
grep -n "^def " experiments/run_experiment.py
```

결과에 따라 (1) 그대로 두기 (2) 별도 plan 으로 미루기 결정. **본 task 범위에서는 `_helpers.py` 분리는 안 하는 것을 권장** — 본 plan이 "순수 이동" 원칙이므로 새 모듈 추가는 scope 위반.

### Step 2 — `run_experiment.py` 의 main() 검증

argparse 가 `EXPERIMENTS.keys()` 로 choices 를 동적 생성하는지 확인. task-05 에서 dispatcher key 가 13개로 줄어들었으므로 main() 코드가 키 셋 변화에 자동 대응해야.

만약 main() 가 하드코딩된 choices list 를 사용한다면 갱신 필요:

```python
# Before (가정)
parser.add_argument("experiment", choices=["baseline", "assertion-cap", ..., "tool-separation", ...])

# After (권장)
parser.add_argument("experiment", choices=list(EXPERIMENTS.keys()))
```

이미 동적 생성을 사용 중이라면 변경 0.

### Step 3 — `experiments/INDEX.md` 완성

task-01의 표 헤더만 있는 골격을 채운다. 각 실험 1행, 13 active + 1 archived = 14행.

```markdown
# Experiments — Index

이 디렉토리는 gemento 프로젝트의 모든 실험을 단위로 관리한다. 각 실험은
독립 디렉토리(`expXX_<slug>/`)로 구성되며 `run.py` (실행 함수), `results/`
(결과 JSON·리포트), `INDEX.md` (개요) 를 보유한다.

## 실험 목록 (13 active + 1 archived)

| # | 디렉토리 | dispatcher key | 핵심 가설/메모 | 결과 |
|---|---------|---------------|----------------|------|
| 00 | [exp00_baseline](exp00_baseline/INDEX.md) | `baseline` | 기준선 (Tattoo·ABC 없음) | 3 trials |
| 01 | [exp01_assertion_cap](exp01_assertion_cap/INDEX.md) | `assertion-cap` | Assertion 상한 효과 | 7 partial+1 final |
| 02 | [exp02_multiloop](exp02_multiloop/INDEX.md) | `multiloop` | H1 — 다단계 루프 품질 누적 | 2 trials + report |
| 03 | [exp03_error_propagation](exp03_error_propagation/INDEX.md) | `error-propagation` | H2 — 오류 전파·자기 교정 | 1 trial |
| 03.5 | [exp035_cross_validation](exp035_cross_validation/INDEX.md) | `cross-validation` | 교차 검증 sanity | 1 trial |
| 04 | [exp04_abc_pipeline](exp04_abc_pipeline/INDEX.md) | `abc-pipeline` | A-B-C 직렬 통합 | 1 trial |
| 05a | [exp05a_prompt_enhance](exp05a_prompt_enhance/INDEX.md) | `prompt-enhance` | 프롬프트 강화 | 1 trial (synthesis-02 None 실패) |
| 04.5 | [exp045_handoff_protocol](exp045_handoff_protocol/INDEX.md) | `handoff-protocol` | A→B, B→C 핸드오프 v2 | 3 trials |
| 06 | [exp06_solo_budget](exp06_solo_budget/INDEX.md) | `solo-budget` | Solo vs ABC 토큰 예산 | 1 trial |
| 07 | [exp07_loop_saturation](exp07_loop_saturation/INDEX.md) | `loop-saturation` | Loop 포화점 (2×4 요인) | 1 trial + report |
| 08 | [exp08_tool_use](exp08_tool_use/INDEX.md) | `tool-use` | H7 — Calculator/Linalg/LP 도구 | 1 trial + report |
| 08b | [exp08b_tool_use_refined](exp08b_tool_use_refined/INDEX.md) | `tool-use-refined` | H8 — 도구 에러+프롬프트 강화 | 1 trial + report (math-04 100%) |
| 09 | [exp09_longctx](exp09_longctx/INDEX.md) | `longctx` | H9 — Long-Context Stress | 1 trial + report (3-hop 100%) |
| (deprecated) | [_archived/exp04_tool_separation_deprecated](_archived/exp04_tool_separation_deprecated/INDEX.md) | (제거됨) | 구 도구 분리 — abc-pipeline 으로 대체 | 0 trials |

## 디렉토리 구조 표준

각 활성 실험 디렉토리는 다음 파일을 가진다:

- `run.py` — `def run():` 실행 함수.
- `INDEX.md` — 실험 개요, 하이퍼파라미터, 메트릭, 결과 파일 링크.
- `results/` — 해당 실험의 모든 JSON·report.md.
- `__init__.py` — 빈 패키지 표지.

## 검증

오프라인 정적 검증 (LLM 호출 0):

```
cd experiments
../.venv/bin/python -m unittest tests.test_static -v
```

기대: 23+ tests, all OK.

실증(LLM) 검증은 사용자 환경에서 별도 진행. 본 디렉토리 검증 가이드는
LLM 호출을 동반하지 않는다.
```

### Step 4 — 각 `experiments/exp*/INDEX.md` 의 메트릭·하이퍼파라미터 채움

task-03~06 에서 placeholder 만 남겼던 부분을 채운다. 각 INDEX.md 는:
- 개요 (1-2문단)
- dispatcher key
- 하이퍼파라미터 (max_cycles, repeat 등)
- 결과 파일 링크
- 핵심 메트릭 표

메트릭은 결과 JSON 을 직접 분석하기보다, 가능한 경우 **abandoned 처리된 plan 문서들** (예: `docs/plans/exp08b-tool-use-refinement-prompt.md`) 또는 **report.md** 에서 추출. 추출 가능한 데이터가 명확하지 않으면 placeholder 유지 (`(분석 보류)`).

본 task 작업자는 13개 INDEX.md 모두 점검하고, **최소** 다음 항목이 채워졌는지 확인:
- `# 실험 NN: 제목`
- `dispatcher key`
- 결과 파일 절대 링크
- (선택) 메트릭 placeholder 또는 실제 값

### Step 5 — `_archived/.../INDEX.md` 보강

task-05 에서 작성된 `_archived/exp04_tool_separation_deprecated/INDEX.md` 의 deprecated 사유, 격리 일자, 격리 전후 위치 명시 확인. 부족하면 보강.

### Step 6 — `tests/test_static.py` 의 `TestRunExperimentSlim` 신규

```python
class TestRunExperimentSlim(unittest.TestCase):
    """task-07 — run_experiment.py 가 dispatcher 모듈 수준으로 슬림"""

    MAX_LINES = 200  # 14 import + EXPERIMENTS dict + main + helper(소수) 가정. 보수적 한계.

    def test_run_experiment_slim(self):
        run_exp = EXPERIMENTS_DIR / "run_experiment.py"
        lines = run_exp.read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), self.MAX_LINES,
                        f"run_experiment.py has {len(lines)} lines, expected < {self.MAX_LINES}")

    def test_run_experiment_no_legacy_run_funcs(self):
        # task-06 의 TestNoLegacyRunFunctions 와 중복 보호용
        run_exp = EXPERIMENTS_DIR / "run_experiment.py"
        text = run_exp.read_text(encoding="utf-8")
        legacy = re.findall(r"^def run_\w+\s*\(", text, flags=re.M)
        self.assertEqual(legacy, [])

    def test_dispatcher_keys_match_split_experiments(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            import run_experiment
            from tests.test_static import TestPerExperimentImports as TPEI
            split_keys = {exp_dir for exp_dir, _, _ in TPEI.SPLIT_EXPERIMENTS}
            # 13 active dispatcher 키와 13 split 디렉토리가 1:1 (이름 다름 — slug)
            # 매핑은 EXPERIMENTS dict 의 value 가 어느 모듈에서 왔는지 확인하는 게 정확
            for k, v in run_experiment.EXPERIMENTS.items():
                module_name = v.__module__  # e.g. "exp00_baseline.run"
                top_dir = module_name.split(".")[0]
                self.assertIn(top_dir, split_keys,
                              f"dispatcher[{k}] from unknown module {module_name}")
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))
```

### Step 7 — `experiments/_template/` 삭제

task-01 에서 만든 템플릿 디렉토리는 본 task 완료 후 더 이상 필요 없음 (모든 실험이 분리 완료, 신규 실험 추가 시 기존 INDEX.md 를 복사하면 충분).

```bash
git rm -r experiments/_template/
```

## Dependencies

- **Task 06 완료** — 모든 14개 함수 분리 완료, `run_experiment.py` 본문에 `^def run_` 0건.
- 외부 패키지: 없음.

## Verification

```bash
# 1. run_experiment.py 가 < 200 라인
wc -l experiments/run_experiment.py | awk '{print $1}'
# 기대: < 200

# 2. EXPERIMENTS dict 가 13개 키
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
assert len(run_experiment.EXPERIMENTS) == 13, f'expected 13, got {len(run_experiment.EXPERIMENTS)}'
print('OK 13 dispatcher keys')
"

# 3. 모든 dispatcher value 가 expXX_*.run 모듈에서 옴
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_experiment
for k, v in run_experiment.EXPERIMENTS.items():
    mod = v.__module__
    assert mod.startswith('exp') and mod.endswith('.run'), \
        f'dispatcher[{k}] from unexpected module {mod}'
print('OK all dispatcher values from exp*.run modules')
"

# 4. INDEX.md 표가 13 active + 1 archived 모두 포함
grep -c "^| " experiments/INDEX.md
# 기대: ≥ 14 (헤더 + 14 행)
grep -q "exp00_baseline" experiments/INDEX.md && \
grep -q "exp09_longctx" experiments/INDEX.md && \
grep -q "_archived/exp04_tool_separation_deprecated" experiments/INDEX.md && \
echo "OK INDEX has all 14 entries"

# 5. INDEX.md 의 모든 [link](path/INDEX.md) 가 실재
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import re
from pathlib import Path
text = Path('INDEX.md').read_text()
broken = []
for m in re.finditer(r'\[([^\]]+)\]\(([^)]+\.md)\)', text):
    link = m.group(2)
    if link.startswith('http'):
        continue
    target = Path(link).resolve()
    if not target.exists():
        broken.append(link)
assert not broken, f'broken links: {broken}'
print('OK all INDEX.md links resolve')
"

# 6. test_static.py 모든 PASS — 본 task 후 23 + 3 = 26 tests
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest tests.test_static -v 2>&1 | tail -10
# 기대: "Ran 26 tests" + "OK"

# 7. _template 디렉토리 삭제 확인
test ! -d experiments/_template && echo "OK _template removed"

# 8. 13개 active INDEX.md 모두 dispatcher key 명시
for d in exp00_baseline exp01_assertion_cap exp02_multiloop exp03_error_propagation \
         exp035_cross_validation exp04_abc_pipeline exp05a_prompt_enhance \
         exp045_handoff_protocol exp06_solo_budget \
         exp07_loop_saturation exp08_tool_use exp08b_tool_use_refined exp09_longctx; do
  grep -q "dispatcher key" experiments/$d/INDEX.md || { echo "FAIL $d: missing dispatcher key"; exit 1; }
done && echo "OK 13 INDEX.md have dispatcher key"

# 9. CLI choices 13개
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_experiment.py --help 2>&1 | grep -A1 "experiment" | head -5

# 10. _archived/ INDEX.md 가 deprecated 사유·격리 일자 포함
grep -q "deprecated" experiments/_archived/exp04_tool_separation_deprecated/INDEX.md && \
grep -q "2026-04-25" experiments/_archived/exp04_tool_separation_deprecated/INDEX.md && \
echo "OK _archived INDEX has deprecation context"

# 11. unittest discover 로 모든 정적 테스트 발견
cd experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest discover -s tests -v 2>&1 | tail -5
# 기대: 26 tests, all OK
```

## Risks

- **잔여 헬퍼 함수 처리**: task-06 후 잔여 함수 수에 따라 본 task 결정 변경. 신규 모듈 분리는 scope 위반이라 본 task에서 안 함. 헬퍼가 너무 많으면 별도 plan 으로 미룸.
- **MAX_LINES 의 임의성**: 200라인 한계는 보수적 추정. 실제 task-06 종료 후 라인 수 보고 조정 가능. 너무 큰 한계 (e.g. 500) 는 의미 약화. 본 task 작업자는 실제 라인 수를 보고 한계를 100~250 사이로 결정.
- **메트릭 placeholder 유지**: 본 task 시간 한도상 13개 INDEX.md 의 메트릭을 모두 분석 못 할 수 있음. placeholder 유지 OK — 향후 plan 에서 메트릭 추출. Verification 8번은 dispatcher key 만 검증, 메트릭 강제 안 함.
- **`EXPERIMENTS_DIR` import 경로**: task-07 이 `_template/` 삭제 시 `experiments/__init__.py` 가 영향 받지 않는지 확인. `__init__.py` 는 task-03 에서 추가, 본 task에서는 손대지 않음.
- **graph data 영향**: `run_experiment.py` 가 슬림화되면서 의존 그래프에 변화. 단 dispatcher 매핑은 보존되므로 기능 변화 0.
- **CLI 호환성**: `python run_experiment.py tool-separation` 호출은 task-05에서 이미 KeyError. 본 task에서는 변화 없음. 외부 script 가 이 키를 호출하면 깨짐 — README 또는 INDEX 에 명시.

## Scope boundary

**Task 07에서 절대 수정 금지**:

- `experiments/exp*/run.py` — 14개 모두 task-03~06 결과물 그대로.
- `experiments/_archived/exp04_tool_separation_deprecated/run.py` — task-05 영역.
- 공용 모듈 (`orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`, `experiment_logger.py`, `config.py`).
- `experiments/results/` — 이미 task-02 에서 폐지됨.
- `experiments/tools/`, `experiments/tasks/`.
- `docs/plans/*` — 본 task 외 plan 문서.

**허용 범위**:

- `experiments/run_experiment.py` 의 dispatcher dict, main, argparse, 상단 import 영역 정리.
- `experiments/INDEX.md` 갱신 (13 active + 1 archived 표 채움).
- `experiments/exp*/INDEX.md` × 13 메트릭·하이퍼파라미터 채움.
- `experiments/_archived/exp04_tool_separation_deprecated/INDEX.md` 보강.
- `experiments/tests/test_static.py` 에 `TestRunExperimentSlim` 신규.
- `experiments/_template/` 삭제.
