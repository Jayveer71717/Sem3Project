-- Student Management System schema (MySQL / MariaDB via XAMPP)
-- Import with phpMyAdmin (Import tab) or:  mysql -u root < schema.sql

CREATE DATABASE IF NOT EXISTS sms
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sms;

-- Login accounts for both roles (passwords are stored as hashes only)
CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('admin','student') NOT NULL,
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  last_login    DATETIME     NULL,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB;

-- Student profile, one-to-one with a student login account
CREATE TABLE IF NOT EXISTS students (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id        INT UNSIGNED NOT NULL,
  roll_no        VARCHAR(30)  NOT NULL,
  full_name      VARCHAR(100) NOT NULL,
  email          VARCHAR(120) NULL,
  phone          VARCHAR(20)  NULL,
  course         VARCHAR(80)  NOT NULL,
  semester       TINYINT UNSIGNED NOT NULL DEFAULT 1,
  date_of_birth  DATE         NULL,
  address        VARCHAR(255) NULL,
  admission_date DATE         NULL,
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_students_user (user_id),
  UNIQUE KEY uq_students_roll (roll_no),
  CONSTRAINT fk_students_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subjects (
  id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code     VARCHAR(20)  NOT NULL,
  name     VARCHAR(100) NOT NULL,
  course   VARCHAR(80)  NOT NULL,
  semester TINYINT UNSIGNED NOT NULL,
  credits  TINYINT UNSIGNED NOT NULL DEFAULT 3,
  PRIMARY KEY (id),
  UNIQUE KEY uq_subjects_code (code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
  id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id INT UNSIGNED NOT NULL,
  subject_id INT UNSIGNED NOT NULL,
  class_date DATE NOT NULL,
  status     ENUM('present','absent','late') NOT NULL,
  marked_by  INT UNSIGNED NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_attendance (student_id, subject_id, class_date),
  KEY idx_attendance_date (class_date),
  CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_user    FOREIGN KEY (marked_by)  REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS marks (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id     INT UNSIGNED NOT NULL,
  subject_id     INT UNSIGNED NOT NULL,
  exam_type      ENUM('internal','midterm','final','practical') NOT NULL,
  marks_obtained DECIMAL(5,2) NOT NULL,
  max_marks      DECIMAL(5,2) NOT NULL DEFAULT 100,
  exam_date      DATE NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_marks (student_id, subject_id, exam_type),
  CONSTRAINT chk_marks_range CHECK (marks_obtained >= 0 AND marks_obtained <= max_marks),
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS assignments (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  subject_id  INT UNSIGNED NOT NULL,
  title       VARCHAR(150) NOT NULL,
  description TEXT NULL,
  due_date    DATE NOT NULL,
  max_marks   DECIMAL(5,2) NOT NULL DEFAULT 10,
  created_by  INT UNSIGNED NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_assignments_due (due_date),
  CONSTRAINT fk_asg_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  CONSTRAINT fk_asg_user    FOREIGN KEY (created_by) REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB;

-- One row per student per assignment: tracks status and grading
CREATE TABLE IF NOT EXISTS assignment_submissions (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  assignment_id INT UNSIGNED NOT NULL,
  student_id    INT UNSIGNED NOT NULL,
  status        ENUM('pending','submitted','graded') NOT NULL DEFAULT 'pending',
  submitted_at  DATETIME NULL,
  marks_awarded DECIMAL(5,2) NULL,
  remarks       VARCHAR(255) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_submission (assignment_id, student_id),
  CONSTRAINT fk_sub_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
  CONSTRAINT fk_sub_student    FOREIGN KEY (student_id)    REFERENCES students(id)    ON DELETE CASCADE
) ENGINE=InnoDB;
