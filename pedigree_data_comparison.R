library(dplyr)
library(readxl)
library(ggroups)

file_path_S1 <- "s1_rodowod.xlsx"
data_S1 <- read_xlsx(file_path_S1)

#usuniecie zbędnych kolumn
data_S1_clean <- data_S1[, -c(4,5,7,9,10,11,12,13,14,15)]

head(data_S1)
head(data_S1_clean)

# Przekształcenie danych do formatu ped (ID, SIRE, DAM, NAME, SEX)
ped_S1 <- data.frame(
  ID = data_S1_clean$No.,
  SIRE = ifelse(is.na(data_S1_clean[["Father No."]]), 0, data_S1_clean[["Father No."]]),
  DAM = ifelse(is.na(data_S1_clean[["Mother No."]]), 0, data_S1_clean[["Mother No."]]),
  NAME = data_S1_clean$Name,
  SEX = data_S1_clean$Sex
)


head(ped_S1)

file_path_EBPB <- "EBPB_parents_20240905.xlsx"
data_EBPB <- read_xlsx(file_path_EBPB)

head(data_EBPB)

# Przekształcenie danych do formatu ped (ID, SIRE, DAM, INDENTIFIER) oraz dzielimy ID przez 10 aby porównać z plikiem S1
ped_EBPB <- data.frame(
  ID = data_EBPB$id / 10,
  SIRE = ifelse(is.na(data_EBPB$father_id), 0, data_EBPB$father_id)  / 10,
  DAM = ifelse(is.na(data_EBPB$mother_id), 0, data_EBPB$mother_id)  / 10,
  IDENTIFIER = data_EBPB$identifier
)

head(ped_EBPB)

# Łączymy oba pliki na podstawie wspólnego ID
merged_ped <- merge(ped_S1[, c("ID", "SIRE", "DAM")], ped_EBPB[, c("ID", "SIRE", "DAM")], 
                    by = "ID", 
                    suffixes = c("_ped_S1", "_ped_EBPB"))

head(merged_ped)

merged_ped$Mismatch_Type <- ifelse(
  merged_ped$SIRE_ped_S1 != merged_ped$SIRE_ped_EBPB & merged_ped$DAM_ped_S1 != merged_ped$DAM_ped_EBPB, "BOTH",
  ifelse(merged_ped$SIRE_ped_S1 != merged_ped$SIRE_ped_EBPB, "SIRE",
         ifelse(merged_ped$DAM_ped_S1 != merged_ped$DAM_ped_EBPB, "DAM", "MATCH"))
)

# Filtrujemy rekordy, gdzie występuje niezgodność wraz z typem niezgodności
inconsistencies <- merged_ped[merged_ped$Mismatch_Type != "MATCH", ]

# Zapisanie wyniku do pliku txt
write.table(inconsistencies, file = "inconsistencies_output_R.txt", sep = "\t", row.names = FALSE, quote = FALSE)


#### WSPÓLNE ID ROZNE NAME

# wczytanie pliku z listą wspólnych ID dla obu rodowodów
commons_ids <- read.delim("common_ids.txt")
names(commons_ids)[1] <- "ID" 

#filtrowanie wpólnych ID
S1_common_id <- data_S1_clean %>% filter(No. %in% commons_ids$ID)
EBPB_common_id <- data_EBPB %>% filter(identifier %in% commons_ids$ID)

# łączenie plików na podstawie kolumny ID 
names(EBPB_common_id)[2] <- "ID"
names(S1_common_id)[2] <- "ID"
names(EBPB_common_id)[1] <- "id_from_page"
merged_data_ids <- merge(S1_common_id, EBPB_common_id, by = "ID")

# Dodanie nowej kolumny, która zwraca różnice w Name
merged_data_ids <- merged_data_ids %>%
  mutate(Different = if_else(is.na(Name) | is.na(name) | (tolower(Name) != tolower(name)), TRUE, FALSE))

different_rows <- merged_data_ids %>% filter(Different == TRUE)

# Zapisanie wyniku do pliku txt
write.table(different_rows, file = "common_ids_with_different_Name.txt", sep = "\t", row.names = FALSE, quote = FALSE)


### WPSOLNE ID ROZNE ID RODZICOW

# Podzielenie id z kolumn father/mother ID z pliku EBPB do porownania z S1
merged_data_ids_divided <- merged_data_ids %>%
  mutate(
    father_id = father_id / 10,
    mother_id = mother_id / 10,
    father_id = coalesce(father_id, 0),
    mother_id = coalesce(mother_id, 0)
  )

#sprawdzenie identycznosci id rodzicow
merged_data_ids_divided$Mismatch_Type <- ifelse(
  merged_data_ids_divided$`Father No.` != merged_data_ids_divided$father_id & merged_data_ids_divided$`Mother No.` != merged_data_ids_divided$mother_id, "BOTH",
  ifelse(merged_data_ids_divided$`Father No.` != merged_data_ids_divided$father_id, "SIRE",
         ifelse(merged_data_ids_divided$`Mother No.` != merged_data_ids_divided$mother_id, "DAM", "MATCH"))
)

# Filtrujemy rekordy, gdzie występuje niezgodność wraz z typem niezgodności
inconsistencies_devided <- merged_data_ids_divided[merged_data_ids_divided$Mismatch_Type != "MATCH", ]

# Zapisanie wyniku do pliku txt
write.table(inconsistencies_devided, file = "common_id_different_parents", sep = "\t", row.names = FALSE, quote = FALSE)




# Liczba wszystkich niezgodności
total_differences <- nrow(inconsistencies)

# Liczba niezgodności z podziałem na typ
difference_summary <- table(inconsistencies$Mismatch_Type)

# Przekształcenie do ramki danych dla czytelnego eksportu lub wykresu
difference_df <- as.data.frame(difference_summary)
colnames(difference_df) <- c("Mismatch_Type", "Count")

# Wyświetlenie wyników
print(paste("Liczba wszystkich niezgodności:", total_differences))
print(difference_df)

# Liczba różnic w imionach (czyli TRUE w kolumnie Different)
name_mismatches <- sum(merged_data_ids_divided$Different, na.rm = TRUE)

# Wyświetlenie wyniku
print(paste("Liczba różnic w imionach między rodowodami:", name_mismatches))








