# filename: etl.py
# Purpose: ETL pipeline for Spotify-like streaming logs → normalized relational tables
# Usage:
#   python etl.py data
#   python etl.py data/*.json
#
# Requirements:
#   pip install pandas python-dateutil
#
# What it does:
# - Reads one or more JSON files containing arrays of streaming records
# - Cleans and deduplicates records
# - Builds normalized dimension tables (User, Artist, Album, Track) and a fact table (History)
# - Extracts “Feat” relationships (artist uri <> track uri) when multiple artists are present or inferred
# - Writes CSVs for subsequent DB load (N-tier: DB + API + UI)
#
# Notes:
# - If your source doesn’t carry popularity/genres/photos, the ETL leaves NULL; later you can augment via Spotify API
# - User info (pp, name) is settable via a simple config; streaming logs rarely contain user profile data
# - Artist/Album/Track IDs are created as stable hashes based on URIs/names (when URI missing)
# - Timestamps are parsed to UTC
# - You can adapt to write directly to DB (psycopg2/sqlalchemy) once schema is created

import os
import sys
import json
import glob
import hashlib
from datetime import datetime
from dateutil import parser as dtparser
import pandas as pd

# ------------------ Config ------------------
CONFIG = {
    # Basic user info (you can put multiple users if needed; this example assumes a single owner of the logs)
    "user": {
        "user_id": "user_001",
        "display_name": "Your Name",
        "profile_picture_url": None  # "https://example.com/pp.jpg"
    },
    # If your logs do not contain genre/popularity/photos, leave enrichment to future steps (API-based)
    "default_values": {
        "artist_genres": None,
        "artist_popularity": None,
        "artist_photo": None,
        "album_photo": None,
        "track_popularity": None,
        "track_photo": None,
    },
    # Feat extraction heuristics:
    # If multiple artists are in "master_metadata_album_artist_name" (comma, &, feat, x), we split them.
    "artist_split_patterns": [",", "&", " x ", " X ", " feat. ", " ft. ", " (feat. ", ")"],
}

OUT_DIR = "out"
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------ Utils ------------------
def read_json_arrays(paths):
    records = []
    for p in paths:
        try:
            text = open(p, "r", encoding="utf-8").read().strip()
            # Extract the first JSON array if text has additional wrappers
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
            arr = json.loads(text)
            if isinstance(arr, list):
                records.extend(arr)
        except Exception as e:
            print(f"[WARN] Failed to parse {p}: {e}")
    return records

def parse_ts(ts):
    if not ts:
        return None
    try:
        dt = dtparser.isoparse(ts)
        # Force UTC if tz-naive
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None

def stable_id(*parts, prefix="id_"):
    h = hashlib.sha1(("|".join(parts)).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{h}"

def clean_str(s):
    if s is None:
        return None
    s = str(s).strip()
    return s if s else None

def minutes(ms):
    try:
        return ms / 1000.0 / 60.0
    except Exception:
        return 0.0

def split_artists(name):
    if not name:
        return []
    # normalize spaces around separators
    n = " " + name + " "
    for pat in CONFIG["artist_split_patterns"]:
        n = n.replace(pat, "|")
    parts = [p.strip() for p in n.split("|") if p.strip()]
    # de-duplicate while preserving order
    seen = set()
    res = []
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower())
            res.append(p)
    return res

