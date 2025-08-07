from flask import make_response
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from io import BytesIO
import os
import logging

# Get logger from the main application
logger = logging.getLogger(__name__)


def generate_mls_pdf(mls_data):
    """Generate a PDF report for an MLS point based on the template"""

    # Create a buffer for the PDF
    buffer = BytesIO()

    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.white,
        backColor=colors.blue,
        alignment=1,
        spaceAfter=10,
        spaceBefore=10,
        borderPadding=5
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.white,
        backColor=colors.blue,
        alignment=0,
        spaceAfter=6,
        borderPadding=3
    )

    # Store elements for the PDF
    elements = []

    # Page 1: MLS AT A GLANCE
    elements.append(Paragraph("MLS AT A GLANCE", title_style))

    # MLS Point Details Section - Remove the icon that caused the error
    elements.append(Paragraph("MLS Point Details", section_style))

    # Basic information table
    cell_style = ParagraphStyle(
        name='CellStyle',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        spaceAfter=4
    )

    # Table data with wrapped content
    basic_data = [
        ["MLS Point Code", Paragraph(str(mls_data.get("mls_point_code", "")), cell_style)],
        ["MLS Point Name", Paragraph(str(mls_data.get("mls_point_name", "")), cell_style)],
        ["District Name", Paragraph(str(mls_data.get("district_name", "")), cell_style)],
        ["Mandal Name", Paragraph(str(mls_data.get("mandal_name", "")), cell_style)],
        ["MLS Point Address", Paragraph(str(mls_data.get("mls_point_address", "")), cell_style)],
        ["Latitude", Paragraph(str(mls_data.get("mls_point_latitude", "")), cell_style)],
        ["Longitude", Paragraph(str(mls_data.get("mls_point_longitude", "")), cell_style)],
        ["Fetch Live Location", Paragraph("", cell_style)],
        ["Mandals Tagged to MLS Point", Paragraph("", cell_style)]
    ]

    # Create the table
    basic_table = Table(basic_data, colWidths=[150, 330])
    basic_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))

    elements.append(basic_table)
    elements.append(Spacer(2, 0.2 * inch))

    # Incharge Details Section - without icon
    elements.append(Paragraph("Incharge Details", section_style))

    # Create a table for incharge details with photo space
    incharge_data = [
        ["CFMS / Corporation EMP ID", mls_data.get("mls_point_incharge_cfms_id", ""), ""],
        ["Name", mls_data.get("mls_point_incharge_name", ""), "MLS"],
        ["Designation", mls_data.get("designation", ""), "Incharge"],
        ["Aadhaar Number", mls_data.get("aadhaar_number", ""), "Photo"],
        ["Phone Number", mls_data.get("phone_number", ""), ""]
    ]

    incharge_table = Table(incharge_data, colWidths=[150, 260, 70])
    incharge_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('SPAN', (2, 0), (2, 4)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, 4), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(incharge_table)
    elements.append(Spacer(1, 0.2 * inch))

    # DEO Details Section - without icon
    elements.append(Paragraph("DEO Details", section_style))

    # Create a table for DEO details with photo space
    deo_data = [
        ["Corporation Emp ID", mls_data.get("deo_cfms_id", ""), ""],
        ["Name", mls_data.get("deo_name", ""), "DEO"],
        ["Aadhaar Number", mls_data.get("deo_aadhaar_number", ""), "Photo"],
        ["Phone Number", mls_data.get("deo_phone_number", ""), ""]
    ]

    deo_table = Table(deo_data, colWidths=[150, 260, 70])
    deo_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('SPAN', (2, 0), (2, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, 3), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(deo_table)
    elements.append(Spacer(1, 0.2 * inch))

    # MLS Point Capacity Details - without icon
    elements.append(Paragraph("MLS Point Details", section_style))

    # Create a table for capacity details
    cell_style = ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        spaceAfter=2
    )

    # Safe paragraph wrapper
    def safe_paragraph(value, style):
        return Paragraph(str(value) if value is not None else "", style)

    # Table headers
    capacity_headers = ["MLS / Block Name", "Dimensions", "Area in Sq. Ft.", "Storage Capacity in MTs",
                        "Owned / Hired", "If rented, Private / AMC / Other", "Weighbridge Availability"]

    # Table data with wrapped Paragraphs
    capacity_data = [
        [safe_paragraph(h, cell_style) for h in capacity_headers],
        [
            safe_paragraph(mls_data.get("mls_point_name", ""), cell_style),
            safe_paragraph("", cell_style),  # Dimensions - left blank
            safe_paragraph(mls_data.get("godown_area_sqft", ""), cell_style),
            safe_paragraph(mls_data.get("storage_capacity_mts", ""), cell_style),
            safe_paragraph(mls_data.get("mls_point_ownership", ""), cell_style),
            safe_paragraph(mls_data.get("rented_type", ""), cell_style),
            safe_paragraph(mls_data.get("weighbridge_available", ""), cell_style)
        ]
    ]

    # Create and style the table
    capacity_table = Table(capacity_data, colWidths=[70, 65, 65, 65, 65, 70, 80])
    capacity_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(capacity_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Hire / Rent Details
    elements.append(Paragraph("Hire / Rent Details", section_style))

    hire_data = [
        ["Hired / Rented from", "Rental Period", "Rental Charges"],
        ["", "", ""]
    ]

    hire_table = Table(hire_data, colWidths=[170, 170, 140])
    hire_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(hire_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Location wise Image section
    elements.append(Paragraph("Location wise Image", section_style))

    image_data = [
        ["Entrance", "Exit", "Loading Area", "Unloading Area", "Storage", "Storage"],
        ["[IMG]", "[IMG]", "[IMG]", "[IMG]", "[IMG]", "[IMG]"]
    ]

    image_table = Table(image_data, colWidths=[80, 80, 80, 80, 80, 80])
    image_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(image_table)

    # Add page break for second page
    elements.append(Spacer(1, 0.5 * inch))

    # PAGE 2

    # Hamalies Details - without icon
    elements.append(Paragraph("Hamalies Details", section_style))

    hamalies_data = [
        ["Hamalies Engaged", "Rate per Quintal", "Rate per Carton Box", "Rate per Bale"],
        [mls_data.get("hamalies_working", ""), "", "", ""]
    ]

    hamalies_table = Table(hamalies_data, colWidths=[120, 140, 140, 140])
    hamalies_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(hamalies_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Stage II Contractor Details - without icon
    elements.append(Paragraph("Stage II Contractor Details", section_style))

    contractor_data = [
        ["Engaged Firm Name", "", ""],
        ["PAN / GST Details", "", "Owner /"],
        ["Owner / Authorised Person Name", "", "Authorised"],
        ["Owner / Authorised Aadhaar Number", "", "Person"],
        ["Contact Phone Number", "", "Photo"],
        ["Approved Rate Per Quintal", "", ""]
    ]

    contractor_table = Table(contractor_data, colWidths=[170, 250, 60])
    contractor_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('SPAN', (2, 0), (2, 5)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, 5), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(contractor_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Stage II Vehicle Details - without icon
    elements.append(Paragraph("Stage II Vehicle Details", section_style))

    vehicle_data = [
        ["Vehicles Engaged", "Own Vehicles Engaged", "Hired vehicles Engaged", "GPS Fitted Vehicles"],
        [mls_data.get("stage2_vehicles_registered", ""), "", "", mls_data.get("gps_installed_on_all_vehicles", "")]
    ]

    vehicle_table = Table(vehicle_data, colWidths=[120, 120, 120, 120])
    vehicle_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(vehicle_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Current Month Commodity Details - without icon
    elements.append(Paragraph("Current Month Commodity Details", section_style))

    commodities = [
        "Fortified Rice", "Fine Quality Rice", "Sugar", "P. Oil ½ Ltr.",
        "P. Oil 1 Ltr.", "RG Dall 1Kg Pkts.", "RG Dall", "Jowar",
        "Ragi", "Jaggery Powder", "Ragi Powder", "3 Kg THR Rice Pkts."
    ]

    commodity_data = [
        ["SL. No.", "Commodity", "Opening Balance", "Received Quantity", "Issued Quantity", "Closing Balance"]]
    for idx, commodity in enumerate(commodities, 1):
        commodity_data.append([str(idx), commodity, "", "", "", ""])

    commodity_table = Table(commodity_data, colWidths=[40, 100, 100, 100, 100, 100])
    commodity_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(commodity_table)

    # Add page break for third page
    elements.append(Spacer(1, 0.5 * inch))

    # PAGE 3

    # Past Six months Stock Movement Details - without icon
    elements.append(Paragraph("Past Six months Stock Movement Details", section_style))

    # Create complex table header for stock movement
    stock_header = [
        ["Commodity", "Month -1", "", "", "Month -2", "", "", "Month -3", "", "", "Month -4", "", "", "Month -5", "",
         "", "Month -6", "", ""],
        ["", "OB", "Receipt", "Issues", "OB", "Receipt", "Issues", "OB", "Receipt", "Issues",
         "OB", "Receipt", "Issues", "OB", "Receipt", "Issues", "OB", "Receipt", "Issues"]
    ]

    # Merge cells for the complex header
    stock_table = Table(stock_header + [[c] + [""] * 19 for c in commodities],
                        colWidths=[80] + [25] * 19)

    stock_styles = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),

        # Span the month headers
        ('SPAN', (1, 0), (3, 0)),  # Month -1
        ('SPAN', (4, 0), (6, 0)),  # Month -2
        ('SPAN', (7, 0), (9, 0)),  # Month -3
        ('SPAN', (10, 0), (12, 0)),  # Month -4
        ('SPAN', (13, 0), (15, 0)),  # Month -5
        ('SPAN', (16, 0), (18, 0)),
        # Month -6
    ]

    stock_table.setStyle(TableStyle(stock_styles))
    elements.append(stock_table)

    # Add page break for fourth page
    elements.append(Spacer(1, 0.5 * inch))

    # PAGE 4

    # CC Cameras Details - without icon
    elements.append(Paragraph("CC Cameras Details", section_style))

    cameras_data = [
        ["Cameras Maintenance Vendor", "CC Camers installed", "Cameras with Live Feed"],
        [mls_data.get("camera_vendor", ""), mls_data.get("cc_cameras_installed", ""), ""]
    ]

    cameras_table = Table(cameras_data, colWidths=[160, 160, 160])
    cameras_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(cameras_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Camera details for Block/MLS Point
    elements.append(Paragraph("Block / MLS Point Name", section_style))

    for i in range(1, 6):
        camera_row_data = [
            [f"Camera {i} Location", ""],
            [f"Camera {i} IP Address", ""]
        ]

        camera_row = Table(camera_row_data, colWidths=[160, 320])
        camera_row.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ]))
        elements.append(camera_row)

    elements.append(Paragraph("Add for more", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Another Block/MLS Point
    elements.append(Paragraph("Block / MLS Point Name", section_style))

    for i in range(1, 6):
        camera_row_data = [
            [f"Camera {i} Location", ""],
            [f"Camera {i} IP Address", ""]
        ]

        camera_row = Table(camera_row_data, colWidths=[160, 320])
        camera_row.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ]))
        elements.append(camera_row)

    elements.append(Paragraph("Add for more", styles['Normal']))

    # Build the PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer and write it to the response
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data