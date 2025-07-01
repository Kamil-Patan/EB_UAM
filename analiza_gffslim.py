#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analiza_gffslim.py
───────────────────────────────────────────────────────────────
Cel:
• Wczytuje plik wygenerowany przez gfftoslim4.py (feature start end)
• Zlicza liczbę regionów każdego typu (EXON, INTRON, NC)
• Oblicza średnie długości i procentowy udział
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def merge_intervals(intervals):
    """Scala nakładające się lub przylegające przedziały"""
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged

def analyze_file(filename):
    exon_count = intron_count = nc_count = 0
    exon_total = intron_total = nc_total = 0
    intervals = []

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("feature"): continue
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            feature = parts[0].upper()
            try:
                start, end = int(parts[1]), int(parts[2])
            except ValueError:
                continue
            intervals.append((start, end))
            length = end - start + 1
            if feature == "EXON":
                exon_count += 1
                exon_total += length
            elif feature == "INTRON":
                intron_count += 1
                intron_total += length
            elif feature == "NC":
                nc_count += 1
                nc_total += length

    merged = merge_intervals(intervals)
    total_length = sum(e - s + 1 for s, e in merged)
    print("Liczba exonów:", exon_count)
    print("Liczba intronów:", intron_count)
    print("Liczba regionów NC:", nc_count)
    print("Średnia długość exonu:", exon_total / max(1, exon_count))
    print("Średnia długość intronu:", intron_total / max(1, intron_count))
    print("Średnia długość NC:", nc_total / max(1, nc_count))
    print("Procent EXON:", exon_total / total_length * 100 if total_length else 0, "%")
    print("Procent INTRON:", intron_total / total_length * 100 if total_length else 0, "%")
    print("Procent NC:", nc_total / total_length * 100 if total_length else 0, "%")
    print("Łączna długość regionu:", total_length)

def main():
    if len(sys.argv) != 2:
        print("Użycie: python analiza_gff.py <plik.txt>")
        sys.exit(1)
    analyze_file(sys.argv[1])

if __name__ == '__main__':
    main()
