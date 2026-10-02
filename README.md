# Sistem Pakar Kerawanan Banjir Suatu Wilayah

Sistem pakar berbasis Python yang menggunakan metode **Fuzzy Mamdani** untuk menilai kerawanan banjir berdasarkan **curah hujan tahunan** dan **elevasi**.

Program berjalan di terminal dan menghasilkan **skor kerawanan pada skala 1–5**. Hasil beberapa wilayah dapat dibandingkan dan diurutkan berdasarkan skor tertinggi.

## Fitur

- Menghitung kerawanan satu atau beberapa wilayah.
- Menampilkan skor dan tingkat kerawanan.
- Menampilkan rincian perhitungan jika pengguna menginginkannya.
- Menyediakan rumus dan penjelasan pada setiap tahap perhitungan.
- Mengurutkan hasil berdasarkan prioritas kerawanan tertinggi.
- Memvalidasi input angka dan jawaban pengguna.
- Mendukung perintah `exit` pada setiap pertanyaan input.

## Persyaratan

- Python 3.9 atau versi lebih baru.
- Terminal, seperti terminal VS Code atau PowerShell.

Program hanya menggunakan pustaka bawaan Python sehingga **tidak memerlukan instalasi paket tambahan**.

## File Proyek

- `sistem_pakar_banjir.py`: kode utama untuk menjalankan sistem pakar.
- `README.md`: panduan penggunaan dan penjelasan model.

## Cara Menjalankan

Buka terminal pada folder proyek, kemudian jalankan:

```powershell
python sistem_pakar_banjir.py
```

Jika menggunakan Python Launcher di Windows:

```powershell
py sistem_pakar_banjir.py
```

Jika nama file kode diubah, sesuaikan nama file pada perintah tersebut.

## Cara Menggunakan

1. Masukkan nama wilayah.
2. Masukkan rata-rata curah hujan tahunan dalam **mm/tahun**.
3. Masukkan elevasi terhadap permukaan laut dalam **meter**.
4. Program menampilkan skor dan tingkat kerawanan.
5. Pilih apakah ingin melihat rincian perhitungan.
6. Pilih apakah ingin menghitung wilayah lain.
7. Setelah selesai, pilih apakah hasil ingin diurutkan berdasarkan prioritas.

Gunakan:

- `y` untuk **ya**.
- `t` untuk **tidak**.
- `exit` untuk **langsung keluar**.

Satu wilayah saja dapat dihitung. Perbandingan prioritas membutuhkan lebih dari satu hasil penilaian.

## Contoh Penggunaan

Masukkan data berikut:

```text
Nama wilayah: Wilayah A
Curah hujan tahunan (mm/tahun): 2543
Elevasi (meter): 32
```

Hasil penilaiannya:

```text
Skor kerawanan    : 4.572 dari 5
Tingkat kerawanan : Sangat tinggi
```

Contoh lain:

- Curah hujan **2200 mm/tahun** dan elevasi **48 meter** menghasilkan skor sekitar **3,846**, dengan tingkat kerawanan **tinggi**.
- Curah hujan **2543 mm/tahun** dan elevasi **32 meter** menghasilkan skor sekitar **4,572**, dengan tingkat kerawanan **sangat tinggi**.

Hasil dihitung dari input pengguna, bukan diambil dari daftar skor yang sudah tersedia.

## Ketentuan Input

- Nama wilayah wajib diisi dan maksimal 24 karakter.
- Nama yang sama dapat digunakan untuk mencoba input berbeda.
- Curah hujan harus berupa angka yang tidak negatif.
- Elevasi negatif diperbolehkan untuk wilayah di bawah permukaan laut.
- Desimal dapat menggunakan titik atau koma, misalnya `48.5` atau `48,5`.
- Jangan menggunakan pemisah ribuan: tulis **`2200`**, bukan **`2.200`**.
- Input angka yang kosong, berupa huruf, `NaN`, atau infinity akan ditolak dan diminta ulang.
- Jawaban pilihan harus `y` atau `t`.
- Perintah `exit` tidak membedakan huruf besar dan kecil.
- Keluar menggunakan `exit` tidak otomatis menampilkan ranking.

