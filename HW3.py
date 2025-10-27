# --- NYC Ped Counts | Brooklyn Bridge 2019: Weekdays, Weather, Time-of-Day ---
# Requirements: pandas, numpy, matplotlib
import os
import re
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# CONFIG — EDIT THESE
# =========================
DATA_PATH = "path/to/your_file.csv"  # ← change me (csv or parquet)
LOCATION_NAME = "Brooklyn Bridge"    # case-insensitive match

# If your file already has a single datetime column, add its exact name here (case-insensitive match).
POSSIBLE_DATETIME_COLS = ["datetime", "timestamp", "date_time", "date/time", "hour_beginning"]

# If your file stores date and hour separately, list candidates here (we’ll auto-detect).
POSSIBLE_DATE_COLS = ["date", "day", "count_date"]
POSSIBLE_HOUR_COLS = ["hour", "hr", "time", "count_hour"]

# If your file uses a location column + a generic count column:
POSSIBLE_LOCATION_COLS = ["location", "bridge", "site", "counter_name"]
POSSIBLE_COUNT_COLS_GENERIC = ["count", "pedestrians", "pedestrian_count", "ped_count", "volume"]

# If your file has one column *per* bridge, list likely column names for Brooklyn Bridge:
POSSIBLE_COUNT_COLS_WIDE = [
    "Brooklyn Bridge", "brooklyn bridge", "Brooklyn_Bridge",
    "Brooklyn Bridge - Pedestrians", "BrooklynBridge_Peds", "BB_Pedestrians"
]

# Weather columns (optional but helpful)
POSSIBLE_WEATHER_SUMMARY = ["weather_summary", "weather", "conditions", "summary"]
POSSIBLE_TEMPERATURE = ["temperature", "temp", "air_temp_f", "air_temp_c"]
POSSIBLE_PRECIP = ["precipitation", "precip", "rain", "precip_mm", "precip_in"]

OUTPUT_DIR = "analysis_outputs"  # plots & tables will be saved here

