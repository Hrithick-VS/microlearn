from flask import Flask, render_template, request, session, redirect
import psycopg2
import psycopg2.extras
import uuid
import os
from datetime import datetime

app = Flask(__name__)

# Used for student sessions
app.secret_key = os.environ.get("SECRET_KEY", "microprocessor_secret_key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set your Neon PostgreSQL connection string before running the app."
    )


# -----------------------------
# Database connection
# -----------------------------
def get_db_connection():
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn


# -----------------------------
# Create database
# -----------------------------

def init_db():

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            register_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            section TEXT DEFAULT 'A',
            video_progress REAL DEFAULT 0,
            video_completed INTEGER DEFAULT 0,
            quiz_completed INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            certificate_generated INTEGER DEFAULT 0,
            certificate_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# -----------------------------
# Home page
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Start learning
# -----------------------------

@app.route("/start", methods=["POST"])
def start():
    name = request.form["name"]
    register_no = request.form["register_no"]
    section = request.form["section"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM students WHERE register_no = %s",
        (register_no,)
    )
    student = cur.fetchone()

    if student is None:
        cur.execute("""
            INSERT INTO students (register_no, name, section)
            VALUES (%s, %s, %s)
        """, (register_no, name, section))
        conn.commit()
    else:
        cur.execute("""
            UPDATE students
            SET name = %s, section = %s
            WHERE register_no = %s
        """, (name, section, register_no))
        conn.commit()

    cur.close()
    conn.close()

    session["name"] = name
    session["register_no"] = register_no
    session["section"] = section

    return redirect("/video")


# -----------------------------
# Video page
# -----------------------------

@app.route("/video")
def video():
    if "register_no" not in session:
        return redirect("/")

    return render_template(
        "video.html",
        name=session.get("name"),
        register_no=session.get("register_no"),
        section=session.get("section")
    )

# -----------------------------
# Quiz page
# -----------------------------

