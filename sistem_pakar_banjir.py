# ==============================================================
# SISTEM PAKAR KERAWANAN BANJIR SUATU WILAYAH
# Metode: Fuzzy Mamdani | Input: curah hujan dan elevasi
# Keluaran: skor 1-5 | AND/implikasi: MIN | agregasi: MAX
# Defuzzifikasi: centroid numerik (integrasi trapesium)
# Python 3.9+; hanya memakai pustaka standar.
# ==============================================================
# ACUAN: Hutauruk dkk. (2020), Tabel 2:
# https://journals.ums.ac.id/fg/article/view/10667/6268
# Jurnal memakai scoring + overlay GIS, BUKAN Mamdani.
# Rentang kelas dan bobot diadaptasi dari jurnal. Titik fuzzy,
# 25 aturan, dan fungsi keluaran adalah rancangan pembelajaran
# yang belum divalidasi pakar/data banjir. Ini bukan probabilitas
# atau prediksi banjir harian.

import math
import sys

# 1. DEKLARASI DATA DAN BASIS PENGETAHUAN
NAMA_HUJAN = ["Sangat kering", "Kering", "Cukup basah", "Basah", "Sangat basah"]
NAMA_ELEVASI = ["Sangat rendah", "Rendah", "Sedang", "Tinggi", "Sangat tinggi"]
NAMA_KELUARAN = ["Sangat rendah", "Rendah", "Sedang", "Tinggi", "Sangat tinggi"]
PUNCAK_HUJAN = [1000.0, 1250.0, 1750.0, 2250.0, 2500.0]
PUNCAK_ELEVASI = [10.0, 30.0, 75.0, 150.0, 200.0]
PUNCAK_KELUARAN = [1.0, 2.0, 3.0, 4.0, 5.0]
SKOR_KELAS_HUJAN = [1, 2, 3, 4, 5]
SKOR_KELAS_ELEVASI = [5, 4, 3, 2, 1]
BOBOT_HUJAN, BOBOT_ELEVASI = 15, 10
JUMLAH_INTERVAL = 4000  # Jarak skor 0,001; 4.001 titik dari 1 sampai 5.

# Baris: kategori hujan; kolom: kategori elevasi.
# Isi: kategori MAKA (1 = sangat rendah, ..., 5 = sangat tinggi).
# Aturan ditetapkan SEBELUM input pengguna, tidak dipelajari otomatis.
# Dasar usulan: q = (15*skor_hujan + 10*skor_elevasi)/25,
# kemudian kategori keluaran terdekat. Ini hanya penetapan aturan,
# BUKAN rumus skor akhir Mamdani.
BASIS_ATURAN = [
    [3, 2, 2, 1, 1],
    [3, 3, 2, 2, 2],
    [4, 3, 3, 3, 2],
    [4, 4, 4, 3, 3],
    [5, 5, 4, 4, 3],
]


def keanggotaan(x, puncak):
    """Lima kategori bertumpang tindih; ujung berupa bahu kiri/kanan."""
    hasil = [0.0] * len(puncak)
    if x <= puncak[0]:
        hasil[0] = 1.0
    elif x >= puncak[-1]:
        hasil[-1] = 1.0
    else:
        for i in range(len(puncak) - 1):
            kiri, kanan = puncak[i], puncak[i + 1]
            if kiri <= x <= kanan:
                hasil[i] = (kanan - x) / (kanan - kiri)
                hasil[i + 1] = (x - kiri) / (kanan - kiri)
                break
    return hasil


def parse_angka(teks):
    """Terima titik/koma desimal; tidak menerima pemisah ribuan."""
    if not teks.strip():
        raise ValueError("Input tidak boleh kosong.")
    try:
        angka = float(teks.strip().replace(",", "."))
    except ValueError:
        raise ValueError("Masukkan angka, bukan huruf. Contoh: 2200 atau 48,5.") from None
    if not math.isfinite(angka):
        raise ValueError("Angka harus berhingga; NaN dan infinity tidak diterima.")
    return angka


