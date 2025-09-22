#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data prep for "Multimodal Pioneer" hackathon demo.
- Reads input JSON: an array of {item_name, marketing_text, image}
- Creates product_id, injects discrepancies into a random subset of marketing_text
- Streams images to memory and uploads to GCS at gs://{BUCKET}/products/{product_id}.jpg
- Loads (product_id, product_name, marketing_text, image_gcs_uri, source_image_url) into BigQuery table products.products_raw
Requires: google-cloud-storage, google-cloud-bigquery, pandas, requests, python-slugify
"""
import os
import io
import json
import random
import hashlib
import requests
import pandas as pd
from datetime import datetime
from slugify import slugify
from google.cloud import storage, bigquery

# ---------- CONFIG ----------
PROJECT_ID   = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID", "YOUR_PROJECT_ID")
BQ_DATASET   = os.environ.get("BQ_DATASET", "products")
BQ_TABLE     = os.environ.get("BQ_TABLE", "products_raw")
GCS_BUCKET   = os.environ.get("GCS_BUCKET", "YOUR_BUCKET_NAME")
LOCATION     = os.environ.get("BQ_LOCATION", "europe-north1")
INPUT_JSON   = os.environ.get("INPUT_JSON", "bquxjob_399b0e32_19972ec7953.json")  # path to the JSON file you attached
SEED         = int(os.environ.get("RANDOM_SEED", "42"))
DISCREPANCY_RATE = float(os.environ.get("DISCREPANCY_RATE", "0.18"))  # 18% of rows get a tweak

# ---------- DISCREPANCY LIB ----------
# A few simple toggleable claims. You can add/remove per your demo.
TOGGLE_CLAIMS = [
    # (needle, replacement)
    ("sockerfri", "med socker"),
    ("utan socker", "med socker"),
    ("vegansk", "innehåller gelatin"),
    ("vegan", "innehåller gelatin"),
    ("laktosfri", "innehåller laktos"),
    ("koffeinfri", "innehåller koffein"),
    ("utan palmolja", "innehåller palmolja"),
    ("sockerfri", "sötad med socker"),
]

ADDITIVE_CLAIMS = [
    "Obs: Innehåller nötter.",         # adds allergen
    "Obs: Innehåller gelatin.",        # breaks vegan claim
    "Obs: Tillsatt socker.",           # breaks sugar-free
    "Obs: Innehåller koffein.",        # breaks caffeine-free
    "Obs: Ej glutenfri.",              # breaks gluten-free
]

random.seed(SEED)

def make_product_id(name: str) -> str:
    slug = slugify(name)[:48]
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"

def perturb_marketing_text(txt: str) -> str:
    """Randomly injects a discrepancy by toggling or adding a contradictory claim."""
    if random.random() < 0.5 and TOGGLE_CLAIMS:
        needle, repl = random.choice(TOGGLE_CLAIMS)
        if needle.lower() in txt.lower():
            # case-insensitive replace once
            idx = txt.lower().find(needle.lower())
            return txt[:idx] + txt[idx:idx+len(needle)].replace(txt[idx:idx+len(needle)], repl) + txt[idx+len(needle):]
    # else: add an extra contradictory line
    return txt.rstrip() + " " + random.choice(ADDITIVE_CLAIMS)

def stream_to_gcs(url: str, bucket: storage.Bucket, object_name: str) -> str:
    """Downloads the image to memory and uploads to GCS. Returns the gs:// URI."""
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = io.BytesIO(resp.content)
    blob = bucket.blob(object_name)
    blob.upload_from_file(data, content_type="image/jpeg")
    return f"gs://{bucket.name}/{object_name}"

def main():
    # Clients
    storage_client = storage.Client(project=PROJECT_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET)

    # Create dataset if not exists
    bq_client.create_dataset(bigquery.Dataset(f"{PROJECT_ID}.{BQ_DATASET}"), exists_ok=True, location=LOCATION)

    # Read JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)

    rows = []
    for obj in items:
        name = obj.get("item_name") or obj.get("product_name") or "Unnamed"
        marketing = obj.get("marketing_text") or ""
        img_url = obj.get("image") or obj.get("image_url") or ""

        product_id = make_product_id(name)

        # Randomly inject discrepancy
        use_discrepancy = random.random() < DISCREPANCY_RATE
        marketing_out = perturb_marketing_text(marketing) if use_discrepancy else marketing

        # Upload image if present
        gcs_uri = None
        if img_url:
            try:
                object_name = f"products/{product_id}.jpg"
                gcs_uri = stream_to_gcs(img_url, bucket, object_name)
            except Exception as e:
                print(f"[WARN] could not upload image for {name}: {e}")

        rows.append({
            "product_id": product_id,
            "product_name": name,
            "marketing_text": marketing_out,
            "image_gcs_uri": gcs_uri,
            "source_image_url": img_url,
            "has_injected_discrepancy": use_discrepancy,
            "ingested_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })

    df = pd.DataFrame(rows)

    # Create table schema (explicit for safety)
    schema = [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_name", "STRING"),
        bigquery.SchemaField("marketing_text", "STRING"),
        bigquery.SchemaField("image_gcs_uri", "STRING"),
        bigquery.SchemaField("source_image_url", "STRING"),
        bigquery.SchemaField("has_injected_discrepancy", "BOOL"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]

    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)

    job = bq_client.load_table_from_dataframe(df, table)
    job.result()

    print(f"Loaded {len(df)} rows into {table_id}")
    bad = df[df["image_gcs_uri"].isna()]
    if len(bad) > 0:
        print(f"[INFO] {len(bad)} rows had missing/failed image upload (kept in table).")

if __name__ == "__main__":
    main()
