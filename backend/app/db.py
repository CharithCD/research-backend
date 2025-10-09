from __future__ import annotations
import os, json, datetime as dt, hashlib
from pathlib import Path
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text, bindparam, Row
from sqlalchemy.dialects.postgresql import JSONB

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///app/data/app.db")

def _is_pg() -> bool:
    return DATABASE_URL.startswith("postgresql+asyncpg://")

def _ensure_sqlite_dir():
    # Expected format: sqlite+aiosqlite:///absolute/path/to/file.db
    if DATABASE_URL.startswith("sqlite"):
        parts = DATABASE_URL.split(":///")[1]
        if len(parts) == 2:
            db_path = Path(parts[1])          # e.g. /app/data/app.db
            db_path.parent.mkdir(parents=True, exist_ok=True)

if not _is_pg():
    _ensure_sqlite_dir()

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS phoneme_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  audio_sha256 TEXT NOT NULL,
  ref_text TEXT,
  pred_phones TEXT NOT NULL,         -- JSON string
  ref_phones TEXT,                   -- JSON string
  ops_raw TEXT,                      -- JSON string
  per_strict REAL,
  per_sle REAL,
  wer REAL,
  word_analysis TEXT,              -- JSON string
  weakness_categories TEXT,        -- JSON string
  created_at TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS grammar_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  input_text TEXT NOT NULL,
  raw_corrected TEXT NOT NULL,
  final_text TEXT NOT NULL,
  edits TEXT,                        -- JSON string
  guardrails TEXT,                   -- JSON string
  latency_ms INTEGER,
  weakness_categories TEXT,        -- JSON string
  created_at TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS user_analytics_cache (
  user_id              VARCHAR(64) PRIMARY KEY,
  window_label         VARCHAR(16) NOT NULL DEFAULT '7d',
  from_ts              TIMESTAMP,
  to_ts                TIMESTAMP,
  attempts_phoneme     INT NOT NULL DEFAULT 0,
  attempts_grammar     INT NOT NULL DEFAULT 0,
  per_sle_avg          REAL,
  per_sle_median       REAL,
  edits_per_100w_avg   REAL,
  latency_ms_p50       INT,
  top_phone_subs       TEXT,      -- JSON
  top_grammar_weaknesses   TEXT,      -- JSON
  top_pronunciation_weaknesses TEXT, -- JSON
  badge                VARCHAR(64),
  headline_msg         TEXT,
  updated_at           TIMESTAMP NOT NULL,
  expires_at           TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_analytics_cache_expires ON user_analytics_cache (expires_at);
"""

DDL_PG = """
CREATE TABLE IF NOT EXISTS phoneme_results (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  audio_sha256 TEXT NOT NULL,
  ref_text TEXT,
  pred_phones JSONB NOT NULL,
  ref_phones JSONB,
  ops_raw JSONB,
  per_strict DOUBLE PRECISION,
  per_sle DOUBLE PRECISION,
  wer DOUBLE PRECISION,
  word_analysis JSONB,
  weakness_categories JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS grammar_results (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  input_text TEXT NOT NULL,
  raw_corrected TEXT NOT NULL,
  final_text TEXT NOT NULL,
  edits JSONB,
  guardrails JSONB,
  latency_ms INTEGER,
  weakness_categories JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS user_analytics_cache (
  user_id              VARCHAR(64) PRIMARY KEY,
  window_label         VARCHAR(16) NOT NULL DEFAULT '7d',
  from_ts              TIMESTAMPTZ,
  to_ts                TIMESTAMPTZ,
  attempts_phoneme     INT NOT NULL DEFAULT 0,
  attempts_grammar     INT NOT NULL DEFAULT 0,
  per_sle_avg          NUMERIC(6,2),
  per_sle_median       NUMERIC(6,2),
  edits_per_100w_avg   NUMERIC(6,2),
  latency_ms_p50       INT,
  top_phone_subs       JSONB,
  top_grammar_weaknesses   JSONB,
  top_pronunciation_weaknesses JSONB,
  badge                VARCHAR(64),
  headline_msg         TEXT,
  updated_at           TIMESTAMPTZ NOT NULL,
  expires_at           TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_analytics_cache_expires ON user_analytics_cache (expires_at);
"""

def _is_pg() -> bool:
    return DATABASE_URL.startswith("postgresql+asyncpg://")

async def init_db():
    ddl = DDL_PG if _is_pg() else DDL_SQLITE
    async with engine.begin() as conn:
        # split on semicolons, execute non-empty statements
        for stmt in filter(None, (s.strip() for s in ddl.split(";"))):
            await conn.execute(text(stmt))

    # --- Add new columns if they don't exist (idempotent migration) ---
    async with engine.begin() as conn:
        alter_commands = [
            # phoneme_results
            "ALTER TABLE phoneme_results ADD COLUMN wer REAL",
            "ALTER TABLE phoneme_results ADD COLUMN word_analysis TEXT",
            "ALTER TABLE phoneme_results ADD COLUMN weakness_categories TEXT",
            # grammar_results
            "ALTER TABLE grammar_results ADD COLUMN weakness_categories TEXT",
        ]
        if _is_pg():
            alter_commands = [
                "ALTER TABLE phoneme_results ADD COLUMN wer DOUBLE PRECISION",
                "ALTER TABLE phoneme_results ADD COLUMN word_analysis JSONB",
                "ALTER TABLE phoneme_results ADD COLUMN weakness_categories JSONB",
                "ALTER TABLE grammar_results ADD COLUMN weakness_categories JSONB",
            ]

        for cmd in alter_commands:
            try:
                await conn.execute(text(cmd))
            except Exception as e:
                # Typically "column ... already exists", which is fine
                if "already exists" not in str(e) and "duplicate column name" not in str(e):
                    print(f"[DB-MIGRATE-WARN] Alter command failed: {cmd} | {e}")

async def save_phoneme_result(user_id: str, audio_bytes: bytes, result: Dict[str, Any]):
    audio_sha = hashlib.sha256(audio_bytes).hexdigest()
    now = dt.datetime.utcnow()

    if _is_pg():
        sql = text("""
          INSERT INTO phoneme_results
          (user_id, audio_sha256, ref_text, pred_phones, ref_phones, ops_raw, per_strict, per_sle, wer, word_analysis, weakness_categories, created_at)
          VALUES (:user_id, :audio_sha256, :ref_text, :pred_phones, :ref_phones, :ops_raw, :per_strict, :per_sle, :wer, :word_analysis, :weakness_categories, :created_at)
        """).bindparams(
            bindparam("pred_phones", type_=JSONB),
            bindparam("ref_phones", type_=JSONB),
            bindparam("ops_raw", type_=JSONB),
            bindparam("word_analysis", type_=JSONB),
            bindparam("weakness_categories", type_=JSONB),
        )
        payload = dict(
            user_id=user_id,
            audio_sha256=audio_sha,
            ref_text=(result.get("ref") or {}).get("text"),
            pred_phones=result.get("pred_phones", []),                      # <— Python list
            ref_phones=(result.get("ref") or {}).get("phones"),             # <— Python list | None
            ops_raw=(result.get("align") or {}).get("ops_raw"),             # <— Python list | None
            per_strict=(result.get("align") or {}).get("per_strict"),
            per_sle=(result.get("sle") or {}).get("per_sle"),
            wer=result.get("wer"),
            word_analysis=result.get("word_analysis"),
            weakness_categories=result.get("weakness_categories"),
            created_at=now,
        )
    else:
        sql = text("""
          INSERT INTO phoneme_results
          (user_id, audio_sha256, ref_text, pred_phones, ref_phones, ops_raw, per_strict, per_sle, wer, word_analysis, weakness_categories, created_at)
          VALUES (:user_id, :audio_sha256, :ref_text, :pred_phones, :ref_phones, :ops_raw, :per_strict, :per_sle, :wer, :word_analysis, :weakness_categories, :created_at)
        """)
        payload = dict(
            user_id=user_id,
            audio_sha256=audio_sha,
            ref_text=(result.get("ref") or {}).get("text"),
            pred_phones=json.dumps(result.get("pred_phones", [])),          # <— TEXT JSON for SQLite
            ref_phones=json.dumps((result.get("ref") or {}).get("phones")),
            ops_raw=json.dumps((result.get("align") or {}).get("ops_raw")),
            per_strict=(result.get("align") or {}).get("per_strict"),
            per_sle=(result.get("sle") or {}).get("per_sle"),
            wer=result.get("wer"),
            word_analysis=json.dumps(result.get("word_analysis")),
            weakness_categories=json.dumps(result.get("weakness_categories")),
        created_at=now,
    )
    async with Session() as s:
        await s.execute(sql, payload)
        await s.commit()

async def save_grammar_result(user_id: str, input_text: str, result: Dict[str, Any]):
    text_sha = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
    now = dt.datetime.utcnow()
    gec = result.get("gec") or {}

    if _is_pg():
        sql = text("""
          INSERT INTO grammar_results
          (user_id, text_sha256, input_text, raw_corrected, final_text, edits, guardrails, latency_ms, weakness_categories, created_at)
          VALUES (:user_id, :text_sha256, :input_text, :raw_corrected, :final_text, :edits, :guardrails, :latency_ms, :weakness_categories, :created_at)
        """).bindparams(
            bindparam("edits", type_=JSONB),
            bindparam("guardrails", type_=JSONB),
            bindparam("weakness_categories", type_=JSONB),
        )
        payload = dict(
            user_id=user_id,
            text_sha256=text_sha,
            input_text=result.get("input") or input_text,
            raw_corrected=gec.get("raw_corrected"),
            final_text=gec.get("final_text"),
            edits=gec.get("edits"),                      # <— Python list
            guardrails=result.get("guardrails"),         # <— Python list
            latency_ms=(result.get("metrics") or {}).get("latency_ms"),
            weakness_categories=result.get("weakness_categories"),
            created_at=now,
        )
    else:
        sql = text("""
          INSERT INTO grammar_results
          (user_id, text_sha256, input_text, raw_corrected, final_text, edits, guardrails, latency_ms, weakness_categories, created_at)
          VALUES (:user_id, :text_sha256, :input_text, :raw_corrected, :final_text, :edits, :guardrails, :latency_ms, :weakness_categories, :created_at)
        """)
        payload = dict(
            user_id=user_id,
            text_sha256=text_sha,
            input_text=result.get("input") or input_text,
            raw_corrected=gec.get("raw_corrected"),
            final_text=gec.get("final_text"),
            edits=json.dumps(gec.get("edits")),          # <— TEXT JSON for SQLite
            guardrails=json.dumps(result.get("guardrails")),
            latency_ms=(result.get("metrics") or {}).get("latency_ms"),
            weakness_categories=json.dumps(result.get("weakness_categories")),
            created_at=now,
        )
    async with Session() as s:
        await s.execute(sql, payload)
        await s.commit()

# backend/app/db.py (append at bottom)
import json

async def fetch_user_results(user_id: str, limit: int = 50):
    # Grammar
    sql_grammar = text("""
      SELECT input_text, raw_corrected, final_text, edits, guardrails, latency_ms, created_at
      FROM grammar_results
      WHERE user_id = :user_id
      ORDER BY created_at DESC
      LIMIT :limit
    """)
    # Phoneme
    sql_phoneme = text("""
      SELECT ref_text, pred_phones, ref_phones, ops_raw, per_strict, per_sle, created_at
      FROM phoneme_results
      WHERE user_id = :user_id
      ORDER BY created_at DESC
      LIMIT :limit
    """)

    out = {"grammar": [], "phoneme": []}
    async with Session() as s:
        # grammar
        gr = await s.execute(sql_grammar, {"user_id": user_id, "limit": limit})
        for row in gr.fetchall():
            edits = row.edits
            guards = row.guardrails
            # SQLite stores JSON as TEXT -> parse; PG returns str too via text() -> parse
            try: edits = json.loads(edits) if isinstance(edits, str) and edits else edits
            except Exception: pass
            try: guards = json.loads(guards) if isinstance(guards, str) and guards else guards
            except Exception: pass
            out["grammar"].append({
                "input_text": row.input_text,
                "raw_corrected": row.raw_corrected,
                "final_text": row.final_text,
                "edits": edits,
                "guardrails": guards,
                "latency_ms": row.latency_ms,
                "created_at": row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
            })

        # phoneme
        pr = await s.execute(sql_phoneme, {"user_id": user_id, "limit": limit})
        for row in pr.fetchall():
            pred = row.pred_phones
            refp = row.ref_phones
            ops = row.ops_raw
            try: pred = json.loads(pred) if isinstance(pred, str) and pred else pred
            except Exception: pass
            try: refp = json.loads(refp) if isinstance(refp, str) and refp else refp
            except Exception: pass
            try: ops = json.loads(ops) if isinstance(ops, str) and ops else ops
            except Exception: pass
            out["phoneme"].append({
                "ref_text": row.ref_text,
                "pred_phones": pred,
                "ref_phones": refp,
                "ops_raw": ops,
                "per_strict": row.per_strict,
                "per_sle": row.per_sle,
                "created_at": row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
            })
    return out

# --- Analytics --- 

async def get_user_analytics_cache(user_id: str) -> Row | None:
    sql = text("SELECT * FROM user_analytics_cache WHERE user_id = :user_id AND window_label = '7d'")
    async with Session() as s:
        result = await s.execute(sql, {"user_id": user_id})
        return result.fetchone()

async def upsert_user_analytics_cache(payload: dict):
    if _is_pg():
        sql = text("""
            INSERT INTO user_analytics_cache (user_id, window_label, from_ts, to_ts, attempts_phoneme, attempts_grammar, per_sle_avg, per_sle_median, edits_per_100w_avg, latency_ms_p50, top_phone_subs, top_grammar_weaknesses, top_pronunciation_weaknesses, badge, headline_msg, updated_at, expires_at)
            VALUES (:user_id, :window_label, :from_ts, :to_ts, :attempts_phoneme, :attempts_grammar, :per_sle_avg, :per_sle_median, :edits_per_100w_avg, :latency_ms_p50, :top_phone_subs, :top_grammar_weaknesses, :top_pronunciation_weaknesses, :badge, :headline_msg, :updated_at, :expires_at)
            ON CONFLICT (user_id) DO UPDATE SET
                from_ts = EXCLUDED.from_ts, to_ts = EXCLUDED.to_ts, attempts_phoneme = EXCLUDED.attempts_phoneme, attempts_grammar = EXCLUDED.attempts_grammar, per_sle_avg = EXCLUDED.per_sle_avg, per_sle_median = EXCLUDED.per_sle_median, edits_per_100w_avg = EXCLUDED.edits_per_100w_avg, latency_ms_p50 = EXCLUDED.latency_ms_p50, top_phone_subs = EXCLUDED.top_phone_subs, top_grammar_weaknesses = EXCLUDED.top_grammar_weaknesses, top_pronunciation_weaknesses = EXCLUDED.top_pronunciation_weaknesses, badge = EXCLUDED.badge, headline_msg = EXCLUDED.headline_msg, updated_at = EXCLUDED.updated_at, expires_at = EXCLUDED.expires_at;
        """).bindparams(
            bindparam("top_phone_subs", type_=JSONB),
            bindparam("top_grammar_weaknesses", type_=JSONB),
            bindparam("top_pronunciation_weaknesses", type_=JSONB),
        )
    else: # SQLite
        sql = text("""
            INSERT INTO user_analytics_cache (user_id, window_label, from_ts, to_ts, attempts_phoneme, attempts_grammar, per_sle_avg, per_sle_median, edits_per_100w_avg, latency_ms_p50, top_phone_subs, top_grammar_weaknesses, top_pronunciation_weaknesses, badge, headline_msg, updated_at, expires_at)
            VALUES (:user_id, :window_label, :from_ts, :to_ts, :attempts_phoneme, :attempts_grammar, :per_sle_avg, :per_sle_median, :edits_per_100w_avg, :latency_ms_p50, :top_phone_subs, :top_grammar_weaknesses, :top_pronunciation_weaknesses, :badge, :headline_msg, :updated_at, :expires_at)
            ON CONFLICT (user_id) DO UPDATE SET
                from_ts = excluded.from_ts, to_ts = excluded.to_ts, attempts_phoneme = excluded.attempts_phoneme, attempts_grammar = excluded.attempts_grammar, per_sle_avg = excluded.per_sle_avg, per_sle_median = excluded.per_sle_median, edits_per_100w_avg = excluded.edits_per_100w_avg, latency_ms_p50 = excluded.latency_ms_p50, top_phone_subs = excluded.top_phone_subs, top_grammar_weaknesses = excluded.top_grammar_weaknesses, top_pronunciation_weaknesses = excluded.top_pronunciation_weaknesses, badge = excluded.badge, headline_msg = excluded.headline_msg, updated_at = excluded.updated_at, expires_at = excluded.expires_at;
        """)
        # For SQLite, convert JSON objects to strings
        if payload.get("top_phone_subs") is not None:
            payload["top_phone_subs"] = json.dumps(payload.get("top_phone_subs"))
        if payload.get("top_grammar_weaknesses") is not None:
            payload["top_grammar_weaknesses"] = json.dumps(payload.get("top_grammar_weaknesses"))
        if payload.get("top_pronunciation_weaknesses") is not None:
            payload["top_pronunciation_weaknesses"] = json.dumps(payload.get("top_pronunciation_weaknesses"))

    async with Session() as s:
        await s.execute(sql, payload)
        await s.commit()

async def get_phoneme_results_last_n_days(user_id: str, days: int) -> List[Row]:
    sql = text("SELECT per_sle, ops_raw, weakness_categories, created_at FROM phoneme_results WHERE user_id = :user_id AND created_at >= :start_date")
    start_date = dt.datetime.utcnow() - dt.timedelta(days=days)
    async with Session() as s:
        result = await s.execute(sql, {"user_id": user_id, "start_date": start_date})
        return result.fetchall()

async def get_grammar_results_last_n_days(user_id: str, days: int) -> List[Row]:
    sql = text("SELECT final_text, edits, latency_ms, weakness_categories, created_at FROM grammar_results WHERE user_id = :user_id AND created_at >= :start_date")
    start_date = dt.datetime.utcnow() - dt.timedelta(days=days)
    async with Session() as s:
        result = await s.execute(sql, {"user_id": user_id, "start_date": start_date})
        return result.fetchall()

async def fetch_user_weaknesses(user_id: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetches a paginated list of all weaknesses for a user."""
    sql = text("""
        SELECT type, text, categories, created_at FROM (
            SELECT 'grammar' as type, input_text as text, weakness_categories as categories, created_at
            FROM grammar_results
            WHERE user_id = :user_id AND weakness_categories IS NOT NULL AND weakness_categories != '[]'
            UNION ALL
            SELECT 'pronunciation' as type, ref_text as text, weakness_categories as categories, created_at
            FROM phoneme_results
            WHERE user_id = :user_id AND weakness_categories IS NOT NULL AND weakness_categories != '[]'
        )
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    results = []
    async with Session() as s:
        res = await s.execute(sql, {"user_id": user_id, "limit": limit, "offset": offset})
        for row in res.fetchall():
            categories = row.categories
            try:
                categories = json.loads(categories) if isinstance(categories, str) else categories
            except json.JSONDecodeError:
                categories = []
            
            results.append({
                "type": row.type,
                "text": row.text,
                "categories": categories,
                "created_at": row.created_at.isoformat(),
            })
    return results