from docx import Document

from reportlab.platypus import *

from reportlab.lib.styles import getSampleStyleSheet
from flask import *
from flask import send_from_directory
import os
import re
import json
import random

from database.database import get_connection

from ai_modules.summarizer import summarize_text
from ai_modules.ocr import extract_text
from ai_modules.speech import audio_to_text
from ai_modules.chatbot import chatbot_response
from ai_modules.pdf_summarizer import summarize_pdf
from ai_modules.tutor import explain_difficult_topic

app = Flask(__name__)

app.secret_key = "studymate_secret_key"
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/resumes', exist_ok=True)

# HOME PAGE
@app.route('/')
def home():

    return render_template('index.html')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        college = request.form['college']
        password = request.form['password']

        connection = get_connection()

        cursor = connection.cursor()

        query = """
        INSERT INTO users
        (name, email, password, department, college)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            name,
            email,
            password,
            department,
            college
        )

        cursor.execute(query, values)
        new_user_id = cursor.lastrowid

        # Initialize fresh student stats in database (0 units until student enters a topic)
        cursor.execute("""
            INSERT INTO student_academic_stats 
            (user_id, level, xp, streak_days, today_studied_hours, today_target_hours, completed_units, total_units, smart_revision_topic, dominant_learning_style, retention_rate)
            VALUES (%s, 1, 0, 1, 0.0, 6.0, 0, 0, NULL, 'Undetermined', 0)
        """, (new_user_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect('/login')

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(query, (email, password))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:

            session['user_id'] = user['user_id']
            session['name'] = user['name']

            return redirect('/dashboard')

        else:

            return """
            <h3>
                Invalid Email or Password ❌
            </h3>
            """

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect('/login')

    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
    stats = cursor.fetchone()

    if not stats:
        cursor.execute("""
            INSERT INTO student_academic_stats 
            (user_id, level, xp, streak_days, today_studied_hours, today_target_hours, completed_units, total_units, smart_revision_topic, dominant_learning_style, retention_rate)
            VALUES (%s, 1, 0, 1, 0.0, 6.0, 0, 0, NULL, 'Undetermined', 0)
        """, (user_id,))
        connection.commit()
        cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
        stats = cursor.fetchone()

    cursor.close()
    connection.close()

    today_studied = float(stats['today_studied_hours']) if stats and stats.get('today_studied_hours') is not None else 0.0
    target_hours = float(stats['today_target_hours']) if stats and stats.get('today_target_hours') is not None and float(stats['today_target_hours']) > 0 else 6.0
    completed_units = int(stats['completed_units']) if stats and stats.get('completed_units') is not None else 0
    total_units = int(stats['total_units']) if stats and stats.get('total_units') is not None and int(stats['total_units']) > 0 else 0

    goal_percent = int(round((today_studied / target_hours) * 100)) if target_hours > 0 else 0
    syllabus_percent = round((float(completed_units) / float(total_units)) * 100, 1) if total_units > 0 else 0.0

    return render_template(
        'dashboard.html',
        name=session['name'],
        stats=stats,
        goal_percent=goal_percent,
        syllabus_percent=syllabus_percent
    )

# PROFILE

@app.route('/profile')
def profile():

    if 'user_id' not in session:

        return redirect('/login')

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT * FROM users
    WHERE user_id=%s
    """

    cursor.execute(

        query,

        (session['user_id'],)

    )

    user = cursor.fetchone()

    cursor.close()

    connection.close()

    return render_template(

        'profile.html',

        user=user

    )
# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# AI SUMMARIZER
@app.route('/summarizer', methods=['GET', 'POST'])
def summarizer():

    summary = None

    if request.method == 'POST':

        long_text = request.form['long_text']

        summary = summarize_text(long_text)

    return render_template(

        'summarizer.html',

        summary=summary

    )


# OCR TOOL
@app.route('/ocr', methods=['GET', 'POST'])
def ocr():

    extracted_text = None

    if request.method == 'POST':

        image = request.files['image']

        image_path = os.path.join(

            'static/uploads',

            image.filename

        )

        image.save(image_path)

        extracted_text = extract_text(image_path)

    return render_template(

        'ocr.html',

        extracted_text=extracted_text

    )


# AUDIO TO TEXT
@app.route('/audio', methods=['GET', 'POST'])
def audio():

    text = None

    if request.method == 'POST':

        audio = request.files['audio']

        audio_path = os.path.join(

            'static/uploads',

            audio.filename

        )

        audio.save(audio_path)

        text = audio_to_text(audio_path)

    return render_template(

        'audio.html',

        text=text

    )


