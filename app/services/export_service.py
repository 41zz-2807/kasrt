from io import BytesIO

from openpyxl import Workbook

from app.services import finance_service


def export_rekap_excel(period: str) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Rekap"
    worksheet.append(["Periode", "Pemasukan", "Pengeluaran"])
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    worksheet.append([period, pemasukan, pengeluaran])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def export_rekap_pdf(period: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    buffer = BytesIO()
    chart = canvas.Canvas(buffer, pagesize=A4)
    chart.drawString(100, 750, f"Rekap KasRT - {period}")
    chart.drawString(100, 720, f"Pemasukan: {pemasukan}")
    chart.drawString(100, 700, f"Pengeluaran: {pengeluaran}")
    chart.save()
    return buffer.getvalue()
