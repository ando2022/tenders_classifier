"""
Load and clean SIMAP kw_hit dataset and standardize schema for modeling.

Usage:
  python src/data_prep/load_and_clean.py \
    --input "bak-economics/My Drive/BAK-Economics/Data/raw/test set/simap/kw hits/tenders_details.xlsx" \
    --output "/Users/anastasiiadobson/Desktop/CAPSTONE PROJECT/bak-economics/data/processed/tenders_clean.parquet"
"""

import argparse
import os
import pandas as pd


CANONICAL_COLUMNS = {
    # text
    "Topic": ["Topic", "Thema", "title", "Titel", "subject", "Order Description"],
    # source / channel
    "Source": ["Source", "Quelle", "channel", "origin", "Procurement Office"],
    # labels
    "kw_hit_selected": ["kw_hit_selected", "kw_hit selected", "kw_hit_selected_flag"],
    "kw_hit_selected_by_sales": [
        "kw_hit_selected_by_sales",
        "kw_hit selected by sales",
        "sales_selected",
    ],
    # status indicator (often holds kw_hit / selected states)
    "Status": ["Status", "status"],
    # optional metadata
    "Budget": ["Budget", "budget"],
    "Year": ["Year", "Jahr"],
    "PublicationDate": ["Publication Date", "publication_date", "Published", "Publikation"],
}


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a.lower() in lowered:
            return lowered[a.lower()]
    return None


def standardize_schema(df: pd.DataFrame) -> pd.DataFrame:
    mapping: dict[str, str] = {}
    for canon, aliases in CANONICAL_COLUMNS.items():
        col = find_column(df, aliases)
        if col:
            mapping[col] = canon
    df = df.rename(columns=mapping)

    # Ensure required columns exist
    required = ["Topic"]
    for r in required:
        if r not in df.columns:
            raise ValueError(f"Required column missing after rename: {r}")

    # Derive labels from Status when explicit label columns are absent
    if "Status" in df.columns:
        status_lower = df["Status"].astype(str).str.lower()
        if "kw_hit_selected" not in df.columns:
            df["kw_hit_selected"] = status_lower.isin([
                "kw_hit selected",
                "kw_hit selected by sales",
                "kw_hit_selected",
                "kw_hit_selected_by_sales",
            ]).astype(int)
        if "kw_hit_selected_by_sales" not in df.columns:
            df["kw_hit_selected_by_sales"] = status_lower.isin([
                "kw_hit selected by sales",
                "kw_hit_selected_by_sales",
            ]).astype(int)

    # Coerce labels to int when present
    for lbl in ["kw_hit_selected", "kw_hit_selected_by_sales"]:
        if lbl in df.columns:
            df[lbl] = pd.to_numeric(df[lbl], errors="coerce").fillna(0).astype(int)

    # Clean text
    df["Topic"] = (
        df["Topic"].fillna("").astype(str).str.replace("\r\n|\n|\r", " ", regex=True).str.strip()
    )

    # Optional types
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    if "Budget" in df.columns:
        # extract numeric if strings like "CHF 100'000"
        df["Budget_numeric"] = (
            df["Budget"].astype(str)
            .str.replace("'", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.extract(r"(\d+(?:\.\d+)?)")[0]
            .astype(float)
        )
    if "Source" in df.columns:
        df["Source"] = df["Source"].astype(str).str.strip()
    if "PublicationDate" in df.columns:
        df["PublicationDate"] = pd.to_datetime(df["PublicationDate"], errors="coerce")

    # Drop PublicationDate/Source if they have no content
    for c in ["PublicationDate", "Source"]:
        if c in df.columns:
            # Treat NaN as empty before string conversion to avoid 'nan'
            col_series = df[c].astype(object)
            empty_mask = col_series.fillna("").astype(str).str.strip() == ""
            if empty_mask.all():
                df = df.drop(columns=[c])

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    inp = args.input
    outp = args.output
    os.makedirs(os.path.dirname(outp), exist_ok=True)

    # Read Excel (auto sheet)
    df = pd.read_excel(inp)
    df = standardize_schema(df)

    # Drop empty topics
    before = len(df)
    df = df[df["Topic"].str.len() > 0].copy()
    print(f"Rows kept after empty-topic filter: {len(df)}/{before}")

    # Save parquet + csv for convenience
    df.to_parquet(outp, index=False)
    csv_out = os.path.splitext(outp)[0] + ".csv"
    # utf-8-sig ensures Excel displays umlauts/accents correctly
    df.to_csv(csv_out, index=False, encoding="utf-8-sig")
    print(f"Saved: {outp}\nSaved: {csv_out}")


if __name__ == "__main__":
    main()


