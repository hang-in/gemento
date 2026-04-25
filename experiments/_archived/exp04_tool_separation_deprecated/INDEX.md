# 실험 4 (deprecated): Tool Separation

> **상태**: deprecated. 결과 파일 0개. 구현 미완성. abc-pipeline (exp04_abc_pipeline)으로 대체됨.
> 격리 일자: 2026-04-25 (experiments-task-05).

## 격리 사유

도구 호출을 같은 루프(단일)에서 처리할지, 별도 루프로 분리할지 결정하는
실험으로 설계되었으나, 실험 2 (multiloop) 이후 도구 시뮬레이션 로직 완성을
기다리며 placeholder 상태로 남아 있었다. 이후 ABC 직렬 파이프라인
(`exp04_abc_pipeline`)에서 도구 통합이 자연스럽게 해결되어 본 실험은 폐기됨.

원본 `run_tool_separation()` 함수는 placeholder 결과만 저장하는 stub:

```python
results.append({
    "task_id": task["id"],
    "status": "not_implemented_yet",
    "note": "실험 2 결과 이후 구현 예정",
})
```

결과 JSON 도 0개로 history 손실 없음.

## 기존 위치

- 함수: `experiments/run_experiment.py:run_tool_separation` (line 661 in v1)
- 디렉토리: `experiments/exp04_tool_separation/설명.md` (현재 삭제됨)
- dispatcher key: `tool-separation` (제거됨, 14 → 13 active)

## 현재 위치

- 함수: `experiments/_archived/exp04_tool_separation_deprecated/run.py:run`
- dispatcher 에서 제거되었으므로 CLI 호출 불가. 수동 호출은 가능:
  ```python
  from _archived.exp04_tool_separation_deprecated.run import run
  run()
  ```

## 변경 이력

- 2026-04-25: experiments-task-05 으로 격리. dispatcher 에서 제거. 설명.md 흡수.
