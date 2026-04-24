---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: plan
parallel_group: B
depends_on: [01]
---

# Task 02 — researchNotebook 가설 표 재부호화

## Changed files

- `docs/reference/researchNotebook.md`
  - 파일 헤더(line 1~5) 바로 아래에 conceptFramework.md로의 참조 1줄 삽입
  - **핵심 가설 표(line 26~34)만** 수정 — 헤더 1열 이름 변경 + 각 가설에 축 prefix 추가
  - 가설 표 **직후**(line 34 뒤)에 새 subsection "#### 축 ↔ 실험 매트릭스" 추가 (4축 × 9개 실험 2D 표)
  - "### 열린 질문"(line 528 근처) 마지막 항목으로 "11. 미외부화 축 보강" 1줄 추가

## Change description

### Step 1 — 헤더에 conceptFramework.md 링크 삽입

기존:
```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-24
---

# 제멘토 연구 노트 (Research Notebook)
```

수정 후 (frontmatter 바로 아래, `#` 제목 위에 추가):
```markdown
---
type: reference
status: in_progress
updated_at: 2026-04-24
---

> **개념 프레임 canonical 문서**: [conceptFramework.md](./conceptFramework.md) — 4축 외부화 원리, 용어 정의, 축 ↔ 실험 매핑.

# 제멘토 연구 노트 (Research Notebook)
```

### Step 2 — 핵심 가설 표 재부호화

**원본 표(line 26~34)**:
```markdown
| ID | 가설 | 최종 판정 | 판정 실험 |
|----|------|----------|----------|
| H1 | 다단계 루프가 단일 추론보다 품질이 높다 | **채택** | Exp02 |
| H2 | 오류가 루프를 거치며 증폭된다 | **기각** (오류 무감지) | Exp03 |
| H3 | 교차 검증(역할 분리)이 오류를 감지할 수 있다 | **채택** (80%) | Exp035 |
| H4 | A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | **채택** (+22.6%p) | Exp06 |
| H5 | MAX_CYCLES 상향이 정답률 향상에 기여한다 (루프 포화점 존재) | **부분 기각** (상한 확장 무효, actual_cycles≈7에서 포화) | Exp07 |
| H6 | Phase별 특화 프롬프트가 baseline 대비 우수하다 | **조건부 채택** (장기 루프 15~20에서 +5~6%p) | Exp07 |
| H7 | 외부 수학 도구(calculator/linalg/linprog)가 E4B의 계산 한계를 보완한다 | **채택** (+18.3%p, math-04 0→80%) | Exp08 |
```

**교체본** — 1열 헤더 이름만 변경, 각 가설에 축 prefix `[X 외부화]` 추가. 판정·근거 실험은 불변:

```markdown
| ID | 가설 (외부화 축) | 최종 판정 | 판정 실험 |
|----|------------------|----------|----------|
| H1 | **[Orchestrator 외부화]** 다단계 루프가 단일 추론보다 품질이 높다 | **채택** | Exp02 |
| H2 | **[Role 외부화 필요성 반증]** 오류가 루프를 거치며 증폭된다 | **기각** (오류 무감지) | Exp03 |
| H3 | **[Role 외부화]** 교차 검증(역할 분리)이 오류를 감지할 수 있다 | **채택** (80%) | Exp035 |
| H4 | **[Role 외부화 시너지]** A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | **채택** (+22.6%p) | Exp06 |
| H5 | **[Orchestrator 상한 효과]** MAX_CYCLES 상향이 정답률 향상에 기여한다 (루프 포화점 존재) | **부분 기각** (상한 확장 무효, actual_cycles≈7에서 포화) | Exp07 |
| H6 | **[Role 외부화 정교화]** Phase별 특화 프롬프트가 baseline 대비 우수하다 | **조건부 채택** (장기 루프 15~20에서 +5~6%p) | Exp07 |
| H7 | **[Tool 외부화]** 외부 수학 도구(calculator/linalg/linprog)가 E4B의 계산 한계를 보완한다 | **채택** (+18.3%p, math-04 0→80%) | Exp08 |
```

**주의**: `H8`은 기존 표에 **없음**(섹션은 최신 갱신에 포함되지 않았을 수 있음). 기존 표에 H8이 누락된 상태라면 추가 금지 — 판정·근거 실험 불변 원칙은 "기존 데이터를 바꾸지 않는다"이지 "새 행을 추가한다"가 아니다. 만약 현재 파일에 H8이 이미 있다면 함께 prefix만 추가.

