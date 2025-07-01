#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_hom_part.py
───────────────────────────────────────────────────────────────
Scalanie danych ROH z wielu symulacji (100 replik, np. out_01–out_100)

Ten skrypt:
• Wyszukuje pliki results_out_*/homozyg_single.parquet
  — Każdy z nich jest generowany wcześniej przez df_to_R.py
    uruchamiany z argumentem: --only out_X
• Scala je w jeden zbiorczy plik:
    ➜ results/homozyg_100rep.parquet

Wykorzystywany jako krok końcowy do agregacji wyników ROH
przed dalszą analizą (np. w R).
"""

import pandas as pd
from pathlib import Path
import glob

# ── Ścieżki ─────────────────────────────────────────────────────────────
BASE = Path("/media/raid/home/kpatan/slim/homozygosity")

# Szukaj plików typu: results_out_*/homozyg_single.parquet
PAT  = BASE / "results_out_*" / "homozyg_single.parquet"

# Plik wyjściowy (scalony)
OUT  = BASE / "results" / "homozyg_100rep.parquet"

# ── Znalezienie plików do scalenia ──────────────────────────────────────
paths = glob.glob(str(PAT))
print(f"Found {len(paths)} parquet parts")  # np. 100 części

# ── Wczytanie i łączenie ────────────────────────────────────────────────
# Każdy plik to dane z jednej symulacji (np. out_17)
df = pd.concat((pd.read_parquet(p) for p in paths),
               ignore_index=True)

# ── Utworzenie katalogu wyjściowego, jeśli nie istnieje ────────────────
OUT.parent.mkdir(exist_ok=True)

# ── Zapis połączonych danych ───────────────────────────────────────────
df.to_parquet(OUT, index=False)
print(f"Written merged file to {OUT} ({OUT.stat().st_size/2**20:.1f} MB)")
