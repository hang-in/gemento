---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: readme-memento-acknowledgement
parallel_group: A
depends_on: []
---

# Task 01 — `README.md` 정확화 + Memento origin 보강 + Nolan acknowledgement

## Changed files

- `README.md` (전체, 320줄)
  - line 3 헤더 한 줄 설명 — 도구 origin 한 구절 추가
  - line 17 "MIT 라이선스로 공개된 1인 연구 노트" 문구 점검
  - line 37~50 § 1 *Why Gemento* — 정치적 톤 표현 다듬기 ("쓸 땐 쓰고 새는 건 막는다" line 41 등)
  - line 52~66 § 2 *The Core Idea — 외부화* + Memento ↔ 제멘토 매핑 — Hero(헤더 바로 아래)와 매핑 표 사이 어디쯤에 *origin 단락* 신설
  - line 116~134 § 3 *What We've Proven* — H1~H7만 있는 표를 H1~H9c로 갱신 (researchNotebook §28~40 기준)
  - line 137~163 § 4 *What's Still Open* — H8/H9이 채택되었으므로 "검증 대기 중인 가설" 항목 갱신
  - 신규 § Acknowledgements (위치는 § 11 License 직전 권고)
  - line 314~316 § 11 *License* — MIT 명시 점검(이미 있음, 재확인만)

새 파일 없음.

## Change description

### Step 1 — Memento origin 단락 신설

`§ 2 The Core Idea — 외부화`의 Memento 매핑 표 직전(line 56 근처)에 한 단락 추가. 톤은 first-person notebook, 마케팅 X.

권고 위치: line 54 *"이 원리는 영화 Memento의 Leonard가..."* 직후, *"### Memento ↔ 제멘토 매핑"* 직전.

권고 내용 (Developer 판단으로 다듬기, 핵심 사실만 보존):

- **출발점**: secall / tunaflow를 만들며 마주한 실제 문제들 — 장기 기억 보존·검색, 컨텍스트의 유연한 확장(무절제한 토큰 사용 지양), 멀티세션
- **첫 가설**: "컨텍스트 다 지우고 DB 검색만 시키면 DB를 거의 무한 컨텍스트로 쓸 수 있는 것 아닌가" 라는 단순한 생각
- **메타포 확장**: 메멘토 영화의 Leonard가 외부 메모(문신·폴라로이드·전화)로 단기 기억상실을 보완하는 방식이 4축 외부화의 직관적 모델이 됨
- 한 줄로: *"제멘토는 secall/tunaflow에서 마주한 컨텍스트·기억 문제를 풀려다 메멘토에서 영감을 얻은 사이드 트랙"* — 학술 신규성 주장이 아닌 *발생사(genesis story)*

### Step 2 — H1~H9 결과 표 갱신 (line 121~128)

현재 `README.md` line 121~128의 *§ 3 What We've Proven* 표는 H1~H7만 있음. `docs/reference/researchNotebook.md` line 28~40의 H1~H9c와 동기화.

**누락된 행 추가**:
- H8 (Tool 외부화 안정성) — 채택 (neglect 0%, calculator 100%, math-04 0→100%, 총 +23.3%p) — Exp08b
- H9a (Tattoo 외부화 — 물리 한계 돌파) — 채택 (+68.3%p, Large 20K에서 Solo 0% → ABC 100%) — Exp09
- H9b (차별성) — 조건부 채택 (전체 +3.3%p; Large 3-hop에서 +33%p) — Exp09
- H9c (에러 모드 차이) — 채택 — Exp09

**갱신할 line**:
- line 118 "지금까지 9차 실험(288 + 누적 150+ trials)에서 확인된 가설" — 정확한 trials 수 점검 후 갱신 (researchNotebook의 누적치 사용)

### Step 3 — § 4 *What's Still Open* 갱신 (line 137~163)

line 143 *"H8 — Tool-use 안정성: ... 실행 대기 상태"* — H8은 이미 채택. 이 항목을 *제거*하고 새 미검증 가설로 대체. researchNotebook §689~720(Active 영역)에서 후보 가져오기:
- Small Paradox 해결 (Exp10 후보)
- 병렬 chunk 순회 (Exp10 후보)
- Exp09 통계 신뢰도 보강 (5 trial + p-value)

§ 3.2 (line 145~155) 미외부화 축 표는 그대로 유지(여전히 valid).

### Step 4 — 정치적 톤 다듬기 (§ 1)

line 41 *"쓸 땐 쓰고 새는 건 막는다"* — 한국어 표현이 한국어 청중에게는 전달되지만, 영문판(task-02)에서는 안 통함. 한국어판은 *유지*하되 영문판에서는 안 옮김(task-02의 의무).

line 44 *"맥락 없는 절약이 오히려 품질을 떨어뜨린다"* — 한국어 톤은 OK. 정치적 표현 없음.

검토 후 *제거 X, 톤만 살짝 부드럽게* — Developer 판단.

### Step 5 — Acknowledgements 신설

§ 11 License 직전(line 313 근처)에 신규 섹션 추가:

