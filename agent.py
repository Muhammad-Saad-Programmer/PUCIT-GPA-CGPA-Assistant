import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, wrap_tool_call
from langchain.mcp import MCPAdapter
from langchain.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import START
from groq import APIError, BadRequestError

from llm import open_model

SYSTEM_PROMPT = """
You are a conversational GPA and CGPA assistant for a PUCIT BS(CS) student.
Use tools for every calculation, including credit totals. Never do arithmetic
yourself. Use facts already provided in this conversation. Never invent marks,
credit hours, CGPA, or semester numbers. Ask for one or two missing facts at
a time. For standard course credits use the scheme returned by the tools.
If only some courses have marks, label any GPA as covering those courses.
MD-001 and MD-002 are non-credit pass/fail and excluded. Every other course in
the scheme counts, including Quran Translation at 0.5 credit hours.

To plan a target, confirm the target, current CGPA, actual completed hours,
and the semester the plan starts in. Use get_semester_courses for the inclusive
credit totals from that semester through each possible end semester.
get_remaining_credit_hours counts only the semesters AFTER its argument.
For a this-semester or unspecified deadline, start with the current semester.
For an explicit graduation deadline, use the whole remaining window.
Call required_gpa_for_target with the student's figures and the tool's hours
for the chosen window. Compare the unrounded result with 4.0. If it exceeds
4.0, extend by exactly one semester and call the tool again. Continue in
this turn until the first feasible window or graduation. Give the start and
end semesters and the required average. If no window works, explain that
the target cannot be reached by graduation. Never present a GPA above 4.0
as advice. If a tool returns an error, clarify the input before proceeding.

Offer to save after a semester GPA, projected CGPA, or target plan. Skip
the offer for a clarification or single grade lookup. Save a report only on
explicit request after a result. Start each new conversation empty.
Redirect questions about course repeats or improvements, curves or relative
grading, moderation, incomplete grades, withdrawals, freezes, and unrelated
topics to the supported GPA and course tasks.
When asked about your capabilities or tools, summarize what you can do for the user in plain, student-friendly language using bullet points. Do not expose raw internal function names (e.g., snake_case tool identifiers). Include 2-3 short example prompts they can try.
"""

@wrap_model_call
async def require_model_reply(request, handler):
    """Retry only the model step when Groq returns an unusable generation."""
    for attempt in range(2):
        if attempt == 1:
            request = request.override(system_message=SystemMessage(content=(
                request.system_message.text
                + "\nIf you need a tool, make one native tool call with its declared "
                  "arguments. Otherwise reply to the student in plain language."
            )))
        try:
            response = await handler(request)
        except BadRequestError as error:
            body = error.body
            details = body.get("error", body) if isinstance(body, dict) else None
            if not isinstance(details, dict) or details.get("code") != "output_parse_failed":
                raise
            continue
        reply = response.result[0]
        if not reply.invalid_tool_calls and (reply.tool_calls or reply.text.strip()):
            return response
    raise ValueError("Groq returned no usable reply after two attempts. Please retry your question.")


OUTAGE_MESSAGE = "The GPA tool server is temporarily unavailable. Please try again."
MCP_TIMEOUT = 20


class MCPUnavailable(Exception):
    """A discovery or execution failure at the remote tool boundary."""


@wrap_tool_call
async def guard_mcp_call(request, handler):
    try:
        async with asyncio.timeout(MCP_TIMEOUT):
            response = await handler(request)
    except Exception:
        raise MCPUnavailable(OUTAGE_MESSAGE) from None
    if isinstance(response, ToolMessage) and response.status == "error":
        raise MCPUnavailable(OUTAGE_MESSAGE)
    return response


@asynccontextmanager
async def open_agent(checkpointer=None, *, history_only=False):
    """Skip network discovery for the CLI graph that only reads and edits history."""
    server = os.getenv(
        "MCP_URL",
        "https://pucit-gpa-cgpa-assistant-production.up.railway.app/mcp",
    )
    tools = []
    if not history_only:
        try:
            async with asyncio.timeout(MCP_TIMEOUT):
                tools = await MCPAdapter(server).list_tools()
        except Exception:
            raise MCPUnavailable(OUTAGE_MESSAGE) from None
        if not tools:
            raise MCPUnavailable(OUTAGE_MESSAGE)
    async with open_model() as model:
        yield create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[require_model_reply, guard_mcp_call],
            checkpointer=checkpointer,
        )


TOOL_STATUS = {
    "marks_to_grade_points": "Converting marks to grade points...",
    "calculate_semester_gpa": "Calculating the semester GPA...",
    "calculate_new_cgpa": "Calculating the projected CGPA...",
    "required_gpa_for_target": "Calculating the GPA needed for your target...",
    "get_semester_courses": "Looking up semester courses...",
    "get_remaining_credit_hours": "Calculating the remaining credit hours...",
    "save_report": "Saving your report...",
}