# =========================
# Helper utilities
# =========================
def find_first_col(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

def standardize_colnames(df):
    m = {}
    for c in df.columns:
        m[c] = re.sub(r"\s+", "_", c.strip()).lower()
    df = df.rename(columns=m)
    # return a mapping from lower->original for later lookups if needed
    rev = {v: k for k, v in m.items()}
    return df, rev

def parse_datetime(df):
    # try single datetime column
    dt_col = find_first_col(df, POSSIBLE_DATETIME_COLS)
    if dt_col:
        dt = pd.to_datetime(df[dt_col], errors="coerce", infer_datetime_format=True, utc=False)
        return dt

    # else try date + hour
    date_col = find_first_col(df, POSSIBLE_DATE_COLS)
    hour_col = find_first_col(df, POSSIBLE_HOUR_COLS)
    if date_col is not None and hour_col is not None:
        # hour might be 0..23, "HH:MM", or "H AM/PM"
        # parse date, then add hour
        d = pd.to_datetime(df[date_col], errors="coerce", infer_datetime_format=True, utc=False)
        h_raw = df[hour_col]

        def parse_hour(x):
            if pd.isna(x): return np.nan
            try:
                if isinstance(x, (int, float)):
                    return int(x)
                s = str(x).strip()
                # try HH:MM
                if ":" in s:
                    hh = int(s.split(":")[0])
                    return hh
                # try AM/PM
                m = re.match(r"^(\d{1,2})\s*(am|pm)$", s, flags=re.I)
                if m:
                    hh = int(m.group(1))
                    if m.group(2).lower() == "pm" and hh != 12:
                        hh += 12
                    if m.group(2).lower() == "am" and hh == 12:
                        hh = 0
                    return hh
                # plain int string
                return int(float(s))
            except Exception:
                return np.nan

        hh = h_raw.map(parse_hour)
        dt = d + pd.to_timedelta(hh, unit="h")
        return dt

    # else try any column named "date" that already includes time
    date_col = find_first_col(df, ["date"])
    if date_col:
        dt = pd.to_datetime(df[date_col], errors="coerce", infer_datetime_format=True, utc=False)
        return dt

    raise ValueError("Could not infer datetime. Please specify column names in CONFIG.")

def pick_count_series(df):
    # Strategy A: wide table with a dedicated Brooklyn Bridge column
    wide_col = find_first_col(df, POSSIBLE_COUNT_COLS_WIDE)
    if wide_col:
        return df[wide_col].astype("float"), None  # no location column used

    # Strategy B: tall table with location + generic count column
    loc_col = find_first_col(df, POSSIBLE_LOCATION_COLS)
    cnt_col = find_first_col(df, POSSIBLE_COUNT_COLS_GENERIC)
    if loc_col and cnt_col:
        # filter location now
        mask = df[loc_col].astype(str).str.strip().str.lower() == LOCATION_NAME.lower()
        return df.loc[mask, cnt_col].astype("float"), (loc_col, cnt_col)

    # Strategy C: fallback — maybe a generic "pedestrians" column without location
    cnt_col = find_first_col(df, POSSIBLE_COUNT_COLS_GENERIC)
    if cnt_col:
        return df[cnt_col].astype("float"), None

    raise ValueError("Could not locate a pedestrian count column. Adjust CONFIG candidates.")

def time_of_day_bucket(h):
    # You can adjust the ranges if you prefer different cut points
    if 5 <= h < 12:
        return "Morning"
    elif 12 <= h < 17:
        return "Afternoon"
    elif 17 <= h < 21:
        return "Evening"
    else:
        return "Night"

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

# =========================
# Load data
# =========================
ext = os.path.splitext(DATA_PATH)[1].lower()
if ext in (".parquet", ".pq"):
    df = pd.read_parquet(DATA_PATH)
else:
    df = pd.read_csv(DATA_PATH)

# standardize for easier matching (keeps original data)
df, revmap = standardize_colnames(df)

# datetime
dt = parse_datetime(df)
df = df.assign(dt=dt).dropna(subset=["dt"])

# year filter: 2019
df["year"] = df["dt"].dt.year.astype(int)
df_2019 = df[df["year"] == 2019].copy()
if df_2019.empty:
    raise ValueError("No rows for year 2019 after datetime parsing. Check your date fields.")

# pick counts (and filter location if a tall layout)
counts_series, loc_info = pick_count_series(df_2019)
if loc_info:
    loc_col, cnt_col = loc_info
    # we already filtered by location in pick_count_series; just align the DataFrame
    df_2019 = df_2019[df_2019[loc_col].astype(str).str.strip().str.lower() == LOCATION_NAME.lower()].copy()

df_2019["count"] = counts_series.values

# weekday fields
df_2019["weekday_idx"] = df_2019["dt"].dt.weekday  # Monday=0..Sunday=6
df_2019["weekday_name"] = df_2019["dt"].dt.day_name()
df_2019["is_weekday"] = df_2019["weekday_idx"] < 5
df_2019["hour"] = df_2019["dt"].dt.hour

# time-of-day bucket
df_2019["time_of_day"] = df_2019["hour"].map(time_of_day_bucket)

# =========================
# 1) Weekdays only (Mon–Fri): line plot of average counts by weekday
# =========================
wk = (df_2019[df_2019["is_weekday"]]
      .groupby("weekday_idx", as_index=False)
      .agg(avg_count=("count", "mean"),
           median_count=("count", "median"),
           samples=("count", "size")))
# order Monday..Friday names
names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
wk["weekday_name"] = wk["weekday_idx"].map({i: n for i, n in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])})
wk = wk[wk["weekday_name"].isin(names)]
wk = wk.sort_values("weekday_idx")

ensure_dir(OUTPUT_DIR)
plt.figure(figsize=(8,4.8))
plt.plot(wk["weekday_name"], wk["avg_count"], marker="o")
plt.title(f"Brooklyn Bridge — Average Pedestrian Count by Weekday (2019, Mon–Fri)")
plt.xlabel("Weekday")
plt.ylabel("Average Ped Count")
plt.grid(True, which="both", linestyle=":", linewidth=0.8)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "weekday_avg_line.png"), dpi=150)

# =========================
# 2) Weather influence & correlation matrix (2019 only)
# =========================
wx_col = find_first_col(df_2019, POSSIBLE_WEATHER_SUMMARY)
tmp_col = find_first_col(df_2019, POSSIBLE_TEMPERATURE)
prp_col = find_first_col(df_2019, POSSIBLE_PRECIP)

