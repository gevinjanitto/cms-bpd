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

## Backlog / Next
- P0: User "Save to Github" → Railway redeploy backend → buka https://cms-bpd-production.up.railway.app/api/auth/status; pastikan code_version = auth-2026.06-v3, bootstrap_password_length = 9, accounts_synced semua true. Jika panjang ≠ 9, perbaiki Variables BOOTSTRAP_PASSWORD di Railway.
- P1: Pin versi three/@react-three/fiber; `git rm --cached backend/.env frontend/.env`.
- P1 (dari KAK): AD/SSO, SIM SDM, mail/OTP, keamanan infrastruktur bank — memerlukan keputusan pemilik sistem.
- P2: Pisahkan stylesheet/page component panjang; fixture teardown pytest.
