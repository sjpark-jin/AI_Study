"""
Week 05 LLM Observability & Tracing 모듈.
에이전트/LLM 실행 단계, Latency, 토큰 소모 추정, 평가 점수 변화 흐름(Audit Trail)을 기록 및 반환한다.
"""
import time
from typing import List, Dict, Any, Optional


class StepTrace:
    def __init__(self, step_name: str, input_data: Any):
        self.step_name = step_name
        self.input_data = input_data
        self.output_data: Any = None
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.latency_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def complete(self, output_data: Any, metadata: Optional[Dict[str, Any]] = None):
        self.end_time = time.time()
        self.latency_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.output_data = output_data
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "latency_ms": self.latency_ms,
            "input": str(self.input_data)[:200],
            "output": str(self.output_data)[:300],
            "metadata": self.metadata,
        }


class ExecutionTracer:
    def __init__(self):
        self.traces: List[StepTrace] = []
        self.session_id: str = f"trace-{int(time.time()*1000)}"

    def start_trace(self, step_name: str, input_data: Any) -> StepTrace:
        trace = StepTrace(step_name, input_data)
        self.traces.append(trace)
        return trace

    def get_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_traces": len(self.traces),
            "total_latency_ms": sum(t.latency_ms for t in self.traces),
        }

    def export_all(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.traces]


# 인스턴스를 공유하거나 세션별로 사용할 수 있도록 준비
tracer_store: List[Dict[str, Any]] = []


def record_session_trace(session_data: Dict[str, Any]):
    tracer_store.append(session_data)
    # 메모리 관리를 위해 최근 50개 유지
    if len(tracer_store) > 50:
        tracer_store.pop(0)


def get_all_session_traces() -> List[Dict[str, Any]]:
    return tracer_store
