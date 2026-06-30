---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: mandatory-tool-opt-in
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — 문서 + Stage 8 verdict

## Changed files

- `docs/reference/conceptFramework.md` (수정) — Orchestrator 축 / Critic Tool 인근에 `mandatory_tool_prompt` opt-in 언급 + "언제 켜나" 가이드.
- `docs/reference/researchNotebook.md` (수정) — Stage 8 항목 (가설표는 신규 H 아님 — H16b/c 의 운영화이므로 Exp 섹션 없이 짧은 운영 노트). verdict-record 스킬로 처리 가능.
- `docs/reference/researchNotebook.en.md` (수정, **append-only**) — 동일 운영 노트 영문 (Change History 위 append).
- `README.md` / `README.ko.md` (수정) — "Adding/using mandatory prompt" 한 줄 가이드 (Running other models 또는 Adding a Role 인근).
- `docs/plans/index.md` (수정) — Active → Recently Done 이동 (verdict-record 스킬 담당).

> 수정 5 (신규 0).

## Change description

### 배경
opt-in 파라미터는 신규 가설이 아니라 H16b/c 의 **운영화(productionization)**. 따라서 새 H 번호 없이 "운영 노트"로 기록하고, "언제 켜나" 가이드를 사용자/기여자가 볼 수 있게 한다.

### Step 1 — "언제 켜나" 가이드 (핵심 메시지)
모든 문서에서 일관:
- **ON**: 큰 로그 (모델 용량 근접/초과) + 1-needle 류 retrieval (전사 누락 실패 모드). Exp16b/c 에서 per-attempt 27→83%.
- **OFF (기본)**: 작은 입력, 추론 중심 multi-hop/집계 task. Exp17 에서 −3pp (failure-mode-specific).
- 자동 게이트 아님 — caller 가 입력 성격으로 판단.

### Step 2 — conceptFramework Orchestrator 축에 1단락 추가
`run_abc_chain(mandatory_tool_prompt=True)` 가 출력 안정화(전사 커밋)를 강제하는 opt-in 임을 명시. failure-mode-specific 임을 강조.

### Step 3 — 연구노트 Stage 8 운영 노트 (ko + en)
짧은 운영 노트: "mandatory 프롬프트를 run_abc_chain opt-in 으로 편입 (안 A). 검증된 4규칙을 system_prompt.MANDATORY_TOOL_RULES 로 source-of-truth 화. 기본 False." en 은 append-only.

### Step 4 — README 양쪽 한 줄
"Adding a Role" 또는 "Running other models" 인근에: "large-log retrieval 시 `mandatory_tool_prompt=True` 로 출력 안정화 (Exp16b/c). 추론 중심 task 엔 끄라 (Exp17)."

### Step 5 — index.md Active → Recently Done
`gemento-verdict-record` 스킬로 처리 (Stage 8 마감).

## Dependencies
- Task 01, 02 완료 (코드 + 검증).
- verdict-record 스킬 (Step 3, 5).

## Verification

```bash
# 1. 문서 링크/참조 깨짐 없음 (수동 grep)
grep -rn "mandatory_tool_prompt" docs/ | head
```

```bash
# 2. en 노트북 append-only 무결성 (표 row 수 / 기존 섹션 불변)
D:/privateProject/gemento/.venv/Scripts/python.exe -c "t=open('docs/reference/researchNotebook.en.md',encoding='utf-8').read(); print('Change History present:', t.count('## Change History')==1)"
```

## Risks
1. **신규 H 번호 오용** — opt-in 은 운영화지 신규 가설 아님. H18 등 부여 금지 (H16b/c 운영 노트로).
2. **en append-only 위반** — Step 3 영문은 Change History 위 append 만. 기존 entry 수정 금지.
3. **README 과장** — "mandatory 가 항상 좋다"로 읽히지 않게 Exp17 caveat (failure-mode-specific) 병기.

## Scope boundary
**수정 금지**: 코드 (`*.py`), 결과 JSON. 문서만. en 노트북은 append-only.