검증 명령:
```bash
grep -n "^| H[0-9]" docs/reference/researchNotebook.md | head -10
```
현재 파일에 H1~H7만 있는지 H1~H8까지 있는지 확인 후, 있는 행 전부에 축 prefix 적용. 

**외부화 축 할당 근거**:
- H1 Orchestrator: Exp02 v1(모델 자율 0%)→v2(Python 강제 94.4%)가 phase 전이 외부화의 효과를 입증.
- H2 Role 반증: 자가 검증이 불가함을 보여 Role 외부화의 필요성을 역으로 제시.
- H3 Role: 같은 E4B 모델이 prompt 역할 분리로 교차 검증 80% 달성.
- H4 Role 시너지: ABC 3역할 분리가 Solo 대비 +22.6%p.
- H5 Orchestrator 상한: MAX_CYCLES는 "Python Orchestrator 안전장치"의 파라미터. 상한 상향의 한계는 결정론적 제어의 한계를 보임.
- H6 Role 정교화: phase별 prompt 분기는 Role 외부화의 세부.
- H7 Tool: 외부 도구 주입이 계산 한계 보완.
- H8이 존재한다면: "[Tool 외부화 안정성]" 또는 "[Tool + Role 외부화 협력]"으로 할당 후보. 실제 행이 있으면 판정되면 적절 라벨 사용.

### Step 3 — "축 ↔ 실험 매트릭스" subsection 추가

가설 표 직후(line 35의 `---` 구분선 앞)에 신규 subsection 추가:

```markdown
#### 축 ↔ 실험 매트릭스

각 실험이 4개 외부화 축 중 어느 축(들)을 검증했는지의 2D 매트릭스. ✅ = 주 검증, ▶ = 간접 관련, — = 해당 없음.

| 실험 | Tattoo | Tool | Role Agent | Orchestrator |
|------|:------:|:----:|:----------:|:------------:|
| Exp00 (Baseline) | — | — | — | — |
| Exp01 (Assertion Cap) | ✅ | — | — | — |
| Exp02 v2 (Multiloop) | ▶ | — | — | ✅ |
| Exp03 (Error Propagation) | — | — | ✅ (반증) | — |
| Exp035 (Cross Validation) | — | — | ✅ | — |
| Exp04 (A-B-C Pipeline) | ▶ | — | ✅ | ✅ (Judge Role) |
| Exp045 (Handoff Protocol) | ✅ | — | ▶ | — |
| Exp05b (Hard Tasks) | ✅ | — | ✅ | — |
| Exp06 (Solo Budget) | — | — | ✅ | — |
| Exp07 (Loop Saturation) | — | — | ▶ | ✅ |
| Exp08 (Math Tool-Use) | — | ✅ | ▶ | — |
| Exp08b (Tool Refinement) | — | ✅ | — | — |

> 자세한 정의는 [conceptFramework.md § 2](./conceptFramework.md)의 4축 정의 참조.
```

### Step 4 — "열린 질문" 섹션에 항목 11 추가

기존 "### 열린 질문"(파일 line 528 근처) 목록의 마지막에 신규 항목 1줄:

```markdown
11. **미외부화 축 보강** — 현재 검증된 4축(Tattoo/Tool/Role/Orchestrator) 외 확장 후보: **Extractor**(원문→claim), **Reducer**(chunk→일일), **Search Tool**(BM25/vector), **Graph Tool**(relation traversal), **Evidence Tool**(evidence_ref resolve), **Critic Tool**(schema·citation 결정론적 검증). 자세한 목록은 [conceptFramework.md § 9](./conceptFramework.md) 참조.
```

기존 1~10번 항목은 **그대로 유지**. 삭제·순서 변경 금지.

### 수정하지 않는 부분

- Exp00~Exp08 각 실험의 상세 기록 섹션(line 37~518 근처): 터치 금지. 축 라벨을 각 실험 설명에 삽입하는 것도 본 Task 범위 외.
- "### 채점 시스템 변천", "### 완료된 보조 작업" 등 다른 섹션: 터치 금지.
- 프로젝트 개요 표의 "핵심 질문" 문구: 유지.

## Dependencies

- **Task 01 완료**: `docs/reference/conceptFramework.md`가 존재해야 Step 1의 링크가 유효. 없으면 dead link.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. conceptFramework.md 링크 헤더에 삽입됨
head -10 docs/reference/researchNotebook.md | grep -c "conceptFramework.md"
# 기대: 1

# 2. 가설 표 헤더 변경 확인
grep "^| ID | 가설 (외부화 축) | 최종 판정 | 판정 실험 |" docs/reference/researchNotebook.md
# 기대: 매칭 라인 1개 출력

