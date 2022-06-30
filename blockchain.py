import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests
from urllib.parse import urlparse


class Blockchain(object):
    # Target kesusahan yang ingin dicapai makin banyak makin baik(sulit)
    difficulty_target = "0000"

    # Fungsi Melakukan Hashing Block
    def hash_block(self, block):
        # Buat code block dan diurutkan secara key/ascending descending json.dumps convert python objek ke json
        block_encoded = json.dumps(block, sort_keys=True).encode()
        # Melakukan hashing dan kembalikan encoded data ke dalam heximal format
        return hashlib.sha256(block_encoded).hexdigest()

    # Fungsi Membuat Block Baru
    def __init__(self):
        # Menyimpan data block di chain
        self.chain = []

        # Menyimpan data transaksi sementara disini
        self.current_transaction = []

        # Menciptakan block dan hash pertama
        genesis_hash = self.hash_block("genesis_block")

        # Menambahkan block
        self.append_block(
            # Mencari hash previos dari genesis hash
            hash_of_previous_block=genesis_hash,
            # Mencari nonce yang akan digunakan untuk menambah kesulitan
            nonce=self.proof_of_work(0, genesis_hash, [])
        )

    # Fungsi Menyelesaikan Hash dan Membuat Nonce
    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0
        # Buat Looping sampai nonce nya sesuai target
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce

    # Fungsi Untuk Memvalidasi Hash
    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        # Menampung konten dalam bentuk string dan di encode
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()
        # Hashing konten kedalam hex format
        content_hash = hashlib.sha256(content).hexdigest()
        # Nilai hash yang muncul apakah sama dengan target yang diinginkan jika sama maka berhenti mencari
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    # Fungsi Menambahkan Block Baru
    def append_block(self, nonce, hash_of_previous_block):
        block = {
            # Index adalah Panjang dari Block
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            # Nonce adalah angka sekali pakai yang berguna untuk menambah kesulitan pada hash
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        # Reset transaksi yang sudah selesai karena akan digantikan oleh yang baru
        self.current_transaction = []

        # Menampilkan Block baru yang sudah dibuat
        self.chain.append(block)
        return block

    # Fungsi untuk membuat transaksi
    def add_transaction(self, sender, recipient, amount):
        # Mengisi data transaksi dengan parameter diatas
        self.current_transaction.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender
        })
        # Kembalikan nilai transaksinya ke Block terakhir
        return self.last_block['index'] + 1

    # Memasukan Nilai Block terakhir kedalam Chain
    @property
    def last_block(self):
        return self.chain[-1]


# Memanggil API
app = Flask(__name__)
# Membuat Address Penambang
node_identifier = str(uuid4()).replace('-', "")
# Meringkas Class supaya bisa di panggil
blockchain = Blockchain()


# Routes / End Point / URL Blockhain
@app.route('/blockchain', methods=['GET'])
# Semua data di blockchain ditampilkan
def full_chain():
    response = {
        'chain': blockchain.chain,
        'lenght': len(blockchain.chain)
    }
    # Mengembalikan objek respon pada aplikasi
    return jsonify(response), 200


# Route Menambang == Menambahkan Data (Nounce)
@app.route('/mine', methods=['GET'])
# Fungsi Reward Penambang
def mine_block():
    # Menambahkan transaksi penambang
    blockchain.add_transaction(
        # Pengirim (0 = Diberi oleh jaringan blockchain)
        sender="0",
        recipient=node_identifier,
        # Rewardnya
        amount=1
    )

    # Mencari Hash dari Block Sebelumnya
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    # Memanggil POW untuk menemukan nounce
    index = len(blockchain.chain)
    # Mencari Nounce dari proof of work
    nonce = blockchain.proof_of_work(
        index, last_block_hash, blockchain.current_transaction)
    # Block Berhasil ditambahkan setelah nounce sudah ketemu dengan proses POW
    block = blockchain.append_block(nonce, last_block_hash)
    # Pemberitahuan Block Telah Berhasil Ditambahkan
    response = {
        'message': "Block baru telah ditambahkan (Mined)",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
    # Menampilkan respon aplikasi
    return jsonify(response), 200


# Route Menambahkan Transaksi Baru
@app.route('/transaction/new', methods=['POST'])
# Fungsi Menambahkan transaksi
def new_transaction():
    # Value(dan data) semua client yang diinput diambil dengan json
    values = request.get_json
    # Input Membutuhkan Parameter berikut
    require_fields = ['sender', 'recipient', 'amount']

    # Jika Status validasi ada yang kosong
    if not all(k in values for k in require_fields):
        return ('Missing Fields', 400)

    # Jika Status Validasi Benar
    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    # Pemberitahuan Penambahan Transaksi
    response = {'message': f'Transaksi Akan Ditambahkan Ke Blok'}
    # Menampilkan Respon Aplikasi
    return(jsonify(response), 201)


# Jalankan Server Flask
if __name__ == '__main__':
    # Jika Name = Jalan maka jalankan dengan host dan port
    app.run(host='0.0.0.0', port=int(sys.argv[1]))
