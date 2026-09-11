import numpy as np
import pandas as pd


# ============================================================
# GRADE
# ============================================================

def calculate_grade(percentage):
    if percentage is None:
        return "F"

    try:
        percentage = float(percentage)
    except Exception:
        return "F"

    if np.isnan(percentage):
        return "F"

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"


# ============================================================
# SUBJECT PERCENTAGE
# ============================================================

def calculate_subject_percentage(
    marks,
    max_marks
):

    try:
        marks = float(marks)
        max_marks = float(max_marks)
    except Exception:
        return np.nan

    if np.isnan(marks):
        return np.nan

    if np.isnan(max_marks) or max_marks <= 0:
        return np.nan

    return round(
        (marks / max_marks) * 100,
        2
    )


# ============================================================
# PROCESS SUBJECT DATA
# ============================================================

def calculate_subject_results(
    normalized_df,
    pass_percentage=40
):

    if normalized_df is None or normalized_df.empty:
        return pd.DataFrame()

    df = normalized_df.copy()

    percentages = []
    grades = []
    results = []

    for _, row in df.iterrows():

        status = str(
            row.get("Status", "Valid")
        ).strip()

        marks = row.get("Marks Obtained")
        max_marks = row.get("Max Marks")

        percentage = calculate_subject_percentage(
            marks,
            max_marks
        )

        if status.lower() == "absent":
            result = "FAIL"
            grade = "F"

        elif status.lower() in {
            "invalid",
            "missing"
        }:
            result = "FAIL"
            grade = "F"

        elif np.isnan(percentage):
            result = "FAIL"
            grade = "F"

        else:

            grade = calculate_grade(
                percentage
            )

            if percentage >= pass_percentage:
                result = "PASS"
            else:
                result = "FAIL"

        percentages.append(percentage)
        grades.append(grade)
        results.append(result)

    df["Percentage"] = percentages
    df["Grade"] = grades
    df["Result"] = results

    return df


# ============================================================
# STUDENT RESULTS
# ============================================================

def calculate_student_results(
    subject_data,
    pass_percentage=40
):

    if subject_data is None or subject_data.empty:
        return pd.DataFrame()

    students = []

    grouped = subject_data.groupby(
        ["Roll No", "Student Name"],
        dropna=False
    )

    for (roll, name), group in grouped:

        total_marks = 0.0
        total_max = 0.0

        subject_count = len(group)

        failed_subjects = 0
        absent_subjects = 0
        invalid_subjects = 0

        for _, row in group.iterrows():

            marks = row.get("Marks Obtained")
            max_marks = row.get("Max Marks")
            result = str(
                row.get("Result", "")
            ).upper()

            status = str(
                row.get("Status", "")
            ).lower()

            if status == "absent":
                absent_subjects += 1

            if status in {
                "invalid",
                "missing"
            }:
                invalid_subjects += 1

            if result == "FAIL":
                failed_subjects += 1

            if pd.notna(marks):
                try:
                    total_marks += float(marks)
                except Exception:
                    pass

            if pd.notna(max_marks):
                try:
                    total_max += float(max_marks)
                except Exception:
                    pass

        if total_max > 0:
            percentage = round(
                (total_marks / total_max) * 100,
                2
            )
        else:
            percentage = np.nan

        if failed_subjects > 0:
            overall_result = "FAIL"
        else:
            overall_result = "PASS"

        grade = calculate_grade(
            percentage
        )

        students.append({
            "Roll No": roll,
            "Student Name": name,
            "Subjects": subject_count,
            "Total Marks": round(total_marks, 2),
            "Maximum Marks": round(total_max, 2),
            "Percentage": percentage,
            "Grade": grade,
            "Result": overall_result,
            "Failed Subjects": failed_subjects,
            "Absent Subjects": absent_subjects,
            "Invalid Subjects": invalid_subjects
        })

    return pd.DataFrame(students)


def calculate_overall_result(
    student_results,
    pass_percentage=40
):

    if student_results is None:
        return pd.DataFrame()

    if student_results.empty:
        return student_results

    df = student_results.copy()

    def result_function(row):

        try:
            percentage = float(
                row["Percentage"]
            )
        except Exception:
            return "FAIL"

        if (
            row.get("Failed Subjects", 0) > 0
            or row.get("Absent Subjects", 0) > 0
            or row.get("Invalid Subjects", 0) > 0
        ):
            return "FAIL"

        if percentage >= pass_percentage:
            return "PASS"

        return "FAIL"

    df["Result"] = df.apply(
        result_function,
        axis=1
    )

    df["Grade"] = df["Percentage"].apply(
        calculate_grade
    )

    return df