def hitung_kerawanan(hujan, elevasi):
    """Mesin inferensi: fuzzifikasi -> MIN -> pemotongan -> MAX -> centroid."""
    if not math.isfinite(hujan) or hujan < 0:
        raise ValueError("Curah hujan harus angka berhingga dan tidak negatif.")
    if not math.isfinite(elevasi):
        raise ValueError("Elevasi harus angka berhingga.")
    # Elevasi negatif sah: wilayah bisa berada di bawah permukaan laut.
    mu_hujan = keanggotaan(hujan, PUNCAK_HUJAN)
    mu_elevasi = keanggotaan(elevasi, PUNCAK_ELEVASI)
    aturan_aktif = []
    for i, mu_h in enumerate(mu_hujan):
        for j, mu_e in enumerate(mu_elevasi):
            alfa = min(mu_h, mu_e)
            if alfa > 0:
                aturan_aktif.append({
                    "nomor": i * 5 + j + 1,
                    "hujan": NAMA_HUJAN[i], "elevasi": NAMA_ELEVASI[j],
                    "mu_hujan": mu_h, "mu_elevasi": mu_e,
                    "alfa": alfa, "keluaran": BASIS_ATURAN[i][j] - 1,
                })
    batas_keluaran = [0.0] * 5
    for aturan in aturan_aktif:
        k = aturan["keluaran"]
        batas_keluaran[k] = max(batas_keluaran[k], aturan["alfa"])

    def gabungan(z):
        awal = keanggotaan(z, PUNCAK_KELUARAN)
        # min(batas, awal) adalah pemotongan; max adalah penggabungan.
        return max(min(batas_keluaran[k], awal[k]) for k in range(5))

    # Integral numerik atas SELURUH rentang 1-5, bukan tabel contoh.
    # Bobot 1/2 pada kedua ujung merupakan aturan integrasi trapesium.
    langkah = 4.0 / JUMLAH_INTERVAL
    total_luas, total_momen = [], []
    for i in range(JUMLAH_INTERVAL + 1):
        z = 1.0 + i * langkah
        mu = gabungan(z)
        bobot = 0.5 if i in (0, JUMLAH_INTERVAL) else 1.0
        total_luas.append(bobot * mu)
        total_momen.append(bobot * z * mu)
    luas = langkah * math.fsum(total_luas)
    momen = langkah * math.fsum(total_momen)
    if luas <= 0:
        raise ValueError("Tidak ada keluaran aktif; periksa basis aturan.")
    skor = momen / luas
    # Label hasil: kategori dengan keanggotaan TERBESAR pada skor crisp.
    # Ini pilihan pelabelan hasil, bukan ambang klasifikasi jurnal.
    mu_skor = keanggotaan(skor, PUNCAK_KELUARAN)
    terbesar = max(mu_skor)
    kategori = " / ".join(NAMA_KELUARAN[k] for k, nilai in enumerate(mu_skor)
                           if math.isclose(nilai, terbesar, abs_tol=1e-12))
    return {"hujan": hujan, "elevasi": elevasi, "mu_hujan": mu_hujan,
            "mu_elevasi": mu_elevasi, "aturan": aturan_aktif,
            "batas": batas_keluaran, "luas": luas, "momen": momen,
            "skor": skor, "kategori": kategori, "gabungan": gabungan}


# 2. MENAMPILKAN PENJELASAN PERHITUNGAN

def garis():
    print("-" * 78)


def tampil_hasil(hasil):
    print("\n" + "=" * 78)
    print(" HASIL PENILAIAN KERAWANAN BANJIR")
    print("=" * 78)
    print(f"{'Wilayah':<24}: {hasil['nama']}")
    print(f"{'Curah hujan tahunan':<24}: {hasil['hujan']:g} mm/tahun")
    print(f"{'Elevasi':<24}: {hasil['elevasi']:g} meter")
    garis()
    print(f"{'Skor kerawanan':<24}: {hasil['skor']:.3f} dari 5")
    print(f"{'Tingkat kerawanan':<24}: {hasil['kategori']}")
    garis()
    print("Penilaian berdasarkan dua faktor: curah hujan tahunan dan elevasi.")


