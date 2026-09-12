# 🏛️ Alexandria • AI Study Notes & Bookshelf Studio

An autonomous academic AI Agent with an **animated bookshelf & library study room UI/UX**. Enter any academic topic or concept to initiate live web research via the **Serper Google Search API**, article content scraping, and human-style pedagogical synthesis via **OpenRouter LLMs**. 

Each generated topic is placed on your **interactive animated bookshelf**, where you can read structured notes and download publication-quality **PDF Study Guides**, **PowerPoint Slide Decks (PPTX)**, and **Word Documents (DOCX)** with one click.

---

## 🌟 Key Features

1. **Animated Library & Bookshelf UI/UX**:
   - Atmospheric study room aesthetic with ambient lighting and floating dust motes.
   - Wooden bookshelf cabinet where each generated guide appears as an embossed leather book.
   - 3D interactive book spines: hover to tilt and slide out, click to read or re-download anytime.
2. **Autonomous Academic Research**:
   - **Serper API**: Real-time Google Search for educational notes, academic tutorials, and study summaries.
   - **Web Scraper**: Extracts clean, readable text from educational sites using `trafilatura` and `BeautifulSoup4`.
3. **Budget-Protected AI Synthesis**:
   - Synthesizes human-friendly notes: Core Definitions, Step-by-Step Mechanisms, Real-World Analogies, Formulas/Laws, Common Exam Traps, and Self-Check Quizzes.
   - Bounded token management to work seamlessly with OpenRouter free and paid tiers.
4. **Multi-Format Compilers & Instant Downloads**:
   - 📕 **PDF Study Guide**: Formatted with headers, callout boxes, and running footers with page numbers.
   - 📊 **PowerPoint Presentation (PPTX)**: 16:9 widescreen slide deck for lectures and revisions.
   - 📝 **Word Document (DOCX)**: Clean editable document with structured headings.
5. **No Phone / WhatsApp Needed**:
   - 100% web-based. Runs locally on your machine at `http://localhost:8000`.

---

## 🚀 How to Run

### 1. Configure API Keys
Ensure your `.env` has your OpenRouter and Serper API keys:
```ini
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=openai/gpt-4o-mini
PORT=8000
```

### 2. Start the Server
```bash
cd /home/talha/Desktop/whatsaap_student
.venv/bin/python3 server.py
```

### 3. Open in Your Web Browser
Open your browser and navigate to:
```
http://localhost:8000
```

---

## 📁 Project Structure

```
whatsaap_student/
├── .env                       # API keys (OpenRouter, Serper)
├── requirements.txt           # Python dependencies
├── config.py                  # App configuration
├── server.py                  # FastAPI server & static file host
├── library_history.json       # Persisted shelf books and study packages
├── generated_notes/           # Compiled PDFs, PPTXs, and DOCXs
├── static/
│   ├── index.html             # Studio UI with animated bookshelf
│   ├── style.css              # Custom CSS animations, textures & lighting
│   └── app.js                 # Ambient particles, shelf rack & note reader
├── agent/
│   ├── orchestrator.py        # Central research & synthesis coordinator
│   ├── intent.py              # Query intent classifier
│   └── prompts.py             # Human-style pedagogical prompt templates
├── search/
│   ├── serper.py              # Serper.dev Google Search client
│   └── scraper.py             # Educational web scraper
└── generators/
    ├── pdf_gen.py             # ReportLab PDF study guide generator
    ├── docx_gen.py            # Word document generator
    └── pptx_gen.py            # PowerPoint presentation generator
```