# ------------------ ETL Core ------------------
def build_tables(raw_records, user_cfg):
    # Deduplicate by (ts, track URI) if possible; fall back to (ts, track name)
    seen = set()
    rows = []
    for r in raw_records:
        ts = r.get("ts") or r.get("timestamp") or r.get("endTime")
        uri = r.get("spotify_track_uri")
        tname = r.get("master_metadata_track_name")
        key = f"{ts}|{uri or tname or ''}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)

    # Normalize base
    norm = []
    for r in rows:
        ts = r.get("ts") or r.get("timestamp") or r.get("endTime")
        dt = parse_ts(ts)
        platform = clean_str(r.get("platform"))
        ms_played = r.get("ms_played") or 0
        artist_name = clean_str(r.get("master_metadata_album_artist_name"))
        track_name = clean_str(r.get("master_metadata_track_name"))
        album_name = clean_str(r.get("master_metadata_album_album_name"))
        conn_country = clean_str(r.get("conn_country"))
        ip_addr = clean_str(r.get("ip_addr"))
        track_uri = clean_str(r.get("spotify_track_uri"))

        reason_start = clean_str(r.get("reason_start"))
        reason_end = clean_str(r.get("reason_end"))
        skipped = bool(r.get("skipped"))
        offline = bool(r.get("offline"))
        shuffle = bool(r.get("shuffle"))
        incognito = bool(r.get("incognito_mode"))

        norm.append({
            "ts": ts,
            "timestamp_dt": dt,
            "platform": platform,
            "ms_played": ms_played,
            "artist_name": artist_name,
            "track_name": track_name,
            "album_name": album_name,
            "conn_country": conn_country,
            "ip_addr": ip_addr,
            "track_uri": track_uri,
            "reason_start": reason_start,
            "reason_end": reason_end,
            "skipped": skipped,
            "offline": offline,
            "shuffle": shuffle,
            "incognito": incognito,
        })

    df = pd.DataFrame(norm)

    # Dimension: Users (single record from config)
    users = pd.DataFrame([{
        "user_id": user_cfg["user_id"],
        "display_name": user_cfg["display_name"],
        "profile_picture_url": user_cfg["profile_picture_url"]
    }])

    # Dimension: Artists
    # Extract unique artists (including feat splits)
    artist_rows = []
    for _, row in df.iterrows():
        for name in split_artists(row["artist_name"]):
            aid = stable_id(name.lower(), prefix="artist_")
            artist_rows.append({
                "artist_id": aid,
                "artist_name": name,
                "popularity": CONFIG["default_values"]["artist_popularity"],
                "photo_url": CONFIG["default_values"]["artist_photo"],
                "genres": CONFIG["default_values"]["artist_genres"],  # later enrichment
            })
    artists = pd.DataFrame(artist_rows).drop_duplicates(subset=["artist_id"])

    # Dimension: Albums
    album_rows = []
    for _, row in df.iterrows():
        alb = row["album_name"]
        if not alb:
            continue
        # We cannot reliably get album URI from logs; derive ID from name + first artist
        first_artist = split_artists(row["artist_name"])[0] if split_artists(row["artist_name"]) else None
        album_id = stable_id((alb or "").lower(), (first_artist or "").lower(), prefix="album_")
        album_rows.append({
            "album_id": album_id,
            "album_name": alb,
            "artist_name": first_artist,
            "release_date": None,  # later enrichment via API
            "total_tracks": None,  # later enrichment via API
            "photo_url": CONFIG["default_values"]["album_photo"],
        })
    albums = pd.DataFrame(album_rows).drop_duplicates(subset=["album_id"])

    # Dimension: Tracks
    track_rows = []
    for _, row in df.iterrows():
        tname = row["track_name"]
        if not tname:
            continue
        t_uri = row["track_uri"] or None
        # Track ID prefers URI; otherwise derive from name + album
        tid = (stable_id(t_uri, prefix="track_") if t_uri
               else stable_id((tname or "").lower(), (row["album_name"] or "").lower(), prefix="track_"))
        # Link to album_id
        first_artist = split_artists(row["artist_name"])[0] if split_artists(row["artist_name"]) else None
        album_id = stable_id((row["album_name"] or "").lower(), (first_artist or "").lower(), prefix="album_")
        track_rows.append({
            "track_id": tid,
            "track_uri": t_uri,
            "track_name": tname,
            "album_id": album_id,
            "main_artist_name": first_artist,
            "duration_ms": None,  # may be enriched via API; logs have ms_played per stream, not canonical duration
            "popularity": CONFIG["default_values"]["track_popularity"],
            "photo_url": CONFIG["default_values"]["track_photo"],
        })
    tracks = pd.DataFrame(track_rows).drop_duplicates(subset=["track_id"])

    # Bridge: Track <-> Artist (including Feat)
    feat_rows = []
    # Map artist_name → artist_id
    artist_map = {row["artist_name"].lower(): row["artist_id"] for _, row in artists.iterrows()}

    for _, row in df.iterrows():
        t_uri = row["track_uri"] or None
        track_id = (stable_id(t_uri, prefix="track_") if t_uri
                    else stable_id((row["track_name"] or "").lower(), (row["album_name"] or "").lower(), prefix="track_"))
        for name in split_artists(row["artist_name"]):
            aid = artist_map.get(name.lower())
            if aid:
                feat_rows.append({
                    "artist_id": aid,
                    "track_id": track_id
                })
    feat = pd.DataFrame(feat_rows).drop_duplicates(subset=["artist_id", "track_id"])

    # Fact: History (per play)
    history_rows = []
    for _, row in df.iterrows():
        # foreign keys
        t_uri = row["track_uri"] or None
        track_id = (stable_id(t_uri, prefix="track_") if t_uri
                    else stable_id((row["track_name"] or "").lower(), (row["album_name"] or "").lower(), prefix="track_"))
        first_artist = split_artists(row["artist_name"])[0] if split_artists(row["artist_name"]) else None
        artist_id = artist_map.get(first_artist.lower()) if first_artist else None

        # Parse timestamp
        ts_dt = row["timestamp_dt"]
        ts_iso = ts_dt.isoformat() if ts_dt else None

        history_id = stable_id(user_cfg["user_id"], track_id, row["ts"] or "", prefix="hist_")

        history_rows.append({
            "history_id": history_id,
            "user_id": user_cfg["user_id"],
            "track_id": track_id,
            "artist_id": artist_id,
            "timestamp_utc": ts_iso,
            "ms_played": int(row["ms_played"] or 0),
            "platform": row["platform"],
            "country": row["conn_country"],
            "ip_addr": row["ip_addr"],
            "reason_start": row["reason_start"],
            "reason_end": row["reason_end"],
            "skipped": bool(row["skipped"]),
            "offline": bool(row["offline"]),
            "shuffle": bool(row["shuffle"]),
            "incognito": bool(row["incognito"]),
        })
    history = pd.DataFrame(history_rows)

    # Deduplicate any lingering collisions
    for name, df_ in [("users", users), ("artists", artists), ("albums", albums), ("tracks", tracks), ("feat", feat), ("history", history)]:
        df_.drop_duplicates(inplace=True)

    return {
        "users": users,
        "artists": artists,
        "albums": albums,
        "tracks": tracks,
        "feat": feat,
        "history": history,
    }

