"""실증 테스트: SSH를 통한 n100 서버 Caddy 로그 인출 및 에이전트 분석.

n100 서버에 SSH로 접속해 Caddy 웹 서버 로그를 획득하여 Redis에 적재한 뒤,
제멘토 Ephemeral Context Router를 이용해 HTTP 에러 로그 분석 리포트를 작성합니다.
접속 실패 시 시뮬레이션용 Caddy 로그 가상 데이터를 생성하여 Fallback 실행 모드를 지원합니다.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# gemento/experiments 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.context_tools import get_redis_client
from orchestrator import run_abc_chain
from config import MODEL_NAME

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── .env 환경변수 수동 파싱 ──
def load_env_vars() -> dict[str, str]:
    env_vars = {}
    env_path = Path("d:/privateProject/gemento/.env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars


def get_caddy_log_via_ssh(env: dict[str, str]) -> tuple[str, bool]:
    """SSH로 n100 서버의 Caddy 로그를 인출합니다. 실패 시 가상 시뮬레이션 로그를 반환합니다."""
    host = env.get("N100_SSH_HOST")
    port = int(env.get("N100_SSH_PORT", "22"))
    user = env.get("N100_SSH_USER")
    key_path = env.get("N100_SSH_KEY_PATH")
    password = env.get("N100_SSH_PASSWORD")
    log_path = env.get("N100_CADDY_LOG_PATH", "/var/log/caddy/access.log")
    
    # 플레이스홀더 상태거나 비어있으면 즉시 Fallback 진입
    if not host or host == "your_n100_ip" or user == "your_username":
        print("  [SSH] Connection credentials not updated. Using Mock Fallback Log.")
        return generate_mock_caddy_log(), True
        
    try:
        import paramiko
        print(f"  [SSH] Connecting to {user}@{host}:{port}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if key_path:
            key_path = os.path.expanduser(key_path)
            print(f"  [SSH] Using Private Key: {key_path}")
            ssh.connect(host, port=port, username=user, key_filename=key_path, timeout=10)
        else:
            ssh.connect(host, port=port, username=user, password=password, timeout=10)
        
        # 최근 1,500줄의 로그 획득
        cmd = f"tail -n 1500 {log_path}"
        print(f"  [SSH] Executing command: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        err = stderr.read().decode("utf-8", errors="ignore")
        if err:
            print(f"  [SSH Error] {err.strip()}. Using Mock Fallback Log.")
            ssh.close()
            return generate_mock_caddy_log(), True
            
        caddy_log = stdout.read().decode("utf-8", errors="ignore")
        ssh.close()
        
        if not caddy_log.strip():
            print("  [SSH] Log file is empty. Using Mock Fallback Log.")
            return generate_mock_caddy_log(), True
            
        print(f"  [SSH] Successfully fetched {len(caddy_log.encode('utf-8'))} bytes from {host}")
        return caddy_log, False
    except Exception as e:
        print(f"  [SSH Connect Failed] {e}. Using Mock Fallback Log.")
        return generate_mock_caddy_log(), True


def generate_mock_caddy_log() -> str:
    """100줄 분량의 가상 Caddy Access 로그 생성."""
    lines = []
    # 일반 정상 요청 로그 적재
    for i in range(1, 101):
        if i == 37:
            # 500 에러 로그 심기
            lines.append('192.168.1.103 - - [28/Jun/2026:14:52:20 +0900] "GET /api/v2/payment/checkout HTTP/1.1" 500 512')
        elif i == 52:
            # 401 에러 로그 심기
            lines.append('192.168.1.52 - - [28/Jun/2026:14:52:15 +0900] "POST /api/v1/auth/login HTTP/1.1" 401 256')
        elif i == 89:
            # 또 다른 500 에러 로그 심기
            lines.append('192.168.1.103 - - [28/Jun/2026:14:52:25 +0900] "GET /api/v2/payment/checkout HTTP/1.1" 500 512')
        else:
            lines.append(f'192.168.1.{i} - - [28/Jun/2026:14:52:00 +0900] "GET /static/assets/app_{i}.js HTTP/1.1" 200 4096')
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("n100 Caddy 로그 SSH 연동 및 에이전트 분석")
    print("=" * 80)
    
    env = load_env_vars()
    log_content, is_fallback = get_caddy_log_via_ssh(env)
    
    # Redis 적재
    redis_key = "ctx:caddy_n100_log:stdout"
    r = get_redis_client()
    r.set(redis_key, log_content)
    print(f"  [Setup] Spooled {len(log_content.encode('utf-8'))} bytes to Redis key: {redis_key}")
    
    # 목표 정의 및 검증용 채점 키워드 (Fallback 기준 또는 실제 분석 기준 유연 대응)
    objective = "Analyze the Caddy access log. Find the IP and URL path that caused the HTTP 500 Internal Server Error."
    
    # Fallback 또는 실제 로그 속 에러 패턴에 유연 대응하기 위한 채점 키워드
    scoring_keywords = [
        ["192.168.1.103", "192.168.1."],  # 에러 유발 IP
        ["/api/v2/payment/checkout", "checkout"],  # 에러 유발 URL
        ["500", "Internal Server Error"]  # HTTP 상태 코드
    ]
    
    # 채점 함수
    def score(ans) -> float:
        if not ans: return 0.0
        if isinstance(ans, dict):
            ans = json.dumps(ans, ensure_ascii=False)
        elif not isinstance(ans, str):
            ans = str(ans)
        matched = sum(1 for grp in scoring_keywords if any(t.lower() in ans.lower() for t in grp))
        return matched / len(scoring_keywords)

    prompt = (
        "We fetched the Caddy access log from the server. The raw log is stored in Redis.\n"
        f"Available Context Handle: {redis_key}\n\n"
        "Please use read_context or grep_context to inspect the log. "
        "Find the exact client IP address, request URL path, and HTTP status code that represents the server internal error."
    )

    print("\n[Start] Running Gemento Ephemeral Context Router (Hybrid Mode)...")
    start_time = time.time()
    tattoo, logs, ans = run_abc_chain(
        task_id="caddy_n100_analysis",
        objective=objective,
        prompt=prompt,
        constraints=["HTTP 500 에러를 유발한 IP와 요청 URL 경로를 정확히 밝혀라", "Caddy 로그 내에 발생한 상태코드를 함께 기입하라"],
        max_cycles=5,
        context_router=True,
        context_handles=[redis_key],
        error_blocks=True, # 하이브리드 슬라이싱 활성화
    )
    duration = time.time() - start_time
    score_val = score(ans)
    
    print("\n" + "=" * 80)
    print("n100 Caddy 로그 분석 결과 요약")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Connection: {'Fallback Simulation' if is_fallback else 'SSH Connected'}")
    print(f"Score: {score_val:.1%}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Answer: {ans}")
    print("-" * 80)
    
    # 결과 저장
    out_data = {
        "experiment": "caddy_n100_analysis",
        "model": MODEL_NAME,
        "is_fallback": is_fallback,
        "score": score_val,
        "duration_seconds": duration,
        "final_answer": ans,
        "cycles": len(logs),
        "tool_calls": [c.tool_calls for c in logs if c.tool_calls]
    }
    
    out_path = RESULTS_DIR / "caddy_n100_analysis_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"  → Analysis results saved: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
