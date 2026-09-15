import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_sample_pdfs():
    out_dir = os.path.join(os.getcwd(), "sample-documents")
    os.makedirs(out_dir, exist_ok=True)
    styles = getSampleStyleSheet()

    # 1. Valid Tax Invoice PDF
    invoice_path = os.path.join(out_dir, "invoice_valid_gst.pdf")
    doc = SimpleDocTemplate(invoice_path, pagesize=letter)
    story = []

    story.append(Paragraph("TAX INVOICE", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Invoice No:</b> INV-2026-9014", styles['Normal']))
    story.append(Paragraph("<b>Invoice Date:</b> 2026-09-15", styles['Normal']))
    story.append(Paragraph("<b>Vendor:</b> ABC Tech Solutions Pvt Ltd", styles['Normal']))
    story.append(Paragraph("<b>Vendor GSTIN:</b> 27AABCU9603R1ZN", styles['Normal']))
    story.append(Paragraph("<b>Buyer:</b> Acme India Corp", styles['Normal']))
    story.append(Paragraph("<b>Buyer GSTIN:</b> 27AABCA1234F1Z5", styles['Normal']))
    story.append(Spacer(1, 15))

    data = [
        ["Item Description", "Qty", "Unit Price (INR)", "Total (INR)"],
        ["Cloud Server Infrastructure Services", "2", "50,000.00", "100,000.00"],
    ]
    t = Table(data, colWidths=[240, 50, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Subtotal:</b> ₹100,000.00", styles['Normal']))
    story.append(Paragraph("<b>CGST (9%):</b> ₹9,000.00", styles['Normal']))
    story.append(Paragraph("<b>SGST (9%):</b> ₹9,000.00", styles['Normal']))
    story.append(Paragraph("<b>Total Amount:</b> ₹118,000.00", styles['Heading2']))

    doc.build(story)

    # 2. Invalid Tax Mismatch Invoice PDF (Forces Human Review Queue!)
    mismatch_path = os.path.join(out_dir, "invoice_tax_mismatch.pdf")
    doc2 = SimpleDocTemplate(mismatch_path, pagesize=letter)
    story2 = []
    story2.append(Paragraph("TAX INVOICE (FLAGGED)", styles['Title']))
    story2.append(Spacer(1, 12))
    story2.append(Paragraph("<b>Invoice No:</b> INV-2026-9099", styles['Normal']))
    story2.append(Paragraph("<b>Vendor GSTIN:</b> 27AABCU9603R1ZN", styles['Normal']))
    story2.append(Paragraph("<b>Subtotal:</b> ₹100,000.00", styles['Normal']))
    story2.append(Paragraph("<b>CGST (9%):</b> ₹9,000.00", styles['Normal']))
    story2.append(Paragraph("<b>SGST (9%):</b> ₹9,000.00", styles['Normal']))
    story2.append(Paragraph("<b>Total Amount:</b> ₹150,000.00 (Mismatched!)", styles['Heading2']))
    doc2.build(story2)

    print(f"Successfully generated demo PDFs in: {out_dir}")

if __name__ == "__main__":
    generate_sample_pdfs()
