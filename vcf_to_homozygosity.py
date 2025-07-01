#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vcf_to_homozygosity.py
────────────────────────────────────────────────────────────────
Cel:
• Wczytuje plik VCF (np. z symulacji SLiM/py_ped_sim)
• Dzieli chromosom na przesuwające się okna (sliding windows)
• Dla każdego osobnika liczy odsetek homozygotycznych pozycji w każdym oknie
• Zapisuje wynik do osobnych plików tekstowych: output_<ID>.txt

Format wyjściowy:
Window_center    Homozygosity

Przykład uruchomienia:
python vcf_to_homozygosity.py finalout_17_genomes.vcf.gz out_17 200000 10000
"""

import sys
import os
from cyvcf2 import VCF

def count_homozygosity_sliding_windows(
    vcf_file, 
    output_dir="output_files", 
    window_size=200000, 
    step_size=10000, 
    default_length=106_932_631
):
    # Upewnij się, że katalog wyjściowy istnieje
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    vcf = VCF(vcf_file)
    chrom_name = vcf.seqnames[0]

    # Pobranie długości chromosomu (jeśli nie podano w nagłówku, użyj default_length)
    try:
        chrom_length = vcf.seqlens[0]
    except AttributeError:
        chrom_length = default_length

    sample_names = vcf.samples  # Lista nazw osobników w VCF

    # Utwórz pliki wyjściowe z nagłówkiem dla każdego osobnika
    for sample in sample_names:
        filename = os.path.join(output_dir, f"output_{sample}.txt")
        with open(filename, "w") as fh:
            fh.write("Window_center\tHomozygosity\n")

    # Przesuwanie się po genomie oknami (sliding window)
    for start in range(0, chrom_length, step_size):
        end = min(start + window_size, chrom_length)
        center = (start + end) // 2

        # Liczniki dla każdego osobnika
        homozygous_counts = {sample: 0 for sample in sample_names}
        total_counts = {sample: 0 for sample in sample_names}

        # Iteracja po wariantach w bieżącym oknie
        for variant in vcf(f"{chrom_name}:{start}-{end}"):
            for idx, genotype in enumerate(variant.genotypes):
                # Pomijamy brakujące dane (np. ./.)
                if genotype[0] < 0 or genotype[1] < 0:
                    continue
                sample = sample_names[idx]
                total_counts[sample] += 1
                if genotype[0] == genotype[1]:
                    homozygous_counts[sample] += 1

        # Oblicz homozygotyczność i dopisz do pliku
        for sample in sample_names:
            if total_counts[sample] > 0:
                homozygosity = homozygous_counts[sample] / total_counts[sample]
            else:
                homozygosity = 0
            filename = os.path.join(output_dir, f"output_{sample}.txt")
            with open(filename, "a") as fh:
                fh.write(f"{center}\t{homozygosity:.4f}\n")

# ── Uruchamianie z linii poleceń ─────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vcf_to_homozygosity_windows.py <vcf_file> [output_dir] [window_size] [step_size]")
        sys.exit(1)

    vcf_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else "output_files"
    window_size = int(sys.argv[3]) if len(sys.argv) >= 4 else 200000
    step_size = int(sys.argv[4]) if len(sys.argv) >= 5 else 10000

    count_homozygosity_sliding_windows(vcf_file, output_dir, window_size, step_size)
