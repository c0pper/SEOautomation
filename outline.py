from typing import List, Optional, Union
from colorama import Fore
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
# from generate_keywords import pk, sec_keys, sec_keys_list, longtail_keys
from utililty import json_fixer, use_component, model




class ParagraphWriter:
    schema = """
    ### Instructions
    Generate the paragraph adhering to the following json schema:
    {
        "paragraph": {
            "type": "string",
            "description": "The content of the paragraph"
        },
        "required": ["paragraph"],
    }

    Only respond with valid json which can be parsed in python.
    """
    
    style_instructions = """### Writing style instructions ###
- Use Short Sentences: Keep sentences short and to the point.
- Where applicable, use bullet points, and numbered lists for readability.
- Active Voice: Use active voice where possible.
- Transitional Words: Use words like “therefore,” “however,” and “moreover” to improve flow.
- Make sure a 13 yeard old could understand your writing.
- The perfect paragraph should be between 50 and 150 words long.
- Banned words: vibrant, delve, unravel, journey, multifaceted, bustling, landscape, testament, realm, embark, crucial, vital, ensure.
"""
    
    system = """You are an expert SEO article writer. You will write the content of a paragraph based on the provided overall outline and paragraph title."""
    human = """### Overall article outline:\n {outline}\n\n### Context:\n{context}\n\n\n### Based on the provided context, write a 50-100 words paragraph about '{p_title}'\n\n{style}\n\n{schema}"""



class OutlineGenerator:
    schema = """
    ### Instructions
    Based on the provided secondary keywords and longtail keywords, generate an outline adhering to the following json schema:
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "Outline",
      "type": "object",
      "properties": {
        "h2_titles": {
          "type": "array",
          "description": "The generated H2Titles",
          "items": {
            "type": "object",
            "properties": {
              "title": {
                "type": "string",
                "description": "The title of this H2Title"
              },
              "content": {
                "type": ["string", "null", "object"],
                "description": "The content related to this H2Title, can be a string, ParagraphWriter object, or null"
              },
              "h3_titles": {
                "type": ["array", "null"],
                "description": "The list of H3Titles that will be generated. They are related to the H2 title.",
                "items": {
                  "type": "object",
                  "properties": {
                    "title": {
                      "type": "string",
                      "description": "The title of this H3Title"
                    },
                    "content": {
                      "type": ["string", "null", "object"],
                      "description": "The content related to this H3Title, can be a string, ParagraphWriter object, or null"
                    },
                    "web_search": {
                      "type": ["object", "null"],
                      "description": "Optional web search results related to the H3Title"
                    },
                    "sources": {
                      "type": ["array", "null"],
                      "description": "Optional sources related to the H3Title",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["title"]
                }
              },
              "web_search": {
                "type": ["object", "null"],
                "description": "Optional web search results related to the H2Title"
              },
              "sources": {
                "type": ["array", "null"],
                "description": "Optional sources related to the H2Title",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["title"]
          }
        }
      },
      "required": ["h2_titles"],
      "additionalProperties": false
    }

    Only respond with valid json which can be parsed in python.
    """
    
    system = """You are an outline generator. You will generate an outline to write an SEO-efficient article starting from a list of secondary keywords and a list of longtail keywords. H1 is the title of the whole article. You will provide a minimum of 3 H2 Titles and maximum 5 H2 Titles. Leave content empty, will be filled later."""
    
    human = """Secondary keywords: {s_kw}\nLongtail Keywords: {l_kw}\n\n###Important instructions###\You will provide a minimum of 3 H2 Titles and maximum 5 H2 Titles. Each H2 title can have a minimum of 0 and a maximum of 2 H3 titles. NEVER include an introduction nor a conclusion. Those will be added later. Add the titles that are the most interesting, current and engaging.\n\n{schema}"""
    
    @classmethod
    def print_formatted_outline(cls, outline: dict) -> str:
        outline_str = ""
        for h2 in outline['h2_titles']:
            outline_str += f"## {h2['title']}\n"
            if h2.get('content') and isinstance(h2['content'], dict) and 'paragraph' in h2['content']:
                outline_str += f"{h2['content']['paragraph']}\n\n"
            else:
                outline_str += "To be filled...\n\n"
            if h2.get('h3_titles'):
                for h3 in h2['h3_titles']:
                    outline_str += f"\t### {h3['title']}\n"
                    if h3.get('content') and isinstance(h3['content'], dict) and 'paragraph' in h3['content']:
                        outline_str += f"{h3['content']['paragraph']}\n\n"
                    else:
                        outline_str += "To be filled...\n\n"
        return outline_str


def get_outline(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting outline...')
    sk = state["secondary_keywords"]
    longtail_keywords = state["longtail_keywords"]
    five_longest_lt_kws = sorted(longtail_keywords, key=len, reverse=True)[:5]
    
    llm_response = model.invoke([
        ("system", OutlineGenerator.system),
        ("human", OutlineGenerator.human.format(s_kw=sk, l_kw=five_longest_lt_kws, schema=OutlineGenerator.schema)),
    ]).content
        
    outline = json_fixer(llm_response)
    state["outline"] = outline.get("outline", outline)
    print(Fore.LIGHTBLUE_EX + f'\t[+] Outline: {outline}')
    return state

if __name__ == "__main__":
    state = {
        "chosen_trend": {
            "name": "",
            "processed_news": [],
        },
        "topic": {
            'name': '', 
            'articles': []
        },
        "primary_keyword": "",
        "secondary_keywords": ['flash flood safety tips', 'how to prepare for flash floods', 'flash flood warning systems', 'flash flood emergency procedures', 'flash flood risk assessment', 'flash flood response plan', 'flash flood preparedness kit', 'flash flood evacuation routes', 'flash flood awareness and education', 'flash flood impact on infrastructure'],
        "longtail_keywords": ['how to stay safe during a flash flood warning', 'essential items to include in a flash flood preparedness kit', 'understanding the impact of flash floods on infrastructure', 'steps to create a comprehensive flash flood response plan', 'importance of flash flood awareness and education', 'evaluating flash flood risk assessment strategies', 'effective flash flood evacuation routes planning', 'utilizing flash flood warning systems for early alerts', 'implementing flash flood emergency procedures efficiently', 'preparing for flash floods: tips and guidelines'],
        "outline": {}
    }
    
    state = get_outline(state)