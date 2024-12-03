document.addEventListener('DOMContentLoaded', function() {
    fetchTransactions();
    document.getElementById('analyzeButton').addEventListener('click', function() {
        analyzeTransactions();
    });
});

function fetchTransactions() {
    fetch('/transactions')
        .then(response => response.json())
        .then(data => {
            const transactionsDiv = document.getElementById('transactions');
            transactionsDiv.innerHTML = ''; // Kosongkan tampilan sebelumnya
            data.forEach(transaction => {
                const div = document.createElement('div');
                div.classList.add('transaction-item');
                div.textContent = `${transaction.tanggal_transaksi}: ${transaction.produk}`;
                transactionsDiv.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Error fetching transactions:', error);
        });
}

function redirectToKelolaTransaksi() {
    window.location.href = '/kelola_transaksi'; // Ganti dengan URL yang sesuai
}

function addTransaction() {
    const tanggal = document.getElementById('tanggal_transaksi').value;
    let barangList = [];
    for (let i = 1; i <= itemCount; i++) {
        const barangValue = document.getElementById(`barang${i}`).value;
        if (barangValue) {
            barangList.push(barangValue);
        }
    }
    const produk = barangList.join(', ');

    fetch('/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tanggal_transaksi: tanggal, produk: produk, toko: document.getElementById('toko').value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Transaksi Berhasil ditambahkan') {
            // Tampilkan modal sukses
            const successModal = new bootstrap.Modal(document.getElementById('successModal'));
            successModal.show();
            fetchTransactions(); // Memperbarui tampilan transaksi
        } else {
            // Tampilkan pesan kesalahan jika ada
            console.error(data.message);
            alert(data.message); // Ganti dengan modal atau tampilan yang lebih baik jika perlu
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Terjadi kesalahan saat menambahkan transaksi.'); // Ganti dengan modal atau tampilan yang lebih baik jika perlu
    });
}
function redirectToIndex() {
    window.location.href = '/';
}

let itemCount = 1;

// Fungsi untuk menambah item baru
document.getElementById('add-item').addEventListener('click', function() {
    if (itemCount < 5) { // Maksimal 5 item
        // Hapus tombol "Hapus Item" dari item sebelumnya jika ada
        if (itemCount > 1) {
            const previousItemDiv = document.getElementById(`item${itemCount}`);
            const deleteButton = previousItemDiv.querySelector('.btn-danger');
            if (deleteButton) {
                deleteButton.remove();
            }
        }

        itemCount++; // Tambahkan jumlah item

        // Buat elemen baru untuk item
        const newItemDiv = document.createElement('div');
        newItemDiv.classList.add('form-group');
        newItemDiv.id = `item${itemCount}`;

        // Buat label dan select untuk produk
        const label = document.createElement('label');
        label.setAttribute('for', `barang${itemCount}`);
        label.textContent = `Produk ${itemCount}:`;

        const select = document.createElement('select');
        select.classList.add('form-control');
        select.id = `barang${itemCount}`;
        select.name = 'produk[]';
        select.required = true;

        // Tambahkan option ke select
        const options = [
            { value: '', text: 'Pilih Produk' },
            { value: 'Kerupuk Udang Melati', text: 'Kerupuk Udang Melati' },
            { value: 'Keripik Pisang', text: 'Keripik Pisang' },
            { value: 'Kerupuk Udang Mawar', text: 'Kerupuk Udang Mawar' },
            { value: 'Makaroni', text: 'Makaroni' },
            { value: 'Keripik Singkong Asin', text: 'Keripik Singkong Asin' },
            { value: 'Ring', text: 'Ring' },
            { value: 'Sanjai Balado', text: 'Sanjai Balado' },
            { value: 'Kerupuk Ikan', text: 'Kerupuk Ikan' },
            { value: 'Kerupuk Jengkol', text: 'Kerupuk Jengkol' },
            { value: 'Keripik Untir-Untir', text: 'Keripik Untir-Untir' },
            { value: 'Kerupuk Seblak', text: 'Kerupuk Seblak' },
            { value: 'Stick Keju', text: 'Stick Keju' },
            { value: 'Keripik Singkong Pedas', text: 'Keripik Singkong Pedas' },
        ];

        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.text = option.text;
            select.appendChild(optionElement);
        });

        // Tambahkan label dan select ke itemDiv
        newItemDiv.appendChild(label);
        newItemDiv.appendChild(select);

        // Tambahkan tombol hapus hanya pada item terakhir
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.textContent = 'Hapus Item';
        deleteButton.classList.add('btn', 'btn-danger', 'btn-sm', 'mt-2');
        deleteButton.onclick = function() {
            deleteItem(newItemDiv.id);
        };
        newItemDiv.appendChild(deleteButton);

        // Tambahkan itemDiv ke dynamic-form
        document.getElementById('dynamic-form').appendChild(newItemDiv);

        // Jika jumlah item mencapai 5, maka tombol "Tambah Item" akan menghilang
        if (itemCount === 5) {
            document.getElementById('add-item').style.display = 'none';
        }
    }
});

// Fungsi untuk menghapus item
function deleteItem(itemId) {
    const itemDiv = document.getElementById(itemId);
    itemDiv.remove();

    // Mengurangi itemCount
    itemCount--;

    // Jika jumlah item kurang dari 5, maka tombol "Tambah Item" akan muncul kembali
    if (itemCount < 5) {
        document.getElementById('add-item').style.display = 'block';
    }

    // Jika itemCount > 1, tambahkan tombol "Hapus Item" ke item terakhir yang tersisa
    if (itemCount > 1) {
        const lastItemDiv = document.getElementById(`item${itemCount}`);
        let deleteButton = lastItemDiv.querySelector('.btn-danger');
        if (!deleteButton) {
            // Tambahkan tombol "Hapus Item" jika belum ada
            deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.textContent = 'Hapus Item';
            deleteButton.classList.add('btn', 'btn-danger', 'btn-sm', 'mt-2');
            deleteButton.onclick = function() {
                deleteItem(lastItemDiv.id);
            };
            lastItemDiv.appendChild(deleteButton);
        }
    }
}

function analyzeTransactions() {
    fetch('/analyze')
        .then(response => response.json())
        .then(data => {
            const analysisResultDiv = document.getElementById('analysisResult');
            if (data.message) {
                analysisResultDiv.innerHTML = `<p>${data.message}</p>`;
            } else {
                analysisResultDiv.innerHTML = `
                    <h3>Rule with Highest Confidence</h3>
                    <p>Antecedents: ${data.highest_confidence_rule.antecedents.join(', ')}</p>
                    <p>Consequents: ${data.highest_confidence_rule.consequents.join(', ')}</p>
                    <p>Confidence: ${data.highest_confidence_rule.confidence}</p>
                    <h3>Rule with Highest Lift</h3>
                    <p>Antecedents: ${data.highest_lift_rule.antecedents.join(', ')}</p>
                    <p>Consequents: ${data.highest_lift_rule.consequents.join(', ')}</p>
                    <p>Lift: ${data.highest_lift_rule.lift}</p>
                `;
            }
        });
}


