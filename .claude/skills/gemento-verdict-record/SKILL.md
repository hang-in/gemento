---
name: gemento-verdict-record
description: gemento 실험 마감 후 가설 verdict (H##) 를 researchNotebook.md (한국어) + researchNotebook.en.md (영문 Closed-append-only) + docs/plans/index.md 에 일관되게 기록한다. 실험 분석이 끝나서 H## 의 verdict 를 노트북에 반영해야 할 때, "verdict 기록", "노트북 갱신", "Exp## 마감", "H## 채택/조건부/미결/기각" 등을 사용자가 언급할 때 사용한다. 영문 파일의 append-only 정책을 자동으로 강제한다 — 기존 entry/표/문장 절대 수정 금지. 한국어 파일은 표 갱신 + 새 섹션 append + 축 매트릭스 갱신을 함께 처리한다.
---

# gemento-verdict-record

gemento 실험 워크플로우의 가장 정책 위반 위험이 큰 단계 — verdict 기록 — 을 자동화. **영문 노트북 append-only 정책 위반은 회복 비용이 크므로 본 스킬이 그것을 강제한다.**

## 언제 실행하는가

다음 신호 중 하나라도 보이면 본 스킬을 사용:

- 사용자가 "Exp## 마감", "verdict 기록", "노트북 갱신" 을 명시
- 분석 보고서 (`docs/reference/exp##-*-analysis-YYYY-MM-DD.md`) 작성 완료 후 다음 단계
- plan 의 task-05 (분석 + verdict + 문서) 진행 시점
- README/노트북 갱신 결정이 사용자로부터 떨어진 직후

## 입력으로 필요한 것

다음을 사용자 또는 분석 보고서에서 확보 후 시작 — 부족하면 사용자에게 질문:

1. **가설 ID** — `H10`, `H11`, `H12`, ... 형식
2. **가설 제목** — 예: "[Role 외부화 분리/추가 — Reducer Role]"
3. **Verdict** — 정확히 4 종 중 1개:
   - **채택** / **Supported**
   - **조건부 채택** (자세한 조건 명시) / **Conditionally supported**
   - **미결** (effectively rejected/supported 추가 가능) / **Inconclusive**
   - **기각** / **Rejected**
4. **결정 실험** — 예: `Exp13`
5. **핵심 수치** — Δ, Cohen's d, Wilcoxon p, paired t p, Bootstrap 95% CI
6. **카테고리별 Δ** (math/logic/synthesis/planning)
7. **메커니즘 한 줄** — verdict 의 근거가 되는 핵심 발견
8. **분석 보고서 경로** — `docs/reference/exp##-*-analysis-*.md`
9. **결과 JSON 경로** — `experiments/exp##_*/results/*.json` × N
10. **plan slug** — `docs/plans/exp##-*.md` 의 파일명 stem (index.md 이동용)
11. **오늘 날짜** — YYYY-MM-DD (frontmatter `updated_at` + 영문 섹션 헤더용)

## 처리 순서

세 파일을 다음 순서로 갱신. **순서가 중요** — 영문은 마지막 (가장 정책 엄격).

### 1. 한국어 노트북 (`docs/reference/researchNotebook.md`)

가장 광범위한 갱신. 4 곳 수정:

**(a) frontmatter `updated_at`** → 오늘 날짜로 갱신.

**(b) `## 핵심 가설` 표** — 새 row 추가. 형식:
```
| **H##** | **[축 분류]** 한국어 가설 본문 | ⚠ **verdict** — YYYY-MM-DD Exp##: Δ=±0.0XXX (방향), Cohen d=±0.XXX, ... 메커니즘 한 줄 | Exp## |
```

**(c) `#### 축 ↔ 실험 매트릭스` 표** — 새 row 추가. 형식:
```
| Exp## (실험명) | Tattoo | Tool | Role Agent | Orchestrator |
```
✅/▶/— 는 가설의 외부화 축 분류를 따라 결정. Role Agent 가 주축이면 `✅ (Role 분리/추가 — H## verdict)` 처럼 부가 설명 포함.

**(d) `### Exp##: <실험명>` 섹션 append** — `## Change History` 또는 문서 끝 직전에 새 섹션. 5W1H 표 + 결과 표 + Δ + 카테고리별 Δ + 핵심 발견 (번호 매김) + Stage 함의 + 상세 보고서 경로 + 결과 JSON 경로. **참고용 템플릿 — `references/korean_section_template.md`** 읽어서 사용.

### 2. 영문 노트북 (`docs/reference/researchNotebook.en.md`) — **APPEND-ONLY**

**여기서 어떤 기존 줄도 수정 금지**. 다음만 허용:

**(a) frontmatter `updated_at`** → 오늘 날짜로 갱신. **이 한 줄만 예외.**

**(b) `## ExpNN — <name> note (YYYY-MM-DD)` 섹션을 `## Change History` 직전에 insert**. 영어 본문. 표는 **건드리지 않는다** — 본문 마지막에 다음 boilerplate 의무 포함:
```
The hypothesis table above (H1~H{prev}) remains unchanged (Closed-append-only policy). H##'s entry is a new addition only.
```
여기서 `{prev}` = 이번에 추가하는 H## 의 *직전* 가설 ID (예: H12 추가 시 `H1~H11`).

**참고용 템플릿 — `references/english_section_template.md`** 읽어서 사용.

**검증 의무**: 본 스킬은 다음을 반드시 확인 후 종료:
- 표의 row 개수 변경 없음 (추가 전후 동일)
- 기존 H## 섹션 (## Exp00 ~ ## Exp{prev}) 본문 변경 없음
- 추가된 섹션은 `## Change History` 위에 위치
- 추가된 섹션 본문에 boilerplate 문장 포함

이 4 검증 중 하나라도 실패 시 **즉시 사용자에게 보고하고 변경 롤백 제안**.

### 3. plans index (`docs/plans/index.md`)

**(a) Active 섹션의 해당 plan 링크 제거**.

**(b) Recently Done — Stage N 섹션의 맨 위에 새 line 추가**:
```
- [<slug>.md](<slug>.md) — **Stage N (Exp##)**: <한 줄 요약>. <verdict>. Δ=±0.0XXX, Cohen d=±0.XXX. <date>.
```

Stage 번호는 plan frontmatter 또는 사용자 확인. 형식은 기존 entry 와 일관.

## 실수 방지 — 영문 파일 안전 패턴

영문 파일 갱신은 다음 알고리즘을 따라 작성:

1. `Read` 로 전체 파일 읽기
2. `## Change History` 가 시작하는 줄 번호 찾기
3. `Edit` 또는 `Write` 사용 시:
   - **`Edit` 권장 패턴**: `old_string` = `"---\n\n## Change History"` (Change History 직전 `---` 구분선부터), `new_string` = `f"---\n\n## Exp{NN} — {name} note ({date})\n\n{body}\n\n---\n\n## Change History"`
   - **`Write` 사용 금지** — 전체 덮어쓰기는 정책 위반 위험이 너무 크다
4. 갱신 후 `Read` 로 재확인 — 표 line 수, 기존 H## 본문 첫 단어 매치 등 spot-check

## verdict 표기 규칙

verdict 한국어 / 영문 매핑 — 일관성을 위해 다음 표 따른다:

| 한국어 | English |
|---|---|
| 채택 | Supported |
| 조건부 채택 | Conditionally supported |
| 미결 | Inconclusive |
| 미결 (실효적 기각) | Inconclusive (effectively rejected) |
| 미결 (실효적 채택) | Inconclusive (effectively supported) |
| 기각 | Rejected |
| 부분 기각 | Partially rejected |

verdict 앞에 `⚠` 이모지를 붙이는 것은 **조건부/미결** 카테고리 한정 (gemento 노트북 관행). **채택/기각** 은 이모지 없음.

## 사용자 confirm 분기

다음 시점에 사용자에게 짧게 확인 후 진행:

- 입력으로 받은 verdict 가 위 7 종 외이면 — 정확한 표기 질의
- 영문 섹션 boilerplate 의 `H1~H{prev}` 의 `{prev}` 가 불명확하면 — 표를 grep 으로 마지막 H## 확인 후 사용자 시현
- index.md 의 Stage 번호가 plan frontmatter 에 없으면 — 사용자 질의

## 외부에서 변경 금지

본 스킬이 절대 만지지 않는 파일:

- `experiments/**/*.py` (코드)
- `experiments/**/results/*.json` (결과 데이터)
- `docs/reference/exp##-*-analysis-*.md` (분석 보고서 — 별도 작업)
- `docs/reference/conceptFramework.md` (canonical 프레임 문서 — 본 스킬 영역 외, 별도 갱신)
- `README.md` / `README.ko.md` (README 갱신은 사용자 결정 사안)

위 파일들이 갱신 필요할 수 있으나 본 스킬에서는 다루지 않고, 마지막에 "추가로 갱신 후보: [목록]" 으로 사용자에게 신호만 준다.

## 종료 시 보고

스킬 작업 완료 후 사용자에게 한국어로 다음 보고:

```
verdict 기록 완료 — H##

갱신:
- researchNotebook.md (한): 표 row + 축 매트릭스 + Exp## 섹션 append
- researchNotebook.en.md (영, append-only): Exp## 섹션 append (표 무변경 검증 통과)
- docs/plans/index.md: Active → Recently Done — Stage N 이동

추가 갱신 후보 (사용자 결정 필요):
- README.ko.md / README.md: Roadmap 진행 상태
- conceptFramework.md: 4축 매트릭스 §8

다음 단계 후보: <Architect 권장>
```