def tabel(judul, kolom, baris):
    """Tabel terminal dengan lebar kolom mengikuti isinya."""
    teks = [[str(v) for v in row] for row in baris]
    lebar = [max(len(str(k)), *(len(row[i]) for row in teks))
             for i, k in enumerate(kolom)]
    garis_tabel = "+" + "+".join("-" * (n + 2) for n in lebar) + "+"
    def cetak(row):
        print("| " + " | ".join(str(v).ljust(n) for v, n in zip(row, lebar)) + " |")
    print("\n" + judul)
    print(garis_tabel)
    cetak(kolom)
    print(garis_tabel)
    for row in teks:
        cetak(row)
    print(garis_tabel)


def tampil_rumus_input(x, puncak, nama, judul):
    nilai = keanggotaan(x, puncak)
    baris = []
    for k, label in enumerate(nama):
        if k == 0 and x <= puncak[0]:
            bagian, rumus = "Penuh", f"x ≤ {puncak[0]:g}"
        elif k == len(puncak)-1 and x >= puncak[-1]:
            bagian, rumus = "Penuh", f"x ≥ {puncak[-1]:g}"
        elif nilai[k] == 0:
            if k < len(puncak)-1 and x >= puncak[k+1]:
                rumus = f"x ≥ {puncak[k+1]:g}"
            else:
                rumus = f"x ≤ {puncak[k-1]:g}"
            bagian = "Nol"
        elif x == puncak[k]:
            bagian, rumus = "Puncak", f"x = {puncak[k]:g}"
        elif x < puncak[k]:
            a, b = puncak[k-1], puncak[k]
            bagian = "Naik"
            rumus = f"({x:g} − {a:g}) ÷ ({b:g} − {a:g}) = {x-a:g} ÷ {b-a:g}"
        else:
            b, c = puncak[k], puncak[k+1]
            bagian = "Turun"
            rumus = f"({c:g} − {x:g}) ÷ ({c:g} − {b:g}) = {c-x:g} ÷ {c-b:g}"
        baris.append([label, bagian, rumus, f"{nilai[k]:.6f}"])
    tabel(judul, ["Kategori", "Posisi", "Perhitungan / kondisi", "μ"], baris)


def rumus_keluaran(k):
    """Fungsi awal dari kategori keluaran, pada semesta 1-5."""
    b = k+1
    if k == 0:
        return "μ(z) = 2 − z, untuk 1 ≤ z < 2; μ(z) = 0, untuk 2 ≤ z ≤ 5"
    if k == 4:
        return "μ(z) = 0, untuk 1 ≤ z ≤ 4; μ(z) = z − 4, untuk 4 < z ≤ 5"
    return (f"μ(z) = 0 di luar ({b-1}, {b+1}); "
            f"μ(z) = z − {b-1}, untuk {b-1} < z ≤ {b}; "
            f"μ(z) = {b+1} − z, untuk {b} < z < {b+1}")


