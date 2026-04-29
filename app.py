import streamlit as st
from PyPDF2 import PdfReader
import urllib.parse
import re
import time
import requests

st.set_page_config(
    page_title="ResuMetric Pro AI | Ayush Chaudhary",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 45%, #f5f0ff 100%);
}

[data-testid="stHeader"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    max-width: 1200px;
}

button[title="View fullscreen"] {
    display: none !important;
}

.hero {
    background: linear-gradient(135deg, #0f172a 0%, #2563eb 55%, #7c3aed 100%);
    padding: 54px;
    border-radius: 34px;
    color: white;
    box-shadow: 0 25px 70px rgba(37,99,235,0.25);
    margin-bottom: 28px;
}

.hero h1 {
    font-size: 58px;
    font-weight: 900;
    margin: 0;
}

.hero p {
    font-size: 21px;
    color: #e0f2fe;
    margin-top: 16px;
    max-width: 780px;
}

.badge {
    display: inline-block;
    margin-top: 20px;
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.28);
    padding: 11px 20px;
    border-radius: 999px;
    font-weight: 700;
    letter-spacing: 1px;
}

.card {
    background: rgba(255,255,255,0.92);
    border: 1px solid #e5e7eb;
    border-radius: 26px;
    padding: 26px;
    box-shadow: 0 16px 45px rgba(15,23,42,0.08);
    margin-bottom: 22px;
}

.upload-img {
    background: linear-gradient(135deg, #eff6ff, #f5f3ff);
    border-radius: 22px;
    padding: 22px;
    text-align: center;
}

.metric-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 12px 30px rgba(15,23,42,0.06);
}

.feature {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 24px;
    min-height: 145px;
    text-align: center;
    box-shadow: 0 12px 30px rgba(15,23,42,0.06);
}

.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: linear-gradient(90deg, #0f172a, #1e3a8a);
    color: white;
    text-align: center;
    padding: 13px;
    font-size: 14px;
    font-weight: 500;
    z-index: 100;
}