## Cara Kerja Fuzzy Mamdani

### 1. Fuzzifikasi

Program mengubah angka input menjadi derajat keanggotaan **μ**, dengan nilai antara **0 dan 1**.

Kategori curah hujan:

- Sangat kering.
- Kering.
- Cukup basah.
- Basah.
- Sangat basah.

Kategori elevasi:

- Sangat rendah.
- Rendah.
- Sedang.
- Tinggi.
- Sangat tinggi.

Kategori tengah menggunakan fungsi segitiga, sedangkan dua kategori ujung menggunakan fungsi bahu.

Titik keanggotaan penuh curah hujan:

- Sangat kering: input ≤1000 mm/tahun.
- Kering: 1250 mm/tahun.
- Cukup basah: 1750 mm/tahun.
- Basah: 2250 mm/tahun.
- Sangat basah: input ≥2500 mm/tahun.

Titik keanggotaan penuh elevasi:

- Sangat rendah: input ≤10 meter.
- Rendah: 30 meter.
- Sedang: 75 meter.
- Tinggi: 150 meter.
- Sangat tinggi: input ≥200 meter.

Pada kategori tengah, titik nol di kedua sisi menggunakan titik keanggotaan penuh kategori tetangga.

Rumus bagian naik:

```text
μ(x) = (x − a) ÷ (b − a)
```

Rumus bagian turun:

```text
μ(x) = (c − x) ÷ (c − b)
```

Keterangan:

- `x`: nilai input.
- `a`: titik awal dengan keanggotaan 0.
- `b`: titik puncak dengan keanggotaan 1.
- `c`: titik akhir dengan keanggotaan 0.

### 2. Menjalankan Aturan

Basis pengetahuan terdiri dari **25 aturan JIKA–MAKA**, yaitu kombinasi lima kategori curah hujan dan lima kategori elevasi.

Contoh aturan:

> JIKA curah hujan sangat basah DAN elevasi rendah, MAKA kerawanan sangat tinggi.

Kekuatan aturan **α** dihitung menggunakan:

```text
α = MIN(μ hujan; μ elevasi)
```

Artinya, sistem mengambil nilai keanggotaan terkecil dari kedua kondisi.

Hanya aturan dengan **α > 0** yang aktif. Jumlah aturan aktif bergantung pada input pengguna.

### 3. Pemotongan Keluaran

Keanggotaan keluaran setiap aturan dibatasi sesuai kekuatan aturan:

```text
μ hasil aturan(z) = MIN(α; μ keluaran(z))
```

Keterangan:

- `z`: posisi skor keluaran pada skala 1–5.
- `α`: kekuatan aturan.
- `μ keluaran(z)`: keanggotaan awal kategori keluaran.

Nilai keanggotaan yang melebihi α dibatasi menjadi α. Nilai yang lebih kecil tetap seperti semula.

### 4. Penggabungan Keluaran

Keluaran semua aturan aktif digabungkan menggunakan **MAX** pada posisi skor yang sama:

```text
μ gabungan(z) = MAX(μ R1(z); μ R2(z); ...; μ Rn(z))
```

Artinya, sistem mengambil keanggotaan terbesar dari seluruh keluaran aturan setelah dipotong.

Jumlah aturan dalam rumus mengikuti jumlah aturan yang aktif.

### 5. Defuzzifikasi Centroid

Program menghitung satu skor akhir menggunakan rumus:

```text
Skor akhir = [∫₁⁵ z × μ gabungan(z) dz] ÷ [∫₁⁵ μ gabungan(z) dz]
```

Keterangan:

- **Luas:** integral keanggotaan gabungan.
- **Momen:** integral posisi skor dikalikan keanggotaan gabungan.
- **Skor akhir:** momen dibagi luas.

Integral dihitung secara numerik menggunakan metode **trapesium**.

Pengaturan perhitungan:

- Rentang skor: **1–5**.
- Jarak antartitik: **0,001**.
- Jumlah interval: **4.000**.
- Jumlah titik yang dihitung: **4.001**.

