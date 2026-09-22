# PRD — CMS Kepatuhan Bank BPD Bali (cms-bpd)

## Problem Statement
Aplikasi asal: Compliance Management System Bank BPD Bali (regulasi, kuis, monitoring, audit; React 19 + FastAPI + MongoDB; UI Bahasa Indonesia nuansa hijau).
Permintaan sesi ini (repo https://github.com/gevinjanitto/cms-bpd):
1. Login gagal "Username atau password tidak sesuai" padahal BOOTSTRAP_PASSWORD (bpdjaya3x) sudah benar → perbaiki.
2. Tambahkan "Design & Develop by MaiHarta" (link https://www.maiharta.com, tab baru) di semua footer copyright tanpa menghapus copyright lama.
3. Deploy: frontend di Vercel (https://cms-bpd.vercel.app), backend di Railway (https://cms-bpd-production.up.railway.app), DB MongoDB Atlas.
4. Permintaan 22 Sep 2026: "lakukan semua perintah yg ada di gambar. Di menu Ketentuan ubah jadi regulasi, ubah semuanya ya termasuk pas buat kuis. di pengaturan hapus identitas gambar dan koneksi sistem (tambahkan pengaturan hubungi yag ada di gambar)". Penegasan: "di gambar sudah saya isikan note ikutkan semuanya itu juga ya".
5. Catatan lampiran: hapus segmen footer "COMPLIANCE MANAGEMENT SYSTEM · Data contoh"; ratakan ikon bantuan ke tengah dan tambahkan pengaturan tautan kontak admin; pindahkan footer copyright/motto/MaiHarta ke paling bawah menggantikan footer lama; hapus caption "Bali Dwipa Jaya · 3D" pada objek interaktif.

## Arsitektur
- Backend FastAPI (port 8001, prefix /api): core, routes, quiz_routes, reports, storage/media, seed, auth. Auth kustom: username + bcrypt + CAPTCHA gambar sekali pakai, token opaque 12 jam, lockout 5 menit setelah 3x gagal, rate limit per IP.
- Frontend React (craco): Login, Dashboard, Regulasi, Kuis, Monitoring, Pengguna, Audit, Pengaturan. Komponen baru React wajib di file .jsx.
- Navigasi Regulasi menggunakan `/regulasi`; `/ketentuan` tetap redirect dengan query/hash. API `/api/documents` dan relasi `document_id` tidak berubah.
- `backend/contact_settings.py`: validasi teks/tautan kontak; GET publik `/api/settings/contact` hanya membuka `contact_label` dan `contact_url`. PUT `/api/settings` tetap administrator-only, invalidasi cache, kompatibel payload numerik lama.
- `frontend/src/components/LoginHelp.jsx` membaca kontak publik. `Settings.jsx` hanya Parameter Kuis, Keamanan Sesi, Hubungi; tidak lagi bergantung pada `/media/status`. `DocumentForm.jsx` dipisah dari halaman dokumen.
- `backend/regulation_migration.py` mengubah hanya teks bawaan sampel dengan ID/nilai tepat saat startup; tidak mengubah konten pengguna, jumlah data, relasi, atau audit tersimpan. Modul audit/notifikasi lama dinormalisasi saat dibaca.
- Akun: admin/supervisor/karyawan/direksi, password dari env BOOTSTRAP_PASSWORD. Lihat memory/test_credentials.md.
- Deploy Railway: backend Root Directory `backend` (backend/Dockerfile), frontend Vercel/Railway dengan REACT_APP_BACKEND_URL saat build. Lihat SETUP.md.

## Yang Sudah Diimplementasikan
### 21 Sep 2026 (sesi sebelumnya)
- FIX LOGIN: initialize_auth menyinkronkan hash password ke BOOTSTRAP_PASSWORD setiap startup.
- Footer credit MaiHarta (komponen DeveloperCredit di components/common.jsx) di Login.jsx (2 footer) dan Layout.jsx.
- Instal three & @react-three/fiber, perbaikan build produksi, pembersihan conflict marker di kode.
- Testing agent iteration_4 & 5: pass.

### Juni 2026 (sesi ini) — login masih gagal di Railway
- Reproduksi: preview Emergent login sukses; backend Railway (cms-bpd-production.up.railway.app) menolak admin/bpdjaya3x → penyebab di lingkungan Railway (env BOOTSTRAP_PASSWORD atau kode lama), bukan di kode repo.
- auth.py: `bootstrap_password()` membersihkan spasi/newline dan tanda kutip pembungkus dari env; log startup "Auth bootstrap selesai"; endpoint diagnostik `GET /api/auth/status` (code_version, bootstrap_password_length, accounts_synced per akun, rehashed) tanpa membocorkan rahasia.
- Bersihkan conflict marker di .gitignore, SETUP.md, memory/PRD.md; SETUP.md ditambah langkah cek /api/auth/status.

### Juni 2026 — "Memuat data..." lama di production
- Pengukuran ke backend Railway: /api/health 0.14s (jaringan OK) tetapi tiap operasi DB ≈0.7–1s dan fetch 100KB results ≈20s → dashboard 40s, monitoring 26s, users 5s. Preview lokal semua <0.2s. Penyebab: koneksi Railway ↔ MongoDB (region berbeda / proxy / tier terbatas), bukan logika aplikasi.
- Optimasi backend: current_user hanya 2 round-trip awaited (settings di-cache 30s + invalidasi saat PUT /settings; update last_seen fire-and-forget); aggregate() gather users+quizzes paralel, proyeksi tanpa questions/answers/essay_scores; dashboard gather aggregate+documents; Motor client compressors=zlib + pool settings; GZipMiddleware (dashboard 4.5KB→1.1KB).
- Diagnostik: `GET /api/health?db_check=true` → db_ping_ms, db_fetch_300_results_ms, db_host_suffix.

### 22 Sep 2026 — Catatan gambar, Regulasi, dan Hubungi (selesai & diuji)
- Semua label menu/dashboard/pencarian/repositori/form tambah/edit/review/hapus, kuis (termasuk formulir), hasil, monitoring, pesan API, dan notifikasi memakai Regulasi.
- Pengaturan Identitas & Gambar serta Koneksi Sistem dihapus, termasuk komponen SettingsPage lama yang kini re-export halaman utama. Layanan branding yang sudah ada tidak dihapus.
- Tambah pengaturan Hubungi: teks maksimal 120 karakter dan URL maksimal 2048; https/http/mailto/tel diterima, skema berbahaya/tautan relatif/format tidak valid ditolak. Teks kosong ditolak; URL kosong menampilkan teks biasa, bukan tautan palsu.
- Ikon bantuan login rata tengah vertikal dan grup bantuan di tengah; label panjang membungkus. Kontak web membuka tab baru dengan noopener/noreferrer.
- Footer login tinggal satu, paling bawah: copyright Bank BPD Bali, "Integritas. Kepatuhan. Kepercayaan.", MaiHarta. Footer panel dan OJK/BI/CMS lama dihapus. Kredit MaiHarta tetap tersedia di mobile.
- Segmen "CMS · Data contoh" di footer aplikasi dihapus; data contoh tidak dihapus. Caption "Bali Dwipa Jaya · 3D" dihapus; ilustrasi, mode 3D, rotasi, reset dipertahankan.
- Perbaikan layout CAPTCHA/login kecil, field pengaturan, wrapping kontak/footer. Lebar 320/768/1024/1440 diverifikasi tanpa overflow halaman.
- Verifikasi: `yarn build` sukses, Python compile sukses. Testing agent iteration_6: 10/10 tes backend lulus serial; UI kontak (https/mailto/tel/kosong), persist/reload/login, hak akses, Regulasi/kuis draft CRUD, tautan legacy, footer dan responsive lolos. Fixtures dibersihkan dan kontak dikembalikan ke URL kosong.
- Gap awal pembacaan piksel WebGL ditutup self-test: 14.400 piksel opaque dan 1.288 warna unik, checksum berubah saat drag/reset, caption tidak ada. Bukti di `/app/test_reports/iteration_6_followup.md`.
- Tidak ada API MOCKED baru. Kontak belum memiliki tujuan resmi karena pengguna belum memberikannya. Jumlah sampel tetap 8 regulasi dan 6 kuis. Kredensial tetap sesuai `test_credentials.md`.

## Backlog / Next
- P0: Tidak ada bug pemblokir pada perubahan sesi ini. Menunggu pengguna memeriksa hasil visual dan memasukkan tautan bantuan resmi di Pengaturan → Hubungi.
- P1: Verifikasi pengguna untuk login/kecepatan lingkungan produksi dari sesi sebelumnya masih belum tercatat; benchmark subdetik preview tidak membuktikan latency database produksi sudah selesai. Diagnostik tersedia di `/api/health?db_check=true` dan `/api/auth/status`.
- P1: Pin versi three/@react-three/fiber; `git rm --cached backend/.env frontend/.env`.
- P1 (dari KAK): AD/SSO, SIM SDM, mail/OTP, keamanan infrastruktur bank — memerlukan keputusan pemilik sistem.
- P2: Pisahkan stylesheet/page component panjang; fixture teardown pytest.
- P2: Pisahkan fixture akun tes rotasi password dari suite lain jika kelak tes dijalankan paralel; saat ini jalankan suite serial untuk menghindari invalidasi sesi saling silang.
- Saran pengembangan: tambahkan jam layanan SISDUR pada kontak bantuan bila diperlukan.
