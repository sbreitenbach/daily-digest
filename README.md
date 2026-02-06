# Daily Digest Script

This Python script generates a personalized daily digest email. This code was written with the assitance of AI. It fetches information from various sources, including:

- **Financial Markets:** Fetches data from Finnhub for specified assets.
- **Weather:** Gets the local forecast from the National Weather Service.
- **Wikipedia:** Retrieves the "Article of the Day."
- **xkcd:** Grabs the latest comic.
- **NASA:** Fetches the Image of the Day.
- **Reddit:** Pulls top posts from specified subreddits.
- **RSS Feeds:** Aggregates news from your favorite sources.

## AI Summary
This script uses the Google Gemini API to summarize the text-based news content. Gemini has a generous free tier and large context window. (Note: This script uses the `requests` library to interact with the Gemini REST API, so the `google-generativeai` package is not required.)

## Personalized Feedback

The digest learns from your preferences over time! Simply reply to any digest email with feedback like:
- "Show more tech news, less sports"
- "I prefer shorter summaries"
- "Prioritize financial and science stories"

The script checks for replies via IMAP, uses AI to extract your preferences, and stores them in `feedback_context.md`. Future digests will prioritize content based on your feedback.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the script:**
    -   Open `config.py` and fill in your API keys, email settings (SMTP and IMAP), and feed URLs.

## Usage

Run the script from your terminal:

```bash
python main.py
```

The script will generate and send the daily digest email to the configured recipient. You can set this up as a cron job or scheduled task to run automatically each day.
