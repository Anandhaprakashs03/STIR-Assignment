import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import uuid
from pymongo import MongoClient
from flask import Flask, render_template_string, jsonify
import logging
import os
from dotenv import load_dotenv

load_dotenv()
print(load_dotenv)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['twitter_trends']
collection = db['trends']
os.environ["USERNAME"] = "AnandhaPrakash"
# ProxyMesh credentials
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

print(f"USERNAME from .env: {os.getenv('USERNAME')}")

# Function to fetch ProxyMesh proxy
def get_proxy():
    proxy_url = f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
    print(proxy_url)
    logger.info(f"Using proxy: {proxy_url}")
    return proxy_url


# Fetch trending topics with rotating proxies
def fetch_trending_topics():
    proxy_ip = None
    driver = None
    try:
        # Use ProxyMesh to rotate IP with each request
        proxy_url = f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
        print(proxy_url)

        # Add X-ProxyMesh-Country header for India region
        headers = {
            'X-ProxyMesh-Country': 'IN'
        }

        # Make a request to ProxyMesh to get a new proxy IP for each request
        ip_response = requests.get(f'https://httpbin.org/ip', proxies={'http': proxy_url, 'https': proxy_url}, headers=headers)
        print(ip_response.json())
        if ip_response.status_code == 200:
            proxy_ip = ip_response.json().get('origin', 'Unknown IP')
            logger.info(f"Proxy IP: {proxy_ip}")
            print(f"Using proxy IP: {proxy_ip}")
        else:
            logger.error(f"Failed to fetch proxy IP: {ip_response.text}")
            print(f"Failed to get IP with proxy: {ip_response.status_code}")

        # Selenium WebDriver setup with proxy
        service = Service('D:/chromedriver-win64/chromedriver-win64/chromedriver.exe')
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--lang=en')
        # chrome_options.add_argument(f'--proxy-server={proxy_url}')
        chrome_options.add_argument('--disable-gpu')  # Disables GPU hardware acceleration

        # Initialize WebDriver with proxy
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get('https://twitter.com/explore/tabs/trending')
        logger.info("Navigating to Twitter Trending page")
        
        # Wait for trending topics to load
        wait = WebDriverWait(driver, 300)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='trend']"))
        )
        

        trending_topics = []
        
        # Find all trend containers
        trend_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='trend']")
        
        for element in trend_elements:
            try:
                # Find all spans within the trend element
                spans = element.find_elements(By.TAG_NAME, "span")
                
                # Get the trend text (usually in the first non-empty span that doesn't contain metadata)
                trend_text = None
                for span in spans:
                    text = span.text.strip()
                    if text and not any(text.startswith(prefix) for prefix in ['#', '·', 'Trending', 'K Tweets', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']):
                        trend_text = text
                        break
                
                if trend_text:
                    trending_topics.append(trend_text)
                    logger.info(f"Found trend: {trend_text}")
            
            except Exception as e:
                logger.warning(f"Error processing trend element: {str(e)}")
                continue
        
        if not trending_topics:
            raise Exception("No trending topics found")
            
        trending_topics = list(dict.fromkeys(trending_topics))
        
        # Save to MongoDB
        record = {
            "_id": str(uuid.uuid4()),
            "trends": trending_topics,
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(record)
        logger.info(f"Successfully saved {len(trending_topics)} trends")
        
        return {
            "success": True,
            "trends": trending_topics,
            "record_id": record["_id"],
            "timestamp": record["timestamp"],
            "proxy_ip": proxy_ip  # Include proxy IP in the response
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if driver:
            driver.save_screenshot('error.png')  # Save a screenshot if error occurs
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            driver.quit()


@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>Twitter Trends</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { padding: 10px 20px; background: #1DA1F2; color: white; 
                  border: none; border-radius: 4px; cursor: pointer; }
            .error { color: #dc3545; }
            .trend-item { padding: 15px; background: #f8f9fa; margin: 5px 0; }
        </style>
    </head><body>
        <div class="container">
            <h1>Twitter Trends Scraper</h1>
            <a href="/run-script" class="btn">Fetch Trends</a>
        </div>
    </body></html>
    ''')


@app.route('/run-script')
def run_script():
    result = fetch_trending_topics()
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>Results</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { padding: 10px 20px; background: #1DA1F2; color: white; text-decoration: none; }
            .error { color: #dc3545; }
            .trend-item { padding: 15px; background: #f8f9fa; margin: 5px 0; }
        </style>
    </head><body>
        <div class="container">
            {% if result.success %}
                <h2>Current Trends</h2>
                {% for trend in result.trends %}
                    <div class="trend-item">{{ trend }}</div>
                {% endfor %}
                <p>Record ID: {{ result.record_id }}</p>
                <p>Fetched: {{ result.timestamp }}</p>
                <p><strong>Proxy IP: </strong>{{ result.proxy_ip }}</p>  <!-- Display the proxy IP -->
            {% else %}
                <h2 class="error">Error</h2>
                <p class="error">{{ result.error }}</p>
            {% endif %}
            <a href="/run-script" class="btn">Fetch Again</a>
            <a href="/" class="btn">Home</a>
        </div>
    </body></html>
    ''', result=result)


# Optionally expose an API endpoint for external use
@app.route('/api/fetch-trends', methods=['GET'])
def api_fetch_trends():
    result = fetch_trending_topics()
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)