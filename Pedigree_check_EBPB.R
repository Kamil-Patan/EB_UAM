library(readxl)
library(ggroups)

file_path <- "EBPB_parents_20240905.xlsx"
data <- read_xlsx(file_path)

head(data)

# Przekształcenie danych do formatu ped (ID, SIRE, DAM, INDENTIFIER)
ped <- data.frame(
  ID = data$id,
  SIRE = ifelse(is.na(data$father_id), 0, data$father_id),
  DAM = ifelse(is.na(data$mother_id), 0, data$mother_id),
  IDENTIFIER = data$identifier
)

head(ped)

# sprawdzenie danych
pedcheck(ped)

id_list <- c(6760, 6930, 9260, 10200, 11640, 13770, 17790, 19430, 20780, 20860, 
             23620, 28090, 28920, 32290, 37180, 41710, 62090, 65840, 74320, 
             76310, 92640, 97420, 105560, 118430, 122540, 122710, 125260, 
             134260)

for (id_to_find in id_list) {
  # Przefiltrowanie wierszy, gdzie ID, SIRE lub DAM zawiera szukane ID
  result <- ped[ped$ID == id_to_find | ped$SIRE == id_to_find | ped$DAM == id_to_find, ]
  
  # Sprawdzamy, czy mamy jakieś wyniki i wypisujemy je
  if (nrow(result) > 0) {
    cat("Results for ID", id_to_find, ":\n")
    print(result)
    cat("\n\n")
  } else {
    cat("No results found for ID", id_to_find, "\n\n")
  }
}

# Używamy subset do przefiltrowania wierszy, gdzie ID występuje w liście
result <- subset(ped, ID %in% id_list)

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


# Dodanie nowej kolumny do określenia płci tam gdzie to możliwe
ped$GENDER <- 3

# określenie płci 1 jako samiec, 2 samica gdy ID występuję w kolumnie father_id/mother_id, 3 jako nieznany
ped$GENDER[ped$ID %in% ped$SIRE] <- 1
ped$GENDER[ped$ID %in% ped$DAM] <- 2

head(ped)




# 1. Liczba osobników z przynajmniej jednym brakującym rodzicem
sum_missing_either <- sum(ped$DAM == 0 | ped$SIRE == 0)

# 2. Liczba osobników z błędem: ID <= ID rodzica
sum_id_gt_parents <- nrow(incorrect_parent_child)

# 3. Liczba osobników, których ID pojawia się jako ojciec i matka
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

# 5. Wyświetlenie tabeli
print(summary_table)

# (opcjonalnie) Zapis do pliku
write.table(summary_table, file = "podsumowanie_bledow_EBPB.txt", sep = "\t", row.names = FALSE, quote = FALSE)


