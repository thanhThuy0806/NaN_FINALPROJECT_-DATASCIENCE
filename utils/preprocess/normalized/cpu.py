import re
import numpy as np
import pandas as pd



cpu_df = pd.read_csv('data/cpu/CpuList.csv')

devices = ["Desktop", "Laptop", "Mobile"]

# only include cpu uses in devices
cpu_df = cpu_df[cpu_df['category'].isin(devices)]
# Build Cleaned Lookup Table from CpuList.csv
def clean_cpu_key(name):
    s = str(name).lower()
    s = re.sub(r'\s*@\s*[\d\.]+\s*(ghz|mhz)', '', s)
    s = re.sub(r'\b(eight-core|six-core|quad-core|dual-core|triple-core|core|processor|apu|intel|amd)\b', '', s)
    return re.sub(r'[\s\-]+', ' ', s).strip()

cpu_df['clean_key'] = cpu_df['name'].apply(clean_cpu_key)
# Prioritize longer, more specific model names and popular desktop chips
valid_cpus = cpu_df[cpu_df['clean_key'].str.len() >= 4].sort_values(
    by=['clean_key', 'samples'], key=lambda col: col.str.len() if col.name == 'clean_key' else col, ascending=False
)

# Pre-calculate Family Fallbacks from CpuList.csv so zero rows are lost
family_fallbacks = [
    (['i9', 'ryzen 9'], cpu_df[cpu_df['name'].str.contains('Core i9|Ryzen 9', na=False)]['rank'].median(), 8),
    (['i7', 'ryzen 7'], cpu_df[cpu_df['name'].str.contains('Core i7|Ryzen 7', na=False)]['rank'].median(), 4),
    (['i5', 'ryzen 5', '4 core', '4-core', 'quad'], cpu_df[cpu_df['name'].str.contains('Core i5|Ryzen 5', na=False)]['rank'].median(), 4),
    (['i3', 'ryzen 3', 'phenom'], cpu_df[cpu_df['name'].str.contains('Core i3|Ryzen 3', na=False)]['rank'].median(), 2),
    (['core 2', 'dual', 'pentium', 'athlon', 'ghz'], cpu_df[cpu_df['name'].str.contains('Core2 Duo|Pentium', na=False)]['rank'].median(), 2),
]



def resolve_cpu_features(raw_req):
    if pd.isna(raw_req):
        return pd.Series([np.nan, np.nan], index=['CPU_Rank', 'CPU_Cores'])
    
    s = str(raw_req).lower().replace('®', ' ').replace('™', ' ').replace('(r)', ' ').replace('(tm)', ' ')
    s_clean = re.sub(r'\b(core|processor|intel|amd)\b', ' ', s)
    s_clean = re.sub(r'[\s\-]+', ' ', s_clean).strip()
    
    # Tier 1: Exact Model Match in CpuList.csv
    for _, row in valid_cpus.iterrows():
        if re.search(r'\b' + re.escape(row['clean_key']) + r'\b', s_clean):
            return pd.Series([float(row['rank']), float(row['cores'])], index=['CPU_Rank', 'CPU_Cores'])
            
    # Tier 2: Generic Family Fallback using CpuList medians
    for keywords, med_rank, med_cores in family_fallbacks:
        if any(k in s for k in keywords):
            return pd.Series([float(med_rank), float(med_cores)], index=['CPU_Rank', 'CPU_Cores'])
            
    return pd.Series([2500.0, 2.0], index=['CPU_Rank', 'CPU_Cores'])








