"""Redis 기반 Ephemeral Context Router 도구 모음.

LLM 에이전트가 필요에 따라 대량의 로그 컨텍스트를 라인 범위 혹은 키워드 매칭으로
부분 인출할 수 있도록 돕는 read_context 및 grep_context 도구를 제공합니다.
"""
from __future__ import annotations

import os
import re
import redis
from typing import Optional, Dict, Any

# Redis 기본 연결 정보 (Docker Compose 기본 포트 6379 사용)
REDIS_HOST = os.getenv("GEMENTO_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("GEMENTO_REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("GEMENTO_REDIS_DB", 0))

_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Redis 클라이언트 싱글톤 인스턴스 반환."""
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
    return _client


def read_context(handle: str, start_line: int, end_line: int) -> dict:
    """Redis 버퍼에서 지정된 범위의 라인을 인출합니다. (단일 호출 최대 500줄, 16KB 제한)

    Args:
        handle: Redis key (예: 'ctx:{run_id}:stdout')
        start_line: 시작 라인 번호 (1-indexed)
        end_line: 종료 라인 번호 (1-indexed)

    Returns:
        추출된 라인 텍스트 및 메타데이터가 포함된 dict
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
        
        lines = content.splitlines()
        total_lines = len(lines)
        
        start = max(1, start_line)
        end = min(total_lines, end_line)
        
        if start > end:
            return {
                "error": f"Invalid line range {start_line}-{end_line}. Total lines: {total_lines}",
                "total_lines": total_lines
            }
        
        # 최대 500줄 제약 강제
        truncated_by_lines = False
        if (end - start + 1) > 500:
            end = start + 500 - 1
            truncated_by_lines = True

        selected_lines = lines[start-1 : end]
        output_text = "\n".join(selected_lines)
        
        # 16KB(16384 bytes) 크기 제한 강제
        max_bytes = 16384
        truncated_by_bytes = False
        if len(output_text.encode("utf-8")) > max_bytes:
            output_bytes = output_text.encode("utf-8")[:max_bytes]
            output_text = output_bytes.decode("utf-8", errors="ignore")
            truncated_by_bytes = True
            
        return {
            "handle": handle,
            "start_line": start,
            "end_line": end,
            "total_lines": total_lines,
            "content": output_text,
            "truncated_by_lines": truncated_by_lines,
            "truncated_by_bytes": truncated_by_bytes
        }
    except Exception as e:
        return {"error": f"Redis connection or read error: {e}"}


def grep_context(handle: str, pattern: str) -> dict:
    """Redis 버퍼에서 지정된 정규식/텍스트 패턴과 일치하는 라인들을 인출합니다. (16KB 제한)

    Args:
        handle: Redis key (예: 'ctx:{run_id}:stdout')
        pattern: 검색할 문자열 또는 정규식 패턴

    Returns:
        매칭된 라인 정보 및 메타데이터가 포함된 dict
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
            
        lines = content.splitlines()
        matched_lines = []
        
        # 정규식 유효성 검사 및 컴파일
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            is_regex = True
        except re.error:
            is_regex = False
            
        for i, line in enumerate(lines, 1):
            if is_regex:
                if regex.search(line):
                    matched_lines.append(f"{i}: {line}")
            else:
                if pattern.lower() in line.lower():
                    matched_lines.append(f"{i}: {line}")
                    
        total_matches = len(matched_lines)
        output_text = "\n".join(matched_lines)
        
        # 16KB(16384 bytes) 크기 제한 강제
        max_bytes = 16384
        truncated = False
        if len(output_text.encode("utf-8")) > max_bytes:
            output_bytes = output_text.encode("utf-8")[:max_bytes]
            output_text = output_bytes.decode("utf-8", errors="ignore")
            truncated = True
            
        return {
            "handle": handle,
            "pattern": pattern,
            "total_matches": total_matches,
            "matches": output_text,
            "truncated": truncated
        }
    except Exception as e:
        return {"error": f"Redis connection or grep error: {e}"}


CONTEXT_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_context",
            "description": "Read a range of lines from a cached terminal output log stored in Redis. Recommended chunk limit is 500 lines (16KB).",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "The Redis key handle, e.g. 'ctx:{run_id}:stdout'",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Start line number (1-indexed, inclusive)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "End line number (1-indexed, inclusive)",
                    }
                },
                "required": ["handle", "start_line", "end_line"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_context",
            "description": "Search for lines matching a string or regex pattern in a cached terminal output log stored in Redis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "The Redis key handle, e.g. 'ctx:{run_id}:stdout'",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern or regex to search for",
                    }
                },
                "required": ["handle", "pattern"],
            },
        },
    },
]

CONTEXT_TOOL_FUNCTIONS = {
    "read_context": read_context,
    "grep_context": grep_context,
}

