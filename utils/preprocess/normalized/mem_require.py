import re
import numpy as np
import pandas as pd

# Normalize unit variations to their divisor back to GB
UNIT_DIVISORS = {
    # Gigabytes
    "GB": 1.0, "GIB": 1.0, "G": 1.0, "GO": 1.0, "ГБ": 1.0, "GIGABYTES": 1.0, "GIGABYTE": 1.0,
    # Megabytes
    "MB": 1024.0, "MIB": 1024.0, "M": 1024.0, "MO": 1024.0, "МБ": 1024.0, "MEGABYTES": 1024.0, "MEGABYTE": 1024.0,
    # Kilobytes
    "KB": 1024.0 * 1024.0, "KIB": 1024.0 * 1024.0, "K": 1024.0 * 1024.0, "КБ": 1024.0 * 1024.0,
}

# 1. Regex that strictly pairs a number (with optional decimal) directly to its RAM unit
PAIRED_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(GIGABYTES?|MEGABYTES?|GIB|MIB|KIB|GB|MB|KB|GO|MO|ГБ|МБ|КБ|G|M|K)\b',
    re.IGNORECASE
)

# 2. Noise patterns to strip BEFORE fallback unitless matching (e.g., DDR3, DDR4, 32-bit, 64-bit)
NOISE_PATTERN = re.compile(
    r'\b(?:DDR\d*|32\s*-?\s*BIT|64\s*-?\s*BIT|WIN(?:DOWS)?\s*\d+|DIRECTX\s*\d+)\b',
    re.IGNORECASE
)

def _clean_numeric_text(s: str) -> str:
    """Standardizes thousand-separators (1,024 -> 1024) and European decimals (1,5 -> 1.5)."""
    # Remove thousand separators like 1,024 or 2,048 (comma followed by 3 digits)
    s = re.sub(r'(\d),(\d{3})\b', r'\1\2', s)
    # Convert remaining comma decimals like 1,5 GB -> 1.5 GB
    s = re.sub(r'(\d),(\d+)', r'\1.\2', s)
    return s

def resolve_mem_require(raw_str) -> float:
    """Normalizes any Steam MemoryRequirement string to a float in GB (or np.nan if invalid)."""
    if pd.isna(raw_str):
        return np.nan

    data = str(raw_str).strip()
    if not data:
        return np.nan

    data = _clean_numeric_text(data.upper())

    # --- STEP 1: Match paired (Number + Unit) directly ---
    # Fixes "DDR4 8GB", "64-bit 4 GB", and "512 MB (1 GB recommended)"
    paired_matches = PAIRED_PATTERN.findall(data)
    if paired_matches:
        num_str, unit_str = paired_matches[0]  # First valid (number, unit) pair is Minimum RAM
        mem_val = float(num_str)
        divisor = UNIT_DIVISORS[unit_str.upper()]
        result_gb = mem_val / divisor
        return result_gb if 0 < result_gb <= 128 else np.nan

    # --- STEP 2: Fallback for strings missing units (e.g., "8 RAM", "1024") ---
    # Strip hardware noise ("DDR4", "64-bit") so we don't grab 4 or 64 by mistake
    cleaned_data = NOISE_PATTERN.sub(' ', data)
    num_matches = re.findall(r'\d+(?:\.\d+)?', cleaned_data)
    
    if not num_matches:
        # Handles "TBA", "TBD", "N/A", "Unknown" gracefully without crashing
        return np.nan

    mem_need = float(num_matches[0])
    if mem_need <= 0:
        return np.nan

    # Fallback thresholds: <= 64 is GB, <= 65536 is MB, larger is KB/Bytes
    if mem_need <= 64:
        return mem_need
    elif mem_need <= 65536:
        return mem_need / 1024.0
    elif mem_need <= 65536 * 1024:
        return mem_need / (1024.0 * 1024.0)

    return np.nan