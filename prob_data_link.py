import pandas as pd
import recordlinkage

# === Load
df1 = pd.read_excel("employee_records_1.xlsx")
df2 = pd.read_excel("employee_records_2.xlsx")

# === Preprocess
for d in (df1, df2):
    if 'birthdate' in d.columns:
        d['birthdate'] = pd.to_datetime(d['birthdate'], errors='coerce')

# === Index (all-vs-all)
indexer = recordlinkage.Index()
indexer.full()
candidate_links = indexer.index(df1, df2)

# === Compare
compare = recordlinkage.Compare()
compare.string('first_name', 'first_name', method='jarowinkler', label='prob_first_name')
compare.string('last_name',  'last_name',  method='jarowinkler', label='prob_last_name')
compare.exact('birthdate',   'birthdate',  label='prob_birthdate')
compare.string('city',       'city',       method='jarowinkler', label='prob_city')

features = compare.compute(candidate_links, df1, df2)

# === Match score
features['match_score'] = features.sum(axis=1)

# Reset index (this gives row ids, but we’ll drop them after merge)
pairs = features.reset_index()

# === Attach ALL original fields (with prefixes so you can tell them apart)
df1_prefixed = df1.add_prefix('df1_')   # -> df1_employee_id, df1_first_name, ...
df2_prefixed = df2.add_prefix('df2_')   # -> df2_student_id, df2_first_name, ...

merged = (
    pairs
    .merge(df1_prefixed, left_on='level_0', right_index=True, how='left')
    .merge(df2_prefixed, left_on='level_1', right_index=True, how='left')
)

# Drop the row index identifiers (level_0, level_1) since they aren’t meaningful
merged = merged.drop(columns=['level_0', 'level_1'])

# === Save outputs
# All pairs with probabilities + all fields
merged.to_csv("all_possible_combos_with_fields.csv", index=False)

# Subset: high-confidence matches only
matches = merged[merged['match_score'] > 3.0]
matches.to_csv("linked_records_with_fields.csv", index=False)

print('done')









