---
type: handoff
status: in_progress
direction: architect → executor
updated_at: 2026-04-26
parent_topic: 연구 인프라 보강 (lab notebook + 환경 스냅샷)
related: docs/reference/researchNotebook.md, experiments/_external/lmstudio_client.py, experiments/config.py
---

# Gemento Executor 핸드오프 — 환경 Probe (lab notebook + env.json 도입 전)

## 1. 배경

arXiv v1 reproducibility appendix 자동 생성을 위해 다음 두 컴포넌트 도입을 준비 중:

- `experiments/exp{NN}_*/lab.md` — 사람의 관찰 1줄 append 채널 (`tools/note.py`)
- `experiments/exp{NN}_*/results/<run_id>.env.json` — 매 run 의 환경 스냅샷 자동 작성 (`tools/env_snapshot.py`)

env.json 의 `model.lmstudio_meta` 필드에 `quant`·`path` 등 LM Studio 자체 메타를 자동 추출하려 한다. 이 자동화가 가능한지 여부가 plan 의 핵심 분기점이라, 본 핸드오프로 사전 검증을 요청한다.

본 핸드오프 자체는 **읽기 전용 작업** — 코드 변경 0, LLM 호출 0.

## 2. 검증 요청 (Executor 측 1회 수행)

Windows + LM Studio (gemma4-e4b serving) 환경에서 다음 7 항목을 한 번에 capture.

### 2.1 LM Studio API endpoint probe

```powershell
# (a) 표준 OpenAI 호환 endpoint
curl -s http://yongseek.iptime.org:8005/v1/models

# (b) LM Studio 전용 endpoint — 본 응답 형태가 plan 분기점
curl -s http://yongseek.iptime.org:8005/api/v0/models/gemma4-e4b
curl -s http://yongseek.iptime.org:8005/api/v0/models

# (c) 헬스/프롭스 (있는지 여부만 체크)
curl -s -o /dev/null -w "%{http_code}\n" http://yongseek.iptime.org:8005/health
curl -s -o /dev/null -w "%{http_code}\n" http://yongseek.iptime.org:8005/v1/internal/model/info
```

기록 항목:
- (a) `/v1/models` raw JSON 응답 전체
- (b) `/api/v0/models/{id}` 와 `/api/v0/models` 의 raw JSON. **404 이면 명시**.
- (c) HTTP status code 만

### 2.2 LM Studio UI 모델 카드 (4.2 fallback)

API 가 quant·architecture 노출하지 않을 경우 UI 정보를 fallback 으로 사용. LM Studio 메뉴에서:
- 모델 카드의 "Model Information" 또는 동등 섹션 스크린샷 1장
- 다음 4 필드 텍스트 옮겨 적기:
  - Quantization (예: `Q4_K_M`)
  - Architecture (예: `Gemma`)
  - Context Length (예: `128K` 또는 토큰 수)
  - Model file path (가능 시)

### 2.3 GPU + driver

```powershell
nvidia-smi
```

전체 출력 그대로 첨부. (GPU 모델, driver version, CUDA version 추출용)

### 2.4 Windows Python 환경

```powershell
python --version
pip freeze | Select-String -Pattern "openai|httpx|tiktoken|google-generativeai"
```

전체 출력 첨부. Mac 측 `.venv` 와 다를 수 있어 별도 기록 필요.

### 2.5 LM Studio 자체 버전

LM Studio 메뉴 → About 에서 표시되는 버전 (예: `LM Studio 0.3.x`) 1줄.

### 2.6 모델 파일 hash (선택, 부담되면 skip)

LM Studio 의 모델 path 가 위 2.1·2.2 에서 확인되면:

```powershell
Get-FileHash "<모델 파일 path>" -Algorithm SHA256
```

비용이 크면 skip. 본 hash 는 env.json 에 **수동 1회만** 기록되고 이후 미갱신.

### 2.7 git 상태

```powershell
git rev-parse HEAD
git status --short
```

probe 시점의 origin/main 동기화 상태 확인용.

## 3. 보고 형식

회신 파일: `docs/reference/handoff-from-gemini-env-probe.md`

권장 구조:

```markdown
---
type: handoff
direction: executor → architect
parent: handoff-to-gemini-env-probe.md
captured_at: 2026-04-XX HH:MM (Windows 로컬 타임존 명시)
---

# Env Probe 결과

## 2.1 API endpoint probe
### /v1/models
\`\`\`json
{... raw 그대로 ...}
\`\`\`

### /api/v0/models/gemma4-e4b
(404 라면 "404 Not Found" 명시)
\`\`\`json
{... 또는 404 메시지 ...}
\`\`\`

(이하 2.2~2.7 동일 형식)

## 비고
- (자유 메모: 비정상 응답·환경 특이사항)
```

분량: 모두 raw 출력 첨부. Architect 측에서 파싱·요약.

## 4. plan 분기 결정 흐름

본 probe 회신 후 Architect 가 다음을 결정:

1. `/api/v0/models/{id}` 200 + quant 노출 → `tools/env_snapshot.py` 가 자동 fetch
2. 404 또는 quant 미노출 → 2.2 UI 정보 + 2.6 hash 를 env.json `notes` 필드에 **수동 1회** 기록 (Exp10 시작 1회만, 이후 모델 변경 전까지 재사용)

## 5. 비검증 항목 (이번 핸드오프 범위 밖)

- llama.cpp commit hash — LM Studio 미노출 가정. researchNotebook 에 한 줄 메모로 처리.
- Tattoo schema 정식 정의 — 별도 plan (reproducibility appendix 작성 시).
- Exp10 본격 실행 — 본 probe 와 무관, 별도 task.

## 6. 다음 단계

- (Architect, 본 핸드오프와 병행) `SAMPLING_PARAMS` 일원화 mini plan — config.py 일원화. probe 회신과 독립적으로 진행.
- (Executor, probe 회신 후) lab notebook + env snapshot + appendix 큰 plan-proposal 작성 → promote 후 실행.
- (Architect → Executor, 큰 plan promote 후) Exp10 본격 실행 핸드오프 갱신 (`tools/note.py` 사용 안내 + env.json 자동 생성 안내).

## 7. 컨텍스트 파일

- `experiments/_external/lmstudio_client.py` — 현재 LM Studio 호출 코드
- `experiments/config.py` — `API_BASE_URL`, `MODEL_NAME` 정의
- `experiments/orchestrator.py:71` — `temperature=0.1` 하드코딩 위치 (SAMPLING_PARAMS 일원화 대상)

---

**작성**: Architect Claude · Architect (claude-opus-4-7, macOS)
**수신**: Executor (Gemini CLI, Windows)
**상위 목표**: arXiv preprint v1 reproducibility appendix 인프라
