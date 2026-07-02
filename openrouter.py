import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from backend.routers.tasks import create_task_db, TaskRequest
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.database import SessionLocal

load_dotenv()

def generate_summary(transcript: str,meeting_datetime: str,team_members: list[dict]) -> str:
    """
    Generate meeting summary using OpenRouter GPT-OSS-120B.
    """

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""
You are an expert project manager and meeting analyst.

The meeting occurred at:

{meeting_datetime}

The authenticated user is the meeting manager.

The following team members belong to this manager:

{team_members}

IMPORTANT:

- Only assign tasks to people from the team_members list.
- Use the provided IDs.
- Never invent IDs.
- Never invent employees.
- If an assignee cannot be matched to a team member, do not create the task.

STEP 1 - Identify Participants

- Extract all participants mentioned in the meeting.
- Include role if explicitly mentioned.

STEP 2 - Identify Decisions

- Extract only decisions explicitly made.
- Do not infer decisions.

STEP 3 - Identify Risks

- Extract risks, blockers, concerns, dependencies, and issues.
- Include owner if explicitly mentioned.

STEP 4 - Extract Tasks

For every explicitly assigned task:

- Create a short title.
- Create a description.
- Determine priority:
  - HIGH
  - MEDIUM
  - LOW
- Determine assignee_id from the provided team_members.
- Determine assigned_by.
- Set completed to false.

Deadline Rules:

- Convert relative deadlines using the meeting datetime.
- Examples:
  - tomorrow afternoon
  - Friday evening
  - next Tuesday
  - before Wednesday

- Return deadline as:

YYYY-MM-DDTHH:MM:SS

- Preserve original wording in deadline_text.

- If deadline is not explicitly mentioned:

deadline = null
deadline_text = null

Task Rules:

- Never invent tasks.
- Never infer tasks.
- Only include tasks explicitly assigned.
- Do not duplicate tasks repeated during meeting recap.
- If assigned_by is not explicitly mentioned, use "Not Mentioned".
- If priority cannot be determined, use "MEDIUM".

STEP 5 - Generate Summary

Create a concise 3-5 sentence summary.

Return ONLY valid JSON.
No markdown.
No explanations.

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
            "title": "",
            "description": "",
            "priority": "HIGH|MEDIUM|LOW",
            "completed": false,
            "assignee_id": 0,
            "assigned_by": "",
            "deadline": null,
            "deadline_text": null
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
team_members = [
    {
        "id": 1,
        "name": "John"
    },
    {
        "id": 2,
        "name": "Priya"
    },
    {
        "id": 3,
        "name": "Anita"
    },
    {
        "id": 4,
        "name": "Arun"
    }
]

# content = generate_summary(transcript,datetime.now().isoformat(),team_members)
content = """
{
    "summary": "The team reviewed progress on the employee management system. John will finish RBAC and deploy authentication to staging by Friday, then begin analytics API work. Priya will complete authentication testing by Monday, Rahul will obtain leave management requirements by tomorrow afternoon, and Arun will deliver a database scaling proposal before Wednesday. Analytics APIs were designated as the highest priority after authentication.",
    "participants": [
        {
            "name": "Rahul",
            "role": "Project Manager"
        },
        {
            "name": "John",
            "role": "Backend Developer"
        },
        {
            "name": "Priya",
            "role": "QA Engineer"
        },
        {
            "name": "Anita",
            "role": "Frontend Developer"
        },
        {
            "name": "Arun",
            "role": "DevOps Engineer"
        }
    ],
    "decisions": [
        "Analytics APIs become the highest priority after authentication."
    ],
    "risks": [
        {
            "description": "Database utilization is at 82% and may hit storage limits within the next six to eight weeks.",
            "owner": "Arun"
        },
        {
            "description": "Final leave management requirements are not yet received, impacting dashboard screens.",
            "owner": "Priya"
        }
    ],
    "tasks": [
        {
            "title": "Complete role-based access control (RBAC)",
            "description": "Implement RBAC for the authentication service.",
            "priority": "HIGH",
            "completed": false,
            "assignee_id": 1,
            "assigned_by": "Rahul",
            "deadline": "2026-07-05T23:59:59",
            "deadline_text": "by Friday"
        },
        {
            "title": "Deploy authentication service to staging",
            "description": "Deploy the completed authentication service to the staging environment.",
            "priority": "HIGH",
            "completed": false,
            "assignee_id": 1,
            "assigned_by": "Rahul",
            "deadline": "2026-07-05T18:00:00",
            "deadline_text": "Friday evening"
        },
        {
            "title": "Complete authentication testing",
            "description": "Test the authentication service after deployment.",
            "priority": "MEDIUM",
            "completed": false,
            "assignee_id": 2,
            "assigned_by": "Rahul",
            "deadline": "2026-07-06T23:59:59",
            "deadline_text": "by Monday"
        },
        {
            "title": "Obtain finalized leave management requirements",
            "description": "Gather the final leave management requirements from the product team.",
            "priority": "MEDIUM",
            "completed": false,
            "assignee_id": 0,
            "assigned_by": "Rahul",
            "deadline": "2026-07-03T15:00:00",
            "deadline_text": "by tomorrow afternoon"
        },
        {
            "title": "Prepare database scaling proposal",
            "description": "Create a proposal for scaling the database to handle future growth.",
            "priority": "MEDIUM",
            "completed": false,
            "assignee_id": 4,
            "assigned_by": "Rahul",
            "deadline": "2026-07-08T00:00:00",
            "deadline_text": "before Wednesday"
        },
        {
            "title": "Start analytics APIs development",
            "description": "Begin development of analytics APIs after authentication deployment.",
            "priority": "HIGH",
            "completed": false,
            "assignee_id": 1,
            "assigned_by": "Rahul",
            "deadline": null,
            "deadline_text": null
        }
    ]
}
"""
print(content)
data = json.loads(content)