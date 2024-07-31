

import json
from typing import List
from pydantic import BaseModel, Field
from topics import chosen_topic
from utililty import json_fixer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)



class PrimaryKeywordGenerator():
    schema = """
    ### Insutrctions
    Based on the above articles, generate a primary keyword adhering to the following json schema:
    {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "PrimaryKeyword",
    "type": "object",
    "properties": {
        "primary_keyword": {
        "type": "string",
        "description": "The main term or phrase a webpage is expected to rank for in search engine results"
        }
    },
    "required": ["primary_keyword"],
    "additionalProperties": false
    }

    Only respond with valid json which can be parsed in python.
    """
    
    system = """You are a primary keyword generator. You will generate a primary keyword to guide the writing of an SEO-efficient article starting from a list of articles."""
    human = """Articles:\n\n {articles}\n\n{schema}"""

    def __init__(self, articles, schema) -> None:
        self.articles = articles
        self.schema = schema

    def generate_primary_kw(self):
        



pk_articles = chosen_topic.articles
formatted_articles = "\n----\n".join([f'Title: {a.title}\nSnippet: {a.snippet}' for a in pk_articles])

llm_response = model.invoke([
    ("system", PrimaryKeywordGenerator.system),
    ("human", PrimaryKeywordGenerator.human.format(articles=formatted_articles, schema=PrimaryKeywordGenerator.schema)),
]).content
    
primary_keyword = json_fixer(llm_response)
print(primary_keyword)