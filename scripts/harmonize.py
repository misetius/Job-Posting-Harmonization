import csv
import re
from pgvector.psycopg2 import register_vector
from pathlib import Path
import argparse
import os
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
from pgvector import Vector
import requests
import uuid


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"
DISTANCE_THRESHOLD = 0.10


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create embeddings and store them in PostgreSQL."
    )

    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--salary-column", type=str, default="salary")
    parser.add_argument("--description-column", type=str, default="description")
    parser.add_argument("--title-column", type=str,  default="title")
    parser.add_argument("--json-or-csv", type=str, choices=["json", "csv"], default="json")
    parser.add_argument(
        "--model",
        type=str,
        default="multi-qa-MiniLM-L6-cos-v1",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=128,
    )

    return parser.parse_args()


def generate_phrases(description) -> list[str]:
    words = re.findall(r"\b[\w+#.-]+\b", description.lower())

    phrases = set()

    for n in range(1, 4):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n]).strip()
            if phrase:
                phrases.add(phrase)

    return sorted(phrases)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )

def ask_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["message"]["content"]

def harmonize_reference_data(input_path: Path, description_column: str, title_column: str, json_or_csv: str = "json", model: str = "multi-qa-MiniLM-L6-cos-v1", batch_size: int = 128):
    if json_or_csv == "json":
        df = pd.read_json(input_path)
    else:
        df = pd.read_csv(input_path)

    df = df.rename(
        columns={
            description_column: "description",
            title_column: "title"
        }
    )

    df_in_list = df.to_dict(orient="records")

    con = get_connection()
    register_vector(con)
    transformer_model = SentenceTransformer(model)
    

    try:
        for row in df_in_list:
            description = row.get("description")
            title = row.get("title")

            if not isinstance(title, str) or not title.strip():
                continue

            if not isinstance(description, str) or not description.strip():
                continue

            title_embedding = transformer_model.encode(
            title.strip(),
            normalize_embeddings=True,
            )

            unique_job_id = uuid.uuid4()

            embedding_vector = Vector(title_embedding.tolist())

            reference_rows = None

            with con.cursor() as cur:
                cur.execute(
                """
                SELECT
                    id,
                    text,
                    embedding <=> %s AS distance
                FROM reference_embeddings
                WHERE item_type = 'title'
                  AND model_name = %s
                ORDER BY embedding <=> %s
                LIMIT 10
                """,
                (
                    embedding_vector,
                    model,
                    embedding_vector,
                ),
            )

                reference_rows = cur.fetchall()

            harmonized_title = None

            print(f"Reference rows for title '{title}':")
            for ref_id, reference_title, distance in reference_rows:
                print(f"ID: {ref_id}, Title: {reference_title}, Distance: {distance:.4f}")

            prompt = f"""Choose the most appropriate canonical job title for the following job title: '{title}' from these options: {', '.join([row[1] for row in reference_rows])}. Do not make up any titles or use the raw title. 
            The description of the job is: '{description}'.
            return only the chosen job title without any additional text or explanation. The canonical job title should be one of the options provided. If none of the options are appropriate, return 'No suitable title found'."""
            harmonized_title = ask_ollama(prompt)
            print(f"Harmonized title from Ollama: {harmonized_title}")

            

            words = generate_phrases(description)
            harmonised_skills = set()

            for phrase in words:

                print(f"Processing phrase: '{phrase}'")
        
                if not isinstance(phrase, str) or not phrase.strip():
                    continue


                skill_rows = csv.reader(open("data/processed/skills_cleaned.csv", "r"))

                skill_rows_to_list = list(skill_rows)

                skills_lower = [row[0].lower() for row in skill_rows_to_list]

                if phrase.lower() in skills_lower:
                    print(f"Found exact match for skill: '{phrase}'")
                    harmonised_skills.add(phrase)
                    continue
            
                
                
            with con.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO harmonized_jobs (job_id, raw_title, raw_description, canonical_title, model_name)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (job_id) DO NOTHING
                    """,
                    (str(unique_job_id), title, description, harmonized_title, model),
                )
                for skill in harmonised_skills:
                    cur.execute(
                        """
                        INSERT INTO harmonized_job_skills (job_id, skill)
                        VALUES (%s, %s)
                        ON CONFLICT (job_id, skill) DO NOTHING
                        """,
                        (str(unique_job_id), skill),
                    )
                con.commit()
    except Exception as e:
        con.rollback()
        raise e

                 
    finally:
        con.close()

if __name__ == "__main__":
    args = parse_args()
    harmonize_reference_data(
        input_path=args.input,
        salary_column=args.salary_column,
        description_column=args.description_column,
        title_column=args.title_column,
        json_or_csv=args.json_or_csv,
        model=args.model,
        batch_size=args.batch_size
    )










