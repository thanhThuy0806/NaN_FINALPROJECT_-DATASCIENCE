import re
import numpy as np
import pandas as pd

def resolve_price(raw_val) -> float:
    """
    Normalizes any Steam price string or numeric value into a float in USD.
    Returns 0.0 for free-to-play titles and np.nan for unpriced/TBA entries.
    """
    if pd.isna(raw_val):
        return np.nan

    # 1. If already an int or float, return directly
    if isinstance(raw_val, (int, float, np.number)):
        return float(raw_val) if raw_val >= 0 else np.nan

    data = str(raw_val).strip()
    if not data:
        return np.nan

    # 2. Check for text-based Free-to-Play labels ("Free", "Free to Play", "F2P")
    data_lower = data.lower()
    if "free" in data_lower or data_lower in {"f2p", "demo"}:
        return 0.0

    # 3. Clean comma separators:
    # Remove thousands commas ("1,299.99" -> "1299.99")
    data_clean = re.sub(r'(\d),(\d{3})\b', r'\1\2', data)
    # Convert European decimal commas ("19,99$" -> "19.99$")
    data_clean = re.sub(r'(\d),(\d{1,2})\b', r'\1.\2', data_clean)

    # 4. Match integer or decimal number (handles both "0$" and "69.99$")
    match = re.search(r'\d+(?:\.\d+)?', data_clean)
    if match:
        return float(match.group(0))

    # 5. Unpriced placeholders ("TBA", "N/A", "Coming Soon") -> np.nan
    return np.nan