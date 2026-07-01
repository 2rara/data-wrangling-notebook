import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    I'm a long distance runner in my personal life, and in 2019, I ran the Reykjavik Marathon.

    I was aiming to run it in under 3 hours (known as "sub-3"), but I failed and ended up being a sub-4 runner for the marathon.
    I was on a good pace even after the half point, but somewhere around 30k, I got cramps and lost speed.
    As a tendency, do sub-3 runners maintain the same-level speed all the way through?
    Or do they also have a slower pace after around the same point as I did? I'd love to check in order to become a stronger runner with some insights!
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In the Reykjavik Marathon, split times are recorded at 29.4k. Let's check if the average running pace (seconds/km) is significantly different before and after this point.

    - **Null Hypothesis 1 ($H_0$):** The difference between the average running pace before and after 29.4k among sub-3 runners is zero.
    - **Alternative Hypothesis 1 ($H_1$):** The average running pace before and after 29.4k among sub-3 runners is different.
    - $\alpha$: 0.05

    - **Null Hypothesis 2 ($H_0$):** The difference between the average running pace before and after 29.4k among sub-4 runners is zero.
    - **Alternative Hypothesis 2 ($H_1$):** The average running pace before and after 29.4k among sub-4 runners is different.
    - $\alpha$: 0.05
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data loading
    """)
    return


@app.cell
def _():
    import pandas as pd
    import polars as pl
    import plotly.express as px
    import numpy as np
    from scipy import stats

    url = 'https://timataka.net/reykjavikurmarathon2019/urslit/?race=1&cat=overall' # Results from Reykjavik Marathon 2019
    table = pd.read_html(url)[0]
    df = pl.from_pandas(table)

    print(df)
    return df, pl, px, stats


@app.cell
def _(df, pl):
    # Extract the sub-3 and sub-4 runners only
    target_runners = df.filter(
        pl.col("Time") < "04:00:00"
    )

    print(target_runners)
    return (target_runners,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data cleansing
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    It looks from the race result page that a few runners missed some internal records. I would like to omit rows with such data to compare records on the same ground. The correct number of intermediate results in this case is 6 (5 km, 10km, 16.4 km, 21.1km, 29.4 km, 38 km). I will use the regular expression ```\([0-9]*\skm\)| \([0-9]*,[0-9]*\skm\``` to omit the "(x km)" parts. It will split each record in "Split" 6 times, which will make the number of elements 7, with a space at the end.
    """)
    return


@app.cell
def _(pl, target_runners):
    REGEX = r" \([0-9]+(?:,[0-9]+)?\skm\)"

    cleansed_df = (
        target_runners
        .with_columns(
            pl.col("Split")
            .str.replace_all(REGEX, "|")
            .str.split("|")
            .alias("splits")
        )
        .filter(
            pl.col("splits").list.len() == 7
        )
    )

    print(cleansed_df)
    return (cleansed_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now I'm ready to put split times and finish times into a table.
    """)
    return


@app.cell
def _(cleansed_df, pl):
    name = ['5k', '10k', '16.4k', '21.1k', '29.4k', '38k']

    # 1. Standardize and parse splits & Chiptime in a single, atomic operation
    parsed_splits_df = cleansed_df.select([
        pl.col("splits").list.eval(
            (pl.element()
             .replace("", None)
             .str.to_time("%H:%M:%S")
             .cast(pl.Int64) // 1_000_000_000)
        ),
        (pl.col("Chiptime")
         .replace("", None)
         .str.to_time("%H:%M:%S")
         .cast(pl.Int64) // 1_000_000_000)
         .alias("42.195k")
    ])

    # 2. Flatten the list into individual named split columns
    runners_df = parsed_splits_df.with_columns([
        pl.col("splits").list.get(i).alias(name[i]) for i in range(len(name))
    ]).drop("splits")

    print(runners_df)
    return (runners_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Comparison of sub-3 runners and sub-4 runners
    """)
    return


