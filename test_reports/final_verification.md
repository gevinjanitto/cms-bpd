# Verifikasi perbaikan — 2026-09-21

- Issue iteration_1: peringatan Recharts width(-1)/height(-1).
- Perbaikan: `ChartContainer.jsx` mengukur parent dengan ResizeObserver, kemudian memberikan width/height numerik ke grafik.
- Screenshot ulang: dua grafik berhasil dirender; navigasi Dashboard → Ketentuan → Dashboard lulus tanpa peringatan Recharts.
- Modal upload: bounding box x=570 y=40 w=780 h=720 pada viewport 1920×800, seluruh modal dalam viewport.
- Backend regression setelah optimasi query kuis: **6 passed** (5.52 detik), JUnit `pytest/final_results.xml`.
- Frontend production build: sukses, `final-build.log`.
- Auth sesi diperbaiki: heartbeat hanya saat aktivitas, idle timer dengan batas dari parameter.
- Verifikasi tambahan lulus: perubahan parameter langsung berlaku, logout setelah 60 detik idle, login ulang berhasil, pengaturan dipulihkan ke 180 detik dan dikonfirmasi setelah reload. Screenshot `idle-session-pass.jpg`.
- Seluruh koneksi AD/SSO, SIM SDM, email/OTP tetap belum dikonfigurasi dan tidak diklaim aktif.