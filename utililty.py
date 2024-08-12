# Author: Linwood Creekmore
# Email: valinvescap@gmail.com
# Description:  Python script to pull content from a website (works on news stories).

#Licensed under GNU GPLv3; see https://choosealicense.com/licenses/lgpl-3.0/ for details

# Notes
"""
23 Oct 2017: updated to include readability based on PyCon talk: https://github.com/DistrictDataLabs/PyCon2016/blob/master/notebooks/tutorial/Working%20with%20Text%20Corpora.ipynb
18 Jul 2018: added keywords and summary
"""

###################################
# Standard Library imports
###################################

from functools import wraps
import os
import re
from typing import Dict
from colorama import Fore
import pytz
import datetime
import time
import platform
import json


###################################
# Third party imports
###################################

import requests
from newspaper import Article
from bs4 import BeautifulSoup
from readability.readability import Document as Paper
import nltk
import spacy
nltk.download('punkt')
import serpapi
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By

nlp = spacy.load("en_core_web_lg")
model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
RIFIUTA_COOKIE_BUTTON_ID = "W0wltc"
N_SOURCES_FROM_VECTORSTORE = 5


def scrape_google(query, search_type=None):
    driver = webdriver.Firefox()
    # Open Google search page
    driver.get("https://www.google.com")
    try:
        rifiuta_button = driver.find_element(By.ID, RIFIUTA_COOKIE_BUTTON_ID)
        rifiuta_button.click()
    except Exception as e:
        raise Exception("Errore nel bottone cookie google", e)

    # Find the search box and enter the query
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    # Wait for the results to load
    time.sleep(2)
    
    if search_type == "news":
        notizie_button = driver.find_element(By.XPATH, "//a//div[text()='Notizie']")
        notizie_button.click()
    
    # Find the div with id "search"
    search_div = driver.find_element(By.ID, "search")
    
    # Find all 'a' tags within the search div
    links = search_div.find_elements(By.TAG_NAME, "a")
    
    results = []
    for link in links:
        try:
            h3_text = link.find_element(By.TAG_NAME, "h3").text
            if len(h3_text) > 2:
                print(f"Title: {h3_text}")
                print(f"URL: {link.get_attribute('href')}")
                print("---")
                results.append({"link": link.get_attribute('href')})
        except:
            # If there's no h3 tag, look for div with role attribute
            try:
                div_with_role = link.find_element(By.XPATH, ".//div[@role]")
                div_text = div_with_role.text
                if len(div_text) > 2:
                    print(f"Title (div): {div_text}")
                    print(f"URL: {link.get_attribute('href')}")
                    print("---")
                    results.append({"link": link.get_attribute('href')})
            except:
                # If neither h3 nor div with role is found, skip this link
                pass
    
    driver.quit()
    return results


def search_google(query, gl="it", hl="it", search_type=None):
    search = scrape_google(query, search_type=search_type)
    
    # params = {
    # "api_key": os.getenv("SERP_API_KEY"),
    # "engine": "google",
    # "q": query,
    # # "location": "Austin, Texas, United States",
    # # "google_domain": "google.com",
    # "gl": gl,
    # "hl": hl,
    # "tbm": search_type #nws: Google News API,
    # }

    # search = serpapi.GoogleSearch(params)
    # search = search.get_dict()
    return search


def use_component(component_cls, input_dict:dict, llm=ChatOpenAI(model="gpt-4o-mini", temperature=0), system_prompt=None, human_prompt_template=None):
    structured_llm = llm.with_structured_output(component_cls)
    if not human_prompt_template:
        human_prompt_template = component_cls.get_user_prompt()


    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt_template)
        ]
    )
    # prompt = [
    #     ("system", component_cls.get_system_prompt()),
    #     ("human", human_prompt)
    # ]
    # system_msg = prompt.messages[0].prompt
    # user_msg = prompt.messages[1].prompt.format(input_dict)
    # print(system_msg)
    # print(user_msg)
    # print(f"\n\n######## PROMPT\nSystem: {system_msg}\nUser: {user_msg}\nTotal len: {len(system_msg)+len(user_msg)}########\n\n")
    generator = prompt | structured_llm
    result = generator.invoke(input_dict)
    # result = structured_llm.invoke(prompt)
    return result


done = {}