def write_csvs(tables, out_dir=OUT_DIR):
    tables["users"].to_csv(os.path.join(out_dir, "users.csv"), index=False)
    tables["artists"].to_csv(os.path.join(out_dir, "artists.csv"), index=False)
    tables["albums"].to_csv(os.path.join(out_dir, "albums.csv"), index=False)
    tables["tracks"].to_csv(os.path.join(out_dir, "tracks.csv"), index=False)
    tables["feat"].to_csv(os.path.join(out_dir, "feat.csv"), index=False)
    tables["history"].to_csv(os.path.join(out_dir, "history.csv"), index=False)
    print(f"[OK] CSVs written to {os.path.abspath(out_dir)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python etl.py <directory|files>")
        sys.exit(1)
    args = sys.argv[1:]
    inputs = []
    for a in args:
        if os.path.isdir(a):
            inputs.extend(glob.glob(os.path.join(a, "*.json")))
        else:
            inputs.extend(glob.glob(a))
    inputs = list(dict.fromkeys(inputs))
    if not inputs:
        print("[ERR] No JSON input files found.")
        sys.exit(1)

    raw = read_json_arrays(inputs)
    if not raw:
        print("[ERR] No records after parsing.")
        sys.exit(1)

    tables = build_tables(raw, CONFIG["user"])
    write_csvs(tables)

    # Quick summary
    print("------ Summary ------")
    print(f"Users:   {len(tables['users'])}")
    print(f"Artists: {len(tables['artists'])}")
    print(f"Albums:  {len(tables['albums'])}")
    print(f"Tracks:  {len(tables['tracks'])}")
    print(f"Feat:    {len(tables['feat'])}")
    print(f"History: {len(tables['history'])}")

if __name__ == "__main__":
    main()
