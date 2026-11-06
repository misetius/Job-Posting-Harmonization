from pathlib import Path
import argparse

import pandas as pd

def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare job titles for vector search."
    )

    parser.add_argument("--input", type=Path, required=True, default=Path("data/raw/job_titles.csv"))
    parser.add_argument("--output", type=Path, required=True, default=Path("data/processed/job_titles_cleaned.csv"))
    parser.add_argument("--title-column", type=str, required=True, default="job_title")

    return parser.parse_args()


def prepare_job_titles(input_path: Path, output_path: Path, title_column: str):
    df = pd.read_csv(input_path)

    print(f"Loaded rows: {len(df):,}")

    if title_column not in df.columns:
        raise ValueError(
            f"Column not found: {title_column}"
        )

    df = df.rename(
        columns={
            title_column: "job_title"
        }
    )

    df["job_title"] = (
        df["job_title"]
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    df = df[
        df["job_title"].notna()
        & df["job_title"].ne("")
    ].copy()

    df = df.drop_duplicates(
        subset=["job_title"]
    ).reset_index(drop=True)

    print(f"After cleaning: {len(df):,}")

    df = df[["job_title"]]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print()
    print("Done!")
    print(f"Output: {output_path}")
    print(f"Rows:   {len(df):,}")


if __name__ == "__main__":
    args = parse_args()
    prepare_job_titles(
        input_path=args.input,
        output_path=args.output,
        title_column=args.title_column
    )