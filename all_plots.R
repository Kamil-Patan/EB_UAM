library(arrow)
library(dplyr)
library(ggplot2)
library(ggridges)
library(kinship2)
library(tidyr)
library(readxl)

# Wczytanie danych
avg <- read_parquet("homozyg_100rep.parquet")
roh <- read_parquet("roh_pct_100rep.parquet")
selection <- read_parquet("C:/Users/kamis/OneDrive/Pulpit/genetic_load_combined.parquet")
ped_data <- read.table("C:/Users/kamis/OneDrive/Pulpit/praca żubry/PEDIGREE/pyped_rodowod",
                       header = FALSE, stringsAsFactors = FALSE,
                       col.names = c("FID", "IID", "FATHER", "MOTHER", "SEX", "PHENO"))

# Przetwarzanie danych
# Średnia homozygotyczność i FROH
avg_by_id <- avg %>%
  group_by(ID, Year) %>%
  summarise(Avg_Hom = mean(avg_hom, na.rm = TRUE), .groups = "drop")

roh_by_id <- roh %>%
  group_by(ID, Year) %>%
  summarise(FROH = mean(ROH_pct, na.rm = TRUE), .groups = "drop") %>%
  mutate(Decade = floor(Year / 10) * 10)

# Średnie dla selection
selection_avg <- selection %>%
  group_by(ID) %>%
  summarise(
    mean_selection_total = mean(selection_total, na.rm = TRUE),
    mean_selection_homo = mean(selection_homo, na.rm = TRUE),
    mean_selection_hetero = mean(selection_hetero, na.rm = TRUE),
    mean_mutation_count = mean(mutation_count, na.rm = TRUE),
    Year = first(Year),
    Decade = floor(first(Year) / 10) * 10
  ) %>%
  mutate(
    abs_mean_selection_total = abs(mean_selection_total),
    abs_mean_selection_homo = abs(mean_selection_homo),
    abs_mean_selection_hetero = abs(mean_selection_hetero)
  )

# Przetworzenie rodowodu i inbredu
ped_data <- ped_data %>%
  mutate(
    FATHER = ifelse(FATHER <= 0, NA, FATHER),
    MOTHER = ifelse(MOTHER <= 0, NA, MOTHER),
    SEX = ifelse(SEX == 0, 2, ifelse(SEX %in% c(1, 2), SEX, NA))
  )

ped <- pedigree(id = ped_data$IID, dadid = ped_data$FATHER, momid = ped_data$MOTHER, sex = ped_data$SEX)
inbreed_data <- data.frame(ID = as.character(ped$id), F = 2 * diag(kinship(ped)) - 1)

combined <- roh_by_id %>%
  mutate(ID = as.character(ID), froh = FROH / 100) %>%
  inner_join(inbreed_data, by = "ID") %>%
  filter(!is.na(F), !is.na(froh), !is.na(Year)) %>%
  mutate(F_scaled = F * 100)

# Funkcja do tworzenia wspólnego stylu wykresów
theme_custom <- function(base_size = 15) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.title = element_text(hjust = 0.5, size = 18, face = "bold"),
      axis.title.x = element_text(size = 40),
      axis.title.y = element_text(size = 40),
      axis.text.x = element_text(size = 28),  # <-- to dodajesz
      axis.text.y = element_text(size = 28),  # <-- i to też
      panel.grid.major = element_line(color = "grey", linetype = "dashed"),
      panel.grid.minor = element_blank()
    )
}


# Wykres 1: Homozygotyczność w czasie
p1 <- ggplot(avg_by_id, aes(x = Year, y = Avg_Hom)) +
  geom_point(size = 0.5, alpha = 0.2, color = "black") +
  geom_smooth(method = "loess", color = "red", se = TRUE, linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(x = "Rok Urodzenia", y = "Średnia Homozygotyczność") +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),  # <- teraz 2020 będzie na pewno
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom()


# Wykres 2: FROH w czasie
p2 <- ggplot(roh_by_id, aes(x = Year, y = FROH)) +
  geom_point(size = 0.5, alpha = 0.2, color = "black") +
  geom_smooth(method = "loess", color = "red", se = TRUE, linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(x = "Rok Urodzenia", y = "FROH [%]") +
  scale_y_continuous(limits = c(0, 100)) +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),  # <- teraz 2020 będzie na pewno
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom()

