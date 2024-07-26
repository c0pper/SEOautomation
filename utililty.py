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
import pytz
import datetime
import platform


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

nlp = spacy.load("en_core_web_lg")

def search_google(query, gl="it", hl="it", search_type=None):
  params = {
    "api_key": os.getenv("SERP_API_KEY"),
    "engine": "google",
    "q": query,
    # "location": "Austin, Texas, United States",
    # "google_domain": "google.com",
    "gl": gl,
    "hl": hl,
    "tbm": search_type #nws: Google News API,
  }

  search = serpapi.GoogleSearch(params)
  search = search.get_dict()
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

if __name__ == "__main__":
    print(list(text_getter("https://www.manchestereveningnews.co.uk/whats-on/music-nightlife-news/pearl-jam-tickets-manchester-29410579")))