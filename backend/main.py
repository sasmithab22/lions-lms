from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.test_data import TESTS
from backend.storage.tests.answers import TEST_SUBMISSIONS
import uvicorn
import shutil
import json
import os
import mimetypes

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

BASE_DIR = os.path.dirname(__file__)

STORAGE_DIR = os.path.join(
    BASE_DIR,
    "storage"
)

RESULTS_FILE = os.path.join(
    STORAGE_DIR,
    "tests",
    "results.json"
)

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
    "vijayalakshmi":   {"password": "vijayalakshmi2026",   "role": "student", "name": "Vijayalakshmi N",  "subject":"English"},
    "keerthiga":       {"password": "keerthiga2026",       "role": "student", "name": "Keerthiga A", "subject":"English"},
    "shobana":         {"password": "shobana2026",         "role": "student", "name": "Shobana R", "subject":"English"},
    "akilandeswari":   {"password": "akilandeswari2026",   "role": "student", "name": "Akilandeswari J", "subject":"Hindi"},
    "rajagnanapazham": {"password": "rajagnanapazham2026", "role": "student", "name": "Rajagnanapazham B", "subject":"EVS/SST"},
    "gnanasundari":    {"password": "gnanasundari2026",    "role": "student", "name": "Gnanasundari D", "subject":"EVS/SST"},
    "janaki":          {"password": "janaki2026",          "role": "student", "name": "Janaki V S", "subject":"EVS/SST"},
    "vidya":           {"password": "vidya2026",           "role": "student", "name": "Vidya C", "subject":"Maths"},
    "ganeshkumar":     {"password": "ganeshkumar2026",     "role": "student", "name": "Ganesh Kumar M", "subject":"Maths"},
    "balaganesh":      {"password": "balaganesh2026",      "role": "student", "name": "Balaganesh J", "subject":"Maths"},
    "srividhyarani":   {"password": "srividhyarani2026",   "role": "student", "name": "Sri Vidhya Rani R", "subject":"Maths"},
    "jeyaprakash":     {"password": "jeyaprakash2026",     "role": "student", "name": "Jeyaprakash T", "subject":"Science"},
    "raja":            {"password": "raja2026",            "role": "student", "name": "Raja P", "subject":"Science"},
    "harikaran":       {"password": "harikaran2026",       "role": "student", "name": "Harikaran M", "subject":"Science"},
    "jegatheesan":     {"password": "jegatheesan2026",     "role": "student", "name": "Jegatheesan C", "subject":"Science"},
    "anitha":          {"password": "anitha2026",          "role": "student", "name": "Anitha K", "subject":"Science"},
    "senthilkumar":    {"password": "senthilkumar2026",    "role": "student", "name": "Senthil Kumar C", "subject":"Computer Science"},
    "balamurugan":     {"password": "balamurugan2026",     "role": "student", "name": "Balamurugan P", "subject":"Accountancy"},
    "shanmugaraja":    {"password": "shanmugaraja2026",    "role": "student", "name": "Shanmugaraja S", "subject":"Economics"},
    "prabavathy":      {"password": "prabavathy2026",      "role": "student", "name": "Prabavathy S", "subject":"Business Studies"},
}

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
REQUIREMENTS_FILE = os.path.join(
    STORAGE_DIR,
    "tests",
    "results.json"
)

