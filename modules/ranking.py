import pandas as pd


def calculate_ranks(student_results):

    if student_results is None:
        return pd.DataFrame()

    if student_results.empty:
        return student_results

    df = student_results.copy()

    if "Percentage" not in df.columns:
        df["Rank"] = pd.NA
        return df

    # Sort by percentage
    df = df.sort_values(
        by="Percentage",
        ascending=False,
        na_position="last"
    ).reset_index(drop=True)

    # Only PASS students can get rank
    ranks = []
    current_rank = 0
    previous_percentage = None

    for index, row in df.iterrows():

        result = str(
            row.get("Result", "")
        ).upper()

        percentage = row.get(
            "Percentage"
        )

        if result != "PASS" or pd.isna(percentage):

            ranks.append(pd.NA)
            continue

        if previous_percentage != percentage:
            current_rank = index + 1
            previous_percentage = percentage

        ranks.append(current_rank)

    df["Rank"] = ranks

    return df


def get_toppers(
    ranked_students,
    count=3
):

    if ranked_students is None:
        return pd.DataFrame()

    if ranked_students.empty:
        return ranked_students

    toppers = ranked_students[
        ranked_students["Result"]
        .astype(str)
        .str.upper()
        == "PASS"
    ].copy()

    toppers = toppers[
        pd.notna(toppers["Rank"])
    ]

    toppers = toppers.sort_values(
        by=["Rank", "Percentage"],
        ascending=[True, False]
    )

    return toppers.head(count)