def tampil_detail(hasil):
    print("\n" + "=" * 78)
    print(" RINCIAN PERHITUNGAN")
    print("=" * 78)
    print("μ = derajat keanggotaan; α = kekuatan aturan. Keduanya bernilai 0–1.")
    print("x = nilai input; z = posisi skor keluaran pada skala 1–5.")
    print("Nilai tampilan dibulatkan; perhitungan menggunakan nilai asli.")
    print("\n1. FUZZIFIKASI — MENGHITUNG KEANGGOTAAN INPUT")
    print("a = titik awal μ = 0; b = puncak μ = 1; c = titik akhir μ = 0.")
    print("Bagian naik: μ(x) = (x − a) ÷ (b − a)")
    print("Bagian turun: μ(x) = (c − x) ÷ (c − b)")
    print("Pada puncak μ = 1; pada bagian nol μ = 0.")
    print("Kategori ujung menggunakan fungsi bahu dengan bagian penuh μ = 1.")
    tampil_rumus_input(hasil['hujan'], PUNCAK_HUJAN, NAMA_HUJAN,
                      f"CURAH HUJAN: x = {hasil['hujan']:g} mm/tahun")
    tampil_rumus_input(hasil['elevasi'], PUNCAK_ELEVASI, NAMA_ELEVASI,
                      f"ELEVASI: x = {hasil['elevasi']:g} meter")

    print("\n2. ATURAN AKTIF — MENENTUKAN KEKUATAN ATURAN")
    print("α = MIN(μ hujan; μ elevasi). Aturan aktif memiliki α > 0.")
    print(f"Jumlah aturan aktif: {len(hasil['aturan'])}")
    tabel("Aturan JIKA–DAN–MAKA", ["Aturan", "JIKA hujan", "DAN elevasi", "MAKA kerawanan"],
          [[f"R{i}", a['hujan'], a['elevasi'], NAMA_KELUARAN[a['keluaran']]]
           for i, a in enumerate(hasil['aturan'], 1)])
    tabel("Kekuatan aturan", ["Aturan", "Perhitungan α", "α"],
          [[f"R{i}", f"MIN({a['mu_hujan']:.6f}; {a['mu_elevasi']:.6f})", f"{a['alfa']:.6f}"]
           for i, a in enumerate(hasil['aturan'], 1)])
    print("\nDASAR PENETAPAN KELUARAN MAKA")
    print("Keluaran aturan sudah ditetapkan dalam basis pengetahuan.")
    print("Acuan rancangan: q = (15 × s_h + 10 × s_e) ÷ 25.")
    print("s_h dan s_e = skor kelas hujan dan elevasi; bobot acuannya 15 dan 10.")
    print("Kategori terdekat terhadap q: 1 Sangat rendah; 2 Rendah; 3 Sedang;")
    print("4 Tinggi; 5 Sangat tinggi.")
    baris = []
    for i, a in enumerate(hasil['aturan'], 1):
        sh = SKOR_KELAS_HUJAN[NAMA_HUJAN.index(a['hujan'])]
        se = SKOR_KELAS_ELEVASI[NAMA_ELEVASI.index(a['elevasi'])]
        total = BOBOT_HUJAN*sh + BOBOT_ELEVASI*se
        q = total/(BOBOT_HUJAN+BOBOT_ELEVASI)
        baris.append([f"R{i}", f"(15 × {sh} + 10 × {se}) ÷ 25 = {total} ÷ 25",
                      f"{q:g}", NAMA_KELUARAN[a['keluaran']]])
    tabel("Penetapan MAKA", ["Aturan", "Perhitungan", "q", "Keluaran"], baris)
    print("q digunakan menyusun kategori aturan, bukan skor akhir wilayah.")

    print("\n3. PEMOTONGAN — MEMBATASI KEANGGOTAAN KELUARAN")
    print("μ Rᵢ(z) = MIN(αᵢ; μ keluaranᵢ(z)).")
    print("Keanggotaan keluaran dibatasi agar tidak melebihi α aturan.")
    print("\nFUNGSI KELUARAN YANG DIGUNAKAN (rentang skor 1–5)")
    for k in sorted({a['keluaran'] for a in hasil['aturan']}):
        print(f"\n{NAMA_KELUARAN[k]}:")
        # Satu bagian per baris supaya rumus tidak terpotong di terminal.
        for bagian in rumus_keluaran(k).split('; '):
            print(f"  {bagian}")
    tabel("Pemotongan setiap aturan", ["Aturan", "Keluaran", "α", "Operasi pada setiap titik skor"],
          [[f"R{i}", NAMA_KELUARAN[a['keluaran']], f"{a['alfa']:.6f}",
            f"μ R{i}(z) = MIN(α{i}; μ {NAMA_KELUARAN[a['keluaran']].lower()}(z))"]
           for i, a in enumerate(hasil['aturan'], 1)])
    print("Operasi memakai α asli sebelum pembulatan.")

    print("\n4. AGREGASI — MENGGABUNGKAN KELUARAN ATURAN")
    langkah = 4/JUMLAH_INTERVAL
    tabel("Ketelitian penggabungan", ["Pengaturan", "Nilai"], [
        ["Jumlah aturan aktif", len(hasil['aturan'])], ["Rentang skor", "1–5"],
        ["Jarak antartitik", f"{langkah:g}"], ["Jumlah interval", JUMLAH_INTERVAL],
        ["Jumlah titik skor", JUMLAH_INTERVAL+1]])
    print(f"N = ((5 − 1) ÷ {langkah:g}) + 1 = {JUMLAH_INTERVAL+1}")
    aturan_teks = '; '.join(f"μ R{i}(z)" for i in range(1, len(hasil['aturan'])+1))
    print(f"\nμ gabungan(z) = MAX({aturan_teks})")
    print("Dengan:")
    for i, a in enumerate(hasil['aturan'], 1):
        print(f"μ R{i}(z) = MIN(α{i}; μ {NAMA_KELUARAN[a['keluaran']].lower()}(z))")
    print("Pada setiap z, sistem mengambil μ terbesar dari semua keluaran")
    print("aturan setelah dipotong. Proses dilakukan pada seluruh titik skor.")

    print("\n5. DEFUZZIFIKASI — MENGHITUNG SKOR AKHIR")
    tabel("Pengaturan perhitungan", ["Pengaturan", "Nilai"], [
        ["Metode", "Centroid"], ["Integrasi numerik", "Trapesium"],
        ["Rentang integrasi", "1–5"], ["Jarak antartitik (Δz)", f"{langkah:g}"],
        ["Jumlah titik", JUMLAH_INTERVAL+1]])
    print("\nSkor akhir = [∫₁⁵ z × μ gabungan(z) dz] ÷ [∫₁⁵ μ gabungan(z) dz]")
    print(f"zᵢ = 1 + i × Δz, untuk i = 0, 1, ..., {JUMLAH_INTERVAL}")
    print("wᵢ = 0.5 pada titik pertama/terakhir; wᵢ = 1 pada titik lainnya.")
    print("Luas  ≈ Δz × Σ [wᵢ × μ gabungan(zᵢ)]")
    print("Momen ≈ Δz × Σ [wᵢ × zᵢ × μ gabungan(zᵢ)]")
    print(f"Penjumlahan Σ mencakup semua {JUMLAH_INTERVAL+1} titik.")
    tabel("Hasil perhitungan", ["Hasil (rumus)", "Nilai"], [
        ["Luas (∫₁⁵ μ gabungan(z) dz)", f"{hasil['luas']:.9f}"],
        ["Momen (∫₁⁵ z × μ gabungan(z) dz)", f"{hasil['momen']:.9f}"],
        ["Skor akhir (momen ÷ luas)", f"{hasil['skor']:.6f}"]])
    print(f"Skor akhir = {hasil['momen']:.9f} ÷ {hasil['luas']:.9f}")
    print(f"           ≈ {hasil['skor']:.6f} ≈ {hasil['skor']:.3f} dari 5")

    print("\n6. MENENTUKAN LABEL TINGKAT KERAWANAN")
    print("Pilih kategori dengan μ terbesar pada skor akhir.")
    z = hasil['skor']
    nilai = keanggotaan(z, PUNCAK_KELUARAN)
    baris = []
    for k, nama in enumerate(NAMA_KELUARAN):
        if nilai[k] == 0: rumus = "Pada bagian nol"
        elif z == k+1: rumus = "Pada puncak: μ = 1"
        elif z < k+1: rumus = f"{z:.6f} − {k}"
        else: rumus = f"{k+2} − {z:.6f}"
        baris.append([nama, rumus, f"{nilai[k]:.6f}"])
    tabel(f"Keanggotaan keluaran pada z ≈ {z:.6f}",
          ["Kategori", "Perhitungan", "μ"], baris)
    print("\n" + "=" * 78)
    print(" KESIMPULAN")
    print("=" * 78)
    print(f"{hasil.get('nama', 'Wilayah')} memiliki tingkat kerawanan {hasil['kategori'].upper()}")
    print("berdasarkan curah hujan tahunan dan elevasi.")
    print(f"Skor kerawanan: {hasil['skor']:.3f} dari 5")
    print("=" * 78)