def text_getter(url: str) -> Dict:
    """Scrapes web news and returns the content.

    Parameters
    ----------
    url : str
        Web address to news report

    Returns
    -------
    answer : dict
        Python dictionary with key/value pairs for:
            text (str) - Full text of article
            url (str) - URL to article
            title (str) - Extracted title of article
            author (str) - Name of extracted author(s)
            base (str) - Base URL of where article was located
            provider (str) - String of the news provider from URL
            published_date (str, isoformat) - Extracted date of article
            top_image (str) - Extracted URL of the top image for article
    """
    global done
    TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'p', 'li']
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0"
    }

    # regex for url check
    s = re.compile('(http://|https://)([A-Za-z0-9_\.-]+)')
    u = re.compile("(http://|https://)(www.)?(.*)(\.[A-Za-z0-9]{1,4})$")
    
    answer = {
        'author': None,
        'base': None,
        'provider': None,
        'published_date': None,
        'text': None,
        'title': None,
        'top_image': None,
        'url': url,
        'keywords': None,
        'summary': None
    }

    if not s.search(url):
        answer['text'] = 'This is not a proper URL'
        yield answer
        return

    if url in done:
        yield done[url]
        return

    try:
        r = requests.get(url, headers=headers, verify=False, timeout=1)
        r.raise_for_status()
    except requests.RequestException:
        answer['text'] = 'Unable to reach website.'
        answer['base'] = s.search(url).group() if s.search(url) else None
        answer['provider'] = u.search(url).group(3) if u.search(url) else None
        done[url] = answer
        yield answer
        return

    site = u.search(url).group(3) if u.search(url) else None
    answer['base'] = s.search(url).group() if s.search(url) else None
    answer['provider'] = site

    if len(r.content) <= 500:
        answer['text'] = 'No text returned'
        yield answer
        return

    article = Article(url)
    if int(platform.python_version_tuple()[0]) == 3:
        article.download(input_html=r.content)
    elif int(platform.python_version_tuple()[0]) == 2:
        article.download(html=r.content)
    article.parse()
    article.nlp()

    if len(article.text) >= 200:
        answer['author'] = ", ".join(article.authors)
        answer['published_date'] = article.publish_date
        if isinstance(article.publish_date, datetime.datetime):
            try:
                answer['published_date'] = article.publish_date.astimezone(pytz.utc).isoformat()
            except:
                answer['published_date'] = article.publish_date.isoformat()
        answer['text'] = article.text
        answer['title'] = article.title
        answer['top_image'] = article.top_image
        answer['keywords'] = article.keywords
        answer['summary'] = article.summary
    else:
        doc = Paper(r.content)
        data = doc.summary()
        title = doc.title()
        soup = BeautifulSoup(data, 'lxml')
        newstext = " ".join([l.text for l in soup.find_all(TAGS)])

        if len(newstext) > 200:
            answer['text'] = newstext
            answer['title'] = title
        else:
            newstext = " ".join([
                l.text for l in soup.find_all('div', class_='field-item even')
            ])
            answer['text'] = newstext
            answer['title'] = title

    done[url] = answer
    yield answer
    
    
def _fix_json(invalid_json, errors: list):    
    if errors:
        nl = "\n"
        error_messages = nl.join([f"- {e}" for e in errors])
        errors_str = f"### Error messages\n{error_messages}"
    else:
        errors_str = f"### Error messages\nNot available"
    
    human_msg = f"### Invalid json\n{invalid_json}\n\n\n{errors_str}\n\n\nBased on the above information, fix the invalid json and return a string that can be parsed in python."
    messages = [
        ("system", "You are a master JSON programmer."),
        ("human", human_msg)
    ]
    response = model.invoke(messages).content
    return response


def json_fixer(json_from_llm):
    is_valid = False
    valid_json = ""
    max_retries = 5
    current = 0

    while not is_valid and current < max_retries:
        current += 1
        try:
            # Try to load the JSON to check its validity
            json_from_llm = json_from_llm.replace("```json", "").replace("```", "").strip()
            valid_json = json.loads(json_from_llm)
            is_valid = True
        except json.JSONDecodeError as e:
            # If there's an error, attempt to fix it
            error_output = str(e)
            json_from_llm = _fix_json(json_from_llm, [error_output])
    
    if is_valid:
        return valid_json
    else:
        raise ValueError("Unable to generate valid JSON after maximum retries")

def sanitize_string(string):
    return re.sub(r'[^A-Za-z0-9 ]+', '', string).lower().replace(" ", "_")


def save_state(state):
    directory = "articles"

    with open(f'{directory}/{state["tmp_name"]}', "w", encoding="utf8") as f:
        json.dump(state, f, indent=4)



def check_nested_keys(state, keys):
    current_level = state
    for key in keys:
        if isinstance(current_level, dict) and key in current_level and current_level[key]:
            current_level = current_level[key]
        else:
            return False
    return True


