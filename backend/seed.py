from datetime import datetime, timezone, timedelta
from core import db, now, uid

UNITS = ['Divisi Kepatuhan', 'Divisi Operasional', 'Divisi Teknologi Informasi', 'KC Denpasar', 'KC Singaraja', 'KC Gianyar']
NAMES = ['Ni Putu Ayu Pratiwi', 'I Made Surya Pratama', 'Ni Kadek Dwi Lestari', 'I Wayan Adi Putra', 'Ni Luh Putu Sari', 'I Ketut Artha Wijaya', 'Ni Komang Ratih', 'I Gede Bayu Saputra']
async def seed_data():
    if await db.settings.find_one({'id': 'main'}): return
    await db.settings.insert_one({'id': 'main', 'passing_grade': 75, 'idle_timeout': 180, 'quiz_duration': 30, 'organization': 'Bank BPD Bali'})
    leaders = [('demo-admin', 'I Made Aditya', 'administrator', 'Administrator I'), ('demo-supervisor', 'Ni Putu Maharani', 'supervisor', 'Kepala Bagian SISDUR'), ('demo-director', 'I Wayan Dharma', 'director', 'Direksi')]
    users = [{'id': i, 'name': n, 'role': r, 'position': p, 'unit': UNITS[0], 'nrk': f'BD{j+1000}', 'email': f'{r}@contoh.invalid', 'active': True, 'created_at': now()} for j, (i,n,r,p) in enumerate(leaders)]
    for k, unit in enumerate(UNITS):
        for j, name in enumerate(NAMES):
            i = 'demo-employee' if k == 0 and j == 0 else f'employee-{k}-{j}'
            users.append({'id': i, 'name': name if k == 0 else name + f' {chr(65+k)}', 'role': 'employee', 'unit': unit, 'position': 'Officer' if j < 5 else 'Kepala Unit', 'nrk': f'BD{2000+k*10+j}', 'email': f'pegawai.{k}.{j}@contoh.invalid', 'active': True, 'created_at': now()})
    await db.users.insert_many(users)
    doc_info = [('Pedoman Penerapan APU, PPT, dan PPPSPM', 'Internal', '012/SK/DIR/2026', 'Divisi Kepatuhan'), ('Pelindungan Konsumen dan Masyarakat', 'Eksternal', 'POJK Nomor 22 Tahun 2023', 'Divisi Kepatuhan'), ('Standar Operasional Layanan Nasabah', 'Internal', '008/SOP/OPS/2026', 'Divisi Operasional'), ('Penerapan Tata Kelola bagi Bank Umum', 'Eksternal', 'POJK Nomor 17 Tahun 2023', 'Divisi Kepatuhan'), ('Kebijakan Keamanan Informasi', 'Internal', '021/SK/TIF/2026', 'Divisi Teknologi Informasi'), ('Pedoman Strategi Anti Fraud', 'Internal', '016/SK/DIR/2026', 'Divisi Kepatuhan'), ('Pembaruan Prosedur Pembukaan Rekening', 'Internal', '032/SE/OPS/2026', 'Divisi Operasional'), ('Manajemen Risiko Teknologi Informasi', 'Eksternal', 'SEOJK Nomor 29/2026', 'Divisi Teknologi Informasi')]
    for j, (title, category, number, unit) in enumerate(doc_info):
        await db.documents.insert_one({'id': f'doc-{j}', 'title': title, 'category': category, 'number': number, 'unit': unit, 'description': 'Materi contoh untuk evaluasi pemahaman ketentuan. Dokumen ini bukan ketentuan resmi bank. Setiap pegawai wajib memahami prinsip kehati-hatian, pelindungan data nasabah, dan tata kelola yang baik.', 'status': 'published' if j < 6 else 'pending', 'version': '1.0' if j < 6 else '2.0', 'filename': None, 'created_by': 'demo-admin', 'created_at': (datetime.now(timezone.utc)-timedelta(days=j*5)).isoformat(), 'updated_at': now(), 'is_deleted': False, 'sample': True})
    titles = ['Pemahaman APU & PPT', 'Pelindungan Konsumen', 'Tata Kelola Perusahaan', 'Keamanan Informasi', 'Budaya Anti Fraud', 'Standar Layanan Nasabah']
    current = datetime.now(timezone.utc)
    for j, title in enumerate(titles):
        active = j in [0, 1]
        start = current - timedelta(days=12 if active else 35*(j-1))
        end = current + timedelta(days=9+j*3) if active else start + timedelta(days=20)
        questions = [
            {'id': 'q1', 'text': 'Apa tujuan utama penerapan ketentuan kepatuhan di bank?', 'type': 'multiple', 'options': ['Mempercepat transaksi tanpa pemeriksaan', 'Memastikan kegiatan bank sesuai peraturan yang berlaku', 'Mengurangi jumlah nasabah', 'Menghilangkan proses dokumentasi'], 'correct': 1},
            {'id': 'q2', 'text': 'Bagaimana tindakan yang tepat jika menemukan transaksi mencurigakan?', 'type': 'multiple', 'options': ['Mengabaikan transaksi tersebut', 'Memberitahu pihak yang dicurigai', 'Melaporkan melalui mekanisme internal yang berlaku', 'Menyebarkan informasi kepada publik'], 'correct': 2},
            {'id': 'q3', 'text': 'Siapa yang bertanggung jawab menjaga kerahasiaan data nasabah?', 'type': 'multiple', 'options': ['Hanya petugas keamanan', 'Hanya direksi', 'Hanya divisi teknologi informasi', 'Seluruh pegawai bank'], 'correct': 3},
            {'id': 'q4', 'text': 'Kapan pegawai perlu mempelajari pembaruan ketentuan?', 'type': 'multiple', 'options': ['Segera setelah ketentuan dipublikasikan', 'Hanya saat audit', 'Setelah terjadi pelanggaran', 'Tidak perlu jika sudah berpengalaman'], 'correct': 0}]
        quiz = {'id': f'quiz-{j}', 'title': title, 'description': 'Evaluasi pemahaman ketentuan dan penerapannya dalam pekerjaan sehari-hari.', 'document_id': f'doc-{j}', 'passing_grade': 75, 'duration': 30, 'units': [], 'positions': [], 'start_date': start.date().isoformat(), 'end_date': end.date().isoformat(), 'status': 'published', 'questions': questions, 'created_by': 'demo-admin', 'created_at': start.isoformat(), 'updated_at': now(), 'is_deleted': False}
        await db.quizzes.insert_one(quiz)
        employees = users[3:]
        for k, user in enumerate(employees):
            if user['id'] == 'demo-employee' or (k+j) % (6 if active else 10) == 0: continue
            score = [100,100,75,100,75,50,100,75,100,100][(k+j)%10]
            await db.results.insert_one({'id': uid(), 'quiz_id': quiz['id'], 'quiz_title': title, 'user_id': user['id'], 'user_name': user['name'], 'unit': user['unit'], 'position': user['position'], 'score': score, 'status': 'passed' if score >= 75 else 'failed', 'passing_grade': 75, 'answers': {'q1': 1, 'q2': 2, 'q3': 3, 'q4': 0}, 'submitted_at': (start+timedelta(days=5+k%6)).isoformat(), 'feedback': '', 'essay_scores': {}})
    await db.notifications.insert_one({'id': uid(), 'title': '2 ketentuan menunggu persetujuan', 'detail': 'Pembaruan ketentuan siap ditinjau oleh Supervisor SISDUR.', 'roles': ['administrator','supervisor'], 'user_ids': [], 'read_by': [], 'link': '/ketentuan?status=pending', 'created_at': now()})
    await db.notifications.insert_one({'id': uid(), 'title': 'Kuis pemahaman APU & PPT dibuka', 'detail': 'Selesaikan evaluasi pemahaman sebelum periode berakhir.', 'roles': ['employee'], 'user_ids': [], 'read_by': [], 'link': '/kuis', 'created_at': now()})
    await db.audit.insert_one({'id': uid(), 'user_id': 'demo-admin', 'user_name': 'I Made Aditya', 'action': 'INITIALIZE', 'module': 'Sistem', 'detail': 'Ruang demo CMS disiapkan dengan data contoh.', 'ip': 'system', 'timestamp': now()})