@app.route("/quiz")
def quiz():
    if "register_no" not in session:
        return redirect("/")

    register_no = session["register_no"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT video_completed
        FROM students
        WHERE register_no = %s
    """, (register_no,))

    student = cur.fetchone()

    cur.close()
    conn.close()

    if not student or student["video_completed"] != 1:
        return redirect("/video")

    return render_template(
        "quiz.html",
        name=session.get("name"),
        register_no=session.get("register_no"),
        section=session.get("section")
    )
# -----------------------------
# Submit quiz
# -----------------------------

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    if "register_no" not in session:
        return redirect("/")

    questions = [
    {"key": "q1", "question": "Which sequence best represents the general data flow described for a computer system?", "options": {
        "a": "CPU → Input → Memory → Output",
        "b": "Input → Memory → CPU → Memory → Output",
        "c": "Input → CPU → Storage → Memory → Output",
        "d": "Memory → Input → CPU → Output → Memory"
    }, "answer": "b"},

    {"key": "q2", "question": "Which statement correctly distinguishes primary and secondary memory?", "options": {
        "a": "Primary memory is always non-volatile, while secondary memory is volatile",
        "b": "Primary memory has larger capacity and is always slower than secondary storage",
        "c": "RAM is temporary primary memory, whereas HDD/SSD are non-volatile secondary storage",
        "d": "ROM is volatile and is normally used as secondary storage"
    }, "answer": "c"},

    {"key": "q3", "question": "According to the memory hierarchy presented, which ordering is correct from fastest to slower?", "options": {
        "a": "RAM → Cache → Registers → Secondary Storage",
        "b": "Registers → Cache → RAM → Secondary Storage",
        "c": "Cache → Registers → RAM → Secondary Storage",
        "d": "Registers → RAM → Cache → Secondary Storage"
    }, "answer": "b"},

    {"key": "q4", "question": "During the fetch stage of the instruction cycle, which pair of actions occurs?", "options": {
        "a": "ALU performs arithmetic and FLAGS are cleared",
        "b": "CU retrieves the instruction using PC and loads it into IR",
        "c": "EU decodes the instruction and BIU executes it",
        "d": "Result is stored and PC is reset to zero"
    }, "answer": "b"},

    {"key": "q5", "question": "What is the primary purpose of incrementing the Program Counter after fetching an instruction?", "options": {
        "a": "To store the result of the ALU operation",
        "b": "To identify the current stack segment",
        "c": "To point toward the next instruction to be fetched",
        "d": "To update the carry and zero flags"
    }, "answer": "c"},

    {"key": "q6", "question": "Which of the following is NOT listed as a condition flag updated after execution?", "options": {
        "a": "Carry Flag",
        "b": "Zero Flag",
        "c": "Sign Flag",
        "d": "Segment Flag"
    }, "answer": "d"},

    {"key": "q7", "question": "Which bus is primarily responsible for carrying the actual data being transferred among CPU, memory and I/O?", "options": {
        "a": "Data bus",
        "b": "Address bus",
        "c": "Control bus",
        "d": "Segment bus"
    }, "answer": "a"},

    {"key": "q8", "question": "Why are control-bus signals necessary in a computer system?", "options": {
        "a": "They permanently store instructions",
        "b": "They specify the numerical value of every operand",
        "c": "They coordinate timing and control operations",
        "d": "They increase RAM capacity"
    }, "answer": "c"},

    {"key": "q9", "question": "Which statement about the 8086 functional organization is most accurate?", "options": {
        "a": "BIU performs all arithmetic while EU handles memory addressing",
        "b": "BIU handles bus operations and EU executes instructions",
        "c": "EU fetches instructions directly from I/O devices",
        "d": "BIU contains the ALU and FLAGS register"
    }, "answer": "b"},

    {"key": "q10", "question": "Which component is specifically associated with the BIU in the video?", "options": {
        "a": "ALU",
        "b": "Flag Register",
        "c": "Instruction Decoder",
        "d": "6-byte Instruction Queue"
    }, "answer": "d"},

    {"key": "q11", "question": "What is the main performance advantage of the 8086 instruction queue?", "options": {
        "a": "It eliminates the need for registers",
        "b": "It allows instruction fetching and execution to overlap",
        "c": "It makes all instructions execute in one clock cycle",
        "d": "It permanently stores the entire program"
    }, "answer": "b"},

    {"key": "q12", "question": "While the EU is executing the current instruction, what can the BIU do?", "options": {
        "a": "Reset all segment registers",
        "b": "Prefetch subsequent instructions",
        "c": "Modify the ALU result",
        "d": "Clear the FLAGS register"
    }, "answer": "b"},

    {"key": "q13", "question": "What happens to the 8086 prefetch queue when a jump/branch changes the instruction sequence?", "options": {
        "a": "It is doubled in size",
        "b": "It is converted into a stack",
        "c": "It is flushed and fetching restarts from the new address",
        "d": "It remains unchanged"
    }, "answer": "c"},

    {"key": "q14", "question": "Which register pair is explicitly associated with the next instruction's offset within the code segment?", "options": {
        "a": "DS:BX",
        "b": "SS:SP",
        "c": "CS:IP",
        "d": "ES:DI"
    }, "answer": "c"},

    {"key": "q15", "question": "Which set contains only 8086 general-purpose registers?", "options": {
        "a": "AX, BX, CX, DX",
        "b": "CS, DS, SS, ES",
        "c": "SP, BP, SI, DI",
        "d": "IP, FLAGS, CS, AX"
    }, "answer": "a"},

    {"key": "q16", "question": "What is a key feature of AX, BX, CX and DX in the 8086?", "options": {
        "a": "Each is 32-bit and cannot be divided",
        "b": "Each is 16-bit and can be split into high and low 8-bit halves",
        "c": "Each is a segment register",
        "d": "Each stores only memory addresses"
    }, "answer": "b"},

    {"key": "q17", "question": "Which register is correctly matched with its primary role?", "options": {
        "a": "SP — Stack Pointer",
        "b": "CS — Data Segment",
        "c": "IP — Stack Pointer",
        "d": "FLAGS — Source Index"
    }, "answer": "a"},

    {"key": "q18", "question": "Which statement about the 8086 FLAGS register is correct?", "options": {
        "a": "It stores the base address of the code segment",
        "b": "It is a 16-bit status/control register reflecting CPU state and ALU results",
        "c": "It contains the next instruction's machine code",
        "d": "It is used only for I/O addresses"
    }, "answer": "b"},

    {"key": "q19", "question": "In immediate addressing, where is the operand value located?", "options": {
        "a": "In a memory location specified by BX",
        "b": "In a segment register",
        "c": "Within the instruction itself",
        "d": "Only in the FLAGS register"
    }, "answer": "c"},

    {"key": "q20", "question": "Which instruction best illustrates register addressing?", "options": {
        "a": "MOV AX, 1234H",
        "b": "MOV AX, [2000H]",
        "c": "MOV AX, BX",
        "d": "MOV AX, [BX+05H]"
    }, "answer": "c"},

    {"key": "q21", "question": "What distinguishes direct addressing from register-indirect addressing?", "options": {
        "a": "Direct uses an effective address in the instruction; register-indirect obtains the address from a register",
        "b": "Direct always uses BX; register-indirect always uses IP",
        "c": "Direct contains an immediate value; register-indirect contains a segment value",
        "d": "There is no difference"
    }, "answer": "a"},

    {"key": "q22", "question": "Which instruction most clearly represents based addressing with a displacement?", "options": {
        "a": "MOV AX, BX",
        "b": "MOV AX, 1234H",
        "c": "MOV AX, [BX+05H]",
        "d": "MOV AX, [2000H]"
    }, "answer": "c"},

    {"key": "q23", "question": "Which addressing mode combines a base register, an index register and a displacement?", "options": {
        "a": "Immediate",
        "b": "Direct",
        "c": "Register",
        "d": "Based-indexed"
    }, "answer": "d"},

    {"key": "q24", "question": "Which statement correctly compares pipelined and non-overlapped operation?", "options": {
        "a": "Pipelining inserts idle time between every fetch and execute",
        "b": "Non-overlapped operation allows BIU and EU to work simultaneously",
        "c": "Pipelining overlaps instruction fetch with execution, reducing wasted waiting time",
        "d": "Both methods have identical instruction-fetch behavior"
    }, "answer": "c"},

    {"key": "q25", "question": "Which option correctly matches the 8086 component to its function?", "options": {
        "a": "EU — fetches every instruction directly from main memory",
        "b": "BIU — performs arithmetic and logical operations",
        "c": "Instruction Decoder — converts fetched instructions into operations/micro-operations for execution",
        "d": "FLAGS — stores the physical address of the next instruction"
    }, "answer": "c"}
]
    score = 0
    review = []

    for q in questions:
        selected = request.form.get(q["key"])

        is_correct = selected == q["answer"]

        if is_correct:
            score += 1

        review.append({
            "question": q["question"],
            "selected": q["options"].get(selected, "Not answered"),
            "correct": q["options"][q["answer"]],
            "is_correct": is_correct
        })

    total_questions = len(questions)
    register_no = session["register_no"]

    certificate_id = "ML-" + uuid.uuid4().hex[:8].upper()
    completion_date = datetime.now().strftime("%d %B %Y")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE students
    SET quiz_completed = 1,
        score = %s,
        total_questions = %s,
        certificate_generated = 1,
        certificate_id = %s
    WHERE register_no = %s
""", (
    score,
    total_questions,
    certificate_id,
    register_no
))
    conn.commit()
    cur.close()
    conn.close()


    session["certificate_id"] = certificate_id
    session["completion_date"] = completion_date

    return render_template(
        "quiz_result.html",
        name=session.get("name"),
        register_no=register_no,
        section=session.get("section"),
        score=score,
        total_questions=total_questions,
        review=review
    )

