from flask import jsonify


class Transaction:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def fetch_transactions(self, filter_toko=None, filter_produk=None, order='asc'):
        with self.db_connection.get_connection() as db:
            cursor = db.cursor(dictionary=True)

            query = "SELECT * FROM transaksi WHERE 1=1"
            params = []

            if filter_toko:
                query += " AND toko = %s"
                params.append(filter_toko)

            if filter_produk:
                query += " AND produk LIKE %s"
                params.append(f"%{filter_produk}%")

            query += f" ORDER BY tanggal_transaksi {order}"

            cursor.execute(query, params)
            transactions = cursor.fetchall()

        return transactions

    def add_transaction(self, data):
        try:
            print(f"Data yang diterima: {data}")  # Tambahkan log ini
            with self.db_connection.get_connection() as db:
                cursor = db.cursor()

                produk = data['produk']
                
                if len(produk) != len(set(produk)):
                    return {'message': 'Tidak boleh ada data produk yang sama dalam satu transaksi '}, 400

                produk_str = ', '.join(produk)

                cursor.execute(
                    "INSERT INTO transaksi (tanggal_transaksi, toko, produk) VALUES (%s, %s, %s)",
                    (data['tanggal_transaksi'], data['toko'], produk_str)
                )
                db.commit()
            return {'message': 'Transaksi Berhasil ditambahkan'}, 200
        except Exception as e:
            print(f"Error saat menambahkan transaksi: {str(e)}")  # Tambahkan log ini
            return {'message': f'Error saat menambahkan transaksi: {str(e)}'}, 500
        
    def edit_transaction(self, id, data):
        try:
            produk = [v for k, v in data.items() if k.startswith('produk') and v]
            if not produk:
                return {'message': 'Produk tidak boleh kosong'}, 400
            if not data['toko']:
                return {'message': 'Toko tidak boleh kosong'}, 400
            if not data['tanggal_transaksi']:
                return {'message': 'Tanggal tidak boleh kosong'}, 400

            if len(produk) != len(set(produk)):
                return {'message': 'Produk tidak boleh sama dalam satu transaksi'}, 400

            produk_str = ', '.join(produk)
            with self.db_connection.get_connection() as db:
                cursor = db.cursor()
                cursor.execute(
                    "UPDATE transaksi SET produk = %s, tanggal_transaksi = %s, toko = %s WHERE id = %s",
                    (produk_str, data['tanggal_transaksi'], data['toko'], id)
                )
                db.commit()
            return {'message': 'Transaksi berhasil diperbarui'}, 200
        except Exception as e:
            print(f"Error saat mengedit transaksi: {str(e)}")  # Log error
            return {'message': f'Error saat mengedit transaksi: {str(e)}'}, 400   

    def delete_transaction(self, id):
        try:
            with self.db_connection.get_connection() as db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM transaksi WHERE id = %s", (id,))
                db.commit()

            return {'message': "Transaksi berhasil dihapus", "status": "success"}, 200
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return {'message': "Terjadi kesalahan saat menghapus transaksi", "status": "error"}, 500

    def fetch_unique_produk(self):
        with self.db_connection.get_connection() as db:
            cursor = db.cursor()
            cursor .execute("SELECT DISTINCT produk FROM transaksi")
            produk_list = cursor.fetchall()

        produk_set = set()
        for row in produk_list:
            if row[0]:
                produk_set.update(row[0].split(', '))

        return sorted(produk_set)

    def fetch_unique_toko(self):
        with self.db_connection.get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT toko FROM transaksi")
            toko_list = cursor.fetchall()

        return sorted([toko[0] for toko in toko_list if toko[0]])
    
    