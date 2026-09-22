"""Rename only unchanged, system-seeded sample copy; preserve user content and audit history."""
import asyncio

from core import db


async def migrate_sample_regulation_terms():
    old_description = 'Materi contoh untuk evaluasi pemahaman ketentuan. Dokumen ini bukan ketentuan resmi bank. Setiap pegawai wajib memahami prinsip kehati-hatian, pelindungan data nasabah, dan tata kelola yang baik.'
    old_quiz_description = 'Evaluasi pemahaman ketentuan dan penerapannya dalam pekerjaan sehari-hari.'
    quiz_filter = {'id': {'$in': [f'quiz-{i}' for i in range(6)]}, 'created_by': 'demo-admin'}
    await asyncio.gather(
        db.documents.update_many(
            {'id': {'$in': [f'doc-{i}' for i in range(8)]}, 'sample': True, 'description': old_description},
            {'$set': {'description': old_description.replace('ketentuan', 'regulasi')}},
        ),
        db.quizzes.update_many(
            {**quiz_filter, 'description': old_quiz_description},
            {'$set': {'description': old_quiz_description.replace('ketentuan', 'regulasi')}},
        ),
        db.quizzes.update_many(
            quiz_filter,
            {'$set': {'questions.$[question].text': 'Apa tujuan utama penerapan regulasi kepatuhan di bank?'}},
            array_filters=[{'question.id': 'q1', 'question.text': 'Apa tujuan utama penerapan ketentuan kepatuhan di bank?'}],
        ),
        db.quizzes.update_many(
            quiz_filter,
            {'$set': {'questions.$[question].text': 'Kapan pegawai perlu mempelajari pembaruan regulasi?'}},
            array_filters=[{'question.id': 'q4', 'question.text': 'Kapan pegawai perlu mempelajari pembaruan ketentuan?'}],
        ),
        db.quizzes.update_many(
            quiz_filter,
            {'$set': {'questions.$[question].options.$[option]': 'Segera setelah regulasi dipublikasikan'}},
            array_filters=[{'question.id': 'q4'}, {'option': 'Segera setelah ketentuan dipublikasikan'}],
        ),
    )