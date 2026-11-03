-- StudyMate AI Platform - Complete MySQL Database Schema
-- Database: studymate_ai (Running on MySQL port 3307)

CREATE DATABASE IF NOT EXISTS studymate_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studymate_ai;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. STUDENT ACADEMIC STATS (Dashboard KPIs, Streaks, Syllabus Progress)
CREATE TABLE IF NOT EXISTS student_academic_stats (
    user_id INT PRIMARY KEY,
    level INT DEFAULT 3,
    xp INT DEFAULT 650,
    streak_days INT DEFAULT 7,
    today_studied_hours DECIMAL(4,1) DEFAULT 4.3,
    today_target_hours DECIMAL(4,1) DEFAULT 6.0,
    completed_units INT DEFAULT 14,
    total_units INT DEFAULT 17,
    smart_revision_topic VARCHAR(150) DEFAULT 'Quadratic Equations',
    smart_revision_reason VARCHAR(255) DEFAULT 'Spaced-repetition trigger: revise roots formula today',
    dominant_learning_style VARCHAR(100) DEFAULT 'Visual & Analogy-Driven',
    retention_rate INT DEFAULT 86,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. LEARNING ROADMAP (Progression phases, topics, quiz scores)
CREATE TABLE IF NOT EXISTS learning_roadmap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phase_number INT NOT NULL,
    phase_name VARCHAR(100) NOT NULL,
    topic_title VARCHAR(200) NOT NULL,
    description TEXT,
    status ENUM('completed', 'in_progress', 'upcoming') DEFAULT 'upcoming',
    progress_percent INT DEFAULT 0,
    quiz_score INT DEFAULT NULL,
    hours_logged DECIMAL(4,1) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. STUDENT STUDY LOGS (Weekly study hours for Chart.js)
CREATE TABLE IF NOT EXISTS student_study_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    hours DECIMAL(4,1) NOT NULL,
    log_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. STUDENT WEAKNESSES (AI Weakness Diagnostic Log)
CREATE TABLE IF NOT EXISTS student_weaknesses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    topic VARCHAR(150) NOT NULL,
    issue_description TEXT NOT NULL,
    severity ENUM('Critical', 'Moderate', 'Low') DEFAULT 'Moderate',
    subject VARCHAR(100) DEFAULT 'General',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. GK QUESTIONS (Competitive Trivia & Flashcards)
CREATE TABLE IF NOT EXISTS gk_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(80) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. CAREER TRACKS (Career Roadmap & Skills Navigator)
CREATE TABLE IF NOT EXISTS career_tracks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    track_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    icon VARCHAR(50) NOT NULL,
    salary_range VARCHAR(80) NOT NULL,
    description TEXT NOT NULL,
    skills JSON NOT NULL,
    certifications JSON NOT NULL,
    target_roles JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. NOTES & KNOWLEDGE BASE
CREATE TABLE IF NOT EXISTS notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. REMINDERS
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    reminder_date DATE NOT NULL,
    reminder_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. STUDY PLANNER
CREATE TABLE IF NOT EXISTS study_planner (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    study_date DATE NOT NULL,
    target_hours DECIMAL(4,1) NOT NULL,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. LOGIN HISTORY
CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
