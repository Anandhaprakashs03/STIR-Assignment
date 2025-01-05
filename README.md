STIR Assignment

Setup and Running Instructions

Clone the repository

Navigate to the project directory:
cd '.\STIR Assignment\'
cd .\project\

Ensure that you update the .env file with your own credentials for proper functionality.

Run the application:
python app.py

Once the application is running, open the browser and visit http://127.0.0.1:5000.

On the homepage, click "Fetch Trends" to start the process.

Make sure to remember your Twitter username and password for login.

The browser will automatically open, prompting you to enter your username and password.

The trending topics will be scraped from X (formerly Twitter).

Important Notes:
Every new request to scrape trending topics will be sent from a different IP address.

If you're located in India, please note that ProxyMesh can be slow and may occasionally cause timeout errors.

To enable ProxyMesh for the browser, uncomment the following line in the code:

python
Copy code
# chrome_options.add_argument(f'--proxy-server={proxy_url}')
This will allow the browser to use the ProxyMesh service.
