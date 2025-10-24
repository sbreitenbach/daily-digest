import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
import main

def test_get_financial_data(mocker):
    # Mock the requests.get call
    mock_response = Mock()
    mock_response.json.return_value = {
        'c': 150.00,
        'd': 5.00,
        'dp': 3.4483
    }
    mock_response.raise_for_status.return_value = None
    mocker.patch('requests.get', return_value=mock_response)

    # Call the function
    api_key = 'test_api_key'
    assets = {'Test Asset': 'TEST'}
    result = main.get_financial_data(api_key, assets)

    # Assert the result
    assert '<h1>Market Report</h1>' in result
    assert '<b>Test Asset:</b> $150.00' in result
    assert '<span style="color:green;">(+5.00 / +3.45%)</span>' in result

def test_get_weather_forecast(mocker):
    # Mock the requests.get call
    mock_response = Mock()
    mock_response.json.return_value = {
        'properties': {
            'periods': [
                {
                    'name': 'Today',
                    'temperature': 65,
                    'temperatureUnit': 'F',
                    'shortForecast': 'Sunny',
                    'detailedForecast': 'Sunny skies throughout the day.'
                },
                {
                    'name': 'Tonight',
                    'temperature': 50,
                    'temperatureUnit': 'F',
                    'shortForecast': 'Clear',
                    'detailedForecast': 'Clear skies throughout the night.'
                }
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    mocker.patch('requests.get', return_value=mock_response)

    # Call the function
    url = 'http://test-weather-url'
    result = main.get_weather_forecast(url)

    # Assert the result
    assert '<h1>Weather Report</h1>' in result
    assert '<h3>Today</h3>' in result
    assert '<p><b>65°F</b> - Sunny</p>' in result
    assert '<p>Sunny skies throughout the day.</p>' in result
    assert '<h3>Tonight</h3>' in result
    assert '<p><b>50°F</b> - Clear</p>' in result
    assert '<p>Clear skies throughout the night.</p>' in result

def test_get_wikipedia_article_of_the_day(mocker):
    # Mock the requests.get call for the main page
    mock_main_page_response = Mock()
    mock_main_page_response.text = '''
        <div id="mp-tfa">
            <b><a href="/wiki/Test_Article" title="Test Article">Test Article</a></b>
        </div>
    '''
    mock_main_page_response.raise_for_status.return_value = None

    # Mock the requests.get call for the API summary
    mock_api_response = Mock()
    mock_api_response.json.return_value = {
        'extract': 'This is a test article.',
        'thumbnail': {
            'source': 'http://test-image-url'
        }
    }
    mock_api_response.raise_for_status.return_value = None

    mocker.patch('requests.get', side_effect=[mock_main_page_response, mock_api_response])

    # Call the function
    result = main.get_wikipedia_article_of_the_day()

    # Assert the result
    assert result is not None
    assert result['title'] == 'Test Article'
    assert result['url'] == 'https://en.wikipedia.org/wiki/Test_Article'
    assert result['intro'] == 'This is a test article.'
    assert result['image_url'] == 'http://test-image-url'

def test_get_latest_xkcd(mocker):
    # Mock feedparser.parse
    mock_feed = Mock()
    mock_feed.status = 200
    mock_entry = Mock()
    mock_entry.title = 'Test Comic'
    mock_entry.summary = '<img src="http://test-comic-url" title="Test alt text" />'
    mock_entry.updated_parsed = (2023, 10, 27, 0, 0, 0, 4, 300, 0) # A fixed time
    mock_feed.entries = [mock_entry]
    mocker.patch('feedparser.parse', return_value=mock_feed)

    # Subclass datetime to override now()
    class MockedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            # Return a fixed time that is 1 hour after the comic's publish time
            return datetime(2023, 10, 27, 1, 0, 0, tzinfo=timezone.utc)

    mocker.patch('main.datetime', MockedDateTime)

    # Call the function
    result = main.get_latest_xkcd()

    # Assert the result
    assert result is not None
    assert result['title'] == 'Test Comic'
    assert result['image_url'] == 'http://test-comic-url'
    assert result['alt_text'] == 'Test alt text'

def test_get_nasa_image_of_the_day(mocker):
    # Mock feedparser.parse
    mock_feed = Mock()
    mock_feed.status = 200
    mock_entry = Mock()
    mock_entry.title = 'Test NASA Image'
    mock_entry.description = 'This is a test description.'
    mock_enclosure = Mock()
    mock_enclosure.href = 'http://test-nasa-image-url'
    mock_entry.enclosures = [mock_enclosure]
    mock_feed.entries = [mock_entry]
    mocker.patch('feedparser.parse', return_value=mock_feed)

    # Call the function
    result = main.get_nasa_image_of_the_day()

    # Assert the result
    assert result is not None
    assert result['title'] == 'Test NASA Image'
    assert result['description'] == 'This is a test description.'
    assert result['image_url'] == 'http://test-nasa-image-url'

def test_get_reddit_json_content(mocker):
    # Mock requests.get
    mock_response = Mock()
    mock_response.json.return_value = {
        'data': {
            'children': [
                {
                    'data': {
                        'title': 'Test Reddit Post',
                        'permalink': '/r/test/comments/123/test_reddit_post/',
                        'is_self': True,
                        'selftext': 'This is a test text post.'
                    }
                }
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    mocker.patch('requests.get', return_value=mock_response)

    # Call the function
    feeds = {'Test Feed': 'http://test-reddit-url'}
    result = main.get_reddit_json_content(feeds)

    # Assert the result
    assert '<h2>Test Feed</h2>' in result
    assert '- Title: Test Reddit Post' in result
    assert 'Type: Text Post' in result
    assert 'Content: This is a test text post.' in result

def test_get_rss_content(mocker):
    # Mock feedparser.parse
    mock_feed = Mock()
    mock_feed.status = 200
    mock_entry = Mock()
    mock_entry.title = 'Test RSS Post'
    mock_entry.link = 'http://test-rss-link'
    mock_entry.get.side_effect = lambda key, default='': {
        'summary': 'This is a test RSS summary.',
    }.get(key, '')
    mock_feed.entries = [mock_entry]
    mocker.patch('feedparser.parse', return_value=mock_feed)

    # Call the function
    feeds = {'Test Feed': 'http://test-rss-url'}
    result = main.get_rss_content(feeds)

    # Assert the result
    assert '<h2>Test Feed</h2>' in result
    assert '- Title: Test RSS Post' in result
    assert 'Content: This is a test RSS summary.' in result

def test_get_ai_summary(mocker):
    # Mock requests.post
    mock_response = Mock()
    mock_response.json.return_value = {
        'candidates': [
            {
                'content': {
                    'parts': [
                        {
                            'text': 'This is a test AI summary.'
                        }
                    ]
                }
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mocker.patch('requests.post', return_value=mock_response)

    # Call the function
    content = 'This is content to be summarized.'
    result = main.get_ai_summary(content)

    # Assert the result
    assert result == 'This is a test AI summary.'

def test_send_email(mocker):
    # Mock smtplib.SMTP
    mock_smtp_class = mocker.patch('smtplib.SMTP')
    mock_server = mock_smtp_class.return_value.__enter__.return_value

    # Call the function
    html_content = '<h1>Test Email</h1>'
    main.send_email(html_content)

    # Assert that the SMTP methods were called
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once()
    mock_server.sendmail.assert_called_once()
