

import json
from typing import List
from colorama import Fore
from pydantic import BaseModel, Field
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

        


def get_primary_keyword(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting primary_keyword for topic {state["topic"]["name"]}')
    pk_articles = state["topic"]["articles"]
    formatted_articles = "\n----\n".join([f'Title: {a.title}\nSnippet: {a.snippet}' for a in pk_articles])

    llm_response = model.invoke([
        ("system", PrimaryKeywordGenerator.system),
        ("human", PrimaryKeywordGenerator.human.format(articles=formatted_articles, schema=PrimaryKeywordGenerator.schema)),
    ]).content
        
    primary_keyword = json_fixer(llm_response)
    state["primary_keyword"] = primary_keyword
    print(Fore.LIGHTBLUE_EX + f'\t[+] Primary_keyword: {primary_keyword}')
    return state