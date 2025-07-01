#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculate_roh_pct.py
───────────────────────────────────────────────────────────────
Cel:
• Oblicza odsetek genomu objętego ROH (Runs of Homozygosity)
  dla każdego osobnika na podstawie 100 replik/folderów (out_0–out_99).
• Dla każdego osobnika liczy średni ROH% (średni udział genomu w ROH)
• Dołącza rok urodzenia z wcześniej scalonego pliku ROH
• Zapisuje wynik do: results/roh_pct_100rep.parquet

Dane wejściowe:
• Pliki out_X/output_*.txt (z homozygotycznością w oknach)
• Plik results/homozyg_100rep.parquet (z ID i rokiem urodzenia)

Dane wyjściowe:
• Plik Parquet z kolumnami: ID, ROH_pct, Year
"""

# ── Importy ─────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import glob
import os
import argparse
from pathlib import Path

# ── Parametry genomu i progu ROH ────────────────────────────────────────
STEP_SIZE = 100_000          # długość jednego okna w bp
GENOME_LENGTH = 106_932_631  # całkowita długość analizowanego genomu
ROH_THRESHOLD = 0.9          # próg dla homozygotyczności, aby zaliczyć do ROH

# ── Ścieżki do danych ───────────────────────────────────────────────────
BASE = Path("/media/raid/home/kpatan/slim/homozygosity")
DATA_DIR = BASE / "output_files"
FULL_PARQUET = BASE / "results" / "homozyg_100rep.parquet"
OUT_PARQUET = BASE / "results" / "roh_pct_100rep.parquet"

# ── Lista folderów out_0, ..., out_99 ───────────────────────────────────
folders = [os.path.join(DATA_DIR, f"out_{i}") for i in range(100)]

# ── Lista do przechowywania wyników ─────────────────────────────────────
results = []

# ── Przetwarzanie plików output_*.txt ──────────────────────────────────
for folder in folders:
    folder_name = os.path.basename(folder)
    files = glob.glob(os.path.join(folder, "output_*.txt"))
    
    for file in files:
        fname = os.path.basename(file)
        sample_id = fname.replace("output_", "").replace(".txt", "")
        
        # Wczytanie danych: kolumna "Homozygosity" dla każdego okna
        dat = pd.read_csv(file, sep="\t", skiprows=1, names=["Window_center", "Homozygosity"])
        
        # Zlicz liczbę okien spełniających próg ROH
        num_windows_roh = (dat["Homozygosity"] >= ROH_THRESHOLD).sum()
        
        # Przelicz długość ROH i odsetek genomu
        roh_length = num_windows_roh * STEP_SIZE
        roh_pct = (roh_length / GENOME_LENGTH) * 100
        
        # Zapisz wynik
        results.append({
            "ID": sample_id,
            "Folder": folder_name,
            "ROH_pct": roh_pct
        })

# ── Konwersja do ramki danych ───────────────────────────────────────────
results_df = pd.DataFrame(results)

# ── Wczytanie pliku z ROH i rokiem urodzenia ────────────────────────────
data = pd.read_parquet(FULL_PARQUET)

# ── Uśrednienie ROH% dla każdego osobnika (100 folderów) ────────────────
results_avg = results_df.groupby("ID").agg({"ROH_pct": "mean"}).reset_index()

# ── Pobranie informacji o roku urodzenia ────────────────────────────────
year_data = data[["ID", "Year"]].drop_duplicates()

# ── Konwersja ID na string (na wypadek niespójności typów) ──────────────
results_avg["ID"] = results_avg["ID"].astype(str)
year_data["ID"] = year_data["ID"].astype(str)

# ── Połączenie ROH% z rokiem urodzenia ──────────────────────────────────
final_data = results_avg.merge(year_data, on="ID", how="left")

# ── Zapis do pliku Parquet ──────────────────────────────────────────────
OUT_PARQUET.parent.mkdir(exist_ok=True)
final_data.to_parquet(OUT_PARQUET, index=False)

print(f"Wyniki zapisano do pliku: {OUT_PARQUET}")
