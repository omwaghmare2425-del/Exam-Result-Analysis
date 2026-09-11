import io
import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from modules.validation import (
    clean_text,
    detect_columns,
    detect_format,
    normalize_result_data,
    find_duplicate_records
)

from modules.calculation import (
    calculate_subject_results,
    calculate_student_results,
    calculate_overall_result
)

from modules.ranking import (
    calculate_ranks,
    get_toppers
)

from modules.analysis import (
    class_analysis,
    grade_distribution,
    subject_analysis,
    low_performing_subjects
)

from modules.export import (
    create_excel_report
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Examination Result Processing & Analysis",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "📊 Examination Result Processing and Analysis System"
)

st.write(
    "Upload an Excel result sheet to validate, process, "
    "analyze and export examination results."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Settings")

pass_percentage = st.sidebar.number_input(
    "Pass Percentage",
    min_value=0.0,
    max_value=100.0,
    value=40.0,
    step=1.0
)

default_max_marks = st.sidebar.number_input(
    "Default Maximum Marks",
    min_value=1.0,
    max_value=10000.0,
    value=100.0,
    step=1.0
)

low_subject_threshold = st.sidebar.number_input(
    "Low Performing Subject Threshold (%)",
    min_value=0.0,
    max_value=100.0,
    value=50.0,
    step=1.0
)


# ============================================================
# DEVELOPER INFO
# ============================================================

with st.sidebar.expander("👨‍💻 Developer Information"):

    st.write("**Name:** Omkar Waghmare")
    st.write("**College:** CSMSS College of Engineering, Chh.Sambhaji Nagar")
    st.write("**Department:** Artificial Intelligence & Data Science")
    st.write("**Class:** TY-B")
    st.write("**Roll No:** AI3212")


# ============================================================
# SESSION STATE
# ============================================================

if "original_data" not in st.session_state:
    st.session_state.original_data = pd.DataFrame()

if "processed_data" not in st.session_state:
    st.session_state.processed_data = pd.DataFrame()

if "validation_errors" not in st.session_state:
    st.session_state.validation_errors = pd.DataFrame()

if "duplicates" not in st.session_state:
    st.session_state.duplicates = pd.DataFrame()

if "student_results" not in st.session_state:
    st.session_state.student_results = pd.DataFrame()

if "subject_results" not in st.session_state:
    st.session_state.subject_results = pd.DataFrame()

if "structure" not in st.session_state:
    st.session_state.structure = ""

if "columns" not in st.session_state:
    st.session_state.columns = {}


# ============================================================
# FILE UPLOAD
# ============================================================

st.header("1️⃣ Upload Excel File")

uploaded_file = st.file_uploader(
    "Select examination result Excel file",
    type=["xlsx", "xls"]
)


if uploaded_file is not None:


    file_bytes = uploaded_file.getvalue()

    if len(file_bytes) == 0:
        st.error("The uploaded file is empty.")
        st.stop()

    # ----------------------------------------------------
    # Read Excel file
    # ----------------------------------------------------

    try:

        excel_file = pd.ExcelFile(
            io.BytesIO(file_bytes)
        )

    except Exception as error:

        st.error(
            "Unable to read this Excel file."
        )

        st.info(
            f"Technical information: {error}"
        )

        st.stop()

    sheet_names = excel_file.sheet_names

    if not sheet_names:

        st.error(
            "No worksheet was found in the Excel file."
        )

        st.stop()

    st.success(
        f"Excel loaded successfully. "
        f"{len(sheet_names)} sheet(s) found."
    )

    # ----------------------------------------------------
    # Sheet selection
    # ----------------------------------------------------

    selected_sheet = st.selectbox(
        "Select worksheet",
        sheet_names
    )

    # ----------------------------------------------------
    # Header row
    # ----------------------------------------------------

    st.subheader("2️⃣ Excel Structure")

    raw_preview = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=selected_sheet,
        header=None,
        nrows=15
    )

    if raw_preview.empty:

        st.error(
            "The selected worksheet is empty."
        )

        st.stop()

    st.write(
        "Preview of the first rows:"
    )

    st.dataframe(
        raw_preview,
        use_container_width=True
    )

    # ----------------------------------------------------
    # Header row selection
    # ----------------------------------------------------

    header_options = list(
        range(
            1,
            min(
                15,
                len(raw_preview)
            ) + 1
        )
    )

    selected_header = st.selectbox(
        "Header row number",
        header_options,
        index=0,
        help=(
            "Choose the row containing column names. "
            "Usually it is row 1."
        )
    )

    header_index = selected_header - 1

    # ----------------------------------------------------
    # Read actual data
    # ----------------------------------------------------

    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=selected_sheet,
        header=header_index
    )

    # ----------------------------------------------------
    # Remove completely empty rows/columns
    # ----------------------------------------------------

    df = df.dropna(
        axis=0,
        how="all"
    )

    df = df.dropna(
        axis=1,
        how="all"
    )

    # ----------------------------------------------------
    # Clean duplicate column names
    # ----------------------------------------------------

    cleaned_columns = []

    used_names = {}

    for index, column in enumerate(df.columns):

        name = clean_text(column)

        if name == "":
            name = f"Column_{index + 1}"

        if name in used_names:

            used_names[name] += 1

            name = (
                f"{name}_{used_names[name]}"
            )

        else:

            used_names[name] = 0

        cleaned_columns.append(name)

    df.columns = cleaned_columns

    # ----------------------------------------------------
    # Empty check
    # ----------------------------------------------------

    if df.empty:

        st.error(
            "No usable data found in the selected worksheet."
        )

        st.stop()

    # ----------------------------------------------------
    # Original data
    # ----------------------------------------------------

    st.session_state.original_data = df.copy()

    st.success(
        f"Data loaded: {len(df)} rows × {len(df.columns)} columns"
    )

    with st.expander("👀 View Original Data"):

        st.dataframe(
            df,
            use_container_width=True
        )

    # ====================================================
    # DETECT COLUMNS
    # ====================================================

    columns = detect_columns(df)

    structure = detect_format(
        df,
        columns
    )

    st.session_state.columns = columns
    st.session_state.structure = structure

    st.subheader("3️⃣ Automatic Format Detection")

    col1, col2 = st.columns(2)

    with col1:

        if structure == "long":
            st.success("Format: Long Result Format")

        elif structure == "wide":
            st.success("Format: Wide Result Format")

        elif structure == "component":
            st.success("Format: Component Result Format")

        else:
            st.warning(
                "Format could not be automatically detected."
            )

    with col2:

        st.write(
            f"**Detected columns:** {columns}"
        )

    # ====================================================
    # MANUAL FORMAT OPTION
    # ====================================================

    if structure == "unknown":

        st.warning(
            "Please check the header row and column names."
        )

        st.info(
            "Supported common formats: "
            "Long, Wide and Component Result sheets."
        )

    # ====================================================
    # PROCESS BUTTON
    # ====================================================

    st.subheader("4️⃣ Process Result")

    process_button = st.button(
        "🚀 Process Result",
        type="primary",
        use_container_width=True
    )

    if process_button:

        with st.spinner(
            "Validating and processing Excel data..."
        ):

            try:

                (
                    processed_data,
                    validation_errors,
                    detected_columns,
                    detected_structure
                ) = normalize_result_data(
                    df,
                    default_max=float(
                        default_max_marks
                    )
                )

                # ------------------------------------------------
                # Duplicate detection
                # ------------------------------------------------

                duplicates = find_duplicate_records(
                    processed_data
                )

                # ------------------------------------------------
                # Remove exact duplicate result rows
                # ------------------------------------------------

                if (
                    processed_data is not None
                    and not processed_data.empty
                ):

                    processed_data = (
                        processed_data
                        .drop_duplicates(
                            subset=[
                                "Roll No",
                                "Student Name",
                                "Subject"
                            ],
                            keep="first"
                        )
                        .reset_index(drop=True)
                    )

                # ------------------------------------------------
                # Subject calculations
                # ------------------------------------------------

                subject_data = calculate_subject_results(
                    processed_data,
                    pass_percentage=float(
                        pass_percentage
                    )
                )

                # ------------------------------------------------
                # Student calculations
                # ------------------------------------------------

                student_results = (
                    calculate_student_results(
                        subject_data,
                        pass_percentage=float(
                            pass_percentage
                        )
                    )
                )

                student_results = (
                    calculate_overall_result(
                        student_results,
                        pass_percentage=float(
                            pass_percentage
                        )
                    )
                )

                # ------------------------------------------------
                # Ranking
                # ------------------------------------------------

                student_results = calculate_ranks(
                    student_results
                )

                # ------------------------------------------------
                # Store results
                # ------------------------------------------------

                st.session_state.processed_data = (
                    subject_data
                )

                st.session_state.validation_errors = (
                    validation_errors
                )

                st.session_state.duplicates = (
                    duplicates
                )

                st.session_state.student_results = (
                    student_results
                )

                st.session_state.subject_results = (
                    subject_analysis(
                        subject_data
                    )
                )

                st.session_state.columns = (
                    detected_columns
                )

                st.session_state.structure = (
                    detected_structure
                )

                st.success(
                    "✅ Result processing completed successfully!"
                )

            except Exception as error:

                st.error(
                    "The file could not be processed completely."
                )

                st.info(
                    "The application was protected from crashing. "
                    "Please check the selected header row and Excel structure."
                )

                st.code(
                    str(error)
                )


