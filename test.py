import math
import mysql.connector
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import csv
import datetime
import argparse


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Skripsi"
    )


def fetch_transactions():
    with get_db_connection() as db:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transaksi")
        transactions = cursor.fetchall()
    return transactions


def clean_data(row):
    if isinstance(row, str):
        return row.split(', ')
    return []


def round_up_to_two_decimals(x):
    return math.ceil(x * 100) / 100


def analyze_transaction_patterns(transactions, min_support=0.1, min_confidence=0.5, round_item_support=False):
    # Membuat DataFrame dari transaksi
    df = pd.DataFrame(transactions)
    df['barang'] = df['barang'].apply(clean_data)

    # Mengubah data menjadi format yang sesuai untuk apriori
    te = TransactionEncoder()
    te_ary = te.fit_transform(df['barang'])
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

    # Menerapkan algoritma apriori
    frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

    # Mengonversi frozenset menjadi list di dalam rules
    rules['antecedents'] = rules['antecedents'].apply(lambda x: list(x))
    rules['consequents'] = rules['consequents'].apply(lambda x: list(x))

    # Menerapkan pembulatan ke atas pada support, confidence, dan lift
    rules['support'] = rules['support'].apply(round_up_to_two_decimals)
    rules['confidence'] = rules['confidence'].apply(round_up_to_two_decimals)
    rules['lift'] = rules['lift'].apply(round_up_to_two_decimals)

    # Mencari aturan dengan confidence dan lift tertinggi
    highest_confidence_rule = rules.iloc[rules['confidence'].idxmax()].to_dict() if not rules.empty else None
    highest_lift_rule = rules.iloc[rules['lift'].idxmax()].to_dict() if not rules.empty else None

    # Menghitung support item (rata-rata per kolom)
    item_supports = df_encoded.mean().sort_values(ascending=False)
    if round_item_support:
        item_supports = item_supports.apply(round_up_to_two_decimals)  # Menerapkan pembulatan jika diminta
    item_supports = item_supports.to_dict()

    # Memberikan insight bisnis berdasarkan aturan confidence tertinggi
    insight_bisnis = None
    if highest_confidence_rule:
        insight_bisnis = (
            f"Pelanggan yang membeli {highest_confidence_rule['antecedents']} "
            f"cenderung juga membeli {highest_confidence_rule['consequents']} "
            f"dengan confidence {highest_confidence_rule['confidence']} "
            f"dan lift {highest_confidence_rule['lift']}."
        )

    # Menyusun hasil analisis
    results = {
        'highest_confidence_rule': highest_confidence_rule,
        'highest_lift_rule': highest_lift_rule,
        'insight_bisnis': insight_bisnis,
        'item_supports': item_supports
    }

    return results


def export_csv(filename='transaksi.csv'):
    transactions = fetch_transactions()
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'tanggal', 'barang'])
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Data exported to {filename}")


def run_analysis(min_support, min_confidence):
    transactions = fetch_transactions()
    if not transactions:
        print("No transactions to analyze.")
        return

    results = analyze_transaction_patterns(transactions, min_support, min_confidence)
    if results['insight_bisnis']:
        print(f"Insight Bisnis: {results['insight_bisnis']}")
    else:
        print("No business insight found.")


if __name__ == '__main__':
    # Define command-line arguments
    parser = argparse.ArgumentParser(description="Transaction Analysis CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Sub-command for running analysis
    analyze_parser = subparsers.add_parser('analyze', help="Run transaction pattern analysis")
    analyze_parser.add_argument('--support', type=float, default=0.1, help="Minimum support threshold")
    analyze_parser.add_argument('--confidence', type=float, default=0.5, help="Minimum confidence threshold")

    # Sub-command for exporting CSV
    csv_parser = subparsers.add_parser('export_csv', help="Export transaction data to CSV")
    csv_parser.add_argument('--filename', type=str, default='transaksi.csv', help="Filename for the exported CSV")

    args = parser.parse_args()

    if args.command == 'analyze':
        run_analysis(args.support, args.confidence)
    elif args.command == 'export_csv':
        export_csv(args.filename)
