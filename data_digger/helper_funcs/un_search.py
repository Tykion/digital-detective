"""
Biggest problem is that i can't just check link for a username on social media platforms and see if it
returns 200 OK or 404, because most of the time the pages return fake 404, with actual code 200

solution: used headless browser to load pages and then fetch meta titles based on the return of the page
"""

import requests
import os
import time
import re

from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
# headless browser to extract title from dynamically loaded html pages
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


from helper_funcs.save_results import *

load_dotenv()

headers = {
    "User-Agent": f"digital_detective ({os.getenv('USER_AGENT')})"
}

def init_selenium():
    #add options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--log-level=3")
    #init chrome service
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

#extract title from a page using headless browser
def get_page_title(driver ,url, wait_time=2):   
    driver.get(url)
    
    time.sleep(wait_time)  # wait for JS to render
    return driver.title
    

@sleep_and_retry
@limits(calls=30,period=60)
def findby_un(un):
    username = un.replace('@', '')
    if len(username) < 3:
        print("Invalid username")
        return

    #dictionary of sites to check
    sites = {
        "Github": f"https://github.com/{username}/",
        "Instagram": f"https://www.instagram.com/{username}/",
        "X": f"https://x.com/{username}/",
        "TikTok": f"https://www.tiktok.com/@{username}/",
        "SoundCloud": f"https://soundcloud.com/{username}/"
    }

    driver = init_selenium()

    final_output = "\n"
    
    for site_name, url in sites.items():
        try:
            response = requests.get(url, headers=headers, timeout = 5)
            # check html - titles for specific sites
            start = response.text.find("<title>")
            end = response.text.find("</title>")

            title = response.text[start+7:end].strip()
            
            #INSTAGRAM SPECIFIC
            if response.status_code == 200 and site_name == "Instagram":
                if title == "Instagram":
                    final_output += f"{site_name}: no\n"
                else:
                    final_output += f"{site_name}: yes\n"
            #GITHUB returns 404 so no need to get page title
            elif site_name == "Github":
                if  response.status_code == 200:
                    final_output += f"{site_name}: yes\n"
                else:
                    final_output += f"{site_name}: no\n"
            #TWITTER
            elif site_name == "X" and response.status_code == 200:
                title = get_page_title(driver, url)
                page_source = driver.page_source
                if title == "Page not found / X" or "This account doesn’t exist" in page_source:
                    final_output += f"{site_name}: no\n"
                else:
                    final_output += f"{site_name}: yes\n"
            #TikTok
            elif site_name == "TikTok":
                title = get_page_title(driver, url)
                if re.search(r"Couldn’t find this account.|TikTok - Make Your Day", title):
                    final_output += f"{site_name}: no\n"
                else:
                    final_output += f"{site_name}: yes\n"
            #SoundCloud
            elif site_name == "SoundCloud":
                title = get_page_title(driver, url)
                if re.search(r"Something went wrong", title):
                    final_output += f"{site_name}: no\n"
                else:
                    final_output += f"{site_name}: yes\n"

        except requests.RequestException as e:
            final_output += f"{site_name}: Error ({e})\n"

    driver.quit()

    filename = save_results("un", username, final_output)
    print(final_output)
    print(f"Results written to file: {filename}")    
    