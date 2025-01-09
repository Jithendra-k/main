# restaurant_admin/utils.py
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime


def generate_order_stats_pdf(request, orders, stats, start_date, end_date):
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_stats_{start_date}_{end_date}.pdf"'

    # Create the PDF object using ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

    # Container for elements to be added to the PDF
    elements = []

    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # Add Title
    elements.append(Paragraph(f"Royal Nepal Restaurant - Order Statistics", title_style))
    elements.append(Spacer(1, 12))

    # Add Date Range
    elements.append(Paragraph(f"Period: {start_date} to {end_date}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Add Financial Summary
    elements.append(Paragraph("Financial Summary", subtitle_style))
    elements.append(Spacer(1, 6))

    financial_data = [
        ["Gross Sales", f"${stats['gross_sales']:.2f}"],
        ["Total Taxes Collected", f"${stats['total_taxes']:.2f}"],
        ["Total Tips", f"${stats['total_tips']:.2f}"],
        ["Net Sales", f"${stats['net_sales']:.2f}"],
    ]

    financial_table = Table(financial_data, colWidths=[3 * inch, 2 * inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 20))

    # Add Order Statistics
    elements.append(Paragraph("Order Statistics", subtitle_style))
    elements.append(Spacer(1, 6))

    summary_data = [
        ["Total Orders", str(stats['order_count'])],
        ["Average Order Value", f"${stats['avg_order_value']:.2f}"],
        ["Orders Completed", str(stats['completed_orders'])],
        ["Orders In Progress", str(stats['in_progress_orders'])],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Add Orders Table
    elements.append(Paragraph("Detailed Orders", subtitle_style))
    elements.append(Spacer(1, 6))

    # Create orders table data
    orders_data = [['Order ID', 'Date', 'Customer', 'Total', 'Status']]
    for order in orders:
        orders_data.append([
            str(order.id),
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.name,
            f"${order.total_amount}",
            order.get_status_display()
        ])

    orders_table = Table(orders_data, colWidths=[1 * inch, 1.5 * inch, 2 * inch, 1 * inch, 1.5 * inch])
    orders_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(orders_table)

    # Add Sales Chart if available
    if hasattr(request, 'session') and 'chart_data' in request.session:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Sales Trend", subtitle_style))
        elements.append(Spacer(1, 6))

        chart_data = json.loads(request.session['chart_data'])
        # Add chart data in tabular format
        chart_table_data = [['Date', 'Orders']]
        for date, count in zip(chart_data['dates'], chart_data['counts']):
            chart_table_data.append([date, str(count)])

        chart_table = Table(chart_table_data, colWidths=[3 * inch, 2 * inch])
        chart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(chart_table)

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response



def generate_transaction_pdf(transactions, stats, start_date, end_date):
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions_{start_date}_{end_date}.pdf"'

    # Create the PDF object using ReportLab
    buffer = BytesIO()
    # Use landscape orientation for better table layout
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=36, leftMargin=36, topMargin=36,
                            bottomMargin=36)

    # Container for elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    # Add Title
    elements.append(Paragraph(f"Royal Nepal Restaurant - Transaction Report", title_style))
    elements.append(Spacer(1, 12))

    # Add Date Range
    elements.append(Paragraph(f"Period: {start_date} to {end_date}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Add Financial Summary
    elements.append(Paragraph("Financial Summary", subtitle_style))
    elements.append(Spacer(1, 6))

    summary_data = [
        ["Total Transactions", f"{stats['total_transactions']}"],
        ["Total Amount", f"${stats['total_amount']:.2f}"],
        ["Total Refunds", f"${stats['total_refunded']:.2f}"],
        ["Net Amount", f"${(stats['total_amount'] - stats['total_refunded']):.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Add Payment Method Breakdown
    if 'payment_methods' in stats:
        elements.append(Paragraph("Payment Method Breakdown", subtitle_style))
        elements.append(Spacer(1, 6))

        payment_data = [["Payment Method", "Count", "Total Amount"]]
        for method, data in stats['payment_methods'].items():
            payment_data.append([
                method,
                str(data['count']),
                f"${data['amount']:.2f}"
            ])

        payment_table = Table(payment_data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))

    # Add Transaction Details
    elements.append(Paragraph("Transaction Details", subtitle_style))
    elements.append(Spacer(1, 6))

    # Create transactions table
    trans_data = [['Date', 'ID', 'Customer', 'Type', 'Amount', 'Status', 'Payment Method', 'Reference']]
    for trans in transactions:
        trans_data.append([
            trans.created_at.strftime('%Y-%m-%d %H:%M'),
            str(trans.id),
            trans.user.get_full_name() if trans.user else 'Guest',
            trans.get_transaction_type_display(),
            f"${trans.amount}",
            trans.get_status_display(),
            trans.get_payment_method_display(),
            trans.reference_id or '-'
        ])

    # Use proportional column widths for landscape orientation
    trans_table = Table(trans_data,
                        colWidths=[1.2 * inch, 0.8 * inch, 1.5 * inch, 1.2 * inch, 1 * inch, 1 * inch, 1.2 * inch,
                                   1.1 * inch])
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(trans_table)

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response