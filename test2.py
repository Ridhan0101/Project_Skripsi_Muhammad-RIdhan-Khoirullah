# Import library yang dibutuhkan
from mlxtend.preprocessing import TransactionEncoder
import pandas as pd


transaksi = [
    ['Keripik', 'Kerupuk', 'Minuman'],
    ['Keripik', 'Minuman'],
    ['Kerupuk'],
    ['Keripik', 'Kerupuk', 'Minuman', 'Permen'],
    ['Permen', 'Kerupuk']
]

# Membuat instance TransactionEncoder
te = TransactionEncoder()

# Mengubah data transaksi menjadi format array biner
transaksi_te = te.fit(transaksi).transform(transaksi)

# Mengubah hasil array menjadi DataFrame agar lebih mudah dibaca
df_transaksi = pd.DataFrame(transaksi_te, columns=te.columns_)

# Menampilkan hasil
print(df_transaksi)
