# Search Agent Project

A web-based search agent that combines LLM capabilities with web search and content extraction tools to generate comprehensive reports.

## Features

- Web search using SerpAPI
- Content extraction from HTML and PDF sources using trafilatura/readability
- Report generation using GROQ LLM
- Search history tracking with SQLite database
- Web interface for viewing search results and past reports

## Tech Stack

- **Backend**: FastAPI, SQLModel, SQLite
- **Frontend**: HTML, CSS, JavaScript
- **LLM**: GROQ (llama-3.3-70b-versatile)
- **Search**: SerpAPI
- **Content Extraction**: trafilatura

## Setup

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
SERPAPI_API_KEY=your_serp_api_key
GROQ_API_KEY=your_groq_api_key
```

## Running the Application

1. Start the backend server:
```bash
uvicorn backend.app:app --reload --port 8000
```

2. Start the frontend server:
```bash
cd frontend
python -m http.server 8080
```

3. Visit `http://localhost:8080` in your browser

## API Endpoints

- `GET /api/v1/search?query={query}` - Perform a search
- `GET /api/v1/history` - Get search history
- `GET /api/v1/history/{search_id}` - Get specific search report
- `GET /health` - Check API health

## License

MIT License - feel free to use this project for your own purposes.
