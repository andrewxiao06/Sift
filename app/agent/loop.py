from pathlib import Path
from time import time

import anthropic

from app.agent.tools import TOOL_DEFINITIONS, TOOL_DISPATCH
from app.agent.trace import Trace
from app.config import AGENT_MAX_ITERATIONS, AGENT_MODEL, ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "agent_system_v1.md"
SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text().strip()


def run_agent(question: str, max_iterations: int = AGENT_MAX_ITERATIONS) -> dict:
    """Runs the agent loop for one question. Returns {"answer": str, "trace": [...]}."""

    messages = [{"role": "user", "content": question}]
    trace = Trace()
    tool_failure_counts = {}

    for iteration in range(max_iterations):
        # 1. call client.messages.create(model=AGENT_MODEL, tools=TOOL_DEFINITIONS,
        #    messages=messages, max_tokens=...)
        # 2. append the assistant's response to `messages` (its content, as returned)
        # 3. check response.stop_reason:
        #    - if it's NOT "tool_use" -> the model gave a final answer, extract the
        #      text and return {"answer": ..., "trace": trace.records}
        #    - if it IS "tool_use" -> there's at least one tool_use content block
        #      to handle (see below)

        # for each tool_use block in the response content:
        #   a. look up the tool name in TOOL_DISPATCH to get the actual function
        #   b. try calling it with the block's input (its arguments)
        #      - malformed/invalid args should NOT raise into this loop —
        #        catch validation errors and build an error tool_result instead
        #   c. record what happened in `trace` (tool name, args, latency, result)
        #   d. build a tool_result content block referencing the tool_use_id,
        #      append it to `messages` as a new user-role message

        # loop continues to the next iteration automatically (the for loop)
        response = client.messages.create(
            model=AGENT_MODEL,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
            max_tokens=5000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            answer_text = "".join(block.text for block in response.content if block.type == "text")
            return {"answer": answer_text, "trace": trace.records}

        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
        tool_result_blocks = []

        for tool_use in tool_use_blocks:
            tool_name = tool_use.name
            tool_args = tool_use.input
            tool_func = TOOL_DISPATCH.get(tool_name)

            if not tool_func:
                trace.record(tool_name, tool_args, None, {"error": "Unknown tool"})
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": f"Tool {tool_name} not found.",
                    "is_error": True,
                })
                continue

            try:
                start = time()
                result = tool_func(**tool_args)
                end = time()
                latency = end - start
                trace.record(tool_name, tool_args, latency, result)
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result),
                })
            except Exception as e:
                end = time()
                latency = end - start
                tool_failure_counts[tool_name] = tool_failure_counts.get(tool_name, 0) + 1
                trace.record(tool_name, tool_args, latency, {"error": str(e)})

                if tool_failure_counts[tool_name] > 2:
                    content = (
                        f"Tool {tool_name} has failed {tool_failure_counts[tool_name]} times. "
                        "Stop retrying it — answer with what you have, or state you cannot "
                        "complete this without it."
                    )
                else:
                    content = f"Error executing tool {tool_name}: {e}"

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": content,
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_result_blocks})


    # if the for loop finishes without returning, you hit max_iterations —
    # decide what "partial results" means here: return whatever you have,
    # clearly marked as incomplete, never silently pretend it succeeded
    
    return {"answer": None, "trace": trace.records, "incomplete": True}
