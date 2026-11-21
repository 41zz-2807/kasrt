"""Isi seluruh fitur dengan data dummy untuk demo client. Aman dijalankan ulang."""

from datetime import date, datetime

from app import create_app, db
from app.models import (
    AuditLog,
    Category,
    DuesRate,
    DuesType,
    House,
    Invoice,
    NotificationOutbox,
    PaymentAllocation,
    PeriodLock,
    Setting,
    Transaction,
    User,
)
from scripts.clear_dummy import MARKER_KEY, clear_dummy_data

PASSWORD = "Demo12345!"


def _period(base, offset):
    index = base.year * 12 + base.month - 1 + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _tanggal(period, day):
    return datetime(int(period[:4]), int(period[5:7]), day)


def seed_dummy_data():
    clear_dummy_data()
    periods = [_period(datetime.now(), offset) for offset in range(-5, 1)]

    users = {}
    for username, role, active in [
        ("demo_admin", "superuser", True),
        ("demo_ketua", "ketua_rt", True),
        ("demo_bendahara", "bendahara", True),
        ("demo_warga", "warga", True),
        ("demo_nonaktif", "warga", False),
    ]:
        user = User(
            username=username,
            email=f"{username}@demo.local",
            role=role,
            is_active=active,
            must_change_password=False,
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.flush()
        users[username] = user
    admin_id = users["demo_admin"].id

    names = [
        "Budi Santoso", "Siti Rahayu", "Ahmad Fauzi", "Dewi Anggraini", "Rizky Pratama",
        "Nur Haliza", "Agus Setiawan", "Maya Sari", "Joko Widodo", "Fitri Handayani",
        "Andi Saputra", "Lina Marlina",
    ]
    houses = []
    for i, name in enumerate(names, start=1):
        house = House(
            blok="DM",
            nomor=f"{i:02d}",
            nama_penghuni=f"{name} (Demo)",
            is_active=True,
            start_period=date.fromisoformat(f"{periods[0]}-01"),
        )
        db.session.add(house)
        db.session.flush()
        houses.append(house)

    dues_type = DuesType(nama="Iuran Bulanan (Demo)", is_active=True)
    db.session.add(dues_type)
    db.session.flush()
    db.session.add(DuesType(nama="Iuran Kebersihan (Demo)", is_active=False))
    db.session.flush()

    for period, nominal in [(periods[0], 50000), (periods[-2], 60000)]:
        db.session.add(
            DuesRate(
                dues_type_id=dues_type.id,
                nominal=nominal,
                effective_period=period,
                created_by=admin_id,
            )
        )
    db.session.flush()

    categories = {}
    for key, nama, jenis, is_system, is_active in [
        ("listrik", "[DEMO] Listrik & Air", "keluar", False, True),
        ("atk", "[DEMO] ATK & Kebersihan", "keluar", False, True),
        ("perbaikan", "[DEMO] Perbaikan Fasilitas", "keluar", False, True),
        ("sumbangan", "[DEMO] Sumbangan Warga", "masuk", True, True),
        ("denda", "[DEMO] Denda Keterlambatan", "masuk", False, True),
        ("nonaktif", "[DEMO] Kategori Nonaktif", "keluar", False, False),
    ]:
        category = Category(nama=nama, jenis=jenis, is_system=is_system, is_active=is_active)
        db.session.add(category)
        db.session.flush()
        categories[key] = category

    for house in houses:
        for index, period in enumerate(periods):
            nominal = 60000 if period >= periods[-2] else 50000
            if index < 4:
                paid = nominal
            elif index == 4:
                paid = nominal // 2 if int(house.nomor) % 2 == 0 else nominal
            else:
                paid = nominal // 2 if int(house.nomor) % 3 == 1 else 0
            status = "belum" if paid == 0 else ("lunas" if paid == nominal else "sebagian")
            invoice = Invoice(
                house_id=house.id,
                dues_type_id=dues_type.id,
                period=period,
                nominal=nominal,
                paid_amount=paid,
                status=status,
            )
            db.session.add(invoice)
            db.session.flush()
            if paid:
                trx = Transaction(
                    trx_no=f"DEMO-{period.replace('-', '')}-{house.nomor}-I",
                    tanggal=_tanggal(period, 5),
                    jenis="iuran",
                    category_id=None,
                    house_id=house.id,
                    jumlah=paid,
                    keterangan=f"[DEMO] Iuran {period} - {house.nama_penghuni}",
                    status="aktif",
                    receipt_no=f"DEMO-KW-{period.replace('-', '')}-{house.nomor}",
                    created_by=admin_id,
                )
                db.session.add(trx)
                db.session.flush()
                db.session.add(
                    PaymentAllocation(transaction_id=trx.id, invoice_id=invoice.id, amount=paid)
                )

    for period in periods:
        for j, (key, amount, keterangan, day) in enumerate(
            [
                ("listrik", 150000, "Bayar listrik dan air", 10),
                ("atk", 95000, "Beli ATK dan alat kebersihan", 17),
                ("perbaikan", 120000, "Perbaikan fasilitas RT", 24),
            ],
            start=1,
        ):
            db.session.add(
                Transaction(
                    trx_no=f"DEMO-{period.replace('-', '')}-K{j}",
                    tanggal=_tanggal(period, day),
                    jenis="pengeluaran",
                    category_id=categories[key].id,
                    house_id=None,
                    jumlah=amount,
                    keterangan=f"[DEMO] {keterangan} {period}",
                    status="aktif",
                    created_by=admin_id,
                )
            )

    db.session.add(
        Transaction(
            trx_no=f"DEMO-{periods[-1].replace('-', '')}-S1",
            tanggal=_tanggal(periods[-1], 26),
            jenis="non_rutin",
            category_id=categories["sumbangan"].id,
            house_id=houses[0].id,
            jumlah=250000,
            keterangan="[DEMO] Sumbangan warga untuk acara RT",
            status="aktif",
            receipt_no=f"DEMO-KW-{periods[-1].replace('-', '')}-S1",
            created_by=admin_id,
        )
    )
    db.session.add(
        Transaction(
            trx_no=f"DEMO-{periods[1].replace('-', '')}-V1",
            tanggal=_tanggal(periods[1], 21),
            jenis="pengeluaran",
            category_id=categories["perbaikan"].id,
            house_id=None,
            jumlah=75000,
            keterangan="[DEMO] Perbaikan lampu (contoh dibatalkan)",
            status="void",
            void_reason="[DEMO] Contoh transaksi dibatalkan",
            voided_by=admin_id,
            voided_at=_tanggal(periods[1], 22),
            created_by=admin_id,
        )
    )
    db.session.flush()

    db.session.add(
        PeriodLock(
            period=periods[0],
            locked_by=admin_id,
            locked_at=_tanggal(periods[0], 28),
        )
    )
    for i, (status, subject) in enumerate(
        [("sent", "Pengingat iuran"), ("sent", "Pembayaran diterima"), ("failed", "Notifikasi gagal")]
    ):
        db.session.add(
            NotificationOutbox(
                to_email=f"warga{i + 1}@demo.local",
                subject=f"[DEMO] {subject}",
                body=f"[DEMO] Contoh notifikasi untuk periode {periods[-1]}.",
                status=status,
                attempts=0 if status == "sent" else 5,
                last_error="SMTP tidak tersedia" if status == "failed" else None,
            )
        )
    for action, entity, period in [
        ("create", "transaction", periods[-1]),
        ("update", "house", periods[-2]),
        ("void", "transaction", periods[1]),
    ]:
        db.session.add(
            AuditLog(
                user_id=admin_id,
                action=action,
                entity=entity,
                entity_id=1,
                after_json='[DEMO]',
                ip="127.0.0.1",
                created_at=_tanggal(period, 12),
            )
        )

    setting_ids = []
    for key, value in {
        "nama_rt": "RT 01 / RW 02 (Demo)",
        "saldo_awal_kas": "1500000",
        "email_ketua_rt": "ketua@demo.local",
        "email_bendahara": "bendahara@demo.local",
        "tampilkan_nama_penghuni": "1",
    }.items():
        row = Setting(key=key, value=value)
        db.session.add(row)
        db.session.flush()
        setting_ids.append(row.id)
    db.session.add(Setting(key=MARKER_KEY, value=",".join(str(i) for i in setting_ids)))

    db.session.commit()
    return {
        "users": len(users),
        "houses": len(houses),
        "periods": len(periods),
        "dues_types": 2,
        "categories": len(categories),
    }


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        result = seed_dummy_data()
    print(
        "Seed dummy selesai: "
        f"{result['users']} pengguna, {result['houses']} rumah, "
        f"{result['periods']} periode, {result['dues_types']} jenis iuran, "
        f"{result['categories']} kategori."
    )
    print(f"Login demo: demo_admin / {PASSWORD}")
