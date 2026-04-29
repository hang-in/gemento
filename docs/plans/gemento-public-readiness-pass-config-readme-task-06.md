---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: gemento-public-readiness-pass-config-readme
parallel_group: B
depends_on: [05]
---

# Task 06 — README Related work 각주 정리 한·영

## Changed files

- `README.md` — **수정**. line 178~196 부근 Related work 섹션. 4 footnote (Externalization frame¹ / LightMem² / ESAA³ / Chain-of-Agents⁴) 의 서지 검증, 검증 불확실 항목은 "citation pending — needs bibliographic verification" 표시.
- `README.ko.md` — **수정**. 한국어판에 Related work 섹션이 있으면 동기화. 없으면 신규 추가 (영문판 동일 사실).

신규 파일 0.

## Change description

### 배경

`README.md:178~196` 의 Related work 섹션 (정찰 결과):

```markdown
## Related work

- **Externalization frame** — A 2026-04 arXiv preprint¹ proposes a general framework for externalizing memory, reasoning, and verification away from the model. Gemento was developed independently — out of practical context/memory problems hit while building secall and tunaFlow — and only later did the author become aware of this preprint. The four-axis split (Tattoo / Tools / Role / Orchestrator) is best read as **independent convergence** with that line of work, not as a derivation from it.
- **LightMem**² — Long-term memory externalization for LLMs. Focused on retrieval and key-value memory; Gemento is closer to *working* state across loops, not retrieval against past sessions.
- **ESAA (Externally Stateful Agentic Architectures)**³ — Treats the agent as a state machine with external state. Conceptually adjacent; Gemento adds explicit role separation (A/B/C) and tool integration on top of the same idea.
- **Chain-of-Agents**⁴ — Sequentially passes a long input across multiple agents. Gemento's A→B→C pipeline shares this structure but uses *the same base model* for all roles, separated only by prompt and validation contract.

¹ A 2026-04 arXiv preprint on externalization frame for LLM agents.
² LightMem (long-term memory module for LLMs).
³ ESAA — Externally Stateful Agentic Architectures.
⁴ Chain-of-Agents — sequential multi-agent reading.
```

문제:
- 4 footnote 모두 서지 정보 (저자, 정확한 제목, arXiv ID, DOI, URL) 없음 — 가짜 인용처럼 보일 위험
- 사용자 정책: "본 적 없는 외부 논문 인용 금지", "검증 불확실 항목은 citation pending"
- 한국어 README 에는 Related work 섹션 자체가 없음 (정찰 grep 결과 0) — 신규 추가 또는 영문판 link

### Step 1 — 4 footnote 서지 상태 점검

각 항목별:

| 항목 | 사용자 인지 상태 | 처리 |
|------|----------------|------|
| Externalization frame (2026-04 arXiv preprint) | 사용자 본 적 없음 (직전 conversation 명시) | "citation pending — author has not directly verified the preprint; reference is the GPT-discovered framing only" |
| LightMem | 서지 미확인 | "citation pending — needs bibliographic verification" |
| ESAA | 서지 미확인 | "citation pending — needs bibliographic verification" |
| Chain-of-Agents | 일반적으로 알려진 multi-agent 방법론, 정확한 인용 미확인 | "citation pending — needs bibliographic verification" |

### Step 2 — README.md Related work 섹션 footnote 갱신

기존 footnote 4개를 다음 패턴으로 변경:

```markdown
¹ A 2026-04 arXiv preprint on externalization frame for LLM agents — *citation pending; author has not directly verified the preprint, reference is the GPT-discovered framing only*.
² LightMem (long-term memory module for LLMs) — *citation pending; needs bibliographic verification*.
³ ESAA — Externally Stateful Agentic Architectures — *citation pending; needs bibliographic verification*.
⁴ Chain-of-Agents — sequential multi-agent reading — *citation pending; needs bibliographic verification*.
```

요구사항:
- 4 footnote 모두 "citation pending" 명시 (italic 권장)
- "Externalization frame" 항목은 사용자 직접 진술 ("author has not directly verified") 추가
- "Gemento was developed independently" 본문 표현 보존 (사용자 정책 — 독창성 표현 유지)

### Step 3 — README.ko.md Related work 섹션 추가 또는 동기화

`README.ko.md` 에 Related work 섹션이 있는지 grep 으로 재확인:

```bash
grep -n "## Related work\|## 관련 연구\|## Related Work" README.ko.md
```

**Case A**: 한국어 README 에 Related work 섹션 없음
→ 신규 추가 (영문판 동일 위치에). 한국어 표현으로 4 항목 + 4 footnote.

**Case B**: 이미 있음
→ 영문판과 동일 사실 동기화.

