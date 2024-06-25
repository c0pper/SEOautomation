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
nltk.download('punkt')




done = {}


def text_getter(url):
    """Scrapes web news and returns the content
    Parameters
    ----------
    url : str
        web address to news report
    Returns 
    -------
    
    answer : dict
        Python dictionary with key/value pairs for:
            text (str) - Full text of article
            url (str) - url to article
            title (str) - extracted title of article
            author (str) - name of extracted author(s)
            base (str) - base url of where article was located
            provider (str) - string of the news provider from url
            published_date (str,isoformat) - extracted date of article
            top_image (str) - extracted url of the top image for article
    """
    global done
    TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'p', 'li']

    # regex for url check
    s = re.compile('(http://|https://)([A-Za-z0-9_\.-]+)')
    u = re.compile("(http://|https://)(www.)?(.*)(\.[A-Za-z0-9]{1,4})$")
    if s.search(url):
        site = u.search(s.search(url).group()).group(3)
    else:
        site = None
    answer = {}
    # check that its an url
    if s.search(url):
        if url in done.keys():
            yield done[url]
            pass
        try:
            # make a request to the url
            r = requests.get(url, verify=False, timeout=1)
        except:
            # if the url does not return data, set to empty values
            done[url] = "Unable to reach website."
            answer['author'] = None
            answer['base'] = s.search(url).group()
            answer['provider']=site
            answer['published_date']=None
            answer['text'] = "Unable to reach website."
            answer['title'] = None
            answer['top_image'] = None
            answer['url'] = url
            answer['keywords']=None
            answer['summary']=None
            yield answer
        # if url does not return successfully, set ot empty values
        if r.status_code != 200:
            done[url] = "Unable to reach website."
            answer['author'] = None
            answer['base'] = s.search(url).group()
            answer['provider']=site
            answer['published_date']=None
            answer['text'] = "Unable to reach website."
            answer['title'] = None
            answer['top_image'] = None
            answer['url'] = url
            answer['keywords']=None
            answer['summary']=None

        # test if length of url content is greater than 500, if so, fill data
        if len(r.content)>500:
            # set article url
            article = Article(url)
            # test for python version because of html different parameters
            if int(platform.python_version_tuple()[0])==3:
                article.download(input_html=r.content)
            elif int(platform.python_version_tuple()[0])==2:
                article.download(html=r.content)
            # parse the url
            article.parse()
            article.nlp()
            # if parse doesn't pull text fill the rest of the data
            if len(article.text) >= 200:
                answer['author'] = ", ".join(article.authors)
                answer['base'] = s.search(url).group()
                answer['provider']=site
                answer['published_date'] = article.publish_date
                answer['keywords']=article.keywords
                answer['summary']=article.summary
                # convert the data to isoformat; exception for naive date
                if isinstance(article.publish_date,datetime.datetime):
                    try:
                        answer['published_date']=article.publish_date.astimezone(pytz.utc).isoformat()
                    except:
                        answer['published_date']=article.publish_date.isoformat()
                

                answer['text'] = article.text
                answer['title'] = article.title
                answer['top_image'] = article.top_image
                answer['url'] = url
                
                

            # if previous didn't work, try another library
            else:
                doc = Paper(r.content)
                data = doc.summary()
                title = doc.title()
                soup = BeautifulSoup(data, 'lxml')
                newstext = " ".join([l.text for l in soup.find_all(TAGS)])

                # as we did above, pull text if it's greater than 200 length
                if len(newstext) > 200:
                    answer['author'] = None
                    answer['base'] = s.search(url).group()
                    answer['provider']=site
                    answer['published_date']=None
                    answer['text'] = newstext
                    answer['title'] = title
                    answer['top_image'] = None
                    answer['url'] = url
                    answer['keywords']=None
                    answer['summary']=None
                # if nothing works above, use beautiful soup
                else:
                    newstext = " ".join([
                        l.text
                        for l in soup.find_all(
                            'div', class_='field-item even')
                    ])
                    done[url] = newstext
                    answer['author'] = None
                    answer['base'] = s.search(url).group()
                    answer['provider']=site
                    answer['published_date']=None
                    answer['text'] = newstext
                    answer['title'] = title
                    answer['top_image'] = None
                    answer['url'] = url
                    answer['keywords']=None
                    answer['summary']=None
        # if nothing works, fill with empty values
        else:
            answer['author'] = None
            answer['base'] = s.search(url).group()
            answer['provider']=site
            answer['published_date']=None
            answer['text'] = 'No text returned'
            answer['title'] = None
            answer['top_image'] = None
            answer['url'] = url
            answer['keywords']=None
            answer['summary']=None
            yield answer
        yield answer

    # the else clause to catch if invalid url passed in
    else:
        answer['author'] = None
        answer['base'] = s.search(url).group()
        answer['provider']=site
        answer['published_date']=None
        answer['text'] = 'This is not a proper url'
        answer['title'] = None
        answer['top_image'] = None
        answer['url'] = url
        answer['keywords']=None
        answer['summary']=None
        yield answer
        

if __name__ == "__main__":
    print(list(text_getter("https://www.areanapoli.it/varie/maradona-e-la-punizione-alla-juventus-platini-a-pecci-ma-non-potevi-passargli-il-pallone-sul-destro_552770.html")))