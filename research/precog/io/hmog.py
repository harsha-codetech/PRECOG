"""HMOG dataset reader.

Column names are taken verbatim from `public_dataset/data_description.pdf`, which ships
inside the dataset. The CSVs carry no header row.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SCHEMAS: dict[str, list[str]] = {
    "Activity.csv": [
        "ActivityID", "SubjectID", "Session_number",
        "Start_time", "End_time", "Relative_Start_time", "Relative_End_time",
        "Gesture_scenario", "TaskID", "ContentID",
    ],
    # One row per MOVE sample. Rows group by ScrollID into a single scroll gesture.
    "ScrollEvent.csv": [
        "Systime", "BeginTime", "CurrentTime", "ActivityID", "ScrollID",
        "Start_action_type", "Start_X", "Start_Y", "Start_pressure", "Start_size",
        "Current_action_type", "Current_X", "Current_Y", "Current_pressure", "Current_size",
        "Distance_X", "Distance_Y", "Phone_orientation",
    ],
    # One row per completed stroke. Speed_X/Speed_Y are measured fling velocity (px/s).
    "StrokeEvent.csv": [
        "Systime", "Begin_time", "End_time", "ActivityID",
        "Start_action_type", "Start_X", "Start_Y", "Start_pressure", "Start_size",
        "End_action_type", "End_X", "End_Y", "End_pressure", "End_size",
        "Speed_X", "Speed_Y", "Phone_orientation",
    ],
    "TouchEvent.csv": [
        "Systime", "EventTime", "ActivityID", "Pointer_count", "PointerID",
        "ActionID", "X", "Y", "Pressure", "Contact_size", "Phone_orientation",
    ],
}

# Systime is epoch milliseconds; the relative columns are milliseconds since boot.
ACTION_DOWN, ACTION_UP, ACTION_MOVE = 0, 1, 2

# Pressure is a constant 1.0 in every HMOG file and for every subject: the 2014 Samsung
# devices did not report it, and Android returns 1.0 when unsupported. Touchalytics ranks
# mid-stroke pressure as its 3rd most discriminative feature (17.3% MI), so any feature set
# shared with FETA must exclude pressure or the comparison is confounded.
UNUSABLE_COLUMNS = ("Start_pressure", "Current_pressure", "End_pressure", "Pressure")

_SESSION_RE = re.compile(r"/(\d+)_session_(\d+)/([A-Za-z]+\.csv)$")


@dataclass(frozen=True)
class SessionRef:
    subject: int
    session: int
    member: str  # path inside the zip


def list_sessions(zip_path: Path) -> list[SessionRef]:
    """Index one subject archive without extracting it."""
    with zipfile.ZipFile(zip_path) as z:
        refs = []
        for name in z.namelist():
            m = _SESSION_RE.search("/" + name)
            if m and m.group(3) in SCHEMAS:
                refs.append(SessionRef(int(m.group(1)), int(m.group(2)), name))
        return refs


def read_member(zip_path: Path, member: str) -> pd.DataFrame:
    """Read one CSV straight out of the archive, with its documented column names."""
    kind = member.rsplit("/", 1)[-1]
    with zipfile.ZipFile(zip_path) as z:
        raw = z.read(member)
    if not raw.strip():
        return pd.DataFrame(columns=SCHEMAS[kind])
    df = pd.read_csv(io.BytesIO(raw), header=None, names=SCHEMAS[kind],
                     on_bad_lines="skip")
    # Every HMOG column is numeric, but some sessions — map navigation especially —
    # contain malformed rows that leave a column as object dtype. Coerce here so the
    # damage is confined to NaNs in the affected rows instead of propagating a mixed
    # dtype into Parquet.
    return df.apply(pd.to_numeric, errors="coerce")


def read_activity(zip_path: Path) -> pd.DataFrame:
    """Every Activity.csv in one subject archive, concatenated.

    Activity rows are the only place task and posture are recorded, so this is what
    decides which sessions are worth extracting.
    """
    frames = []
    for ref in list_sessions(zip_path):
        if not ref.member.endswith("Activity.csv"):
            continue
        df = read_member(zip_path, ref.member)
        if df.empty:
            continue
        df["session"] = ref.session
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=[*SCHEMAS["Activity.csv"], "session"])
    return pd.concat(frames, ignore_index=True)


def scroll_gestures(scroll: pd.DataFrame) -> pd.DataFrame:
    """Collapse MOVE samples into one row per scroll gesture.

    A ScrollEvent row is a single MOVE sample, not a scroll. Treating rows as gestures
    overcounts by roughly 24x, so every downstream feature depends on this grouping.
    """
    if scroll.empty:
        return pd.DataFrame()
    g = scroll.groupby(["ActivityID", "ScrollID"], sort=True)
    out = g.agg(
        n_samples=("Systime", "size"),
        t_start=("Systime", "min"),
        t_end=("Systime", "max"),
        start_x=("Start_X", "first"),
        start_y=("Start_Y", "first"),
        end_x=("Current_X", "last"),
        end_y=("Current_Y", "last"),
        pressure_mean=("Current_pressure", "mean"),
        size_mean=("Current_size", "mean"),
        dx_sum=("Distance_X", "sum"),
        dy_sum=("Distance_Y", "sum"),
        orientation=("Phone_orientation", "first"),
    ).reset_index()
    out["duration_ms"] = out["t_end"] - out["t_start"]
    out = out.sort_values(["ActivityID", "t_start"])
    # Gap from the end of the previous gesture to the start of this one: the dwell /
    # pause signal that FETA's feature table cannot provide. First gesture of each
    # activity has no predecessor, so it is NaN by construction.
    prev_end = out.groupby("ActivityID")["t_end"].shift(1)
    out["inter_scroll_ms"] = out["t_start"] - prev_end
    # A negative gap means two gestures overlapped (multi-touch). Rare and not
    # meaningful as a pause, so it is dropped rather than clamped.
    out.loc[out["inter_scroll_ms"] < 0, "inter_scroll_ms"] = pd.NA
    return out.reset_index(drop=True)
