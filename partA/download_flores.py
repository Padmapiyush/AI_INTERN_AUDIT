#!/usr/bin/env python3
"""
download_flores.py — Download FLORES-200 devtest split for selected languages.
Saves one .txt file per language in the corpus/ directory.
"""

import os
import sys

def main():
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing 'datasets' library...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
        from datasets import load_dataset

    # FLORES-200 language codes -> our short codes
    lang_map = {
        "eng_Latn": "eng",
        "hin_Deva": "hin",
        "kan_Knda": "kan",
        "tam_Taml": "tam",
    }

    output_dir = os.path.join(os.path.dirname(__file__), "corpus")
    os.makedirs(output_dir, exist_ok=True)

    print("Loading FLORES-200 devtest split...")
    ds = load_dataset("Muennighoff/flores200", "all", split="devtest", trust_remote_code=True)

    for flores_code, short_code in lang_map.items():
        col_name = f"sentence_{flores_code}"
        if col_name not in ds.column_names:
            # Try alternative column naming
            col_name = f"sentence_{flores_code}"
            print(f"WARNING: Column '{col_name}' not found. Available: {ds.column_names[:10]}...")
            continue

        out_path = os.path.join(output_dir, f"{short_code}.txt")
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for row in ds:
                sentence = row[col_name].strip()
                if sentence:
                    f.write(sentence + "\n")
                    count += 1

        print(f"  {short_code}: {count} sentences -> {out_path}")

    print("Done!")


if __name__ == "__main__":
    main()
