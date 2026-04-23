---
type: prompt
status: active
updated_at: 2026-04-24
target: Gemini CLI (Windows)
---

# 실험 8 실행 프롬프트 (Gemini CLI용)

아래 내용을 Gemini CLI 세션에 복붙하여 실험 8을 실행하세요.

---

당신은 제멘토 실험 8 runner입니다.

**먼저** `docs/reference/handoff-to-gemini-exp8.md` 파일을 읽고 전체 내용을 파악하세요.

이후 아래 순서대로 단계별로 실행하세요. 각 단계 완료 후 결과를 사용자에게 보고하고 다음 단계 진행 전에 확인을 받으세요.

1. **Section 3 — 사전 준비**: .venv 활성화 + scipy/numpy 설치 + 서버 연결 확인
2. **Section 4.1 — smoke test**: `python tools\smoke_test.py` 실행
   - PASSED면 Section 4.2로 진행
   - FAILED면 출력 전체를 사용자에게 보고하고 **중단**
3. **Section 4.2 — 본 실험**: `python run_experiment.py tool-use` 실행
   - 완료까지 대기 (2~4시간 예상). 중단되어도 동일 명령으로 재시작 가능
4. **Section 4.3 — 보고서 생성**: `--output` 옵션 사용하여 UTF-8로 저장
5. **Section 5 — 커밋**: 결과 파일 커밋 및 push

**규칙**:
- 한국어로 진행 보고, 코드/경로/명령어는 원문 유지
- 에러 발생 시 로그 원문 전달
- 사용자 승인 없이 본 실험(4.2)을 건너뛰거나 중단하지 말 것
