"""
PDF Generation Utility for Water Quality Reports
"""
import os
import tempfile
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_water_quality_report(location, water_data, analysis):
    """
    Generate a PDF report for water quality analysis using ReportLab
    
    Args:
        location: Dictionary or sqlite3.Row containing location information
        water_data: Dictionary or sqlite3.Row containing water quality parameters
        analysis: Dictionary containing analysis results
        
    Returns:
        Path to the generated PDF file
    """
    try:
        # Convert sqlite3.Row objects to dictionaries if needed
        if isinstance(location, sqlite3.Row):
            location = dict(location)
            
        if isinstance(water_data, sqlite3.Row):
            water_data = dict(water_data)
            
        # Create a temporary file for the PDF
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_file.close()
        
        # Generate a filename for the report
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        # Handle date which might be a datetime object or a string
        if hasattr(water_data.get('date_submitted', None), 'strftime'):
            sample_date = water_data['date_submitted'].strftime('%Y-%m-%d')
        else:
            sample_date = str(water_data.get('date_submitted', 'N/A'))
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_file.name,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Set up styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add custom styles
        safety_style = ParagraphStyle('SafetyStyle', parent=normal_style, textColor=colors.green)
        concern_style = ParagraphStyle('ConcernStyle', parent=normal_style, textColor=colors.red)
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=normal_style,
            backColor=colors.lightgreen,
            borderColor=colors.green,
            borderWidth=1,
            borderPadding=5,
            borderRadius=2
        )
        
        # Build the content
        content = []
        
        # Add title
        content.append(Paragraph(f"Water Quality Report: {location['location_name']}", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add report info
        content.append(Paragraph(f"Location: {location['location_name']}", subtitle_style))
        content.append(Paragraph(f"Report Date: {report_date}", normal_style))
        content.append(Paragraph(f"Sample Date: {sample_date}", normal_style))
        if location.get('description'):
            content.append(Paragraph(f"Description: {location['description']}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add overall quality summary
        overall_quality = analysis.get('overall_quality', 'Unknown')
        quality_style = safety_style if overall_quality == 'Good' else concern_style
        content.append(Paragraph(f"Overall Water Quality: {overall_quality}", quality_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add water parameters table
        content.append(Paragraph("Water Quality Parameters", subtitle_style))
        
        # Prepare table data
        table_data = [['Parameter', 'Value', 'Unit', 'Analysis']]
        
        # Define the parameters with their detailed analysis information
        params = [
            ('pH', water_data.get('ph'), '', analysis.get('ph_analysis', 'No analysis available')),
            ('BOD', water_data.get('bod'), 'mg/l', analysis.get('bod_analysis', 'No analysis available')),
            ('COD', water_data.get('cod'), 'mg/l', analysis.get('cod_analysis', 'No analysis available')),
            ('Temperature', water_data.get('temperature'), '°C', analysis.get('temperature_analysis', 'No analysis available')),
            ('Ammonia', water_data.get('ammonia'), 'mg/l', analysis.get('ammonia_analysis', 'No analysis available')),
            ('Arsenic', water_data.get('arsenic'), 'mg/l', analysis.get('arsenic_analysis', 'No analysis available')),
            ('Calcium', water_data.get('calcium'), 'mg/l', analysis.get('calcium_analysis', 'No analysis available')),
            ('EC', water_data.get('ec'), 'μS/cm', analysis.get('ec_analysis', 'No analysis available')),
            ('Coliform', water_data.get('coliform'), 'N/100ml', analysis.get('coliform_analysis', 'No analysis available')),
            ('Hardness', water_data.get('hardness'), 'mg/l', analysis.get('hardness_analysis', 'No analysis available')),
            ('Lead', water_data.get('lead_pb'), 'mg/l', analysis.get('lead_analysis', 'No analysis available')),
            ('Nitrogen', water_data.get('nitrogen'), 'mg/l', analysis.get('nitrogen_analysis', 'No analysis available')),
            ('Sodium', water_data.get('sodium'), 'mg/l', analysis.get('sodium_analysis', 'No analysis available')),
            ('Sulfate', water_data.get('sulfate'), 'mg/l', analysis.get('sulfate_analysis', 'No analysis available')),
            ('TSS', water_data.get('tss'), 'mg/l', analysis.get('tss_analysis', 'No analysis available')),
            ('Turbidity', water_data.get('turbidity'), 'NTU', analysis.get('turbidity_analysis', 'No analysis available')),
            ('TDS', water_data.get('tds'), 'mg/l', analysis.get('tds_analysis', 'No analysis available'))
        ]
        
        for param in params:
            if param[1] is not None:
                # Create a paragraph for the analysis text to enable proper wrapping
                analysis_text = Paragraph(str(param[3]), normal_style)
                table_data.append([param[0], str(param[1]), param[2], analysis_text])
        
        # Create the table with adjusted column widths to accommodate analysis text
        table = Table(table_data, colWidths=[1*inch, 0.7*inch, 0.6*inch, 3.5*inch])
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
        
        table.setStyle(table_style)
        content.append(table)
        content.append(Spacer(1, 0.25*inch))
        
        # Add recommendations
        if analysis.get('recommendations'):
            content.append(Paragraph("Recommendations", subtitle_style))
            for rec in analysis.get('recommendations', []):
                content.append(Paragraph(f"• {rec}", normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Add summary
        if analysis.get('summary'):
            content.append(Paragraph("Summary", subtitle_style))
            content.append(Paragraph(analysis.get('summary', ''), normal_style))
        
        # Build and save the PDF
        doc.build(content)
        return pdf_file.name
    
    except Exception as e:
        # Print detailed error and traceback
        import traceback
        print(f"Error generating PDF: {e}")
        print(traceback.format_exc())
        
        # Clean up any temporary file if it exists
        if 'pdf_file' in locals() and os.path.exists(pdf_file.name):
            os.unlink(pdf_file.name)
        
        return None 