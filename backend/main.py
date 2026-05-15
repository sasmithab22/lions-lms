from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from test_data import TESTS
from storage.tests.answers import TEST_SUBMISSIONS
import uvicorn
import shutil
import json
import os

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_FILE = "storage/tests/results.json"

# ─────────────────────────────────────────────
# USER STORES
# ─────────────────────────────────────────────

ADMIN_USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "Administrator",
    }
}

SCHOOL_USERS = {
    "sivakasi_lions": {
        "password": "lions123",
        "role": "school",
        "name": "Sivakasi Lions",
    }
}

STAFF_USERS = {
    "sas": {
        "password": "sas2026",
        "role": "staff",
        "name": "Sasmitha B",
    }
}

STUDENT_USERS = {
    "vijayalakshmi":   {"password": "vijayalakshmi2026",   "role": "student", "name": "Vijayalakshmi N",  "subject":"Science Biology"},
    "keerthiga":       {"password": "keerthiga2026",       "role": "student", "name": "Keerthiga A", "subject":"Science Biology"},
    "shobana":         {"password": "shobana2026",         "role": "student", "name": "Shobana R", "subject":"Science Biology"},
    "akilandeswari":   {"password": "akilandeswari2026",   "role": "student", "name": "Akilandeswari J", "subject":"Science Biology"},
    "rajagnanapazham": {"password": "rajagnanapazham2026", "role": "student", "name": "Rajagnanapazham B", "subject":"Science Biology"},
    "gnanasundari":    {"password": "gnanasundari2026",    "role": "student", "name": "Gnanasundari D", "subject":"Science Biology"},
    "janaki":          {"password": "janaki2026",          "role": "student", "name": "Janaki V S", "subject":"Science Biology"},
    "vidya":           {"password": "vidya2026",           "role": "student", "name": "Vidya C", "subject":"Science Biology"},
    "ganeshkumar":     {"password": "ganeshkumar2026",     "role": "student", "name": "Ganesh Kumar M", "subject":"Science Biology"},
    "balaganesh":      {"password": "balaganesh2026",      "role": "student", "name": "Balaganesh J", "subject":"Science Biology"},
    "srividhyarani":   {"password": "srividhyarani2026",   "role": "student", "name": "Sri Vidhya Rani R", "subject":"Science Biology"},
    "jeyaprakash":     {"password": "jeyaprakash2026",     "role": "student", "name": "Jeyaprakash T", "subject":"Science Biology"},
    "raja":            {"password": "raja2026",            "role": "student", "name": "Raja P", "subject":"Science Biology"},
    "harikaran":       {"password": "harikaran2026",       "role": "student", "name": "Harikaran M", "subject":"Science Biology"},
    "jegatheesan":     {"password": "jegatheesan2026",     "role": "student", "name": "Jegatheesan C", "subject":"Science Biology"},
    "anitha":          {"password": "anitha2026",          "role": "student", "name": "Anitha K", "subject":"Science Biology"},
    "senthilkumar":    {"password": "senthilkumar2026",    "role": "student", "name": "Senthil Kumar C", "subject":"Science Biology"},
    "balamurugan":     {"password": "balamurugan2026",     "role": "student", "name": "Balamurugan P", "subject":"Science Biology"},
    "shanmugaraja":    {"password": "shanmugaraja2026",    "role": "student", "name": "Shanmugaraja S", "subject":"Science Biology"},
    "prabavathy":      {"password": "prabavathy2026",      "role": "student", "name": "Prabavathy S", "subject":"Science Biology"},
}

# ─────────────────────────────────────────────
# STUDENT STORAGE STRUCTURE
# ─────────────────────────────────────────────

def create_student_structure(student: str):
    base = f"storage/students/{student}"
    for folder in ["tests", "submissions", "attendance", "marks", "activity"]:
        os.makedirs(f"{base}/{folder}", exist_ok=True)


# Create folders for all existing students on startup
for student in STUDENT_USERS:
    create_student_structure(student)

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str


class CreateUserRequest(BaseModel):
    user_type: str
    username: str
    password: str
    name: str
    extra: Optional[dict] = {}


