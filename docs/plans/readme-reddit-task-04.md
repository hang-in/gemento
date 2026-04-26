---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: B
depends_on: [01]
---

# Task 04 — Related work 섹션 추가

## Changed files

- `README.md` (영문 메인) — **수정**. `## Acknowledgements` 직전에 `## Related work` 신규 섹션 추가.

신규 파일 0. README.ko.md 변경 0.

## Change description

### 배경

지피티 권고 섹션 매핑에서 영문 README 에 **Related work** 섹션이 누락. arXiv preprint 또는 학계 reviewer 에게 첫 인상에서 "이미 비슷한 연구가 있는데 왜 이게 다른가" 의 답이 명시되어야 한다.

이전 conversation 에서 정리된 4개 비교 대상:
- **Externalization** 프레임 (arXiv 2026-04-09 등장) — 본 프로젝트의 4축이 그 프레임의 한 구체화.
- **LightMem** — 메모리 외부화 연구.
- **ESAA** (Externally Stateful Agentic Architectures) — 상태 외부화.
- **Chain-of-Agents** — 역할 분리 패턴.

본 task 는 각 1줄 비교 + 본 프로젝트의 차별 위치 (정확도 검증 + 비용·재현성 데이터) 명시.

### Step 1 — 섹션 위치 확인

현재 영문 README 섹션 순서 (task-02·03 후 기준):
1. # Gemento
2. ## Why I built this
3. ## Core idea (task-03 신규)
4. ## What I measured
5. ## What worked / What didn't
6. ## Why this matters
7. ## Quickstart
8. ## Reproduce / Extend
9. ## Roadmap
10. ## How to Contribute
11. ## Acknowledgements   ← 여기 직전 삽입
12. ## License

### Step 2 — Related work 섹션 본문 작성

```markdown
## Related work

The "externalize the LLM" framing is not unique to this project. Adjacent or overlapping ideas:

- **Externalization frame** — A 2026-04 arXiv preprint¹ proposes a general framework for externalizing memory, reasoning, and verification away from the model. Gemento's four-axis split (Tattoo / Tools / Role / Orchestrator) is one concrete instantiation rather than a new theory.
- **LightMem**² — Long-term memory externalization for LLMs. Focused on retrieval and key-value memory; Gemento is closer to *working* state across loops, not retrieval against past sessions.
- **ESAA (Externally Stateful Agentic Architectures)**³ — Treats the agent as a state machine with external state. Conceptually adjacent; Gemento adds explicit role separation (A/B/C) and tool integration on top of the same idea.
- **Chain-of-Agents**⁴ — Sequentially passes a long input across multiple agents. Gemento's A→B→C pipeline shares this structure but uses *the same base model* for all roles, separated only by prompt and validation contract.

What is contributed here, and what is **not**:

- Contributed: a measured workbook of small-LLM (Gemma 4 E4B, 4.5B) behavior across the four axes, with reproducible numbers and sampling parameters.
- Not contributed: a new architecture, a new training method, or a claim that small LLMs replace large ones. Gemento is a structural workflow harness on top of an unmodified open-weight model.

---
¹ arXiv 2026-04-09 (preprint, externalization framework). Cited by handoff notes; not a direct comparison run in this repository.
² LightMem (long-term memory module for LLMs).
³ ESAA — Externally Stateful Agentic Architectures.
⁴ Chain-of-Agents — sequential multi-agent reading.
```

### Step 3 — Footnote 인용 형식

각 footnote 는 1줄 요약 + 직접 인용 안 함 (정확한 arXiv ID 미보유 — 본 task 는 placeholder). 향후 arXiv preprint 작성 시 정식 [Author, Year] BibTeX 인용으로 강화 — 본 plan 범위 밖.

### Step 4 — 차별 위치 (What is contributed) 명시

"a measured workbook ... with reproducible numbers and sampling parameters" 가 핵심 차별. SAMPLING_PARAMS 일원화 (이전 plan) 가 본 문장의 근거.

