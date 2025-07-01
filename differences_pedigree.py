import pandas as pd

file_path_S1 = "C:/Users/kamis/Downloads/journal.pone.0277456.s001.xlsx"
file_path_EBPB = "C:/Users/kamis/OneDrive/Pulpit/EBPB_parents_20240905.xlsx"

data_S1 = pd.read_excel(file_path_S1)
data_EBPB = pd.read_excel(file_path_EBPB)

columns_of_interest = ['No.', 'Name']
subset_data_S1 = data_S1[columns_of_interest]
columns_of_interest_EBPB = ['identifier', 'name']
subset_data_data_EBPB = data_EBPB[columns_of_interest_EBPB]

# zapisanie ID i imienia z pliku S1
with open("output_S1.txt", "w", encoding="utf-8") as f:
    for row in subset_data_S1.itertuples(index=False):
        f.write(f"{row._0} {row.Name}\n")

print("IDs and Names have been written to output_S1.txt")

# zapisanie Identifiera(jako id) i imienia z pliku EBPB
with open("output_EBPB.txt", "w", encoding="utf-8") as f:
    for row in subset_data_data_EBPB.itertuples(index=False):
        f.write(f"{row.identifier} {row.name}\n")

print("IDs and Names have been written to output_EBPB.txt")


import re

def alphanumeric_sort_key(item):
    """
    This function splits a string into a list of integers and strings so that sorting happens 
    numerically for numbers and lexicographically for non-numeric parts.
    """
    # Split the string into parts: numeric and non-numeric
    parts = re.split('(\d+)', item)
    return [int(part) if part.isdigit() else part.lower() for part in parts]

with open("output_S1.txt", "r", encoding="utf-8") as file_S1:
    data_S1_set = set(line.strip().lower() for line in file_S1)

with open("output_EBPB.txt", "r", encoding="utf-8") as file_EBPB:
    data_EBPB_set  = set(line.strip().lower() for line in file_EBPB)



only_in_S1 = data_S1_set  - data_EBPB_set  
only_in_EBPB = data_EBPB_set  - data_S1_set  
common_in_both = data_S1_set  & data_EBPB_set  

# zapis bledow i podobienst do 3 plików
with open("only_in_S1.txt", "w", encoding="utf-8") as diff_file_S1:
    diff_file_S1.write("Items in output_S1.txt but not in output_EBPB.txt:\n")
    for item in sorted(only_in_S1, key=alphanumeric_sort_key):
        diff_file_S1.write(item + "\n")
    print("Items in output_S1.txt but not in output_EBPB.txt have been written to 'only_in_S1.txt'.")

with open("only_in_EBPB.txt", "w", encoding="utf-8") as diff_file_EBPB:
    diff_file_EBPB.write("Items in output_EBPB.txt (EBPB) but not in output_S1.txt:\n")
    for item in sorted(only_in_EBPB, key=alphanumeric_sort_key):
        diff_file_EBPB.write(item + "\n")
    print("Items in output_EBPB.txt (EBPB) but not in output_S1.txt have been written to 'only_in_EBPB.txt'.")

with open("common_items.txt", "w", encoding="utf-8") as diff_file_common:
    diff_file_common.write("Common items in both output_S1.txt and output_EBPB.txt:\n")
    for item in sorted(common_in_both, key=alphanumeric_sort_key):
        diff_file_common.write(item + "\n")
    print("Common items in both output_S1.txt and output_EBPB.txt have been written to 'common_items.txt'.")

# rozwiązanie problemu wartości NaN
data_S1['No.'] = data_S1['No.'].astype(str).fillna('') 
data_EBPB['identifier'] = data_EBPB['identifier'].astype(str).fillna('')

# wyciągnięcie tylko kolumny z ID
ids_S1 = data_S1['No.'].str.lower().unique()  
ids_EBPB = data_EBPB['identifier'].str.lower().unique()  

set_S1 = set(ids_S1)
set_EBPB = set(ids_EBPB)

unique_S1_ids = set_S1 - set_EBPB 
unique_EBPB_ids = set_EBPB - set_S1 
common_ids = set_S1 & set_EBPB
sorted_common_ids = sorted(common_ids, key=alphanumeric_sort_key)

with open("unique_id_S1.txt", 'w') as  uniq_S1:
    uniq_S1.write("Unique IDs in S1 (not in EBPB):\n")
    for item in sorted(unique_S1_ids, key=alphanumeric_sort_key):
        uniq_S1.write(item + '\n')
    print("Unique IDs from S1 have been written to 'unique_id_S1.txt'")


with open("unique_id_EBPB.txt", 'w') as  uniq_EBPB:
    uniq_EBPB.write("Unique IDs in EBPB (not in S1):\n")
    for item in sorted(unique_EBPB_ids, key=alphanumeric_sort_key):
        uniq_EBPB.write(item + '\n')
    print("Unique IDs from EBPB have been written to 'unique_id_EBPB.txt'")

with open("common_ids.txt", "w", encoding="utf-8") as common_ids_file:
    common_ids_file.write("Common IDs in both S1 and EBPB:\n")
    for item in sorted_common_ids:
        common_ids_file.write(item + "\n")

print("Common IDs have been written to 'common_ids.txt'.")