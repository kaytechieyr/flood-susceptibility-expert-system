# Sistem Pakar Kerawanan Banjir Suatu Wilayah

Program terminal Python 3.9+ dengan dua input: rata-rata curah hujan tahunan (mm/tahun) dan elevasi terhadap permukaan laut (meter). Skor akhir 1–5 memakai fuzzy Mamdani. Tidak perlu memasang paket pip.

## Menjalankan di terminal VS Code / PowerShell

Buka folder hasil ekstraksi, lalu:

```powershell
python sistem_pakar_banjir.py
```

Jika Windows menggunakan Python Launcher:

```powershell
py sistem_pakar_banjir.py
```

Langsung masukkan nama wilayah, curah hujan, lalu elevasi. Setelah hasil muncul, pilih y untuk menghitung kasus lain atau t untuk selesai. Satu wilayah saja diperbolehkan. Setelah selesai memasukkan kasus, program bertanya apakah hasil ingin diurutkan. Jika y, program menampilkan ranking dan kesimpulan semua wilayah dengan skor tertinggi. Semua hasil dihitung dan ditampilkan di terminal. Lebih dari satu wilayah menghasilkan ranking berdasarkan skor asli tanpa pembulatan. Tidak ada file data yang disimpan otomatis; output sesi muncul di terminal.

Contoh isian:

```text
Nama wilayah: Wilayah A
Curah hujan: 2200
Elevasi: 48
Hitung wilayah lain? (y/t): t
Urutkan hasil berdasarkan prioritas tertinggi? (y/t): y
```

Hasil: skor sekitar **3,845745 / 5** atau **3,846** jika ditampilkan tiga desimal; label dominan **Tinggi**. Aturan aktif memiliki alfa 0,1; 0,1; 0,6; 0,4. Nomor aturan di program merujuk indeks dalam seluruh 25 aturan, sehingga berbeda dari penomoran empat aturan aktif pada penjelasan belajar.

Demo tanpa mengetik input:

```powershell
python sistem_pakar_banjir.py --demo
```

## Validasi

- Huruf, kosong, NaN, infinity, dan format angka salah ditolak lalu diminta ulang.
- Curah hujan harus >= 0; elevasi negatif diperbolehkan untuk lokasi di bawah permukaan laut.
- Nama wilayah wajib terisi dan maksimum 24 karakter. Nama yang sama diperbolehkan untuk pengujian input berbeda.
- Koma/titik diterima sebagai pemisah desimal. Jangan memakai pemisah ribuan: tulis **2200**, bukan **2.200** (2.200 dibaca 2,2).
- Ctrl+C atau akhir input menghentikan program dengan pesan yang rapi.

## Basis pengetahuan dan asal angka

Acuan: Hutauruk dkk. (2020), *GIS-based Flood Susceptibility Mapping in Central Sulawesi*, Forum Geografi 34(2), DOI 10.23917/forgeo.v34i2.10667.
https://journals.ums.ac.id/fg/article/view/10667/6268

Kategori hujan dari Tabel 2: <1000; 1000–1500; 1500–2000; 2000–2500; >2500 mm/tahun, skor kelas 1–5. Elevasi: <10; 10–50; 50–100; 100–200; >200 meter, skor kelas 5–1. Bobot jurnal hujan 15 dan elevasi 10.

Jurnal aslinya menggunakan enam faktor dengan scoring dan overlay GIS, bukan Mamdani. Program ini pengembangan pembelajaran dua faktor. Titik fuzzy, basis aturan, skala keluaran dan pelabelan hasil adalah rancangan yang belum divalidasi pakar atau data kejadian banjir. Jangan menyatakan aturan fuzzy ini tersedia dalam jurnal.

Puncak input hujan: 1000, 1250, 1750, 2250, 2500. Puncak elevasi: 10, 30, 75, 150, 200. Kategori tengah segitiga, dua ujung fungsi bahu. Titik nol kategori tengah adalah puncak tetangga. Di luar puncak ujung, kategori ujung memiliki keanggotaan penuh.

Keluaran memiliki puncak 1, 2, 3, 4, 5. Kategori keluaran adalah sangat rendah, rendah, sedang, tinggi, sangat tinggi. MAKA setiap aturan diusulkan dari q=(15*skor_kelas_hujan+10*skor_kelas_elevasi)/25, dibulatkan ke kategori terdekat. Perhitungan ini hanya menetapkan kategori aturan; skor pengguna dihitung melalui Mamdani.

## Alur mesin inferensi

1. Fuzzifikasi semua kategori dua input.
2. Pilih aturan dengan keanggotaan > 0; AND menggunakan MIN.
3. Potong keanggotaan fungsi MAKA sesuai alfa (MIN).
4. Gabungkan keluaran aturan pada posisi skor sama (MAX).
5. Centroid = integral z*mu(z) / integral mu(z).
6. Integral numerik trapesium, 4000 interval/4001 titik, jarak 0,001.
7. Label hasil: kategori keluaran dengan keanggotaan terbesar pada skor crisp; ikatan label ditampilkan bersama. Ini bukan ambang kategori akhir jurnal.
8. Urutkan wilayah berdasarkan skor akhir terbesar. Skor yang sama mendapat prioritas sama (competition ranking: 1,1,3).

Tabel titik berjarak 0,5 pada terminal hanya contoh penjelasan. Tabel itu **tidak** dipakai menghitung centroid; perhitungan memakai seluruh 4001 titik. Karena keluaran ujung berbentuk bahu dan dihitung dengan centroid, skor tidak harus mencapai persis 1 atau 5: pusat bahu penuh masing-masing mendekati 1,333 dan 4,667. Skala semesta keluarannya tetap 1–5.

Ini skor kerawanan model dua faktor, bukan persentase peluang banjir atau ramalan banjir harian.

## Mengapa dua input?

Dua input menjaga model sesuai dengan alur yang sudah dipelajari, memerlukan data numerik yang lebih mudah disiapkan, dan cukup untuk demonstrasi 25 aturan. Enam faktor memberi cakupan lebih luas tetapi memerlukan data lereng, tanah, penggunaan lahan dan kepadatan drainase serta perancangan ulang basis pengetahuan. Python bisa menjalankan keduanya; pilihan jumlah faktor harus mengikuti tujuan dan ketersediaan data, bukan bahasa pemrograman. Penambahan faktor tidak otomatis membuat model lebih akurat tanpa validasi.


Hasil semua kasus disimpan dalam list selama sesi program. Ketika program ditutup, data sesi tidak disimpan permanen. Pertanyaan pengurutan muncul setelah pengguna memilih tidak menambah kasus. Centroid mengevaluasi 4.001 titik (1 sampai 5, langkah 0,001), bukan menjalankan 4.001 kali pembelajaran atau optimasi.
