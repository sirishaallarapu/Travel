from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

def generate_pdf(data):
    """
    Generate a PDF from the itinerary data with a logo in the top right corner of every page.
    Args:
        data (dict): A dictionary containing the itinerary (as a nested dictionary).
    Returns:
        BytesIO: A buffer containing the generated PDF.
    """
    # Extract the itinerary from the data
    itinerary = data.get("itinerary", {})
    vibe = data.get("vibe", "Adventure Vibe")
    total_budget = data.get("total_budget", None)

    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()

    # Define page margins
    margin = 0.75 * inch
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin + 0.5 * inch,  # Extra space for header
        bottomMargin=margin
    )
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        name="Title",
        fontSize=18,
        spaceAfter=12,
        textColor=colors.navy,
        alignment=1  # Center
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        fontSize=12,
        spaceAfter=12,
        textColor=colors.gray,
        alignment=1  # Center
    )
    heading_style = ParagraphStyle(
        name="Heading",
        fontSize=14,
        spaceAfter=12,
        textColor=colors.navy,
    )
    section_style = ParagraphStyle(
        name="Section",
        fontSize=12,
        spaceAfter=6,
        textColor=colors.black,
    )
    item_style = ParagraphStyle(
        name="Item",
        fontSize=10,
        spaceAfter=4,
        leading=12,
    )

    # Path to the logo (ensure this path is correct on your system)
    logo_path = r"C:\Users\Dell\Desktop\travel\frontend\src\assets\infologo1.png"

    # Function to draw the header (logo) on each page
    def draw_header(canvas, doc):
        # Set the position for the logo (top right)
        page_width, page_height = letter
        logo_width = 1 * inch
        logo_height = 0.5 * inch
        logo_x = page_width - margin - logo_width
        logo_y = page_height - margin - logo_height

        try:
            # Draw the logo image
            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.drawOn(canvas, logo_x, logo_y)
        except Exception as e:
            # Fallback to a placeholder if the logo fails to load
            canvas.saveState()
            canvas.setStrokeColor(colors.gray)
            canvas.setFillColor(colors.lightgrey)
            canvas.rect(logo_x, logo_y, logo_width, logo_height, fill=1)
            canvas.setFillColor(colors.black)
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(logo_x + logo_width / 2, logo_y + logo_height / 2, "[Logo]")
            canvas.restoreState()

    # Build the PDF content
    story = []

    # Add title and subtitle
    story.append(Paragraph("Your Trip Itinerary", title_style))
    story.append(Paragraph(f"{vibe} | June 24, 2025 – June 28, 2025", subtitle_style))
    total_budget_str = f"Total Estimated Cost: ₹{total_budget:,}" if total_budget else "Total Estimated Cost: Not Available"
    story.append(Paragraph(total_budget_str, subtitle_style))
    story.append(Spacer(1, 12))

    # Add itinerary content
    for day, sections in itinerary.items():
        # Add day heading
        story.append(Paragraph(day, heading_style))
        story.append(Spacer(1, 6))

        # Handle error case
        if "Error" in sections:
            story.append(Paragraph(sections["Error"][0], item_style))
            story.append(Spacer(1, 12))
            continue

        # Add transportation
        if sections.get("Transportation"):
            story.append(Paragraph("Transportation:", section_style))
            for item in sections["Transportation"]:
                story.append(Paragraph(item.replace("Transportation:", "").strip(), item_style))

        # Add accommodation
        if sections.get("Accommodation"):
            story.append(Paragraph("Accommodation:", section_style))
            for item in sections["Accommodation"]:
                story.append(Paragraph(item.replace("Accommodation:", "").strip(), item_style))

        # Add planned activities
        if sections.get("Planned Activities"):
            story.append(Paragraph("Planned Activities:", section_style))
            for item in sections["Planned Activities"]:
                story.append(Paragraph(item, item_style))

        # Add meals
        if sections.get("Meals"):
            story.append(Paragraph("Meals for the Day:", section_style))
            for item in sections["Meals"]:
                story.append(Paragraph(item, item_style))

        # Add total cost for the day
        if sections.get("Total Cost"):
            story.append(Paragraph(sections["Total Cost"], section_style))

        # Add spacing between days
        story.append(Spacer(1, 12))

    # Build the PDF with the custom header
    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)

    # Reset the buffer position to the beginning
    buffer.seek(0)
    return buffer