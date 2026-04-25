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

공용 모듈(`orchestrator.py`, `schema.py`, `system_prompt.py`, `measure.py`,
`experiment_logger.py`, `config.py`, `tools/`, `tasks/`)는 `experiments/` 최상위에
유지. 모든 실험이 import 한다.

## 검증

오프라인 정적 검증 (LLM 호출 0):

```
cd experiments
../.venv/bin/python -m unittest tests.test_static -v
```

기대: 18+ tests, all OK.

실증(LLM) 검증은 사용자 환경(Windows + LM Studio, gemma4:e4b)에서 별도 진행. 본 디렉토리
검증 가이드는 LLM 호출을 동반하지 않는다.

## CLI

```
cd experiments
../.venv/bin/python run_experiment.py <key>
```

`<key>`는 위 표의 `dispatcher key` 컬럼 참조 (13 active).

## 참고

- 본 디렉토리의 모듈화는 plan `experiments` (docs/plans/experiments.md) 의 task-01~07 결과.
- abandoned 처리된 plan 문서는 `docs/plans/index.md` 의 Abandoned 섹션 참조.
