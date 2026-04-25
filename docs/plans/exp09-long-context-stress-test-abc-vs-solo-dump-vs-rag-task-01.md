---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: A
depends_on: []
---

# Task 01 — Long-doc 태스크셋 설계 (10 tasks, 3 size × 3 hop)

## Changed files

- `experiments/tasks/longctx_taskset.json` — **신규 파일**. 10개 long-document 태스크.
- `experiments/tasks/longctx_docs/` — **신규 디렉토리**. 긴 문서 본문을 별도 파일로 저장 (태스크셋 JSON은 참조만).
  - 최소 10개 `.md` 또는 `.txt` 파일. 파일명 규칙: `doc_01_topic.md` 등.

## Change description

### Step 1 — 태스크 분포 확정

| 카테고리 | 개수 | Context size | Hop type |
|---------|------|--------------|----------|
| Needle-in-haystack | 3 | 3K / 10K / 20K 각 1개 | 1-hop (단일 증거) |
| 2-hop multi-hop | 4 | 3K 1, 10K 2, 20K 1 | 2개 증거 연결 |
| 3+hop multi-hop | 3 | 10K 1, 20K 2 | 3개 이상 증거 종합 |

**Context size 기준**: 단어 수로 측정 (토큰 아님). 대략 1 token ≈ 0.75 words 가정 시:
- **Small (3K tokens)**: ~2,250 words
- **Medium (10K tokens)**: ~7,500 words
- **Large (20K tokens)**: ~15,000 words

### Step 2 — 태스크셋 JSON 스키마

`experiments/tasks/longctx_taskset.json`:

```json
{
  "version": "1.0",
  "description": "Exp09 Long-Context Stress Test. Multi-hop QA over long documents.",
  "tasks": [
    {
      "id": "longctx-small-needle-01",
      "category": "longctx",
      "size_class": "small",
      "hop_type": "needle",
      "document_path": "longctx_docs/doc_01_small_needle.md",
      "document_word_count": 2180,
      "question": "...",
      "expected_answer": "...",
      "scoring_keywords": [["..."], ["..."]],
      "gold_evidence_chunks": [3],
      "gold_evidence_text": "원문에서 정답을 뒷받침하는 짧은 구절 (해설용, 채점에 사용 안 함)"
    }
  ]
}
```

### Step 3 — Document 작성 방식

**두 가지 선택지**:

- **(권장) 공개 도메인 텍스트 편집**: Wikipedia 요약, 오래된 소설(Project Gutenberg), 논문 abstract 모음 등을 짜깁기하여 길이 맞춤. **출처 명시 필수**.
- **합성 문서**: 가상 회사 문서, 가상 연구 보고서, 가상 회의록 등 직접 작성. 저작권 이슈 0이지만 작성 비용 큼.

**실용적 하이브리드**: 80% 공개 도메인 + 20% 수동 작성 (정답 증거 구간을 직접 넣어 multi-hop 설계 가능).

### Step 4 — 10개 태스크 상세 구성

```
longctx-small-needle-01  (3K, needle): "회사 X의 CEO는 누구인가?" 식 단일 사실
longctx-medium-needle-01 (10K, needle): 문서 후반부 단일 사실 찾기
longctx-large-needle-01  (20K, needle): 문서 중반·후반 단일 사실

longctx-small-2hop-01   (3K, 2-hop): "A가 만든 제품의 출시 연도는?" (A→제품 먼저, 제품→연도 두 번째)
longctx-medium-2hop-01  (10K, 2-hop): 연결 증거가 서로 멀리 떨어짐
longctx-medium-2hop-02  (10K, 2-hop): 다른 주제로 difficulty 분산
longctx-large-2hop-01   (20K, 2-hop): 두 증거가 문서 전반·후반에 분리

longctx-medium-3hop-01  (10K, 3-hop): 3단계 연쇄 추론
longctx-large-3hop-01   (20K, 3-hop): 3개 증거 공간적으로 흩어짐
longctx-large-3hop-02   (20K, 3-hop): 방해 정보(distractor) 다수 포함
```

### Step 5 — Scoring keywords 설계

기존 math-04 결함 교훈 반영:
- 각 scoring_keywords 그룹은 **최소 2 token 조합** (예: `[["CEO", "이름"], ["2023"]]` 대신 `[["2023년", "출시"]]`)
- distractor와 우연 매칭되지 않도록 task별로 **직접 테스트** — Small 문서 안에서 grep해서 답 외 위치에 같은 키워드가 등장하면 교체
- `gold_evidence_chunks` 필드는 분석용(chunker 관점에서 어느 chunk가 정답 포함) — 자동 채점에 사용 안 함

### Step 6 — 교차 검증 (math-04 교훈)

태스크 10개 작성 후 **다음 체크리스트**:

