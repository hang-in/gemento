---
type: plan
status: abandoned
updated_at: 2026-04-25
slug: readme-memento-acknowledgement
---

# 오픈소스 좌표 선점 — README 한·영 + 연구노트 분할·종결 파트 영문화 + Memento Acknowledgement

## Description

실증·논문은 별도 트랙으로 두고, *MIT 라이선스 오픈소스 좌표 선점*을 위해 한국어/영어 문서를 정비. 외부(특히 영어권)가 제멘토를 *영어로* 인지·검증할 수 있는 단일 묶음을 만든다.

핵심 통찰:

- **연구노트의 종결된 부분(Exp00~09 결과, H1~H9 판정)은 변하지 않는다** → 거의 1:1 영문화가 가능하고 *정확*하다.
- **진행 중인 부분(열린 질문, 다음 실험 후보)은 계속 갱신된다** → 한국어만 유지.
- 따라서 연구노트를 두 파트로 *섹션 분할*하고, 영문판은 Closed 파트만 1:1 번역. 압축 학술 풍 권고는 철회 — 종결된 사실은 1:1이 정확성·신뢰 측면에서 더 강함.

Memento 영화 메타포는 origin story로 보존하고 Christopher Nolan 감독 acknowledgement를 명시한다. 이는 marketing이 아니라 *발생사(genesis story)* — 1인 연구의 가장 단단한 자산.

본 적 없는 외부 논문은 인용하지 않는다(직전 토론 결정). "Operating System" / "novel framework" / "AGI" 같은 과적재 명칭도 금지.

## Expected Outcome

- 한국어 `README.md`: 일관된 톤, 정확한 측정 숫자(H8 채택·H9 채택 동기화), secall/tunaflow에서 비롯한 origin, Memento 매핑, Nolan acknowledgement, MIT 라이선스 명시
- 신규 `README.en.md`: 영어권 청중에 맞춰 재구성된 first-person solo notebook 톤(1:1 번역 아님), 동일 측정 사실
- `docs/reference/researchNotebook.md`: **Part 1 Closed Findings**(line 1~686 내용) + **Part 2 Active Research**(line 689~ 내용) 두 섹션으로 명확히 분할, H1~H9 첫 등장 학술 주석 추가
- 신규 `docs/reference/researchNotebook.en.md`: Part 1만 거의 1:1 영문 번역 (압축 X)
- 두 README가 같은 사실을 가리키고, 두 연구노트의 Closed 파트도 동일

## Subtask Index

1. [task-01](./readme-memento-acknowledgement-task-01.md) — `README.md` 정확화 + Memento origin 보강 + Nolan acknowledgement (parallel_group A)
2. [task-02](./readme-memento-acknowledgement-task-02.md) — `README.en.md` 신규 작성 (parallel_group B, depends_on 01)
3. [task-03](./readme-memento-acknowledgement-task-03.md) — `researchNotebook.md` 분할·재구조화 + H1~H9 학술 주석 (parallel_group A)
4. [task-04](./readme-memento-acknowledgement-task-04.md) — `researchNotebook.en.md` 신규 작성 (Closed 파트만 1:1) (parallel_group B, depends_on 03)

## Constraints

- 측정 숫자(정답률, runs 수, hop별 결과)는 `docs/reference/researchNotebook.md`(한국어)를 *single source of truth* 로 참조
- 본 적 없는 외부 논문 인용 금지
- "Operating System" / "novel framework" / "AGI" 같은 과적재 명칭 금지
- Memento 메타포 + Nolan acknowledgement는 한·영 양쪽에 보존
- 한·영 README가 같은 사실을 가리켜야 함, 한·영 연구노트의 Closed 파트도 동일
- MIT License는 한·영 README 모두 명시 — 좌표 선점의 핵심 도구
- researchNotebook의 Closed 파트는 *추가만 허용·수정 금지* 원칙 명시
- 영문 연구노트는 Closed 파트만 — Active 파트는 영문화하지 않음(설계 결정)

## Non-goals

- 외부 채널 게시(HN, r/LocalLLaMA, Twitter) — 사용자 별도 결정
- 중국어/일본어 번역 — 1차 영어 반응 후 별도 결정
- arXiv 논문 작성 — 실증 트랙 진척 후 재논의
- secall / tunaflow / wiki 파서 실증 트랙 — 별도 plan
- Role Adapter Phase 1 구현 — 별도 plan(이미 작성됨)
- 시각적 디자인(스크린샷, 다이어그램 신규 제작) — 텍스트 정확화에 집중
- `researchNotebook.en.md`의 Part 2 (Active Research) 영문 번역 — 설계상 제외
- `conceptFramework.md` 영문판 — 본 plan 범위 밖 (필요 시 후속 plan)
- `researchNotebook`을 별도 파일로 물리 분할 — 한 파일에 두 섹션으로 충분

## Version

- v1 (2026-04-25): 초안. 압축 학술 풍 권고 → 사용자 revision으로 1:1 종결 파트 번역으로 변경.
