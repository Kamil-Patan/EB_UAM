# EB_UAM

Computational tools for analyzing the genetic dynamics of endangered species using pedigree and genomic data.  
This repository contains Python, R, and SLiM scripts used in population genetics simulations and post-processing of results for the European bison (*Bison bonasus*).

---

## Repository structure

| File / Folder | Description |
|----------------|--------------|
| `Pedigree_check_EBPB.R`, `Pedigree_check_S1.R` | Pedigree validation for the two bison lines (EBPB – lowland, S1 – mixed). |
| `pedigree_data_comparison.R` | Comparison of pedigree structures and founder representation. |
| `gff_to_slim.py`, `analiza_gffslim.py` | Conversion and analysis of GFF3 genome annotations for SLiM input. |
| `calculate_genetic_load.py` | Calculates genetic load from simulated VCF data. |
| `calculate_roh_pct.py`, `vcf_to_homozygosity.py`, `merge_homozygosity.py` | Compute runs of homozygosity (ROH) and genome-wide homozygosity per individual. |
| `founders_sim_slim/` | Contains SLiM simulation input and output files. |
| `run_py_ped_sim_1.sh` | Example script for running inheritance simulations with `py_ped_sim`. |
| `all_plots.R` | Generates summary plots for ROH, heterozygosity, and genetic load. |

---

##  Requirements

**System:**
- Linux / macOS (recommended for SLiM and `py_ped_sim`)
- Python 3.9+
- R 4.0+
- SLiM 4.0+

**Python packages:**
- `pandas`  
- `numpy`  
- `scikit-allel`  
- `matplotlib`  
- `tqdm`

**R packages:**
- `tidyverse`  
- `ggplot2`  
- `kinship2`

**Other dependencies:**
- `py_ped_sim` – custom package for pedigree-based genetic simulations  
- Reference genome annotation file in **GFF3** format  
- Pedigree file (`.nx`) and founder list (`exact_founder_input.txt`) used as input for simulations  

---

## Author

**Kamil Patan**  
Adam Mickiewicz University in Poznań  
Faculty of Biology
