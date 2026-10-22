import re
import numpy as np
import pandas as pd

os_df = pd.read_csv('data/os/OsList.csv')

# 1. Pre-build Linux & Other OS lookup from OsList.csv
# Filter out 2-3 character tokens (like 'MX' or 'B2G') that could false-positive on hardware specs
linux_and_other_rules = []
for _, row in os_df[os_df['family'] != 'Windows'].iterrows():
    raw_tokens = str(row['common_aliases_and_tokens']).split(';')
    tokens = [t.strip() for t in raw_tokens if len(t.strip()) >= 4]
    
    if str(row['canonical_name']) not in tokens:
        tokens.append(str(row['canonical_name']))

    linux_and_other_rules.append({
        'os_id': int(row['os_id']),
        'family': str(row['family']),
        'tokens': tokens
    })

# 2. Windows Minimum-Requirement Hierarchy (Ordered OLDEST -> NEWEST)
# Ensures "Windows 10 or Windows 11" resolves to Windows 10 (the true minimum)
WINDOWS_MIN_HIERARCHY = [
    # (os_id, os_tier, regex_patterns)
    (11, 1, [r'\bwindows 95\b', r'\bwin 95\b']),
    (10, 1, [r'\bwindows 98\b', r'\bwin 98\b']),
    (8,  1, [r'\bwindows 2000\b', r'\bwin 2000\b', r'\bwin2k\b']),
    (7,  1, [r'\bwindows xp\b', r'\bwin xp\b', r'\bxp\b']),
    (6,  1, [r'\bwindows vista\b', r'\bwin vista\b', r'\bvista\b']),
    (5,  2, [r'\bwindows 7\b', r'\bwin 7\b']),
    (4,  2, [r'\bwindows 8\b', r'\bwin 8\b']),
    (3,  2, [r'\bwindows 8\.1\b', r'\bwin 8\.1\b']),
    (2,  3, [r'\bwindows 10\b', r'\bwin 10\b']),
    (1,  4, [r'\bwindows 11\b', r'\bwin 11\b']),
]

def resolve_os_features(raw_os) -> pd.Series:
    """
    Returns:
      - OS_ID: Exact os_id from OsList.csv (1-14 for Windows, 30 for macOS, 42+ for Linux)
      - OS_Tier: Hardware era (1=Legacy XP/Vista, 2=Win7/8, 3=Win10/Modern Linux/macOS, 4=Win11)
    """
    if pd.isna(raw_os):
        return pd.Series([np.nan, np.nan], index=['OS_ID', 'OS_Tier'])

    # Clean symbols and split attached numbers (e.g. 'Windows®10' -> 'Windows 10')
    s = str(raw_os).replace('®', ' ').replace('™', ' ')
    s = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', s)
    s_lower = re.sub(r'\s+', ' ', s).strip().lower()

    # Priority 1: Check Windows Versions (Oldest -> Newest)
    for os_id, tier, patterns in WINDOWS_MIN_HIERARCHY:
        if any(re.search(p, s_lower) for p in patterns):
            return pd.Series([os_id, tier], index=['OS_ID', 'OS_Tier'])

    # Priority 2: Check Specific Linux Distros, macOS, BSD, etc. from OsList.csv
    for rule in linux_and_other_rules:
        for token in rule['tokens']:
            if re.search(r'\b' + re.escape(token.lower()) + r'\b', s_lower):
                # Map modern Desktop Linux / macOS to Era Tier 3 (equivalent to Win 10 era)
                tier = 3 if rule['family'] in ('Linux', 'macOS') else 2
                return pd.Series([rule['os_id'], tier], index=['OS_ID', 'OS_Tier'])

    # Priority 3: Generic "Linux" or "SteamOS" fallback -> Ubuntu (os_id = 42)
    if any(k in s_lower for k in ['linux', 'steamos', 'steam os']):
        return pd.Series([42, 3], index=['OS_ID', 'OS_Tier'])

    # Priority 4: Generic "Mac" fallback -> macOS (os_id = 30)
    if any(k in s_lower for k in ['mac os', 'macos', 'os x', 'osx', 'macintosh']):
        return pd.Series([30, 3], index=['OS_ID', 'OS_Tier'])

    # Priority 5: Generic "Windows" without version -> Windows 10 (os_id = 2)
    if 'windows' in s_lower or 'win' in s_lower:
        return pd.Series([2, 3], index=['OS_ID', 'OS_Tier'])

    return pd.Series([2, 3], index=['OS_ID', 'OS_Tier'])