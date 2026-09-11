import re
import numpy as np
import pandas as pd


# ============================================================
# BASIC CLEANING FUNCTIONS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def normalize_text(value):
    text = clean_text(value)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def is_blank(value):
    text = normalize_text(value)

    return text in {
        "",
        "nan",
        "none",
        "null",
        "-"
    }


def is_absent(value):
    text = normalize_text(value)

    return text in {
        "ab",
        "a",
        "abs",
        "absent",
        "aa",
        "not present",
        "notpresent"
    }


def is_excel_error(value):
    text = normalize_text(value)

    errors = {
        "#num!",
        "#value!",
        "#n/a",
        "#ref!",
        "#div/0!",
        "#name?",
        "#null!",
        "#spill!",
        "#calc!"
    }

    return text in errors


def to_number(value):
    """
    Safely converts value into numeric value.

    Returns:
        float -> valid number
        np.nan -> invalid / blank / absent / Excel error
    """

    if value is None:
        return np.nan

    try:
        if pd.isna(value):
            return np.nan
    except Exception:
        pass

    if is_absent(value):
        return np.nan

    if is_excel_error(value):
        return np.nan

    text = clean_text(value)

    if text == "":
        return np.nan

    # Remove common formatting characters
    text = text.replace(",", "")
    text = text.replace("%", "")

    try:
        return float(text)
    except Exception:
        return np.nan


# ============================================================
# COLUMN DETECTION
# ============================================================

ROLL_KEYWORDS = [
    "roll",
    "roll no",
    "rollno",
    "roll number",
    "rollnumber",
    "student id",
    "studentid",
    "enrollment",
    "enrollment no",
    "enrollment number",
    "registration",
    "registration no",
    "reg no",
    "seat no",
    "seat number"
]

NAME_KEYWORDS = [
    "student name",
    "studentname",
    "name",
    "student"
]

SUBJECT_KEYWORDS = [
    "subject",
    "subject name",
    "subjectname",
    "course",
    "course name",
    "paper",
    "paper name"
]

MARK_KEYWORDS = [
    "marks",
    "mark",
    "marks obtained",
    "marksobtained",
    "obtained marks",
    "score",
    "obtained",
    "result"
]

MAX_KEYWORDS = [
    "max marks",
    "maximum marks",
    "maximum",
    "max",
    "out of",
    "outof",
    "total marks",
    "full marks"
]


def find_column(columns, keywords):
    """
    Finds the best matching column.
    """

    normalized_columns = {
        col: normalize_text(col)
        for col in columns
    }

    # Exact match first
    for col, norm in normalized_columns.items():
        for keyword in keywords:
            if norm == normalize_text(keyword):
                return col

    # Partial match second
    for col, norm in normalized_columns.items():
        for keyword in keywords:
            key = normalize_text(keyword)

            if key in norm:
                return col

    return None


def detect_columns(df):
    """
    Detects common student/result columns.
    """

    columns = list(df.columns)

    roll_col = find_column(columns, ROLL_KEYWORDS)
    name_col = find_column(columns, NAME_KEYWORDS)
    subject_col = find_column(columns, SUBJECT_KEYWORDS)
    marks_col = find_column(columns, MARK_KEYWORDS)
    max_col = find_column(columns, MAX_KEYWORDS)

    return {
        "roll": roll_col,
        "name": name_col,
        "subject": subject_col,
        "marks": marks_col,
        "max": max_col
    }


# ============================================================
# COMPONENT DETECTION
# ============================================================

COMPONENT_KEYWORDS = [
    "ct",
    "ct1",
    "ct2",
    "ct-i",
    "ct-ii",
    "ct i",
    "ct ii",
    "assignment",
    "assign",
    "mse",
    "mse exam",
    "ca",
    "ese",
    "theory",
    "practical",
    "internal",
    "external",
    "term work",
    "tw",
    "oral",
    "viva"
]