```markdown
## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — 외부 메모 보조의 원형 메타포. 4축 외부화의 직관적 모델이 됨.
- secall · tunaflow — 본 연구의 실제 출발점. 거기서 마주친 컨텍스트·기억 문제가 제멘토 설계의 토대가 됐다.
```

### Step 6 — 측정 숫자 일관성 검증

`grep`으로 README의 측정 숫자가 researchNotebook 최신 값과 일치하는지 점검:

- README line 11~13 핵심 수치 표 (Exp02 94.4%, Exp035 80%, Exp08 80%)는 그대로 (researchNotebook과 일치 확인)
- H1~H9 표의 % 값들 (재배치하며 사실 일치 확인)

### Step 7 — frontmatter / 작성일 명시

README.md 최상단에 작성·갱신일이 명시되어 있는지 확인. 없으면 `> *Last updated: 2026-04-25*` 같은 한 줄을 line 17 직후에 추가.

## Dependencies

- 없음 (parallel_group A, depends_on 없음)
- task-03(researchNotebook 분할)이 같은 group A이지만 *다른 파일* 수정 — 병렬 가능
- 단 *측정 숫자*는 researchNotebook을 단일 출처로 참조 — researchNotebook의 H1~H9 라벨/판정은 task-03에서 *변경 금지*가 약속되어 있어 안전

## Verification

```bash
# 1. README의 H1~H9이 모두 등장하는지
grep -E "^\| \*\*H[1-9]" /Users/d9ng/privateProject/gemento/README.md | wc -l
# 기대: 11 (H1, H2, H3, H4, H5, H6, H7, H8, H9a, H9b, H9c) 또는 10 (H9 단일행으로 묶을 경우)

# 2. Memento origin 단락 존재 확인 — secall 또는 tunaflow 키워드 등장
grep -c "secall\|tunaflow" /Users/d9ng/privateProject/gemento/README.md
# 기대: 1 이상 (origin 단락에서 등장)

# 3. Christopher Nolan acknowledgement 존재
grep -c "Nolan\|Memento.*2000" /Users/d9ng/privateProject/gemento/README.md
# 기대: 1 이상

# 4. Acknowledgements 섹션 존재
grep -c "^## Acknowledgements" /Users/d9ng/privateProject/gemento/README.md
# 기대: 1

# 5. MIT License 명시 보존 (line 314~316)
grep -c "MIT" /Users/d9ng/privateProject/gemento/README.md
# 기대: 1 이상

# 6. H8 "실행 대기" 표현이 § 4에서 사라졌는지
grep -c "H8.*실행 대기\|H8.*Exp08b.*실행 대기" /Users/d9ng/privateProject/gemento/README.md
# 기대: 0 (H8은 채택됨)

# 7. README 전체 줄 수 (대략적인 변화 확인)
wc -l /Users/d9ng/privateProject/gemento/README.md
# 기대: 약 320 ~ 360 (Acknowledgements 추가 + origin 단락으로 약간 증가)

# 8. 정치적/마케팅 과적재 명칭 미등장
grep -ci "Operating System\|novel framework\|AGI" /Users/d9ng/privateProject/gemento/README.md
# 기대: 0
```

## Risks

- **researchNotebook과 README의 % 수치 불일치**: 한국어 README는 여러 차례 갱신되어 측정 숫자 일관성이 흐트러져 있을 가능성. Developer는 H1~H9 표 갱신 시 researchNotebook line 28~40을 *유일한 출처*로 참조.
- **§ 1 정치적 톤 과도 삭제**: 사용자가 직전 토론에서 "쓸 땐 쓰고 새는 건 막는다"는 표현을 자기 가치관 표명으로 보존하길 원함. *제거 X, 다듬기만*.
- **Memento 메타포 강도 약화**: 직전 토론에서 사용자가 "양키들이 메타포 강도가 낮든 높든 1인 연구라면 중요한 가치"라고 명시. Hero 단락에서 *제거 금지*, 보존·강화 방향.
- **task-02(영문 README)와 동기화 어긋남**: 한국어 README의 사실(특히 H1~H9 표, Acknowledgements 문구)이 영문판과 어긋나면 신뢰 깎임 — task-02 작업 시 한국어판을 single source of truth로 참조.
- **새 file 생성 금지 위반**: 본 task는 README.md 한 파일만 수정. 다른 파일 생성·수정 시 Reviewer fail.

## Scope boundary

본 task에서 *절대 수정 금지*:

- `docs/reference/researchNotebook.md` (task-03 영역 — H1~H9 라벨/판정 변경 금지가 task-03 약속)
- `docs/reference/conceptFramework.md` (본 plan 범위 밖)
- `README.en.md` (task-02 영역, 아직 존재하지 않음)
- `experiments/` 하위 어느 파일도
- `LICENSE` (이미 MIT, 변경 금지)
- `docs/plans/` 하위 어느 파일도 (본 task 문서 자신 포함)

*허용*: `README.md` 단일 파일의 위 Step 1~7 영역만.