class TestSubmit(BaseModel):
    student: str
    test_id: str
    answers: dict

# ─────────────────────────────────────────────
# AUTH — LOGIN
# ─────────────────────────────────────────────

@app.post("/api/login")
def login(req: LoginRequest):
    username = req.username.strip().lower()
    role = req.role.strip().lower()

    store_map = {
        "admin":   ADMIN_USERS,
        "school":  SCHOOL_USERS,
        "staff":   STAFF_USERS,
        "student": STUDENT_USERS,
    }

    store = store_map.get(role)
    if store is None:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = store.get(username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "success": True,
        "role": role,
        "name": user["name"],
        "data": user,
    }

# ─────────────────────────────────────────────
# ADMIN — CREATE USER
# ─────────────────────────────────────────────

@app.post("/api/create-user")
def create_user(req: CreateUserRequest):
    username = req.username.strip().lower()
    utype = req.user_type.lower()

    store_map = {
        "school":  SCHOOL_USERS,
        "staff":   STAFF_USERS,
        "student": STUDENT_USERS,
    }

    store = store_map.get(utype)
    if store is None:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    if username in store:
        raise HTTPException(status_code=400, detail=f"{utype.capitalize()} username already exists")

    store[username] = {
        "password": req.password,
        "role": utype,
        "name": req.name,
        **(req.extra or {}),
    }

    if utype == "student":
        create_student_structure(username)

    return {"success": True, "username": username, "password": req.password}

# ─────────────────────────────────────────────
# ADMIN — LIST USERS
# ─────────────────────────────────────────────

@app.get("/api/users/{user_type}")
def list_users(user_type: str):
    store_map = {
        "school":  SCHOOL_USERS,
        "staff":   STAFF_USERS,
        "student": STUDENT_USERS,
    }

    store = store_map.get(user_type)
    if store is None:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    return [
        {
            "username": uname,
            "name": data["name"],
            "password": data["password"],
            **{k: v for k, v in data.items() if k not in ("password", "role", "name")},
        }
        for uname, data in store.items()
    ]

# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

@app.get("/api/tests/{student}")
def get_tests(student: str):
    completed = TEST_SUBMISSIONS.get(student, {})
    return [
        {
            "id": tid,
            "title": data["title"],
            "completed": tid in completed,
        }
        for tid, data in TESTS.items()
    ]


@app.get("/api/test/{test_id}")
def get_test(test_id: str):
    test = TESTS.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in test["questions"]
    ]


