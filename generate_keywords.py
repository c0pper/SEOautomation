

import json
from typing import List
from colorama import Fore
from pydantic import BaseModel, Field
from utililty import check_and_load_state, json_fixer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utililty import gpt35




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


class SecondaryKeywordGenerator():
    schema = """
    ### Insutrctions
    Generate a list of secondary keywords adhering strictly to the following json schema:
    {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SecondaryKeyword",
    "type": "object",
    "properties": {
        "secondary_keywords": {
        "type": "array",
        "description": "The list of generated secondary keywords"
        }
    },
    "required": ["secondary_keywords"],
    "additionalProperties": false
    }

    Only respond with valid json which can be parsed in python.
    """
    
    system = """You are a secondary keywords generator. You will generate a list of secondary keywords to guide the writing of an SEO-efficient article based on the provided primary keyword and a list of related articles.\n\n Example: For an article with the primary keyword "how to bake a cake," potential secondary keywords could be:\n    "cake baking tips"\n    "best cake baking recipes"\n    "cake baking ingredients"\n    "cake baking tools"\n    "common cake baking mistakes.\n\nAVOID generic keywords such as "Obama news", be specific."""
    human = """### Primary keyword:\n {p_kw}\n\n### Related articles:\n{articles}\n\n###Additional instructions###\n AVOID any generic keywords such as 'Obama news', be specific.\n\n{schema}"""


class LongtailKeywordsGenerator():
    schema = """
    ### Insutrctions
    Generate a list of longtail keywords adhering strictly to the following json schema:
    {
        "longtail_keywords": {
            "type": "array",
            "description": "The list of generated longtail keywords"
        },
        "required": ["longtail_keywords"],
    }

    Only respond with valid json which can be parsed in python.
    """
    
    system = """You will generate longtail keywords starting from a primary keyword, a list of secondary keywords and a list of related articles. For example, if the primary keyword was 'bake a cake,' potential long-tail keywords could be:\n\n    'how to bake a chocolate cake from scratch'\n    'easy homemade vanilla cake recipe'\n    'gluten-free cake baking tips'\n    'best tools for cake baking beginners'\n    'how to bake a moist red velvet cake'"""
    human = """### Primary keyword:\n {p_kw}\n\n### Secondary keywords:\n {s_kw}\n\n### Related articles:\n{articles}\n\n{schema}"""


@check_and_load_state(["primary_keyword"])
def get_primary_keyword(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting primary_keyword for topic {state["topic"]["name"]}')
    pk_articles = state["topic"]["articles"]
    formatted_articles = "\n----\n".join([f'Title: {a["title"]}\nSnippet: {a["snippet"]}' for a in pk_articles])

    llm_response = gpt35.invoke([
        ("system", PrimaryKeywordGenerator.system),
        ("human", PrimaryKeywordGenerator.human.format(articles=formatted_articles, schema=PrimaryKeywordGenerator.schema)),
    ]).content
        
    primary_keyword = json_fixer(llm_response)
    state["primary_keyword"] = primary_keyword.get("primary_keyword", primary_keyword)
    state["topic"]["formatted_articles"] = formatted_articles
    print(Fore.LIGHTBLUE_EX + f'\t[+] Primary_keyword: {primary_keyword}')
    return state


@check_and_load_state(["secondary_keywords"])
def get_secondary_keywords(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting secondary_keywords for topic {state["topic"]["name"]}')
    formatted_articles = state["topic"]["formatted_articles"]
    pk = state["primary_keyword"]
    
    llm_response = gpt35.invoke([
        ("system", SecondaryKeywordGenerator.system),
        ("human", SecondaryKeywordGenerator.human.format(p_kw=pk, articles=formatted_articles, schema=SecondaryKeywordGenerator.schema)),
    ]).content
        
    secondary_keywords = json_fixer(llm_response)
    state["secondary_keywords"] = secondary_keywords.get("secondary_keywords", secondary_keywords)
    print(Fore.LIGHTBLUE_EX + f'\t[+] Secondary keywords: {secondary_keywords}')
    return state


@check_and_load_state(["longtail_keywords"])
def get_longtail_keywords(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting longtail_keywords for topic {state["topic"]["name"]}')
    formatted_articles = state["topic"]["formatted_articles"]
    pk = state["primary_keyword"]
    sk = state["secondary_keywords"]
    
    llm_response = gpt35.invoke([
        ("system", LongtailKeywordsGenerator.system),
        ("human", LongtailKeywordsGenerator.human.format(p_kw=pk, s_kw=sk, articles=formatted_articles, schema=LongtailKeywordsGenerator.schema)),
    ]).content
        
    longtail_keywords = json_fixer(llm_response)
    state["longtail_keywords"] = longtail_keywords.get("longtail_keywords", longtail_keywords)
    print(Fore.LIGHTBLUE_EX + f'\t[+] Longtail keywords: {longtail_keywords}')
    return state