import io
import pandas as pd


def safe_dataframe(df):
    """
    Always returns a DataFrame.
    """

    if df is None:
        return pd.DataFrame()

    if isinstance(df, pd.DataFrame):
        return df

    return pd.DataFrame(df)


def create_excel_report(
    original_data,
    processed_data,
    student_results,
    subject_results,
    validation_errors,
    duplicates
):

    output = io.BytesIO()

    original_data = safe_dataframe(
        original_data
    )

    processed_data = safe_dataframe(
        processed_data
    )

    student_results = safe_dataframe(
        student_results
    )

    subject_results = safe_dataframe(
        subject_results
    )

    validation_errors = safe_dataframe(
        validation_errors
    )

    duplicates = safe_dataframe(
        duplicates
    )

    try:

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            original_data.to_excel(
                writer,
                sheet_name="Original Data",
                index=False
            )

            processed_data.to_excel(
                writer,
                sheet_name="Processed Marks",
                index=False
            )

            student_results.to_excel(
                writer,
                sheet_name="Student Results",
                index=False
            )

            subject_results.to_excel(
                writer,
                sheet_name="Subject Analysis",
                index=False
            )

            validation_errors.to_excel(
                writer,
                sheet_name="Validation Errors",
                index=False
            )

            duplicates.to_excel(
                writer,
                sheet_name="Duplicates",
                index=False
            )

        output.seek(0)

        return output

    except Exception as error:

        # Return a simple report even if one sheet has a problem
        fallback = io.BytesIO()

        with pd.ExcelWriter(
            fallback,
            engine="openpyxl"
        ) as writer:

            pd.DataFrame({
                "Message": [
                    "Report generation encountered an issue.",
                    str(error)
                ]
            }).to_excel(
                writer,
                sheet_name="Report Error",
                index=False
            )

        fallback.seek(0)

        return fallback