# 3. H1~H7(또는 H8) 각 행에 "[" + "외부화" 패턴 포함 (축 prefix 확인)
grep -cE "^\| H[0-9]+ \| \*\*\[.*외부화" docs/reference/researchNotebook.md
# 기대: 7 이상 (H1~H7 최소)

# 4. "축 ↔ 실험 매트릭스" subsection 존재
grep -c "#### 축 ↔ 실험 매트릭스" docs/reference/researchNotebook.md
# 기대: 1

# 5. 매트릭스 표가 12개 이상의 실험 행 포함 (Exp00 ~ Exp08b)
grep -cE "^\| Exp0[0-9]" docs/reference/researchNotebook.md
# 기대: 12 이상 (baseline, 01, 02, 03, 035, 04, 045, 05b, 06, 07, 08, 08b)

# 6. 열린 질문 11번 항목 추가
grep -c "11\. \*\*미외부화 축 보강\*\*" docs/reference/researchNotebook.md
# 기대: 1

# 7. 기존 1~10번 질문 항목 보존
grep -cE "^[0-9]+\. \*\*" docs/reference/researchNotebook.md
# 기대: 11 이상 (기존 10 + 신규 1)

# 8. 기존 실험 기록 섹션 보존 — 축 라벨이 실험 기록 섹션 본문에 침투하지 않았는지
grep -c "### Exp0" docs/reference/researchNotebook.md
# 기대: 기존 값과 동일 (Task 전 값을 미리 확인하여 비교)

# 9. 기존 판정 문자열 보존 (대표 3개 샘플)
grep -cE "판정 실험|\*\*채택\*\*|\*\*기각\*\*|\*\*부분 기각\*\*" docs/reference/researchNotebook.md
# 기대: 4 이상
```

## Risks

- **line 번호 drift**: researchNotebook.md가 향후 편집되며 line 번호가 바뀔 수 있음. 본 Task는 line 번호 기반이 아니라 **패턴 매칭 기반**(`^| ID |`, `### 열린 질문` 등)으로 타깃해야 함. 작업 시 Edit의 `old_string`은 유니크한 문맥을 포함.
- **H8 행 유무 불확실**: 사용자 참조 시점에 가설 표에 H7까지만 있음. 실제 수정 시 `grep -n "^| H[0-9]"`로 실제 행을 확인하고 있는 행만 prefix 적용. H8을 **새로 추가하지 말 것**.
- **매트릭스 정확성**: 각 실험 × 축의 ✅/▶/— 할당은 Task 01 섹션 8의 "실험별 검증 축 매핑"과 **반드시 일치**해야 함. 불일치 시 researchNotebook과 conceptFramework이 상호 모순. 본 Task는 Task 01 이후에 진행하므로 섹션 8 표를 직접 참고.
- **기존 가설 문구 훼손**: 축 prefix를 추가할 때 기존 문장의 공백·따옴표·볼드가 실수로 변경되면 판정의 원본성 훼손. 기존 문장은 **그대로 두고 앞쪽에만 `**[X 외부화]**` prefix 삽입**.
- **열린 질문 11번 링크**: `[conceptFramework.md § 9](./conceptFramework.md)`의 § 9가 Task 01에서 "외부화 미완 영역" 섹션 번호와 일치해야 함. Task 01의 섹션 번호 변경 시 본 Task도 동기화 필요.

## Scope boundary

**Task 02에서 절대 수정 금지**:
- `experiments/` 전체
- `README.md`
- `docs/reference/conceptFramework.md` (Task 01에서만 수정)
- `docs/reference/experimentSummary.md`, `experimentDesign.md`
- `docs/reference/index.md`
- `docs/plans/` 하위 다른 파일
- `researchNotebook.md` 내의 다음 섹션들:
  - "## 프로젝트 개요" 표
  - 각 실험 상세 기록 섹션 (`### Exp00` ~ `### Exp08b`)
  - "## 채점 시스템 변천"
  - "### 완료된 보조 작업"
  - 기존 열린 질문 1~10번 항목 (삭제·순서 변경 금지)

**허용 범위**:
- `researchNotebook.md` 헤더에 conceptFramework 링크 1줄
- 가설 표(line 26~34 근처) 헤더 1열 이름 변경 + 각 행 축 prefix
- 가설 표 직후 "#### 축 ↔ 실험 매트릭스" subsection 신설
- "### 열린 질문" 섹션에 11번 항목 1줄 추가
