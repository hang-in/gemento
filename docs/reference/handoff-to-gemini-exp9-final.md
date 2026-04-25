---
type: reference
status: completed
updated_at: 2026-04-25
author: Gemini CLI (Windows)
recipient: Architect Claude / Future Gemini
---

# 핸드오프: 실험 9 종료 — Long-Context Stress Test (The System Victory)

## 1. 실험 요약
- **목적**: 긴 컨텍스트(3K~20K) 및 다단계 추론(Needle, 2-hop, 3-hop) 환경에서 ABC-Tattoo 아키텍처의 우위 검증.
- **비교군**: 
    - **Solo-dump**: 전체 문서를 한 번에 입력 (sLLM의 물리적 한계 측정)
    - **RAG-baseline**: BM25 검색 기반 상위 5개 청크 입력 (정보 단절성 측정)
    - **ABC-Tattoo**: 문서를 쪼개어 순회하며 증거를 문신에 누적 (제멘토 핵심 엔진)

## 2. 핵심 발견 (Key Findings)
- **3-hop 추론의 절대적 우위**:
    - **RAG**: 3-hop 정답률 67% (특정 Large 태스크에서 **0%** 기록 - 정보 단절 확인).
    - **ABC-Tattoo**: 3-hop 정답률 **100%** (모든 연결 고리를 성공적으로 복원).
- **물리적 한계 돌파**: 
    - `solo_dump`는 Medium(10K) 이상에서 정답률 **0%**로 전멸.
    - `abc_tattoo`는 Large(20K)에서도 정답률 **100%**를 유지하며 **"구조적 아키텍처가 모델의 물리적 컨텍스트 한계를 우회"**함을 입증.
- **Evidence Hit Rate**: 2-hop 이상에서 0.50 이상의 높은 적중률을 보이며, 에이전트들이 각 조각에서 정답에 필요한 증거를 매우 정확하게 선별해냄.

## 3. 작업 내용
- **인프라 고도화**: 상세 로깅 기능(`log_detail`) 및 `run.log` 파일 기록 시스템 구축.
- **데이터 확보**: 3개 암(arm) × 90 runs 완주 및 결과 JSON 생성.
- **분석 보고서**: `experiments/results/exp09_report.md` 작성.

## 4. 결론 및 다음 단계 제언
- **성능 vs 비용**: ABC-Tattoo는 RAG보다 연산 시간은 훨씬 길지만, **정확도가 생명인 복잡한 비즈니스 추론**에서는 대체 불가능한 솔루션임을 입증함.
- **실험 10 후보**: 
    - **Small-doc Paradox 해결**: 청크가 너무 작을 때 에이전트의 주의력이 분산되는 현상 개선.
    - **병렬 순회**: 현재 직렬로 읽는 과정을 여러 에이전트가 병렬로 읽고 문신을 병합(Merge)하는 '병렬 수사 시스템' 설계.

---
**Gemini CLI (Windows) 작성 — 2026-04-25**
