"""제멘토 문신(Tattoo) 스키마 정의.

문신은 다음 추론의 유일한 입력이 되는 구조화된 외부 상태다.
로그가 아니라 상태(state)이며, 결론만 남기고 과정은 버린다.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class Phase(str, Enum):
    """계산 진행 단계. 유한 상태 머신."""
    DECOMPOSE = "DECOMPOSE"      # 문제를 하위 질문으로 분해
    INVESTIGATE = "INVESTIGATE"  # 하위 질문에 대해 사실 수집/추론
    SYNTHESIZE = "SYNTHESIZE"    # 수집된 사실을 종합하여 답 구성
    VERIFY = "VERIFY"            # 종합된 답의 정합성 검증
    CONVERGED = "CONVERGED"      # 종료 조건 충족, 최종 결과 확정


class AssertionStatus(str, Enum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"


# ── Phase 전이 규칙 ──
VALID_TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.DECOMPOSE: {Phase.INVESTIGATE},
    Phase.INVESTIGATE: {Phase.INVESTIGATE, Phase.SYNTHESIZE},
    Phase.SYNTHESIZE: {Phase.VERIFY},
    Phase.VERIFY: {Phase.CONVERGED, Phase.INVESTIGATE},
    Phase.CONVERGED: set(),  # 수렴 후 재개 불가
}

# 어떤 phase에서든 confidence < FLOOR이면 VERIFY로 긴급 전환 가능
EMERGENCY_VERIFY_ALLOWED_FROM = {
    Phase.DECOMPOSE, Phase.INVESTIGATE, Phase.SYNTHESIZE,
}


@dataclass
class HandoffA2B:
    """Architect(A) -> Developer(B) 인계 문서."""
    blueprint: str = ""
    constraints: List[str] = field(default_factory=list)
    prioritized_focus: str = ""
    open_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "blueprint": self.blueprint,
            "constraints": self.constraints,
            "prioritized_focus": self.prioritized_focus,
            "open_questions": self.open_questions
        }

    @classmethod
    def from_dict(cls, d: dict) -> HandoffA2B:
        return cls(
            blueprint=d.get("blueprint", ""),
            constraints=d.get("constraints", []),
            prioritized_focus=d.get("prioritized_focus", ""),
            open_questions=d.get("open_questions", [])
        )


@dataclass
class HandoffB2C:
    """Developer(B) -> Reviewer(C) 인계 문서."""
    implementation_summary: str = ""
    deviations: List[dict] = field(default_factory=list)
    self_test_results: str = ""

    def to_dict(self) -> dict:
        return {
            "implementation_summary": self.implementation_summary,
            "deviations": self.deviations,
            "self_test_results": self.self_test_results
        }

    @classmethod
    def from_dict(cls, d: dict) -> HandoffB2C:
        return cls(
            implementation_summary=d.get("implementation_summary", ""),
            deviations=d.get("deviations", []),
            self_test_results=d.get("self_test_results", "")
        )


@dataclass
class RejectMemo:
    """Reviewer(C) -> A/B 반려 메모."""
    target_phase: str = "A"  # "A" or "B"
    failed_assertions: List[str] = field(default_factory=list)
    remediation_hint: str = ""

    def to_dict(self) -> dict:
        return {
            "target_phase": self.target_phase,
            "failed_assertions": self.failed_assertions,
            "remediation_hint": self.remediation_hint
        }

    @classmethod
    def from_dict(cls, d: dict) -> RejectMemo:
        return cls(
            target_phase=d.get("target_phase", "A"),
            failed_assertions=d.get("failed_assertions", []),
            remediation_hint=d.get("remediation_hint", "")
        )


@dataclass
class Assertion:
    """확정된 사실 하나. 문신의 핵심 단위."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    content: str = ""
    source_loop: int = 0
    confidence: float = 0.0
    status: AssertionStatus = AssertionStatus.ACTIVE
    invalidated_by: Optional[str] = None
    # Long-context 실험용 — Optional, 기본 None. 기존 실험 역호환 보장.
    # dict 구조: {"chunk_id": int, "span": [int, int] | None}
    evidence_ref: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "content": self.content,
            "source_loop": self.source_loop,
            "confidence": self.confidence,
            "status": self.status.value,
        }
        if self.invalidated_by:
            d["invalidated_by"] = self.invalidated_by
        if self.evidence_ref is not None:
            d["evidence_ref"] = self.evidence_ref
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Assertion:
        return cls(
            id=d["id"],
            content=d["content"],
            source_loop=d["source_loop"],
            confidence=d["confidence"],
            status=AssertionStatus(d["status"]),
            invalidated_by=d.get("invalidated_by"),
            evidence_ref=d.get("evidence_ref"),
        )