a {
    text-decoration: none !important;
    font-weight: 700;
    color: #2563eb !important;
}
</style>
""", unsafe_allow_html=True)


def get_experience_data(text):
    text = text.lower()
    current_year = 2026

    date_ranges = re.findall(
        r'(\b(?:jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|sept|oct|nov|dec|march|april|august|september|october|november|december)?\.?\s*\d{4})\s*[-–]\s*(present|current|\b(?:jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|sept|oct|nov|dec|march|april|august|september|october|november|december)?\.?\s*\d{4})',
        text
    )

    total_years = 0

    for start, end in date_ranges:
        start_year = re.search(r'\d{4}', start)
        end_year = re.search(r'\d{4}', end)

        if start_year:
            sy = int(start_year.group())
            ey = current_year if end in ["present", "current"] else int(end_year.group()) if end_year else sy
            if ey >= sy and 2000 <= sy <= current_year:
                total_years += max(1, ey - sy)

    direct_years = re.findall(r'(\d+)\+?\s*(?:year|years|yr|yrs)', text)
    if direct_years:
        total_years = max(total_years, max([int(y) for y in direct_years]))

    if total_years == 0:
        return "Fresher 🎓", "Entry Level"
    elif total_years <= 2:
        return f"{total_years}+ Year 💼", "Junior Level"
    elif total_years <= 5:
        return f"{total_years}+ Years 💼", "Mid Level"
    else:
        return f"{total_years}+ Years 🚀", "Senior Level"

def get_job_links(role):
    q = urllib.parse.quote(role)
    return {
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords={q}",
        "Indeed": f"https://www.indeed.com/jobs?q={q}",
        "Naukri": f"https://www.naukri.com/{role.replace(' ', '-')}-jobs",
        "Internshala": f"https://internshala.com/jobs/keywords-{q}",
        "Google": f"https://www.google.com/search?q={q}+jobs"
    }


def detect_roles(full_text):
    role_rules = {
        "Teaching / Education": {
            "strong": ["b.ed", "bed", "teacher", "teaching", "ktet", "school", "lesson plan"],
            "normal": ["education", "students", "classroom", "english language", "english literature", "powerpoint presentations"],
            "roles": ["English Teacher", "School Teacher"],
            "reason": "Detected teaching qualifications/experience such as B.Ed, KTET, teacher role, school experience, or student-focused skills."
        },
        "PMO / IT Operations": {
            "strong": ["pmo", "service level manager", "service delivery", "sla", "governance review", "weekly service review", "monthly service review"],
            "normal": ["kpi", "dashboard", "vendor", "resource utilization", "servicenow", "beeline", "stakeholders", "incident", "excel"],
            "roles": ["PMO Analyst", "Service Delivery Coordinator"],
            "reason": "Detected PMO/service delivery work such as SLA tracking, governance reviews, KPI reporting, vendor coordination, and resource utilization."
        },
        "Law / Legal": {
            "strong": ["llb", "llm", "law", "legal", "advocate", "court", "litigation"],
            "normal": ["contract", "criminal law", "legal research", "case law", "compliance", "moot court", "solicitor"],
            "roles": ["Legal Associate", "Legal Research Intern"],
            "reason": "Detected legal education/experience such as LLB, law subjects, legal research, contracts, court exposure, or litigation terms."
        },
        "Psychology / Counselling": {
            "strong": ["psychologist", "psychology", "counselling", "counseling", "therapy", "therapist"],
            "normal": ["mental health", "cbt", "clinical", "psychotherapy", "anxiety", "depression", "mindfulness"],
            "roles": ["Counselling Psychologist", "Clinical Psychology Intern"],
            "reason": "Detected psychology/counselling background through therapy, CBT, mental health, clinical exposure, or psychologist-related experience."
        },
        "Software / IT": {
            "strong": ["python", "java", "javascript", "react", "django", "flask", "fastapi"],
            "normal": ["api", "backend", "frontend", "html", "css", "sql", "mysql", "software", "github"],
            "roles": ["Software Developer", "Python Backend Developer"],
            "reason": "Detected software development skills such as programming languages, frameworks, APIs, databases, or frontend/backend terms."
        },
        "Data / AI": {
            "strong": ["data analyst", "data science", "machine learning", "deep learning"],
            "normal": ["pandas", "numpy", "scikit-learn", "tensorflow", "power bi", "tableau", "data visualization"],
            "roles": ["Data Analyst", "AI/ML Engineer"],
            "reason": "Detected data/AI skills such as data science, machine learning, analytics tools, Python libraries, or visualization platforms."
        },
        "Commerce / Finance": {
            "strong": ["b.com", "bcom", "commerce", "accounting", "finance"],
            "normal": ["gst", "tally", "audit", "taxation", "bookkeeping", "financial statements"],
            "roles": ["Accounts Executive", "Finance Associate"],
            "reason": "Detected commerce/finance background such as accounting, finance, GST, Tally, audit, or taxation."
        },
        "Business / Management": {
            "strong": ["bba", "business administration", "management trainee", "business development"],
            "normal": ["marketing", "sales", "operations", "client handling", "market research"],
            "roles": ["Business Development Executive", "Management Trainee"],
            "reason": "Detected business/management background through BBA, sales, marketing, operations, or business development terms."
        },
        "Medical / Healthcare": {
            "strong": ["mbbs", "bds", "bams", "bhms", "nursing", "pharmacy"],
            "normal": ["hospital", "patient care", "clinical", "healthcare", "medical", "physiotherapy"],
            "roles": ["Clinical Assistant", "Healthcare Coordinator"],
            "reason": "Detected healthcare background through medical education, hospital exposure, patient care, or clinical terms."
        }
    }

    best_domain = None
    best_score = 0
    best_reason = ""

    for domain, data in role_rules.items():
        strong_score = sum(3 for keyword in data["strong"] if keyword in full_text)
        normal_score = sum(1 for keyword in data["normal"] if keyword in full_text)
        total_score = strong_score + normal_score

        if total_score > best_score:
            best_score = total_score
            best_domain = domain
            best_reason = data["reason"]

    if best_score == 0:
        return ["General Fresher Role", "Project Coordinator"], "Low", "No strong domain-specific keywords were detected."

    if best_score >= 8:
        confidence = "High"
    elif best_score >= 4:
        confidence = "Medium"
    else:
        confidence = "Low"

    return role_rules[best_domain]["roles"], confidence, best_reason
st.markdown("""
<div class="hero">
    <h1>🚀 ResuMetric Pro AI</h1>
    <p>AI-powered resume analyzer that helps you improve your resume, detect experience level, and find matching jobs faster.</p>
    <div class="badge">SMART AUDIT • ATS OPTIMIZATION • JOB MATCHING • DIRECT APPLY HUB</div>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([2.2, 1])

