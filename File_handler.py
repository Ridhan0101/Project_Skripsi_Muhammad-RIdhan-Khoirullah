from io import StringIO
import pandas as pd
import os
from werkzeug.utils import secure_filename
from flask import Response, jsonify
import csv
import pdfkit

class FileHandler:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.upload_folder = 'uploads'
        self.allowed_extensions = {'csv'}
        self.path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def upload_csv(self, file):
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)

            df = pd.read_csv(filepath)

            required_columns = ['tanggal_transaksi', 'toko', 'produk']
            if not all(column in df.columns for column in required_columns):
                return {'message': 'File CSV harus memiliki kolom: tanggal_transaksi, toko, produk'}, 400

            if df.empty:
                return {'message': 'Semua nilai tanggal tidak valid.'}, 400

            # Konversi kolom 'tanggal_transaksi' menjadi datetime
            df['tanggal_transaksi'] = pd.to_datetime(df['tanggal_transaksi'], errors='coerce')

            with self.db_connection.get_connection() as db:
                cursor = db.cursor()
                for _, row in df.iterrows():
                    # Pastikan bahwa row['tanggal_transaksi'] bukan NaT (Not a Time)
                    if pd.isnull(row['tanggal_transaksi']):
                        return {'message': 'Tanggal transaksi tidak valid.'}, 400

                    cursor.execute(
                        "INSERT INTO transaksi (tanggal_transaksi, toko, produk) VALUES (%s, %s, %s)",
                        (row['tanggal_transaksi'].strftime('%Y-%m-%d'), row['toko'], row['produk'])
                    )
                db.commit()

            return {'message': 'CSV berhasil diunggah'}, 200
        return {'message': 'Hanya File CSV yang diperbolehkan.'}, 400

    def export_csv(self):
        with self.db_connection.get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM transaksi")
            rows = cursor.fetchall()

        # Get column names from the cursor
        column_names = [desc[0] for desc in cursor.description]

        # Convert rows from tuples to dictionaries
        rows_dict = [dict(zip(column_names, row)) for row in rows]

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(rows_dict)

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=transaksi.csv'}
        )

    def export_pdf(self, rendered_html, min_support, min_confidence):
        if not isinstance(rendered_html, str):
            return {'message': 'Rendered HTML must be a string.'}, 400

        config = pdfkit.configuration(wkhtmltopdf=self.path_wkhtmltopdf)
        options = {
            'enable-local-file-access': None,  
        }

        pdf = pdfkit.from_string(rendered_html, False, configuration=config, options=options)

        filename = f"laporan_analisis_support_{min_support}_confidence_{min_confidence}.pdf"

        return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename={filename}'})
