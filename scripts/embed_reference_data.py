from pgvector.psycopg2 import register_vector
from pathlib import Path
import argparse
import os
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create embeddings and store them in PostgreSQL."
    )

    parser.add_argument("--input", type=Path, required=True, default=Path("data/processed/job_titles_cleaned.csv"))
    parser.add_argument("--column", type=str, required=True, default="job_title")
    parser.add_argument(
        "--item-type",
        choices=["title", "skill"],
        required=True,
        default="title",
    )
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


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def embed_reference_data(input_path: Path, column: str, item_type: str, model: str, batch_size: int):
    df = pd.read_csv(input_path)

    if column not in df.columns:
        raise ValueError(
            f"Column not found: {column}"
        )

    texts = (
        df[column]
        .dropna()
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    texts_to_list = texts.tolist() if hasattr(texts, "tolist") else list(texts)
    transformer_model = SentenceTransformer(model)

    embeddings = transformer_model.encode(
        texts_to_list, batch_size=batch_size, show_progress_bar=True
    )

    conn = get_connection()
    register_vector(conn)  

    try:
        with conn.cursor() as cursor:
            data_to_insert = [
                (text, embedding.tolist(), item_type, model)
                for text, embedding in zip(texts_to_list, embeddings)
            ]

            cursor.executemany(
                """
                INSERT INTO reference_embeddings (text, embedding, item_type, model_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (text, item_type, model_name) DO NOTHING
                """,
                data_to_insert
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
if __name__ == "__main__":
    args = parse_args()

    embed_reference_data(
        input_path=args.input,
        column=args.column,
        item_type=args.item_type,
        model=args.model,
        batch_size=args.batch_size,
    )