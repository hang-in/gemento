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


def aggregate_context(handle: str, pattern: str, group_by: str | None = None,
                      top_n: int = 10) -> dict:
    """Redis 로그에서 pattern 매치 라인을 전수 집계한다 (16KB 라인덤프 대신 카운트).

    group_by 가 capture group 을 가진 regex 면 그 그룹값별 카운트를 top_n 으로 반환.
    group_by 가 None 이면 매치 총수 + 소수 sample 라인만 반환.
    절단 없음 — top_n 행만 반환하므로 출력이 항상 작다.

    Args:
        handle: Redis key
        pattern: 매치 대상 문자열/정규식 (grep_context 와 동일 의미, IGNORECASE)
        group_by: (선택) capture group 1 개를 가진 정규식.
                  예: r"from (\\d+\\.\\d+\\.\\d+\\.\\d+)"  → IP 별 카운트.
                  예: r"(\\S+\\.service)"  → systemd unit 별 카운트.
        top_n: 반환할 상위 그룹 수 (기본 10)
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
        lines = content.splitlines()
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {"error": f"invalid pattern regex: {e}"}
        matched = [ln for ln in lines if regex.search(ln)]
        total = len(matched)

        if group_by:
            try:
                grp = re.compile(group_by, re.IGNORECASE)
            except re.error as e:
                return {"error": f"invalid group_by regex: {e}"}
            from collections import Counter
            counts: "Counter[str]" = Counter()
            for ln in matched:
                m = grp.search(ln)
                if m and m.groups():
                    counts[m.group(1)] += 1
            top = [{"value": v, "count": c} for v, c in counts.most_common(top_n)]
            return {"handle": handle, "pattern": pattern, "group_by": group_by,
                    "total_matches": total, "unique_groups": len(counts),
                    "top": top, "truncated": False}
        # group_by 없음 → 총수 + sample (절단 아님: sample 개수만 의도적으로 제한)
        sample = matched[:5]
        return {"handle": handle, "pattern": pattern, "group_by": None,
                "total_matches": total, "sample": sample,
                "note": "Use group_by (regex with one capture group) to aggregate by field.",
                "truncated": False}
    except Exception as e:
        return {"error": f"Redis connection or aggregate error: {e}"}


def list_failed_units(handle: str, top_n: int = 10) -> dict:
    """실패/재시작 중인 systemd unit 을 전수 집계해 top-N 반환 (인자 없는 preset).

    grep_context 로 검색어를 formulate 할 필요 없이, 표준 systemd 실패 신호
    ('Failed with result' / 'Main process exited' / 'start-limit' / '.service' churn)
    를 내부에서 스캔해 unit 별 실패-신호 카운트를 untruncated 로 돌려준다.
    per-attempt retrieval_gap(모델이 넓은 grep 후 포기) 우회용.

    Args:
        handle: Redis key
        top_n: 반환할 상위 unit 수 (기본 10)
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
        lines = content.splitlines()
        signal = re.compile(
            r"Failed with result|Main process exited|start-limit|entered failed state|Failed to start",
            re.IGNORECASE,
        )
        unit = re.compile(r"(\S+\.service)", re.IGNORECASE)
        from collections import Counter
        counts: "Counter[str]" = Counter()
        for ln in lines:
            if signal.search(ln):
                m = unit.search(ln)
                if m:
                    counts[m.group(1)] += 1
        top = [{"unit": u, "failure_signals": c} for u, c in counts.most_common(top_n)]
        return {"handle": handle, "signal_lines": sum(counts.values()),
                "unique_units": len(counts), "top": top, "truncated": False}
    except Exception as e:
        return {"error": f"Redis connection or scan error: {e}"}


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

FACET_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "aggregate_context",
            "description": (
                "Aggregate ALL matching lines in a cached log by count, with NO 16KB "
                "truncation. Use this instead of grep_context when a pattern has many "
                "matches and you need totals or the top contributors. If you give "
                "'group_by' (a regex with ONE capture group), it returns the top values "
                "by frequency. Examples: to find the IP with the most failed SSH logins, "
                "pattern='Failed password', group_by='from (\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+)'. "
                "To find which systemd unit fails most, pattern='Failed with result', "
                "group_by='(\\\\S+\\\\.service)'. Without group_by it returns the total "
                "match count plus a few sample lines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "The Redis key handle"},
                    "pattern": {"type": "string", "description": "Text/regex to match lines (IGNORECASE)"},
                    "group_by": {"type": "string", "description": "Optional regex with ONE capture group to aggregate by"},
                    "top_n": {"type": "integer", "description": "How many top groups to return (default 10)"},
                },
                "required": ["handle", "pattern"],
            },
        },
    },
]

FACET_TOOL_FUNCTIONS = {
    "aggregate_context": aggregate_context,
}

FAILED_UNITS_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_failed_units",
            "description": (
                "List the systemd units that are FAILING or crash-looping in a cached log, "
                "as an untruncated top-N count — NO search pattern needed. Call this FIRST "
                "when diagnosing a service crash/failure: it scans standard systemd failure "
                "signals ('Failed with result', 'Main process exited', start-limit, entered "
                "failed state) and returns the units with the most failure signals. Use it "
                "instead of guessing grep patterns. Returns {top:[{unit,failure_signals}], ...}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "The Redis key handle"},
                    "top_n": {"type": "integer", "description": "How many top units to return (default 10)"},
                },
                "required": ["handle"],
            },
        },
    },
]

FAILED_UNITS_TOOL_FUNCTIONS = {
    "list_failed_units": list_failed_units,
}