@app.post("/api/submit-test")
def submit_test(req: TestSubmit):
    if req.student not in TEST_SUBMISSIONS:
        TEST_SUBMISSIONS[req.student] = {}

    if req.test_id in TEST_SUBMISSIONS[req.student]:
        raise HTTPException(status_code=400, detail="Already completed")

    test = TESTS[req.test_id]
    score = 0
    review = []

    for q in test["questions"]:
        qid = str(q["id"])
        student_answer = req.answers.get(qid, "Not Answered")

        if student_answer == q["answer"]:
            score += 1

        review.append({
            "question": q["question"],
            "student_answer": student_answer,
            "correct_answer": q["answer"],
            "explanation": q.get("explanation", "No explanation available"),
        })

    TEST_SUBMISSIONS[req.student][req.test_id] = {
        "date": str(datetime.now().date()),
        "score": score,
        "answers": req.answers,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(TEST_SUBMISSIONS, f, indent=4)

    return {
        "success": True,
        "score": score,
        "total_questions": len(test["questions"]),
        "review": review,
    }


@app.get("/api/all-test-results")
def get_all_results():
    return [
        {
            "student": student,
            "test": test_id,
            "score": test_data["score"],
            "date": test_data["date"],
        }
        for student, data in TEST_SUBMISSIONS.items()
        for test_id, test_data in data.items()
    ]

# ─────────────────────────────────────────────
# SUBMISSIONS
# ─────────────────────────────────────────────

@app.post("/api/upload-submission")
async def upload_submission(
    student: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        date = str(datetime.now().date())
        folder = f"storage/students/{student}/submissions/{date}"
        os.makedirs(folder, exist_ok=True)

        filename = f"{title}_{file.filename}"
        filepath = os.path.join(folder, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"success": True, "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/student-submissions/{student}")
def student_submissions(student: str):
    base = f"storage/students/{student}/submissions"
    result = []

    if os.path.exists(base):
        for date in os.listdir(base):
            date_folder = os.path.join(base, date)
            for file in os.listdir(date_folder):
                result.append({"date": date, "file": file})

    return result


@app.get("/api/all-submissions")
def all_submissions():
    result = []
    base = "storage/students"

    if not os.path.exists(base):
        return []

    for student in os.listdir(base):
        student_path = f"{base}/{student}/submissions"
        if not os.path.exists(student_path):
            continue

        for date in os.listdir(student_path):
            date_path = os.path.join(student_path, date)
            for file in os.listdir(date_path):
                result.append({
                    "student": student,
                    "date": date,
                    "file": file,
                    "download_url": f"/api/download-submission/{student}/{date}/{file}",
                })

    return result


@app.get("/api/download-submission/{student}/{date}/{filename}")
def download_submission(student: str, date: str, filename: str):
    path = f"storage/students/{student}/submissions/{date}/{filename}"
    return FileResponse(path=path, filename=filename)

# ─────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────

@app.post("/api/save-attendance")
def save_attendance(data: dict):
    student = data["student"]
    date = data["date"]
    status = data["status"]

    file = f"storage/students/{student}/attendance/attendance.json"
    attendance = {}

    if os.path.exists(file):
        with open(file, "r") as f:
            attendance = json.load(f)

    attendance[date] = status

    with open(file, "w") as f:
        json.dump(attendance, f, indent=4)

    return {"success": True}


@app.get("/api/student-attendance/{student}")
def get_attendance(student: str):
    file = f"storage/students/{student}/attendance/attendance.json"

    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)

    return {}

# ─────────────────────────────────────────────
# MARKS
# ─────────────────────────────────────────────

@app.post("/api/save-marks")
def save_marks(data: dict):
    student = data["student"]
    date = data["date"]
    subject = data["subject"]
    mark = data["mark"]

    file = f"storage/students/{student}/marks/marks.json"
    marks = {}

    if os.path.exists(file):
        with open(file, "r") as f:
            marks = json.load(f)

    if date not in marks:
        marks[date] = {}

    marks[date][subject] = mark

    with open(file, "w") as f:
        json.dump(marks, f, indent=4)

    return {"success": True}


@app.get("/api/student-marks/{student}")
def get_marks(student: str):
    file = f"storage/students/{student}/marks/marks.json"

    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)

    return {}

# ─────────────────────────────────────────────
# SCHOOL ANALYTICS
# ─────────────────────────────────────────────

@app.get("/api/school-analytics")
def school_analytics():
    base = "storage/students"

    if not os.path.exists(base):
        return {}

    students = os.listdir(base)
    result = []

    total_tests = 0
    total_submissions = 0
    attendance_count = 0
    attendance_present = 0
    marks_total = 0
    marks_count = 0

    for student in students:
        student_path = os.path.join(base, student)
        student_data = {
            "student": student,
            "tests": 0,
            "submissions": 0,
            "attendance": "-",
            "marks": "-",
        }

        # Tests
        test_path = os.path.join(student_path, "tests")
        if os.path.exists(test_path):
            tests = len(os.listdir(test_path))
            student_data["tests"] = tests
            total_tests += tests

        # Submissions
        sub_path = os.path.join(student_path, "submissions")
        if os.path.exists(sub_path):
            count = sum(
                len(os.listdir(os.path.join(sub_path, d)))
                for d in os.listdir(sub_path)
            )
            student_data["submissions"] = count
            total_submissions += count

        # Attendance
        att_file = os.path.join(student_path, "attendance", "attendance.json")
        if os.path.exists(att_file):
            with open(att_file) as f:
                attendance = json.load(f)
            latest = list(attendance.values())[-1]
            student_data["attendance"] = latest
            attendance_count += 1
            if latest == "Present":
                attendance_present += 1

        # Marks
        marks_file = os.path.join(student_path, "marks", "marks.json")
        if os.path.exists(marks_file):
            with open(marks_file) as f:
                marks = json.load(f)
            values = [v for d in marks.values() for v in d.values()]
            if values:
                student_data["marks"] = round(sum(values) / len(values), 1)
                marks_total += sum(values)
                marks_count += len(values)

        result.append(student_data)

    overall_attendance = (
        round((attendance_present / attendance_count) * 100, 1)
        if attendance_count else 0
    )

    avg_marks = (
        round(marks_total / marks_count, 1)
        if marks_count else 0
    )

    return {
        "summary": {
            "students": len(students),
            "tests": total_tests,
            "submissions": total_submissions,
            "attendance": overall_attendance,
            "marks": avg_marks,
        },
        "students": result,
    }

