# 한국어 노트북 섹션 템플릿 (참고용)

`docs/reference/researchNotebook.md` 의 `### Exp##: <실험명>` append 시 다음 형식을 따른다. **placeholder 값은 모두 채워서 사용** — 빈 칸 금지.

```markdown
### Exp##: <실험 이름>

| 항목 | 내용 |
|------|------|
| **누가 (Who)** | <Role 별 모델 구성, condition 별 다르면 명시> |
| **언제 (When)** | YYYY-MM-DD ~ YYYY-MM-DD |
| **어디서 (Where)** | <환경, 예: Windows + LM Studio (`http://192.168.1.179:1234`)> |
| **무엇을 (What)** | H## 후보 — "<가설 본문 한 줄>". <N> condition × <M> task × <K> trial = **<총> trial** |
| **왜 (Why)** | <이전 실험 결과로부터 본 실험의 동기, 외부화 축 분류, 운영 원칙 매핑> |
| **어떻게 (How)** | <구현 요약 — 코드 변경 위치 + 1-2라인 patch + Stage 2A/2B/2C 보존 명시> |

**결과 (v3 채점, <총> trial):**

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur | total cost |
|-----------|--:|---------:|----------------:|--------:|-----------:|--------:|-----------:|
| <baseline_name> | <n> | **0.XXXX** | 0.XXXX | <e>+<null> | X.X | XXXs | $0.0000 |
| <treatment_name> | <n> | **0.XXXX** | 0.XXXX | <e>+<null> | X.X | XXXs | $X.XXXX |

**Δ(<treatment> − baseline) = ±0.0XXX** (<양수/음수>). 통계 (n=<task> paired): Wilcoxon p=X.XXX / paired t p=X.XXX (NOT SIGNIFICANT 또는 SIGNIFICANT). Cohen's d = ±0.XXX (<small/medium/large> effect <양수/음수>). Bootstrap 95% CI Δ: [±0.XXX, ±0.XXX].

**카테고리별 Δ(<treatment>−baseline)**:
- math: ±0.XXX
- logic: ±0.XXX
- synthesis: ±0.XXX
- planning: ±0.XXX

**핵심 발견:**
1. **H## <verdict>** — <한 줄 요약>
2. **<메커니즘 발견 1>** — <근거>
3. **<case study>** — <대표 task 의 trial-level 관찰>
4. **<의외/대비>** — <Exp## 결과와의 대비, 또는 정반대 메커니즘 발견>
5. **<카테고리 패턴>** — <어느 카테고리에서 강하고 어느 카테고리에서 약한가>

**Stage <N> 의제 함의:**
- ✅/❌ <본 방향의 후속 plan 추천 여부>
- 🎯 <다음 Exp 후보>
- <보류/재검증 후보>

**상세 보고서:** `docs/reference/exp##-<slug>-analysis-YYYY-MM-DD.md`
**결과 데이터:**
- `experiments/exp##_<slug>/results/<baseline_file>.json` (<baseline_name>)
- `experiments/exp##_<slug>/results/<treatment_file>.json` (<treatment_name>)
```

## 위치 결정

- 기존 `### Exp{prev}: ...` 섹션 직후, 또는 `## Change History` 직전, 또는 `---` 다음 `*이 문서는 ... 증분 관리합니다.*` 직전.
- grep `^### Exp` 으로 마지막 ### Exp## 섹션 위치 확인 후 그 다음에 insert.

## 일관성 체크

작성 후 다음을 spot-check:
- 표의 `mean_acc` 값과 `Δ` 가 산술적으로 일치
- 카테고리별 Δ 의 가중 평균이 전체 Δ 와 근사 (task 수 차이 고려)
- "**채택**" / "**조건부 채택**" / "**⚠ 미결**" / "**기각**" 표기 일관 (verdict mapping 표 따름)
