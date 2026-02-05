
import matplotlib.pyplot as plt

def create_submission_pdf():
    # Content
    course = "CSCN8010 - Practical Lab 1"
    name = "Student Name: Ali Cihan Ozdemir"
    student_id = "Student ID: 9091405"
    repo_url = "https://github.com/alicih4n/CSCN8010-Practical-Lab1.git"
    
    # Create a figure
    fig = plt.figure(figsize=(8.5, 11)) # Letter size
    plt.axis('off')
    
    # Add text
    plt.text(0.5, 0.8, course, ha='center', fontsize=20, weight='bold')
    plt.text(0.5, 0.7, "Submission Details", ha='center', fontsize=16, weight='bold', style='italic')
    
    plt.text(0.2, 0.6, name, fontsize=14)
    plt.text(0.2, 0.55, student_id, fontsize=14)
    plt.text(0.2, 0.5, "Repository Link:", fontsize=14, weight='bold')
    plt.text(0.2, 0.45, repo_url, fontsize=12, color='blue')

    # Project Summary
    summary_title = "Project Summary"
    summary_text = (
        "This project implements a predictive maintenance system for manufacturing robots.\n"
        "1. Data Ingestion: Streamed sensor data into a Neon.tech PostgreSQL database.\n"
        "2. Modeling: Performed Univariate Linear Regression on 8 sensor axes to determine trends.\n"
        "3. Thresholds: Calculated residuals and established MinC (Alert) and MaxC (Error)\n"
        "   thresholds based on statistical variance (2-sigma and 3-sigma).\n"
        "4. Alert System: Developed a real-time monitor that logs events when anomalies\n"
        "   persist for a continuous duration (T seconds).\n"
    )
    
    plt.text(0.5, 0.35, summary_title, ha='center', fontsize=14, weight='bold')
    plt.text(0.1, 0.15, summary_text, fontsize=11, wrap=True)
    
    # Save as PDF
    output_path = "CSCN8010_Lab1_Submission.pdf"
    plt.savefig(output_path, bbox_inches='tight')
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    create_submission_pdf()
