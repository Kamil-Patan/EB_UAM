#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_mut_part.py
───────────────────────────────────────────────────────────────
Cel:
• Scala częściowe pliki .parquet zawierające dane o mutacjach m2 
  i obciążeniu genetycznym (genetic load), wygenerowane przez:
    ➜ vcf_to_genetic_load.py (dawniej nowamutacjatest.py)

• Każdy plik np. part1.parquet, part2.parquet, ... zawiera dane
  dla określonego zakresu folderów symulacyjnych (np. 1–50)

• Skrypt scala je w jeden zbiorczy plik:
    ➜ genetic_load_combined.parquet

Używany przed analizą obciążenia genetycznego w czasie i między osobnikami.
"""

# ── Importy ─────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

# ── Ścieżka do folderu z częściowymi plikami wynikowymi ─────────────────
folder = Path("/media/raid/home/kpatan/slim/homozygosity/results")

# ── Lista plików do scalenia ────────────────────────────────────────────
file_names = [
    "part1.parquet",
    "part2.parquet",
    "part3.parquet",
    "part4.parquet",
    "part5.parquet",
    "part6.parquet",
    "part7.parquet"
]

# ── Wczytaj każdy plik do osobnego DataFrame i połącz w jeden ──────────
dfs = [pd.read_parquet(folder / name) for name in file_names]
merged = pd.concat(dfs, ignore_index=True)

# ── Zapisz scalony zbiór danych do jednego pliku .parquet ──────────────
merged.to_parquet(folder / "genetic_load_combined.parquet")
