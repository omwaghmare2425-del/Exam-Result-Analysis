import numpy as np
import pandas as pd


# ============================================================
# CLASS ANALYSIS
# ============================================================

def class_analysis(
    student_results,
    subject_data
):

    if student_results is None:
        student_results = pd.DataFrame()

    if subject_data is None:
        subject_data = pd.DataFrame()

    total_students = len(student_results)

    if total_students == 0:
        return {
            "Total Students": 0,
            "Passed Students": 0,
            "Failed Students": 0,
            "Pass Percentage": 0,
            "Class Average": 0,
            "Highest Percentage": 0,
            "Lowest Percentage": 0
        }

    passed = (
        student_results["Result"]
        .astype(str)
        .str.upper()
        .eq("PASS")
        .sum()
    )

    failed = total_students - passed

    pass_percentage = round(
        (passed / total_students) * 100,
        2
    )

    percentage_series = pd.to_numeric(
        student_results["Percentage"],
        errors="coerce"
    )

    class_average = round(
        percentage_series.mean(),
        2
    ) if percentage_series.notna().any() else 0

    highest = round(
        percentage_series.max(),
        2
    ) if percentage_series.notna().any() else 0

    lowest = round(
        percentage_series.min(),
        2
    ) if percentage_series.notna().any() else 0

    return {
        "Total Students": total_students,
        "Passed Students": int(passed),
        "Failed Students": int(failed),
        "Pass Percentage": pass_percentage,
        "Class Average": class_average,
        "Highest Percentage": highest,
        "Lowest Percentage": lowest
    }


# ============================================================
# GRADE DISTRIBUTION
# ============================================================

def grade_distribution(student_results):

    grades = [
        "A+",
        "A",
        "B+",
        "B",
        "C",
        "D",
        "F"
    ]

    if (
        student_results is None
        or student_results.empty
        or "Grade" not in student_results.columns
    ):
        return pd.DataFrame({
            "Grade": grades,
            "Students": [0] * len(grades)
        })

    counts = (
        student_results["Grade"]
        .value_counts()
        .reindex(
            grades,
            fill_value=0
        )
    )

    return pd.DataFrame({
        "Grade": grades,
        "Students": counts.values
    })


# ============================================================
# SUBJECT ANALYSIS
# ============================================================

def subject_analysis(subject_data):

    if subject_data is None or subject_data.empty:
        return pd.DataFrame()

    records = []

    grouped = subject_data.groupby(
        "Subject",
        dropna=False
    )

    for subject, group in grouped:

        total_students = len(group)

        passed = (
            group["Result"]
            .astype(str)
            .str.upper()
            .eq("PASS")
            .sum()
        )

        failed = total_students - passed

        pass_rate = round(
            (passed / total_students) * 100,
            2
        ) if total_students > 0 else 0

        percentages = pd.to_numeric(
            group["Percentage"],
            errors="coerce"
        )

        average = (
            round(percentages.mean(), 2)
            if percentages.notna().any()
            else 0
        )

        highest = (
            round(percentages.max(), 2)
            if percentages.notna().any()
            else 0
        )

        lowest = (
            round(percentages.min(), 2)
            if percentages.notna().any()
            else 0
        )

        records.append({
            "Subject": str(subject),
            "Students": total_students,
            "Passed": int(passed),
            "Failed": int(failed),
            "Pass Percentage": pass_rate,
            "Average Percentage": average,
            "Highest Percentage": highest,
            "Lowest Percentage": lowest
        })

    return pd.DataFrame(records)


# ============================================================
# LOW PERFORMING SUBJECTS
# ============================================================

def low_performing_subjects(
    subject_results,
    threshold=50
):

    if subject_results is None:
        return pd.DataFrame()

    if subject_results.empty:
        return subject_results

    if "Pass Percentage" not in subject_results.columns:
        return pd.DataFrame()

    result = subject_results[
        subject_results["Pass Percentage"]
        < threshold
    ].copy()

    return result.sort_values(
        by="Pass Percentage",
        ascending=True
    ).reset_index(drop=True)