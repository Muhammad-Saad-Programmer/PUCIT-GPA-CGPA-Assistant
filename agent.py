import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain.mcp import MCPAdapter
from langchain.messages import HumanMessage, SystemMessage
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


@asynccontextmanager
async def open_agent(checkpointer=None):
    """Discover remote tools and attach them to the GPA agent."""
    server = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    tools = await MCPAdapter(server).list_tools()
    async with open_model() as model:
        yield create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[require_model_reply],
            checkpointer=checkpointer,
        )


async def invoke_turn(messages):
    """Run a Streamlit turn with discovery and invocation on the same event loop."""
    async with open_agent() as agent:
        return await agent.ainvoke({"messages": messages})


async def select_thread(agent, name):
    config = {"configurable": {"thread_id": name}}
    state = await agent.aget_state(config)
    if state.created_at is None:
        await agent.aupdate_state(config, {"messages": []}, as_node=START)
    return config


async def show_history(agent, config):
    state = await agent.aget_state(config)
    messages = state.values.get("messages", [])
    if not messages:
        print("No saved messages.")
    for message in messages:
        print(message.pretty_repr())


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
        async with open_agent(memory) as agent:
            await chat_loop(agent, memory, name)


async def chat_loop(agent, memory, name):
    config = await select_thread(agent, name)
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
                config = await select_thread(agent, name)
                print(f"Switched to {name}.")
            continue
        if user_input == "/history":
            await show_history(agent, config)
            continue
        if user_input == "/forget":
            await memory.adelete_thread(name)
            print(f"Deleted the chat for {name}. Your next message starts a fresh chat.")
            continue

        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]}, config=config
            )
        except (APIError, ValueError) as error:
            print(f"Request failed ({type(error).__name__}): {error}")
            continue

        print("\nAssistant:", result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(chat())
