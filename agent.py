from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain.messages import HumanMessage, SystemMessage
from groq import APIError, BadRequestError

from llm import llm

from tools import (
    calculate_new_cgpa,
    calculate_semester_gpa,
    get_remaining_credit_hours,
    get_semester_courses,
    marks_to_grade_points,
    required_gpa_for_target,
    save_report,
)


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
"""

@wrap_model_call
def require_model_reply(request, handler):
    """Retry only the model step when Groq returns an unusable generation."""
    for attempt in range(2):
        if attempt == 1:
            request = request.override(system_message=SystemMessage(content=(
                request.system_message.text
                + "\nIf you need a tool, make one native tool call with its declared "
                  "arguments. Otherwise reply to the student in plain language."
            )))
        try:
            response = handler(request)
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


agent = create_agent(
    model=llm,
    tools=[
        marks_to_grade_points,
        calculate_semester_gpa,
        calculate_new_cgpa,
        required_gpa_for_target,
        get_semester_courses,
        get_remaining_credit_hours,
        save_report,
    ],
    system_prompt=SYSTEM_PROMPT,
    middleware=[require_model_reply],
)


def chat():
    messages = []

    print("GPA/CGPA Assistant")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break

        if user_input.lower() == "exit":
            break

        if not user_input:
            continue
        try:
            result = agent.invoke({"messages": [*messages, HumanMessage(content=user_input)]})
        except (APIError, ValueError) as error:
            print(f"Request failed ({type(error).__name__}): {error}")
            continue

        messages = result["messages"]

        print("\nAssistant:", messages[-1].text)
if __name__ == "__main__":
    chat()
