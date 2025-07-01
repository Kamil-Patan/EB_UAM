import pandas as pd

# Wczytaj dane rodowodu
pedigree = pd.read_csv(
    "C:/Users/kamis/OneDrive/Pulpit/praca żubry/S1.ped",
    sep=r'\s+',
    names=["ID", "SIRE", "DAM", "SEX", "PHENOTYPE"]
)

# Lista założycieli
founders = {15, 16, 35, 42, 45, 46, 87, 89, 95, 96, 100, 147}

# Funkcja do sprawdzania potomków z użyciem memoizacji
def is_descendant_memoized(ind_id, ped, founders, memo):
    if ind_id in memo:  # Jeśli wynik dla danego ID już istnieje
        return memo[ind_id]

    # Jeśli osobnik jest założycielem, zwracamy True
    if ind_id in founders:
        memo[ind_id] = True
        return True

    # Pobierz rodziców osobnika
    parents = ped.loc[ped['ID'] == ind_id, ['SIRE', 'DAM']].values.flatten()

    # Jeśli brak rodziców (SIRE lub DAM = 0), osobnik jest nieprawidłowy
    if any(parent == 0 for parent in parents):
        memo[ind_id] = False
        return False

    # Rekurencyjnie sprawdź oboje rodziców
    if all(parent != 0 and is_descendant_memoized(parent, ped, founders, memo) for parent in parents):
        memo[ind_id] = True
        return True

    # Jeśli którykolwiek rodzic nie spełnia warunków, osobnik jest nieprawidłowy
    memo[ind_id] = False
    return False

# Memoizacja
descendant_memo = {}

# Przefiltruj osobniki wywodzące się od założycieli
valid_individuals = [
    ind for ind in pedigree["ID"] if is_descendant_memoized(ind, pedigree, founders, descendant_memo)
]

# Utwórz przefiltrowany rodowód
filtered_pedigree = pedigree[pedigree["ID"].isin(valid_individuals)]

# Zapisz wynik
filtered_pedigree.to_csv("przefiltrowany_rodowod_v4.ped", sep=" ", index=False, header=False)
print("Przefiltrowany rodowód zapisano do 'przefiltrowany_rodowod_v4.ped'.")
