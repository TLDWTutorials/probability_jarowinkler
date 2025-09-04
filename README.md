# Probabilistic Record Linkage (No Unique ID)

A starting point for linking two tables of people (employees, students, etc.) **without a unique identifier** using classic probabilistic record linkage.  
This example uses `recordlinkage` Python module with Jaro-Winkler string similarity and exact date matches to produce (a) all candidate pairs with similarity scores and (b) a high-confidence subset.

Outputs include **every original column from both files** (with `df1_` / `df2_` prefixes) so you can audit results easily.

I also made a short YouTube video demonstrating how to use this: https://youtu.be/NBIFKW6NT-Q

---

## What it does

- Reads two Excel files: `employee_records_1.xlsx` and `employee_records_2.xlsx`
- Compares records on: `first_name`, `last_name`, `birthdate`, and `city`
- Computes a **match score** (sum of per-field similarities)
- Saves:
  - `all_possible_combos_with_fields.csv` – every candidate pair + similarity scores + all original fields
  - `linked_records_with_fields.csv` – high-confidence matches only (by default, `match_score > 3.0`)

---

## How it works

- **Indexing:** This example uses *all-vs-all* to keep it simple.
- **Similarity:** Jaro-Winkler for strings; exact match for `birthdate`.
- **Score:** `match_score = prob_first_name + prob_last_name + prob_birthdate + prob_city` (range ~0–4).
- **Threshold:** You choose what score counts as a match (default `> 3.0`).

---

## Installation

```bash
# Create/activate a virtual environment (optional but recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install deps
pip install pandas recordlinkage 
```

> Note if you get an error about needing `openpyxl` (which lets pandas read `.xlsx` files), just do `pip install openpyxl`.   

---

## Input files

Place these at the project root (or update the paths in the script):

- `employee_records_1.xlsx`
- `employee_records_2.xlsx`

**Recommended columns (case-sensitive):**

| Column      | Type        | Notes                                  |
|-------------|-------------|----------------------------------------|
| first_name  | text        | free text; Jaro-Winkler similarity     |
| last_name   | text        | free text; Jaro-Winkler similarity     |
| birthdate   | date/string | parsed to datetime; exact comparison   |
| city        | text        | free text; Jaro-Winkler similarity     |

> If a column is missing, the script safely skips the `birthdate` coercion step and will error only if a compared field doesn’t exist in both files. Adjust the compare block to match your schema.

---

## Run it

```bash
python link_records.py
```

You’ll see `done` when finished.

---

## Outputs

| File                               | Description                                                      |
|------------------------------------|------------------------------------------------------------------|
| `all_possible_combos_with_fields.csv` | Every candidate pair with per-field probabilities & match_score, plus **all original fields** from both files (prefixed). |
| `linked_records_with_fields.csv`      | High-confidence matches only (see thresholds below for suggestions for ranges).      |

---

## Tune the threshold

- Start around **3.0** for conservative matches (out of ~4.0 max if all fields present).
- Loosen to **2.5–2.8** if you’re missing `birthdate` or data is noisy.
- Tighten to **3.3–3.6** for stricter matches on larger/cleaner datasets.

**Pro tip:** Inspect a sample of rows just below and above your threshold to calibrate.

---

## Speed tips (blocking)

All-vs-all can be slow for large datasets. To speed up, replace:

```python
indexer = recordlinkage.Index()
indexer.full()
```

with a **blocking** strategy, e.g.:

```python
indexer = recordlinkage.Index()
indexer.block('city')  # or block on first letter of last_name, postal code, etc.
```

You can also **pre-normalize** (lowercase, strip whitespace, remove punctuation) to improve similarity scores.

---

## Why we reset the index

`features` uses a **MultiIndex** of row positions from `df1` and `df2` to identify each candidate pair.  
`features.reset_index()` turns those index levels into regular columns (`level_0`, `level_1`) so we can merge back the **full original rows** from each dataframe. After merging, those numeric row IDs are no longer meaningful, so we drop them.

---

## Troubleshooting

- **ValueError: column not found**  
  Make sure both files contain the compared columns, or adjust the `compare` section.
- **Dates don’t match**  
  Confirm `birthdate` is truly a date in both files. Consider using a looser rule (e.g., year or ±1 day) if needed.
- **Too many false positives**  
  Raise the threshold or add more comparison fields (e.g., `state`, `phone`, `email` with partial/character-level comparisons).
- **Too few matches**  
  Lower the threshold and/or ensure your preprocessing (lowercasing, trimming, removing accents) is consistent across both tables.

---

## Code

Save as `link_records.py`:

```python
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
```

---

## License

MIT © You
