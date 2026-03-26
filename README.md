<div align="center">

# Auto Job Applicant

### Automated Job Search & Application Bot

**Find, filter, and auto-apply to hundreds of job postings across 5 ATS platforms — hands-free.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-WebDriver-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-Parser-orange?style=for-the-badge)](https://www.crummy.com/software/BeautifulSoup/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[![Greenhouse](https://img.shields.io/badge/Greenhouse-supported-24A47F?style=flat-square)](https://www.greenhouse.io/)
[![Lever](https://img.shields.io/badge/Lever-supported-5B21B6?style=flat-square)](https://www.lever.co/)
[![Workable](https://img.shields.io/badge/Workable-supported-0EA5E9?style=flat-square)](https://www.workable.com/)
[![Ashby](https://img.shields.io/badge/Ashby-supported-1E293B?style=flat-square)](https://www.ashbyhq.com/)
[![SmartRecruiters](https://img.shields.io/badge/SmartRecruiters-supported-E11D48?style=flat-square)](https://www.smartrecruiters.com/)

[Features](#features) | [How It Works](#how-it-works) | [Setup](#setup) | [Usage](#usage) | [ATS Platforms](#supported-ats-platforms)

---

</div>

## The Problem

Applying to jobs is repetitive and time-consuming. You find a listing, fill the same form fields over and over — name, email, phone, upload CV, write a cover letter — across dozens of different platforms. Each one takes 5-15 minutes. Multiply that by 50+ applications and you've lost days.

## The Solution

Auto Job Applicant **automates the entire pipeline**:

```
Search → Filter → Detect ATS → Fill Form → Generate Cover Letter → Submit → Report
```

> *"Run the script, go grab a coffee, come back to 20+ applications submitted."*

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-ATS Engine** | Detects and handles 5 major ATS platforms automatically |
| **Smart Form Detection** | Identifies form fields using multi-selector strategies with fallbacks |
| **Cover Letter Generator** | Creates tailored cover letters per job posting |
| **SPA-Aware Navigation** | Intelligent wait strategies for React/Angular single-page apps |
| **Post-Submit Verification** | Confirms successful submissions, retries on failure |
| **Duplicate Tracking** | Logs applied URLs to never re-apply to the same job |
| **Job Search Engine** | Scrapes RSS feeds, job boards & ATS APIs for matching listings |
| **HTML Reports** | Generates detailed visual reports of found jobs & applications |
| **Email Notifications** | Sends results via Gmail with HTML formatting |
| **Resume Upload** | Handles file upload fields across all platforms |

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                   AUTO JOB APPLICANT                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. DISCOVER    Scrape job boards, RSS feeds, ATS APIs  │
│       │                                                 │
│       ▼                                                 │
│  2. FILTER      Match by keywords, location, recency    │
│       │                                                 │
│       ▼                                                 │
│  3. DETECT      Identify ATS platform (GH/Lever/etc)    │
│       │                                                 │
│       ▼                                                 │
│  4. FILL        Smart form filling with multi-strategy  │
│       │         selectors and fallback chains            │
│       ▼                                                 │
│  5. GENERATE    Create tailored cover letter for role    │
│       │                                                 │
│       ▼                                                 │
│  6. SUBMIT      Click submit + post-submit verification │
│       │                                                 │
│       ▼                                                 │
│  7. TRACK       Log URL, update report, send email      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Supported ATS Platforms

Each platform has a dedicated handler with optimized strategies:

| Platform | Detection | Form Fill | Submit | Special Features |
|:--------:|:---------:|:---------:|:------:|:----------------:|
| **Greenhouse** | iframe + URL | Multi-strategy | Pre-submit validation | iframe detection, field mapping |
| **Lever** | URL pattern | Multi-selector | Double fallback | Dynamic field detection |
| **Workable** | URL + DOM | Triple fallback | SPA-aware submit | React SPA handling |
| **Ashby** | URL pattern | SPA wait + fill | Enhanced submit | Single-page app support |
| **SmartRecruiters** | URL + DOM | Multi-selector | Double fallback | Complex form handling |

---

## Tech Stack

| Technology | Purpose |
|:----------:|:-------:|
| **Python 3.10+** | Core language |
| **Selenium WebDriver** | Browser automation (Edge/Chrome) |
| **BeautifulSoup4** | HTML parsing & scraping |
| **Requests** | HTTP client for API calls |
| **feedparser** | RSS/Atom feed parsing |
| **smtplib** | Email notifications |

---

## Project Structure

```
auto-job-applicant/
│
├── src/
│   ├── auto_applicant.py       # Main bot — search, fill & apply (~4,800 lines)
│   ├── job_searcher.py         # Job search engine + HTML reports (~1,300 lines)
│   └── fresh_listings.py       # Curated active listings from ATS platforms
│
├── tools/
│   ├── greenhouse_scanner.py   # Greenhouse API scanner — finds live jobs
│   └── pdf_generator.py        # HTML → PDF resume converter (Edge CDP)
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Setup

### 1. Clone

```bash
git clone https://github.com/spirit122/auto-job-applicant.git
cd auto-job-applicant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your personal data:

```env
APPLICANT_FULL_NAME=John Doe
APPLICANT_EMAIL=john@example.com
APPLICANT_PHONE=+1234567890
APPLICANT_CITY=New York
APPLICANT_TITLE=Backend Developer
APPLICANT_CV_PATH=./my_resume.pdf
```

### 4. Gmail notifications (optional)

1. Enable [2-Step Verification](https://myaccount.google.com/security)
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Add to `.env`:
   ```env
   GMAIL_APP_PASSWORD=your-16-char-password
   ```

### 5. Place your resume

Drop your CV/Resume PDF files in the project directory.

---

## Usage

### Search for jobs

```bash
python src/job_searcher.py
```

Scrapes multiple sources and generates `resultados_trabajos.html` — open it in your browser to review found listings.

### Auto-apply

```bash
python src/auto_applicant.py
```

Launches a browser, navigates to each listing, detects the ATS, fills forms, generates cover letters, and submits. Progress is logged in real-time.

### Scan Greenhouse API

```bash
python tools/greenhouse_scanner.py
```

Finds active job listings directly from Greenhouse's public API across 30+ companies.

### Output

| File | Description |
|------|-------------|
| `resultados_trabajos.html` | Visual report of found job listings |
| `reporte_postulaciones.html` | Report of submitted applications |
| `urls_aplicadas.txt` | Log of applied URLs (prevents duplicates) |
| `auto_applicant.log` | Detailed execution log |

---

## Configuration

All configuration is done via environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Required | Description |
|----------|:--------:|-------------|
| `APPLICANT_FULL_NAME` | Yes | Your full name |
| `APPLICANT_EMAIL` | Yes | Email for applications |
| `APPLICANT_PHONE` | Yes | Phone number |
| `APPLICANT_CITY` | Yes | Your city |
| `APPLICANT_TITLE` | Yes | Professional title |
| `APPLICANT_CV_PATH` | Yes | Path to your resume PDF |
| `GMAIL_APP_PASSWORD` | No | For email notifications |

---

## Disclaimer

This tool is for educational and personal use. Always review applications before bulk-submitting. Respect each platform's terms of service. The author is not responsible for any misuse.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by [Ricardo Sepúlveda](https://github.com/spirit122)**

</div>