if wx_col:
    df_2019["weather_summary"] = df_2019[wx_col].astype(str).str.strip()
    # basic sorted view by weather summary (mean & count)
    weather_stats = (df_2019.groupby("weather_summary", as_index=False)
                     .agg(mean_count=("count", "mean"),
                          median_count=("count", "median"),
                          samples=("count", "size"))
                     .sort_values(["samples","mean_count"], ascending=[False, False]))
    weather_stats.to_csv(os.path.join(OUTPUT_DIR, "weather_stats_sorted.csv"), index=False)

    # Build correlation matrix:
    # - One-hot top K weather categories (to avoid an explosion of columns)
    K = 10
    top_wx = weather_stats.head(K)["weather_summary"].tolist()
    df_corr = df_2019[df_2019["weather_summary"].isin(top_wx)].copy()
    wx_dummies = pd.get_dummies(df_corr["weather_summary"], prefix="wx")

    num_cols = [("count", df_corr["count"])]
    if tmp_col:
        # try to make it numeric (C or F—doesn’t matter for correlation direction)
        df_corr["temperature_num"] = pd.to_numeric(df_corr[tmp_col], errors="coerce")
        num_cols.append(("temperature_num", df_corr["temperature_num"]))
    if prp_col:
        df_corr["precip_num"] = pd.to_numeric(df_corr[prp_col], errors="coerce")
        num_cols.append(("precip_num", df_corr["precip_num"]))

    base = pd.DataFrame({name: series for (name, series) in num_cols})
    corr_input = pd.concat([base, wx_dummies], axis=1)
    corr = corr_input.corr(numeric_only=True)

    corr_path = os.path.join(OUTPUT_DIR, "correlation_matrix.csv")
    corr.to_csv(corr_path)

    # Simple heatmap with matplotlib (no seaborn)
    plt.figure(figsize=(10, 8))
    im = plt.imshow(corr.values, aspect="auto")
    plt.colorbar(im, fraction=0.046, pad=0.04)
    plt.xticks(ticks=np.arange(corr.shape[1]), labels=corr.columns, rotation=90)
    plt.yticks(ticks=np.arange(corr.shape[0]), labels=corr.index)
    plt.title("Correlation Matrix: Counts vs Weather (Top Categories) + Temp/Precip (2019)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "correlation_matrix_heatmap.png"), dpi=150)

else:
    print("No weather summary column detected. Add it to POSSIBLE_WEATHER_SUMMARY if present in your data.")

# =========================
# 3) Time-of-day analysis (Morning/Afternoon/Evening/Night)
# =========================
tod_order = ["Night", "Morning", "Afternoon", "Evening"]
tod_stats = (df_2019.groupby("time_of_day", as_index=False)
             .agg(mean_count=("count", "mean"),
                  median_count=("count", "median"),
                  total_count=("count", "sum"),
                  samples=("count", "size")))
tod_stats["time_of_day"] = pd.Categorical(tod_stats["time_of_day"], categories=tod_order, ordered=True)
tod_stats = tod_stats.sort_values("time_of_day")
tod_stats.to_csv(os.path.join(OUTPUT_DIR, "time_of_day_stats.csv"), index=False)

# Plot average counts by time of day
plt.figure(figsize=(7.5, 4.8))
plt.bar(tod_stats["time_of_day"].astype(str), tod_stats["mean_count"])
plt.title("Average Pedestrian Count by Time of Day — Brooklyn Bridge (2019)")
plt.xlabel("Time of Day")
plt.ylabel("Average Ped Count")
plt.grid(axis="y", linestyle=":", linewidth=0.8)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "time_of_day_average_bar.png"), dpi=150)

# A quick printout to confirm where things were saved
print(textwrap.dedent(f"""
Done. Outputs saved in: {os.path.abspath(OUTPUT_DIR)}

• weekday_avg_line.png
• correlation_matrix.csv (if weather available)
• correlation_matrix_heatmap.png (if weather available)
• weather_stats_sorted.csv (if weather available)
• time_of_day_stats.csv
• time_of_day_average_bar.png
"""))