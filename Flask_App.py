from datetime import datetime
from flask import Flask, flash, render_template, request, redirect, session, url_for, jsonify
import numpy as np
from Database_Connection import DatabaseConnection
from File_handler import FileHandler
from Transaction import Transaction
from Analysis_Result import AnalysisResult
import os
import matplotlib
matplotlib.use('Agg') 
from flask_session import Session

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')
app.config['SESSION_PERMANENT'] = False  # Sesi hanya berlangsung selama browser terbuka
app.config['SESSION_TYPE'] = 'filesystem'  # Atur tipe penyimpanan sesi
Session(app)

# Initialize classes
db_connection = DatabaseConnection()
file_handler = FileHandler(db_connection)
transaction = Transaction(db_connection)
analysis_result = AnalysisResult(db_connection)

@app.route('/')
def index():
    # Fetch transactions to display
    all_transactions = transaction.fetch_transactions()
    page = request.args.get('page', 1, type=int)
    limit = 20
    total_transactions = len(all_transactions)
    total_pages = (total_transactions + limit - 1) // limit
    page = max(1, min(page, total_pages))
    
    offset = (page - 1) * limit
    transactions = all_transactions[offset:offset + limit]

    return render_template('kelola_transaksi.html', 
                           transactions=transactions,
                           page=page,
                           total_transactions=total_transactions,
                           limit=limit)

@app.route('/kelola_transaksi')
def kelola_transaksi():
    return index()

@app.route('/filter_data')
def filter_data():
    filter_toko = request.args.get('filter_toko', default=None, type=str)
    filter_produk = request.args.get('filter_produk', default=None, type=str)
    order = request.args.get('order', default='asc', type=str)
    page = request.args.get('page', 1, type=int)
    limit = 20

    unique_toko = transaction.fetch_unique_toko()
    unique_produk = transaction.fetch_unique_produk()
    all_transactions = transaction.fetch_transactions(filter_toko, filter_produk, order)
    
    total_transactions = len(all_transactions)
    total_pages = (total_transactions + limit - 1) // limit
    page = max(1, min(page, total_pages))
    
    offset = (page - 1) * limit
    transactions = all_transactions[offset:offset + limit]

    return render_template('filter_data.html',
                           transactions=transactions,
                           page=page,
                           total_transactions=total_transactions,
                           limit=limit,
                           filter_toko=filter_toko,
                           filter_produk=filter_produk,
                           order=order,
                           unique_toko=unique_toko,
                           unique_produk=unique_produk)

@app.route('/add', methods=['POST'])
def add_transaction():
    data = request.json
    response, status_code = transaction.add_transaction(data)
    return jsonify(response), status_code

@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    data = request.form.to_dict()
    transaction.edit_transaction(id, data)
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    response, status_code = transaction.delete_transaction(id)
    return jsonify(response), status_code

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    results = None  
    plot_url = None

    if request.method == 'POST':
        min_support = request.form.get('support', 0.1)
        min_confidence = request.form.get('confidence', 0.5)

        try:
            min_support = float(min_support)
            # min_confidence = float(min_confidence)
        except ValueError:
            flash("Nilai support dan confidence harus berupa angka desimal (misalnya, 0.01).")
            return redirect(url_for('analyze'))

        if not (0 < min_support <= 1) or not (0 < min_confidence <= 1):
            flash("Nilai Support dan confidence harus berada dalam rentang 0 sampai 1.")
            return redirect(url_for('analyze'))

        transactions = transaction.fetch_transactions()
        results = analysis_result.analyze_transaction_patterns(transactions, min_support, min_confidence)

        if 'pola_asosiasi' in results:
            # Urutkan berdasarkan lift tertinggi
            top_rules = sorted(results['pola_asosiasi'], key=lambda x: x['lift'], reverse=True)
            print([rule['lift'] for rule in top_rules])
            # Ambil 10 aturan teratas
            top_rules = top_rules[:10]
            plot_url = analysis_result.create_bar_chart(top_rules, min_support, min_confidence)

        if not results.get('pola_asosiasi'):
            results['error'] = 'Tidak ditemukan pola asosiasi yang memenuhi kriteria minimum support dan confidence.'

        session['results'] = results

    return render_template('analyze.html', results=results, plot_url=plot_url)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    response, status_code = file_handler.upload_csv(file)
    return jsonify(response), status_code

@app.route('/export_csv')
def export_csv():
    return file_handler.export_csv()

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    results = session.get('results')

    if results is None:
        return {'message': 'No analysis results found. Please perform analysis first.'}, 400

    results['cetak_waktu'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    min_support = float(request.form.get('support', 0.1))
    min_confidence = float(request.form.get('confidence', 0.5))

    if 'pola_asosiasi' in results:
        top_rules = sorted(results['pola_asosiasi'], key=lambda x: ( x['lift']), reverse=True)
        if len(top_rules) > 10:
            top_rules = top_rules[:10]
        plot_url = analysis_result.create_bar_chart(top_rules, min_support, min_confidence)
    else:
        plot_url = None

    rendered_html = render_template('analyze_pdf.html', results=results, plot_url=plot_url)
    return file_handler.export_pdf(rendered_html, min_support, min_confidence)

if __name__ == '__main__':
    app.run(debug=True)
