from typing import List
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from trend import get_news_for_trend, ask_trend, get_trends
from langchain_core.prompts import ChatPromptTemplate



model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    
class Article(BaseModel):
    link: Union[str|None]
    title: Union[str|None]
    source: Union[str|None]
    date: Union[str|None]
    snippet: Union[str|None]
    summary: Union[str|None]
    
class Topic(BaseModel):
    topic: str = Field(description="The topic name")
    articles: List[Article] = Field(description="The list of related news articles")
    
    
class NewsClusterer(BaseModel):
    topics: List[Topic] = Field(description="The list of generated topics")

news_clusterer_system = """You are a news clustering generator. You will cluster news articles into related topics based on their title and summary."""
news_clusterer_human = """Articles:\n\n {articles}"""
news_clusterer_template = ChatPromptTemplate.from_messages(
    [
        ("system", news_clusterer_system),
        ("human", news_clusterer_human)
    ]
)


chosen_trend = ask_trend()
processed_news_results = get_news_for_trend(chosen_trend)

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

    
structured_llm = model.with_structured_output(NewsClusterer)
generator = news_clusterer_template | structured_llm
generated_topics = generator.invoke({"articles": news_art_formatted})

for topic in generated_topics.topics:  # readd full articles after using shortened for llm
    article_titles = [article.title for article in topic.articles]
    complete_articles = [a for a in news_articles if a.title in article_titles]
    topic.articles = complete_articles


if len (generated_topics.topics) > 1:
    for idx, topic in enumerate(generated_topics.topics):
        print(f"{idx}. Topic: {topic.topic}")
        for art in topic.articles:
            print(f"\tArt title: {art.title}")
            print(f"\tArt snippet: {art.snippet}")
            print(f"\tArt url: {art.link}")
            print(f"\t--------------------------------")
    selected_index = 0 #int(input("Please select a topic by typing the number corresponding to the index: "))
    chosen_topic = generated_topics.topics[selected_index]
    print(f"\nYou selected query: {chosen_topic.topic}")
else:
    chosen_topic = generated_topics.topics[0]
    print(f"\One topic generated: {chosen_topic.topic}")