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