# 3. INPUT TERMINAL DAN VALIDASI

class KeluarProgram(Exception):
    """Perintah keluar pengguna, terpisah dari kesalahan input angka."""


def baca_input(pesan):
    teks = input(pesan).strip()
    if teks.casefold() == "exit":
        raise KeluarProgram
    return teks


def input_angka(pesan, minimum=None):
    while True:
        try:
            nilai = parse_angka(baca_input(pesan))
            if minimum is not None and nilai < minimum:
                raise ValueError(f"Nilai harus >= {minimum}.")
            return nilai
        except ValueError as error:
            print(f"Input tidak valid: {error} Silakan ulangi.")


def tanya_ya_tidak(pesan):
    while True:
        jawab = baca_input(pesan).lower()
        if jawab in ("y", "t"):
            return jawab == "y"
        print("Jawaban harus y (ya) atau t (tidak).")


def tambah_wilayah():
    return tanya_ya_tidak("\nHitung wilayah lain? (y/t): ")


def ranking(daftar):
    """Competition ranking: skor sama mendapat prioritas sama (1,1,3)."""
    urut = sorted(daftar, key=lambda h: h["skor"], reverse=True)
    peringkat = 0
    sebelumnya = None
    for posisi, hasil in enumerate(urut, 1):
        if sebelumnya is None or not math.isclose(hasil["skor"], sebelumnya, rel_tol=0, abs_tol=1e-12):
            peringkat = posisi
        hasil["prioritas"] = peringkat
        sebelumnya = hasil["skor"]
    return urut


