---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: D
depends_on: [06]
---

# Task 07 — Measure analyzer + Gemini 핸드오프

## Changed files

- `experiments/measure.py`
  - `analyze_tool_use()` (line 416~) 뒤에 `analyze_longctx()` 신규 함수 추가
  - `ANALYZERS` 딕셔너리 (line 550~)에 `"longctx": analyze_longctx` 추가
  - `generate_markdown_report()` (line 205~) 에 `longctx` 분기 추가
- `docs/reference/handoff-to-gemini-exp9.md` — **신규**. Gemini 실행 가이드.
- `docs/prompts/2026-04-25/run-exp9.md` — **신규**. Gemini 세션 복붙용 프롬프트.
- `docs/reference/index.md` — **조건부**. 파일 존재 시 링크 1줄 추가.

## Change description

### Step 1 — `analyze_longctx()` 함수 설계

**입력**: `exp09_longctx_*.json` 결과 파일 (Task 06 출력).

**반환 구조**:

```python
{
    "experiment": "longctx",
    "arm_summary": {
        "solo_dump":    {"accuracy_v2": 0.XX, "accuracy_v1": 0.XX, "n_trials": NN, "error_count": M},
        "rag_baseline": {...},
        "abc_tattoo":   {...},
    },
    "arm_by_size": {
        # arm × size_class의 정답률 2D
        "solo_dump":    {"small": 0.XX, "medium": 0.XX, "large": 0.XX},
        "rag_baseline": {...},
        "abc_tattoo":   {...},
    },
    "arm_by_hop": {
        "solo_dump":    {"needle": ..., "2-hop": ..., "3-hop": ...},
        "rag_baseline": {...},
        "abc_tattoo":   {...},
    },
    "task_breakdown": [
        {
            "task_id": "longctx-large-3hop-01",
            "size_class": "large",
            "hop_type": "3-hop",
            "solo_dump":    {"accuracy_v2": 0.XX, "avg_trial_errors": N},
            "rag_baseline": {"accuracy_v2": 0.XX, "avg_retrieved_chunks": 5},
            "abc_tattoo":   {"accuracy_v2": 0.XX, "avg_num_assertions": N, "evidence_hit_rate": 0.XX},
        },
        ...
    ],
    "key_deltas": {
        "H9a (abc - solo)":  float,  # +X%p
        "H9b (abc - rag)":   float,  # 양수면 제멘토 차별성 긍정
    },
    "evidence_hit_rate_abc": {
        # ABC arm에서 모델이 첨부한 evidence_ref.chunk_id가 
        # task의 gold_evidence_chunks 안에 든 비율
        "overall": float,
        "by_hop": {"needle": ..., "2-hop": ..., "3-hop": ...},
    },
    "error_modes": {
        # 실패 trial의 에러 분류 (arm별)
        "solo_dump":    {"context_overflow": N, "format_error": N, "wrong_synthesis": N, "other": N},
        "rag_baseline": {"retrieval_miss": N, "format_error": N, "wrong_synthesis": N, "other": N},
        "abc_tattoo":   {"evidence_miss": N, "format_error": N, "wrong_synthesis": N, "other": N},
    },
}
```

### Step 2 — Error mode taxonomy 분류 규칙

arm별로 실패 trial(정답률 < 1.0)을 다음 카테고리로 자동 분류:

- **context_overflow** (solo_dump 전용): `error` 필드에 `"context length exceeded"` 유사 문자열 포함
- **retrieval_miss** (rag_baseline 전용): `retrieved_chunk_ids`와 `gold_evidence_chunks`의 교집합이 비어 있음
- **evidence_miss** (abc_tattoo 전용): `evidence_refs_used`의 chunk_id들과 `gold_evidence_chunks`의 교집합이 비어 있음
- **format_error**: `final_answer` == None
- **wrong_synthesis**: final_answer 있으나 scoring_keywords 매칭 실패
- **other**: 위에 해당하지 않는 모든 경우

**분류 우선순위**: context_overflow > retrieval_miss/evidence_miss > format_error > wrong_synthesis > other

### Step 3 — Evidence hit rate 계산 (ABC arm)

```python
hit_rate = (
    evidence_refs_used 중 chunk_id가 gold_evidence_chunks에 속한 것의 개수
) / len(evidence_refs_used)
```

**의미**: 모델이 선택한 근거가 실제 정답 근거와 겹치는 정도. ABC arm 고유 메트릭.

### Step 4 — `generate_markdown_report()` 분기

기존 `loop_saturation`, `tool_use` 분기 패턴 그대로. 출력 마크다운 구성:

