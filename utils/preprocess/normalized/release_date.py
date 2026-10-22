import re
import numpy as np
import pandas as pd

MONTH_TO_INT = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

# Map quarters to the middle month of each quarter
QUARTER_TO_MONTH = {
    '1': 2,   # Q1 -> Feb
    '2': 5,   # Q2 -> May
    '3': 8,   # Q3 -> Aug
    '4': 11,  # Q4 -> Nov
}

def _to_yyyymmdd(y: int, m: int = 1, d: int = 1) -> float:
    """Validates bounds and packs Year, Month, Day into YYYYMMDD integer format."""
    if not (1970 <= y <= 2035):
        return np.nan
    m = max(1, min(12, m))
    d = max(1, min(31, d))
    return float(y * 10000 + m * 100 + d)


def resolve_release_date(raw_str) -> float:
    """
    Normalizes any Steam ReleaseDate string into a YYYYMMDD float/int (e.g., 20260226).
    Returns np.nan if missing or unreleased ('Coming soon', 'TBA', etc.).
    """
    if pd.isna(raw_str):
        return np.nan

    data = str(raw_str).strip()
    if not data:
        return np.nan

    s = data.lower()

    # 1. Standard US Format: "Feb 26, 2026" or "February 26, 2026"
    m_us = re.search(r'\b([a-z]{3})[a-z]*\s+(\d{1,2})[,\s]+(\d{4})\b', s)
    if m_us and m_us.group(1) in MONTH_TO_INT:
        month = MONTH_TO_INT[m_us.group(1)]
        day = int(m_us.group(2))
        year = int(m_us.group(3))
        return _to_yyyymmdd(year, month, day)

    # 2. Day-First (EU) Format: "26 Feb, 2026" or "26 February 2026"
    m_eu = re.search(r'\b(\d{1,2})\s+([a-z]{3})[a-z]*[,\s]+(\d{4})\b', s)
    if m_eu and m_eu.group(2) in MONTH_TO_INT:
        day = int(m_eu.group(1))
        month = MONTH_TO_INT[m_eu.group(2)]
        year = int(m_eu.group(3))
        return _to_yyyymmdd(year, month, day)

    # 3. ISO / Numeric Format: "2026-02-26" or "2026/02/26"
    m_iso = re.search(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b', s)
    if m_iso:
        return _to_yyyymmdd(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))

    # 4. Month + Year Only: "Oct 2026" or "October, 2026" (Default day = 15)
    m_my = re.search(r'\b([a-z]{3})[a-z]*[,\s]+(\d{4})\b', s)
    if m_my and m_my.group(1) in MONTH_TO_INT:
        month = MONTH_TO_INT[m_my.group(1)]
        year = int(m_my.group(2))
        return _to_yyyymmdd(year, month, 15)

    # 5. Quarter + Year: "Q1 2026" or "Q4, 2025"
    m_q = re.search(r'\bq([1-4])[,\s]+(\d{4})\b', s)
    if m_q:
        month = QUARTER_TO_MONTH[m_q.group(1)]
        year = int(m_q.group(2))
        return _to_yyyymmdd(year, month, 15)

    # 6. Year Only Fallback: "2025" (Default to Mid-Year: July 1)
    m_y = re.search(r'\b(19[7-9]\d|20[0-3]\d)\b', s)
    if m_y:
        return _to_yyyymmdd(int(m_y.group(1)), 7, 1)

    # 7. Unreleased / Placeholders ("Coming soon", "TBA", "TBD") -> np.nan
    return np.nan