from typing import List, Union

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from trend import get_news_for_trend, ask_trend, get_trends
from utililty import use_component
import langchain

langchain.debug = True


class Article(BaseModel):
    link: Union[str|None]
    title: Union[str|None]
    source: Union[str|None]
    date: Union[str|None]
    snippet: Union[str|None]
    summary: Union[str|None]

class Topic(BaseModel):
    # """A class representing a topic and its related news articles."""
    """A class representing a topic."""
    topic: str = Field(description="The topic name")
    articles: List[Article] = Field(description="The list of related news articles")


class TopicsGenerator(BaseModel):
    """A component responsible for generating topics based on a list of article titles and snippets."""
    
    topics: List[Topic] = Field(description="The list of generated topics, each containing a title and related articles.")

    @classmethod
    def get_system_prompt(cls) -> str:
        """Returns the system prompt used to guide the topic generation process."""
        return """You are a news topics generator. Generate a list of distinct topics based on a list of article titles and snippets provided. Aim to identify multiple topics, even if the differences are subtle."""

    @classmethod
    def get_user_prompt(cls) -> str:
        """Returns the user prompt with the given articles embedded.
        
        Args:
            articles (str): The string containing article titles and snippets.
        
        Returns:
            str: The user prompt with embedded articles.
        """
        return """List of articles:\n\n{articles}"""


class NewsClusterer(BaseModel):
    """A component responsible for clustering news articles into related topics based on their title and summary."""

    topics: List[Topic] = Field(description="The list of generated topics")

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You are a news clustering generator. You will cluster news articles into related topics based on their title and summary."""

    @classmethod
    def get_user_prompt(cls):
        return """Articles:\n\n {articles}"""



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
generated_topics = use_component(NewsClusterer, {"articles": news_art_formatted})
generated_topics = TopicsGenerator(topics=[Topic(topic='Pearl Jam Tour and Tickets', articles=[Article(link=None, title='Last-minute Pearl Jam resale tickets released for Co-op Live show tomorrow', source=None, date=None, snippet="The monumental rock band Pearl Jam recently started their world tour, kicking off in the USA first. And this will be the first of two chances British fans will have to see Pearl Jam hit stages this year. Here's the breakdown:How to buy Pearl Jam resale tickets nowPearl Jam tickets...", summary=None), Article(link=None, title='Pearl Jam Announce New Album, Dark Matter, Out April 19, 2024 Plus World Tour', source=None, date=None, snippet='Produced by multi-GRAMMY® award winning producer Andrew Watt, Dark Matter, marks the band’s first release since critically-acclaimed Gigaton (2020). Writing and recording in a burst of inspiration, Dark Matter was born in just three weeks. Get more information and find stores at www.recordstoreday.comDark Matter album packaging features light painting art...', summary=None), Article(link=None, title='Pearl Jam Slash Ticket Prices as Poor Sales Trend Lingers', source=None, date=None, snippet='Pearl Jam are the latest of many acts to have to shift plans or prices amid soft demand so far in 2024. While promoters and artists have rode a wave of post-COVID demand to record-shattering profits driven by ever-spiraling ticket prices, that trend seems to have fallen apart for many...', summary=None), Article(link=None, title='Pearl Jam asked Bill Clinton to take on Ticketmaster 30 years ago', source=None, date=None, snippet='Pearl Jam was at the White House, and President Bill Clinton wanted some advice from the musicians. It was April 9, 1994, and Pearl Jam was at the height of its fame after releasing “Vs.,” its second album. Days earlier, Nirvana frontman and fellow Seattle native Kurt Cobain had been...', summary=None), Article(link=None, title='How to buy Pearl Jam tickets today for 2024 UK tour', source=None, date=None, snippet="Pearl Jam also announced an enormous world tour will be taking place throughout 2024. Here's what you need to know:Pearl Jam's new album cover for Dark MatterHow to buy Pearl Jam ticketsPearl Jam tickets will be released today, Friday, February 23, 2024, at 10am. Here's the link breakdown on where...", summary=None), Article(link=None, title='Pearl Jam announce Spurs Stadium concert and you need to register for tickets', source=None, date=None, snippet="Dark Matter is being released on April 19, but you have to register for concert tickets way before that. They'll be available from Live Nation and Ticketmaster. You'll have until February 18 to register on either Live Nation and Ticketmaster, and you'll get alerted when the sale starts. You can...", summary=None)]), Topic(topic='Music Concerts and Tours', articles=[Article(link=None, title='Australia concerts in 2024: here’s a list of shows and tours coming up', source=None, date=None, snippet='To celebrate, she’ll stage her debut headline shows in Australia with four stops across Brisbane, Sydney and Melbourne. In July, he’ll perform three shows in Melbourne, Sydney and Brisbane – tickets are now on sale. Tickets are now available for all shows in Sydney, Brisbane, Melbourne, Adelaide and Perth. Sofi...', summary=None), Article(link=None, title='Pearl Jam, Neil Young and more: Several major performers announce Chicago tour stops', source=None, date=None, snippet='According to an announcement from Live Nation, Seattle grunge band Pearl Jam has announced a 2024 world tour with a two-night stop in Chicago at Wrigley Field. The 35-date "Dark Matter" tour, which coincides with their new album set to be released April 19, will come to Chicago Aug. 29...', summary=None), Article(link=None, title='The LA Setlist: May 21-26, 2024', source=None, date=None, snippet='While forever associated with the grunge genre that they helped propel out of Seattle in the early 1990s, Pearl Jam is in truth simply a fantastic band that would’ve thrived in any era of rock ‘n roll. Indeed, in some ways the quintet is a modern anomaly, not least in...', summary=None)])])

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
    selected_index = int(input("Please select a topic by typing the number corresponding to the index: "))
    chosen_topic = generated_topics.topics[selected_index]
    print(f"\nYou selected query: {chosen_topic.topic}")
else:
    chosen_topic = generated_topics.topics[0]
    print(f"\One topic generated: {chosen_topic.topic}")