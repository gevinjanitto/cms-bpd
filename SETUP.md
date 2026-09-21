# COMPLIANCE MANAGEMENT SYSTEM Bank BPD Bali

## Arsitektur mandiri
- Frontend React 19 + CRA/CRACO standar; tidak memakai plugin, overlay, analytics, atau SDK khusus platform.
- Backend FastAPI + Python 3.11, SDK resmi Cloudinary, Pillow, openpyxl.
- MongoDB menyimpan data dan dokumen PDF/DOCX privat melalui GridFS. Tidak bergantung filesystem ephemeral.
- Gambar opsional di Cloudinary. Logo, font Manrope, dan ilustrasi awal disertakan lokal; tidak ada runtime request ke penyedia aset sebelumnya.
- Login username/password + CAPTCHA gambar satu kali pakai yang diverifikasi server. Password bcrypt, token opaque dengan revocation, rate limit, dan lock 5 menit setelah 3 password salah.

## Deploy ke Railway (dua service, satu repo)
Error `Railpack failed to prepare the build` terjadi ketika service dibangun dari root repo tanpa Root Directory. Perbaikan:

1. **Service backend**: Settings → Source → Root Directory = `backend`. Builder otomatis memakai `backend/Dockerfile` via `backend/railway.json`. (Jika Root Directory dikosongkan, `Dockerfile` + `railway.json` di root repo juga membangun backend.)
   Variables: `MONGO_URL` (Atlas, format `mongodb+srv://...`), `DB_NAME`, `CORS_ORIGINS` (URL publik frontend, mis. `https://cms-bpd-frontend.up.railway.app`), `BOOTSTRAP_PASSWORD`, `SEED_SAMPLE_DATA`, opsional `CLOUDINARY_*`. `PORT` diisi Railway.
   Setelah deploy: Settings → Networking → Generate Domain, catat URL backend.
2. **Service frontend**: New Service → GitHub repo yang sama → Root Directory = `frontend`. Builder memakai `frontend/Dockerfile` via `frontend/railway.json` (build CRA lalu disajikan `serve` sebagai SPA).
   Variables: `REACT_APP_BACKEND_URL` = URL backend dari langkah 1 tanpa `/api` dan tanpa slash akhir. Variabel ini dipakai saat build (ARG), redeploy bila berubah.
3. Generate Domain untuk frontend, lalu pastikan domain tersebut sudah ada di `CORS_ORIGINS` backend (redeploy backend jika baru ditambahkan).
4. MongoDB Atlas: Network Access → allow `0.0.0.0/0` (Railway tidak memiliki IP statis) dan user database dengan hak readWrite.

## Backend
1. Root directory service: `backend`.
2. Salin `.env.example` menjadi `.env` untuk penggunaan lokal, atau isi variabel rahasia di layanan hosting.
3. Wajib: `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, `BOOTSTRAP_PASSWORD`, `PORT`.
4. `CORS_ORIGINS` berisi origin frontend lengkap (https), dapat dipisahkan koma, tanpa slash di akhir. Jangan gunakan wildcard untuk penggunaan nyata.
5. MongoDB bisa Atlas atau instance lain. Pastikan koneksi jaringan/IP allowlist dan TLS sesuai provider.
6. Jalankan `pip install -r requirements.txt`, lalu `python run.py`.
7. Health endpoint: `GET /api/health`.

Konfigurasi container dan service tersedia di `backend/Dockerfile` dan `backend/railway.json`. Hosting mengisi `PORT` secara otomatis; aplikasi membacanya dari environment. Dalam lingkungan pengembangan bawaan, service tetap di port 8001 melalui supervisor.

## Frontend
1. Root directory: `frontend`.
2. Isi `REACT_APP_BACKEND_URL` dengan URL publik backend, tanpa `/api` dan tanpa slash di akhir.
3. Opsional direkomendasikan: `GENERATE_SOURCEMAP=false`.
4. Install `yarn install --frozen-lockfile`; build `yarn build`; output `build`.
5. `frontend/vercel.json` menyediakan SPA rewrites dan header dasar. URL API adalah build-time variable: build ulang bila berubah.
6. Gunakan Node 20 atau 22. Three.js 0.181.0 dipasangkan dengan React Three Fiber 9.7, tanpa dependency kamera yang mensyaratkan Node 22. Versi Three ini dipilih untuk kompatibilitas API Clock yang masih digunakan Fiber; bayangan memakai PCFShadowMap secara eksplisit.

## Akun awal
| Username | Peran |
|---|---|
| admin | Administrator |
| supervisor | Supervisor |
| karyawan | Karyawan |
| direksi | Direksi |

Password awal seluruh akun diambil dari `BOOTSTRAP_PASSWORD` ketika akun pertama kali dibuat. Untuk lingkungan kerja saat ini sudah diisi sesuai permintaan pengguna. Tidak ada password bawaan yang ditanam dalam source code.

Setelah login, ikon kunci pada header membuka perubahan password. Mengubah environment bootstrap tidak mengubah password akun yang sudah ada. Password plaintext tidak dikembalikan dalam API dan disimpan terpisah dari data pengguna.

`SEED_SAMPLE_DATA=true` memuat contoh sintetis saat database kosong; pilih `false` untuk database baru tanpa contoh ketentuan/kuis. Pilihan ini tidak menghapus data yang sudah ada. Untuk penggunaan bank nyata, gunakan data resmi dan tata kelola akun individual, bukan password awal bersama.

## Cloudinary
Backend variables:
```
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```
Sesudah terisi dan backend dimulai ulang, buka Pengaturan → Identitas & Gambar. Administrator dapat mengunggah logo atau ilustrasi login. SDK resmi melakukan upload bertanda tangan dari server; public_id/secure_url disimpan di MongoDB. Hanya gambar PNG/JPEG/WebP terverifikasi, maksimal 5 MB. API secret tidak pernah dikirim ke frontend.

Tanpa kredensial, status jelas “Belum dikonfigurasi”, upload gambar tidak aktif, aset lokal tetap digunakan. Upload PDF/DOCX tetap berfungsi karena dokumen disimpan di GridFS, bukan Cloudinary.

## Ekspor
- CSV: UTF-8 BOM, deklarasi `sep=;`, delimiter titik koma, quote field yang perlu, label status Bahasa Indonesia, waktu WITA, proteksi formula injection.
- XLSX: judul organisasi, filter periode/unit, header hijau, lebar kolom, wrap text, zebra rows, nilai numerik, waktu Excel, freeze header dan autofilter.
- Ekspor monitoring mengikuti tab, periode, unit, pencarian dan filter kuis yang dipilih.

## Batasan integrasi
AD/SSO bank, mail server/OTP, dan SIM SDM belum terhubung. CAPTCHA ini self-hosted, bukan reCAPTCHA. Siapkan observabilitas, backup, pemindaian malware dokumen, serta pengujian keamanan dan beban sebelum penggunaan produksi bank. File GridFS dilayani lewat API dengan verifikasi hak akses.

## Portabilitas
Tidak perlu akun, token, plugin, atau layanan integrasi dari pembuat aplikasi. File environment yang lama mungkin masih memiliki variabel tidak terpakai; konfigurasi mandiri hanya menggunakan template `.env.example` yang bersih. Jangan memasukkan `.env`, cache, atau laporan pengujian ke image container.