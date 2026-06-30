---
type: plan
status: draft
updated_at: 2026-06-30
slug: mandatory-tool-opt-in
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) 또는 Architect 직접 진행 + 사용자 검토
---

# Stage 8 — mandatory-tool 프롬프트 opt-in 편입 (안 A: caller-decides)

## Description

Exp16b/c (2026-06-30) 에서 mandatory-tool 프롬프트 — "반드시 `grep_context` 먼저 호출 / 다양한 패턴 / 'not found' 조기 단정 금지 / **매치 라인의 파일·라인·식별자를 그대로 final_answer 에 전사**" — 가 큰 로그 1-needle 의 e4b Context Router per-attempt 정답률을 **27%→83% (+57pp)** 끌어올렸다. 실패의 원인이 tool-neglect 가 아니라 **전사 누락**(grep 은 하지만 찾은 라인을 답으로 커밋 안 함)이었고, 규칙 4번이 그 단계를 잡았다.

단 Exp17 (hard task) 에서는 mandatory 가 **−3pp** (neutral~약간 음수) — baseline 이 이미 높은 추론 중심 task 에선 무효. 즉 mandatory 는 **범용 부스터가 아니라 failure-mode-specific (큰 로그 전사 누락) 처방**이다.

현재 mandatory 블록 텍스트는 실험 드라이버 (`run_v16b_mandatory.py` / `run_v16c_combined.py` / `run_v17_hardtasks.py`) 에 **복붙으로 흩어져** 있다. 본 plan 은 이를 **공유 코드의 opt-in 파라미터로 정식 편입**한다.

**핵심 결정 (안 A — caller-decides)**: 자동 임계 게이트는 만들지 않는다. 현 증거로는 신뢰할 신호가 없다 — 로그 크기가 신호가 아님 (Exp16b 12K baseline 20% < Exp17 23K baseline 75%, 역전). 따라서 `mandatory_tool_prompt: bool = False` 파라미터만 추가하고, **언제 켤지는 caller (또는 미래의 게이트 plan) 가 결정**한다. 기본 False → 기존 실험/Stage 6 거동 불변.

## Expected Outcome

1. `experiments/system_prompt.py` 에 canonical `MANDATORY_TOOL_RULES` 문자열 상수 (드라이버 3곳의 중복 제거 source-of-truth).
2. `experiments/orchestrator.py:run_abc_chain` 에 `mandatory_tool_prompt: bool = False` 파라미터 + True 일 때만 prompt 에 주입하는 로직 (error_blocks / extractor_pre_stage 와 동일 패턴, 같은 영역).
3. 회귀 게이트: default False 시 기존 거동이 byte-identical 임을 검증 (정적 + 선택적 tunnel A/B).
4. 문서: "언제 켜나" 가이드 (conceptFramework / README / 연구노트) + Stage 8 verdict 기록.
5. 드라이버 3곳은 새 source-of-truth 상수를 import 하도록 정리 (선택, behavior 불변).

## Subtask Index

1. **Task 01 — 코드: 상수 + 파라미터 + 주입 로직** (`system_prompt.py`, `orchestrator.py`). (M, parallel_group A, depends_on: [])
2. **Task 02 — 회귀 게이트 + opt-in 동작 검증** (`experiments/tests/`, tunnel A/B). (S, parallel_group B, depends_on: [01])
3. **Task 03 — 문서 + Stage 8 verdict** (conceptFramework / README / 연구노트 / index). (S, parallel_group C, depends_on: [01, 02])

### 의존성

```
Stage 8
  Group A: task-01 (code)
            │
  Group B: task-02 (regression + opt-in verify)
            │
  Group C: task-03 (docs + verdict)
```

순차 (A → B → C). 병렬 없음 — 코드가 먼저, 검증, 문서 순.

## Constraints

