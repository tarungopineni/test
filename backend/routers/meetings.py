from typing_extensions import Annotated
import whisper
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import *
from pydantic import BaseModel
from datetime import datetime
from .auth import get_current_user
from .tasks import TaskRequest, create_task_db
from ..models import Tasks
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

# =====================================================================================================================
    # openrouter

load_dotenv()

def transcribe_audio(audio_path: str, whisper_model: str = "medium") -> str:
    """
    Convert audio to English text using Whisper.
    """

    print("\nLoading Whisper model...")

    model = whisper.load_model(whisper_model)

    start_time = datetime.now()

    result = model.transcribe(
        audio_path,
        task="translate",  # Translate non-English speech to English
        fp16=False
    )

    end_time = datetime.now()

    elapsed = (end_time - start_time).total_seconds()

    print(f"\nTranscription completed in {elapsed:.2f} seconds")
    print(f"Detected language: {result['language']}")

    return result["text"]

def generate_summary(transcript: str,meeting_datetime: str,team_members: dict) -> str:
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

The following participants are known and can be referenced when assigning tasks:

{team_members}

IMPORTANT RULES

* Use ONLY IDs from the provided participants list.
* Never invent IDs.
* Never invent participants.
* Every task must have both:

  * manager_id
  * assignee_id
* manager_id is the ID of the person who assigned the task.
* assignee_id is the ID of the person who must complete the task.
* If either person cannot be matched to a provided participant, do not create the task.

STEP 1 — Participants

Extract all participants mentioned in the meeting.

For each participant return:

* name
* role

STEP 2 — Decisions

Extract only decisions explicitly made during the meeting.

Do not infer decisions.

STEP 3 — Risks and Blockers

Extract:

* risks
* blockers
* concerns
* dependencies
* issues

Include owner only if explicitly mentioned.

STEP 4 — Tasks

Extract ONLY explicitly assigned tasks.

For every task determine:

* title
* description
* priority
* completed
* manager_id
* assignee_id
* deadline
* deadline_text

Assignment Rules

Example:

Rahul: "Ramu, complete backend integration by tomorrow."

Return:

manager_id = Rahul's ID
assignee_id = Ramu's ID

Examples:

John: "Priya, please test the authentication service."

manager_id = John's ID
assignee_id = Priya's ID

Rahul: "Arun, prepare a database scaling proposal."

manager_id = Rahul's ID
assignee_id = Arun's ID

Priority Rules

Use:

* HIGH
* MEDIUM
* LOW

If priority cannot be determined, use MEDIUM.

Completed Rules

Always set:

completed = false

Deadline Rules

Use the meeting datetime as the reference date.

Convert relative dates such as:

* tomorrow
* Friday
* Friday evening
* next Tuesday
* before Wednesday
* in 3 days

into:

YYYY-MM-DDTHH:MM:SS

Store the original phrase in deadline_text.

Examples:

deadline = "2026-07-05T18:00:00"
deadline_text = "Friday evening"

If no explicit deadline exists:

deadline = null
deadline_text = null

Task Extraction Rules

* Never invent tasks.
* Never infer tasks.
* Only extract explicitly assigned tasks.
* Do not create tasks from general discussion.
* Do not create tasks from possibilities.
* Do not duplicate tasks repeated during meeting recap.

STEP 5 — Summary

Generate a concise 3–5 sentence summary.

Return ONLY valid JSON.

No markdown.
No explanations.
No extra text.

JSON Schema