한국어 footnote 예시:
```markdown
¹ 2026-04 arXiv preprint (외부화 frame for LLM agents) — *서지 검증 미완 (citation pending); 저자가 직접 확인하지 않았으며, GPT 가 제시한 framing 만 참조함*.
² LightMem (LLM 장기 기억 모듈) — *서지 검증 미완 (citation pending)*.
³ ESAA — Externally Stateful Agentic Architectures — *서지 검증 미완 (citation pending)*.
⁴ Chain-of-Agents — sequential multi-agent reading — *서지 검증 미완 (citation pending)*.
```

### Step 4 — "Gemento was developed independently" / "독립적으로 개발됨" 표현 보존

본 task 는 footnote 의 검증 상태만 명시. 본문의 "independent convergence" / "독립 개발" 표현은 사용자 정책상 유지 — 변경 0.

### Step 5 — 새 인용 추가 금지

본 task 는 검증 불확실 항목을 "pending" 으로 표기만. 새 논문 인용 추가 또는 footnote 수 증가 금지.

## Dependencies

- Task 05 — Group B 의 직전 task (직렬). Task 05 가 README 두 파일 다른 영역 수정 완료 후 본 task 진행.
- 패키지: 없음 (마크다운 편집)

## Verification

```bash
# 1) README.md 의 4 footnote 모두 "citation pending" 표기
grep -c "citation pending" README.md
# 기대: 4 이상

# 2) README.md 의 Externalization frame footnote 가 "author has not directly verified" 표기
grep "author has not directly verified" README.md
# 기대: 1 라인

# 3) README.ko.md 의 Related work 섹션 존재 (Case A or B)
grep -E "## Related work|## 관련 연구" README.ko.md
# 기대: 1 라인

# 4) README.ko.md 의 4 항목 모두 "서지 검증 미완" / "citation pending" 표기
grep -c "citation pending\|서지 검증 미완" README.ko.md
# 기대: 4 이상

# 5) "independent convergence" / "독립 개발" 표현 보존
grep "independent convergence\|독립" README.md README.ko.md | head -5
# 기대: 1+ 라인 (사용자 정책 보존)

# 6) 새 인용 추가 금지 — footnote 카운트 영문판 4 유지
grep -c "^¹\|^²\|^³\|^⁴" README.md
# 기대: 4 (footnote 4개 유지, 5개 이상 추가 안 됨)

# 7) 한·영 동기화 — 동일 사실 4 항목
.venv/bin/python -c "
en = open('README.md').read()
ko = open('README.ko.md').read()
for keyword in ('Externalization frame', 'LightMem', 'ESAA', 'Chain-of-Agents'):
    assert keyword in en, f'README.md missing {keyword}'
    assert keyword in ko, f'README.ko.md missing {keyword}'
print('한·영 Related work 4 항목 동기화 ok')
"
```

7 명령 모두 정상.

## Risks

- **새 인용 추가 유혹**: footnote 정리 중 "차라리 정확한 인용 추가하자" 충동 위험. 본 task 정책: 검증 불확실 항목을 "pending" 으로만. 새 인용 추가는 별도 plan (외부 논문 직접 확인 후).
- **한국어판 위치 결정**: Case A 일 때 신규 추가 위치는 영문판 동일 위치 (Why this matters / Roadmap 등 인접 섹션). 한국어 README 의 섹션 순서가 영문판과 다를 수 있음 — grep 으로 영문판 인접 섹션 위치 확인 후 결정.
- **footnote ¹²³⁴ 유니코드 문자**: 한국어 README 에서 동일 유니코드 superscript 사용. 입력 환경에 따라 깨질 위험 — 확인 후 동일 유지.
- **"GPT-discovered framing" 표현**: 사용자 직접 진술 ("본 적 없음, GPT 가 알려준 framing") 의 정확한 표현 — README 외부 노출이라 너무 캐주얼한 톤은 회피, 그러나 정직성 우선.
- **"independent convergence" 표현 유지**: 사용자 정책상 유지 — 본 task 가 이걸 약화시키면 안 됨. footnote 의 "pending" 표기와 본문의 "independent convergence" 가 양립 (footnote = 인용 검증 상태, 본문 = 개발 경위).

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `README.md` 의 H 표 / Headline / What this is / is not / Roadmap — Task 04/05 영역 또는 직전 plan 영역
- `README.ko.md` 의 H 표 / What this is / is not / Roadmap — Task 04/05 영역
- `experiments/config.py` / `requirements.txt` / `docs/reference/conceptFramework.md` / `experiments/exp10_reproducibility_cost/INDEX.md` — Task 01/02/03 영역
- `docs/reference/researchNotebook.md` / `.en.md` — 직전 plan 영역
- `docs/reference/results/exp-10-reproducibility-cost.md` — 직전 plan 영역
- 본문의 "Gemento was developed independently" / "independent convergence" 등 사용자 정책 표현 — footnote 만 변경, 본문 변경 0
- 새 외부 논문 인용 추가 — 본 task 는 기존 4 footnote 정리만
