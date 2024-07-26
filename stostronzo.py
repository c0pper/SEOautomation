

from typing import List
from pydantic import BaseModel, Field
from topics import chosen_topic
from utililty import use_component
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

# class PrimaryKeyword(BaseModel):
#     # """ primary keyword is the central term or phrase that best represents the main topic of a piece of content."""
#     keyword: str = Field(description="The primary keyword")

class PrimaryKeywordGenerator(BaseModel):
    # """A component responsible for generating a primary keyword for an article starting from a list of related articles."""
    # primary_keyword: PrimaryKeyword = Field(
    #     description="The generated primary keyword"
    # )
    primary_keyword: str = Field(
        description="The generated primary keyword"
    )
    
primary_keyword_gen_system = """You are a primary keyword generator. You will generate a primary keyword to guide the writing of an SEO-efficient article starting from a list of articles."""
primary_keyword_gen_human = """Articles:\n\n {articles}"""
primary_keyword_gen_template = ChatPromptTemplate.from_messages(
    [
        ("system", primary_keyword_gen_system),
        ("human", primary_keyword_gen_human)
    ]
)





pk_articles = chosen_topic.articles
# formatted_articles = 'Title: Two inches of rain per hour possible: Flood watch issued by National Weather Service\nSnippet: Two inches of rain per hour possible: Flood watch issued by National Weather ServiceNational Weather Service has issued a time sensitive severe alert. A flood watch is in effect Tuesday from 5 p.m. to 11 p.m. this evening. WHERE: Portions of central, northern, northwest, and western Virginia, including the following...\n----\nTitle: National Weather Service issues flood watch for Tri-Cities until 10 p.m. Saturday\nSnippet: National Weather Service issues flood watch for Tri-Cities until 10 p.m. SaturdaySaturday\'s hard rain pummeling the Tri-City area has led to a flash-flood watch from the National Weather Service until 10 p.m., with warnings issues for points north and east of here. NWS\' Wakefield office issued the advisory around 3:40...\n----\nTitle: \'Life-Threatening Flash Flooding\' Possible In GA; Warnings Issued\nSnippet: Weather \'Life-Threatening Flash Flooding\' Possible In GA; Warnings Issued "Life-threatening flash flooding" may occur in some parts of Georgia on Tuesday, according to two warnings. A flash flood warning has been issued for some Georgia cities until 10 p.m. Tuesday. (Shutterstock)GEORGIA — A flash flood warning has been issued for...\n----\nTitle: Flash flood warning issued for Harrisonburg and Rockingham County\nSnippet: HARRISONBURG, Va. ( ROCKTOWN NOW ) – The National Weather Service has issued a flash flood warning for central Rockingham County and Harrisonburg, Virginia until 7:45 p.m. According to an alert from NWS in Sterling, Va., thunderstorms are producing heavy rainfall of 1-2 inches per hour, with 1-1.5 inches already...'
formatted_articles = "\n----\n".join([f'Title: {a.title}\nSnippet: {a.snippet}' for a in pk_articles])

structured_llm = model.with_structured_output(PrimaryKeywordGenerator)
generator = primary_keyword_gen_template | structured_llm
pk = generator.invoke({"articles": formatted_articles})
print(pk)