@app.get("/api/student-report")
def student_report():
    result = []
    for username, udata in STUDENT_USERS.items():
        row = {
            "username": username,
            "name": udata["name"],
            "subject": udata.get("subject", "—"),
            "avg_marks": None,
            "attendance_pct": None,
            "tests_completed": 0,
        }
        # Marks
        marks_file = f"storage/students/{username}/marks/marks.json"
        if os.path.exists(marks_file):
            with open(marks_file) as f:
                marks = json.load(f)
            values = [v for d in marks.values() for v in d.values()]
            if values:
                row["avg_marks"] = round(sum(values) / len(values), 1)
        # Attendance
        att_file = f"storage/students/{username}/attendance/attendance.json"
        if os.path.exists(att_file):
            with open(att_file) as f:
                att = json.load(f)
            days = list(att.values())
            if days:
                row["attendance_pct"] = round(len([d for d in days if d == "Present"]) / len(days) * 100, 1)
        # Tests
        completed = TEST_SUBMISSIONS.get(username, {})
        row["tests_completed"] = len(completed)
        result.append(row)
    return result

@app.get("/api/date-report/{date}")
def date_report(date:str):

    result=[]

    for username,data in STUDENT_USERS.items():

        student={

            "student":data["name"],
            "subject":data.get("subject","-"),
            "attendance":"-",
            "marks":"-"

        }

        # ATTENDANCE

        attendance_file=f"""
storage/students/{username}/attendance/attendance.json
""".replace("\n","")

        if os.path.exists(attendance_file):

            with open(attendance_file,"r") as f:

                attendance=json.load(f)

            if date in attendance:

                student["attendance"]=attendance[date]


        # MARKS

        marks_file=f"""
storage/students/{username}/marks/marks.json
""".replace("\n","")

        if os.path.exists(marks_file):

            with open(marks_file,"r") as f:

                marks=json.load(f)

            if date in marks:

                student["marks"]=marks[date]


        result.append(student)

    return result
