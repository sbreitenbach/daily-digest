# Daily Digest Script

This Python script generates a personalized daily digest email. It fetches information from various sources, including:

- **Financial Markets:** Fetches data from Finnhub for specified assets.
- **Weather:** Gets the local forecast from the National Weather Service.
- **Wikipedia:** Retrieves the "Article of the Day."
- **xkcd:** Grabs the latest comic.
- **NASA:** Fetches the Image of the Day.
- **Reddit:** Pulls top posts from specified subreddits.
- **RSS Feeds:** Aggregates news from your favorite sources.
- **AI Summary:** Uses the Gemini API to summarize the text-based news content. (Note: This script uses the `requests` library to interact with the Gemini REST API, so the `google-generativeai` package is not required.)

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
    -   Create a `config.py` file by copying the `sample_config.py`:
        ```bash
        cp sample_config.py config.py
        ```
    -   Open `config.py` and fill in your API keys, email settings, and feed URLs.

## Usage

Run the script from your terminal:

```bash
python main.py
```

The script will generate and send the daily digest email to the configured recipient. You can set this up as a cron job or scheduled task to run automatically each day.
