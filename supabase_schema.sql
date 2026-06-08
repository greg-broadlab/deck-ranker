-- Deck Ranker Schema
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS decks (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    category TEXT NOT NULL,
    elo INTEGER DEFAULT 1000,
    matches INTEGER DEFAULT 0,
    slide_count INTEGER DEFAULT 0,
    cloudinary_prefix TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comparisons (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category TEXT NOT NULL,
    winner_id TEXT NOT NULL,
    loser_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Allow public read/write (internal tool)
ALTER TABLE decks ENABLE ROW LEVEL SECURITY;
ALTER TABLE comparisons ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_decks" ON decks FOR SELECT USING (true);
CREATE POLICY "public_insert_decks" ON decks FOR INSERT WITH CHECK (true);
CREATE POLICY "public_update_decks" ON decks FOR UPDATE USING (true);
CREATE POLICY "public_read_comparisons" ON comparisons FOR SELECT USING (true);
CREATE POLICY "public_insert_comparisons" ON comparisons FOR INSERT WITH CHECK (true);
