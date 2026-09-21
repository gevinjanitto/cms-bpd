# Pemeriksaan dependensi runtime

Kode aplikasi tidak memuat Cloudflare Insights atau analytics lain. `frontend/public/index.html`, sumber React, konfigurasi CRACO, dan paket dependency tidak merujuk layanan tersebut. Penguji melihat `static.cloudflareinsights.com` pada domain preview; script itu bukan bagian dari source/build aplikasi dan tidak diperlukan oleh fungsi aplikasi.

Source dan build mandiri memakai aset logo, ilustrasi, dan font lokal; hanya API backend dari environment dan URL gambar Cloudinary yang telah dikonfigurasi yang dibutuhkan oleh aplikasi. Dependensi integrasi objek terdahulu diganti MongoDB GridFS, dan paket/plugin khusus telah dihapus.