EXCLUDE_MARK_KEYWORDS = [
    "roll",
    "name",
    "student",
    "id",
    "enrollment",
    "registration",
    "division",
    "class",
    "branch",
    "semester",
    "year",
    "attendance",
    "present",
    "absent",
    "serial",
    "sr no",
    "srno",
    "number",
    "rank",
    "grade",
    "percentage",
    "result",
    "status"
]


def is_component_column(column_name):
    text = normalize_text(column_name)

    for keyword in COMPONENT_KEYWORDS:
        if normalize_text(keyword) in text:
            return True

    return False


def is_excluded_mark_column(column_name):
    text = normalize_text(column_name)

    for keyword in EXCLUDE_MARK_KEYWORDS:
        if normalize_text(keyword) in text:
            return True

    return False


def detect_mark_columns(df):
    """
    Detects possible subject/mark columns in wide-format files.
    """

    mark_columns = []

    for column in df.columns:

        if is_excluded_mark_column(column):
            continue

        if is_component_column(column):
            continue

        series = df[column]

        numeric_count = 0
        valid_count = 0

        for value in series:

            if is_blank(value):
                continue

            if is_absent(value):
                valid_count += 1
                continue

            if is_excel_error(value):
                continue

            number = to_number(value)

            if not np.isnan(number):
                numeric_count += 1
                valid_count += 1

        if valid_count > 0 and numeric_count > 0:
            mark_columns.append(column)

    return mark_columns


# ============================================================
# STRUCTURE DETECTION
# ============================================================

def detect_format(df, columns):
    """
    Detects:
        long
        component
        wide
        unknown
    """

    roll = columns.get("roll")
    name = columns.get("name")
    subject = columns.get("subject")
    marks = columns.get("marks")

    has_student = roll is not None or name is not None
    has_subject = subject is not None
    has_marks = marks is not None

    component_columns = [
        col for col in df.columns
        if is_component_column(col)
    ]

    # Long format
    if has_student and has_subject and has_marks:
        if component_columns:
            return "component"

        return "long"

    # Component format
    if has_student and has_subject and component_columns:
        return "component"

    # Wide format
    if has_student:
        mark_columns = detect_mark_columns(df)

        if len(mark_columns) > 0:
            return "wide"

    return "unknown"


# ============================================================
# MAXIMUM MARKS
# ============================================================

