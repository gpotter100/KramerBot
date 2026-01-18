#!/usr/bin/env Rscript

# ============================================================
# NFL PBP INGESTION PIPELINE (1999–2025)
# - Uses nflreadr to download play-by-play
# - Normalizes to a canonical schema
# - Writes one parquet per season:
#     backend/tmp/kramerbot_pbp_cache/pbp_{season}.parquet
# ============================================================

suppressPackageStartupMessages({
  library(nflreadr)
  library(dplyr)
  library(arrow)
  library(purrr)
  library(glue)
  library(stringr)
})

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

# Adjust this to your actual backend root if needed
backend_root <- here::here()  # assumes script is run from repo root

cache_dir <- file.path(
  backend_root,
  "backend",
  "tmp",
  "kramerbot_pbp_cache"
)

if (!dir.exists(cache_dir)) {
  dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
}

seasons <- 1999:2025

# ------------------------------------------------------------
# CANONICAL SCHEMA DEFINITION
# (we'll coerce/rename into this shape as best as possible)
# ------------------------------------------------------------

canonical_cols <- c(
  # identifiers
  "season", "week", "season_type",
  "game_id", "play_id",
  
  # teams
  "posteam", "defteam", "home_team", "away_team",
  
  # context
  "game_date", "qtr", "quarter_seconds_remaining",
  "game_seconds_remaining", "down", "ydstogo", "yardline_100",
  
  # play type flags
  "play_type", "pass_attempt", "rush_attempt",
  "complete_pass", "interception", "fumble_lost",
  "touchdown", "first_down", "penalty",
  
  # yardage / EPA
  "yards_gained", "air_yards", "yac_yards",
  "epa", "wpa", "success",
  
  # players
  "passer_id", "passer",
  "rusher_id", "rusher",
  "receiver_id", "receiver",
  
  # misc
  "desc"
)

# ------------------------------------------------------------
# NORMALIZATION FUNCTION
# ------------------------------------------------------------

normalize_pbp <- function(df) {
  # Ensure basic columns exist
  add_missing <- setdiff(canonical_cols, names(df))
  if (length(add_missing) > 0) {
    for (col in add_missing) {
      df[[col]] <- NA
    }
  }
  
  # Coerce types where reasonable
  int_cols <- c("season", "week", "qtr", "down", "ydstogo", "yardline_100")
  num_cols <- c(
    "quarter_seconds_remaining", "game_seconds_remaining",
    "yards_gained", "air_yards", "yac_yards",
    "epa", "wpa"
  )
  logi_cols <- c(
    "pass_attempt", "rush_attempt", "complete_pass",
    "interception", "fumble_lost", "touchdown",
    "first_down", "penalty", "success"
  )
  
  for (col in intersect(int_cols, names(df))) {
    df[[col]] <- suppressWarnings(as.integer(df[[col]]))
  }
  
  for (col in intersect(num_cols, names(df))) {
    df[[col]] <- suppressWarnings(as.numeric(df[[col]]))
  }
  
  for (col in intersect(logi_cols, names(df))) {
    # Some older seasons may store as 0/1 or NA
    df[[col]] <- dplyr::case_when(
      is.na(df[[col]]) ~ NA,
      df[[col]] %in% c(TRUE, FALSE) ~ as.logical(df[[col]]),
      df[[col]] %in% c(1, "1", "TRUE", "T") ~ TRUE,
      df[[col]] %in% c(0, "0", "FALSE", "F") ~ FALSE,
      TRUE ~ NA
    )
  }
  
  # Ensure character columns for IDs/names/teams
  char_cols <- c(
    "game_id", "play_id", "posteam", "defteam",
    "home_team", "away_team",
    "play_type",
    "passer_id", "passer",
    "rusher_id", "rusher",
    "receiver_id", "receiver",
    "season_type", "desc"
  )
  
  for (col in intersect(char_cols, names(df))) {
    df[[col]] <- as.character(df[[col]])
  }
  
  # Ensure game_date is Date if present
  if ("game_date" %in% names(df)) {
    df$game_date <- as.Date(df$game_date)
  }
  
  # Keep only canonical columns in a stable order
  df <- df[, canonical_cols]
  
  df
}

# ------------------------------------------------------------
# INGEST ONE SEASON
# ------------------------------------------------------------

ingest_season <- function(season) {
  message(glue("🔄 Ingesting season {season}..."))
  
  out_path <- file.path(cache_dir, glue("pbp_{season}.parquet"))
  
  # If you want to skip existing files, uncomment:
  # if (file.exists(out_path)) {
  #   message(glue("✅ Already exists, skipping: {out_path}"))
  #   return(invisible(NULL))
  # }
  
  # nflreadr handles caching internally; this will be fast after first run
  df <- tryCatch(
    {
      nflreadr::load_pbp(seasons = season)
    },
    error = function(e) {
      message(glue("⚠️ Failed to load PBP for {season}: {e$message}"))
      return(NULL)
    }
  )
  
  if (is.null(df) || nrow(df) == 0) {
    message(glue("⚠️ No PBP rows for {season}, skipping"))
    return(invisible(NULL))
  }
  
  # Normalize to canonical schema
  df_norm <- normalize_pbp(df)
  
  # Write parquet
  message(glue("💾 Writing {nrow(df_norm)} rows → {out_path}"))
  arrow::write_parquet(df_norm, out_path)
  
  invisible(NULL)
}

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

message(glue("📁 Backend root: {backend_root}"))
message(glue("📁 Cache dir:    {cache_dir}"))
message(glue("📅 Seasons:      {min(seasons)}–{max(seasons)}"))

walk(seasons, ingest_season)

message("✅ PBP ingestion complete.")