TOOLS_LIST = [
    {
        "name": "ChatGPT",
        "icon": "🤖",
        "color": "teal",
        "category": "AI Assistant",
        "learnt": [
            "How to ask clear, effective prompts",
            "Using it to explain difficult Biology concepts",
            "Summarising long study material quickly",
            "Generating quiz questions for self-revision",
        ],
    },
    {
        "name": "Mentimeter",
        "icon": "📊",
        "color": "purple",
        "category": "Interactive Polling",
        "learnt": [
            "Creating live polls and word clouds in class",
            "Participating in real-time quizzes during lessons",
            "Voting on questions anonymously",
            "Viewing class-wide responses on a shared screen",
        ],
    },
    {
        "name": "Google Forms",
        "icon": "📋",
        "color": "blue",
        "category": "Survey & Quiz",
        "learnt": [
            "Filling online tests and assessments",
            "Submitting feedback through forms",
            "Understanding auto-graded quiz responses",
            "Creating simple surveys",
        ],
    },
    {
        "name": "Canva",
        "icon": "🎨",
        "color": "rose",
        "category": "Design Tool",
        "learnt": [
            "Designing Biology project posters",
            "Using templates to create presentations",
            "Adding infographics and diagrams to reports",
            "Exporting designs as PDF or image",
        ],
    },
    {
        "name": "YouTube",
        "icon": "▶️",
        "color": "rose",
        "category": "Video Learning",
        "learnt": [
            "Watching Biology concept explanation videos",
            "Using timestamps to navigate specific topics",
            "Finding lab experiment demonstrations",
            "Enabling subtitles for better understanding",
        ],
    },
    {
        "name": "Google Slides",
        "icon": "🖥️",
        "color": "amber",
        "category": "Presentation",
        "learnt": [
            "Creating and sharing class presentations",
            "Collaborating on slides with classmates",
            "Embedding images and diagrams",
            "Presenting in front of the class digitally",
        ],
    },
    {
        "name": "WhatsApp",
        "icon": "💬",
        "color": "green",
        "category": "Communication",
        "learnt": [
            "Sharing study materials and notes in groups",
            "Receiving announcements from teachers",
            "Sending assignment files and photos",
            "Using it for peer-to-peer doubt clearing",
        ],
    },
    {
        "name": "EduPortal",
        "icon": "🏫",
        "color": "sky",
        "category": "School Platform",
        "learnt": [
            "Logging in and navigating the student dashboard",
            "Taking online tests and viewing scores",
            "Checking personal attendance records",
            "Downloading study materials uploaded by staff",
        ],
    },
    {
        "name": "QR Code Scanner",
        "icon": "📷",
        "color": "slate",
        "category": "Utility Tool",
        "learnt": [
            "Scanning QR codes to open websites and forms",
            "Using the phone camera as a scanner",
            "Accessing shared links quickly in class",
            "Understanding how QR codes store information",
        ],
    },
    {
        "name": "Google Search",
        "icon": "🔍",
        "color": "blue",
        "category": "Research Tool",
        "learnt": [
            "Using keywords to find Biology topics",
            "Identifying reliable vs unreliable sources",
            "Using Google Images for diagrams",
            "Applying search filters like 'site:' and 'filetype:'",
        ],
    },
]


@app.get("/api/tools")
def get_tools():
    return TOOLS_LIST



async def upload_material(file: UploadFile = File(...)):
    folder = "storage/materials"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"success": True, "filename": file.filename}

@app.get("/api/materials")
def get_materials():
    folder = "storage/materials"
    if not os.path.exists(folder):
        return []
    result = []
    for file in os.listdir(folder):
        filepath = os.path.join(folder, file)
        size = os.path.getsize(filepath)
        mtime = os.path.getmtime(filepath)
        date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        result.append({"filename": file, "url": f"/storage/materials/{file}", "size": size, "date": date})
    return result

@app.get("/api/reports")
def get_reports():
    base = "storage/reports"
    if not os.path.exists(base):
        return []
    result = []
    for date in sorted(os.listdir(base), reverse=True):
        date_folder = os.path.join(base, date)
        if os.path.isdir(date_folder):
            for file in os.listdir(date_folder):
                size = os.path.getsize(os.path.join(date_folder, file))
                result.append({"date": date, "filename": file, "url": f"/storage/reports/{date}/{file}", "size": size})
    return result

@app.post("/api/upload-report")
async def upload_report(

    file:UploadFile=File(...)

):

    date=str(datetime.now().date())

    folder=f"storage/reports/{date}"

    os.makedirs(folder,exist_ok=True)

    filepath=os.path.join(
        folder,
        file.filename
    )

    with open(filepath,"wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return{
        "success":True
    }

@app.post("/api/upload-gallery")
async def upload_gallery(

    file:UploadFile=File(...)

):

    date=str(datetime.now().date())

    folder=f"storage/gallery/{date}"

    os.makedirs(folder,exist_ok=True)

    filepath=os.path.join(
        folder,
        file.filename
    )

    with open(filepath,"wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return{
        "success":True
    }

@app.get("/api/gallery")
def gallery():

    result=[]

    base="storage/gallery"

    if not os.path.exists(base):

        return []

    for date in os.listdir(base):

        date_folder=os.path.join(
            base,
            date
        )

        for file in os.listdir(date_folder):

            result.append({

                "date":date,

                "file":file,

                "url":

                f"/storage/gallery/{date}/{file}"

            })

    return result
# ─────────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────────

app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage",
)

app.mount(
    "/",
    StaticFiles(directory="../frontend", html=True),
    name="static",
)

# ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)