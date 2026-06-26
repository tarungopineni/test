from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
load_dotenv()
def generate_summary(transcript: str) -> str:
    """
    Generate meeting summary using OpenRouter GPT-OSS-120B.
    """

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""
You are an expert project manager and meeting analyst.

Your task is to analyze the meeting transcript and extract structured information.

Follow these steps EXACTLY:

STEP 1 - Identify Participants
- Find all people mentioned in the meeting.
- Record their names and roles if available.

STEP 2 - Identify Decisions
- Extract only decisions that were explicitly made.
- Do not infer decisions.

STEP 3 - Identify Risks and Blockers
- Extract risks, blockers, concerns, dependencies, and issues discussed.
- Include owner if explicitly mentioned.

STEP 4 - Extract Action Items
For every action item:

1. Identify the assignee.
2. Identify the task.
3. Identify the deadline.
4. Identify who assigned the task if mentioned.

IMPORTANT:
- Never invent tasks.
- Never infer deadlines.
- Never create tasks from meeting announcements.
- Never create tasks from future possibilities.
- Only extract actions explicitly assigned in the meeting.
- If deadline is not explicitly mentioned, use "Not Mentioned".
- If assigner is not explicitly mentioned, use "Not Mentioned".

STEP 5 - Create Summary
Generate a concise summary of the meeting in 3-5 sentences.

Return ONLY valid JSON.

JSON Schema:

{{
    "summary": "",
    "participants": [
        {{
            "name": "",
            "role": ""
        }}
    ],
    "decisions": [
        ""
    ],
    "risks": [
        {{
            "description": "",
            "owner": ""
        }}
    ],
    "tasks": [
        {{
            "assignee": "",
            "assigned_by": "",
            "task": "",
            "deadline": ""
        }}
    ]
}}

Meeting Transcript:

{transcript}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b:free",
        messages=[
            {
                "role": "system",
                "content": "You are an expert project manager."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

transcript = '''Rahul (Project Manager):

Good morning everyone. Let's start with the progress update on the employee management system.

John (Backend Developer):

The authentication service is completed. Login, registration, and refresh token APIs are working. I still need to integrate role-based access control. I should be able to finish that by Friday.

Rahul:

Okay. Please deploy the authentication service to staging once RBAC is complete.

John:

Sure, I'll deploy it on Friday evening.

Priya (QA Engineer):

Once it's deployed, I'll start testing on Saturday morning. Assuming no major issues, testing should be completed by Monday.

Rahul:

Sounds good.

What about the employee dashboard?

Anita (Frontend Developer):

The dashboard UI is mostly done. Around eighty percent is complete. The only thing blocking me right now is the analytics API.

John:

I haven't started that yet. After RBAC deployment I'll begin work on analytics APIs. It should take about three days.

Rahul:

Okay. Analytics APIs become the highest priority after authentication.

Priya:

One concern. We still don't have the final leave management requirements from the product team.

Rahul:

Good point.

I'll speak with the product manager today and get the finalized requirements document by tomorrow afternoon.

Anita:

That would help because some dashboard screens depend on those requirements.

Rahul:

Noted.

Any infrastructure concerns?

Arun (DevOps Engineer):

Actually yes. Database utilization is already at eighty-two percent. If the current growth trend continues, we may hit storage limits within the next six to eight weeks.

Rahul:

That's concerning.

Can you prepare a database scaling proposal?

Arun:

Yes. I'll prepare a proposal and share it before Wednesday.

Rahul:

Perfect.

Let's quickly summarize.

John will complete RBAC by Friday and deploy authentication to staging Friday evening.

Priya will complete authentication testing by Monday.

Rahul will obtain the finalized leave management requirements by tomorrow afternoon.

John will start analytics APIs after authentication deployment.

Arun will prepare a database scaling proposal before Wednesday.

Anita will continue dashboard development once analytics APIs and requirements are available.

Thank you everyone. Let's meet again next Tuesday.'''

print(generate_summary(transcript))