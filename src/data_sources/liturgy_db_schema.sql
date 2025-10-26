-- Liturgical Librarian Database Schema
-- Phase 1: Comprehensive liturgical corpus with phrase-level indexing
-- Created: 2025-10-26

-- ============================================================================
-- Table: prayers
-- Stores complete text of all liturgical sources from Sefaria
-- ============================================================================
CREATE TABLE IF NOT EXISTS prayers (
    prayer_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Source identification
    source_text TEXT NOT NULL,        -- 'Siddur_Ashkenaz', 'Machzor_Rosh_Hashanah_Edot_HaMizrach'
    sefaria_ref TEXT NOT NULL UNIQUE, -- Full Sefaria reference (e.g., "Siddur Ashkenaz, Weekday, Shacharit, Pesukei Dezimrah, Ashrei 1")

    -- Classification
    nusach TEXT NOT NULL,             -- 'Ashkenaz', 'Sefard', 'Edot_HaMizrach'
    prayer_type TEXT NOT NULL,        -- 'Siddur', 'Machzor', 'Haggadah', etc.
    occasion TEXT,                    -- 'Weekday', 'Shabbat', 'Rosh_Hashanah', 'Yom_Kippur', etc.
    service TEXT,                     -- 'Shacharit', 'Mincha', 'Maariv', 'Musaf', 'Neilah'
    section TEXT,                     -- 'Pesukei_DZimrah', 'Amidah', 'Tachanun', 'Hallel', etc.

    -- Content
    prayer_name TEXT,                 -- 'Ashrei', 'Kaddish', 'Aleinu', etc.
    hebrew_text TEXT NOT NULL,
    english_text TEXT,

    -- Context
    sequence_order INTEGER,           -- Order within service
    liturgical_notes TEXT,            -- Additional context

    -- Metadata
    created_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prayers_nusach ON prayers(nusach);
CREATE INDEX IF NOT EXISTS idx_prayers_occasion_service ON prayers(occasion, service);
CREATE INDEX IF NOT EXISTS idx_prayers_section ON prayers(section);
CREATE INDEX IF NOT EXISTS idx_prayers_sefaria_ref ON prayers(sefaria_ref);

-- ============================================================================
-- Table: psalms_liturgy_index
-- Pre-computed index of all Psalms references in liturgy (phrase-level)
-- ============================================================================
CREATE TABLE IF NOT EXISTS psalms_liturgy_index (
    index_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Psalms reference
    psalm_chapter INTEGER NOT NULL,
    psalm_verse_start INTEGER,        -- NULL for chapter-level or phrase-level
    psalm_verse_end INTEGER,          -- NULL if single verse or phrase
    psalm_phrase_hebrew TEXT,         -- Exact Hebrew phrase matched
    psalm_phrase_normalized TEXT,     -- Level 2 normalization for searching
    phrase_length INTEGER,            -- Word count (2-10+)

    -- Liturgy reference
    prayer_id INTEGER NOT NULL,
    liturgy_phrase_hebrew TEXT,       -- The matching text from liturgy
    liturgy_context TEXT,             -- Surrounding text (±20 words)

    -- Match metadata
    match_type TEXT NOT NULL,         -- 'exact_verse', 'exact_chapter', 'exact_phrase', 'near_phrase', 'likely_influence'
    normalization_level INTEGER,      -- 0=exact, 1=voweled, 2=consonantal, 3=lemma
    confidence REAL NOT NULL,         -- 0.0 to 1.0
    distinctiveness_score REAL,       -- TF-IDF or frequency-based score

    -- Manual curation
    manually_verified BOOLEAN DEFAULT 0,
    curator_notes TEXT,

    -- Metadata
    indexed_date TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(prayer_id) REFERENCES prayers(prayer_id)
);

CREATE INDEX IF NOT EXISTS idx_index_psalm_ref ON psalms_liturgy_index(psalm_chapter, psalm_verse_start);
CREATE INDEX IF NOT EXISTS idx_index_match_type ON psalms_liturgy_index(match_type);
CREATE INDEX IF NOT EXISTS idx_index_confidence ON psalms_liturgy_index(confidence);
CREATE INDEX IF NOT EXISTS idx_index_prayer_id ON psalms_liturgy_index(prayer_id);

-- ============================================================================
-- Table: liturgical_metadata
-- Rich contextual information about services, occasions, and traditions
-- ============================================================================
CREATE TABLE IF NOT EXISTS liturgical_metadata (
    metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,

    category TEXT NOT NULL,           -- 'service', 'occasion', 'section', 'nusach'
    key TEXT NOT NULL,                -- e.g., 'Shacharit', 'Pesukei_DZimrah'

    display_name_english TEXT,        -- 'Morning Service', 'Verses of Praise'
    display_name_hebrew TEXT,         -- 'שחרית', 'פסוקי דזמרה'
    description TEXT,                 -- Detailed explanation
    typical_timing TEXT,              -- 'Daily', 'Sabbath and Holidays', etc.

    UNIQUE(category, key)
);

CREATE INDEX IF NOT EXISTS idx_metadata_category ON liturgical_metadata(category);

-- ============================================================================
-- Table: harvest_log
-- Track corpus building progress and errors
-- ============================================================================
CREATE TABLE IF NOT EXISTS harvest_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_text TEXT NOT NULL,
    sefaria_ref TEXT,
    status TEXT NOT NULL,             -- 'success', 'failed', 'skipped'
    error_message TEXT,
    harvest_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_log_status ON harvest_log(status);
CREATE INDEX IF NOT EXISTS idx_log_source ON harvest_log(source_text);

-- ============================================================================
-- Table: phrase_cache
-- Cache phrase distinctiveness scores to avoid recomputation
-- ============================================================================
CREATE TABLE IF NOT EXISTS phrase_cache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_normalized TEXT NOT NULL UNIQUE,  -- Level 2 normalized phrase
    word_count INTEGER NOT NULL,
    corpus_frequency INTEGER NOT NULL,       -- Occurrences in Tanakh
    distinctiveness_score REAL NOT NULL,     -- TF-IDF score
    is_searchable BOOLEAN NOT NULL,          -- Meets threshold for searching
    computed_date TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_phrase ON phrase_cache(phrase_normalized);
CREATE INDEX IF NOT EXISTS idx_cache_searchable ON phrase_cache(is_searchable);