def extract_max_from_column_name(column_name):
    """
    Supports:
        Maths (100)
        Maths - 100
        Maths [100]
        Maths / 100
    """

    text = clean_text(column_name)

    patterns = [
        r"\(\s*(\d+(?:\.\d+)?)\s*\)",
        r"\[\s*(\d+(?:\.\d+)?)\s*\]",
        r"/\s*(\d+(?:\.\d+)?)",
        r"-\s*(\d+(?:\.\d+)?)$",
        r"out\s*of\s*(\d+(?:\.\d+)?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            try:
                return float(match.group(1))
            except Exception:
                pass

    return np.nan


def get_max_marks(row, max_column, default_max):
    """
    Gets maximum marks safely.
    """

    if max_column is not None:
        value = to_number(row.get(max_column))

        if not np.isnan(value) and value > 0:
            return value

    return float(default_max)


# ============================================================
# NORMALIZED DATA
# ============================================================

def create_empty_normalized():
    return pd.DataFrame(
        columns=[
            "Roll No",
            "Student Name",
            "Subject",
            "Marks Obtained",
            "Max Marks",
            "Status",
            "Source Row"
        ]
    )


def normalize_long_data(df, columns, default_max):
    """
    Converts long-format data into standard format.
    """

    result = []
    errors = []

    roll_col = columns.get("roll")
    name_col = columns.get("name")
    subject_col = columns.get("subject")
    marks_col = columns.get("marks")
    max_col = columns.get("max")

    for index, row in df.iterrows():

        excel_row = index + 2

        roll = clean_text(row.get(roll_col)) if roll_col else ""
        name = clean_text(row.get(name_col)) if name_col else ""
        subject = clean_text(row.get(subject_col)) if subject_col else ""

        raw_marks = row.get(marks_col) if marks_col else None

        max_marks = get_max_marks(
            row,
            max_col,
            default_max
        )

        status = "Valid"
        marks = np.nan

        if roll == "" and name == "":
            continue

        if roll == "":
            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Student ID",
                "Column": roll_col or "Roll No",
                "Value": "",
                "Message": "Student roll/enrollment number is missing."
            })

        if name == "":
            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Student Name",
                "Column": name_col or "Student Name",
                "Value": "",
                "Message": "Student name is missing."
            })

        if subject == "":
            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Subject",
                "Column": subject_col or "Subject",
                "Value": "",
                "Message": "Subject name is missing."
            })

        if is_absent(raw_marks):

            status = "Absent"

            errors.append({
                "Source Row": excel_row,
                "Error Type": "Absent",
                "Column": marks_col or "Marks",
                "Value": clean_text(raw_marks),
                "Message": "Student is marked absent."
            })

        elif is_excel_error(raw_marks):

            status = "Invalid"

            errors.append({
                "Source Row": excel_row,
                "Error Type": "Excel Error",
                "Column": marks_col or "Marks",
                "Value": clean_text(raw_marks),
                "Message": "Excel contains an error value."
            })

        elif is_blank(raw_marks):

            status = "Missing"

            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Marks",
                "Column": marks_col or "Marks",
                "Value": "",
                "Message": "Marks are missing."
            })

        else:

            marks = to_number(raw_marks)

            if np.isnan(marks):

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Invalid Marks",
                    "Column": marks_col or "Marks",
                    "Value": clean_text(raw_marks),
                    "Message": "Marks are not numeric."
                })

            elif marks < 0:

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Negative Marks",
                    "Column": marks_col or "Marks",
                    "Value": marks,
                    "Message": "Marks cannot be negative."
                })

            elif marks > max_marks:

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Marks Above Maximum",
                    "Column": marks_col or "Marks",
                    "Value": marks,
                    "Message": f"Marks cannot be greater than {max_marks}."
                })

        result.append({
            "Roll No": roll,
            "Student Name": name,
            "Subject": subject,
            "Marks Obtained": marks,
            "Max Marks": max_marks,
            "Status": status,
            "Source Row": excel_row
        })

    return (
        pd.DataFrame(result),
        pd.DataFrame(errors)
    )


# ============================================================
# COMPONENT FORMAT
# ============================================================