```markdown
# 실험 결과: longctx

> N = 3 trials per (arm × task); arms = solo_dump / rag_baseline / abc_tattoo

## Arm Summary

| Arm | Accuracy (v2) | Errors | Avg word count (solo/rag/abc) |
|-----|---------------|--------|-------------------------------|
| solo_dump    | X.XX | N | ... |
| rag_baseline | X.XX | N | ... |
| abc_tattoo   | X.XX | N | ... |

**Key Deltas**:
- H9a (abc − solo): +X.XX%p
- H9b (abc − rag): +X.XX%p

## Arm × Size Class

| Arm | Small (3K) | Medium (10K) | Large (20K) |
|-----|------------|--------------|-------------|
| solo_dump    | X | X | X (context overflow expected) |
| rag_baseline | X | X | X |
| abc_tattoo   | X | X | X |

## Arm × Hop Type

...

## Evidence Hit Rate (abc_tattoo)

- Overall: X.XX
- By hop: needle X.XX / 2-hop X.XX / 3-hop X.XX

## Error Modes

...

## Per-task Breakdown

...

**H9a breakthrough**: ✅/❌ (abc > solo)
**H9b differentiation**: ✅/❌ (abc ≥ rag)
```

### Step 5 — `docs/reference/handoff-to-gemini-exp9.md`

Exp08b 핸드오프 템플릿 재사용. 주요 내용:

```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-25
author: Architect Claude
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 9 — Long-Context Stress Test

## 1. 목적
제멘토 원래 가설 검증: 외부 상태(Tattoo)로 유효 context 확장.
3 arm 비교: solo_dump / rag_baseline / abc_tattoo.
가설 H9a/b/c (ABC > Solo, ABC ≥ RAG, 에러 모드 다름).

## 2. 환경
- 파이썬: .venv (프로젝트 루트)
- 서버: llama.cpp (기존 설정 그대로)
- 추가 패키지: **bm25s** (신규). Exp08에서 scipy/numpy 이미 설치됨.

## 3. 사전 준비
```powershell
cd C:\path\to\gemento
git pull origin main
.\.venv\Scripts\Activate.ps1
pip install bm25s

# 서버 확인
curl.exe -s http://yongseek.iptime.org:8005/v1/models
```

## 4. 실행
### 4.1 Smoke test (태스크셋 로드 + 첫 1개 태스크 solo_dump 1 trial만)
```powershell
cd experiments
# (선택: 빠른 smoke 스크립트가 Task 07에서 만들어지지 않는다면
#  run_longctx 전체 실행으로 진행)
python run_experiment.py longctx
# 체크포인트: partial_longctx.json 으로 중단/재개 가능
```

### 4.2 분석
```powershell
python measure.py "results\exp09_longctx_*.json" --markdown --output "results\exp09_report.md"
```

## 5. 예상 소요
- 90 runs × 평균 수 분 = 수 시간~1일
- ABC arm + Large 20K 문서는 chunk 당 A 호출 → 가장 오래 걸림

## 6. 결과 기록·커밋
```powershell
git add experiments\results\exp09_longctx_*.json experiments\results\exp09_report.md
git commit -m "feat: 실험 9 결과 — Long-Context Stress Test"
git push origin main
```

## 7. 문제 발생 시
- n_ctx 8K 초과 에러 (Solo-dump Large): **예상된 현상**. 결과에 error 필드로 기록되고 진행.
- bm25s ImportError: `pip install bm25s` 재실행.
- 체크포인트 이어가기: 동일 명령 재실행 시 `partial_longctx.json`에서 자동 이어감.
```

### Step 6 — `docs/prompts/2026-04-25/run-exp9.md`

Gemini가 자기 세션에 복붙할 단일 프롬프트. exp7/exp8 프롬프트 패턴 재사용.

### Step 7 — `docs/reference/index.md` 조건부 업데이트

파일 존재 시에만:
```markdown
- [handoff-to-gemini-exp9.md](handoff-to-gemini-exp9.md) — 실험 9 Gemini 핸드오프 (Long-Context Stress Test)
```

## Dependencies

- **Task 06 완료**: `run_longctx()` + `EXPERIMENTS["longctx"]` 등록이 있어야 Gemini 실행 지시가 유효.
- 외부 패키지 추가 없음 (measure 분석기만).

## Verification

