# PUCIT BS(CS) GPA & CGPA Assistant

Ask about marks, semester GPA, projected CGPA, target GPA, courses, and graded credit hours from the terminal or Streamlit. Both interfaces use the same LangChain agent. Groq handles the conversation, and a local FastMCP server performs the calculations and course lookups.

## Setup

From the repository root, create a virtual environment using Python 3.12 (the version used to test this project).

```bash
python -m venv .venv
```

Activate it in each terminal. On Linux or macOS, run `source .venv/bin/activate`. On Windows PowerShell, run `.\.venv\Scripts\Activate.ps1`. Install the agent, app, and server dependencies together:

```bash
python -m pip install -r requirements.txt -r server/requirements.txt
```

For chat, create a local `.env` beside `agent.py` using `.env.example` as the template. Set your Groq key and the MCP endpoint:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
MCP_URL=http://127.0.0.1:8000/mcp
```

## Run the assistant

**Terminal 1 — MCP server.** From the repository root, run:

```bash
cd server
python server.py
```

Leave this terminal running while using either chat interface.

**Terminal 2 — chat.** From the repository root with the same environment active, choose an interface:

| Interface | Command | How to use it |
|---|---|---|
| Terminal | `python agent.py` | Choose a student name to open a saved chat. Type `exit` to quit. |
| Streamlit | `python -m streamlit run app.py` | Open the local URL printed in the terminal. Use **Clear Conversation** to start again. |

The terminal saves chats in `cgpa_memory.sqlite` beside `agent.py`. Choose the same student name after a restart to resume. Use `/switch <name>` to change chats, `/history` to read the current chat, or `/forget` to permanently delete it. Streamlit keeps its own browser-session history. **Clear Conversation** resets that session.

Both chat interfaces need internet access to Groq. To check the running MCP server independently of Groq or an API key, run these commands from the activated environment:

```bash
fastmcp list http://127.0.0.1:8000/mcp
fastmcp call http://127.0.0.1:8000/mcp get_remaining_credit_hours current_semester=5
```

Expect seven tools and **51.5** graded hours remaining after semester 5. To check only the server in a separate environment, install `server/requirements.txt`.

## Where to make changes

| File | Role |
|---|---|
| `server/tools.py` | Course data, grading rules, GPA calculations, and report writing used by MCP. |
| `server/server.py` | Registers the seven tools and starts the HTTP endpoint. |
| `agent.py` | System prompt, model retry middleware, MCP discovery, async turns, and CLI. |
| `llm.py` | Loads the environment and opens the Groq model client. |
| `app.py` | Streamlit chat UI and session history. |
| `tools.py` | Standalone GPA and course functions. The running server imports its own copy in `server/`. |

Relative report filenames resolve from the repository root. Ask for a path such as `reports/gpa.txt` to save inside the Git-ignored reports folder. The server creates that folder on the first such save.

## Prompts to test the assistant

Start each row in a fresh conversation using **Clear Conversation** in Streamlit or a new student name in the CLI.
Send follow-ups in the same chat. Compare the result and behavior, allowing for different wording.

| Try this prompt | What to check |
|---|---|
| I got 82 marks. What are my grade points? | **3.7**. A single grade lookup should end without a report offer. |
| Give me the grade points for 49, 50, 55, 58, 61, 65, 70, 75, 80, and 85 marks, in that order. | **0.0, 1.0, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0**. |
| In semester 5 I got 78 in Analysis of Algorithms, 85 in AI, and 64 in HCI. What's my GPA for these three courses? | **3.20** across the three named courses. Other semester courses have unknown marks. |
| In semester 5 I scored 85 in every course except Quran Translation V, where I got 50. I also passed MD-001 and MD-002. What's my full semester GPA? | **3.92** over **18.5** graded credits. Quran Translation contributes **0.5** credit hours. Both Math Deficiency courses are excluded. |
| In semester 2 I got 85 in Programming Fundamentals and 50 in its lab. What's my GPA for just those two? | **3.25**. The course carries **3** credits and the separate lab carries **1**. |
| Show me the semester 5 courses with their codes, credit hours, and semester total. | Seven courses, including **CC-310 Artificial Intelligence (3.0)** and **HQ-005 Quran Translation V (0.5)**. Total **18.5**. |
| How many graded credit hours are left after I finish semester 5? | **51.5**. Follow up with “And after semester 8?” Expect **0**. |
| My CGPA is 3.1 after 64 credits. If I get a 3.6 this semester, where do I end up? | It should ask for the missing semester hours or semester number. Reply **“I'm taking 18.5 credits.”** Expect **3.21**. |
| I want to graduate with a 3.5. What do I need from here? | It should ask for missing facts. Reply **“I'm starting semester 5, with a 3.0 CGPA and 64 completed credits. I follow the standard scheme.”** Expect about **3.96** across the remaining **70** credits. |
| I've completed 18.5 credits with a 3.0 CGPA. I'm taking the standard 18.5 credits in semester 5. Can I reach a 3.5 CGPA this semester? | **Exactly 4.0** is achievable in that semester. The plan should stop there. |
| I'm starting semester 8 with a 3.0 CGPA and 119.5 completed credits. Can I graduate with a 4.0 if I take the standard 14.5 credits? | Explain that the target is **unreachable by graduation**, even with a 4.0 this semester. |
| What grade points do I get for 101 marks? | Explain the valid range **0–100** and ask for corrected marks. Also try **−1**. |
| What courses are in semester 9? | Explain that the scheme covers **semesters 1–8**. |
| Calculate my GPA from grade points [4.0, 3.0] and credit hours [3.0]. | Ask for the missing credit value or a corrected list. No GPA can be calculated yet. |
| My CGPA is 4.5 after 64 credits. If I get 3.6 over 18.5 credits, what will my CGPA be? | Ask for a current CGPA in **0–4**. |
| Can you calculate how repeating a course will replace my old grade? | Explain which GPA questions the assistant can help with. Repeat with a grading curve, withdrawal, or unrelated question. |

### Multi-turn target plan, report saving, and reset

1. Ask **“What GPA do I need this semester?”** Expect one or two clarifying questions.
2. Reply **“I'm in semester 5. My CGPA is 3.0 and my target is 3.4.”** It still needs your actual completed credits.
3. Reply **“I've completed 64 credits. I follow the standard scheme.”** The first feasible window ends in **semester VII**, with an average of about **3.86**. For checking the calculation, semester V alone requires **4.78**, and V–VI requires **4.09**. The reply can summarize the first feasible window.
4. At this point it should offer to save the plan and wait for permission. Reply **“Save this plan as reports/viva_gpa_test.txt.”** Use a new filename. Open the file in the reports folder and verify it contains the target and the semester VII plan.
5. Clear the conversation and ask **“What was my target CGPA?”** It should ask you for the target again.

## Scope

This assistant only handles questions about GPA, CGPA, grades, credit hours, and PUCIT course-related information. It does not answer unrelated questions.

Do not share or submit your `.env` file because it contains your private API key.
