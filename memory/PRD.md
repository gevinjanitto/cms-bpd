# PRD — CMS Kepatuhan Bank BPD Bali (cms-bpd)

## Problem Statement
Aplikasi asal: Compliance Management System Bank BPD Bali (ketentuan, kuis, monitoring, audit; React 19 + FastAPI + MongoDB; UI Bahasa Indonesia nuansa hijau).
Permintaan sesi ini (repo https://github.com/gevinjanitto/cms-bpd):
1. Login gagal "Username atau password tidak sesuai" padahal BOOTSTRAP_PASSWORD (bpdjaya3x) sudah benar → perbaiki.
2. Tambahkan "Design & Develop by MaiHarta" (link https://www.maiharta.com, tab baru) di semua footer copyright tanpa menghapus copyright lama.
3. Deploy: frontend di Vercel (https://cms-bpd.vercel.app), backend di Railway (https://cms-bpd-production.up.railway.app), DB MongoDB Atlas.

## Arsitektur
- Backend FastAPI (port 8001, prefix /api): core, routes, quiz_routes, reports, storage/media, seed, auth. Auth kustom: username + bcrypt + CAPTCHA gambar sekali pakai, token opaque 12 jam, lockout 5 menit setelah 3x gagal, rate limit per IP.
- Frontend React (craco): Login, Dashboard, Ketentuan, Kuis, Monitoring, Pengguna, Audit, Pengaturan. Komponen React wajib di file .jsx (JSX di .js membuat build produksi gagal).
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

## Backlog / Next
- P0: User "Save to Github" → Railway redeploy backend → buka /api/health?db_check=true; jika db_ping_ms > 100 → pindahkan cluster MongoDB ke region yang sama dengan service Railway (atau pakai private network jika Mongo di Railway).
- P0 (selesai jika login production sudah OK): cek /api/auth/status.
- P1: Pin versi three/@react-three/fiber; `git rm --cached backend/.env frontend/.env`.
- P1 (dari KAK): AD/SSO, SIM SDM, mail/OTP, keamanan infrastruktur bank — memerlukan keputusan pemilik sistem.
- P2: Pisahkan stylesheet/page component panjang; fixture teardown pytest.
