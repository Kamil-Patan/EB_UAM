#!/bin/bash
for i in $(seq 1 33); do
    # Sciezka do pliku founderów dla biezacej iteracji
    file="mydata/exact_founder_input_${i}.txt"
    rm -f "${file}"
    
    # Stala lista founderów (kolejno przypisywane liczby)
    founder_numbers=(15 16 35 42 45 46 87 89 95 96 100 147)
    
    # Losowo wybieramy 12 unikalnych liczb z zakresu 0-49
    founder_nums=($(seq 0 49 | shuf -n 12))
    
    # Tworzymy plik z 12 liniami: np. "i7 15", "i2 16", ...
    for j in $(seq 0 11); do
        echo "i${founder_nums[$j]} ${founder_numbers[$j]}" >> "${file}"
    done

    # Uruchomienie symulacji pypedsim
    python run_ped_sim.py -t sim_genomes_exact -mu 0 -n mydata/mypedigree.nx -e "${file}" -v mydata/wisentinfo_slim_fil.vcf -o finalout_${i}
    
    # Kompresja wszystkich plików VCF wygenerowanych dla danego ID (finalout_<i>_*.vcf)
    gzip finalout_${i}_*.vcf
done