# ============================================================
# SHOW RESULTS ONLY AFTER PROCESSING
# ============================================================
if (
    not st.session_state.student_results.empty
    or not st.session_state.processed_data.empty
):
    # code
    pass

    # ========================================================
    # CLASS ANALYSIS
    # ========================================================

    st.header("📊 5️⃣ Class Analysis")

    summary = class_analysis(
        st.session_state.student_results,
        st.session_state.processed_data
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Total Students",
            summary["Total Students"]
        )

    with c2:
        st.metric(
            "Passed",
            summary["Passed Students"]
        )

    with c3:
        st.metric(
            "Failed",
            summary["Failed Students"]
        )

    with c4:
        st.metric(
            "Pass %",
            f'{summary["Pass Percentage"]}%'
        )

    c5, c6, c7 = st.columns(3)

    with c5:
        st.metric(
            "Class Average",
            f'{summary["Class Average"]}%'
        )

    with c6:
        st.metric(
            "Highest %",
            f'{summary["Highest Percentage"]}%'
        )

    with c7:
        st.metric(
            "Lowest %",
            f'{summary["Lowest Percentage"]}%'
        )

    # ========================================================
    # STUDENT RESULTS
    # ========================================================

    st.header("👨‍🎓 6️⃣ Student Results")

    student_display = (
        st.session_state.student_results.copy()
    )

    st.dataframe(
        student_display,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # TOPPERS
    # ========================================================

    st.subheader("🏆 Top 3 Toppers")

    toppers = get_toppers(
        st.session_state.student_results,
        count=3
    )

    if toppers.empty:

        st.info(
            "No topper data available."
        )

    else:

        st.dataframe(
            toppers,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # SUBJECT RESULTS
    # ========================================================

    st.header("📚 7️⃣ Subject-wise Analysis")

    subject_results = (
        st.session_state.subject_results
    )

    if subject_results.empty:

        st.info(
            "No subject analysis available."
        )

    else:

        st.dataframe(
            subject_results,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # LOW PERFORMING SUBJECTS
    # ========================================================

    st.subheader(
        "⚠️ Low Performing Subjects"
    )

    low_subjects = low_performing_subjects(
        subject_results,
        threshold=float(
            low_subject_threshold
        )
    )

    if low_subjects.empty:

        st.success(
            "No low-performing subjects found."
        )

    else:

        st.dataframe(
            low_subjects,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # GRADE DISTRIBUTION
    # ========================================================

    st.header("📈 8️⃣ Grade Distribution")

    grade_data = grade_distribution(
        st.session_state.student_results
    )

    if not grade_data.empty:

        fig, ax = plt.subplots(
            figsize=(8, 4)
        )

        ax.bar(
            grade_data["Grade"],
            grade_data["Students"]
        )

        ax.set_title(
            "Grade Distribution"
        )

        ax.set_xlabel(
            "Grade"
        )

        ax.set_ylabel(
            "Number of Students"
        )

        ax.grid(
            axis="y",
            alpha=0.2
        )

        st.pyplot(
            fig,
            clear_figure=True
        )

        plt.close(fig)

    # ========================================================
    # SUBJECT PERFORMANCE CHART
    # ========================================================

    st.header(
        "📊 9️⃣ Subject Performance"
    )

    if (
        not subject_results.empty
        and "Average Percentage"
        in subject_results.columns
    ):

        chart_data = (
            subject_results[
                [
                    "Subject",
                    "Average Percentage"
                ]
            ]
            .copy()
        )

        chart_data = chart_data.dropna()

        if not chart_data.empty:

            fig, ax = plt.subplots(
                figsize=(10, 5)
            )

            ax.bar(
                chart_data["Subject"].astype(str),
                chart_data["Average Percentage"]
            )

            ax.set_title(
                "Average Subject Performance"
            )

            ax.set_xlabel(
                "Subject"
            )

            ax.set_ylabel(
                "Average Percentage"
            )

            ax.tick_params(
                axis="x",
                rotation=45
            )

            ax.grid(
                axis="y",
                alpha=0.2
            )

            plt.tight_layout()

            st.pyplot(
                fig,
                clear_figure=True
            )

            plt.close(fig)

    # ========================================================
    # PROCESSED DATA
    # ========================================================

    st.header(
        "📋 🔟 Processed Subject Data"
    )

    st.dataframe(
        st.session_state.processed_data,
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # VALIDATION REPORT
    # ========================================================

    st.header(
        "🔍 1️⃣1️⃣ Validation Report"
    )

    errors = (
        st.session_state.validation_errors
    )

    if errors.empty:

        st.success(
            "✅ No validation errors found."
        )

    else:

        st.warning(
            f"{len(errors)} validation issue(s) found."
        )

        st.dataframe(
            errors,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # DUPLICATE REPORT
    # ========================================================

    st.header(
        "♻️ 1️⃣2️⃣ Duplicate Records"
    )

    duplicates = (
        st.session_state.duplicates
    )

    if duplicates.empty:

        st.success(
            "✅ No duplicate Roll No + Subject records found."
        )

    else:

        st.warning(
            f"{len(duplicates)} duplicate record(s) found."
        )

        st.dataframe(
            duplicates,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # EXPORT
    # ========================================================

    st.header(
        "📥 1️⃣3️⃣ Export Final Report"
    )

    report_file = create_excel_report(
        st.session_state.original_data,
        st.session_state.processed_data,
        st.session_state.student_results,
        st.session_state.subject_results,
        st.session_state.validation_errors,
        st.session_state.duplicates
    )

    st.download_button(
        label="📥 Download Final Excel Report",
        data=report_file.getvalue(),
        file_name="Examination_Result_Final_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Examination Result Processing and Analysis System | "
    "Developed by Omkar Waghmare | AI & Data Science"
)