{
"summary": "",
"participants": [
{
"name": "",
"role": ""
}
],
"decisions": [
""
],
"risks": [
{
"description": "",
"owner": ""
}
],
"tasks": [
{
"title": "",
"description": "",
"priority": "HIGH|MEDIUM|LOW",
"completed": false,
"manager_id": 0,
"assignee_id": 0,
"deadline": null,
"deadline_text": null
}
]
}

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
content = """{
  "summary": "The team reviewed progress on the employee management system. John will complete RBAC and deploy the authentication service to staging by Friday, after which analytics API development will begin. Priya will test the authentication service after deployment and complete testing by Monday. Rahul will obtain finalized leave management requirements, while Arun will prepare a database scaling proposal due to storage utilization concerns. Analytics APIs were designated as the highest priority after authentication work.",
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
      "description": "Database utilization is already at 82% and may hit storage limits within six to eight weeks.",
      "owner": "Arun"
    },
    {
      "description": "Final leave management requirements from the product team are not yet available and are blocking dependent dashboard work.",
      "owner": "Priya"
    }
  ],
  "tasks": [
    {
      "title": "Complete RBAC implementation",
      "description": "Implement role-based access control for the authentication service.",
      "priority": "HIGH",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 3,
      "deadline": "2026-07-03T23:59:59",
      "deadline_text": "by Friday"
    },
    {
      "title": "Deploy authentication service to staging",
      "description": "Deploy the authentication service to the staging environment after RBAC completion.",
      "priority": "HIGH",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 3,
      "deadline": "2026-07-03T18:00:00",
      "deadline_text": "Friday evening"
    },
    {
      "title": "Complete authentication testing",
      "description": "Test the authentication service after deployment and complete validation.",
      "priority": "MEDIUM",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 4,
      "deadline": "2026-07-06T23:59:59",
      "deadline_text": "by Monday"
    },
    {
      "title": "Obtain finalized leave management requirements",
      "description": "Coordinate with the product manager and obtain the finalized leave management requirements document.",
      "priority": "MEDIUM",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 7,
      "deadline": "2026-07-01T15:00:00",
      "deadline_text": "by tomorrow afternoon"
    },
    {
      "title": "Start analytics API development",
      "description": "Begin development of analytics APIs after authentication deployment.",
      "priority": "HIGH",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 3,
      "deadline": null,
      "deadline_text": null
    },
    {
      "title": "Prepare database scaling proposal",
      "description": "Create and share a database scaling proposal to address future storage growth.",
      "priority": "MEDIUM",
      "completed": false,
      "manager_id": 7,
      "assignee_id": 6,
      "deadline": "2026-07-08T00:00:00",
      "deadline_text": "before Wednesday"
    }
  ]
}
"""
# print(content)
# data = json.loads(content)
# =====================================================================================================================


router = APIRouter(
    prefix="/meetings",
    tags=["meetings"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

def create_tasks_from_summary(
    json_data: dict,
    manager_id: int,
    db
):
    for task in json_data.get("tasks", []):
        create_task_db(
            TaskRequest(
                title=task["title"],
                description=task["description"],
                priority=task["priority"],
                manager_id=manager_id,
                assignee_id=task["assignee_id"],
                deadline=task.get("deadline"),
                deadline_text=task.get("deadline_text")
            ),
            db
        )

@router.post("/create")
async def create_meeting(title: str,db: db_dependency,transcript:str):
    d = {u.name: u.id for u in db.query(Users).all()}
    audio_file = 'meeting_audio.mp3'
    # transcript = transcribe_audio(audio_path=audio_file)
    # content = generate_summary(transcript,datetime.now().isoformat(),d)
    data = json.loads(content)
    meeting = Meetings(
        title=title,
        summary=content,
        audio_file_path=None,
        transcript=transcript
    )
    db.add(meeting)
    for task in data["tasks"]:
        create_task_db(
            TaskRequest(
                title=task["title"],
                description=task["description"],
                priority=task["priority"],
                manager_id=task["manager_id"],
                assignee_id=task["assignee_id"],
                deadline=datetime.fromisoformat(task["deadline"]) if task["deadline"] else None,
                deadline_text=task["deadline_text"],
                completed=task["completed"]
            ),
            db
        )
    db.commit()
    db.refresh(meeting)

    # return meeting
    return {"message": "Meeting summary and tasks created successfully."}