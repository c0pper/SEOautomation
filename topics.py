from typing import List
from typing import Union
from colorama import Fore
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from trend import get_news_for_trend, ask_trend, get_trends
from utililty import json_fixer
from langchain_core.prompts import ChatPromptTemplate



model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    
class Article(BaseModel):
    link: Union[str|None]
    title: Union[str|None]
    source: Union[str|None]
    date: Union[str|None]
    snippet: Union[str|None]
    summary: Union[str|None]
    

class TopicsGenerator():
    schema = """### Insutrctions
    Based on the above articles, generate a list of topics adhering to the following json schema:
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NewsClusterer",
  "type": "object",
  "properties": {
    "topics": {
      "type": "array",
      "description": "The list of generated topics",
      "items": {
        "$ref": "#/definitions/Topic"
      }
    }
  },
  "required": ["topics"],
  "additionalProperties": false,
  "definitions": {
    "Article": {
      "type": "object",
      "properties": {
        "title": {
          "type": ["string", "null"],
          "description": "The title of the article"
        }
      },
      "additionalProperties": false
    },
    "Topic": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "The topic name"
        },
        "articles": {
          "type": "array",
          "description": "The list of related news articles",
          "items": {
            "$ref": "#/definitions/Article"
          }
        }
      },
      "required": ["topic"],
      "additionalProperties": false
    }
  }
}"""
    
    system = """You are a news clustering generator. You will cluster news articles into related topics based on their title and summary."""
    human = """Articles:\n\n {articles}\n\n\n{schema}"""



# chosen_trend = ask_trend()
# processed_news_results = get_news_for_trend(chosen_trend)

def get_topics(state):
    trend = state["chosen_trend"]["name"]
    print(Fore.LIGHTBLUE_EX + f'[+] Getting topics for trend {trend}')
    
    processed_news_results = state['chosen_trend']['processed_news']
    news_articles = [Article(
            title=n['title'],
            link=n['url'],
            source=n['provider'],
            date=n['published_date'],
            snippet=' '.join(n['summary'].split()[:50])+"..." if n['summary'] else ' '.join(n['text'].split()[:50])+"...",
            summary=n["summary"])
        for n in processed_news_results]

    news_articles_shortened = [Article(
            title=n['title'],
            link="",
            source="",
            date="",
            snippet=' '.join(n['summary'].split()[:50])+"..." if n['summary'] else ' '.join(n['text'].split()[:50])+"...",
            summary="")
        for n in processed_news_results]

    news_art_formatted = "\n-----\n".join([f"Article Title: {a.title}\nArticle Snippet: {a.snippet}" for a in news_articles_shortened][:4])

    llm_response = model.invoke([
        ("system", TopicsGenerator.system),
        ("human", TopicsGenerator.human.format(articles=news_art_formatted, schema=TopicsGenerator.schema)),
    ]).content

    topics = json_fixer(llm_response)
    if topics["topics"]:
        for topic in topics["topics"]:  # re-add full articles after using shortened for llm
            article_titles = [article["title"] for article in topic["articles"]]
            complete_articles = [a for a in news_articles if a.title in article_titles]
            topic["articles"] = complete_articles
    else:
        raise ValueError(f"No topics generated: {topics}")

    if len (topics["topics"]) > 1:
        for idx, topic in enumerate(topics["topics"]):
            print(f"{idx}. Topic: {topic.topic}")
            for art in topic["articles"]:
                print(f"\tArt title: {art.title}")
                print(f"\tArt snippet: {art.snippet}")
                print(f"\tArt url: {art.link}")
                print(f"\t--------------------------------")
        selected_index = 0 #int(input("Please select a topic by typing the number corresponding to the index: "))
        chosen_topic = topics["topics"][selected_index]
        print(f"\nYou selected query: {chosen_topic['topic']}")
        state["topic"] = chosen_topic
        return state
    else:
        chosen_topic = topics["topics"][0]
        print(f"\nOne topic generated: {chosen_topic['topic']}")
        for art in chosen_topic["articles"]:
            print(f"\tArt title: {art.title}")
            print(f"\tArt snippet: {art.snippet}")
            print(f"\tArt url: {art.link}")
            print(f"\t--------------------------------")
        state["topic"] = chosen_topic
        return state