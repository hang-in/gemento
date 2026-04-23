---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: A
depends_on: []
---

# Task 01 — Exp07 산출물 정정 (UTF-8 옵션 + 해석 보정)

## Changed files

- `experiments/measure.py` — CLI 인자 확장 + 보고서 파일 출력 함수 추가
  - 기존 `argparse.ArgumentParser` 정의부 (파일 끝 부근 `if __name__ == "__main__":` 블록, 약 line 400~460 범위)
  - 기존 `print("\n" + generate_markdown_report(analysis))` 경로 (약 line 459)
- `docs/reference/handoff-to-gemini-exp7-final.md` — "Loop Saturation 해석 정정" 섹션 추가 (기존 내용은 유지, append 방식)

## Change description

### 1. measure.py — `--output` 옵션 추가

**Step 1**: `argparse.ArgumentParser` 정의부에 다음 인자 추가:

```python
parser.add_argument(
    "-o", "--output",
    type=str,
    default=None,
    help="보고서를 지정 경로에 UTF-8로 저장 (stdout 대신)",
)
```

**Step 2**: `args.markdown` 경로에서 출력 분기:

```python
if args.markdown:
    report_md = generate_markdown_report(analysis)
    if args.output:
        Path(args.output).write_text(report_md, encoding="utf-8")
        print(f"✓ 보고서 저장: {args.output}")
    else:
        print("\n" + report_md)
```

**근거**: Windows PowerShell의 `>` 리다이렉트 기본 인코딩이 UTF-16 LE. Python이 직접 `encoding="utf-8"`로 기록하면 근본 해결.

**원칙**: 기존 stdout 출력 경로는 그대로 — `--output` 없이 호출하면 회귀 없음.

### 2. handoff-to-gemini-exp7-final.md — 해석 정정 섹션

기존 문서 하단(구분선 `---` 앞)에 다음 섹션 append:

```markdown
---

## 5. 사후 정정 (Architect Claude, 2026-04-24)

### 5.1 포화점 해석 재검토

원시 데이터(`exp07_loop_saturation_20260424_015343.json`)를 288 trial 전체로 분석한 결과:

| 조건 | 평균 actual_cycles |
|------|-------------------|
| baseline_8 ~ baseline_20 | 6.86 ~ 7.00 |
| phase_8 ~ phase_20 | 6.97 ~ 7.11 |

**모든 조건에서 실제 사용된 cycle 수는 약 7**로 수렴했다. 즉 `MAX_CYCLES`를 15, 20으로 올려도 내부 수렴 판정(C)이 먼저 CONVERGED를 찍어 상한이 사용되지 않는다.

### 5.2 정정 결론

- **포화점은 "MAX_CYCLES 15"가 아니라 "actual_cycles ≈ 7"** — 상한은 안전장치일 뿐.
- 정답률 차이(79~88%)는 같은 7 cycle 안에서 **phase 프롬프트가 추론 품질**을 다르게 만든 결과.
- **운영 기본값 권장**: `MAX_CYCLES=11, use_phase_prompt=True` — 저비용·고안정.

### 5.3 인코딩 이슈 해결

`experiments/results/exp07_report.md`는 UTF-16 LE로 저장되었다. Windows PowerShell의 `>` 기본 인코딩이 원인. 향후 Exp08부터는 `python measure.py ... --output 파일경로` 경로를 사용할 것 (UTF-8 직접 기록, measure.py Task 01에서 추가).
```

## Dependencies

- 선행 Task 없음.
- 외부 의존성 없음 (표준 라이브러리만 사용).

## Verification

```bash
# 1. --output 옵션 존재 확인
cd /Users/d9ng/privateProject/gemento && python3 experiments/measure.py --help | grep -- '--output'
# 기대: "-o OUTPUT, --output OUTPUT ..." 라인 출력

# 2. UTF-8로 실제 파일 기록 확인
cd /Users/d9ng/privateProject/gemento && python3 experiments/measure.py \
  "experiments/results/exp07_loop_saturation_20260424_015343.json" \
  --markdown --output /tmp/exp07_retest.md \
&& file /tmp/exp07_retest.md | grep -E "UTF-8|ASCII"
# 기대: "UTF-8" 또는 "ASCII text" 포함 (UTF-16 아님)

# 3. 기존 stdout 경로 회귀 없음 확인
cd /Users/d9ng/privateProject/gemento && python3 experiments/measure.py \
  "experiments/results/exp07_loop_saturation_20260424_015343.json" \
  --markdown | head -5
# 기대: Markdown 표 헤더 출력 (에러 없이)

# 4. 정정 섹션 확인
grep -c "actual_cycles ≈ 7" docs/reference/handoff-to-gemini-exp7-final.md
# 기대: 1 이상
```

## Risks

- **영향 범위**: measure.py는 모든 실험의 보고서 생성에 사용됨. `--output` 인자 기본값 `None`과 분기로 회귀 방지.
- **파일 경로 유효성**: `Path(args.output).write_text(...)`는 상위 디렉토리 부재 시 예외. 사용자 실수 입력 대비 의도적 실패(silent 폴백 금지) — CLAUDE.md "silent fallbacks 최소화" 원칙 준수.
- **handoff 문서는 완료(status: completed) 상태**이지만 append-only 정정이므로 안전. metadata `updated_at` 갱신 고려 가능하나 필수 아님 (완료 문서의 이력 추적은 git으로).

## Scope boundary

**Task 01에서 절대 수정 금지**:
- `experiments/orchestrator.py` (Task 03 영역)
- `experiments/run_experiment.py` (Task 04 영역)
- `experiments/measure.py`의 `generate_markdown_report()`, `analyze_*()` 함수 본문 (Task 05 영역 — 본 Task는 CLI/출력만)
- `experiments/tools/` 전체 (Task 02 영역)
- `experiments/results/exp07_report.md` 재생성 (과거 결과는 그대로 두되, 새 실험부터 UTF-8 보장)
