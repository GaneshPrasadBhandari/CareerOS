from fpdf import FPDF
import os

def create_resume(name, content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=name, ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for line in content:
        pdf.multi_cell(0, 10, txt=line)
    
    # Save in the data/resumes folder for the app to pick up
    os.makedirs("data/resumes", exist_ok=True)
    path = f"data/resumes/{filename}"
    pdf.output(path)
    print(f"✅ Success: Created {name}'s resume at {path}")

# --- DEMO CANDIDATE DATA ---
resumes = [
    {
        "name": "Ganesh - Principal AI Solution Architect",
        "filename": "Ganesh_AI_Architect.pdf",
        "content": [
            "Summary: 12+ years of experience in Enterprise AI Strategy.",
            "Core Skills: LLM Orchestration, RAG Systems, Multi-Agent Workflows.",
            "Tech Stack: Python, LangChain, Pinecone, PyTorch, Azure AI.",
            "Experience: Led AI transformation for Fortune 500 companies.",
            "Architectural Focus: Scalable MLOps and ethical AI governance."
        ]
    },
    {
        "name": "Ram - Senior Java Developer",
        "filename": "Ram_Java_Dev.pdf",
        "content": [
            "Summary: Senior Software Engineer specializing in high-concurrency systems.",
            "Core Skills: Java 21, Spring Boot, Microservices Architecture.",
            "Cloud/DevOps: AWS (EKS, Lambda), Docker, Terraform.",
            "Database: Kafka, PostgreSQL, Redis.",
            "Experience: Optimized backend performance by 40% for a global fintech app."
        ]
    },
    {
        "name": "Krishna - Manual QA Generalist",
        "filename": "Krishna_Manual_QA.pdf",
        "content": [
            "Summary: Quality Assurance specialist with a focus on User Experience.",
            "Core Skills: Manual Testing, Regression Testing, Exploratory Testing.",
            "Tools: Jira, TestRail, Postman, BrowserStack.",
            "Domain: Healthcare and E-commerce platform testing.",
            "Experience: Managed end-to-end testing for 50+ mobile application releases."
        ]
    }
]

if __name__ == "__main__":
    for r in resumes:
        create_resume(r["name"], r["content"], r["filename"])