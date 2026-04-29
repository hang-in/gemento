# gemento — Agent Instructions

> This file defines project-level rules for all agents in tunaFlow.
> All agents (Claude, Gemini, Codex, OpenCode) must follow these rules.

---

## 1. Project Overview

- Name: gemento
- Status: active
- Language: Python
- Stack: Python

> Auto-detected by tunaFlow. Verify and adjust if needed.

---

## 2. File Storage Rules

**All documents and artifacts must be created within this project directory.**

- Do NOT create files in `~/.claude/`, `~/.gemini/`, or any external path
- Plans: `docs/plans/`
- Reference docs: `docs/reference/`
- Prompts: `docs/prompts/`
- Code: follow project structure

---

## 3. Documentation Rules

### File Naming
- Short, 2-4 core tokens (camelCase)
- Reference: stable names without dates (e.g., `implementationStatus.md`)
- Plan: `featureNamePlan.md` or `featureNamePlan_YYYY-MM-DD.md`
- Prompt: `docs/prompts/YYYY-MM-DD/short_name.md`

### Document Metadata
- Top of every document: `type`, `status`, `updated_at`
- Status values: `draft` → `in_progress` → `done` → `archived`
- Reference docs: update same file (no date-based duplication)
- Plans/prompts: new documents per task allowed (must update index.md)

### Versioning
- Use `status: archived` + `superseded_by` instead of deletion
- Brainstorm/comparison docs: mark `canonical: false`

---

## 4. Coding Rules

### Language
- Respond in the language the user uses (match user's message language)
- Code, paths, identifiers: keep in original language

### Code Quality
- Only modify what was requested. Do not clean up surrounding code
- Error handling: minimize silent fallbacks during development
- No speculative abstractions or future-proofing
- Modify one path at a time → verify → proceed to next

### Testing
- Verify existing tests pass after changes
- Consider unit tests for new logic

---

## 5. Work Safety Rules

- **Verify replacement works** before removing existing functionality
- **Confirm before destructive operations** (file deletion, schema changes)
- **Single-path modification** — never change multiple execution paths simultaneously
- Check all consumers before modifying shared state

---

## 6. Agent Behavior Rules

- **Plan before implementing** — present your plan and wait for user approval before writing code
- Introduce yourself by profile name first, then engine. No mixed expressions
- Do not claim ownership of other agents' messages
- Respond in the user's language
- Lead with conclusions, then reasoning

---

## 7. Current Status

### Completed
- 핵심 개념 정의 (RT 토론: 상태 전이 시스템, 문신 규약)
- 문신 스키마 설계 (schema.py)
- 오케스트레이터 구현 (orchestrator.py)
- 시스템 프롬프트 설계 (system_prompt.py)
- 실험 설계서 작성 (docs/reference/experimentDesign.md)
- 실험 인프라 구축 (experiments/)
- 평가 태스크셋 작성 (6개 태스크, 3 카테고리)
- 측정/채점 스크립트 (measure.py)
- 결과 문서 템플릿 (docs/reference/results/)

### In Progress
- 실험 0-4 실행 대기 (브랜치별 분기 실행 예정)

### Known Issues
- Python 환경: PEP 668 제한으로 venv 필수 (.venv/)
- 실험 4 (도구 분리): 실험 2 결과 이후 구현 완성 예정
- 채점: v0은 단순 포함 기반, 향후 LLM 기반 채점 검토 필요

---

## 8. Next Priorities

1. 실험 0 실행 (exp/00-baseline) — Baseline 측정
2. 실험 1 실행 (exp/01-assertion-cap) — Soft cap 확정
3. 실험 2 실행 (exp/02-multiloop-quality) — H1 검증
4. 실험 3, 4 병렬 실행 — H2 검증 + 도구 통합

## 9. Tech Stack

- 타겟 모델: Gemma 4 E4B (Ollama `gemma4:e4b`, Q4_K_M)
- 언어: Python 3.14
- 의존성: httpx
- 환경: .venv/ (venv)