@app.cell
def _(pl, runners_df):
    # Split the tables for走力別 (Sub-3 vs Sub-4)
    sub_three_df = runners_df.filter(pl.col("42.195k") < 3 * 60 * 60)

    sub_four_df = runners_df.filter(
        (pl.col("42.195k") >= 3 * 60 * 60) & (pl.col("42.195k") < 4 * 60 * 60)
    )
    return sub_four_df, sub_three_df


@app.cell
def _(px, sub_three_df):
    # Define the exact chronological order of the splits
    split_order = ['5k', '10k', '16.4k', '21.1k', '29.4k', '38k', '42.195k']

    fig_sub_three = px.box(
        sub_three_df.to_pandas(), 
        title="Sub-3 Runners Pace Distribution",
        points="outliers",
        category_orders={"variable": split_order}  # This forces the chronological sequence
    )
    fig_sub_three
    return (split_order,)


@app.cell
def _(px, split_order, sub_four_df):
    fig_sub_four = px.box(
        sub_four_df.to_pandas(), 
        title="Sub-4 Runners Pace Distribution",
        points="outliers",
        category_orders={"variable": split_order}
    )
    fig_sub_four
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both groups slow down, the variance (the vertical spread/outliers) in the Sub-4 group after 29.4k is much wider, indicating catastrophic pacing breakdowns compared to the more controlled, tighter deceleration seen in Sub-3 runners.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    From here, I'm going to refer to the 29.4k point as the pace separator because it's my point of interest in this study.
    """)
    return


@app.cell
def _(pl, sub_three_df):
    sub_three_before = sub_three_df.select(pl.col("29.4k") / 29.4).to_series()

    sub_three_after = sub_three_df.select(
        (pl.col("42.195k") - pl.col("29.4k")) / (42.195 - 29.4)
    ).to_series()
    return sub_three_after, sub_three_before


@app.cell
def _(pl, sub_four_df):
    sub_four_before = sub_four_df.select(pl.col("29.4k") / 29.4).to_series()

    sub_four_after = sub_four_df.select(
        (pl.col("42.195k") - pl.col("29.4k")) / (42.195 - 29.4)
    ).to_series()
    return sub_four_after, sub_four_before


@app.cell
def _(stats, sub_three_after, sub_three_before):
    # Execute t-test for Sub-3 group (from scipy.stats imported in cell 4)
    res_sub3 = stats.ttest_rel(sub_three_before, sub_three_after)
    res_sub3
    return


@app.cell
def _(stats, sub_four_after, sub_four_before):
    # Execute t-test for Sub-4 group
    res_sub4 = stats.ttest_rel(sub_four_before, sub_four_after)
    res_sub4
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Conclusion
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both cases yield extremely small p-values ($p < 0.01$). Since $p < \alpha$, we reject both Null Hypothesis 1 and Null Hypothesis 2 at a 99% confidence level.

    ***Conclusion: The average running pace changes significantly before and after the 29.4k mark for both sub-3 and sub-4 runners.***
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Average paces
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nonetheless, even with a slower average pace over the final kilometers, sub-3 runners still manage to complete the full marathon under 3 hours. How fast did the sub-3 runners from the Reykjavik Marathon 2019 actually run?
    """)
    return


@app.cell
def _(pl):
    def minute_per_km(series: pl.Series) -> str:
        mean_seconds = series.mean()
        if mean_seconds is None:
            return "N/A"

        minutes = int(mean_seconds // 60)
        seconds = int(round(mean_seconds % 60))

        if seconds == 60:
            minutes += 1
            seconds = 0

        return f"{minutes}:{seconds:02d} min/km"

    return (minute_per_km,)


@app.cell
def _(minute_per_km, sub_three_before):
    minute_per_km(sub_three_before) # Incredible!
    return


@app.cell
def _(minute_per_km, sub_three_after):
    minute_per_km(sub_three_after) # Wow, still very fast!
    return


@app.cell
def _(minute_per_km, sub_four_before):
    minute_per_km(sub_four_before) # Not too bad!
    return


@app.cell
def _(minute_per_km, sub_four_after):
    minute_per_km(sub_four_after) # well, we might have slowed down, but we didn't give up!
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
