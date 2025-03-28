import os
import re
import fitz  # PyMuPDF
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using multiple methods to ensure success.
    """
    text = ""
    
    # Method 1: Try PyMuPDF (digital PDFs)
    try:
        with fitz.open(pdf_path) as doc:
            text = "\n".join(page.get_text() for page in doc).strip()
        if text and len(text) > 100:  # If substantial text was extracted
            print(f"Text successfully extracted using PyMuPDF from {pdf_path}")
            print(f"Text length: {len(text)} characters")
            return text
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
    
    # Method 2: Try pdfplumber (better for some digital PDFs)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages_text).strip()
        if text and len(text) > 100:  # If substantial text was extracted
            print(f"Text successfully extracted using pdfplumber from {pdf_path}")
            return text
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
    
    return "Text extraction failed for this document."

def parse_mcq_section(lines, start_index):
    """
    Parse a Multiple Choice Questions section, creating a structured 
    representation of questions and their options.
    """
    questions = []
    i = start_index
    
    # First line after "Multiple Choice Questions:" should be skipped if empty
    if i < len(lines) and not lines[i].strip():
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check if we've reached a different section
        if re.match(r'^(True\s+or\s+False|Short\s+Answer|Long\s+Answer)', line, re.IGNORECASE):
            break
        
        # Check if this is a question (starts with a number)
        question_match = re.match(r'^(\d+)[\.)\s]+(.+)', line)
        if question_match:
            q_num = question_match.group(1)
            q_text = question_match.group(2).strip()
            
            # Create a new question entry
            question = {
                "number": q_num,
                "text": f"{q_num}. {q_text}",
                "type": "mcq",
                "options": []
            }
            
            # Move to the next line to look for options
            i += 1
            
            # Look for 4 options
            option_count = 0
            while i < len(lines) and option_count < 4:
                option_line = lines[i].strip()
                
                # Skip empty lines
                if not option_line:
                    i += 1
                    continue
                
                # Check if this is an option (starts with a number or letter)
                option_match = re.match(r'^([a-d1-4])[\.)\s]+(.+)', option_line, re.IGNORECASE)
                if option_match:
                    opt_num = option_match.group(1)
                    opt_text = option_match.group(2).strip()
                    
                    # Add the option to the current question
                    question["options"].append({
                        "letter": opt_num,
                        "text": f"{opt_num}. {opt_text}"
                    })
                    
                    option_count += 1
                    i += 1
                else:
                    # If this line doesn't match an option pattern, it might be the next question
                    break
            
            # Add the question to our list
            questions.append(question)
        else:
            # If the line doesn't match a question pattern, skip it
            i += 1
    
    return questions, i

def parse_true_false_section(lines, start_index):
    """
    Parse a True/False section.
    """
    questions = []
    i = start_index
    
    # First line after "True or False:" should be skipped if empty
    if i < len(lines) and not lines[i].strip():
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check if we've reached a different section
        if re.match(r'^(Multiple\s+Choice|Short\s+Answer|Long\s+Answer)', line, re.IGNORECASE):
            break
        
        # Check if this is a true/false question
        question_match = re.match(r'^(\d+)[\.)\s]+(.+)', line)
        if question_match:
            q_num = question_match.group(1)
            q_text = question_match.group(2).strip()
            
            # Create a new question entry
            question = {
                "number": q_num,
                "text": f"{q_num}. {q_text}",
                "type": "true_false",
                "options": []  # No options for true/false questions
            }
            
            questions.append(question)
        
        i += 1
    
    return questions, i

def parse_short_answer_section(lines, start_index):
    """
    Parse a Short Answer section.
    """
    questions = []
    i = start_index
    
    # First line after "Short Answer Questions:" should be skipped if empty
    if i < len(lines) and not lines[i].strip():
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check if we've reached a different section
        if re.match(r'^(Multiple\s+Choice|True\s+or\s+False|Long\s+Answer)', line, re.IGNORECASE):
            break
        
        # Check if this is a question
        question_match = re.match(r'^(\d+)[\.)\s]+(.+)', line)
        if question_match:
            q_num = question_match.group(1)
            q_text = question_match.group(2).strip()
            
            # Create a new question entry
            question = {
                "number": q_num,
                "text": f"{q_num}. {q_text}",
                "type": "short_answer",
                "options": []  # No options for short answer questions
            }
            
            questions.append(question)
        
        i += 1
    
    return questions, i

def parse_long_answer_section(lines, start_index):
    """
    Parse a Long Answer section.
    """
    questions = []
    i = start_index
    
    # First line after "Long Answer Questions:" should be skipped if empty
    if i < len(lines) and not lines[i].strip():
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check if we've reached a different section
        if re.match(r'^(Multiple\s+Choice|True\s+or\s+False|Short\s+Answer)', line, re.IGNORECASE):
            break
        
        # Check if this is a question
        question_match = re.match(r'^(\d+)[\.)\s]+(.+)', line)
        if question_match:
            q_num = question_match.group(1)
            q_text = question_match.group(2).strip()
            
            # Create a new question entry
            question = {
                "number": q_num,
                "text": f"{q_num}. {q_text}",
                "type": "long_answer",
                "options": []  # No options for long answer questions
            }
            
            questions.append(question)
        
        i += 1
    
    return questions, i

def parse_questionnaire(text):
    """
    Parse the questionnaire by sections, handling each type of question appropriately.
    """
    # Clean up the text
    text = re.sub(r'\n+', '\n', text)  # Normalize line breaks
    
    # Split into lines and clean them
    lines = [line.strip() for line in text.split('\n')]
    
    all_questions = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check for section headers
        if re.match(r'^Multiple\s+Choice', line, re.IGNORECASE):
            print(f"Found section: Multiple Choice")
            mcq_questions, i = parse_mcq_section(lines, i + 1)
            all_questions.extend(mcq_questions)
            continue
            
        elif re.match(r'^True\s+or\s+False', line, re.IGNORECASE):
            print(f"Found section: True or False")
            tf_questions, i = parse_true_false_section(lines, i + 1)
            all_questions.extend(tf_questions)
            continue
            
        elif re.match(r'^Short\s+Answer', line, re.IGNORECASE):
            print(f"Found section: Short Answer")
            sa_questions, i = parse_short_answer_section(lines, i + 1)
            all_questions.extend(sa_questions)
            continue
            
        elif re.match(r'^Long\s+Answer', line, re.IGNORECASE):
            print(f"Found section: Long Answer")
            la_questions, i = parse_long_answer_section(lines, i + 1)
            all_questions.extend(la_questions)
            continue
        
        # If none of the above, move to the next line
        i += 1
    
    print(f"Extracted {len(all_questions)} questions in total")
    return all_questions

def create_structured_pdf(questions, output_path):
    """
    Create a well-structured PDF with questions correctly grouped by type.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    subheading_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # Build the PDF content
    content = []
    content.append(Paragraph("Questionnaire", title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Group questions by type
    mcq_questions = [q for q in questions if q["type"] == "mcq"]
    tf_questions = [q for q in questions if q["type"] == "true_false"]
    sa_questions = [q for q in questions if q["type"] == "short_answer"]
    la_questions = [q for q in questions if q["type"] == "long_answer"]
    
    # Add MCQ questions
    if mcq_questions:
        content.append(Paragraph("Multiple Choice Questions:", heading_style))
        content.append(Spacer(1, 0.15*inch))
        
        for question in mcq_questions:
            content.append(Paragraph(question["text"], subheading_style))
            content.append(Spacer(1, 0.05*inch))
            
            # Add options
            for option in question["options"]:
                content.append(Paragraph(option["text"], normal_style))
            
            content.append(Spacer(1, 0.15*inch))
    
    # Add True/False questions
    if tf_questions:
        content.append(Paragraph("True or False:", heading_style))
        content.append(Spacer(1, 0.15*inch))
        
        for question in tf_questions:
            content.append(Paragraph(question["text"], subheading_style))
            content.append(Spacer(1, 0.15*inch))
    
    # Add Short Answer questions
    if sa_questions:
        content.append(Paragraph("Short Answer Questions:", heading_style))
        content.append(Spacer(1, 0.15*inch))
        
        for question in sa_questions:
            content.append(Paragraph(question["text"], subheading_style))
            content.append(Spacer(1, 0.15*inch))
    
    # Add Long Answer questions
    if la_questions:
        content.append(Paragraph("Long Answer Questions:", heading_style))
        content.append(Spacer(1, 0.15*inch))
        
        for question in la_questions:
            content.append(Paragraph(question["text"], subheading_style))
            content.append(Spacer(1, 0.15*inch))
    
    # Build and save the PDF
    doc.build(content)
    print(f"Structured questionnaire saved to {output_path}")

def main():
    # File paths
    project_dir = r"D:\Shraddha_Project"
    questionnaire_pdf = os.path.join(project_dir, "DL_QNS1.pdf")  # Replace with your questionnaire
    output_pdf = os.path.join(project_dir, "STRUCTURED_QUESTIONS.pdf")
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(questionnaire_pdf)
    
    # Parse the questionnaire into structured questions
    questions = parse_questionnaire(pdf_text)
    
    # Display the parsed questions for verification
    print("\nParsed Questions:")
    
    # Group questions by type for clearer display
    question_types = {"mcq": [], "true_false": [], "short_answer": [], "long_answer": []}
    for q in questions:
        question_types[q["type"]].append(q)
    
    # Display MCQ questions
    print("\nMultiple Choice Questions:")
    for i, q in enumerate(question_types["mcq"], 1):
        print(f"Question {i}: {q['text']}")
        print("  Options:")
        for opt in q["options"]:
            print(f"    - {opt['text']}")
    
    # Display True/False questions
    print("\nTrue or False Questions:")
    for i, q in enumerate(question_types["true_false"], 1):
        print(f"Question {i}: {q['text']}")
    
    # Display Short Answer questions
    print("\nShort Answer Questions:")
    for i, q in enumerate(question_types["short_answer"], 1):
        print(f"Question {i}: {q['text']}")
    
    # Display Long Answer questions
    print("\nLong Answer Questions:")
    for i, q in enumerate(question_types["long_answer"], 1):
        print(f"Question {i}: {q['text']}")
    
    # Create the structured PDF
    create_structured_pdf(questions, output_pdf)

if __name__ == "__main__":
    main()