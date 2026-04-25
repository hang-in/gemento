"""External API clients for Exp10 (Gemini Flash, LM Studio)."""
from __future__ import annotations

import os
import re
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    """`.env` 파일 (export KEY=VALUE 또는 KEY=VALUE) 파싱. 따옴표 제거.

    secall 의 `export FOO=bar` 형식과 표준 dotenv `FOO=bar` 형식 모두 지원.
    파일 없거나 권한 오류 시 빈 dict 반환.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 'export ' prefix 제거
        if line.startswith("export "):
            line = line[len("export "):]
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        # 양 끝 따옴표 제거 (single 또는 double)
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        out[key] = value
    return out


def resolve_gemini_key() -> str | None:
    """Gemini API 키 우선순위: env > gemento/.env > ../secall/.env."""
    # 1. env 변수
    for env_name in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        v = os.environ.get(env_name)
        if v:
            return v
    # 2. gemento/.env
    here = Path(__file__).resolve()
    gemento_env = here.parent.parent.parent / ".env"  # .../gemento/.env
    env1 = load_env_file(gemento_env)
    for k in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        if env1.get(k):
            return env1[k]
    # 3. ../secall/.env
    secall_env = here.parent.parent.parent.parent / "secall" / ".env"
    env2 = load_env_file(secall_env)
    for k in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        if env2.get(k):
            return env2[k]
    return None
