---
type: prompt
status: draft
updated_at: 2026-04-21
author: Architect Claude · Architect (claude-code)
recipient: Gemini CLI (Windows)
---

# 실험 7 재개 프롬프트 — Loop Saturation + Loop-Phase

## 상황 요약

실험 7 (Loop Saturation + Loop-Phase 프롬프트) 작업을 수정하다가 중단된 상태입니다.
이 프롬프트를 따라 코드를 수정하고 실험을 실행해주세요.

---

## 1. API 엔드포인트 변경 (필수)

**이전**: Ollama API (`localhost:11434/api/chat`, 모델명 `gemma4:e4b`)
**현재**: llama.cpp 서버 (`yongseek.iptime.org:8005`, OpenAI-compatible API, 모델명 `gemma4-e4b`)

### 변경할 파일: `experiments/config.py`

```python
# 변경 전
MODEL_NAME = "gemma4:e4b"
OLLAMA_BASE_URL = "http://localhost:11434"
# ...
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TIMEOUT = 600

# 변경 후
MODEL_NAME = "gemma4-e4b"
API_BASE_URL = "http://yongseek.iptime.org:8005"
API_CHAT_URL = f"{API_BASE_URL}/v1/chat/completions"
API_TIMEOUT = 600
```

### 변경할 파일: `experiments/orchestrator.py`

`call_ollama()` 함수를 OpenAI-compatible API 형식으로 수정해야 합니다.

**현재 코드** (50~69행):
```python
def call_ollama(messages: list[dict], model: str = MODEL_NAME) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
            "num_ctx": 4096,
            "num_gpu": 35,
            "f16_kv": True,
            "num_thread": 8,
        },
    }
    with httpx.Client(timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=30.0)) as client:
        resp = client.post(OLLAMA_GENERATE_URL, json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
```

**수정 방향**:
```python
def call_model(messages: list[dict], model: str = MODEL_NAME) -> str:
    """OpenAI-compatible chat API를 호출하고 응답 텍스트를 반환한다."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=httpx.Timeout(API_TIMEOUT, connect=30.0)) as client:
        resp = client.post(API_CHAT_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
```

**주의사항**:
- `call_ollama`를 호출하는 모든 곳을 `call_model`로 변경하거나, 함수명을 그대로 유지해도 됩니다
- `format: "json"` (Ollama 전용) → `response_format: {"type": "json_object"}` (OpenAI 호환)
- 응답 구조: `resp["message"]["content"]` → `resp["choices"][0]["message"]["content"]`
- Ollama 전용 `options` (num_gpu, f16_kv, num_thread 등)는 제거합니다

---

## 2. API 연결 테스트

코드 수정 후 실험 실행 전에 반드시 테스트:

```bash
curl -s http://yongseek.iptime.org:8005/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"gemma4-e4b","messages":[{"role":"user","content":"1+1="}],"max_tokens":32}' \
    | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['choices'][0]['message']['content'])"
```

서버가 응답하면 다음 단계로 진행합니다.

---

## 3. 체크포인트 확인

`experiments/results/partial_loop_saturation.json` 파일이 있는지 확인:

- **있으면**: 이미 완료된 (condition, task) 쌍은 자동 스킵됩니다. 그냥 실행하세요.
- **없으면**: 처음부터 시작합니다.
- **이전 실행이 잘못된 API로 돌아갔다면**: `partial_loop_saturation.json`을 삭제하고 처음부터 시작하세요.

---

## 4. 실험 실행

```bash
cd /path/to/gemento
python experiments/run_experiment.py loop-saturation
```

### 실험 설계 (변경 없음)
- **요인**: 2×4 (프롬프트 baseline/phase × MAX_CYCLES 8/11/15/20)
- **8개 조건**: baseline_8, baseline_11, baseline_15, baseline_20, phase_8, phase_11, phase_15, phase_20
- **태스크**: 12개 (기존 9 + 고난도 math-04, logic-04, synthesis-04)
- **반복**: 조건당 태스크당 3 trials
- **총 288 runs**, 예상 20~38시간

### 모니터링
- 콘솔에 `[Loop Saturation] Condition=... | Task=...` 로그 출력
- 태스크 완료마다 체크포인트 자동 저장
- 중단 후 재실행하면 자동 이어하기

---

## 5. 결과 확인 및 분석

실험 완료 후:

```bash
python experiments/measure.py "experiments/results/exp07_loop_saturation_*.json"
```

### 관찰 포인트
1. **포화 곡선**: MAX_CYCLES 8→11→15→20에서 정답률이 평탄해지는 지점
2. **Phase 프롬프트 효과**: baseline vs phase 정답률 차이
3. **고난도 태스크(04급)**: 사이클 소모량 및 정답률
4. **비교 기준선**: exp045 정답률 88.9% (7.2 사이클), exp06 정답률 96.7% (21 루프)

---

## 6. 결과 커밋 및 푸시

```bash
git add experiments/results/exp07_loop_saturation_*.json
git add experiments/config.py experiments/orchestrator.py
git commit -m "feat: 실험 7 결과 + API 엔드포인트 llama.cpp 전환"
git push origin main
```

---

## 7. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `httpx.ConnectError` | 서버 주소 `yongseek.iptime.org:8005` 확인, 네트워크 연결 점검 |
| `httpx.ReadTimeout` | `API_TIMEOUT` 값 증가 (config.py), Q8_0이라 추론이 느릴 수 있음 |
| JSON 파싱 실패 | `response_format` 지원 여부 확인. 미지원 시 `response_format` 제거하고 기존 `extract_json_from_response()` 폴백 사용 |
| `model not found` | 모델명 `gemma4-e4b` 확인 (`curl http://yongseek.iptime.org:8005/v1/models`) |
| 특정 조건만 재실행 | `partial_loop_saturation.json`에서 해당 label 데이터 삭제 후 재실행 |

### response_format 미지원 시 대안

llama.cpp 서버가 `response_format`을 지원하지 않을 수 있습니다. 그 경우:

```python
# response_format 줄을 제거하고:
payload = {
    "model": model,
    "messages": messages,
    "max_tokens": 4096,
    "temperature": 0.1,
    # response_format 없음 — extract_json_from_response()가 후처리
}
```

기존 `extract_json_from_response()` 함수가 마크다운 코드블록에서 JSON을 추출하므로 대부분 동작합니다.
