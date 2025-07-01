library(readxl)
library(ggroups)

file_path <- "s1_rodowod.xlsx"
data <- read_xlsx(file_path)

head(data)

# Przekształcenie danych do formatu ped (ID, SIRE, DAM, NAME, SEX)
ped <- data.frame(
  ID = data$No.,
  SIRE = ifelse(is.na(data[["Father No."]]), 0, data[["Father No."]]),
  DAM = ifelse(is.na(data[["Mother No."]]), 0, data[["Mother No."]]),
  NAME = data$Name,
  SEX = data$Sex
)

head(ped)

# ped do py_ped
ped_py <- data.frame(
  ID = data$No.,
  SIRE = ifelse(is.na(data[["Father No."]]), 0, data[["Father No."]]),
  DAM = ifelse(is.na(data[["Mother No."]]), 0, data[["Mother No."]]),
  SEX = data$Sex
)

ped_py$PHENOTYPE <- -9

head(ped_py)

# Zapisanie danych do pliku .ped
write.table(
  ped_py, 
  file = "S1.ped", 
  sep = " ",             # Oddzielenie kolumn spacją
  row.names = FALSE,     # Bez nazw wierszy
  col.names = FALSE,     # Bez nazw kolumn (format PED tego nie wymaga)
  quote = FALSE          # Bez cudzysłowów wokół wartości
)


# sprawdzenie danych
pedcheck(ped)

# sprawdzenie obecności zduplikowanych ID
any(duplicated(ped$ID))

# suma osobników bez ID matki/ojca lub obu
sum_missing_mother <- sum(ped$DAM == 0)
sum_missing_father <- sum(ped$SIRE == 0)
sum_missing_both <- sum((ped$DAM == 0) & (ped$SIRE == 0))

# id osobników bez matki/ojca
missing_mother_ids <- ped$ID [ped$DAM == 0]
missing_father_ids <- ped$ID[ped$SIRE == 0]

# id osobników bez obu rodziców
missing_both_ids <- ped$ID[ped$DAM == 0 & ped$SIRE == 0]

# id gdzie brakuje tylko ojca/matki
missing_only_mother_ids <- ped$ID[ped$DAM == 0 & ped$SIRE != 0]
missing_only_father_ids <- ped$ID[ped$SIRE == 0 & ped$DAM != 0]

# osobniki z wyższym ID matki/ojca od siebie
incorrect_parent_child <- ped[ped$ID <= ped$DAM | ped$ID <= ped$SIRE, ]

# ID osobników pojawiających się zarówno jako ojciec i matka
common_ids <- intersect(ped$SIRE, ped$DAM)








# 1. Liczba osobników z przynajmniej jednym brakującym rodzicem
sum_missing_either <- sum(ped$DAM == 0 | ped$SIRE == 0)

# 2. Liczba osobników z błędem: ID <= SIRE lub DAM
sum_id_gt_parents <- nrow(incorrect_parent_child)

# 3. Liczba osobników, których ID pojawia się zarówno jako SIRE, jak i DAM
# (wyklucz ID = 0)
common_ids_no_zero <- common_ids[common_ids != 0]
sum_id_as_sire_and_dam <- length(common_ids_no_zero)

# 4. Budowa zbiorczej tabeli
summary_table <- data.frame(
  Typ_błędu = c(
    "Brak ID matki",
    "Brak ID ojca",
    "Brak ID obojga rodziców",
    "Brak przynajmniej jednego rodzica",
    "ID mniejsze/równe ID rodzica",
    "ID występuje jako SIRE i DAM"
  ),
  Liczba_osobników = c(
    sum_missing_mother,
    sum_missing_father,
    sum_missing_both,
    sum_missing_either,
    sum_id_gt_parents,
    sum_id_as_sire_and_dam
  )
)

# Wyświetlenie tabeli
print(summary_table)

# (opcjonalnie) Zapis do pliku CSV lub TXT
write.table(summary_table, file = "podsumowanie_bledow_S1.txt", sep = "\t", row.names = FALSE, quote = FALSE)
# lub:
# write.csv(summary_table, file = "podsumowanie_bledow_S1.csv", row.names = FALSE)


