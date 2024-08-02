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

import re
from typing import Dict
from guardrails import Guard
from guardrails.hub import ValidJson
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
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

nlp = spacy.load("en_core_web_lg")
model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
RIFIUTA_COOKIE_BUTTON_ID = "W0wltc"


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
    
    if search_type == "nws":
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
    # errors coming from guardrails
    # example: guard = Guard().use(ValidJson, on_fail=fix_json)
    
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


def _old_json_fixer(json_from_llm):
    guard = Guard().use(ValidJson, on_fail=_fix_json)
    is_valid = False
    valid_json = ""
    max_retries = 5
    current = 0

    while not is_valid and current < max_retries:
        current += 1
        validation = guard.parse(json_from_llm)
        # validation.validated_output = ''
        if validation.validated_output:
            # validation.validated_output = '```json\n{\n    "primary_keyword": "Flood watch alert"\n}\n```'
            valid_json = validation.validated_output.replace("```json", "").replace("```", "").strip()
            try: 
                json.loads(valid_json)
                is_valid = validation.validation_passed
            except:
                is_valid = False
        else:
            raise ValueError("LLM responded with empty string")
    # print("Good JSON!\n", json.loads(valid_json))
    return json.loads(valid_json)

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


if __name__ == "__main__":
    print(list(text_getter("https://www.manchestereveningnews.co.uk/whats-on/music-nightlife-news/pearl-jam-tickets-manchester-29410579")))