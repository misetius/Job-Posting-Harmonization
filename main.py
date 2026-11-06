from pathlib import Path
import subprocess
import pandas as pd
import time
import argparse
from scripts.prepare_job_titles import prepare_job_titles
from scripts.prepare_skills import prepare_skills
from scripts.embed_reference_data import embed_reference_data
from scripts.harmonize import harmonize_reference_data


def parse_args():

    parser = argparse.ArgumentParser(
        description="Prepare and embed job titles and skills."
    )

    parser.add_argument("--job-titles-input", type=Path, default="data/raw/job_titles.csv")
    parser.add_argument("--job-titles-output", type=Path, default="data/processed/job_titles_cleaned.csv")
    parser.add_argument("--job-title-column", type=str, default="job_title")

    parser.add_argument("--skills-input", type=Path, default="data/raw/software_skills.csv")
    parser.add_argument("--skills-output", type=Path, default="data/processed/skills_cleaned.csv")
    parser.add_argument("--skill-column", type=str, default="skill")

    parser.add_argument("--model", type=str, default="multi-qa-MiniLM-L6-cos-v1")
    parser.add_argument("--batch-size", type=int, default=128)

    parser.add_argument("--job-postings-input", type=Path, default="jobs.json")
    parser.add_argument("--salary-column", type=str, default="salary")
    parser.add_argument("--description-column", type=str, default="description")
    parser.add_argument("--title-column", type=str,  default="title")
    parser.add_argument("--json-or-csv", type=str, choices=["json", "csv"], default="json")

    return parser.parse_args()

def main(args):



    # Prepare job titles
    prepare_job_titles(
        input_path=args.job_titles_input,
        output_path=args.job_titles_output,
        title_column=args.job_title_column
    )
    print(f"Job titles prepared and saved to {args.job_titles_output}")

    # Prepare skills
    prepare_skills(
        input_path=args.skills_input,
        output_path=args.skills_output,
        skill_column=args.skill_column
    )
    print(f"Skills prepared and saved to {args.skills_output}")

    subprocess.run(["docker-compose", "up", "-d", "postgres"])

    time.sleep(5)  # Wait for PostgreSQL to start

    # Embed job titles
    embed_reference_data(
        input_path=args.job_titles_output,
        column=args.job_title_column,
        item_type="title",
        model=args.model,
        batch_size=args.batch_size
    )

    # Embed skills
    embed_reference_data(
        input_path=args.skills_output,
        column=args.skill_column,
        item_type="skill",
        model=args.model,
        batch_size=args.batch_size
    )

    subprocess.run(
        ["docker-compose", "up", "-d", "ollama"],
        check=True,
    )

    subprocess.run(
        ["docker", "exec", "jobs-ollama", "ollama", "pull", "llama3.1:8b"],
        check=True,
    )

    # Harmonize reference data
    harmonize_reference_data(
        input_path=args.job_postings_input,
        description_column=args.description_column,
        title_column=args.title_column,
        json_or_csv=args.json_or_csv,
        model=args.model,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    args = parse_args()
    main(args)
    