# STUDY PLANNER
@app.route('/planner', methods=['GET', 'POST'])
def planner():

    if 'user_id' not in session:

        return redirect('/login')

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        subject = request.form['subject']
        study_time = request.form['study_time']
        exam_date = request.form['exam_date']

        query = """
        INSERT INTO study_planner
        (user_id, subject, study_time, exam_date)
        VALUES (%s, %s, %s, %s)
        """

        values = (

            session['user_id'],
            subject,
            study_time,
            exam_date

        )

        cursor.execute(query, values)

        connection.commit()

    query = """
    SELECT * FROM study_planner
    WHERE user_id=%s
    """

    cursor.execute(query, (session['user_id'],))

    plans = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(

        'planner.html',

        plans=plans

    )


# SMART REMINDERS
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():

    if 'user_id' not in session:

        return redirect('/login')

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        title = request.form['title']
        reminder_date = request.form['reminder_date']
        reminder_time = request.form['reminder_time']

        query = """
        INSERT INTO reminders
        (user_id, title, reminder_date, reminder_time)
        VALUES (%s, %s, %s, %s)
        """

        values = (

            session['user_id'],
            title,
            reminder_date,
            reminder_time

        )

        cursor.execute(query, values)

        connection.commit()

    query = """
    SELECT * FROM reminders
    WHERE user_id=%s
    ORDER BY reminder_date
    """

    cursor.execute(query, (session['user_id'],))

    reminders_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(

        'reminders.html',

        reminders=reminders_data

    )


# NOTES / KNOWLEDGE BASE
@app.route('/notes', methods=['GET', 'POST'])
def notes():

    if 'user_id' not in session:

        return redirect('/login')

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        note_type = request.form['type']

        title = request.form['title']

        content = request.form['content']

        uploaded_file = request.files['file']

        file_name = None

        if uploaded_file.filename != '':

            file_name = uploaded_file.filename

            file_path = os.path.join(

                'static/uploads',

                file_name

            )

            uploaded_file.save(file_path)

        query = """
        INSERT INTO notes
        (user_id, type, title, content, file_name)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (

            session['user_id'],
            note_type,
            title,
            content,
            file_name

        )

        cursor.execute(query, values)

        connection.commit()

    query = """
    SELECT * FROM notes
    WHERE user_id=%s
    ORDER BY note_id DESC
    """

    cursor.execute(

        query,

        (session['user_id'],)

    )

    notes_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(

        'notes.html',

        notes=notes_data

    )


# AI CHATBOT
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    reply = None

    if request.method == 'POST':

        message = request.form['message']

        reply = chatbot_response(message)

    return render_template(

        'chatbot.html',

        reply=reply

    )


# AI QUIZ GENERATOR
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    quiz_result = None

    if request.method == 'POST':

        topic = request.form['topic']

        prompt = f"""
Generate 5 multiple choice questions
with answers for:

{topic}
"""

        quiz_result = chatbot_response(prompt)

    return render_template(

        'quiz.html',

        quiz_result=quiz_result

    )


# AI PDF SUMMARIZER
@app.route('/pdf-summary', methods=['GET', 'POST'])
def pdf_summary():

    summary = None

    if request.method == 'POST':

        pdf = request.files['pdf']

        pdf_path = os.path.join(

            'static/uploads',

            pdf.filename

        )

        pdf.save(pdf_path)

        summary = summarize_pdf(pdf_path)

    return render_template(

        'pdf_summary.html',

        summary=summary

    )


# AI TIMETABLE GENERATOR
@app.route('/timetable', methods=['GET', 'POST'])
def timetable():

    timetable_output = None

    if request.method == 'POST':

        subjects = request.form['subjects']

        hours = request.form['hours']

        prompt = f"""
Create a smart study timetable.

Subjects:
{subjects}

Available Study Hours:
{hours}
"""

        timetable_output = chatbot_response(prompt)

    return render_template(

        'timetable.html',

        timetable_output=timetable_output

    )


# AI DOUBT SOLVER
@app.route('/doubt-solver', methods=['GET', 'POST'])
def doubt_solver():

    extracted_text = None

    ai_answer = None

    if request.method == 'POST':

        image = request.files['image']

        image_path = os.path.join(

            'static/uploads',

            image.filename

        )

        image.save(image_path)

        extracted_text = extract_text(image_path)

        prompt = f"""
Answer this academic question clearly:

{extracted_text}
"""

        ai_answer = chatbot_response(prompt)

    return render_template(

        'doubt_solver.html',

        extracted_text=extracted_text,

        ai_answer=ai_answer

    )


# PROFESSIONAL RESUME BUILDER

@app.route('/resume', methods=['GET', 'POST'])
def resume():

    if request.method == 'POST':

        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        objective = request.form['objective']
        education = request.form['education']
        projects = request.form['projects']
        skills = request.form['skills']

        # CREATE FOLDER

        os.makedirs('static/resumes', exist_ok=True)

        # =========================
        # WORD RESUME
        # =========================

        document = Document()

        # NAME

        heading = document.add_heading(name, level=1)

        document.add_heading(role, level=2)

        # CONTACT

        document.add_paragraph(
            f"Phone: {phone}"
        )

        document.add_paragraph(
            f"Email: {email}"
        )

        document.add_paragraph(
            f"Address: {address}"
        )

        # ABOUT

        document.add_heading(
            'ABOUT ME',
            level=2
        )

        document.add_paragraph(objective)

        # EDUCATION

        document.add_heading(
            'EDUCATION',
            level=2
        )

        document.add_paragraph(education)

        # PROJECTS

        document.add_heading(
            'PROJECTS',
            level=2
        )

        document.add_paragraph(projects)

        # SKILLS

        document.add_heading(
            'SKILLS',
            level=2
        )

        for skill in skills.split(','):

            document.add_paragraph(
                skill.strip(),
                style='List Bullet'
            )

        # SAVE WORD FILE

        docx_path = f"static/resumes/{name}.docx"

        document.save(docx_path)

        # =========================
        # PDF RESUME
        # =========================

        pdf_path = f"static/resumes/{name}.pdf"

        doc = SimpleDocTemplate(pdf_path)

        styles = getSampleStyleSheet()

        flowables = []

        # TITLE

        flowables.append(
            Paragraph(
                f"<font size=24><b>{name}</b></font>",
                styles['Title']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # ROLE

        flowables.append(
            Paragraph(
                f"<b>{role}</b>",
                styles['Heading2']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # CONTACT

        flowables.append(
            Paragraph(
                f"📞 {phone}<br/>📧 {email}<br/>📍 {address}",
                styles['BodyText']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # ABOUT

        flowables.append(
            Paragraph(
                "<b>ABOUT ME</b>",
                styles['Heading2']
            )
        )

        flowables.append(
            Paragraph(
                objective,
                styles['BodyText']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # EDUCATION

        flowables.append(
            Paragraph(
                "<b>EDUCATION</b>",
                styles['Heading2']
            )
        )

        flowables.append(
            Paragraph(
                education,
                styles['BodyText']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # PROJECTS

        flowables.append(
            Paragraph(
                "<b>PROJECTS</b>",
                styles['Heading2']
            )
        )

        flowables.append(
            Paragraph(
                projects,
                styles['BodyText']
            )
        )

        flowables.append(
            Spacer(1, 20)
        )

        # SKILLS

        flowables.append(
            Paragraph(
                "<b>SKILLS</b>",
                styles['Heading2']
            )
        )

        for skill in skills.split(','):

            flowables.append(
                Paragraph(
                    f"• {skill.strip()}",
                    styles['BodyText']
                )
            )

        # BUILD PDF

        doc.build(flowables)

        return render_template(

            'resume_template.html',

            name=name,
            role=role,
            email=email,
            phone=phone,
            address=address,
            objective=objective,
            education=education,
            projects=projects,
            skills=skills,

            docx_file=docx_path,
            pdf_file=pdf_path

        )

    return render_template('resume.html')
# DOWNLOAD WORD RESUME

@app.route('/download/docx/<filename>')
def download_docx(filename):

    return send_from_directory(

        'static/resumes',
        filename,
        as_attachment=True

    )


# DOWNLOAD PDF RESUME

@app.route('/download/pdf/<filename>')
def download_pdf(filename):

    return send_from_directory(

        'static/resumes',
        filename,
        as_attachment=True

    )
# UPDATE PROFILE
@app.route('/update-profile', methods=['POST'])
def update_profile():

    if 'user_id' not in session:

        return redirect('/login')

    # FORM DATA

    name = request.form['name']
    email = request.form['email']
    department = request.form['department']
    college = request.form['college']
    phone = request.form['phone']
    address = request.form['address']
    skills = request.form['skills']

    # PHOTO

    photo = request.files.get('photo')

    # DATABASE

    connection = get_connection()

    cursor = connection.cursor()

    # CREATE UPLOAD FOLDER

    os.makedirs(

        'static/uploads',

        exist_ok=True

    )

    # PHOTO UPLOAD

    if photo and photo.filename != '':

        photo_name = photo.filename

        photo_path = os.path.join(

            'static/uploads',

            photo_name

        )

        photo.save(photo_path)

        query = """
        UPDATE users
        SET
        name=%s,
        email=%s,
        department=%s,
        college=%s,
        phone=%s,
        address=%s,
        skills=%s,
        photo=%s
        WHERE user_id=%s
        """

        values = (

            name,
            email,
            department,
            college,
            phone,
            address,
            skills,
            photo_name,
            session['user_id']

        )

    else:

        query = """
        UPDATE users
        SET
        name=%s,
        email=%s,
        department=%s,
        college=%s,
        phone=%s,
        address=%s,
        skills=%s
        WHERE user_id=%s
        """

        values = (

            name,
            email,
            department,
            college,
            phone,
            address,
            skills,
            session['user_id']

        )

    # EXECUTE

    cursor.execute(query, values)

    connection.commit()

    cursor.close()

    connection.close()

    # SESSION UPDATE

    session['name'] = name

    return redirect('/profile')

# ==========================================
# NEW ACADEMIC INTELLIGENCE SUITE ROUTES
# ==========================================

# 1. DIFFICULT TOPIC TUTOR [AI]
@app.route('/tutor', methods=['GET', 'POST'])
def tutor():
    if 'user_id' not in session:
        return redirect('/login')

    explanation = None
    topic = ""
    level = "intermediate"

    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        level = request.form.get('level', 'intermediate')
        if topic:
            explanation = explain_difficult_topic(topic, level)

    return render_template('tutor.html', explanation=explanation, topic=topic, level=level, name=session.get('name', 'Student'))

# 2. LEARNING ROADMAP
@app.route('/learning-roadmap')
def learning_roadmap():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM learning_roadmap WHERE user_id = %s ORDER BY phase_number ASC", (user_id,))
    roadmap_items = cursor.fetchall()

    cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
    stats = cursor.fetchone()

    cursor.close()
    connection.close()

    total_units = int(stats['total_units']) if stats and stats.get('total_units') else len(roadmap_items)
    completed_units = int(stats['completed_units']) if stats and stats.get('completed_units') else 0
    syllabus_percent = round((float(completed_units) / float(total_units)) * 100, 1) if total_units > 0 else 0.0

    return render_template(
        'learning_roadmap.html',
        name=session.get('name', 'Student'),
        roadmap_items=roadmap_items,
        stats=stats,
        syllabus_percent=syllabus_percent
    )

@app.route('/learning-roadmap/generate', methods=['POST'])
def generate_roadmap():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    topic = request.form.get('topic', '').strip()
    level = request.form.get('level', 'Beginner to Advanced')

    if not topic:
        return redirect('/learning-roadmap')

    prompt = f"""Generate a structured learning roadmap for student studying: "{topic}".