- **공유 코드 단일 경로 수정**: `run_abc_chain` 의 prompt 주입 영역만 (error_blocks 직후). 다른 경로 (A/B/C 호출, model_caller, search_tool, extractor/reducer) 변경 금지.
- **기본 False 불변식**: `mandatory_tool_prompt=False` (기본) 시 prompt / 거동이 변경 전과 **완전히 동일**해야 한다. Stage 6 cross_model 및 기존 exp 드라이버 영향 0.
- **자동 게이트 금지**: 본 plan 은 opt-in 파라미터까지만. log-size 휴리스틱/임계 코딩은 범위 밖 (별도 plan, 증거 필요).
- mandatory 블록 텍스트는 Exp16b/c 에서 검증된 4규칙 그대로 (임의 수정 금지 — 검증된 효과 보존).

## 결정 1 — 게이트 방식 — **안 A (opt-in 파라미터, caller-decides)** 확정
사용자 2026-06-30 결정. 자동 임계 게이트 (안 B) 및 신호 매핑 실험 선행 (안 C) 은 미채택 — 현 증거 부족.

## 결정 2 — mandatory 상수 위치 — **`system_prompt.py`** 확정 (Architect default)
역할 프롬프트가 모여 있는 곳. `MANDATORY_TOOL_RULES` 상수로 노출.

## 결정 3 — 회귀 검증 방식 — **정적 동치 + 선택적 tunnel A/B** 확정 (Architect default)
정적: `mandatory_tool_prompt=False` 시 빌드되는 prompt 가 변경 전과 동일함을 단위 테스트로 assert. 선택: cloud 터널로 mandatory=True 가 드라이버 주입 방식과 동일 결과 내는지 소규모 확인 (검증 실행은 cloud 라 Architect 가능).

## Non-goals

- 자동 (log-size) 게이트 / 임계 — 별도 plan.
- retry-on-None 의 공유 코드 편입 — 본 plan 은 mandatory 프롬프트만 (retry 는 드라이버 유지).
- mandatory 블록 텍스트 개선/실험 — 검증된 버전 보존.
- e2b / cross-model 적용.

## Risks

1. **기본 False 비불변** — 주입 로직이 False 경로에 영향 주면 전체 실험 회귀. → Task 02 정적 동치 테스트로 차단.
2. **드라이버 중복 제거 시 텍스트 drift** — 드라이버 상수와 새 상수가 미세 차이 시 Exp16b/c 재현 불가. → Task 01 에서 드라이버 블록과 새 상수 **문자 단위 일치** 확인 후 import 교체.
3. **주입 위치 충돌** — error_blocks / extractor 가 이미 prompt 를 수정. 순서/중복 주입 가능. → 단일 지점, 멱등 주입, 순서 명시.
4. **공유 코드 prompt 변경이 Stage 6 결과 해석 흔듦** — default False 면 영향 0 이나, 검증으로 재확인.

## Sonnet (Developer) 진행 가이드

본 plan 은 규모가 작아 Architect 직접 진행 가능. Sonnet 위임 시:

1. Plan 그대로. scope 확장 금지 (자동 게이트/ retry 편입 금지).
2. 결정 1~3 변경 금지.
3. Task 01 → 02 → 03 순차. 각 task: read → Step → Verification → commit → 사용자 confirm.
4. **기본 False 불변식**이 최우선 — Task 02 통과 전 Task 03 진행 금지.
5. 드라이버 블록과 새 상수 문자 단위 일치 확인 (Risk 2).
6. 검증 실행은 cloud 터널 (지인 서버 e4b) — 로컬 LLM 로딩 금지 (사용자 VRAM).
7. 영문 노트북 Closed-append-only / README 갱신은 사용자 결정.
8. Verification 실패 / Scope boundary 위반 직전 / Risk 발견 시 사용자 호출.

## 변경 이력

- 2026-06-30 v1: 초안. Exp17 결과 (mandatory = failure-mode-specific) 후 "router 기본값 무조건 승격" 대신 opt-in 파라미터 (안 A) 로 확정. 자동 게이트는 증거 부족으로 별도 plan 보류.