async def stream_turn(agent, messages, config, on_text, on_status):
    """Display one turn and return its completed node messages for the browser UI."""
    completed = []
    streamed_text = False
    async for chunk in agent.astream(
        {"messages": messages}, config, stream_mode=["updates", "messages"], version="v2"
    ):
        data = chunk.get("data")
        if chunk.get("type") == "messages":
            if not isinstance(data, (tuple, list)) or len(data) != 2:
                continue
            token, metadata = data
            if (isinstance(metadata, dict) and metadata.get("langgraph_node") == "model"
                    and isinstance(token, AIMessageChunk) and not token.tool_call_chunks
                    and token.text):
                on_text(token.text)
                streamed_text = True

        elif chunk.get("type") == "updates" and isinstance(data, dict):
            for node, update in data.items():
                if not isinstance(update, dict):
                    continue
                outputs = update.get("messages")
                if not isinstance(outputs, (tuple, list)):
                    continue
                completed.extend(outputs)
                if node == "tools":
                    on_status("")
                for message in outputs:
                    if node != "model" or not isinstance(message, AIMessage):
                        continue
                    if message.tool_calls:
                        for call in message.tool_calls:
                            on_status(TOOL_STATUS.get(call.get("name"), "Using a GPA tool..."))
                    elif message.text and not streamed_text:
                        # Some model responses arrive in a single completed update.
                        on_text(message.text)
                    streamed_text = False
    return completed


async def stream_browser_turn(messages, on_text, on_status):
    async with open_agent() as agent:
        completed = await stream_turn(agent, messages, None, on_text, on_status)
    return [*messages, *completed]


async def repair_tool_history(agent, config, state):
    """Patch unfinished calls in place, keeping matched results and later turns."""
    messages = state.values.get("messages", [])
    replacements = []
    for index, message in enumerate(messages):
        if not isinstance(message, AIMessage) or not message.tool_calls:
            continue
        answered = set()
        pos = index + 1
        while pos < len(messages) and isinstance(messages[pos], ToolMessage):
            answered.add(messages[pos].tool_call_id)
            pos += 1
        matched = [call for call in message.tool_calls if call["id"] in answered]
        if len(matched) == len(message.tool_calls):
            continue
        if matched:
            # Groq also accepts raw provider tool_calls. Keep only normalized calls.
            extra = dict(message.additional_kwargs)
            extra.pop("tool_calls", None)
            replacements.append(message.model_copy(
                update={"tool_calls": matched, "additional_kwargs": extra}
            ))
        else:
            replacements.append(AIMessage(id=message.id, content=OUTAGE_MESSAGE))
    if replacements:
        await agent.aupdate_state(config, {"messages": replacements}, as_node=START)


async def select_thread(agent, name):
    config = {"configurable": {"thread_id": name}}
    state = await agent.aget_state(config)
    if state.created_at is None:
        await agent.aupdate_state(config, {"messages": []}, as_node=START)
    else:
        await repair_tool_history(agent, config, state)
    return config


async def show_history(agent, config):
    state = await agent.aget_state(config)
    messages = state.values.get("messages", [])
    if not messages:
        print("No saved messages.")
    for message in messages:
        if isinstance(message, HumanMessage):
            print("You:", message.text)
        elif isinstance(message, AIMessage) and not message.tool_calls and message.text:
            print("Assistant:", message.text)


async def chat():
    database = Path(__file__).resolve().with_name("cgpa_memory.sqlite")
    async with AsyncSqliteSaver.from_conn_string(str(database)) as memory:
        names = {
            entry.config["configurable"]["thread_id"]
            async for entry in memory.alist(None)
        }
        print("Saved chats:", ", ".join(sorted(names)) or "(none)")
        try:
            name = input("Who is chatting? ").strip()
            while not name:
                name = input("Enter a student name: ").strip()
        except EOFError:
            return
        async with open_agent(memory, history_only=True) as history:
            await chat_loop(history, memory, name)


async def chat_loop(history, memory, name):
    config = await select_thread(history, name)
    print("GPA/CGPA Assistant")
    print("Commands: /switch <name>, /history, /forget, exit")

    while True:
        try:
            user_input = input(f"\n{name}> ").strip()
        except EOFError:
            break

        if user_input.lower() == "exit":
            break
        if not user_input:
            continue
        command = user_input.split(maxsplit=1)
        if command[0] == "/switch":
            if len(command) == 1:
                print("Usage: /switch <name>")
            else:
                name = command[1]
                config = await select_thread(history, name)
                print(f"Switched to {name}.")
            continue
        if user_input == "/history":
            await show_history(history, config)
            continue
        if user_input == "/forget":
            await memory.adelete_thread(name)
            print(f"Deleted the chat for {name}. Your next message starts a fresh chat.")
            continue

        started_reply = False

        def write_text(text):
            nonlocal started_reply
            if not started_reply:
                print("Assistant: ", end="")
                started_reply = True
            print(text, end="", flush=True)

        def write_status(status):
            nonlocal started_reply
            if status:
                if started_reply:
                    print()
                    started_reply = False
                print(status, flush=True)

        try:
            async with open_agent(memory) as agent:
                await stream_turn(agent, [HumanMessage(content=user_input)], config, write_text, write_status)
        except MCPUnavailable:
            state = await history.aget_state(config)
            await repair_tool_history(history, config, state)
            print("\n" + OUTAGE_MESSAGE)
        except (APIError, ValueError):
            print("\nCould not complete your request. Please try again.")
        else:
            print()


if __name__ == "__main__":
    asyncio.run(chat())
