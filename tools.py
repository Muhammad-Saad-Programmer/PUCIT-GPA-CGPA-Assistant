from math import inf

COURSES = {
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation - I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],

    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation - II", 0.5),
    ],

    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation - III", 0.5),
    ],

    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation - IV", 0.5),
    ],

    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation - V", 0.5),
    ],

    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation - VI", 0.5),
    ],

    7: [
        ("CC-411", "Final Year Project - I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation - VII", 0.5),
    ],

    8: [
        ("CC-412", "Final Year Project - II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation - VIII", 0.5),
    ],
}


def _valid_gpa(value):
    return type(value) in (int, float) and 0 <= value <= 4
def _valid_hours(value):
    return type(value) in (int, float) and 0 < value < inf
def marks_to_grade_points(marks: int) -> float | str:
    """Use when a student provides marks and asks for the corresponding grade points."""
    if type(marks) is not int or not 0 <= marks <= 100:
        return "Error: marks must be between 0 and 100"
    if marks >= 85:
        return 4.0
    elif marks >= 80:
        return 3.7
    elif marks >= 75:
        return 3.3
    elif marks >= 70:
        return 3.0
    elif marks >= 65:
        return 2.7
    elif marks >= 61:
        return 2.3
    elif marks >= 58:
        return 2.0
    elif marks >= 55:
        return 1.7
    elif marks >= 50:
        return 1.0
    else:
        return 0.0
def calculate_semester_gpa(
    grade_points: list[float],
    credit_hours: list[float]
) -> float | str:
    """Use when grade points and their credit hours are available and the student asks for semester GPA."""
    if not isinstance(grade_points, (list, tuple)) or not isinstance(credit_hours, (list, tuple)):
        return "Error: grade points and credit hours must be lists"
    if not grade_points or not credit_hours:
        return "Error: grade points and credit hours cannot be empty"

    if len(grade_points) != len(credit_hours):
        return "Error: grade points and credit hours must have the same length"

    if not all(_valid_hours(credit) for credit in credit_hours):
        return "Error: credit hours must be greater than 0"

    if not all(_valid_gpa(point) for point in grade_points):
        return "Error: grade points must be between 0 and 4"

    total_credit_hours = sum(credit_hours)

    weighted_points = sum(
        grade * credit
        for grade, credit in zip(grade_points, credit_hours)
    )
    return weighted_points / total_credit_hours

def calculate_new_cgpa(
    current_cgpa: float,
    completed_credit_hours: float,
    semester_gpa: float,
    semester_credit_hours: float
) -> float | str:
    """Use when a student provides current CGPA, completed hours, semester GPA, and semester hours to project a new CGPA."""

    if not _valid_gpa(current_cgpa):
        return "Error: current CGPA must be between 0 and 4"

    if not _valid_gpa(semester_gpa):
        return "Error: semester GPA must be between 0 and 4"

    if not _valid_hours(completed_credit_hours):
        return "Error: completed credit hours must be greater than 0"

    if not _valid_hours(semester_credit_hours):
        return "Error: semester credit hours must be greater than 0"

    new_cgpa = (
        current_cgpa * completed_credit_hours
        + semester_gpa * semester_credit_hours
    ) / (
        completed_credit_hours + semester_credit_hours
    )

    return new_cgpa

def required_gpa_for_target(
    target_cgpa: float,
    current_cgpa: float,
    completed_credit_hours: float,
    remaining_credit_hours: float
) -> float | str:
    """Use when a student wants to know the GPA needed over the remaining credit hours to reach a target CGPA."""

    if not _valid_gpa(target_cgpa):
        return "Error: target CGPA must be between 0 and 4"

    if not _valid_gpa(current_cgpa):
        return "Error: current CGPA must be between 0 and 4"

    if not _valid_hours(completed_credit_hours):
        return "Error: completed credit hours must be greater than 0"

    if not _valid_hours(remaining_credit_hours):
        return "Error: remaining credit hours must be greater than 0"

    required_gpa = (
        target_cgpa * (completed_credit_hours + remaining_credit_hours)
        - current_cgpa * completed_credit_hours
    ) / remaining_credit_hours

    return required_gpa
def get_semester_courses(semester: int) -> str:
    """Look up courses, semester hours, or cumulative planning hours starting in this semester."""

    if type(semester) is not int or semester not in COURSES:
        return "Error: semester must be between 1 and 8"

    courses = COURSES[semester]

    result = f"Semester {semester} courses:\n"

    for code, name, credit_hours in courses:
        result += f"- {code}: {name} ({credit_hours} credit hours)\n"

    result += f"Graded hours starting in semester {semester}:\n"
    horizon_hours = 0.0
    for end in range(semester, 9):
        horizon_hours += sum(hours for _, _, hours in COURSES[end])
        result += f"- Through semester {end}: {horizon_hours} credit hours\n"

    return result

def get_remaining_credit_hours(current_semester: int) -> float | str:
    """Use when a student asks how many graded credit hours remain after their current semester."""

    if type(current_semester) is not int or current_semester not in COURSES:
        return "Error: semester must be between 1 and 8"

    remaining_hours = 0.0

    for semester in range(current_semester + 1, 9):
        for _, _, credit_hours in COURSES[semester]:
            remaining_hours += credit_hours

    return remaining_hours
def save_report(filename: str, content: str) -> str:
    """Use when the student explicitly asks to save a useful GPA, CGPA, or target-GPA result to a file."""

    if not isinstance(filename, str) or not filename.strip():
        return "Error: filename cannot be empty"

    if not isinstance(content, str) or not content.strip():
        return "Error: report content cannot be empty"

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Report saved successfully to {filename}"

    except (OSError, ValueError) as error:
        return f"Error: could not save report: {error}"
