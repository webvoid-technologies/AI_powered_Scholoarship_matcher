<p align="center">
  <img src="https://www.webvoidtechnologies.com/webvoid_logo_tm.png" alt="Webvoid Technologies" width="220">
</p>

# AI Scholarship & Opportunity Matcher

**Developed by Webvoid Technologies**

A production-ready Flask Application that uses the Groq API to help students discover personalized scholarships, internships, hackathons, fellowships, certifications, and career opportunities based on their academic profile, skills, interests, and career goals.

## Features

- Student Profile Analyzer
- AI Scholarship Matcher (Government, Private, International, Women, Minority, Merit, Need-Based)
- AI Internship Matcher
- AI Hackathon & Competition Matcher
- AI Fellowship & Research Opportunity Matcher
- AI Certification & Learning Roadmap Generator
- AI Resume & Skill Gap Analyzer
- AI Career Opportunity Report with downloadable Markdown report
- Responsive dashboard with glassmorphism UI
- Match percentage progress rings
- Career roadmap timeline
- Toast notifications and loading states

## Technology Stack

- Python 3.11+
- Flask + Flask Blueprints
- Jinja2 Templates
- Tailwind CSS (CDN)
- Vanilla JavaScript + Fetch API
- Groq API (Llama 3.3 / DeepSeek / Qwen)
- python-dotenv, requests, httpx

## Project Structure

```
AI_SCHOLARSHIP_MATCHER/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── routes/
│   ├── profile.py
│   ├── scholarship.py
│   ├── internship.py
│   ├── hackathon.py
│   ├── fellowship.py
│   ├── certification.py
│   ├── skill_gap.py
│   └── career_report.py
├── services/
│   ├── groq_service.py
│   └── validation.py
├── prompts/
│   ├── profile_prompt.txt
│   ├── scholarship_prompt.txt
│   ├── internship_prompt.txt
│   ├── hackathon_prompt.txt
│   ├── fellowship_prompt.txt
│   ├── certification_prompt.txt
│   ├── skill_gap_prompt.txt
│   └── career_report_prompt.txt
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── assets/
├── README.ms
└── PROJECT_DOC.md
```

## Setup Instructions

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free Groq API key from [https://console.groq.com](https://console.groq.com).

4. Run the application:

```bash
python app.py
```

5. Open in browser:

```
http://localhost:5000
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | Model name, e.g. `llama-3.3-70b-versatile` |
| `SECRET_KEY` | Flask secret key |
| `FLASK_DEBUG` | Enable debug mode (`True`/`False`) |

## API Endpoints

All endpoints accept JSON and return JSON.

| Endpoint | Description |
|----------|-------------|
| `GET /` | Render dashboard |
| `POST /api/analyze-profile` | Analyze student profile |
| `POST /api/match-scholarships` | Match scholarships |
| `POST /api/match-internships` | Match internships |
| `POST /api/match-hackathons` | Match hackathons and competitions |
| `POST /api/match-fellowships` | Match fellowships and research opportunities |
| `POST /api/generate-certifications` | Generate certification roadmap |
| `POST /api/skill-gap` | Analyze skill gaps |
| `POST /api/career-report` | Generate full career report |

## Demo Mode

If `GROQ_API_KEY` is not configured, the application automatically returns realistic sample data so the project can be demonstrated without an active API key.

## Support

For questions or support, contact [studentprogram@webvoidtechnologies.com](mailto:studentprogram@webvoidtechnologies.com).
