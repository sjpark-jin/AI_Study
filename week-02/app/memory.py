"""
세션 기반 대화 메모리 관리자.
[실수 2,7 방어] 슬라이딩 윈도우 방식으로 최근 N개 메세지만 유지하여 토큰 폭발 및 메모리 누수 방지.
"""
import logging
from typing import Dict, List

log = logging.getLogger("memory")


class InMemorySessionStore:
    def __init__(self, max_messages: int = 6):
        # session_id -> list of {"role": "user"|"assistant", "content": str}
        self.store: Dict[str, List[Dict[str, str]]] = {}
        self.max_messages = max_messages

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """해당 세션의 최근 대화 기록을 반환."""
        return self.store.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """세션에 메시지 추가 (최대 수 초과 시 오래된 메시지 제거)."""
        if session_id not in self.store:
            self.store[session_id] = []
        self.store[session_id].append({"role": role, "content": content})
        
        # 슬라이딩 윈도우 적용
        if len(self.store[session_id]) > self.max_messages:
            self.store[session_id] = self.store[session_id][-self.max_messages:]

    def clear_session(self, session_id: str) -> bool:
        """세션 메모리 초기화."""
        if session_id in self.store:
            del self.store[session_id]
            log.info("세션 %s 초기화 완료", session_id)
            return True
        return False


# 전역 단일 세션 메모리 객체
session_store = InMemorySessionStore()