@dataclass
class Tattoo:
    """문신: 다음 추론을 가능하게 하는 구조화된 외부 상태."""

    # ── 메타 ──
    tattoo_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str = ""
    loop_index: int = 0
    parent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    # ── 목표 (불변) ──
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    termination: str = ""

    # ── 상태 (가변) ──
    phase: Phase = Phase.DECOMPOSE
    assertions: list[Assertion] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    next_directive: str = ""
    critique_log: list[dict] = field(default_factory=list)  # B의 비판 기록 (A-B-C용)

    # ── Handoff Protocol (실험 4.5) ──
    handoff_a2b: Optional[HandoffA2B] = None
    handoff_b2c: Optional[HandoffB2C] = None
    reject_memo: Optional[RejectMemo] = None

    # ── 무결성 ──
    assertion_hash: str = ""
    chain_hash: str = ""
    confidence: float = 1.0

    # ... (생략된 메서드들은 그대로 유지되도록 명령 수행)

    # ── 불변 규칙 적용 ──

    @property
    def active_assertions(self) -> list[Assertion]:
        return [a for a in self.assertions if a.status == AssertionStatus.ACTIVE]

    def compute_assertion_hash(self) -> str:
        """active assertion들의 해시를 계산한다."""
        data = json.dumps(
            [a.to_dict() for a in self.active_assertions],
            sort_keys=True, ensure_ascii=False,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def compute_chain_hash(self, parent_chain_hash: str = "") -> str:
        """부모의 chain_hash + 현재 assertion_hash로 체인 해시를 계산한다."""
        combined = parent_chain_hash + self.compute_assertion_hash()
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def finalize_integrity(self, parent_chain_hash: str = "") -> None:
        """무결성 필드를 확정한다. 문신 생성의 마지막 단계에서 호출."""
        self.assertion_hash = self.compute_assertion_hash()
        self.chain_hash = self.compute_chain_hash(parent_chain_hash)

    def verify_integrity(self) -> bool:
        """무결성을 검증한다. 해석 규약의 마지막 단계."""
        return self.assertion_hash == self.compute_assertion_hash()

    def can_transition_to(self, target: Phase) -> bool:
        """phase 전이가 유효한지 확인한다."""
        if self.phase == Phase.CONVERGED:
            return False
        if target == Phase.VERIFY and self.phase in EMERGENCY_VERIFY_ALLOWED_FROM:
            return True  # 긴급 VERIFY 전환
        return target in VALID_TRANSITIONS.get(self.phase, set())

    def add_assertion(self, content: str, confidence: float, source_loop: int) -> Assertion:
        """새 assertion을 추가한다. 수정은 불가, 추가만 가능."""
        a = Assertion(
            content=content,
            source_loop=source_loop,
            confidence=confidence,
            status=AssertionStatus.ACTIVE,
        )
        self.assertions.append(a)
        return a

    def invalidate_assertion(self, assertion_id: str, reason: str) -> bool:
        """assertion을 무효화한다. 내용 수정이 아닌 상태 변경."""
        for a in self.assertions:
            if a.id == assertion_id and a.status == AssertionStatus.ACTIVE:
                a.status = AssertionStatus.INVALIDATED
                a.invalidated_by = reason
                return True
        return False

    def to_dict(self) -> dict:
        d = {
            "meta": {
                "tattoo_id": self.tattoo_id,
                "task_id": self.task_id,
                "loop_index": self.loop_index,
                "parent_id": self.parent_id,
                "created_at": self.created_at,
            },
            "goal": {
                "objective": self.objective,
                "constraints": self.constraints,
                "termination": self.termination,
            },
            "state": {
                "phase": self.phase.value,
                "assertions": [a.to_dict() for a in self.assertions],
                "open_questions": self.open_questions,
                "next_directive": self.next_directive,
                "critique_log": self.critique_log,
            },
            "handoff": {},
            "integrity": {
                "assertion_hash": self.assertion_hash,
                "chain_hash": self.chain_hash,
                "confidence": self.confidence,
            },
        }
        if self.handoff_a2b:
            d["handoff"]["a2b"] = self.handoff_a2b.to_dict()
        if self.handoff_b2c:
            d["handoff"]["b2c"] = self.handoff_b2c.to_dict()
        if self.reject_memo:
            d["handoff"]["reject_memo"] = self.reject_memo.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Tattoo:
        meta = d["meta"]
        goal = d["goal"]
        state = d["state"]
        integrity = d["integrity"]
        handoff = d.get("handoff", {})
        
        t = cls(
            tattoo_id=meta["tattoo_id"],
            task_id=meta["task_id"],
            loop_index=meta["loop_index"],
            parent_id=meta.get("parent_id"),
            created_at=meta["created_at"],
            objective=goal["objective"],
            constraints=goal.get("constraints", []),
            termination=goal.get("termination", ""),
            phase=Phase(state["phase"]),
            assertions=[Assertion.from_dict(a) for a in state["assertions"]],
            open_questions=state.get("open_questions", []),
            next_directive=state.get("next_directive", ""),
            critique_log=state.get("critique_log", []),
            assertion_hash=integrity["assertion_hash"],
            chain_hash=integrity["chain_hash"],
            confidence=integrity["confidence"],
        )
        
        if "a2b" in handoff:
            t.handoff_a2b = HandoffA2B.from_dict(handoff["a2b"])
        if "b2c" in handoff:
            t.handoff_b2c = HandoffB2C.from_dict(handoff["b2c"])
        if "reject_memo" in handoff:
            t.reject_memo = RejectMemo.from_dict(handoff["reject_memo"])
            
        return t

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> Tattoo:
        return cls.from_dict(json.loads(s))


class FailureLabel(Enum):
    """trial result 의 failure / success 분류.

    namingConventions.md §9.3 와 Stage 2C `ErrorMode` 의 표준 정의.
    Stage 2C 의 `experiments/exp_h4_recheck/analyze.py:ErrorMode` 는 본 enum 의 alias.

    분류 의미:
    - NONE: 정답 (acc_v3 ≥ 0.5 등 task 별 기준)
    - FORMAT_ERROR: JSON parse / schema 위반 (final_answer 없음 또는 malformed)
    - WRONG_SYNTHESIS: 형식은 OK 인데 내용 틀림 (acc < 0.5, len > 10)
    - EVIDENCE_MISS: evidence_ref 누락 또는 잘못된 출처 (heuristic, Stage 2C+)
    - NULL_ANSWER: final_answer 가 None / 빈 문자열
    - CONNECTION_ERROR: WinError 10061 등 (Stage 2A `TrialError.CONNECTION_ERROR` 와 동기)
    - PARSE_ERROR: Stage 2A `TrialError.PARSE_ERROR` 와 동기
    - TIMEOUT: Stage 2A `TrialError.TIMEOUT` 와 동기
    - OTHER: 미분류
    """

    NONE = "none"
    FORMAT_ERROR = "format_error"
    WRONG_SYNTHESIS = "wrong_synthesis"
    EVIDENCE_MISS = "evidence_miss"
    NULL_ANSWER = "null_answer"
    CONNECTION_ERROR = "connection_error"
    PARSE_ERROR = "parse_error"
    TIMEOUT = "timeout"
    OTHER = "other"


def create_initial_tattoo(
    task_id: str,
    objective: str,
    constraints: list[str] | None = None,
    termination: str = "",
) -> Tattoo:
    """최초 루프를 위한 빈 문신을 생성한다."""
    t = Tattoo(
        task_id=task_id,
        loop_index=0,
        objective=objective,
        constraints=constraints or [],
        termination=termination,
        phase=Phase.DECOMPOSE,
        next_directive="문제를 하위 질문으로 분해하라.",
    )
    t.finalize_integrity()
    return t
