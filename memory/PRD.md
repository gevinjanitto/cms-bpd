<<<<<<< HEAD
# PRD — CMS Bank BPD Bali (cms-bpd)

## Problem Statement (21 Sep 2026)
User memiliki kode di https://github.com/gevinjanitto/cms-bpd. Login gagal ("Username atau password tidak sesuai") padahal BOOTSTRAP_PASSWORD di backend sudah benar (bpdjaya3x). Diminta: perbaiki login + tambahkan "Design & Develop by MaiHarta" (link ke www.maiharta.com, tab baru) di semua footer copyright, tanpa menghapus copyright lama.

## Arsitektur
- Backend: FastAPI + motor (MongoDB), port 8001, prefix /api. Auth kustom: username + bcrypt password + CAPTCHA gambar sekali pakai, sesi token 12 jam, lockout 5 menit setelah 3x gagal.
- Frontend: React (craco), port 3000. Halaman: Login, Dashboard, Ketentuan, Kuis, Monitoring, Pengguna, Audit, Pengaturan.
- Kredensial: admin/supervisor/karyawan/direksi, password dari env BOOTSTRAP_PASSWORD (bpdjaya3x). Lihat /app/memory/test_credentials.md.

## Yang Sudah Diimplementasikan
### 21 Sep 2026
- FIX LOGIN: `initialize_auth` di backend/auth.py kini menyinkronkan hash password dengan BOOTSTRAP_PASSWORD setiap startup (re-hash jika tidak cocok + reset lockout). Root cause: hash lama di DB tidak pernah diperbarui saat env berubah.
- Footer credit "Design & Develop by MaiHarta" (link https://www.maiharta.com, target _blank) via komponen `DeveloperCredit` di src/lib/branding.js, dipasang di 3 footer: login-panel-footer, login-page-footer (Login.jsx), page-footer (Layout.jsx). Styling di App.css.
- Instal dependensi three & @react-three/fiber (error kompilasi bawaan repo) dan koreksi REACT_APP_BACKEND_URL.
- Testing agent iteration_4: 100% pass (backend + frontend).

## Backlog / Next
- P0: User push perubahan ke GitHub (fitur "Save to Github") lalu redeploy Railway — hash password production otomatis tersinkron ke bpdjaya3x saat startup.
- P1: Pin versi @react-three/fiber/three agar environment baru tidak gagal kompilasi.
- P2: —
=======
# CMS Kepatuhan Bank BPD Bali

## Permintaan asli
“berdasarkan dokumen doc tersebut, pelajarilah dan buatkan aplikasinya. pakai image.png sebagai logo dan buat nuansa hijau”

Pengguna: “Start the task now”. Konfirmasi prioritas: “Ya, langsung buat alur utama yang lengkap sesuai dokumen”.

Sumber: Lampiran Surat (KAK).docx, berhasil diekstrak. Dokumen menyebut pengembangan Compliance Management System Bank BPD Bali untuk ketentuan, kuis, monitoring kepatuhan, audit, dan integrasi sistem internal bank.

Logo yang digunakan sesuai aset pengguna: Bali Dwipa Jaya. UI Bahasa Indonesia, nuansa hijau, aksen emas dan biru, mode terang/gelap, responsif.

## Persona
1. Administrator I / SISDUR: mengelola ketentuan, kuis, peserta, parameter, audit, pengguna, monitoring.
2. Supervisor SISDUR: review/approve/reject ketentuan dan kuis; penilaian esai.
3. Karyawan: membaca/mengunduh ketentuan terpublikasi, mengerjakan kuis yang ditargetkan, melihat nilai dan memberikan feedback.
4. Direksi: dashboard, monitoring dan laporan; tidak dapat mengubah materi atau membaca kunci jawaban.

## Persyaratan inti (statis)
- Siklus ketentuan internal/eksternal: draf, upload, review, persetujuan/penolakan, publikasi, unduh.
- Kuis terkait ketentuan dengan pilihan ganda/esai, passing grade, durasi, periode dan penargetan unit/jabatan.
- Satu kali pengerjaan per peserta, penilaian otomatis pilihan ganda, esai dinilai supervisor, feedback peserta.
- Monitoring partisipasi dan kelulusan, agregat unit kerja, top/bottom/never participated, historis periode, ekspor.
- Hak akses per peran, masking identitas pada daftar, audit aktivitas, parameter aplikasi.
- Integrasi KAK menyebut AD SSO, SIM SDM, mail server bank/OTP; membutuhkan konektivitas dan konfigurasi bank.
- KAK juga menyebut persyaratan institusional keamanan dan infrastruktur (WAF, MFA, SIEM, SSDLC, encrypted-at-rest, immutable audit, backup/DR, concurrent users dan SLA); tidak boleh diklaim dipenuhi oleh versi awal ini.

## Keputusan arsitektur
- React 19, React Router, Shadcn Dialog/Button, Sonner, Lucide, Recharts.
- Backend FastAPI dengan module core/routes/quiz_routes/reports/storage/seed; MongoDB via Motor.
- Stack mengikuti lingkungan yang tersedia. Berbeda dari rekomendasi database relasional di KAK; migrasi/konfirmasi arsitektur perbankan tetap perlu pada tahap integrasi.
- Semua API menggunakan `/api`, frontend memakai REACT_APP_BACKEND_URL, database hanya MONGO_URL. Variabel awal tidak diubah.
- Collections: users, sessions, documents, quizzes, attempts, results, settings, notifications, audit.
- ID string UUID, projection mengecualikan BSON `_id`, response-model Record untuk respons dokumen tunggal/daftar; waktu ISO UTC.
- Penyimpanan berkas nyata melalui managed object storage; canonical storage_path di database; unduh diproksi backend dengan verifikasi peran/status.
- Terima PDF/DOCX, maksimum 10 MB, pemeriksaan ekstensi dan signature sederhana; pemindaian malware belum tersedia.
- Demo persona login digated `DEMO_MODE=true`; opaque bearer token, hash token dalam database, revocation/logout, idle 180 detik dapat dikonfigurasi. Bukan AD/SSO dan bukan autentikasi produksi.
- Interface jelas bertanda “Lingkungan demo · Data contoh”. Default membuka dashboard administrator; pemilih peran mengizinkan mencoba empat alur.
- Data bawaan 48 karyawan + 3 peran pengelola, 8 ketentuan, 6 kuis dan 248 hasil contoh. Tidak ada data nyata bank. Berkas ketentuan contoh berupa teks yang ditandai bukan ketentuan resmi; unggahan pengguna disimpan dan diunduh utuh.
- Notifikasi aplikasi nyata; tidak mengirim email atau OTP. Halaman pengaturan menandai koneksi bank belum dikonfigurasi.
- Audit append-only melalui aplikasi, tetapi bukan penyimpanan immutable/WORM pada tingkat infrastruktur.

## Implementasi — 2026-09-21
- Dashboard agregat dan personal: total ketentuan, kuis aktif, partisipasi, kelulusan, tren, donut, performa unit, tugas review.
- Filter tahun/triwulan/semester/unit dan CSV sesuai filter; data dihitung dari records bukan angka statis di UI.
- Ketentuan: pencarian, kategori/status, CRUD draf, upload PDF/DOCX, review/approve/reject, unduh terotorisasi, metadata detail.
- Kuis: authoring soal pilihan ganda/esai, kunci jawaban, target satu unit/jabatan atau semuanya, tanggal, durasi, passing grade, CRUD draf, approval supervisor.
- Pengerjaan karyawan: waktu mulai server, countdown, navigasi soal, radio/textarea, validasi lengkap, konfirmasi kirim, nilai/feedback tersimpan, unique index satu hasil per kuis/peserta. Kunci tidak diekspos kepada karyawan.
- Supervisor menilai setiap esai 0–100; total nilai diperbarui, notifikasi peserta.
- Monitoring: hasil per karyawan, unit, daftar belum mengikuti, top/bottom/never 10; pengingat dalam aplikasi; penilaian esai.
- Pengguna: tambah, masking email/NRK, reveal berizin dengan audit, blokir/buka blokir. Satu administrator bawaan; form tidak mengizinkan membuat administrator tambahan.
- Audit read-only pencarian/filter; notifikasi read/unread; parameter passing grade/durasi/idle.
- Responsive navigation, mobile tables scrolling within wrappers, theme, toast feedback, empty states, unique data-testid controls.
- Optimasi N+1 daftar kuis: prefetch karyawan sekali, aggregate completion counts, prefetch hasil personal.
- Grafik memakai ResizeObserver ChartContainer, dirender hanya setelah ukuran positif; peringatan dimensi Recharts diatasi.
- Activity heartbeat menjaga sesi ketika pengguna aktif mengisi formulir/kuis; auto logout saat benar-benar idle.
- Perubahan idle timeout langsung diterapkan melalui event pengaturan; logout idempotent mencabut token tanpa perlu sesi yang masih aktif. Judul tab browser menggunakan identitas CMS.

## Verifikasi — 2026-09-21
- Testing agent report `/app/test_reports/iteration_1.json`: alur backend/frontend utama lulus, satu masalah dimensi grafik.
- Enam tes pytest mencakup auth, dashboard/CSV, RBAC, upload invalid/oversize/valid + approval/download, kuis MCQ/esai + grading.
- Setelah perbaikan: enam tes kembali lulus, JUnit `/app/test_reports/pytest/final_results.xml`.
- Build produksi sukses, log `/app/test_reports/final-build.log`.
- Browser memverifikasi 2 grafik, perpindahan halaman, modal sepenuhnya dalam viewport; console tidak lagi berisi warning Recharts.
- Mobile 390px diuji agent: menu hamburger dan overflow lulus.
- Pengujian browser tambahan: ubah idle menjadi 60 detik, tunggu tanpa aktivitas, auto logout lulus; masuk kembali lulus; parameter 180 detik dipulihkan dan persistensi diverifikasi setelah reload.
- Record TEST_* dari pengujian disembunyikan (soft delete dokumen/kuis); hasil uji dilepas. Audit tidak dihapus. Parameter kembali 75 / 30 menit / 180 detik.

## Backlog prioritas dan langkah berikut
### P0 — prasyarat penggunaan nyata di bank
- Konfirmasi arsitektur yang diterima bank dan penyelarasan ulang lengkap dengan KAK.
- AD/SSO dan sinkronisasi SIM SDM; autentikasi nyata, disable persona login demo.
- Mail server bank, OTP/MFA, email approval/rejection/new regulation/reminder.
- Kontrol perangkat/IP, penguncian setelah kesalahan password, blokir akun idle 30 hari.
- Infrastruktur keamanan: TLS sesuai standar bank, WAF, SIEM, EDR, encrypted-at-rest, secrets management, logging immutable/WORM, backup/DR.
- Security assessment, threat model, review privasi, SIT/UAT formal dan load testing 1000 concurrent users; tidak ada klaim SLA saat ini.

### P1 — perluasan fungsional
- Roles Administrator II TIF dan Supervisi II SDM, matriks hak akses granular sesuai persetujuan bank.
- Version history ketentuan lengkap, perubahan status arsip/kedaluwarsa, viewer PDF dalam aplikasi.
- Pilihan multi-unit/jabatan di UI (schema backend sudah list), unit kerja dinamis dari SIM SDM.
- Pagination server untuk skala data besar, query indexes lanjutan, caching agregat.
- Filter rentang tanggal penuh/histori, ekspor PDF/XLSX, adjustment hasil terkontrol.
- Pengingat otomatis mendekati tenggat, bukan hanya pengiriman manual.
- Autosave jawaban server dan prosedur toleransi timeout/resume; saat ini draft jawaban lokal tab browser dan waktu mulai server.
- Dynamic year choices (UI saat ini fokus 2026), denominator historis peserta sesuai snapshot saat penugasan.

### P2 — peningkatan pengalaman dan maintainability
- Sertifikat evaluasi, ringkasan rekomendasi pembelajaran berbasis hasil.
- Pengaturan preferensi pribadi, panduan operasional lengkap.
- Pisahkan dan format stylesheet serta beberapa page components yang masih panjang.
- Tambah fixture teardown otomatis pada pytest agar record uji tidak perlu dibersihkan terpisah.

## Catatan kelanjutan
<<<<<<< HEAD
Gunakan pengujian yang sudah ada. Jangan mengklaim demo authentication sebagai SSO atau notifikasi aplikasi sebagai email. Jangan hapus audit ketika membersihkan data uji. Integrasi bank memerlukan keputusan dan konfigurasi dari pemilik sistem.
## Perbaikan deploy Railway (Juni 2026)
- Root cause: service Railway dibangun dari root repo (tanpa Root Directory); root berisi `yarn.lock` kosong + file log sehingga Railpack gagal mendeteksi aplikasi.
- Dilakukan: hapus root `yarn.lock`/`three-*.log`; tambah `frontend/Dockerfile` (node:20 build + `serve` SPA, ARG REACT_APP_BACKEND_URL), `frontend/railway.json`, `.dockerignore` (root/frontend), root `Dockerfile`+`railway.json` sebagai fallback backend; `.gitignore` sekarang mengabaikan `.env`; SETUP.md berisi langkah Railway dua service + Atlas.
- Diverifikasi testing agent (iteration_3): health, captcha, login-reject, halaman login, `yarn build` produksi.
- Backlog: `git rm --cached backend/.env frontend/.env` di repo user agar rahasia tidak tersimpan; verifikasi deploy nyata di Railway; Atlas IP allowlist.
=======
Gunakan pengujian yang sudah ada. Jangan mengklaim demo authentication sebagai SSO atau notifikasi aplikasi sebagai email. Jangan hapus audit ketika membersihkan data uji. Integrasi bank memerlukan keputusan dan konfigurasi dari pemilik sistem.
>>>>>>> 28f218d13e8bf8ef8c54d93ba94fdf682e6494d0
>>>>>>> 91ae9f0a5bad37493205b97706d3dde110afcab8
