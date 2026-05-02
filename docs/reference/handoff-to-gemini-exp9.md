---
type: reference
status: archived
archived_at: 2026-05-03  # auto-set stale cleanup
updated_at: 2026-04-25
author: Coder Claude · Implementer
recipient: Gemini CLI (Windows)
---

# 핸드오프: 실험 9 — Long-Context Stress Test

## 1. 목적

제멘토 원래 핵심 가설 검증: 외부 상태(Tattoo)로 소형 LLM의 유효 컨텍스트를 확장한다.

3 arm 비교: **solo_dump** / **rag_baseline** / **abc_tattoo**

- **H9a**: ABC+Tattoo accuracy > Solo-dump (전체 문서 단일 투입)
- **H9b**: ABC+Tattoo accuracy ≥ RAG baseline (BM25 top-K 검색)
- **H9c**: 에러 모드 분포가 arm별로 다름 (context_overflow vs retrieval_miss vs evidence_miss)

## 2. 환경

- 파이썬: `.venv` (프로젝트 루트)
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

### 4.1 Smoke test (BM25 + chunker 동작 확인)

```powershell
cd experiments
python -c "
from tools.chunker import chunk_document
from tools.bm25_tool import bm25_retrieve
text = 'hello world ' * 200
chunks = [c.to_dict() for c in chunk_document(text, size=50, overlap=5)]
results = bm25_retrieve('hello', chunks, top_k=3)
print('smoke OK, top chunk_id:', results[0]['chunk_id'])
"
```

### 4.2 태스크셋 로드 확인

```powershell
cd experiments
python -c "
import json
from run_experiment import LONGCTX_TASKSET_PATH, _TASKS_DIR, LONGCTX_CHUNK_SIZE, LONGCTX_CHUNK_OVERLAP
from tools.chunker import chunk_document
with open(LONGCTX_TASKSET_PATH) as f:
    data = json.load(f)
print(f'loaded {len(data[chr(116)+chr(97)+chr(115)+chr(107)+chr(115)])} tasks')
for t in data['tasks'][:3]:
    with open(_TASKS_DIR / t['document_path']) as f:
        doc = f.read()
    chunks = chunk_document(doc, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)
    print(f'  {t[\"id\"]}: {len(doc.split())} words -> {len(chunks)} chunks')
"
```

### 4.3 본 실험 실행

```powershell
cd experiments
python run_experiment.py longctx
# 체크포인트: partial_longctx.json 으로 중단/재개 가능
# 중단 후 재실행하면 자동으로 이어서 진행
```

### 4.4 분석

```powershell
python measure.py "results\exp09_longctx_*.json" --markdown --output "results\exp09_report.md"
```

## 5. 예상 소요

- 90 runs × 평균 수 분 = **수 시간 ~ 1일**
- ABC arm + Large 20K 문서는 chunk 당 A 호출 → 가장 오래 걸림
  - Large 20K / 500 words_per_chunk ≈ 30 chunks × 3 trials × 4 tasks × 1 A call = ~360 A calls (ABC arm만)
- 체크포인트(`partial_longctx.json`)로 분할 실행 권장

## 6. 결과 기록·커밋

```powershell
git add experiments\results\exp09_longctx_*.json experiments\results\exp09_report.md
git commit -m "feat: 실험 9 결과 — Long-Context Stress Test"
git push origin main
```

## 7. 문제 발생 시

| 문제 | 원인 | 대처 |
|------|------|------|
| n_ctx 8K 초과 에러 (Solo-dump Large) | **예상된 현상** — 실험 포인트 | error 필드에 기록되고 계속 진행됨 |
| `ModuleNotFoundError: bm25s` | bm25s 미설치 | `pip install bm25s` 재실행 |
| 체크포인트 없이 처음부터 다시 | partial_longctx.json 손상 | 파일 삭제 후 재실행 |
| ABC arm assertion 폭증 | Large 20K 문서 처리 중 | 정상 — assertion_soft_cap=64로 제한됨 |
| final_answer=None | LLM JSON 파싱 실패 | error_modes에 format_error로 집계됨 |

## 8. 핵심 메트릭 해석

- **accuracy_v2**: scoring_keywords 기반 채점 (0.0~1.0)
- **evidence_hit_rate**: ABC arm에서 모델이 선택한 chunk_id가 gold_evidence_chunks와 겹치는 비율
- **H9a ✅**: abc_tattoo accuracy > solo_dump accuracy
- **H9b ✅**: abc_tattoo accuracy ≥ rag_baseline accuracy
