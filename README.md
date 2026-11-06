# IT Job Posting Harmonization

A Python-based data engineering project that cleans IT job-title and skill reference data, creates 384-dimensional text embeddings, stores them in PostgreSQL, and processes job postings using semantic search and a locally hosted large language model (LLM).

The project uses `multi-qa-MiniLM-L6-cos-v1` as its default embedding model, PostgreSQL with `pgvector` for vector similarity search, and Ollama with `llama3.1:8b` for job-title harmonization.

## Table of Contents

- [Project Overview](#project-overview)
- [Project Goals](#project-goals)
- [Project Scripts](#project-scripts)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Database Design](#database-design)
- [Example Data Visualization](#example-data-visualization)
- [Installation and Setup](#installation-and-setup)
- [Environment Configuration](#environment-configuration)
- [How to Run](#how-to-run)
- [How the Pipeline Works](#how-the-pipeline-works)
- [Vector Similarity and Thresholds](#vector-similarity-and-thresholds)



## Project Overview

IT job postings use inconsistent job titles and skill descriptions. Similar roles may be advertised under different titles, making it difficult to compare vacancies or analyze labor-market data consistently.

This project creates a processing pipeline that:

1. Cleans and deduplicates job-title and skill reference data.
2. Generates 384-dimensional embeddings for reference titles and skills.
3. Stores the reference text and vectors in PostgreSQL.
4. Loads job postings from CSV or JSON files.
5. Retrieves similar reference titles and skills using `pgvector`.
6. Uses Ollama to select a canonical job title from retrieved title candidates.
7. Matches phrases from job descriptions to standardized reference skills.

**Current design:** the LLM is used for job-title harmonization. Skills are matched through embedding similarity and a distance threshold, not by asking the LLM to harmonize them.

## Project Goals

- Build a repeatable data preparation and harmonization pipeline.
- Standardize job titles against a reference list.
- Map job-description phrases to a controlled list of skills.
- Use semantic vector search to find relevant reference entries.
- Run LLM-based title selection locally through Ollama.
- Store embeddings in PostgreSQL so they can be reused across runs.
- Reduce embedding storage and computation by using 384-dimensional vectors.

## Project Results

### Review process

One hundred harmonized job titles have been randomly chosen from the postgres database ordering by the randomly generated UUID. I decided to focus on harmonized titles since in these LLM is used for picking
the right answer. In cases where there were some ambiguity I also reviewed the raw description for the job posting.

### Results

This is developing process. I am currently trying to enhance the LLM models ability to 

#### 1. Without giving description to the LLM

Without giving description to the LLM 65/100 titles could be said to be harmonized in a right way. I am quite sure that this can be improved by giving job posting description to the LLM with the vector calculated titles. The prompt itself can also be improved most likely.






## Project Scripts

The code shared for this project consists of four scripts. The filenames below are descriptive; use the actual filenames in your repository.

| Script / function | Responsibility | Input | Output |
|---|---|---|---|
| `prepare_job_titles.py` / `prepare_job_titles()` | Cleans job titles, removes blanks and duplicates | CSV file and title column | Cleaned CSV with `job_title` |
| `prepare_skills.py` / `prepare_skills()` | Cleans skill reference values and removes duplicates | CSV file and skill column | Cleaned CSV with `skill` |
| `embed_reference_data.py` / `embed_reference_data()` | Embeds reference titles or skills and inserts them into PostgreSQL | Cleaned CSV, column, item type and model | Rows in `reference_embeddings` |
| `harmonize_reference_data.py` / `harmonize_reference_data()` | Processes postings, selects a canonical title with Ollama, and matches skills by vector search | CSV or JSON job-posting file | Console output with title and skill matches |

 
## How to run

The easiest way to use the program is to keep the input files, output files, and column names at their default values. The default settings are:

- Job titles input: `data/raw/job_titles.csv`
- Job titles output: `data/processed/job_titles_cleaned.csv`
- Job title column: `job_title`
- Skills input: `data/raw/software_skills.csv`
- Skills output: `data/processed/skills_cleaned.csv`
- Skill column: `skill`
- Job postings input: `jobs.json`
- Salary column: `salary`
- Description column: `description`
- Title column: `title`
- Input format: `json`
- Embedding model: `multi-qa-MiniLM-L6-cos-v1`
- Batch size: `128`

Using these default values allows the program to run without specifying additional command-line arguments. If different file paths or column names are needed, they can be overridden using the corresponding arguments.



## Architecture

```text
Reference data
     |
     +------------------------------+
     |                              |
     v                              v
Prepare job titles             Prepare skills
     |                              |
     v                              v
Clean and deduplicate          Clean and deduplicate
     |                              |
     +---------------+--------------+
                     |
                     v
            Generate embeddings
        multi-qa-MiniLM-L6-cos-v1
                     |
                     v
              PostgreSQL
             + pgvector
                     ^
                     |
Incoming job postings (CSV / JSON)
                     |
                     v
             Validate each row
                     |
          +----------+-----------+
          |                      |
          v                      v
       Job title             Description
          |                      |
          v                      v
      Create vector        Extract 1–3 token phrases
          |                      |
          v                      v
   Retrieve top 5 titles   Retrieve nearest skill
          |                      |
          v                      v
   Ollama selects title    Apply distance threshold
          |                      |
          +----------+-----------+
                     |
                     v
             Print results
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Pipeline logic and orchestration |
| pandas | CSV and JSON data handling |
| Sentence Transformers | Embedding generation |
| `multi-qa-MiniLM-L6-cos-v1` | Default 384-dimensional embedding model |
| PostgreSQL | Persistent storage |
| pgvector | Vector similarity search |
| psycopg2 | PostgreSQL connectivity |
| Ollama | Local LLM inference |
| `llama3.1:8b` | Default Ollama chat model |
| Docker Compose | Optional container management |

## Requirements

- Python version compatible with the installed dependencies.
- PostgreSQL with the pgvector extension installed.
- A 384-dimensional embedding model compatible with Sentence Transformers.
- Reference title and skill CSV files.
- An input job-posting CSV or JSON file.
- A populated `reference_embeddings` table before running harmonization.

## Database Design

The reference embedding table stores both job titles and skills. The `item_type` column separates these record types.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE reference_embeddings (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    item_type TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (item_type IN ('title', 'skill')),
    UNIQUE (text, item_type, model_name)
);

CREATE INDEX idx_reference_embeddings_vector
ON reference_embeddings
USING hnsw (embedding vector_cosine_ops);
```

### Columns

| Column | Description |
|---|---|
| `id` | Unique identifier |
| `text` | Reference title or skill |
| `item_type` | `title` or `skill` |
| `embedding` | 384-dimensional embedding vector |
| `model_name` | Model used to create the embedding |
| `created_at` | Record creation timestamp |

The unique constraint prevents duplicate reference text for the same item type and model. Duplicate inserts are ignored by the embedding script.

### Vector retrieval

The harmonization script retrieves the five closest title references:

```sql
SELECT
    id,
    text,
    embedding <=> %s AS distance
FROM reference_embeddings
WHERE item_type = 'title'
  AND model_name = %s
ORDER BY embedding <=> %s
LIMIT 5;
```

For skills, the same approach is used with `item_type = 'skill'` and `LIMIT 1`.

The `<=>` operator represents cosine distance when used with `vector_cosine_ops`. A lower distance means the vectors are closer. A distance value is not a calibrated confidence probability.

**Important:** The database column dimension, embedding model output, and all stored/query vectors must agree. If the table was created with `VECTOR(1024)`, changing this README will not migrate the database. Recreate or migrate the column and regenerate embeddings if moving to 384 dimensions.

## Example Data Visualization

## How the Pipeline Works

### Embedding reference data

The embedding script:

1. Reads the selected CSV column.
2. Removes missing values, normalizes whitespace, and trims text.
3. Loads the configured Sentence Transformers model.
4. Generates embeddings in batches.
5. Inserts the text, vector, item type, and model name.
6. Skips duplicates through the unique constraint.

The default model, `multi-qa-MiniLM-L6-cos-v1`, produces 384-dimensional embeddings, matching `VECTOR(384)`.

### Job-title harmonization

For each posting with a valid title and description, the current script:

1. Embeds the title.
2. Retrieves up to five reference titles with the same `model_name`.
3. Prints the candidates and their distances.
4. Sends the candidates and incoming title to Ollama.
5. Prints the returned canonical title.

Although the script defines `DISTANCE_THRESHOLD = 0.10`, the shared version currently calls Ollama for every title and does not use the threshold in the title-selection decision. The threshold is used for skill matching.

### Skill matching

The current `generate_phrases()` function:

1. Converts the description to lowercase.
2. Tokenizes it with a regular expression.
3. Creates unique one-, two-, and three-token phrases.
4. Embeds each phrase.
5. Retrieves the nearest reference skill.
6. Adds the skill to a set when its distance is below `DISTANCE_THRESHOLD`.

Using a set prevents duplicate matched skill names in the collected results for a posting.

This simple phrase-generation approach can produce many phrases, including phrases that do not represent actual skills. Its quality and performance should be evaluated for the dataset.

## Vector Similarity and Thresholds

The harmonization script currently defines:

```python
DISTANCE_THRESHOLD = 0.10
```

This threshold controls which skill matches are accepted. It is a project parameter, not a universal cutoff. Tune it against manually reviewed examples.

Potential improvements include:

- Use separate thresholds for title retrieval and skill matching.
- Compare automatic matches with a manually labeled evaluation set.
- Track the number of unmatched phrases and accepted skill matches.
- Avoid treating distance as a probability or guaranteed measure of correctness.