@app.route("/certificate")
def certificate():
    if "register_no" not in session:
        return redirect("/")

    register_no = session["register_no"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM students
        WHERE register_no = %s
    """, (register_no,))

    student = cur.fetchone()

    cur.close()
    conn.close()

    if not student:
        return redirect("/")

    return render_template(
        "certificate.html",
        name=student["name"],
        register_no=student["register_no"],
        section=student["section"],
        date=session.get(
            "completion_date",
            datetime.now().strftime("%d %B %Y")
        ),
        certificate_id=student["certificate_id"]
    )
# -----------------------------
# Update video progress
# -----------------------------

@app.route("/update_progress", methods=["POST"])
def update_progress():
    if "register_no" not in session:
        return {"error": "Student not logged in"}, 401

    register_no = session["register_no"]
    data = request.get_json()

    try:
        progress = float(data.get("progress", 0))
    except (TypeError, ValueError):
        progress = 0
    progress = max(0, min(progress, 100))

    video_completed = 1 if progress >= 50 else 0

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE students
        SET video_progress = %s,
            video_completed = %s
        WHERE register_no = %s
    """, (
        progress,
        video_completed,
        register_no
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "success": True,
        "progress": progress,
        "video_completed": video_completed
    }
# -----------------------------
# Faculty login
# -----------------------------



@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Development login
        if username == "faculty" and password == "micro123":

            session["faculty_logged_in"] = True

            return redirect("/dashboard")

        else:

            return render_template(
                "admin_login.html",
                error="Invalid username or password"
            )

    return render_template("admin_login.html")
# -----------------------------
# Faculty dashboard
# -----------------------------

@app.route("/dashboard")
def dashboard():
    if not session.get("faculty_logged_in"):
        return redirect("/admin")

    selected_section = request.args.get("section", "ALL")
    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if selected_section != "ALL":
        query += " AND section = %s"
        params.append(selected_section)

    if search:
        query += " AND (name ILIKE %s OR register_no ILIKE %s)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    query += " ORDER BY section ASC, register_no ASC"

    cur.execute(query, params)
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        students=students,
        selected_section=selected_section,
        search=search
    )

@app.route("/faculty_logout")
def faculty_logout():
    session.pop("faculty_logged_in", None)
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/clear_records", methods=["POST"])
def clear_records():
    if not session.get("faculty_logged_in"):
        return redirect("/admin")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM students")

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")

if __name__ == "__main__":

    init_db()

    app.run(debug=True)

