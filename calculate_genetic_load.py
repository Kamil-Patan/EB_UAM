#!/usr/bin/env python3
"""
calculate_genetic_load.py
─────────────────────────────────────────────────────────────
Cel:
• Przetwarza zestaw plików VCF (.vcf.gz) wygenerowanych przez SLiM/py_ped_sim.
• Identyfikuje mutacje m2 (szkodliwe) na podstawie pozycji z pliku tekstowego.
• Dla każdej osoby oblicza obciążenie genetyczne:
    – suma współczynników selekcji dla homozygot i heterozygot
    – liczba mutacji
• Dane łączone są z rokiem urodzenia (Year) z ROH
• Wynik to jeden plik .parquet (np. part1.parquet), który później scala merge_mut.py

Uruchamianie:
python vcf_to_genetic_load.py --start 1 --end 50 --out part1.parquet
"""

# ── Importy ─────────────────────────────────────────────────────────────
import pandas as pd
import cyvcf2
import os
import gzip
import shutil
import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile

# ── Argumenty wejściowe ─────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Batch VCF processing for selection coefficients.")
parser.add_argument("--start", type=int, required=True, help="Start folder ID.")
parser.add_argument("--end", type=int, required=True, help="End folder ID (inclusive).")
parser.add_argument("--out", type=str, required=True, help="Output Parquet file name.")
args = parser.parse_args()

# ── Ścieżki ─────────────────────────────────────────────────────────────
BASE_DIR = Path("/media/raid/home/kpatan/slim/homozygosity")
VCF_DIR = Path("/media/raid/home/kpatan/slim/py_ped_sim")
MUTATION_DATA = Path("/media/raid/home/kpatan/slim/mutations_output_final_m2.txt")
YEAR_DATA = BASE_DIR / "results" / "homozyg_100rep.parquet"
OUT_PARQUET = BASE_DIR / "results" / args.out

# ── Wczytanie danych pomocniczych ──────────────────────────────────────
# Informacje o mutacjach m2 i ich współczynnikach selekcyjnych
mutation_df = pd.read_csv(
    MUTATION_DATA, sep="\t", 
    names=["Mutation_ID", "Position", "Type", "selection_coef"]
)
mutation_df["Position"] = mutation_df["Position"].astype(int)

# Informacje o latach urodzenia osobników z ROH
year_data = pd.read_parquet(YEAR_DATA)[["ID", "Year"]].drop_duplicates()
year_data["ID"] = year_data["ID"].astype(str)  # identyfikatory z VCF są tekstowe

# ── Główna pętla przetwarzania folderów ────────────────────────────────
all_results = []

for folder_id in range(args.start, args.end + 1):
    vcf_file = VCF_DIR / f"finalout_{folder_id}_genomes.vcf.gz"
    if not vcf_file.exists():
        print(f"[!] Plik nie istnieje: {vcf_file}")
        continue

    try:
        # Rozpakuj VCF do tymczasowego pliku
        with NamedTemporaryFile(delete=False, suffix=".vcf") as temp_vcf:
            temp_vcf_path = temp_vcf.name
        with gzip.open(vcf_file, 'rb') as f_in, open(temp_vcf_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        # Wczytaj VCF
        vcf = cyvcf2.VCF(temp_vcf_path)
        for variant in vcf:
            corrected_position = variant.POS
            # Znajdź pasującą mutację m2 (uwzględnia +1 w pozycjonowaniu)
            matching_mutations = mutation_df[mutation_df["Position"] + 1 == corrected_position]
            if not matching_mutations.empty:
                selection_coef = matching_mutations.iloc[0]["selection_coef"]
                genotypes = variant.genotypes

                for i, genotype in enumerate(genotypes):
                    sample_id = vcf.samples[i]
                    gt = genotype[0] + genotype[1]  # suma alleli

                    # Homozygota szkodliwa
                    if gt == 2:
                        all_results.append({
                            "ID": sample_id,
                            "Folder": folder_id,
                            "selection_homo": 2 * selection_coef,
                            "selection_hetero": 0,
                            "mutation_count": 2
                        })
                    # Heterozygota
                    elif gt == 1:
                        all_results.append({
                            "ID": sample_id,
                            "Folder": folder_id,
                            "selection_homo": 0,
                            "selection_hetero": selection_coef,
                            "mutation_count": 1
                        })

    finally:
        # Usuń tymczasowy plik
        if os.path.exists(temp_vcf_path):
            os.remove(temp_vcf_path)

# ── Agregacja wyników ───────────────────────────────────────────────────
if not all_results:
    print("Brak pasujących mutacji.")
    sum_df = pd.DataFrame(columns=[
        "ID", "Folder", "selection_homo", "selection_hetero", 
        "mutation_count", "selection_total", "Year"
    ])
else:
    results_df = pd.DataFrame(all_results)
    sum_df = results_df.groupby(["ID", "Folder"]).agg({
        "selection_homo": "sum",
        "selection_hetero": "sum",
        "mutation_count": "sum"
    }).reset_index()
    sum_df["selection_total"] = sum_df["selection_homo"] + sum_df["selection_hetero"]

    # Dołączenie informacji o roku urodzenia
    sum_df = sum_df.merge(year_data, on="ID", how="left")

# ── Zapis do pliku .parquet ─────────────────────────────────────────────
sum_df.to_parquet(OUT_PARQUET)
print(f"[✓] Zapisano zakres {args.start}-{args.end} do: {OUT_PARQUET}")
