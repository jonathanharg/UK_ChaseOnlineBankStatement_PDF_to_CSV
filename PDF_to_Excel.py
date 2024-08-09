import argparse
import pathlib
from datetime import datetime

import pandas
import pdfplumber


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Chase UK statements to machine readable formats."
    )
    parser.add_argument("files", type=pathlib.Path, nargs="+")
    parser.add_argument(
        "-f",
        "--format",
        choices=["csv", "xlsx", "json"],
        default="xlsx",
        help="export file format",
    )

    args = parser.parse_args()

    transaction = {
        "Date": [],
        "Transaction details": [],
        "Amount": [],
        "Balance": [],
    }

    for path in args.files:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text().split("\n")

                for line in page_text:
                    if "£" not in line:
                        # Skip all non transaction lines of text
                        continue

                    if line.startswith("£"):
                        # skip line below: Opening balance + Money in - Money out = Closing balance
                        continue

                    if line.startswith("The AER is"):
                        continue

                    words = line.split()

                    date_str = " ".join(words[:3])
                    date = datetime.strptime(date_str, "%d %b %Y").date()
                    transaction["Date"].append(date)

                    balance_str = words[-1].replace("£", "").replace(",", "")
                    balance = float(balance_str)
                    transaction["Balance"].append(balance)

                    amount_str = words[-2].replace("£", "").replace(",", "")
                    amount = to_float(amount_str)
                    transaction["Amount"].append(amount)

                    details_words = words[3:-2] if amount is not None else words[3:-1]
                    details = " ".join(details_words)
                    transaction["Transaction details"].append(details)

        df = pandas.DataFrame(transaction)
        df.sort_values(by=['Date'], ascending=False)

        outputs = {
            "csv": lambda: df.to_csv("output.csv", index=False),
            "xlsx": lambda: df.to_excel("output.xlsx", index=False),
            "json": lambda: df.to_json("output.json", index=False),
        }

        outputs[args.format]()