# Wykres 3: Rozkład FROH w dekadach
selected_decades <- c("1930", "1950", "1970", "2000", "2020")
filtered_results <- roh_by_id %>%
  filter(Decade %in% as.numeric(selected_decades)) %>%
  mutate(Decade = factor(Decade, levels = selected_decades))

p3 <- ggplot(filtered_results, aes(x = FROH, y = Decade)) +
  geom_density_ridges(fill = "lightblue", color = "black", alpha = 0.7, scale = 0.9, bandwidth = 3, linewidth = 0.5) +
  labs(x = expression("FROH [%]"), y = "Dekada") +
  scale_x_continuous(limits = c(0, 100), breaks = seq(0, 100, by = 25)) +
  theme_custom() +
  theme(legend.position = "none", plot.margin = margin(10, 10, 10, 10))
print(p3)

# Wykresy dla obciążenia genetycznego
# Wykres 4: Obciążenie genetyczne (total, homo, hetero)
df_long <- selection_avg %>%
  pivot_longer(cols = starts_with("abs_mean_selection"), names_to = "Selection_Type", values_to = "Value") %>%
  mutate(Selection_Type = gsub("abs_mean_selection_", "", Selection_Type))

p4 <- ggplot(df_long, aes(x = Year, y = Value, color = Selection_Type, fill = Selection_Type)) +
  geom_smooth(method = "loess", se = TRUE, linewidth = 1.2, alpha = 0.3) +
  scale_color_manual(
    values = c("total" = "blue", "homo" = "red", "hetero" = "green"),
    labels = c("total" = "Całkowite", "homo" = "Homozygotyczne", "hetero" = "Heterozygotyczne")
  ) +
  scale_fill_manual(
    values = c("total" = "lightblue", "homo" = "pink", "hetero" = "lightgreen"),
    labels = c("total" = "Całkowite", "homo" = "Homozygotyczne", "hetero" = "Heterozygotyczne")
  ) +
  labs(
    x = "Rok",
    y = "Obciążenie Genetyczne"
  ) +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom() +
  theme(
    legend.position = "bottom",
    legend.title = element_blank(),
    legend.text = element_text(size = 28)
  )


# Wykres 5: Liczba mutacji
p5 <- ggplot(selection_avg, aes(x = Year, y = mean_mutation_count)) +
  geom_point(size = 0.5, alpha = 0.3, color = "black") +
  geom_smooth(method = "loess", color = "red", se = TRUE, linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(
    x = "Rok",
    y = "Liczba Mutacji"
  ) +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom()


# Wykres 6: Ekstremalne obciążenie genetyczne (największe)
extreme_individuals <- selection_avg %>%
  group_by(Year) %>%
  arrange(abs_mean_selection_total) %>%
  slice_head(n = 3) %>%
  bind_rows(
    selection_avg %>%
      group_by(Year) %>%
      arrange(desc(abs_mean_selection_total)) %>%
      slice_head(n = 3)
  ) %>%
  arrange(Year, abs_mean_selection_total)

max_load <- extreme_individuals %>%
  group_by(Year) %>%
  filter(abs_mean_selection_total >= sort(abs_mean_selection_total, decreasing = TRUE)[min(3, n())]) %>%
  ungroup()

min_load <- extreme_individuals %>%
  group_by(Year) %>%
  filter(abs_mean_selection_total <= sort(abs_mean_selection_total)[min(3, n())]) %>%
  ungroup()

p6 <- ggplot(max_load, aes(x = Year, y = abs_mean_selection_total)) +
  geom_point(size = 1.5, color = "darkred", alpha = 0.5) +
  geom_smooth(method = "loess", color = "darkred", se = TRUE,
              linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(x = "Rok", y = "Średnie Obciążenie") +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom()



# Wykres 7: Ekstremalne obciążenie genetyczne (najmniejsze)
p7 <- ggplot(min_load, aes(x = Year, y = abs_mean_selection_total)) +
  geom_point(size = 1.5, color = "darkgreen", alpha = 0.5) +
  geom_smooth(method = "loess", color = "darkgreen", se = TRUE,
              linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(x = "Rok", y = "Średnie Obciążenie") +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  theme_custom()


# Wykresy dla F vs FROH
correlation <- cor(combined$F, combined$froh)
p8 <- ggplot(combined, aes(x = F, y = froh)) +
  geom_point(size = 0.5, alpha = 0.3, color = "darkgreen") +
  geom_smooth(method = "lm", se = TRUE, color = "red", linewidth = 1.2, fill = "grey70", alpha = 0.3) +
  labs(
    x = "Inbred (F)",
    y = "FROH"
  ) +
  theme_custom()


p9 <- ggplot(combined, aes(x = Year)) +
  geom_smooth(aes(y = FROH, color = "FROH [%]", fill = "FROH [%]"),
              method = "loess", se = TRUE, linewidth = 1.2) +
  geom_smooth(aes(y = F_scaled, color = "Inbred [F]", fill = "Inbred [F]"),
              method = "loess", se = TRUE, linewidth = 1.2, linetype = "dashed") +
  scale_y_continuous(
    name = "FROH [%]",
    sec.axis = sec_axis(~ . / 100, name = "Inbred [F]")
  ) +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0))
  ) +
  scale_color_manual(
    values = c("FROH [%]" = "red", "Inbred [F]" = "blue"),
    name = "Zmienna"
  ) +
  scale_fill_manual(
    values = c("FROH [%]" = "grey70", "Inbred [F]" = "lightblue"),
    name = "Zmienna"
  ) +
  labs(x = "Rok Urodzenia") +
  theme_custom() +
  theme(
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.title = element_text(size = 32),
    legend.text = element_text(size = 28),
    legend.background = element_rect(fill = "white", color = "black"),
    axis.title.y.right = element_text(size = 40),
    axis.title.y.left = element_text(size = 40),
    axis.text = element_text(size = 28)
  )

