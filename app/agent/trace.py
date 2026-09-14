"""Structured record of every tool call an agent run makes — used for
debugging, computing cost/latency, and (Phase 2) streaming to the frontend.
"""

import time


class Trace:
    def __init__(self):
        self.records: list[dict] = []

    def record(self, tool_name: str, args: dict, latency: float | None, result) -> None:
        self.records.append(
            {
                "step": len(self.records) + 1,
                "tool": tool_name,
                "args": args,
                "latency_s": latency,
                "result": result,
                "timestamp": time.time(),
            }
        )
