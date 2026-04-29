---
type: plan
status: in_progress
updated_at: 2026-04-29
slug: gemento-public-readiness-pass-config-readme
version: 1
---

# Gemento Public-Readiness Pass — config 안전화 + 문서 정합 + README 보수화

## Description

외부 공개/재현/토론에 적합한 상태로 정리. 직전 reviewer finding (Task 03 한·영 README 동기화 — `README.ko.md:146` 의 4 fail / early-stop disclosure 누락) 도 함께 처리.

**사용자 명시 정책 준수**:
- 과장된 주장 금지 ("RAG 이긴다" / "대형 모델 대체" / "novel framework" / "AGI" / "Operating System" / "ABC+Tattoo universally beats RAG")
- README 의 현재 보수적 톤 유지
- 문서·코드 불일치 제거
- 최소 변경으로 public-readiness 향상
- 큰 리팩토링 / 결과 재해석 / 새 기능 추가 금지
- 본 적 없는 외부 논문 인용 금지 — 검증 불확실 항목은 "citation pending"

7개 정찰 항목 모두 변경 필요 확인:
1. `experiments/config.py:14` — 개인 서버 (`yongseek.iptime.org:8005`) 노출
2. `requirements.txt` 없음 — Exp09 RAG baseline 의 `bm25_tool.py` 가 `bm25s` import 하는데 README Quickstart 누락
3. `docs/reference/conceptFramework.md` — `evidence_ref` 미래형 표현, 실제 schema 에 이미 구현
4. `experiments/exp10_reproducibility_cost/INDEX.md` — "task-06 후 채워짐" TBD
5. `README.md:35` / `README.ko.md:132` — H4 강한 톤 ("✅ Supported (+22.6pp)")
6. `README.md:178~196` — Related work 4 footnote 서지 미검증
7. `README.md` 상단 "What this is / is not" 박스 부재 + `README.ko.md:146` Exp10 4 fail / early-stop disclosure 동기화 누락

## Expected Outcome

1. `experiments/config.py` — `os.getenv("GEMENTO_API_BASE_URL", "http://localhost:8080")` 환경변수 + 기본값. 개인 서버 URL 노출 0.
2. `requirements.txt` 신규 — `httpx / numpy / scipy / bm25s`. README Quickstart `pip install -r requirements.txt` 한 줄.
3. `docs/reference/conceptFramework.md` — Assertion.evidence_ref 가 `experiments/schema.py` 에 이미 존재하는 사실 명시. Evidence Tool / citation resolver / validator 미구현 으로 정확화.
4. `experiments/exp10_reproducibility_cost/INDEX.md` — 현재 results/ 디렉토리의 실제 파일 (v2 final / v3 rescored / logic04 retry / math04 debug) 명시. TBD 제거.
5. README H4 행 한·영 — "✅ Supported (+22.6pp)" → "⚠ Conditionally supported", v1/v2 caveat 한 줄 evidence 컬럼.
6. README Related work 한·영 — 검증 불확실 항목은 "citation pending — needs bibliographic verification" 표시. "Gemento was developed independently" 표현 유지.
7. README 상단 "What this is / is not" 박스 한·영 — 첫인상에서 과장 리스크 제거, "ABC+Tattoo universally beats RAG" 명시 부정. `README.ko.md:146` Exp10 bullet 끝 4 trial JSON parse fail / early-stop 한 줄 동기화.

## Subtask Index

1. [task-01](./gemento-public-readiness-pass-config-readme-task-01.md) — config.py API URL 환경변수화 + requirements.txt 신규 (parallel_group A, depends_on: [])
2. [task-02](./gemento-public-readiness-pass-config-readme-task-02.md) — conceptFramework.md evidence_ref 상태 수정 (parallel_group A, depends_on: [])
3. [task-03](./gemento-public-readiness-pass-config-readme-task-03.md) — Exp10 INDEX.md 최신화 (parallel_group A, depends_on: [])
4. [task-04](./gemento-public-readiness-pass-config-readme-task-04.md) — README H4 보수화 한·영 (parallel_group B, depends_on: [])
5. [task-05](./gemento-public-readiness-pass-config-readme-task-05.md) — README "What this is / is not" 박스 한·영 + Exp10 ko disclosure 동기화 (parallel_group B, depends_on: [04])
6. [task-06](./gemento-public-readiness-pass-config-readme-task-06.md) — README Related work 각주 정리 한·영 (parallel_group B, depends_on: [05])

### 의존성 (Stage 기반)

```
Stage 1 (병렬 가능):
  Group A (코드·참고 문서, 독립 영역):
    task-01 (config + requirements)
    task-02 (conceptFramework)
    task-03 (Exp10 INDEX)

  Group B (README 한·영, 직렬 — 같은 두 파일 수정 conflict 회피):
    task-04 (H4 보수화)
       │
       ▼
    task-05 (What this is / is not + ko Exp10 disclosure)
       │
       ▼
    task-06 (Related work 정리)
```

Group A 와 Group B 독립. Group B 는 README 두 파일 동시 수정이라 직렬.

## Constraints

- 사용자 정책 준수: 과장 금지, 보수적 톤 유지, 가짜 인용 위험 제거, README 현재 톤 보존
- 코드 변경 영역은 `experiments/config.py` 만 (Subtask 1) — orchestrator / measure / schema / taskset 변경 0
- v2 final / v3 rescored / logic04 retry / math04 debug JSON 모두 read-only
- `docs/reference/results/exp-10-reproducibility-cost.md` 변경 0 (직전 plan 산출물)
- `docs/reference/researchNotebook.md` 변경 0 (직전 plan 산출물)
- 영문 `researchNotebook.en.md` 변경 0 (Closed 추가만 정책)
- score_answer_v3 / taskset.json 의 logic-04 정의 변경 0
- 외부 노출 톤 검사: `\bOperating System\b` / `\bnovel framework\b` / `\bAGI\b` 모두 미사용 검증
- 한·영 README 동기화 — 핵심 사실/수치 양쪽 일치
- README 의 디자인/시각 요소 (스크린샷, 다이어그램) 변경 금지
- requirements.txt 의 패키지 버전은 unpinned (loose) — 재현성 vs 호환성 trade-off, 별도 결정

## Non-goals

- 큰 코드 리팩토링 (orchestrator 구조 변경 / scoring logic 변경)
- 실험 결과 재해석 / 수치 변경 (Exp00~10 모든 결과 그대로)
- 새 기능 추가 (Exp11 / Exp12 / 도구 추가 / 모델 변경)
- H4 의 balanced rerun 실제 실행 (별도 plan, README 에 caveat 만 명시)
- Related work 의 새 인용 추가 (검증 불확실 항목은 "pending" 으로만 표기)
- README 의 Roadmap / Headline / H1~H9c 표 다른 부분 대대적 개편
- conceptFramework.md 의 4-axis 핵심 모델 변경 (포지션 보강만)
- math 카테고리 use_tools 정책 통일 (Exp11 후보, 별도 plan)
- logic 카테고리 multi-stage / 도구화 (Exp12 후보, 별도 plan)
- Exp00~09 v3 채점 적용 (logic-04 미포함 → 변동 0 예상, 별도 plan 우선순위 낮음)
- 새 H 가설 추가 (H10+) — 본 plan 범위 외
- requirements.txt 의 버전 pinning + lock file (별도 결정)

## 변경 이력

- 2026-04-29 v1: 초안. 외부 공개/재현 정리 + 직전 reviewer finding 해결.