```bash
# 1. analyze_longctx 등록
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import ANALYZERS, analyze_longctx
assert 'longctx' in ANALYZERS
print('OK ANALYZERS')
"

# 2. Mock 데이터로 analyze_longctx 호출 smoke
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import analyze_longctx, generate_markdown_report
mock = {
    'experiment': 'longctx',
    'model': 'gemma4-e4b',
    'arms': [
        {'label':'solo_dump'}, {'label':'rag_baseline'}, {'label':'abc_tattoo'},
    ],
    'trials_per_task': 3,
    'chunk_size': 500,
    'chunk_overlap': 50,
    'rag_top_k': 5,
    'results_by_arm': {
        'solo_dump': [{
            'task_id':'longctx-small-needle-01','size_class':'small','hop_type':'needle',
            'expected_answer':'','gold_evidence_chunks':[1],
            'trials':[{'trial':1,'arm':'solo_dump','final_answer':'foo','error':None,'doc_word_count':2200}],
        }],
        'rag_baseline': [{
            'task_id':'longctx-small-needle-01','size_class':'small','hop_type':'needle',
            'expected_answer':'','gold_evidence_chunks':[1],
            'trials':[{'trial':1,'arm':'rag_baseline','final_answer':'bar','error':None,'retrieved_chunk_ids':[0,1,2],'top_k':5}],
        }],
        'abc_tattoo': [{
            'task_id':'longctx-small-needle-01','size_class':'small','hop_type':'needle',
            'expected_answer':'','gold_evidence_chunks':[1],
            'trials':[{'trial':1,'arm':'abc_tattoo','final_answer':'baz','error':None,'num_chunks':5,'num_assertions':3,'evidence_refs_used':[{'chunk_id':1}]}],
        }],
    },
}
r = analyze_longctx(mock, task_map=None)
required = {'arm_summary','arm_by_size','arm_by_hop','key_deltas','evidence_hit_rate_abc','error_modes'}
assert required.issubset(r.keys()), f'missing: {required - set(r.keys())}'
md = generate_markdown_report(r)
assert 'H9a' in md and 'H9b' in md
print('OK analyzer smoke')
"

# 3. 핸드오프 문서
test -f docs/reference/handoff-to-gemini-exp9.md && echo 'handoff: OK'
test -f docs/prompts/2026-04-25/run-exp9.md && echo 'prompt: OK'

# 4. 핸드오프에 bm25s 설치 명시
grep -c "pip install bm25s" docs/reference/handoff-to-gemini-exp9.md
# 기대: 1 이상

# 5. 핸드오프에 체크포인트 언급
grep -c "partial_longctx" docs/reference/handoff-to-gemini-exp9.md
# 기대: 1 이상

# 6. 기존 실험 결과 분석 회귀 없음 — 최근 exp08b 결과 파일로 기존 분석기 동작 확인
cd /Users/d9ng/privateProject/gemento && .venv/bin/python experiments/measure.py "experiments/results/exp08b_tool_use_refined_*.json" --markdown 2>&1 | head -3
# 기대: markdown 출력 시작 (에러 없이)
```

## Risks

- **Mock 데이터 분석 실패 시 실제 실행 결과 분석도 실패**: Verification 2번이 mock로 smoke 테스트. 실제 필드 명 일치(Task 06 출력 스키마) 필수.
- **Evidence hit rate 제로 division**: `evidence_refs_used`가 빈 리스트면 hit rate 분모 0. `if ... else 0.0` 처리 필수.
- **Error mode 오분류**: context_overflow를 문자열 매칭으로 감지. llama.cpp 에러 메시지 변화 시 other로 잡힘. 초기엔 여러 패턴 fallback (`"context"`, `"overflow"`, `"length"`, `"n_ctx"` 등).
- **Gold evidence chunks과 chunker 결과 불일치**: Task 01에서 `gold_evidence_chunks`를 설계할 때 500 words chunker 기준으로 작성해야 함. chunker 파라미터 변경 시 gold도 갱신 필요. 이 제약을 Task 01에서 명시.
- **실험 결과 파일 크기**: 문서·chunk 포함 시 매우 커질 수 있음. Task 06에서 이미 `_document` 원문 저장 금지했음. 재확인.
- **해석 편향**: Measure가 analyzer 레벨에서 H9a/b 결론을 출력 — 수치가 애매하면 분석가(사용자)가 별도 판단. analyzer는 수치만 제시, 결론은 false/true만 표시.

## Scope boundary

**Task 07에서 절대 수정 금지**:
- `experiments/run_experiment.py` (Task 06 영역)
- `experiments/orchestrator.py`, `experiments/system_prompt.py` (Task 05 영역)
- `experiments/schema.py` (Task 04 영역)
- `experiments/tools/` (Task 02, 03 영역)
- `experiments/tasks/` (Task 01 영역)
- `experiments/measure.py`의 기존 `analyze_*` 함수 본문 — 본 Task는 추가만.
- 기존 `docs/reference/handoff-to-gemini-exp*.md` 본문 — 신규 파일만 작성.

**허용 범위**:
- `experiments/measure.py`: `analyze_longctx` 함수 신규 추가 + `ANALYZERS` 1줄 + `generate_markdown_report` 내 `longctx` 분기 추가
- 신규: `docs/reference/handoff-to-gemini-exp9.md`, `docs/prompts/2026-04-25/run-exp9.md`
- 조건부: `docs/reference/index.md`에 1줄 link 추가 (파일 존재 시에만)