# Wyodrębnienie linii rodowodowych
s1_rodowod <- read_excel("PEDIGREE/s1_rodowod.xlsx")
ped_data <- read.table("C:/Users/kamis/OneDrive/Pulpit/praca żubry/PEDIGREE/pyped_rodowod",
                       header = FALSE, stringsAsFactors = FALSE,
                       col.names = c("FID", "IID", "FATHER", "MOTHER", "SEX", "PHENO"))

s1_rodowod <- s1_rodowod %>%
  mutate(lineage = case_when(
    lineage2 == 1 ~ "nizina",
    `lineage 1` == 1 ~ "nizinno-kaukaska",
    TRUE ~ "brak danych"
  ))

ped_data <- ped_data %>%
  mutate(IID = as.character(IID))

s1_rodowod <- s1_rodowod %>%
  mutate(`No.` = as.character(`No.`))

ped_data_z_linia <- ped_data %>%
  left_join(s1_rodowod %>% select(`No.`, lineage), by = c("IID" = "No.")) %>%
  mutate(IID = as.character(IID))

roh_with_lineage <- roh_by_id %>%
  mutate(ID = as.character(ID)) %>%
  left_join(ped_data_z_linia %>% select(IID, lineage), by = c("ID" = "IID")) %>%
  filter(lineage %in% c("nizinno-kaukaska", "nizina"), !is.na(FROH), !is.na(Year))

# Wykres 10: FROH wg linii genetycznej w czasie
p10 <- ggplot(roh_with_lineage, aes(x = Year, y = FROH, color = lineage)) +
  geom_point(size = 0.8, alpha = 0.3) +
  geom_smooth(method = "loess", se = TRUE, linewidth = 1.2) +
  labs(
    x = "Rok urodzenia",
    y = "FROH [%]",
    color = "Linia"
  ) +
  scale_y_continuous(limits = c(0, 100)) +
  scale_x_continuous(
    limits = c(1900, 2020),
    breaks = c(1900, 1925, 1950, 1975, 2000, 2020),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  scale_color_manual(
    values = c("nizina" = "#e41a1c", "nizinno-kaukaska" = "#377eb8")
  ) +
  theme_custom() +
  theme(
    legend.position = c(0.02, 0.94),
    legend.justification = c(0, 1),
    legend.text = element_text(size = 28),
    legend.title = element_text(size = 32),
    legend.background = element_rect(fill = "white", color = "black")
  )