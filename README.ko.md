# gemento (제멘토)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-active-success)]()
[![Last commit](https://img.shields.io/github/last-commit/hang-in/gemento)](https://github.com/hang-in/gemento/commits/main)
[![Paper](https://img.shields.io/badge/Paper-draft%20in%20progress-orange)](docs/paper/draft.md)

> **작은 LLM을 더 크게 만들 수는 없다.  
> 대신 부족한 기억, 계산, 검증, 제어를 모델 밖으로 빼낼 수는 있다.**

제멘토는 Gemma 4 E4B 같은 소형 로컬 LLM이 혼자 풀기 어려운 작업을  
**외부 상태 + 도구 + 역할 분리 + 오케스트레이션**으로 어디까지 보완할 수 있는지 측정하는 실험 저장소입니다.

이 프로젝트는 새 모델을 만들거나 학습시키는 프로젝트가 아닙니다.  
기존 소형 모델 위에 구조화된 작업 흐름을 얹고, 그 효과를 반복 실험으로 확인하는 **1인 연구 노트이자 재현 가능한 실험 하네스**입니다.

*Last updated: 2026-06-30*  
📚 English version: [README.md](./README.md)

---

## 한눈에 보는 결과

제멘토의 핵심 관찰은 단순합니다.

| 질문 | 관찰된 결과 |
|---|---|
| 소형 LLM도 반복 구조를 주면 좋아지는가? | Exp02에서 1-shot 50% → 8-loop 94.4% |
| 자기 검증이 되는가? | Exp03에서 오류 감지 0% |
| 역할을 나누면 검증이 나아지는가? | Exp035에서 교차 검증 80% |
| 계산 도구를 붙이면 수학 문제가 나아지는가? | Exp08b에서 math-04 0% → 100% |
| 긴 로그를 통째로 넣는 대신 라우터를 쓰면 나은가? | Exp15/16에서 큰 로그 기준 router + mandatory + retry 조합이 가장 안정적 |
| 강한 모델을 Judge로 넣으면 항상 좋아지는가? | Exp11에서는 오히려 악화. 강한 Judge가 약한 모델의 자기 발견 흐름을 끊을 수 있음 |

다만 이 결과는 일반 법칙이 아닙니다.  
대부분은 **Gemma 4 E4B와 자체 태스크셋 기준의 실험 결과**이며, 일부 가설은 통계적으로 비유의입니다.  
이 저장소는 “소형 모델이 대형 모델을 대체한다”는 주장을 하지 않습니다.

---

## 이 저장소는 무엇인가

제멘토는 다음을 제공합니다.

- 소형 로컬 LLM workflow를 재현할 수 있는 실험 코드
- 외부 상태, 도구, 역할 분리, 제어 구조를 비교한 실험 기록
- 실패 사례까지 포함한 연구 노트
- 다른 모델·다른 태스크로 재현하거나 반박할 수 있는 baseline

반대로, 다음은 아닙니다.

- 새로운 LLM 아키텍처
- 새로운 학습 방법
- frontier 모델 대체 주장
- RAG보다 항상 낫다는 주장
- 프로덕션용 에이전트 프레임워크

---

## 왜 제멘토인가

소형 LLM은 대형 LLM의 축소판이 아닙니다.  
작은 모델은 작은 모델대로 강점이 있고, 약점도 분명합니다.

제멘토는 이 약점을 모델 안에서 해결하려 하지 않습니다.  
대신 다음 네 가지를 모델 밖으로 꺼냅니다.

| 축 | 모델 안에서 생기는 문제 | 제멘토의 처리 방식 |
|---|---|---|
| 상태 | 이전 판단과 근거를 잊음 | Tattoo라는 구조화된 JSON 상태로 남김 |
| 도구 | 계산·검색을 추론으로 때움 | calculator, linprog, grep/read 도구 사용 |
| 역할 | 스스로 검증하면 오류를 못 잡음 | Proposer, Critic, Judge 역할 분리 |
| 제어 | 언제 멈추고 반복할지 불안정 | Python orchestrator와 Judge를 함께 사용 |

한 문장으로 줄이면 다음과 같습니다.

> 기억은 환경에 남기고, 계산은 도구에 맡기고, 검증은 다른 역할에게 시킨다.

---

## 핵심 아이디어: 외부화

제멘토의 메타포는 영화 *Memento*입니다.

영화 속 Leonard는 기억을 믿을 수 없기 때문에 문신, 사진, 메모, 전화 같은 외부 장치에 의존합니다.  
제멘토도 비슷합니다. 소형 LLM의 내부 기억과 판단을 그대로 믿지 않고, 중요한 정보를 외부 구조로 고정합니다.

| Memento 요소 | 제멘토 대응 | 외부화 대상 |
|---|---|---|
| 문신 | Tattoo JSON | 상태 |
| 폴라로이드 | `evidence_ref` | 증거 |
| 전화 | Tool 호출 | 행동 |
| 조연 인물 | Role Agent | 관점 |
| 반복 조사 | Orchestrator loop | 제어 |

차이는 있습니다.  
제멘토는 우연한 메모가 아니라 명시적 스키마와 호출 순서를 사용합니다.

---

## 구조

```text
            소형 LLM
               │
        ┌──────┴──────┐
        │   내부 한계  │
        └──────┬──────┘
               │
 ┌─────────────┼─────────────┐
 ▼             ▼             ▼
Tattoo        Tools        Roles
상태 저장     계산/검색     A/B/C 역할 분리
               │
               ▼
        Orchestrator
        반복·중단·검증 제어
```

제멘토에서는 Critic도 두 종류로 나눕니다.

| 구분 | Critic Tool | Critic Agent |
|---|---|---|
| 성격 | 결정론적 검증 | 의미론적 비판 |
| 예시 | JSON schema, citation resolve, 파일 존재 확인 | 논리 모순, 근거 부족, 해석 충돌 |
| 구현 | Python/Rust 함수 | LLM 역할 프롬프트 |

Orchestrator도 마찬가지입니다.

| 구분 | Python Orchestrator | Judge Role |
|---|---|---|
| 성격 | 결정론적 안전장치 | 비결정론적 메타 판단 |
| 담당 | 최대 반복 수, schema validation, tool loop | 수렴 판단, retry 여부, accept/reject |
| 역할 | 폭주 방지 | 판단 흐름 제어 |

둘은 대체재가 아닙니다.  
Python은 안전망이고, Judge는 판단자입니다.

---

## 주요 실험 결과

### 1. 루프는 효과가 있었다

| 실험 | Before | After | 차이 | 의미 |
|---|---:|---:|---:|---|
| Exp02 | 50% | 94.4% | +44.4%p | 단일 추론보다 강제 루프가 효과적 |
| Exp10 | 41.3% | 78.1% | +36.8%p | 9-task cost-aware benchmark에서 ABC 루프가 개선 |

해석:  
같은 모델이라도 한 번에 답하게 할 때와, 외부 구조가 단계적으로 밀어줄 때 결과가 크게 달라졌습니다.

주의:  
Exp10 비교는 9-task benchmark 기준입니다. Gemini 2.5 Flash 1-call보다 높게 나온 조건이 있지만, wall time은 약 20배 더 길었습니다. 일반적인 우월 주장으로 해석하면 안 됩니다.

---

### 2. 자기 검증은 실패했고, 역할 분리는 효과가 있었다

| 실험 | 조건 | 결과 |
|---|---|---|
| Exp03 | 모델이 자기 답을 검증 | 오류 감지 0/15 |
| Exp035 | 별도 Critic 역할이 검증 | 오류 감지 12/15, 80% |

*Exp035는 Exp03과 Exp04 사이의 간이 실험(cross-validation gate)이며 "35번째"가 아닙니다. 신규 실험은 letter suffix를 씁니다 (`docs/reference/namingConventions.md` §5).*

해석:  
같은 모델이라도 “답하는 역할”과 “비판하는 역할”을 분리하면 실패 회수율이 달라졌습니다.

---

### 3. 도구는 문제 유형에 따라 효과가 갈렸다

| 실험 | 도구 유형 | 결과 |
|---|---|---|
| Exp08 / Exp08b | calculator, linprog 같은 결정론적 계산 도구 | 큰 폭 개선 |
| Exp14 | agent-active BM25 retrieval | 32K context baseline 대비 악화 |
| Exp15~16 | Redis context router + grep/read 도구 | 큰 로그에서 개선, 작은 로그에서는 overhead |

해석:  
“도구를 붙이면 좋아진다”가 아닙니다.  
도구의 성격, 호출 횟수, 모델의 도구 사용 능력, 입력 크기에 따라 결과가 갈립니다.

특히 Exp14에서는 검색 도구를 줬지만 multi-hop task에서 충분히 반복 검색하지 못해 성능이 떨어졌습니다.  
반대로 Exp15~16에서는 큰 로그를 통째로 넣는 방식이 무너지는 구간에서 context router가 유효했습니다.  
Exp18은 이를 합성 repo-규모(~245K tok, 컨텍스트 7.5배)까지 밀어도 무저하였고, **Exp19는 실데이터로 검증**했습니다: RTX 5060Ti의 gemma4:e4b가 다른 서버의 살아있는 1.15M-token `journald`에서 실제 `certbot` 장애를 매 trial 정확히 진단(stuffing 불가). router는 prefill 비용을 로그 크기에서 분리합니다(5060Ti에서 gemma4:e4b 생성 ~95 tok/s / prefill ~1,620 tok/s — stuffing이면 1.15M tok prefill만 ~12분/호출, router는 grep 결과만 ~3초).

---

### 4. 강한 Judge가 항상 좋은 것은 아니었다

Exp11에서는 Gemini 2.5 Flash를 Judge로 넣었지만, 모두 Gemma로 구성한 baseline보다 낮은 성능이 나왔습니다.

가능한 해석은 다음과 같습니다.

- 강한 Judge가 약한 모델의 중간 탐색 흐름을 너무 빨리 끊었다.
- Tattoo schema와 Judge의 판단 방식이 맞지 않았다.
- 약한 모델이 스스로 발견하던 chain이 단절됐다.

따라서 제멘토의 현재 방향은 “더 강한 모델을 위에 얹기”보다는  
**역할을 더 잘 나누고, 필요한 입력을 더 잘 정리하는 것**에 가깝습니다.

---

## 가설 요약

| ID | 주제 | 현재 판정 | 요약 |
|---|---|---|---|
| H1 | Orchestrator loop | 채택 | 다단계 루프가 단일 추론보다 좋았다 |
| H2 | Self-check | 기각 | 자기 검증은 실패했다 |
| H3 | Role Critic | 채택 | 역할 분리 검증은 오류를 회수했다 |
| H4 | ABC 역할 분리 | 조건부 | synthesis 계열에서 양수 신호 |
| H7/H8 | 계산 도구 | 채택 | calculator/linprog가 계산 문제를 보완 |
| H9 | Tattoo long-context | 조건부 | 긴 입력에서 Solo-dump보다 유리한 조건 확인 |
| H10 | 강한 Judge | 미결/실효 기각 | mixed intelligence가 오히려 악화 |
| H11 | Extractor | 조건부 | pre-stage 입력 정리는 양수 방향 |
| H12 | Reducer | 미결/실효 기각 | post-stage 압축은 정보 손실 가능 |
| H13 | Search Tool | 미결/실효 기각 | agent-active retrieval은 multi-hop에서 부족 |
| H15 | Context Router | 조건부 | 큰 로그에서 유효, 작은 로그에서는 overhead |
| H16b/c | mandatory prompt + retry | 채택 | 큰 로그 router 조건에서 출력 안정화 |
| H17 | 복잡도 상한 | 부분 | e4b+router가 multi-hop/집계/판별까지 스케일(baseline ~92%); 단 mandatory 스택은 특정 실패 모드 전용이라 hard task에선 −3pp |
| H18 | size invariance | 채택 | router가 추론 부하를 로그 크기와 분리(O(1)) — multi-hop/집계가 ~245K tok(컨텍스트 7.5배)까지 92~100% 무저하; 모델은 거대 로그가 아닌 grep 결과만 봄 |
| H21 | Facet 집계 도구 | 조건부(집계 한정) | untruncated 전수 집계(`aggregate_context`)가 집계 task에서 결정적(score 0.0→0.8) — 16KB 캡의 confidently-wrong을 정정; 단일-needle엔 무효. "more structure ≠ monotonically better" |
| H22 | retrieval-discipline nudge | 미결/실효 기각 | narrow-query nudge opt-in 편입 후 재검증(n=10)에서 레버(+50pp) 미재현·부호 역전 — control baseline이 run마다 17%↔70%로 요동. 진짜 문제는 nudge 부재가 아닌 finalization 자체의 분산 |

상세 수치와 분석은 `docs/reference/` 아래의 각 실험 보고서에 있습니다.

---

## 재현성 주의사항

수치를 인용하기 전에 다음 조건을 확인해야 합니다.

- 주요 결과는 Gemma 4 E4B와 자체 benchmark 기준입니다.
- 일부 실험은 n=15 paired test 기준으로 통계적으로 비유의입니다.
- keyword scorer는 실제 품질 차이와 답변 스타일 차이를 완전히 분리하지 못합니다.
- Gemini 2.5 Flash와의 비교는 9-task cost-aware benchmark에 한정됩니다.
- Context Router 결과는 입력 크기와 모델의 tool-use 능력에 크게 의존합니다.

이 저장소의 수치는 “가능성을 보여주는 실험 결과”이지, 일반화된 벤치마크 결론이 아닙니다.

---

## 빠른 시작

### 1. 설치

```bash
git clone https://github.com/hang-in/gemento.git
cd gemento

python3.14 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. 추론 서버 설정

`experiments/config.py`에서 OpenAI 호환 서버 주소를 설정합니다.

```python
MODEL_NAME = "gemma4-e4b"
API_BASE_URL = "http://localhost:8080"
```

llama.cpp 서버를 사용할 경우 `/v1/chat/completions`와 `tool_calls`를 지원해야 합니다.

서버 확인:

```bash
curl -s http://localhost:8080/v1/models | jq .data[].id
```

### 3. Smoke test

```bash
cd experiments
python tools/smoke_test.py
```

기대 출력:

```text
SMOKE TEST PASSED: math-04 answer=..., tool_calls=...
```

### 4. 첫 실험 실행

짧은 baseline:

```bash
python run_experiment.py baseline
```

tool-use 실험:

```bash
python run_experiment.py tool-use
python measure.py "results/exp08_*.json" --markdown --output results/exp08_report.md
```

실험은 checkpoint를 지원합니다.  
중단 후 다시 실행하면 `partial_*.json`에서 이어갑니다.

---

## 다른 모델로 돌리기

`experiments/config.py`에서 모델명과 서버 주소만 바꿉니다.

```python
MODEL_NAME = "qwen2.5-7b-instruct"
API_BASE_URL = "http://localhost:8080"
```

주의할 점:

- 서버가 tool_calls를 지원해야 합니다.
- 같은 태스크라도 모델마다 도구 호출 능력이 크게 다를 수 있습니다.
- 작은 모델은 agent가 직접 도구를 고르는 pull 방식보다, orchestrator가 강제로 밀어주는 push 방식이 나을 수 있습니다.

---

## 새 Tool 추가

`experiments/tools/math_tools.py` 구조를 참고해 새 도구를 추가합니다.

```python
def search_tool(query: str, limit: int = 10) -> list[dict]:
    """BM25/vector hybrid search over your knowledge base."""
    ...
```

등록 위치:

- `experiments/tools/__init__.py`
- `TOOL_FUNCTIONS`
- `TOOL_SCHEMAS`

주의:  
도구를 추가했다고 성능이 자동으로 좋아지지 않습니다.  
Exp14처럼 agent가 충분히 반복 호출하지 못하면 오히려 나빠질 수 있습니다.

---

## 새 Role 추가

`experiments/system_prompt.py`에서 기존 역할 프롬프트를 참고합니다.

기본 역할:

- Proposer: 답을 제안
- Critic: 오류와 근거를 비판
- Judge: 수렴, 재시도, 종료 판단
- Extractor: 입력에서 claim/entity를 사전 추출
- Reducer: 결과를 후처리 정리

호출 순서는 `experiments/orchestrator.py`의 `run_abc_chain`을 참고합니다.

현재 실험 기준으로는 pre-stage Extractor가 post-stage Reducer보다 안전한 방향으로 관찰됐습니다.  
다만 이 역시 확정 결론은 아니며, 모델·태스크별 재현이 필요합니다.

큰 로그 retrieval에는 `run_abc_chain(mandatory_tool_prompt=True)`로 검증된 mandatory-tool 규칙(grep 먼저 / 조기 단정 금지 / 매치 라인 그대로 전사)을 주입할 수 있습니다 — 1-needle 큰 로그에서 e4b router per-attempt를 27%→83%로 끌어올림(Exp16b). opt-in이며 **failure-mode-specific**: 추론 중심·작은 입력엔 끄세요(기본값, Exp17에서 −3pp). 자동 게이트 아님 — caller가 입력 성격으로 판단.

---

## 새 태스크셋 추가

`experiments/tasks/taskset.json`에 항목을 추가합니다.

필수 필드:

```json
{
  "id": "task-id",
  "category": "logic",
  "difficulty": "medium",
  "prompt": "...",
  "expected_answer": "...",
  "scoring_keywords": ["..."]
}
```

주의:  
수학 문제는 `expected_answer` 자체가 제약 조건을 만족하는지 먼저 검증해야 합니다.  
Exp07/Exp08에서 정답 데이터 결함이 실험 결론을 바꾼 사례가 있었습니다.

---

## 문서 구조

| 경로 | 내용 |
|---|---|
| `docs/reference/conceptFramework.md` | 4축 외부화 개념 문서 |
| `docs/reference/researchNotebook.md` | 메인 연구 노트 |
| `docs/reference/results/` | 실험별 결과 문서 |
| `docs/reference/scoringHistory.md` | 채점기 변천 |
| `docs/reference/failureLabels.md` | 실패 분류 |
| `docs/reference/resultJsonSchema.md` | 결과 JSON schema |
| `docs/plans/` | 실험 계획과 진행 기록 |
| `docs/agents/` | 역할 정의 |
| `experiments/schema.py` | Tattoo schema |
| `experiments/system_prompt.py` | 역할별 system prompt |
| `experiments/orchestrator.py` | loop, tool call, ABC chain |
| `experiments/measure.py` | 결과 채점 |
| `experiments/tools/math_tools.py` | calculator, linprog 등 |

---

## Roadmap

| 단계 | 상태 | 내용 |
|---|---|---|
| Phase 1 | 완료 | Exp00~Exp10, 4축 baseline |
| Stage 2 | 완료 | 인프라 안정화, scorer/failure label 정리 |
| Stage 5 | 완료 | Extractor, Reducer, Search Tool ablation |
| Stage 6 | 완료 | cross-model replication, LLM-as-judge 보조 검증 |
| Stage 7 | 완료 | Context Router, mandatory prompt, retry 조합 |
| Stage 8 | 완료 | mandatory-tool 프롬프트 opt-in 편입 (caller-decides) |
| Stage 9 | 완료 | Facet 집계 도구 A/B (H21 조건부, 집계 task 한정) |
| Stage 10 | 완료 | 오케스트레이터 신뢰성 — retrieval-discipline opt-in (H22 미결/실효 기각) + finalization 분산 진단·retry K-sweep 트랙 종결 (per-attempt ≈49% 고분산, retry K=5→95%) |
| 중기 | 예정 | per-attempt 신뢰도(Exp16b류)·a2a, Graph/Evidence Tool |
| 장기 | 예정 | 더 체계적인 cross-model ablation과 technical report |

---

## 기여 방법

제멘토는 현재 1인 연구 노트에 가깝습니다.  
다만 재현 결과, 반례, 문서 개선은 모두 의미가 있습니다.

| 난이도 | 예시 | 기여 방식 |
|---|---|---|
| 5분 | 오탈자, README 개선 | PR |
| 수 시간 | 다른 모델로 기존 실험 재현 | Issue |
| 수 일 | 새 Tool 구현 + 테스트 | PR + 결과 리포트 |
| 수 주 | 새 Role 설계·평가 | PR + 연구 노트 |
| 수 개월 | 체계적 ablation | 공동 연구 기록 검토 |

절차:

1. Issue로 무엇을 해볼지 남깁니다.
2. Fork에서 실험합니다.
3. 코드 변경은 PR로, 재현 결과는 Issue 댓글이나 gist로 공유합니다.

---

## Related Work

제멘토의 “LLM 인지 외부화”라는 방향은 완전히 고립된 아이디어가 아닙니다.  
다음 흐름과 인접합니다.

- **Externalization in LLM Agents** — memory, skills, protocols, harness engineering 관점의 외부화 리뷰
- **LightMem** — lightweight memory-augmented generation
- **StateFlow** — LLM 작업 해결을 state machine으로 구조화
- **Chain-of-Agents** — 긴 입력을 여러 agent가 나누어 처리하고 manager가 종합

제멘토의 차이는 다음에 있습니다.

- Gemma 4 E4B 같은 소형 모델을 중심으로 측정
- 같은 base model을 역할만 바꿔 A/B/C로 분리
- Tattoo라는 명시적 working-state schema 사용
- 성공뿐 아니라 실패 모드와 채점 오류까지 연구 노트에 남김

---

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — 외부 기억 보조라는 핵심 메타포
- secall · tunaflow — 제멘토가 출발한 실제 문제 공간

---

## License

[MIT](./LICENSE) — 자유롭게 fork, 수정, 재배포, 상업 사용 가능합니다.  
저작권 고지만 유지해주세요.

---

## 질문·제안

GitHub Issues 또는 Discussions를 통해 남겨주세요.  
재현 결과와 반례도 환영합니다.