with right_col:
    st.markdown("""
    <div class="card">
        <h2>📥 Smart Resume Upload</h2>
        <div class="upload-img">
            <svg width="100%" height="230" viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="90" y="28" width="190" height="220" rx="18" fill="white" stroke="#dbeafe" stroke-width="4"/>
                <rect x="120" y="65" width="90" height="12" rx="6" fill="#2563eb"/>
                <rect x="120" y="95" width="130" height="9" rx="5" fill="#c7d2fe"/>
                <rect x="120" y="120" width="120" height="9" rx="5" fill="#c7d2fe"/>
                <rect x="120" y="145" width="135" height="9" rx="5" fill="#c7d2fe"/>
                <circle cx="280" cy="150" r="52" fill="#eff6ff" stroke="#2563eb" stroke-width="8"/>
                <path d="M258 150L274 166L306 130" stroke="#22c55e" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="250" y="25" width="88" height="88" rx="18" fill="#7c3aed"/>
                <text x="272" y="80" fill="white" font-size="34" font-weight="700">AI</text>
                <circle cx="97" cy="40" r="20" fill="#dbeafe"/>
                <path d="M97 29V50M86 39L97 28L108 39" stroke="#2563eb" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <p style="color:#475569; margin-top:14px;">Upload your PDF resume and get instant AI-based career insights.</p>
    </div>
    """, unsafe_allow_html=True)

    resume_file = st.file_uploader("Upload your resume PDF", type="pdf")

    st.markdown("""
    <div class="card">
        <h2>🎨 Premium CV Templates</h2>
        <p style="color:#475569;">Hand-picked resume template sources for better ATS visibility.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⭐ Modern Tech Resume"):
        st.markdown("[Visit Canva Library 🔗](https://www.canva.com/resumes/templates/)")

    with st.expander("💼 Executive Resume"):
        st.markdown("[Visit Novoresume 🔗](https://novoresume.com/)")

    with st.expander("🔬 Academic / Research CV"):
        st.markdown("[Visit Overleaf 🔗](https://www.overleaf.com/gallery/tagged/cv)")


with left_col:
    if resume_file:
        with st.status("AI is analyzing your resume...", expanded=False) as status:
            time.sleep(1.2)
            reader = PdfReader(resume_file)

            try:
                full_text = " ".join([p.extract_text() or "" for p in reader.pages]).lower()
            except:
                full_text = ""

            exp_text, tier = get_experience_data(full_text)
            status.update(label="Resume analysis completed!", state="complete")

        st.markdown('<div class="card"><h2>📊 Resume Intelligence Dashboard</h2></div>', unsafe_allow_html=True)

        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-box">
                <p>Experience Detection</p>
                <h1>{exp_text}</h1>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-box">
                <p>Market Seniority</p>
                <h1>{tier}</h1>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
            <h2>🔥 Top Market Matches & Application Hub</h2>
            <p style="color:#475569;">Best matching job roles based on your resume keywords.</p>
        </div>
        """, unsafe_allow_html=True)

        potential_roles = detect_roles(full_text)

        for role in potential_roles:
            st.markdown(f"### {role}")
            links = get_job_links(role)
            row = st.columns(5)
            row[0].markdown(f"[LinkedIn]({links['LinkedIn']})")
            row[1].markdown(f"[Indeed]({links['Indeed']})")
            row[2].markdown(f"[Naukri]({links['Naukri']})")
            row[3].markdown(f"[Internshala]({links['Internshala']})")
            row[4].markdown(f"[Google]({links['Google']})")

        st.success("✅ Recruiter Insight: Your resume has been scanned for role-based matching.")

        st.markdown("""
        <div class="card">
            <h2>✅ Resume Optimization Focus</h2>
            <p style="color:#475569;">Improve keywords, project impact, skills alignment, and ATS readability before applying.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="card">
            <h2>🔍 Analyze Your Resume Like a Recruiter</h2>
            <p style="color:#475569; font-size:18px;">
                Upload your resume PDF from the right panel. ResuMetric Pro AI will scan your resume,
                detect your experience level, and suggest matching job roles.
            </p>
            <svg width="100%" height="290" viewBox="0 0 760 300" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="55" y="25" width="250" height="245" rx="22" fill="white" stroke="#dbeafe" stroke-width="4"/>
                <rect x="90" y="65" width="120" height="14" rx="7" fill="#2563eb"/>
                <rect x="90" y="102" width="165" height="10" rx="5" fill="#c7d2fe"/>
                <rect x="90" y="132" width="140" height="10" rx="5" fill="#c7d2fe"/>
                <rect x="90" y="162" width="160" height="10" rx="5" fill="#c7d2fe"/>
                <rect x="90" y="205" width="110" height="12" rx="6" fill="#bfdbfe"/>
                <circle cx="315" cy="170" r="62" fill="#eff6ff" stroke="#2563eb" stroke-width="10"/>
                <path d="M290 170L307 188L345 145" stroke="#22c55e" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="420" y="50" width="260" height="190" rx="24" fill="#f8fafc" stroke="#ddd6fe" stroke-width="4"/>
                <text x="455" y="95" fill="#0f172a" font-size="24" font-weight="800">ATS Score</text>
                <circle cx="535" cy="160" r="52" fill="white" stroke="#22c55e" stroke-width="12"/>
                <text x="505" y="172" fill="#0f172a" font-size="36" font-weight="900">92</text>
                <text x="585" y="162" fill="#64748b" font-size="18">/100</text>
            </svg>
        </div>
        """, unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)

        with f1:
            st.markdown("""
            <div class="feature">
                <h1>🤖</h1>
                <h3>AI Resume Analysis</h3>
                <p>Scans your resume content instantly.</p>
            </div>
            """, unsafe_allow_html=True)

        with f2:
            st.markdown("""
            <div class="feature">
                <h1>📊</h1>
                <h3>Experience Detection</h3>
                <p>Finds your career level automatically.</p>
            </div>
            """, unsafe_allow_html=True)

        with f3:
            st.markdown("""
            <div class="feature">
                <h1>💼</h1>
                <h3>Job Match Hub</h3>
                <p>Gives direct job apply links.</p>
            </div>
            """, unsafe_allow_html=True)


st.markdown("""
<div class="footer">
    Developed with ❤️ by Ayush Chaudhary | Mathura, India | © 2026 ResuMetric Pro AI
</div>
""", unsafe_allow_html=True)