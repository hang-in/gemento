---
type: plan
status: in_progress
updated_at: 2026-04-26
slug: readme-reddit
version: 1
---

# README 영문 메인 전환 + Reddit 공개 톤 정정

## Description

레딧 (r/LocalLLaMA, r/MachineLearning, r/opensource) 공개를 위해 현재 한국어 메인 `README.md` (339 줄) 와 영문 보조 `README.en.md` (160 줄) 의 역할을 swap 한다. 단순 swap 만으로는 부족하고, 영문 README 의 톤·섹션 구조를 외부 검토자가 첫 화면에서 빠르게 판단할 수 있게 정정한다.

핵심 변경 4가지:
1. 파일 swap — `README.md` ↔ `README.en.md` (`git mv` 로 history 보존).
2. 영문 README 톤 정정 — claim inflation 방지 ("Externalize the limits of small LLMs..." → "Gemento is an experimental harness, not a new architecture or a paper. It tests whether small local LLMs can run long workflows when memory, tools, roles, and control are externalized.", "proves" → "experiments suggest").
3. 누락 섹션 3개 추가 — Core idea (4축 명시), Related work (Externalization 프레임 인용), Research notes (한국어 README + researchNotebook 등 docs 링크).
4. 내부 링크 정정 — `README.md ↔ README.ko.md` cross-link.

상위 목표: arXiv preprint v1 timeline 의 외부 노출 첫 단계 (레딧 공개) 에서 첫 화면 이탈률 최소화 + 학술 톤 유지.

## Expected Outcome

1. `README.md` — 영문 메인 (구 README.en.md 내용 + 톤 정정 + 누락 섹션 3개). 약 200~250 줄.
2. `README.ko.md` — 한국어 (구 README.md 본문 그대로 + 영문 README 링크만 정정).
3. `README.en.md` — 삭제 (README.md 로 흡수, `git mv` history 추적 가능).
4. 내부 링크 모두 정확 (broken link 0건).
5. README 양쪽에서 cross-link 작동 (`README.md` ↔ `README.ko.md`).
6. Reddit 첫 화면 후크 — 첫 문장 (서술형) + Results 표 (H1·H7·H9a 핵심) + "Not a claim" 명시 가시화.
7. claim inflation 단어 ("proves", "beats", "conquers" 등) README.md 본문 0건.

## Subtask Index

1. [task-01](./readme-reddit-task-01.md) — README 파일 swap (git mv) (parallel_group A, depends_on: [])
2. [task-02](./readme-reddit-task-02.md) — 영문 README 톤 정정 (parallel_group B, depends_on: [01])
3. [task-03](./readme-reddit-task-03.md) — Core idea 섹션 추가 (parallel_group B, depends_on: [01])
4. [task-04](./readme-reddit-task-04.md) — Related work 섹션 추가 (parallel_group B, depends_on: [01])
5. [task-05](./readme-reddit-task-05.md) — Research notes / Docs Map 섹션 추가 (parallel_group B, depends_on: [01])
6. [task-06](./readme-reddit-task-06.md) — 내부 링크 정정 (parallel_group B, depends_on: [01])
7. [task-07](./readme-reddit-task-07.md) — broken link 정적 검증 (parallel_group C, depends_on: [01, 02, 03, 04, 05, 06])

### 의존성 (Stage 기반)

```
Stage 1 (단독):
  task-01 (README swap)
       │
       ▼
Stage 2 (sequential 권고 — 동일 파일 README.md 동시 편집 위험):
  task-02 (톤 정정)
  task-03 (Core idea 섹션 추가)
  task-04 (Related work 섹션 추가)
  task-05 (Research notes 섹션 추가)
  task-06 (내부 링크 정정)
       │
       ▼
Stage 3 (단독):
  task-07 (broken link 정적 검증)
```

- 모든 Stage 2 task 가 README.md 단일 파일을 수정하므로 **순차 진행 권고**. parallel_group="B" 표기는 "task-01 후 시작 가능" 의미. Developer 는 본 plan 의 task-02 → 03 → 04 → 05 → 06 순으로 진행.
- task-06 (링크 정정) 만 `README.ko.md` 도 수정 — 다른 task 와 별개 영역이므로 순서 유연.
- task-07 은 모든 변경 후 단독 검증.

## Constraints

- **git history 보존**: rename 시 `git mv` 사용 (cp + rm 금지). file blame 추적 가능해야 함.
- **수치·verdict 변경 금지**: H1~H9c 결과 표의 정량 수치 (94.4%, 80%, +44.4pp 등) + verdict (Supported / Rejected / Conditionally supported) 변경 금지. 톤 단어만 정정.
- **Acknowledgements/License 보존**: Memento (Christopher Nolan, 2000) + secall · tunaflow + MIT 모두 그대로.
- **README.ko.md 본문 미수정**: 한국어 README 는 단순 rename + 영문 링크 정정만. 한국어 본문 변경 금지 (한국어 사용자 경험 유지).
- **arXiv timeline 의식**: 본 plan 은 ~1일 작업. probe 회신과 병행 가능.
- **Reviewer 가드**: LLM 호출 0. 정적 검증만 (broken link, claim word grep 등).
- **동일 파일 동시 편집 방지**: Stage 2 task 들이 README.md 를 수정 — 순차 진행 강제.

## Non-goals

- README 구조의 전면 재작성 — 현재 README.en.md 가 충실하므로 점진 정정.
- researchNotebook.md / .en.md 추가 변경 — 별도 plan.
- README.ko.md 한국어 본문 정정 — 한국어 사용자 경험 유지.
- arXiv 부록 작성 — 별도 큰 plan (probe 회신 후).
- Quickstart 의 코드 변경 (실제 동작 점검) — 본 plan 은 문서 작업.
- 신규 docs 파일 생성 — 본 plan 은 README 영역 만 손댐.

## 변경 이력

- 2026-04-26 v1: 초안. swap + 톤 정정 + 누락 섹션 3개 추가 + 링크 정정 + 검증.
