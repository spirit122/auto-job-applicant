# Auto Job Applicant

Automated job search and application bot built with Python and Selenium. Scrapes job listings from multiple ATS platforms (Greenhouse, Lever, Workable, Ashby, SmartRecruiters), generates tailored cover letters, and submits applications automatically.

## Features

- **Multi-ATS Support**: Greenhouse, Lever, Workable, Ashby, SmartRecruiters
- **Smart Form Filling**: Detects and fills application forms automatically using Selenium
- **Cover Letter Generation**: Creates customized cover letters per job posting
- **Job Search Engine**: Scrapes multiple sources for relevant job listings
- **SPA Handling**: Intelligent wait strategies for single-page applications
- **Post-Submit Verification**: Confirms successful application submissions
- **Email Notifications**: Sends HTML reports via Gmail
- **Duplicate Detection**: Tracks applied URLs to avoid re-applying
- **HTML Reports**: Generates detailed reports of found jobs and applications

## Tech Stack

- **Python 3.10+**
- **Selenium WebDriver** (Edge/Chrome)
- **BeautifulSoup4** - HTML parsing
- **Requests** - HTTP client
- **feedparser** - RSS feed parsing
- **smtplib** - Email notifications

## Project Structure

```
auto-job-applicant/
├── auto_postulador.py    # Main bot - searches & applies to jobs (~4,800 lines)
├── buscador_trabajos.py  # Job search engine with HTML reports (~1,300 lines)
├── ofertas_frescas.py    # Curated job listings from ATS platforms
├── .env.example          # Environment variables template
├── .gitignore
└── README.md
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/spirit122/auto-job-applicant.git
   cd auto-job-applicant
   ```

2. **Install dependencies**
   ```bash
   pip install requests beautifulsoup4 selenium feedparser lxml
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your personal data
   ```

4. **Set up Gmail App Password** (for email notifications)
   - Enable 2-Step Verification at https://myaccount.google.com/security
   - Generate an App Password at https://myaccount.google.com/apppasswords
   - Add it to your `.env` file

5. **Place your CV/Resume** PDFs in the project directory

## Usage

### Search for jobs
```bash
python buscador_trabajos.py
```
Generates `resultados_trabajos.html` with found listings.

### Auto-apply to jobs
```bash
python auto_postulador.py
```
Opens a browser, fills forms, and submits applications automatically.

## Supported ATS Platforms

| Platform | Features |
|----------|----------|
| Greenhouse | iframe detection, multi-strategy filling, pre-submit validation |
| Lever | Multi-selector support, double fallback |
| Workable | SPA wait, triple fallback strategies |
| Ashby | SPA-aware, enhanced submit |
| SmartRecruiters | Multi-selector, double fallback |

## How It Works

1. **Job Discovery**: Scrapes job boards, RSS feeds, and ATS APIs for matching positions
2. **Filtering**: Filters by keywords, location, and recency
3. **Form Detection**: Identifies the ATS platform and form structure
4. **Smart Filling**: Fills name, email, phone, uploads CV, writes cover letter
5. **Submission**: Clicks submit with verification and retry logic
6. **Tracking**: Logs applied URLs to prevent duplicates
7. **Reporting**: Generates HTML reports and sends email notifications

## License

MIT

## Author

Built by [spirit122](https://github.com/spirit122)