def normalize_component_data(df, columns, default_max):
    """
    Handles sheets like:

    Roll No | Name | Subject | CT-I | CT-II | Assignment | MSE | CA | TOTAL
    """

    result = []
    errors = []

    roll_col = columns.get("roll")
    name_col = columns.get("name")
    subject_col = columns.get("subject")
    max_col = columns.get("max")

    total_col = None

    for col in df.columns:

        text = normalize_text(col)

        if text in {
            "total",
            "total marks",
            "marks total",
            "grand total"
        }:
            total_col = col
            break

    component_columns = []

    for col in df.columns:

        if col in {
            roll_col,
            name_col,
            subject_col,
            max_col,
            total_col
        }:
            continue

        if is_component_column(col):
            component_columns.append(col)

    for index, row in df.iterrows():

        excel_row = index + 2

        roll = clean_text(row.get(roll_col)) if roll_col else ""
        name = clean_text(row.get(name_col)) if name_col else ""
        subject = clean_text(row.get(subject_col)) if subject_col else ""

        if roll == "" and name == "":
            continue

        total_raw = row.get(total_col) if total_col else None

        # ----------------------------------------------------
        # If TOTAL exists and is valid, use TOTAL
        # ----------------------------------------------------

        marks = np.nan
        status = "Valid"

        if total_col is not None:

            if is_absent(total_raw):

                status = "Absent"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Absent",
                    "Column": total_col,
                    "Value": clean_text(total_raw),
                    "Message": "Student is absent."
                })

            elif is_excel_error(total_raw):

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Excel Error",
                    "Column": total_col,
                    "Value": clean_text(total_raw),
                    "Message": "TOTAL contains an Excel error."
                })

            elif not is_blank(total_raw):

                marks = to_number(total_raw)

        # ----------------------------------------------------
        # If TOTAL is missing/invalid, calculate from components
        # ----------------------------------------------------

        if np.isnan(marks):

            component_values = []

            has_absent = False
            has_invalid = False

            for col in component_columns:

                raw_value = row.get(col)

                if is_absent(raw_value):
                    has_absent = True
                    continue

                if is_excel_error(raw_value):
                    has_invalid = True
                    continue

                if is_blank(raw_value):
                    continue

                number = to_number(raw_value)

                if not np.isnan(number):
                    component_values.append(number)
                else:
                    has_invalid = True

            if component_values:
                marks = sum(component_values)

            if has_absent and not component_values:
                status = "Absent"

            elif has_invalid and not component_values:
                status = "Invalid"

            elif not component_values:
                status = "Missing"

        max_marks = get_max_marks(
            row,
            max_col,
            default_max
        )

        if not np.isnan(marks):

            if marks < 0:

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Negative Marks",
                    "Column": total_col or "Calculated Total",
                    "Value": marks,
                    "Message": "Marks cannot be negative."
                })

            elif marks > max_marks:

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Marks Above Maximum",
                    "Column": total_col or "Calculated Total",
                    "Value": marks,
                    "Message": f"Marks cannot be greater than {max_marks}."
                })

        result.append({
            "Roll No": roll,
            "Student Name": name,
            "Subject": subject,
            "Marks Obtained": marks,
            "Max Marks": max_marks,
            "Status": status,
            "Source Row": excel_row
        })

    return (
        pd.DataFrame(result),
        pd.DataFrame(errors)
    )


# ============================================================
# WIDE FORMAT
# ============================================================

def normalize_wide_data(df, columns, default_max):
    """
    Handles:

    Roll No | Student Name | Python | DBMS | AI | ML
    """

    result = []
    errors = []

    roll_col = columns.get("roll")
    name_col = columns.get("name")

    mark_columns = detect_mark_columns(df)

    for index, row in df.iterrows():

        excel_row = index + 2

        roll = clean_text(row.get(roll_col)) if roll_col else ""
        name = clean_text(row.get(name_col)) if name_col else ""

        if roll == "" and name == "":
            continue

        if roll == "":
            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Student ID",
                "Column": roll_col or "Roll No",
                "Value": "",
                "Message": "Student roll/enrollment number is missing."
            })

        if name == "":
            errors.append({
                "Source Row": excel_row,
                "Error Type": "Missing Student Name",
                "Column": name_col or "Student Name",
                "Value": "",
                "Message": "Student name is missing."
            })

        for subject_col in mark_columns:

            raw_marks = row.get(subject_col)

            max_from_header = extract_max_from_column_name(
                subject_col
            )

            if np.isnan(max_from_header):
                max_marks = float(default_max)
            else:
                max_marks = float(max_from_header)

            marks = np.nan
            status = "Valid"

            if is_absent(raw_marks):

                status = "Absent"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Absent",
                    "Column": subject_col,
                    "Value": clean_text(raw_marks),
                    "Message": "Student is absent."
                })

            elif is_excel_error(raw_marks):

                status = "Invalid"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Excel Error",
                    "Column": subject_col,
                    "Value": clean_text(raw_marks),
                    "Message": "Excel contains an error value."
                })

            elif is_blank(raw_marks):

                status = "Missing"

                errors.append({
                    "Source Row": excel_row,
                    "Error Type": "Missing Marks",
                    "Column": subject_col,
                    "Value": "",
                    "Message": "Marks are missing."
                })

            else:

                marks = to_number(raw_marks)

                if np.isnan(marks):

                    status = "Invalid"

                    errors.append({
                        "Source Row": excel_row,
                        "Error Type": "Invalid Marks",
                        "Column": subject_col,
                        "Value": clean_text(raw_marks),
                        "Message": "Marks are not numeric."
                    })

                elif marks < 0:

                    status = "Invalid"

                    errors.append({
                        "Source Row": excel_row,
                        "Error Type": "Negative Marks",
                        "Column": subject_col,
                        "Value": marks,
                        "Message": "Marks cannot be negative."
                    })

                elif marks > max_marks:

                    status = "Invalid"

                    errors.append({
                        "Source Row": excel_row,
                        "Error Type": "Marks Above Maximum",
                        "Column": subject_col,
                        "Value": marks,
                        "Message": f"Marks cannot be greater than {max_marks}."
                    })

            result.append({
                "Roll No": roll,
                "Student Name": name,
                "Subject": clean_text(subject_col),
                "Marks Obtained": marks,
                "Max Marks": max_marks,
                "Status": status,
                "Source Row": excel_row
            })

    return (
        pd.DataFrame(result),
        pd.DataFrame(errors)
    )