- [ ] `expected_answer`가 실제로 `document` 본문에서 도출 가능한지 직접 확인 (자동화 말고 수동)
- [ ] `scoring_keywords`가 해당 태스크의 document 내에서 **정답 구간 외**에는 매칭되지 않는지 grep 확인
- [ ] `hop_type` 라벨이 실제 필요 증거 개수와 일치하는지 검토
- [ ] `size_class`가 실제 word count와 일치하는지 확인 (±10% 허용)

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음.
- 공개 도메인 텍스트 소싱 필요 (Wikipedia, Gutenberg 등)

## Verification

```bash
# 1. 파일 존재 확인
test -f experiments/tasks/longctx_taskset.json && echo "taskset: OK"
test -d experiments/tasks/longctx_docs && echo "docs dir: OK"
ls experiments/tasks/longctx_docs/*.md 2>/dev/null | wc -l
# 기대: 10 이상 (최소 10개 문서)

# 2. 태스크 개수 및 분포
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import json
with open('experiments/tasks/longctx_taskset.json') as f:
    d = json.load(f)
tasks = d['tasks']
assert len(tasks) == 10, f'need 10 tasks, got {len(tasks)}'

from collections import Counter
size_count = Counter(t['size_class'] for t in tasks)
hop_count = Counter(t['hop_type'] for t in tasks)
print(f'size: {dict(size_count)}')
print(f'hop:  {dict(hop_count)}')
# 기대: size {'small':2, 'medium':4, 'large':4}
# 기대: hop {'needle':3, '2-hop':4, '3-hop':3}
"

# 3. 각 태스크의 document_path가 실제 존재하는지
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import json, os
with open('experiments/tasks/longctx_taskset.json') as f:
    d = json.load(f)
missing = [t['id'] for t in d['tasks'] if not os.path.exists('experiments/tasks/' + t['document_path'])]
assert not missing, f'missing docs: {missing}'
print('all doc paths resolve')
"

# 4. size_class와 실제 word count 일치 (±10%)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import json, os
with open('experiments/tasks/longctx_taskset.json') as f:
    d = json.load(f)
targets = {'small': 2250, 'medium': 7500, 'large': 15000}
for t in d['tasks']:
    with open('experiments/tasks/' + t['document_path']) as f:
        wc = len(f.read().split())
    target = targets[t['size_class']]
    diff_pct = abs(wc - target) / target
    ok = '✓' if diff_pct <= 0.10 else '✗'
    print(f'{ok} {t[\"id\"]}: {wc} words (target {target})')
"

# 5. scoring_keywords false-positive 스캐닝 (정답 외 매칭 여부)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import json
with open('experiments/tasks/longctx_taskset.json') as f:
    d = json.load(f)
# 수동 검증 체크리스트 프린트
for t in d['tasks']:
    kws = t['scoring_keywords']
    print(f'{t[\"id\"]}: keywords={kws}')
    print(f'  expected: {t[\"expected_answer\"][:80]}')
# 기대: 출력만 — 실제 검증은 Developer가 document 내 grep으로 수동 확인
"
```

## Risks

- **저자 편향**: Developer가 직접 작성한 태스크는 본인이 알고 있는 답 구조에 유리하게 편향될 수 있음. 최소 체크리스트 4개를 **개별 태스크마다** 반드시 수동 통과.
- **공개 도메인 출처**: Wikipedia는 라이선스 OK. Project Gutenberg도 대부분 Public Domain. 단 **출처 표기 필수** — document 파일 상단에 `source:` 주석.
- **Size class 드리프트**: ±10% 허용이지만 편집 중 길이가 조절되면 `document_word_count` 필드도 갱신 필수.
- **Scoring keyword false-positive**: 긴 문서에서는 단일 단어가 여러 곳에 등장. **반드시 grep으로 정답 외 매칭 검증**. math-04 결함의 현대적 재현 방지.
- **한국어 vs 영어**: Exp08 math-03에서 한국어 답변의 scoring 매칭 편차 관측됨. Exp09는 영어 문서로 통일 권장 — 한국어 버전은 별도 실험으로 분리.

## Scope boundary

**Task 01에서 절대 수정 금지**:
- 기존 `experiments/tasks/taskset.json` — 건드리지 않음 (math/logic/synthesis 태스크 유지)
- `experiments/tools/` 내 모든 파일 (Task 02, 03 영역)
- `experiments/schema.py` (Task 04 영역)
- `experiments/orchestrator.py`, `run_experiment.py`, `measure.py`, `system_prompt.py`
- `experiments/results/` 아래 기존 파일

**허용 범위**:
- 신규: `experiments/tasks/longctx_taskset.json`
- 신규 디렉토리: `experiments/tasks/longctx_docs/` + 내부 `.md`/`.txt` 파일 10개