Seluruh titik digunakan dalam perhitungan. Rincian terminal menampilkan rumus dan hasil integrasi tanpa menampilkan ribuan baris titik skor.

### 6. Menentukan Tingkat Kerawanan

Kategori keluaran memiliki titik puncak:

- Sangat rendah: **1**.
- Rendah: **2**.
- Sedang: **3**.
- Tinggi: **4**.
- Sangat tinggi: **5**.

Kategori tengah menggunakan fungsi segitiga, sedangkan kategori ujung menggunakan fungsi bahu pada rentang keluaran 1–5.

Label hasil dipilih berdasarkan kategori yang memiliki **μ terbesar pada skor akhir**. Jika terdapat keanggotaan terbesar yang sama, kedua label ditampilkan.

Karena skor dihitung menggunakan centroid, hasilnya tidak harus mencapai tepat 1 atau 5.

## Rincian Perhitungan

Pengguna dapat memilih apakah ingin melihat rincian setelah hasil utama ditampilkan.

Rincian meliputi:

1. Keanggotaan curah hujan dan elevasi beserta rumusnya.
2. Aturan aktif dan kekuatan α.
3. Dasar penetapan keluaran MAKA.
4. Fungsi keluaran dan operasi pemotongan.
5. Rumus penggabungan MAX.
6. Ketelitian perhitungan dan jumlah titik.
7. Rumus centroid serta hasil luas, momen, dan skor akhir.
8. Dasar penentuan label tingkat kerawanan.

Memilih untuk tidak menampilkan rincian **tidak mengubah perhitungan atau hasil skor**.

## Pengurutan Prioritas

Hasil setiap wilayah disimpan selama program berjalan.

Setelah pengguna selesai memasukkan wilayah, program menanyakan apakah hasil ingin diurutkan.

Jika pengguna memilih `y`:

- Hasil diurutkan dari **skor terbesar ke terkecil**.
- Pengurutan menggunakan nilai asli sebelum pembulatan.
- Skor yang sama mendapatkan prioritas yang sama.
- Program menampilkan kesimpulan wilayah dengan skor tertinggi.

Jika hanya satu wilayah dimasukkan, program tetap dapat menampilkan hasilnya, tetapi belum ada wilayah pembanding.

Data hanya disimpan selama sesi dan tidak disimpan permanen setelah program ditutup.

## Sumber dan Dasar Rancangan

Acuan kategori input dan bobot:

Hutauruk dkk. (2020). *GIS-based Flood Susceptibility Mapping in Central Sulawesi*. Forum Geografi, 34(2).

- [Artikel acuan](https://journals.ums.ac.id/fg/article/view/10667/6268)
- DOI: `10.23917/forgeo.v34i2.10667`

Jurnal menggunakan **scoring dan overlay GIS dengan enam faktor**, bukan Fuzzy Mamdani.

Program ini mengadaptasi dua faktor:

- Curah hujan tahunan.
- Elevasi terhadap permukaan laut.

Fungsi keanggotaan, aturan fuzzy, skala keluaran, dan pelabelan hasil merupakan rancangan pengembangan.

Kategori MAKA diusulkan menggunakan skor kelas dan perbandingan bobot jurnal:

```text
q = (15 × skor kelas hujan + 10 × skor kelas elevasi) ÷ 25
```

Dasar penetapannya:

- Bobot curah hujan: **15**.
- Bobot elevasi: **10**.
- Jumlah bobot: **25**.
- Nilai q dibulatkan ke kategori keluaran terdekat.

Rumus tersebut digunakan untuk menyusun basis aturan, **bukan menghitung skor akhir pengguna**. Skor akhir tetap dihitung melalui proses Mamdani dan centroid.

## Batasan

- Model ini merupakan proyek pembelajaran.
- Fungsi keanggotaan dan basis aturan belum divalidasi oleh pakar atau data kejadian banjir.
- Penilaian hanya mempertimbangkan curah hujan tahunan dan elevasi.
- Faktor lain, seperti lereng, jenis tanah, penggunaan lahan, dan kepadatan drainase, belum digunakan.
- Skor menunjukkan kerawanan menurut model dua faktor, **bukan persentase peluang banjir atau prediksi banjir harian**.