Target Level: {level}.
Output strictly a valid JSON array of 4 or 5 objects with keys:
"phase_number": integer (1, 2, 3, etc.),
"phase_name": short string (e.g. "Phase 1: Foundations"),
"topic_title": string (title of the module),
"description": string (1-2 sentences on what will be mastered in this phase).
No markdown backticks, only raw JSON array."""

    phases = []
    try:
        raw = chatbot_response(prompt)
        cleaned = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        phases = json.loads(cleaned)
    except Exception:
        phases = [
            {"phase_number": 1, "phase_name": "Phase 1: Core Fundamentals", "topic_title": f"{topic} Basics & Terminology", "description": f"Foundational syntax, key concepts, core principles, and introductory frameworks for {topic}."},
            {"phase_number": 2, "phase_name": "Phase 2: Intermediate Deep Dive", "topic_title": f"{topic} Application & Patterns", "description": f"Intermediate techniques, problem-solving paradigms, core libraries, and practical drills in {topic}."},
            {"phase_number": 3, "phase_name": "Phase 3: Advanced Concepts", "topic_title": f"Advanced {topic} & Architecture", "description": f"Complex architectural patterns, performance optimization, best practices, and enterprise standards."},
            {"phase_number": 4, "phase_name": "Phase 4: Capstone & Mastery", "topic_title": f"{topic} Exam & Project Readiness", "description": f"Comprehensive review, past problem sets, end-to-end implementation project, and final certification drill."}
        ]

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Replace prior roadmap for this user with new topic
    cursor.execute("DELETE FROM learning_roadmap WHERE user_id = %s", (user_id,))

    for p in phases:
        p_num = int(p.get('phase_number', 1))
        status = 'in_progress' if p_num == 1 else 'upcoming'
        cursor.execute("""
            INSERT INTO learning_roadmap (user_id, phase_number, phase_name, topic_title, description, status, progress_percent, quiz_score, hours_logged)
            VALUES (%s, %s, %s, %s, %s, %s, 0, NULL, 0.0)
        """, (user_id, p_num, p.get('phase_name'), p.get('topic_title'), p.get('description'), status))

    cursor.execute("""
        UPDATE student_academic_stats 
        SET total_units = %s, completed_units = 0, smart_revision_topic = %s
        WHERE user_id = %s
    """, (len(phases), topic, user_id))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('/learning-roadmap')

@app.route('/learning-roadmap/reset', methods=['POST'])
def reset_roadmap():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM learning_roadmap WHERE user_id = %s", (user_id,))
    cursor.execute("UPDATE student_academic_stats SET completed_units = 0, total_units = 0, smart_revision_topic = NULL WHERE user_id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/learning-roadmap')

@app.route('/learning-roadmap/update', methods=['POST'])
def update_roadmap():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    item_id = request.form.get('id')
    action = request.form.get('action', 'complete')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    if action == 'complete':
        cursor.execute("UPDATE learning_roadmap SET status = 'completed', progress_percent = 100 WHERE id = %s AND user_id = %s", (item_id, user_id))

        cursor.execute("SELECT phase_number FROM learning_roadmap WHERE id = %s", (item_id,))
        curr = cursor.fetchone()
        if curr:
            next_phase = curr['phase_number'] + 1
            cursor.execute("UPDATE learning_roadmap SET status = 'in_progress', progress_percent = 25 WHERE user_id = %s AND phase_number = %s AND status = 'upcoming'", (user_id, next_phase))

    elif action == 'incomplete':
        cursor.execute("UPDATE learning_roadmap SET status = 'in_progress', progress_percent = 50 WHERE id = %s AND user_id = %s", (item_id, user_id))

    cursor.execute("SELECT COUNT(*) as comp FROM learning_roadmap WHERE user_id = %s AND status = 'completed'", (user_id,))
    comp_row = cursor.fetchone()
    if comp_row:
        cursor.execute("UPDATE student_academic_stats SET completed_units = %s WHERE user_id = %s", (comp_row['comp'], user_id))

    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/learning-roadmap')

# 3. PROGRESS & ANALYTICS
@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
    stats = cursor.fetchone()

    if not stats:
        cursor.execute("""
            INSERT INTO student_academic_stats 
            (user_id, level, xp, streak_days, today_studied_hours, today_target_hours, completed_units, total_units, smart_revision_topic, dominant_learning_style, retention_rate)
            VALUES (%s, 1, 0, 1, 0.0, 6.0, 0, 0, NULL, 'Undetermined', 0)
        """, (user_id,))
        connection.commit()
        cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
        stats = cursor.fetchone()

    cursor.execute("SELECT * FROM student_study_logs WHERE user_id = %s ORDER BY id ASC", (user_id,))
    study_logs = cursor.fetchall()

    cursor.execute("SELECT * FROM student_weaknesses WHERE user_id = %s ORDER BY id ASC", (user_id,))
    weaknesses = cursor.fetchall()

    # Dynamic Subject Mastery and roadmap unit tracking directly from MySQL
    cursor.execute("""
        SELECT topic_title, phase_name, quiz_score, progress_percent, status 
        FROM learning_roadmap 
        WHERE user_id = %s 
        ORDER BY phase_number ASC
    """, (user_id,))
    roadmap_rows = cursor.fetchall()

    if roadmap_rows:
        total_units = len(roadmap_rows)
        completed_units = sum(1 for rm in roadmap_rows if rm.get('status') == 'completed')
        if stats and (stats.get('total_units') != total_units or stats.get('completed_units') != completed_units):
            cursor.execute("UPDATE student_academic_stats SET total_units = %s, completed_units = %s WHERE user_id = %s", (total_units, completed_units, user_id))
            connection.commit()
            stats['total_units'] = total_units
            stats['completed_units'] = completed_units
    else:
        total_units = int(stats['total_units']) if stats and stats.get('total_units') is not None else 0
        completed_units = int(stats['completed_units']) if stats and stats.get('completed_units') is not None else 0

    mastery_labels = []
    mastery_data = []

    if roadmap_rows:
        for rm in roadmap_rows:
            label = rm['topic_title'] if rm.get('topic_title') else rm.get('phase_name', 'Topic')
            if len(label) > 22:
                label = label[:20] + '..'
            score = 0
            if rm.get('quiz_score') is not None and int(rm['quiz_score']) > 0:
                score = int(rm['quiz_score'])
            elif rm.get('status') == 'completed':
                score = 100
            elif rm.get('progress_percent') is not None and int(rm['progress_percent']) > 0:
                score = int(rm['progress_percent'])
            mastery_labels.append(label)
            mastery_data.append(score)
    else:
        cursor.execute("SELECT subject, COUNT(*) as cnt FROM study_planner WHERE user_id = %s GROUP BY subject", (user_id,))
        planner_rows = cursor.fetchall()
        if planner_rows:
            tot = sum(p['cnt'] for p in planner_rows)
            for p in planner_rows:
                mastery_labels.append(p['subject'])
                mastery_data.append(int(round((p['cnt'] / tot) * 100)) if tot > 0 else 0)

    cursor.close()
    connection.close()

    today_studied = float(stats['today_studied_hours']) if stats and stats.get('today_studied_hours') is not None else 0.0
    target_hours = float(stats['today_target_hours']) if stats and stats.get('today_target_hours') is not None and float(stats['today_target_hours']) > 0 else 6.0
    goal_percent = int(round((today_studied / target_hours) * 100)) if target_hours > 0 else 0
    syllabus_percent = round((float(completed_units) / float(total_units)) * 100, 1) if total_units > 0 else 0.0

    return render_template(
        'analytics.html',
        name=session.get('name', 'Student'),
        stats=stats,
        study_logs=study_logs,
        weaknesses=weaknesses,
        goal_percent=goal_percent,
        syllabus_percent=syllabus_percent,
        mastery_labels=mastery_labels,
        mastery_data=mastery_data
    )

@app.route('/analytics/log-study', methods=['POST'])
def log_study():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    hours = float(request.form.get('hours', 1.0))
    day_name = request.form.get('day_name', 'Today')

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE student_academic_stats SET today_studied_hours = today_studied_hours + %s WHERE user_id = %s", (hours, user_id))
    cursor.execute("INSERT INTO student_study_logs (user_id, day_name, hours, log_date) VALUES (%s, %s, %s, CURDATE())", (user_id, day_name, hours))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/analytics')

@app.route('/analytics/resolve-weakness/<int:weakness_id>', methods=['POST'])
def resolve_weakness(weakness_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM student_weaknesses WHERE id = %s AND user_id = %s", (weakness_id, user_id))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/analytics')

# 4. GK ZONE
GK_FACTS_POOL = [
    {
        "title": "Quantum Supercomputer Milestone",
        "description": "Researchers have demonstrated 1,000+ logical qubits operating with real-time quantum error correction, solving classical cryptography challenges in seconds.",
        "category": "Quantum Computing",
        "icon": "fa-atom"
    },
    {
        "title": "James Webb's Earliest Galaxy Discovery",
        "description": "JWST detected JADES-GS-z14-0, a luminous galaxy formed just 290 million years after the Big Bang, defying traditional cosmic evolution models.",
        "category": "Astrophysics",
        "icon": "fa-satellite"
    },
    {
        "title": "Voyager 1 Interstellar Longevity",
        "description": "Launched in 1977, Voyager 1 is over 15 billion miles away, communicating across interstellar space with radio signals taking over 22 hours each way.",
        "category": "Space Exploration",
        "icon": "fa-shuttle-space"
    },
    {
        "title": "Neural Plasticity & Sleep Consolidation",
        "description": "During deep slow-wave sleep, the brain activates the glymphatic system to flush metabolic waste and replays neural patterns to cement long-term memories.",
        "category": "Neuroscience",
        "icon": "fa-brain"
    },
    {
        "title": "Silicon Photonics Speed Breakthrough",
        "description": "Optical interconnects transmitting data at 1.6 Terabits per second using light instead of copper wires reduce AI datacenter power draw by over 40%.",
        "category": "Computer Science",
        "icon": "fa-microchip"
    },
    {
        "title": "The Origin of the Mathematical Zero",
        "description": "The numeral zero as both a placeholder and a number with arithmetic rules was formalized by Indian astronomer Brahmagupta in the 7th century CE.",
        "category": "Mathematics & History",
        "icon": "fa-calculator"
    },
    {
        "title": "Challenger Deep & Ocean Extremophiles",
        "description": "At Challenger Deep (10,994 meters depth), pressure exceeds 1,000 atmospheres, yet snailfish and xenophyophores thrive without any sunlight.",
        "category": "Oceanography",
        "icon": "fa-water"
    },
    {
        "title": "CRISPR-Cas9 Base Editing Precision",
        "description": "Next-generation base editors can chemically swap individual DNA base pairs without double-stranded breaks, correcting point mutations for sickle cell anemia.",
        "category": "Biotechnology",
        "icon": "fa-dna"
    },
    {
        "title": "The 2,000-Year-Old Antikythera Mechanism",
        "description": "Discovered in a shipwreck, this geared bronze computational artifact predicted solar eclipses, planetary alignments, and Olympic cycles with clockwork precision.",
        "category": "Ancient Science",
        "icon": "fa-gear"
    },
    {
        "title": "Fast Radio Bursts (FRBs) from Magnetars",
        "description": "Millisecond-long radio bursts with energy exceeding 500 million Suns have been traced to magnetars—neutron stars with magnetic fields a quadrillion times Earth's.",
        "category": "Cosmology",
        "icon": "fa-bolt"
    },
    {
        "title": "Graphene: The One-Atom Miracle",
        "description": "A single atom-thick lattice of carbon is 200 times stronger than steel, more conductive than copper, and absorbs only 2.3% of incident light.",
        "category": "Materials Science",
        "icon": "fa-cubes"
    },
    {
        "title": "Attention is All You Need (Transformers)",
        "description": "Published by Google researchers in 2017, the Transformer neural architecture replaced recurrence with self-attention, powering all modern LLMs.",
        "category": "Artificial Intelligence",
        "icon": "fa-robot"
    },
    {
        "title": "Pacific Ring of Fire Subduction",
        "description": "The Pacific Plate tectonic motion drives over 75% of the world's active volcanoes and 90% of global seismic energy around the 40,000 km Ring of Fire.",
        "category": "Geology",
        "icon": "fa-volcano"
    },
    {
        "title": "Quantum Coherence in Photosynthesis",
        "description": "Plant chlorophyll complexes harvest solar photons with near 100% quantum efficiency by exploiting quantum coherence to probe multiple energy pathways simultaneously.",
        "category": "Quantum Biology",
        "icon": "fa-leaf"
    },
    {
        "title": "The Library of Alexandria Legacy",
        "description": "Founded in the 3rd century BCE, the Library gathered an estimated 400,000 scrolls, preserving early astronomy, geometry, and medicine for antiquity.",
        "category": "World History",
        "icon": "fa-landmark"
    }
]

@app.route('/gk-zone')
def gk_zone():
    if 'user_id' not in session:
        return redirect('/login')

    # Randomly select a fresh fact on EVERY refresh
    fact_of_the_day = random.choice(GK_FACTS_POOL)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Shuffle questions on every refresh
    cursor.execute("SELECT * FROM gk_questions ORDER BY RAND()")
    gk_questions = cursor.fetchall()

    # Dynamic counts per category
    cursor.execute("SELECT category, COUNT(*) as cnt FROM gk_questions GROUP BY category")
    cat_rows = cursor.fetchall()
    cat_counts = {}
    for r in cat_rows:
        cat_counts[r['category'].lower()] = r['cnt']

    cursor.close()
    connection.close()

    return render_template(
        'gk_zone.html',
        name=session.get('name', 'Student'),
        gk_questions=gk_questions,
        fact_of_the_day=fact_of_the_day,
        cat_counts=cat_counts,
        all_facts=GK_FACTS_POOL
    )

@app.route('/gk-zone/add', methods=['POST'])
def add_gk_question():
    if 'user_id' not in session:
        return redirect('/login')
    category = request.form.get('category', 'General')
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    if question and answer:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO gk_questions (category, question, answer) VALUES (%s, %s, %s)", (category, question, answer))
        connection.commit()
        cursor.close()
        connection.close()
    return redirect('/gk-zone')

# 5. CAREER ROADMAP
@app.route('/career-roadmap')
def career_roadmap():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    retake = request.args.get('retake') == '1'

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT target_career_track FROM student_academic_stats WHERE user_id = %s", (user_id,))
    stats_row = cursor.fetchone()
    selected_track_code = stats_row.get('target_career_track') if stats_row else None

    if retake:
        selected_track_code = None

    cursor.execute("SELECT * FROM career_tracks ORDER BY id ASC")
    raw_tracks = cursor.fetchall()
    cursor.close()
    connection.close()

    tracks = []
    for t in raw_tracks:
        item = dict(t)
        if isinstance(item.get('skills'), str):
            try:
                item['skills'] = json.loads(item['skills'])
            except Exception:
                item['skills'] = [item['skills']]
        if isinstance(item.get('certifications'), str):
            try:
                item['certifications'] = json.loads(item['certifications'])
            except Exception:
                item['certifications'] = [item['certifications']]
        if isinstance(item.get('target_roles'), str):
            try:
                item['target_roles'] = json.loads(item['target_roles'])
            except Exception:
                item['target_roles'] = [item['target_roles']]
        tracks.append(item)

    chosen_track = None
    if selected_track_code:
        for t in tracks:
            if t['track_code'] == selected_track_code:
                chosen_track = t
                break

    has_assessed = chosen_track is not None

    return render_template(
        'career_roadmap.html',
        name=session.get('name', 'Student'),
        tracks=tracks,
        has_assessed=has_assessed,
        chosen_track=chosen_track,
        selected_track_code=selected_track_code
    )

@app.route('/career-roadmap/select', methods=['POST'])
def select_career_track():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    track_code = request.form.get('track_code', '').strip().lower()

    if track_code:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE student_academic_stats SET target_career_track = %s WHERE user_id = %s", (track_code, user_id))
        connection.commit()
        cursor.close()
        connection.close()

    return redirect('/career-roadmap')

@app.route('/career-roadmap/reset', methods=['POST'])
def reset_career_track():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE student_academic_stats SET target_career_track = NULL WHERE user_id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return redirect('/career-roadmap')

# 6. SETTINGS
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    message = None

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        daily_hours = request.form.get('daily_hours', '6.0')
        studied_hours = request.form.get('studied_hours')
        rev_topic = request.form.get('rev_topic')
        learning_style = request.form.get('learning_style')

        cursor.execute("""
            UPDATE student_academic_stats 
            SET today_target_hours = %s,
                today_studied_hours = COALESCE(%s, today_studied_hours),
                smart_revision_topic = COALESCE(%s, smart_revision_topic),
                dominant_learning_style = COALESCE(%s, dominant_learning_style)
            WHERE user_id = %s
        """, (daily_hours, studied_hours if studied_hours else None, rev_topic if rev_topic else None, learning_style if learning_style else None, user_id))
        connection.commit()
        message = "Academic quotas & preferences updated in MySQL database successfully! ✅"

    cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
    stats = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template('settings.html', message=message, name=session.get('name', 'Student'), stats=stats)

# 7. CLOSED-LOOP FLYWHEEL API (100% DYNAMIC FROM MYSQL DATABASE)
@app.route('/api/flywheel/<int:step>')
def flywheel_status(step):
    user_id = session.get('user_id')
    user_name = session.get('name', 'Student')

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    stats = None
    weaknesses = []
    active_roadmap = None

    if user_id:
        cursor.execute("SELECT * FROM student_academic_stats WHERE user_id = %s", (user_id,))
        stats = cursor.fetchone()

        cursor.execute("SELECT topic, severity FROM student_weaknesses WHERE user_id = %s", (user_id,))
        weaknesses = cursor.fetchall()

        cursor.execute("SELECT topic_title, phase_name, status, progress_percent FROM learning_roadmap WHERE user_id = %s AND status = 'in_progress' LIMIT 1", (user_id,))
        active_roadmap = cursor.fetchone()

    cursor.close()
    connection.close()

    studied = float(stats['today_studied_hours']) if stats and stats.get('today_studied_hours') is not None else 0.0
    target = float(stats['today_target_hours']) if stats and stats.get('today_target_hours') is not None and float(stats['today_target_hours']) > 0 else 6.0
    completed = int(stats['completed_units']) if stats and stats.get('completed_units') is not None else 0
    total = int(stats['total_units']) if stats and stats.get('total_units') is not None and int(stats['total_units']) > 0 else 0
    goal_pct = int(round((studied / target) * 100)) if target > 0 else 0
    syl_pct = round((float(completed) / float(total)) * 100, 1) if total > 0 else 0.0
    streak = int(stats['streak_days']) if stats and stats.get('streak_days') is not None else 1
    rev_topic = stats.get('smart_revision_topic') if stats else None
    style = stats.get('dominant_learning_style') if stats and stats.get('dominant_learning_style') else 'Adaptive'
    retention = int(stats['retention_rate']) if stats and stats.get('retention_rate') is not None else 0

    if step == 1:
        return jsonify({
            "title": "1. Quiz Engine System",
            "detail": f"Active student assessment engine. Current streak: {streak} Day{'s' if streak > 1 else ''}. Take a quiz to test your mastery.",
            "url": "/quiz",
            "action_text": "Launch Practice Quiz"
        })
    elif step == 2:
        return jsonify({
            "title": "2. Mistake & Doubt Analysis",
            "detail": "AI Doubt Solver is online. Ask questions anytime or submit complex problems for step-by-step breakdown.",
            "url": "/doubt-solver",
            "action_text": "Open Doubt Solver"
        })
    elif step == 3:
        if weaknesses:
            w_list = ", ".join([w['topic'] for w in weaknesses[:2]])
            w_detail = f"Identified {len(weaknesses)} active weakness{'es' if len(weaknesses) > 1 else ''} in database ({w_list}). Focused revision recommended."
        else:
            w_detail = "0 active weaknesses diagnosed in MySQL database. You currently have a clean mastery record!"
        return jsonify({
            "title": "3. Weakness Diagnostic Log",
            "detail": w_detail,
            "url": "/analytics",
            "action_text": "View Weakness Diagnostic"
        })
    elif step == 4:
        d_text = f"Cognitive Profile: {style} (Retention Rate: {retention}%)." if retention > 0 else f"Cognitive Profile: {style}. Complete practice modules to compute your exact retention score."
        return jsonify({
            "title": "4. Learning DNA Profile",
            "detail": d_text,
            "url": "/analytics",
            "action_text": "View Learning DNA"
        })
    elif step == 5:
        m_title = active_roadmap['topic_title'] if active_roadmap else "Phase 1: Foundations"
        return jsonify({
            "title": "5. Adaptive Learning Roadmap",
            "detail": f"Current Active Module: {m_title}. Total progress: {completed} of {total} units mastered ({syl_pct}%).",
            "url": "/learning-roadmap",
            "action_text": "Open Learning Roadmap"
        })
    elif step == 6:
        rev_detail = f"Smart spaced-repetition trigger scheduled for '{rev_topic}'." if rev_topic else "No revision backlog! Complete your next study module to queue automatic spaced revisions."
        return jsonify({
            "title": "6. Smart Revision Trigger",
            "detail": rev_detail,
            "url": "/tutor" if rev_topic else "/learning-roadmap",
            "action_text": "Revise with AI Tutor" if rev_topic else "Explore Roadmap"
        })
    elif step == 7:
        return jsonify({
            "title": "7. Targeted New Quiz",
            "detail": f"Generates dynamic recovery questions targeted to your active curriculum ({completed}/{total} units completed).",
            "url": "/quiz",
            "action_text": "Generate Targeted Quiz"
        })
    elif step == 8:
        return jsonify({
            "title": "8. Real-Time Progress Tracker",
            "detail": f"Today's Goal: {studied} / {target} Hours ({goal_pct}%). Total Syllabus: {completed} / {total} Units ({syl_pct}%). Streak: {streak} Day{'s' if streak > 1 else ''}.",
            "url": "/analytics",
            "action_text": "Open Full Analytics"
        })
    elif step == 9:
        return jsonify({
            "title": "9. Neural DNA & Database Sync",
            "detail": f"Student account ({user_name}, ID: {user_id}) synchronized across all 9 platform subsystems with MySQL database.",
            "url": "/settings",
            "action_text": "Platform Settings"
        })
    else:
        return jsonify({"title": "System Active", "detail": "Live database sync active.", "url": "/dashboard", "action_text": "Dashboard"})

if __name__ == '__main__':

    app.run(debug=True)