def check_and_load_state(required_keys):
    def decorator(func):
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            directory = "articles"
            if state['tmp_name']:
                file_path = f"{directory}/{state['tmp_name']}"
                
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf8") as f:
                        saved_state = json.load(f)
                    
                    all_keys_present = all(check_nested_keys(saved_state, keys.split('.')) for keys in required_keys)
                    if all_keys_present:
                        return saved_state
            
            result_state = func(state, *args, **kwargs)
            with open(f'{directory}/{result_state["tmp_name"]}', "w", encoding="utf8") as f:
                json.dump(result_state, f, indent=4)
            return result_state
        return wrapper
    return decorator


def check_web_search(state):
    if "outline" not in state:
        return False
    
    outline = state["outline"]
    
    for h2 in outline.get("h2_titles", []):
        if not h2.get("web_search"):
            return False
        if h2.get("h3_titles"):
            for h3 in h2["h3_titles"]:
                if not h3.get("web_search"):
                    return False
    return True


def check_and_load_web_search_state(func):
    @wraps(func)
    def wrapper(state, *args, **kwargs):
        directory = "articles"
        if state.get('tmp_name'):
            file_path = f"{directory}/{state['tmp_name']}"
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf8") as f:
                    saved_state = json.load(f)
                
                if check_web_search(saved_state):
                    return saved_state
        
        result_state = func(state, *args, **kwargs)
        with open(f'{directory}/{result_state["tmp_name"]}', "w", encoding="utf8") as f:
            json.dump(result_state, f, indent=4)
        return result_state
    return wrapper


def check_filled_outline(state):
    if "outline" not in state:
        return False
    
    outline = state["outline"]
    
    for h2 in outline.get("h2_titles", []):
        if not h2.get("content") or not h2.get("sources"):
            return False
        if h2.get("h3_titles"):
            for h3 in h2["h3_titles"]:
                if not h3.get("content") or not h3.get("sources"):
                    return False
    return True


def check_and_load_filled_outline_state(func):
    @wraps(func)
    def wrapper(state, *args, **kwargs):
        directory = "articles"
        if state.get('tmp_name'):
            file_path = f"{directory}/{state['tmp_name']}"
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf8") as f:
                    saved_state = json.load(f)
                
                if check_filled_outline(saved_state):
                    return saved_state
        
        result_state = func(state, *args, **kwargs)
        with open(f'{directory}/{result_state["tmp_name"]}', "w", encoding="utf8") as f:
            json.dump(result_state, f, indent=4)
        return result_state
    return wrapper


######### LINKS


def contains_links(content):
    url_pattern = re.compile(r'(https?://\S+)')
    return bool(url_pattern.search(content))

def check_links_in_outline(state):
    if "outline" not in state:
        return False
    
    outline = state["outline"]
    
    for h2 in outline.get("h2_titles", []):
        if not contains_links(h2.get("content", "")):
            return False
        if h2.get("h3_titles"):
            for h3 in h2["h3_titles"]:
                if not contains_links(h3.get("content", "")):
                    return False
    return True


def check_and_load_links_state(func):
    @wraps(func)
    def wrapper(state, *args, **kwargs):
        directory = "articles"
        if state.get('tmp_name'):
            file_path = f"{directory}/{state['tmp_name']}"
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf8") as f:
                    saved_state = json.load(f)
                
                if check_links_in_outline(saved_state):
                    return saved_state
        
        result_state = func(state, *args, **kwargs)
        with open(f'{directory}/{result_state["tmp_name"]}', "w", encoding="utf8") as f:
            json.dump(result_state, f, indent=4)
        return result_state
    return wrapper


import requests

def create_wordpress_post(title, content, site_id="93simon7.wordpress.com", tags=None, categories=None):
    print(Fore.BLUE + f'[+] Posting article...')
    if not os.getenv("WP_TOKEN"):
        raise ValueError("Missing wordpress token")
    
    token = os.getenv("WP_TOKEN")
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_id}/posts/new"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "title": title,
        "content": content,
        "tags": tags if tags else '',
        "categories": categories if categories else '',
        "status": "publish"  # You can change the status if needed
    }
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 201:
        print("Post created successfully!")
        return response.json()
    else:
        print(f"Failed to create post: {response.status_code}")
        print(response.json())
        return None






if __name__ == "__main__":
    print(list(text_getter("https://www.manchestereveningnews.co.uk/whats-on/music-nightlife-news/pearl-jam-tickets-manchester-29410579")))