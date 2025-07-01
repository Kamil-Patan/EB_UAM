#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gff_to_slim.py
───────────────────────────────────────────────────────────────
Cel:
• Parsuje plik GFF3 (np. genom bydlęcy) i tworzy uproszczoną adnotację
  genomu zawierającą trzy typy regionów:
    ➤ EXON     – scalone eksony
    ➤ INTRON   – przestrzenie między eksonami
    ➤ NC       – regiony międzygenowe (intergenic)

• Na wyjściu generuje plik TXT (feature, start, end), np. do SLiM

• Wypisuje też podsumowanie liczby i długości każdego typu

Uruchamianie:
python gfftoslim4.py input.gff3 <długość chromosomu> output.txt
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Funkcje pomocnicze ──────────────────────────────────────────────────

def merge_intervals(intervals):
    """Scala przedziały, które się nachodzą lub stykają"""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1] + 1:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def compute_intergenic_intervals(gene_regions, chrom_length):
    """Zwraca regiony międzygenowe (luk między genami)"""
    intergenic = []
    if not gene_regions:
        return [(1, chrom_length)]
    gene_regions = sorted(gene_regions, key=lambda x: x[0])
    if gene_regions[0][0] > 1:
        intergenic.append((1, gene_regions[0][0] - 1))
    for i in range(len(gene_regions) - 1):
        current_end = gene_regions[i][1]
        next_start = gene_regions[i+1][0]
        if next_start > current_end + 1:
            intergenic.append((current_end + 1, next_start - 1))
    if gene_regions[-1][1] < chrom_length:
        intergenic.append((gene_regions[-1][1] + 1, chrom_length))
    return intergenic

def parse_gff3_transcripts(gff_file):
    """
    Parsuje plik GFF3 i zwraca słowniki:
    - transcripts[transcript_id] = {'start':, 'end':, 'exons': []}
    - transcript_to_gene[transcript_id] = gene_id
    """
    transcripts = {}
    transcript_to_gene = {}
    with open(gff_file) as f:
        for line in f:
            if line.startswith("#"): continue
            fields = line.strip().split("\t")
            if len(fields) < 9: continue
            feature = fields[2].lower()
            try:
                start = int(fields[3])
                end = int(fields[4])
            except ValueError:
                continue
            attributes = fields[8]

            # Transkrypty
            if feature in {"mrna", "lnc_rna"}:
                tid = gene_id = None
                for attr in attributes.split(";"):
                    if attr.startswith("ID="):
                        tid = attr.split("=")[1].split(":")[-1]
                    if attr.startswith("Parent="):
                        gene_id = attr.split("=")[1].split(":")[-1]
                if tid:
                    transcripts[tid] = {"start": start, "end": end, "exons": []}
                    transcript_to_gene[tid] = gene_id

            # Eksony
            elif feature == "exon":
                parent = None
                for attr in attributes.split(";"):
                    if attr.startswith("Parent="):
                        parent = attr.split("=")[1].split(":")[-1]
                if parent:
                    if parent not in transcripts:
                        transcripts[parent] = {"start": start, "end": end, "exons": []}
                    transcripts[parent]["exons"].append((start, end))
    return transcripts, transcript_to_gene

# ── Główna funkcja ───────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 4:
        print("Usage: python gfftoslim4.py <input.gff3> <chrom_length> <output.txt>")
        sys.exit(1)

    gff_file = sys.argv[1]
    chrom_length = int(sys.argv[2])
    output_file = sys.argv[3]

    transcripts, transcript_to_gene = parse_gff3_transcripts(gff_file)

    # Grupowanie transkryptów wg genu
    gene_dict = {}
    for tid, data in transcripts.items():
        gene_id = transcript_to_gene.get(tid, tid)
        gene = gene_dict.setdefault(gene_id, {"transcripts": [], "exons": [], "gene_start": None, "gene_end": None})
        gene["transcripts"].append(tid)
        gene["exons"].extend(data["exons"])
        gene["gene_start"] = min(gene["gene_start"] or data["start"], data["start"])
        gene["gene_end"] = max(gene["gene_end"] or data["end"], data["end"])

    # Przetwarzanie genów: scala eksony, oblicza introny
    gene_intervals = {}
    for gid, info in gene_dict.items():
        exons = info["exons"]
        if exons:
            merged_exons = merge_intervals(exons)
            introns = []
            for i in range(len(merged_exons) - 1):
                s, e = merged_exons[i][1] + 1, merged_exons[i+1][0] - 1
                if s <= e:
                    introns.append((s, e))
            gene_intervals[gid] = {
                "adj_start": merged_exons[0][0],
                "adj_end": merged_exons[-1][1],
                "merged_exons": merged_exons,
                "introns": introns
            }
        else:
            gene_intervals[gid] = {
                "adj_start": info["gene_start"],
                "adj_end": info["gene_end"],
                "merged_exons": [(info["gene_start"], info["gene_end"])],
                "introns": []
            }

    # Zbieranie przedziałów do zapisu
    intervals = []
    for info in gene_intervals.values():
        intervals.extend([("EXON", s, e) for s, e in info["merged_exons"]])
        intervals.extend([("INTRON", s, e) for s, e in info["introns"]])

    # Regiony NC (międzygenowe)
    gene_regions = [(info["adj_start"], info["adj_end"]) for info in gene_intervals.values()]
    intergenic = compute_intergenic_intervals(merge_intervals(gene_regions), chrom_length)
    intervals.extend([("NC", s, e) for s, e in intergenic])

    # Sortowanie i zapis
    intervals.sort(key=lambda x: x[1])
    with open(output_file, "w") as out:
        out.write("feature\tstart\tend\n")
        for feat, s, e in intervals:
            out.write(f"{feat}\t{s}\t{e}\n")

    # Statystyki
    exon_total = sum(e - s + 1 for feat, s, e in intervals if feat == "EXON")
    intron_total = sum(e - s + 1 for feat, s, e in intervals if feat == "INTRON")
    nc_total = sum(e - s + 1 for feat, s, e in intervals if feat == "NC")
    total_covered = exon_total + intron_total + nc_total
    print("Liczba exonów:", sum(1 for i in intervals if i[0] == "EXON"))
    print("Liczba intronów:", sum(1 for i in intervals if i[0] == "INTRON"))
    print("Liczba regionów NC:", sum(1 for i in intervals if i[0] == "NC"))
    print("Średnia długość exonu:", exon_total / max(1, sum(1 for i in intervals if i[0] == "EXON")))
    print("Średnia długość intronu:", intron_total / max(1, sum(1 for i in intervals if i[0] == "INTRON")))
    print("Procentowy udział exonów w genomie:", (exon_total / total_covered * 100), "%")
    print("Wynik zapisano do:", output_file)

if __name__ == '__main__':
    main()
