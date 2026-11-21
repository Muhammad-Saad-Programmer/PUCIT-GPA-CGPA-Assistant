# PUCIT BS(CS) GPA & CGPA Assistant

A simple Streamlit assistant for calculating GPA, CGPA, grades, and credit-hour information for PUCIT BS(CS) students.

## Main Features

- Convert marks into grade points
- Calculate semester GPA
- Project a new CGPA
- Calculate the GPA needed to reach a target CGPA
- View semester courses and credit hours
- Calculate remaining credit hours
- Save a useful GPA or CGPA report when requested

## Technologies Used

- Python
- Streamlit
- LangChain
- Groq API
- python-dotenv

## Project Structure

```text
assignment_02/
├── app.py       # Streamlit user interface and chat handling
├── agent.py     # GPA assistant agent and instructions
├── llm.py       # Groq language model configuration
├── tools.py     # GPA, CGPA, grade, course, and report tools
└── README.md    # Project documentation
```

## Installation

1. Clone or download this project.
2. Open a terminal in the project folder.
3. Create a virtual environment:

	```bash
	python -m venv .venv
	```

4. Activate the virtual environment.

	On Linux/macOS:

	```bash
	source .venv/bin/activate
	```

	On Windows:

	```powershell
	.venv\Scripts\activate
	```

5. Install the required packages:

	```bash
	python -m pip install streamlit langchain langchain-groq python-dotenv
	```

## Configure the `.env` File

Create a file named `.env` in the project folder and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with your actual API key.

## Run the App

Start the Streamlit app with:

```bash
python -m streamlit run app.py
```

On Windows, use the virtual-environment interpreter to avoid loading packages
from a different Python installation:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Then open the local URL shown in the terminal.

For the terminal conversation, run `python agent.py`. Both interfaces use the
same Groq model and require an internet connection for chat.

## Prompts to test the assistant

Start each row in a fresh conversation using **Clear Conversation** (or restart the CLI).
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
| Can you calculate how repeating a course will replace my old grade? | Explain the assignment's scope and redirect to a supported GPA task. Repeat with a grading curve, withdrawal, or unrelated question. |

### Multi-turn target plan, report saving, and reset

1. Ask **“What GPA do I need this semester?”** Expect one or two clarifying questions.
2. Reply **“I'm in semester 5. My CGPA is 3.0 and my target is 3.4.”** It still needs your actual completed credits.
3. Reply **“I've completed 64 credits. I follow the standard scheme.”** The first feasible window ends in **semester VII**, with an average of about **3.86**. For checking the calculation, semester V alone requires **4.78**, and V–VI requires **4.09**. The reply can summarize the first feasible window.
4. At this point it should offer to save the plan and wait for permission. Reply **“Save this plan as viva_gpa_test.txt.”** Use a new filename. Open the file in the project folder and verify it contains the target and the semester VII plan.
5. Clear the conversation and ask **“What was my target CGPA?”** It should ask you for the target again.

## Scope

This assistant only handles questions about GPA, CGPA, grades, credit hours, and PUCIT course-related information. It does not answer unrelated questions.

Do not share or submit your `.env` file because it contains your private API key.
