#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_homozygosity.py
-------------------------------------------------------
Cel:
• Przetwarza wyniki homozygotyczności (ROH) z plików .txt.
• Dla każdego osobnika oblicza średni poziom homozygotyczności.
• Łączy te dane z rodowodem (plik Excel z datami urodzenia).
• Zapisuje finalną tabelę do pliku .parquet do dalszej analizy.

Uruchamianie:
• Bez argumentów     ➜ zapis do katalogu results/
• Z  --only out_17   ➜ zapis do katalogu results_out_17/
"""

# ── importy ──────────────────────────────────────────────────────────────
from pathlib import Path
import pandas as pd, re, logging, sys, argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from typing import Optional

# ── ścieżki do danych ─────────────────────────────────────────────────────
BASE_DIR = Path("/media/raid/home/kpatan/slim/homozygosity")  # katalog główny projektu
DATA_DIR = BASE_DIR / "output_files"                          # katalog z plikami TXT (ROH)
PED_FILE = BASE_DIR / "s1_rodowod.xlsx"                        # plik z rodowodem

# ─────────────────────────────────────────────────────────────────────────
# Funkcja: mean_homozygosity
# • Wczytuje jeden plik .txt z ROH
# • Oblicza średnią homozygotyczność dla osobnika
# • Wyciąga ID osobnika z nazwy pliku
# ─────────────────────────────────────────────────────────────────────────
def mean_homozygosity(txt: Path) -> dict:
    df = pd.read_csv(
        txt, sep="\t", skiprows=1,
        names=["Window_center", "Homozygosity"],
        dtype={"Window_center": "int32", "Homozygosity": "float32"},
        engine="c"
    )
    return {
        "ID": int(re.search(r"output_(\d+)\.txt", txt.name)[1]),  # ID z nazwy pliku
        "avg_hom": df["Homozygosity"].mean(),                     # średnia homozygotyczność
        "Folder": txt.parent.name,                                # folder, np. out_17
    }

# ─────────────────────────────────────────────────────────────────────────
# Funkcja: collect
# • Przeszukuje foldery out_*/ z plikami TXT
# • Przetwarza pliki równolegle (parallel processing)
# • Zwraca tabelę z ID, avg_hom, Folder
# ─────────────────────────────────────────────────────────────────────────
def collect(workers: int, only: Optional[str]) -> pd.DataFrame:
    pattern = f"{only}/*.txt" if only else "out_*/*.txt"
    files   = list(DATA_DIR.glob(pattern))
    logging.info("Znaleziono %d plików TXT (wzorzec: %s)", len(files), pattern)

    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(mean_homozygosity, p): p for p in files}
        for fut in tqdm(as_completed(futs),
                        total=len(futs),
                        desc="Parsuję TXT", unit="plk",
                        file=sys.stdout):
            rows.append(fut.result())
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────
# Funkcja główna
# • Obsługa argumentów
# • Łączenie ROH z rodowodem
# • Zapis do pliku wynikowego
# ─────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24,
                    help="liczba procesów równoległych")
    ap.add_argument("--only", help="np. out_17  ➜ zapis do results_out_17/")
    args = ap.parse_args()

    # Ustalenie katalogu wynikowego
    out_dir = BASE_DIR / (f"results_{args.only}" if args.only else "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Konfiguracja logowania
    log_file = out_dir / "df_all.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)8s  %(message)s",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(log_file, mode="w")],
        force=True)

    logging.info("START  — katalog wynikowy: %s", out_dir)
    
    # Agregacja wyników homozygotyczności
    df_hom = collect(args.workers, args.only)
    logging.info("df_hom  %s×%s", *df_hom.shape)

    # Wczytanie i przygotowanie rodowodu
    ped = (pd.read_excel(PED_FILE, usecols=["No.", "Date of birth"])
             .rename(columns={"No.": "ID"}))
    ped = ped[ped.ID.isin(df_hom.ID)]
    ped["Year"]   = pd.to_datetime(ped["Date of birth"]).dt.year
    ped["Decade"] = (ped.Year // 10) * 10
    ped["FiveYr"] = (ped.Year // 5)  * 5

    # Połączenie ROH z rodowodem
    df_final = (df_hom
                .merge(ped[["ID","Year","Decade","FiveYr"]], on="ID", how="left")
                .sort_values(["Folder","ID"]))

    # Zapis do pliku .parquet
    out_name = "homozyg_single.parquet" if args.only else "homozyg_100rep.parquet"
    out_file = out_dir / out_name
    df_final.to_parquet(out_file, index=False)

    logging.info("ZAPIS  %s  (%.2f MB)", out_file, out_file.stat().st_size/2**20)
    logging.info("KONIEC — OK")

if __name__ == "__main__":
    main()