def load_requirements() -> dict:
    """Load test requirements. Returns {} if file missing."""
    if os.path.exists(REQUIREMENTS_FILE):
        with open(REQUIREMENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def student_allowed_for_test(test_id: str, student_name: str) -> bool:
    """
    Returns True if the student is allowed to take the test.
    - If test_id not in requirements → allowed (no restriction)
    - If requirements[test_id] is empty list → allowed (open to all)
    - Otherwise → student's name must be in the list
    """
    reqs = load_requirements()
    if test_id not in reqs:
        return True
    allowed_names = reqs[test_id]
    if len(allowed_names) == 0:
        return True
    return student_name in allowed_names

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

@app.post("/api/submit-test")
def submit_test(req: TestSubmit):
    try:
        if req.student not in TEST_SUBMISSIONS:
            TEST_SUBMISSIONS[req.student] = {}

        if req.test_id in TEST_SUBMISSIONS[req.student]:
            raise HTTPException(
                status_code=400,
                detail="Already completed"
            )

        test = TESTS.get(req.test_id)

        if not test:
            raise HTTPException(
                status_code=404,
                detail="Test not found"
            )

        score = 0
        review = []

        for q in test["questions"]:
            qid = str(q["id"])

            student_answer = req.answers.get(
                qid,
                "Not Answered"
            )

            if student_answer == q["answer"]:
                score += 1

            review.append({
                "question": q["question"],
                "student_answer": student_answer,
                "correct_answer": q["answer"],
                "explanation": q.get(
                    "explanation",
                    "No explanation available"
                ),
            })

        TEST_SUBMISSIONS[req.student][req.test_id] = {
            "date": str(datetime.now().date()),
            "score": score,
            "answers": req.answers,
        }

        # OPTIONAL SAVE TO TMP
        try:
            tmp_file = "/tmp/results.json"

            with open(tmp_file, "w") as f:
                json.dump(
                    TEST_SUBMISSIONS,
                    f,
                    indent=4
                )
        except Exception:
            pass

        return {
            "success": True,
            "score": score,
            "total_questions": len(
                test["questions"]
            ),
            "review": review,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

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

        # Use temporary Vercel storage
        folder = os.path.join(
            "/tmp",
            "students",
            student,
            "submissions",
            date
        )

        # Create folder
        os.makedirs(
            folder,
            exist_ok=True
        )

        filename = (
            f"{title}_{file.filename}"
        )

        filepath = os.path.join(
            folder,
            filename
        )

        with open(
            filepath,
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        return {
            "success": True,
            "filename": filename,
            "date": date
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/student-submissions/{student}")
def student_submissions(student: str):
    base = os.path.join(
        STORAGE_DIR,
        "students",
        student,
        "submissions"
    )
    result = []
    if not os.path.exists(base):
        return []
    for date in os.listdir(base):
        date_folder = os.path.join(
            base,
            date
        )
        if not os.path.isdir(date_folder):
            continue
        try:
            for file in os.listdir(date_folder):

                result.append({
                    "date": date,
                    "file": file
                })
        except:
            continue
    return result


@app.get("/api/all-submissions")
def all_submissions():

    result = []

    base = os.path.join(
        "/tmp",
        "students"
    )

    if not os.path.exists(base):
        return []

    for student in os.listdir(base):

        student_path = os.path.join(
            base,
            student,
            "submissions"
        )

        if not os.path.exists(
            student_path
        ):
            continue

        for date in os.listdir(
            student_path
        ):

            date_path = os.path.join(
                student_path,
                date
            )

            if not os.path.isdir(
                date_path
            ):
                continue

            for file in os.listdir(
                date_path
            ):

                result.append({
                    "student": student,
                    "date": date,
                    "file": file,
                    "download_url":
                    f"/api/download-submission/{student}/{date}/{file}",
                })

    return result

@app.get("/api/download-submission/{student}/{date}/{filename}")
def download_submission(
    student: str,
    date: str,
    filename: str
):
    path = os.path.join(
        "/tmp",
        "students",
        student,
        "submissions",
        date,
        filename
    )

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    # Detect MIME type from file extension
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"

    # Extract the original student-submitted filename
    # Files are stored as "{title}_{original_filename}"
    # We return the full stored filename as the download name
    return FileResponse(
        path=path,
        filename=filename,           # browser saves with this name
        media_type=mime_type,
    )

# ─────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────

@app.post("/api/save-attendance")
def save_attendance(data: dict):
    student = data["student"]
    date = data["date"]
    status = data["status"]

    file = os.path.join(
    STORAGE_DIR,
    "students",
    student,
    "attendance",
    "attendance.json"
)
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
    file = os.path.join(
    STORAGE_DIR,
    "students",
    student,
    "attendance",
    "attendance.json"
)

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

    file = os.path.join(
    STORAGE_DIR,
    "students",
    student,
    "marks",
    "marks.json"
)
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
    file = os.path.join(
    STORAGE_DIR,
    "students",
    student,
    "marks",
    "marks.json"
)

    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)

    return {}

# ─────────────────────────────────────────────
# SCHOOL ANALYTICS
# ─────────────────────────────────────────────

@app.get("/api/school-analytics")
def school_analytics():

    base = os.path.join(
        STORAGE_DIR,
        "students"
    )

    if not os.path.exists(base):
        return {
            "summary": {},
            "students": []
        }

    result = []

    total_tests = 2
    total_submissions = 36
    attendance_count = 0
    attendance_present = 0
    marks_total = 0
    marks_count = 0

    for student in STUDENT_USERS.keys():

        student_path = os.path.join(
            base,
            student
        )

        student_data = {
            "student": student,
            "subject":
            STUDENT_USERS[student].get(
                "subject",
                "-"
            ),
            "tests": 0,
            "submissions": 0,
            "attendance": "-",
            "marks": "-"
        }

        # TESTS
        try:
            completed = TEST_SUBMISSIONS.get(
                student,
                {}
            )

            tests = len(completed)

            student_data["tests"] = tests

            total_tests += tests

        except:
            pass

        # SUBMISSIONS
        try:

            sub_path = os.path.join(
                student_path,
                "submissions"
            )

            count = 0

            if os.path.exists(sub_path):

                for d in os.listdir(sub_path):

                    date_folder = os.path.join(
                        sub_path,
                        d
                    )

                    if os.path.isdir(date_folder):

                        count += len([
                            f for f in os.listdir(date_folder)
                            if not f.startswith(".")
                        ])

            student_data[
                "submissions"
            ] = count

            total_submissions += count

        except:
            pass

        # ATTENDANCE
        try:

            att_file = os.path.join(
                student_path,
                "attendance",
                "attendance.json"
            )

            if os.path.exists(att_file):

                with open(att_file) as f:

                    attendance = json.load(f)

                if attendance:

                    latest = list(
                        attendance.values()
                    )[-1]

                    student_data[
                        "attendance"
                    ] = latest

                    attendance_count += 1

                    if latest == "Present":

                        attendance_present += 1

        except:
            pass

        # MARKS
        try:

            marks_file = os.path.join(
                student_path,
                "marks",
                "marks.json"
            )

            if os.path.exists(marks_file):

                with open(marks_file) as f:

                    marks = json.load(f)

                values = []

                for d in marks.values():

                    if isinstance(d, dict):

                        for v in d.values():

                            try:
                                values.append(
                                    float(v)
                                )
                            except:
                                pass

                if values:

                    avg = round(
                        sum(values)
                        / len(values),
                        1
                    )

                    student_data[
                        "marks"
                    ] = avg

                    marks_total += sum(values)

                    marks_count += len(values)

        except:
            pass

        result.append(student_data)

    overall_attendance = 0

    if attendance_count > 0:

        overall_attendance = round(
            attendance_present
            / attendance_count * 100,
            1
        )

    avg_marks = 0

    if marks_count > 0:

        avg_marks = round(
            marks_total / marks_count,
            1
        )

    return {

        "summary": {
            "students":
            len(STUDENT_USERS),

            "tests":
            total_tests,

            "submissions":
            total_submissions,

            "attendance":
            overall_attendance,

            "marks":
            avg_marks
        },

        "students":
        result
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
        marks_file = os.path.join(
    STORAGE_DIR,
    "students",
    username,
    "marks",
    "marks.json"
)
        if os.path.exists(marks_file):
            with open(marks_file) as f:
                marks = json.load(f)
            values = []
            for d in marks.values():
                for v in d.values():
                    try:
                        values.append(float(v))
                    except:
                        pass
            if values:
                row["avg_marks"] = round(sum(values) / len(values),1)
        # Attendance
        att_file = os.path.join(
    STORAGE_DIR,
    "students",
    username,
    "attendance",
    "attendance.json"
)
        if os.path.exists(att_file):
            with open(att_file) as f:
                att = json.load(f)
            days = list(att.values())
            if len(days) > 0:
                present = len([
                    d for d in days
                    if d == "Present"
                ])
                row["attendance_pct"] = round(
                    present / len(days) * 100,
                    1
                )
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

        attendance_file = os.path.join(
    STORAGE_DIR,
    "students",
    username,
    "attendance",
    "attendance.json"
)

        if os.path.exists(attendance_file):

            with open(attendance_file,"r") as f:

                attendance=json.load(f)

            if date in attendance:

                student["attendance"]=attendance[date]


        # MARKS

        marks_file = os.path.join(
    STORAGE_DIR,
    "students",
    username,
    "marks",
    "marks.json"
)

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
        "category": "AI Lesson Planning",
        "learnt": [
            "Creating complete class lesson plans",
            "Generating topic-wise teaching flow",
            "Planning classroom activities and engagement",
            "Creating quizzes and classroom questions",
        ],
    },
    {
        "name": "Claude",
        "icon": "📑",
        "color": "orange",
        "category": "Presentation Creation",
        "learnt": [
            "Generating professional classroom PPTs",
            "Creating visually attractive subject slides",
            "Using prompts to build complete presentations",
            "Adding storytelling and student engagement in PPTs",
        ],
    },
    {
        "name": "Mentimeter",
        "icon": "📊",
        "color": "purple",
        "category": "Interactive Presentation",
        "learnt": [
            "Creating interactive classroom presentations",
            "Adding live polls and quizzes in lessons",
            "Using word clouds for student participation",
            "Making PPTs more engaging and student-friendly",
        ],
    },
    {
        "name": "NotebookLM",
        "icon": "🧠",
        "color": "blue",
        "category": "Study & Revision Tool",
        "learnt": [
            "Creating mind maps from study content",
            "Generating flashcards for revision",
            "Summarising learning material effectively",
            "Organising concepts for easier understanding",
        ],
    },
    {
        "name": "Wayground",
        "icon": "🗺️",
        "color": "green",
        "category": "Virtual Tour & Exploration",
        "learnt": [
            "Creating virtual tours for classroom use",
            "Exploring real-world locations interactively",
            "Using virtual environments for experiential learning",
            "Engaging students with immersive visual content",
        ],
    },
    {
        "name": "Jotform AI",
        "icon": "📝",
        "color": "red",
        "category": "AI Form & Data Collection",
        "learnt": [
            "Creating smart forms and surveys with AI",
            "Collecting and analysing student feedback",
            "Building automated response forms for classroom use",
            "Using AI-powered forms for assessments and data gathering",
        ],
    },
]

@app.get("/api/tools")
def get_tools():
    return TOOLS_LIST


@app.post("/api/upload-material")
async def upload_material(file: UploadFile = File(...)):
    folder = os.path.join(
    STORAGE_DIR,
    "materials"
)
    
    filepath = os.path.join(folder, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"success": True, "filename": file.filename}

@app.get("/api/materials")
def get_materials():
    folder = os.path.join(
    STORAGE_DIR,
    "materials"
)
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
    base = os.path.join(
    STORAGE_DIR,
    "reports"
)
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

    folder = os.path.join(
    STORAGE_DIR,
    "reports",
    date
)

    

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

    folder = os.path.join(
    STORAGE_DIR,
    "gallery",
    date
)

    

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
    result = []
    base = os.path.join(
        STORAGE_DIR,
        "gallery"
    )

    if not os.path.exists(base):
        return []
    for date in os.listdir(base):
        date_folder = os.path.join(
            base,
            date
        )
        if not os.path.isdir(date_folder):
            continue
        try:

            for file in os.listdir(date_folder):

                result.append({

                    "date": date,
                    "file": file,

                    "url":
                    f"/storage/gallery/{date}/{file}"
                })
        except:
            continue

    return result
# ─────────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────────

app.mount(
    "/storage",
    StaticFiles(directory=STORAGE_DIR),
    name="storage",
)


# ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )