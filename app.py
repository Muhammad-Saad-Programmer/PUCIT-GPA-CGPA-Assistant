import asyncio

import streamlit as st
from langchain.messages import AIMessage, HumanMessage


st.set_page_config(page_title="PUCIT GPA Assistant", page_icon="🎓", layout="centered")
st.title("PUCIT GPA & CGPA Assistant")
st.caption("Calculate GPA, project CGPA, and look up semester courses and credit hours.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("🎓 GPA Assistant")
    st.markdown(
        "- Semester GPA and projected CGPA\n"
        "- Target GPA planning\n"
        "- Courses and remaining credit hours\n"
        "- Save a GPA report"
    )
    if st.button("Clear Conversation"):
        st.session_state.messages = []

# Keep tool messages in the history passed to the agent.
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        st.chat_message("user").markdown(message.text)
    elif isinstance(message, AIMessage) and not message.tool_calls and message.text:
        st.chat_message("assistant").markdown(message.text)

question = st.chat_input("Ask about your GPA or CGPA...")
if question:
    st.chat_message("user").markdown(question)
    with st.chat_message("assistant"):
        try:
            from agent import MCPUnavailable, OUTAGE_MESSAGE, stream_browser_turn

            messages = st.session_state.messages + [HumanMessage(content=question)]
            status = st.empty()
            reply = st.empty()
            parts = []

            def display_text(text):
                parts.append(text)
                reply.markdown("".join(parts))

            def display_status(text):
                if text:
                    status.caption(text)
                else:
                    status.empty()

            try:
                st.session_state.messages = asyncio.run(
                    stream_browser_turn(messages, display_text, display_status)
                )
            except MCPUnavailable:
                reply.markdown(OUTAGE_MESSAGE)
                st.session_state.messages = [*messages, AIMessage(content=OUTAGE_MESSAGE)]
            finally:
                status.empty()
        except ImportError:
            st.error("Install the packages listed in the README, then retry.")
        except Exception:
            st.error("Could not complete your request. Please try again.")