def tampil_ranking(daftar):
    print("\n" + "=" * 78)
    print(" PRIORITAS KERAWANAN BANJIR: SKOR TERBESAR KE TERKECIL")
    print("=" * 78)

    print(f"{'Prioritas':<10} {'Wilayah':<24} {'Skor / 5':>10}  {'Kategori':<20}")
    garis()
    for h in ranking(daftar):
        print(f"{h['prioritas']:<10} {h['nama']:<24} {h['skor']:>10.6f}  {h['kategori']:<20}")
    terurut = ranking(daftar)
    tertinggi = [h for h in terurut if h["prioritas"] == 1]
    print("\nKESIMPULAN:")
    for h in tertinggi:
        print(f"Skor tertinggi diperoleh {h['nama']} dengan kerawanan "
              f"{h['kategori']} dan skor {h['skor']:.6f} dari 5.")
    if len(tertinggi) > 1:
        print("Beberapa kasus memiliki skor tertinggi yang sama.")
    if len(daftar) == 1:
        print("Hanya satu kasus dimasukkan, sehingga belum ada pembanding.")
    print("Prioritas ditentukan berdasarkan skor kerawanan tertinggi.")


def main():
    print("=" * 78)
    print(" SISTEM PAKAR KERAWANAN BANJIR SUATU WILAYAH - FUZZY MAMDANI")
    print("=" * 78)
    print("Input: rata-rata curah hujan tahunan (mm/tahun) dan elevasi (meter).")
    print("Keluaran: skor 1-5. Semakin besar, semakin rawan menurut model.")
    print("Masukkan angka tanpa pemisah ribuan. Desimal boleh titik atau koma.")
    print("Ketik exit pada pertanyaan mana pun untuk langsung keluar.")
    if "--demo" in sys.argv:
        hasil = hitung_kerawanan(2200.0, 48.0)
        hasil["nama"] = "Wilayah contoh"
        tampil_detail(hasil)
        tampil_ranking([hasil])
        return
    daftar = []
    while True:
        print(f"\nPENILAIAN WILAYAH {len(daftar) + 1}")
        garis()
        while True:
            nama = baca_input("Nama wilayah (maksimum 24 karakter): ")
            if not nama or len(nama) > 24:
                print("Nama harus terisi dan maksimal 24 karakter.")
            else:
                break
        hujan = input_angka("Curah hujan rata-rata tahunan (mm/tahun): ", minimum=0)
        elevasi = input_angka("Elevasi terhadap permukaan laut (meter): ")
        hasil = hitung_kerawanan(hujan, elevasi)
        hasil["nama"] = nama
        daftar.append(hasil)
        tampil_hasil(hasil)
        if tanya_ya_tidak("\nTampilkan rincian perhitungan? (y/t): "):
            tampil_detail(hasil)
        if not tambah_wilayah():
            break
    if tanya_ya_tidak("\nUrutkan hasil berdasarkan prioritas tertinggi? (y/t): "):
        tampil_ranking(daftar)
    else:
        print("Pengurutan tidak dilakukan. Hasil penilaian telah ditampilkan.")
    print("\nSelesai.")


if __name__ == "__main__":
    try:
        main()
    except KeluarProgram:
        print("\nPerintah exit diterima. Program ditutup.")
    except (KeyboardInterrupt, EOFError):
        print("\nInput dihentikan. Program selesai.")