## Dependencies

- **task-01 완료** — README.md (영문) 가 메인 위치.
- task-02·03 와 동일 파일 → 순차 진행.
- 외부 패키지: 없음.

## Verification

```bash
# 1. ## Related work 섹션 존재
grep -E "^## Related work" /Users/d9ng/privateProject/gemento/README.md && echo "OK Related work section added"

# 2. 4 항목 키워드 모두 등장 (대소문자 무시)
cd /Users/d9ng/privateProject/gemento && grep -i "Externalization frame" README.md && \
grep -i "LightMem" README.md && \
grep -i "ESAA" README.md && \
grep -i "Chain-of-Agents" README.md && \
echo "OK 4 related work items mentioned"

# 3. "What is contributed" + "Not contributed" 둘 다 등장
cd /Users/d9ng/privateProject/gemento && grep -F "Contributed" README.md && grep -E "Not contributed|not contributed" README.md && echo "OK contribution boundary stated"

# 4. 섹션 순서 — Related work 가 Acknowledgements 직전
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
text = open('README.md', encoding='utf-8').read()
related_pos = text.find('## Related work')
ack_pos = text.find('## Acknowledgements')
license_pos = text.find('## License')
assert related_pos > 0, 'Related work section missing'
assert ack_pos > related_pos, 'Related work must come before Acknowledgements'
assert license_pos > ack_pos, 'License remains last'
print('OK section order: Related work < Acknowledgements < License')
"

# 5. footnote 4개 모두 등장 (¹²³⁴ 또는 [1]~[4])
cd /Users/d9ng/privateProject/gemento && grep -cE "[¹²³⁴]" README.md | grep -E "^[1-9][0-9]*$" && echo "OK footnotes present" || echo "WARN footnote markers may differ"

# 6. README.ko.md 미수정
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep "README.ko.md" && echo "FAIL README.ko.md modified" || echo "OK README.ko.md unchanged"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **footnote 의 정확성**: arXiv 2026-04-09 같은 placeholder 인용 — 정확한 paper ID·저자·제목 미보유. 본 task 의 footnote 는 "방향성 인용" 으로 acknowledgement 역할만. arXiv preprint 작성 시 정식 BibTeX 강화 (별도 plan).
- **claim 톤다운 위반**: "What is contributed" 단락에서 "small LLMs replace large ones" 같은 단정 회피 — "not contributed" 영역에 명시적으로 부재 선언.
- **외부 비교 부재**: Related work 항목들과 직접 비교 실험은 본 repo 에 없음. 본 task 의 Related work 는 conceptual mapping 만 — 실증 비교는 Exp12 (CoT/ReAct/Self-refine baseline) 등 별도 plan 의 영역.
- **footnote 형식 — Markdown vs HTML**: `¹²³⁴` 유니코드 superscript 는 Reddit·GitHub 모두 렌더 OK. 단 `[1]` 같은 footnote 마커가 표준 markdown 호환성 더 좋음. 현재 spec 은 superscript — 호환성 우려 시 `[1]~[4]` 로 변경 가능 (본 task 자유 재량).

## Scope boundary

**Task 04 에서 절대 수정 금지**:

- README.md 의 기존 섹션 (Why I built this, Core idea, What I measured, Quickstart, Acknowledgements 등).
- README.md 의 첫 문장 (task-02 결과물).
- README.md 의 Core idea 표 (task-03 결과물).
- README.ko.md.
- `docs/` 의 모든 파일.
- `experiments/` 의 모든 파일.

**허용 범위**:

- README.md 에 `## Related work` 섹션 신규 추가 (How to Contribute 다음, Acknowledgements 직전).
- 본 섹션은 4 bullet (Externalization / LightMem / ESAA / Chain-of-Agents) + Contributed/Not contributed 구분 + 4 footnote. ~25 줄 신규.
