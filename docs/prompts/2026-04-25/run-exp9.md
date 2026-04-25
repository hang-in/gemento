---
type: prompt
status: ready
updated_at: 2026-04-25
for: Gemini CLI (Windows 실행용)
experiment: exp09-long-context-stress-test
---

# Exp09 실행 프롬프트

아래를 복붙하여 Gemini 세션에서 실행하세요.

---

제멘토 실험 9(Long-Context Stress Test)를 실행해줘.

## 목표

3 arm 비교 실험:
- solo_dump: 문서 전체를 LLM에 단일 투입
- rag_baseline: BM25 top-5 chunks 검색 후 투입
- abc_tattoo: ABC + Tattoo + chunk-by-chunk iteration

가설:
- H9a: abc_tattoo > solo_dump (accuracy_v2)
- H9b: abc_tattoo ≥ rag_baseline (accuracy_v2)

## 사전 준비 (이미 완료되지 않았으면)

```powershell
cd C:\path\to\gemento
git pull origin main
.\.venv\Scripts\Activate.ps1
pip install bm25s
```

## 실행 순서

1. 서버 상태 확인:
   ```powershell
   curl.exe -s http://yongseek.iptime.org:8005/v1/models
   ```

2. Smoke test:
   ```powershell
   cd experiments
   python -c "from tools.chunker import chunk_document; from tools.bm25_tool import bm25_retrieve; print('OK')"
   ```

3. 실험 실행:
   ```powershell
   python run_experiment.py longctx
   ```
   - 체크포인트: `experiments\results\partial_longctx.json`
   - 중단 후 재실행 시 자동으로 이어서 진행

4. 분석:
   ```powershell
   python measure.py "results\exp09_longctx_*.json" --markdown --output "results\exp09_report.md"
   ```

5. 커밋:
   ```powershell
   git add experiments\results\exp09_longctx_*.json experiments\results\exp09_report.md
   git commit -m "feat: 실험 9 결과 — Long-Context Stress Test"
   git push origin main
   ```

## 결과 해석

- accuracy_v2 기준 arm별 비교
- arm_by_size: Small(3K) / Medium(10K) / Large(20K) 별 성능
- arm_by_hop: needle / 2-hop / 3-hop 별 성능
- evidence_hit_rate_abc: ABC arm의 chunk retrieval 품질

## 참조

- 상세 핸드오프: `docs/reference/handoff-to-gemini-exp9.md`
- 태스크셋: `experiments/tasks/longctx_taskset.json`
- 문서들: `experiments/tasks/longctx_docs/*.md`
