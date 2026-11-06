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

CREATE TABLE harmonized_jobs (
    job_id TEXT PRIMARY KEY,
    raw_title TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    canonical_title TEXT NOT NULL,
    model_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() 
);

CREATE TABLE harmonized_job_skills (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL
        REFERENCES harmonized_jobs(job_id)
        ON DELETE CASCADE,
    skill TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  
    UNIQUE (job_id, skill)
);

CREATE INDEX idx_harmonized_job_skills_job_id
ON harmonized_job_skills(job_id);

CREATE INDEX idx_harmonized_job_skills_reference
ON harmonized_job_skills(reference_item_id);