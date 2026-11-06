from pathlib import Path
import argparse

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare skills for vector search."
    )

    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skill-column", type=str, required=True)

    return parser.parse_args()


def prepare_skills(input_path: Path, output_path: Path, skill_column: str):

    if not input_path.exists():
        args = parse_args()
        input_path = args.input
        output_path = args.output
        skill_column = args.skill_column


    df = pd.read_csv(input_path)

    print(f"Loaded rows: {len(df):,}")

    if skill_column not in df.columns:
        raise ValueError(
            f"Column not found: {skill_column}"
        )

    df = df.rename(
        columns={
            skill_column: "skill"
        }
    )

    df["skill"] = (
        df["skill"]
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    df = df[
        df["skill"].notna()
        & df["skill"].ne("")
    ].copy()

    df = df.drop_duplicates(
        subset=["skill"]
    ).reset_index(drop=True)

    print(f"After cleaning: {len(df):,}")

    df = df[["skill"]]

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
    prepare_skills(
        input_path=args.input,
        output_path=args.output,
        skill_column=args.skill_column
    )