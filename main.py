import requests
import feedparser
import smtplib
import time
import logging
import json
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

# --- Set up Logging (Dual-Output Version) ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('digest.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_formatter = logging.Formatter('%(message)s')
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


# --- Import settings from config.py ---
try:
    import sample_config
except ImportError:
    logging.error("config.py not found. Please create it and add your API keys and settings.")
    exit()

# Define a single, descriptive User-Agent for all requests.
USER_AGENT = "DailyDigestBot/1.0"

def get_financial_data(api_key, assets):
    """Fetches financial data from the Finnhub API."""
    if not api_key or not assets:
        return ""
    
    logging.info("Fetching financial data...")
    html = "<h1>Market Report</h1>"
    
    for name, symbol in assets.items():
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            price = data.get('c', 0)
            change = data.get('d', 0)
            pct_change = data.get('dp', 0)
            
            color = "green" if change >= 0 else "red"
            sign = "+" if change >= 0 else ""

            html += f"""
                <p>
                    <b>{name}:</b> ${price:,.2f} 
                    <span style="color:{color};">({sign}{change:,.2f} / {sign}{pct_change:.2f}%)</span>
                </p>
            """
        except Exception:
            logging.exception(f"Could not fetch data for financial asset: {name}")

    return html + "<hr>"

def get_weather_forecast(url):
    """Fetches the weather forecast from the National Weather Service (NWS) API."""
    if not url:
        return ""
    
    headers = {'User-Agent': USER_AGENT}
    
    logging.info("Fetching weather forecast from NWS...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        weather_data = response.json()
        periods = weather_data.get('properties', {}).get('periods', [])
        
        if not periods:
            logging.warning("Weather data received, but no forecast periods found.")
            return ""

        logging.debug(f"Found {len(periods)} weather periods.")
        forecast_html = "<h1>Weather Report</h1>"
        for period in periods[:2]:
            forecast_html += f"""
                <h3>{period['name']}</h3>
                <p><b>{period['temperature']}°{period['temperatureUnit']}</b> - {period['shortForecast']}</p>
                <p>{period['detailedForecast']}</p>
            """
        return forecast_html + "<hr>"

    except requests.exceptions.RequestException:
        logging.exception("Error fetching weather data")
        return ""

def fetch_summary_via_api(title):
    """Fetches Wikipedia article details using the REST API."""
    logging.debug(f"Fetching Wikipedia API summary for: {title}")
    encoded_title = quote(title, safe='')
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    headers = {'User-Agent': USER_AGENT}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        return {
            "intro": data.get("extract") or "",
            "image_url": (data.get("thumbnail") or {}).get("source"),
        }
    except Exception:
        logging.exception(f"Wikipedia REST API summary fetch failed for title: {title}")
        return None

def get_wikipedia_article_of_the_day():
    """Fetches Wikipedia's featured article by scraping the main page, then using the API."""
    logging.info("Fetching Wikipedia Article of the Day...")
    try:
        main_page_url = "https://en.wikipedia.org/wiki/Main_Page"
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(main_page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tfa_div = soup.find('div', id='mp-tfa')
        article_link_tag = tfa_div.find('b').find('a')
        article_title = article_link_tag.get_text()
        article_url = f"https://en.wikipedia.org{article_link_tag['href']}"
        
        api_data = fetch_summary_via_api(article_title)
        
        if not api_data:
            return None

        return {
            "title": article_title,
            "url": article_url,
            "intro": api_data["intro"],
            "image_url": api_data["image_url"]
        }

    except Exception:
        logging.exception("Could not find the featured article on Wikipedia's Main Page.")
        return None

def get_latest_xkcd():
    """Fetches the latest comic from xkcd if it's new."""
    logging.info("Fetching latest xkcd comic...")
    url = "https://xkcd.com/atom.xml"
    feed = feedparser.parse(url, agent=USER_AGENT)
    
    if feed.status != 200 or not feed.entries:
        logging.warning(f"Could not fetch or parse xkcd feed. Status: {feed.status}")
        return None

    latest_comic = feed.entries[0]
    pub_time_struct = latest_comic.updated_parsed
    pub_date_utc = datetime.fromtimestamp(time.mktime(pub_time_struct), tz=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    
    age = now_utc - pub_date_utc
    logging.debug(f"Current xkcd comic is {age.total_seconds() / 3600:.2f} hours old.")
    
    if age > timedelta(hours=30):
        logging.info("xkcd comic is not new. Skipping.")
        return None
    
    logging.info("New xkcd comic found!")
    summary_html = latest_comic.summary
    soup = BeautifulSoup(summary_html, 'html.parser')
    img_tag = soup.find('img')

    if not img_tag:
        logging.warning("Could not find image tag in xkcd feed item.")
        return None
        
    return {"title": latest_comic.title, "image_url": img_tag['src'], "alt_text": img_tag['title']}

def get_nasa_image_of_the_day():
    """Fetches the latest image and description from the NASA IOTD feed."""
    logging.info("Fetching NASA Image of the Day...")
    url = "https://www.nasa.gov/feeds/iotd-feed/"
    
    feed = feedparser.parse(url, agent=USER_AGENT)
    if feed.status != 200 or not feed.entries:
        logging.warning(f"Could not fetch NASA feed. Status: {feed.status}")
        return None
    latest_item = feed.entries[0]
    image_url = latest_item.enclosures[0].href if latest_item.enclosures else None
    if not image_url:
        logging.warning("Could not find image URL in the NASA feed item.")
        return None
    return {"title": latest_item.title, "description": latest_item.description, "image_url": image_url}

def get_reddit_json_content(feeds):
    """Fetches headlines and identifies post type (text vs. link/image) from Reddit."""
    all_content = ""
    headers = {'User-Agent': USER_AGENT}
    for category, url in feeds.items():
        logging.info(f"Fetching JSON for {category}...")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            all_content += f"<h2>{category}</h2>\n"
            posts = data['data']['children']
            logging.debug(f"Found {len(posts)} posts in {category} feed.")
            for post in posts[:5]:
                post_data = post['data']
                title = post_data['title']
                link = f"https://www.reddit.com{post_data['permalink']}"
                
                if post_data.get('is_self', False):
                    post_type = "Text Post"
                    body = post_data.get('selftext', '')
                else:
                    post_type = "Link/Image Post"
                    body = "No summary available."
                
                all_content += f"- Title: {title} ({link})\n  Type: {post_type}\n  Content: {body}\n"
            all_content += "\n"
        except Exception:
            logging.exception(f"Error fetching JSON from {url}")
    return all_content

def get_rss_content(feeds):
    """Fetches headlines and summaries/descriptions from a dictionary of standard RSS feeds."""
    all_content = ""
    for category, url in feeds.items():
        logging.info(f"Fetching RSS feed for {category}...")
        feed = feedparser.parse(url, agent=USER_AGENT)
        if feed.status != 200:
            logging.warning(f"Error fetching RSS feed {url}. Status: {feed.status}")
            continue
        logging.debug(f"Found {len(feed.entries)} entries in {category} feed.")
        all_content += f"<h2>{category}</h2>\n"
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            content_blurb = entry.get('summary', entry.get('description', ''))
            all_content += f"- Title: {title} ({link})\n  Content: {content_blurb}\n"
        all_content += "\n"
    return all_content

def get_ai_summary(content_to_summarize):
    """Sends content to Gemini AI for summarization using a direct requests call.
    Usees the REST API endpoint to interact with the Gemini model. 
    Not using the Google client library due to issues getting that working on some hardware."""
    logging.info("Sending content to Gemini for summarization via requests...")
    
    api_key = config.GEMINI_API_KEY
    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}

    prompt = f"""
    You are my personalized news digest assistant. Your task is to review a list of headlines and their accompanying content, then create a clean and insightful HTML email digest.

    Instructions:
    1.  Review the headlines and content for each category provided below. If the same news story appears in multiple categories, please only include it once.
    2.  For each category, select the 3-4 most interesting or important stories.
    3.  For each selected story, write a single, engaging summary sentence. This summary MUST NOT simply rephrase the headline. It should provide a unique insight from the provided content.
    4.  IMPORTANT EXCEPTION: If an item is marked "Type: Link/Image Post", you MUST NOT write a summary for it. Just list the title.
    5.  Format your entire response in simple, clean HTML. Use <h2> for category titles and an unordered list (<ul> with <li>) for the stories. Each list item must contain the hyperlinked title. If you wrote a summary, add it in a <p> tag with smaller, italicized text.
    6.  Do not include anything in your response except the final HTp-=ML code. Start with <h2> and end with </ul>.

    Here is the list of headlines and content to analyze:
    {content_to_summarize}
    """

    body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        logging.debug("Prompting Gemini model via REST API...")
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
        
        response_data = response.json()
        generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        logging.info("Successfully received summary from Gemini.")
        return generated_text
    except Exception:
        logging.exception("Error communicating with Gemini API via requests")
        return f"<h2>Error</h2><p>Could not generate AI summary. See digest.log for details.</p>"

def send_email(html_content):
    """Connects to an SMTP server and sends the email."""
    logging.info("Preparing to send email...")
    msg = MIMEMultipart('alternative')
    today_date = datetime.now().strftime("%B %d, %Y")
    msg['Subject'] = f"Your Daily Digest - {today_date}"
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = config.EMAIL_RECEIVER
    msg.attach(MIMEText(html_content, 'html'))
    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECEIVER, msg.as_string())
        logging.info("Email sent successfully!")
    except Exception:
        logging.exception("Error sending email")

def main():
    """Main function to run the digest creation process."""
    logging.info("--- Starting the daily digest script ---")
    
    # --- STEP 1: Gather all content ---
    financial_html = ""
    if hasattr(config, 'FINNHUB_API_KEY') and config.FINNHUB_API_KEY and hasattr(config, 'FINANCIAL_ASSETS'):
        financial_html = get_financial_data(config.FINNHUB_API_KEY, config.FINANCIAL_ASSETS)
    
    weather_html = get_weather_forecast(config.NWS_FORECAST_URL)
    nasa_data = get_nasa_image_of_the_day()
    wiki_data = get_wikipedia_article_of_the_day()
    xkcd_data = get_latest_xkcd()
    reddit_content = get_reddit_json_content(config.REDDIT_JSON_FEEDS)
    rss_content = get_rss_content(config.GENERAL_RSS_FEEDS)
    
    # --- STEP 2: Get the AI summary for the text news ---
    full_content_for_ai = reddit_content + rss_content
    ai_html_body = ""
    if full_content_for_ai.strip():
        ai_html_body = get_ai_summary(full_content_for_ai)
    else:
        logging.warning("No text-based news content gathered to send to AI.")

    # --- STEP 3: Build the final email body ---
    final_html_content = financial_html + weather_html

    if nasa_data:
        final_html_content += f"""
            <h1>Image of the Day: {nasa_data['title']}</h1>
            <p><img src="{nasa_data['image_url']}" alt="{nasa_data['title']}" style="max-width:100%; height:auto;" /></p>
            <p>{nasa_data['description']}</p>
        """
    
    if wiki_data:
        final_html_content += f"""
            <hr><h1>Wikipedia Article of the Day</h1>
            <h2><a href="{wiki_data['url']}">{wiki_data['title']}</a></h2>
        """
        if wiki_data.get('image_url'):
            final_html_content += f"""
                <p><img src="{wiki_data['image_url']}" alt="{wiki_data['title']}" style="max-width:100%; height:auto;" /></p>
            """
        final_html_content += f"<p>{wiki_data['intro']}</p>"

    if ai_html_body:
        final_html_content += f"<hr><h1>Your News Digest</h1>{ai_html_body}"

    if xkcd_data:
        final_html_content += f"""
            <hr>
            <h1>Daily Comic: xkcd</h1>
            <h2>{xkcd_data['title']}</h2>
            <p><img src="{xkcd_data['image_url']}" alt="{xkcd_data['title']}" style="max-width:100%; height:auto;" /></p>
            <p><i>{xkcd_data['alt_text']}</i></p>
        """

    # --- STEP 4: Send the email ---
    if not final_html_content.strip():
        logging.warning("No content at all was generated. Exiting without sending email.")
        return

    send_email(final_html_content)
    
    logging.info("--- Digest script finished ---")

if __name__ == "__main__":
    main()
