from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "123"

# DATABASE
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'peminjaman_lab'

mysql = MySQL(app)

# ================= ROUTE =================

@app.route('/')
def home():
    return redirect('/login')

# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username,password))
        user = cur.fetchone()

        if user:
            session['id'] = user[0]
            session['role'] = user[3]

            if user[3] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/user')
        else:
            return "Username / Password salah"

    return render_template('login.html')

# DASHBOARD ADMIN
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT peminjaman.id, users.username, barang.nama_barang, peminjaman.jumlah, peminjaman.status
        FROM peminjaman
        JOIN users ON peminjaman.id_user = users.id
        JOIN barang ON peminjaman.id_barang = barang.id
    """)
    data = cur.fetchall()

    return render_template('dashboard_admin.html', data=data)

#approve
@app.route('/approve/<int:id>')
def approve(id):
    # 🔒 hanya admin
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()

    # 🔍 ambil data peminjaman
    cur.execute("SELECT id_barang, jumlah FROM peminjaman WHERE id=%s", (id,))
    data = cur.fetchone()

    # ❗ kalau data tidak ada
    if data is None:
        return "Data peminjaman tidak ditemukan!"

    id_barang = data[0]
    jumlah = data[1]

    # ❗ cek stok dulu
    cur.execute("SELECT stok FROM barang WHERE id=%s", (id_barang,))
    stok = cur.fetchone()

    if stok is None:
        return "Barang tidak ditemukan!"

    if stok[0] < jumlah:
        return "Stok tidak cukup!"

    # 📉 kurangi stok
    cur.execute("UPDATE barang SET stok = stok - %s WHERE id=%s", (jumlah, id_barang))

    # ✅ update status
    cur.execute("UPDATE peminjaman SET status='disetujui' WHERE id=%s", (id,))
    
    mysql.connection.commit()

    return redirect('/admin')

#reject
@app.route('/reject/<int:id>')
def reject(id):
    # 🔒 hanya admin
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("UPDATE peminjaman SET status='ditolak' WHERE id=%s", (id,))
    mysql.connection.commit()

    return redirect('/admin')

#logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

    # ambil data peminjaman
    cur.execute("SELECT id_barang, jumlah FROM peminjaman WHERE id=%s", (id,))
    data = cur.fetchone()

    id_barang = data[0]
    jumlah = data[1]

    # kurangi stok barang
    cur.execute("UPDATE barang SET stok = stok - %s WHERE id=%s", (jumlah, id_barang))

    # update status
    cur.execute("UPDATE peminjaman SET status='disetujui' WHERE id=%s", (id,))
    
    mysql.connection.commit()

    return redirect('/admin')

# DASHBOARD USER
@app.route('/user')
def user():
    return render_template('dashboard_user.html')

# PINJAM BARANG (PAKAI NAMA + ANTI ERROR)
@app.route('/pinjam', methods=['GET','POST'])
def pinjam():
    if 'id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # ambil semua barang
    cur.execute("SELECT * FROM barang")
    barang_list = cur.fetchall()

    if request.method == 'POST':
        id_user = session['id']
        id_barang = request.form.get('id_barang')
        jumlah = request.form.get('jumlah')

        if not id_barang or not jumlah:
            return "Semua data harus diisi!"

        # simpan
        cur.execute(
            "INSERT INTO peminjaman (id_user,id_barang,jumlah,status) VALUES (%s,%s,%s,'menunggu')",
            (id_user, id_barang, jumlah)
        )
        mysql.connection.commit()

        return "Berhasil meminjam!"

    return render_template('pinjam.html', barang=barang_list)

#barang
@app.route('/barang')
def barang():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM barang")
    data = cur.fetchall()

    return render_template('barang.html', data=data)

# ================= RUN =================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
    