# ============================================================
# MAIN NORMALIZATION FUNCTION
# ============================================================

def normalize_result_data(df, default_max=100):
    """
    Main function.

    Automatically detects Excel structure and converts it
    into a standard result format.
    """

    if df is None:
        return (
            create_empty_normalized(),
            pd.DataFrame(),
            {},
            "unknown"
        )

    if df.empty:
        return (
            create_empty_normalized(),
            pd.DataFrame(),
            {},
            "unknown"
        )

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all").copy()

    # Clean column names
    new_columns = []

    for index, column in enumerate(df.columns):

        name = clean_text(column)

        if name == "":
            name = f"Column_{index + 1}"

        new_columns.append(name)

    df.columns = new_columns

    columns = detect_columns(df)

    structure = detect_format(
        df,
        columns
    )

    if structure == "long":

        normalized, errors = normalize_long_data(
            df,
            columns,
            default_max
        )

    elif structure == "component":

        normalized, errors = normalize_component_data(
            df,
            columns,
            default_max
        )

    elif structure == "wide":

        normalized, errors = normalize_wide_data(
            df,
            columns,
            default_max
        )

    else:

        normalized = create_empty_normalized()

        errors = pd.DataFrame([
            {
                "Source Row": "",
                "Error Type": "Unknown Format",
                "Column": "",
                "Value": "",
                "Message": (
                    "Could not automatically detect a result format. "
                    "Expected Roll/Name with subject and marks information."
                )
            }
        ])

    return (
        normalized,
        errors,
        columns,
        structure
    )


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def find_duplicate_records(normalized_df):

    if normalized_df is None or normalized_df.empty:
        return pd.DataFrame()

    required = [
        "Roll No",
        "Subject"
    ]

    for col in required:
        if col not in normalized_df.columns:
            return pd.DataFrame()

    temp = normalized_df.copy()

    temp["_roll"] = temp["Roll No"].astype(str).str.strip().str.lower()
    temp["_subject"] = temp["Subject"].astype(str).str.strip().str.lower()

    duplicate_mask = temp.duplicated(
        subset=["_roll", "_subject"],
        keep=False
    )

    duplicates = temp.loc[
        duplicate_mask
    ].copy()

    if duplicates.empty:
        return pd.DataFrame()

    duplicates.drop(
        columns=["_roll", "_subject"],
        inplace=True,
        errors="ignore"
    )

    return duplicates


# ============================================================
# LEGACY VALIDATION FUNCTIONS
# ============================================================

def validate_long_data(df, columns, default_max=100):
    return normalize_long_data(
        df,
        columns,
        default_max
    )


def validate_wide_data(df, columns, default_max=100):
    return normalize_wide_data(
        df,
        columns,
        default_max
    )