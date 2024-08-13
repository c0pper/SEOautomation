from colorama import Fore
from utililty import check_and_load_state, json_fixer, gpt35, gpt4omini, MIN_H2
from yt_script import VideoScriptSegmentWriter


class OutlineGenerator:
    schema = """
    ### Instructions
    Based on the provided secondary keywords and longtail keywords, generate an outline adhering to the following json schema:
    {
        "h2_titles": [
            {
                "title": "The title of this H2Title",
                "content": "The content related to this H2Title, can be a string or null",
                "h3_titles": [
                    {
                        "title": "The title of this H3Title",
                        "content": "The content related to this H3Title, can be a string or null",
                        "web_search": "Optional web search results related to the H3Title"
                    }
                    ...
                ],
                "web_search": "Optional web search results related to the H2Title",
                "sources": Optional sources related to the H2Title
            }
            ...
        ]
    }

    Only respond with valid json which can be parsed in python.
    """
    
    system = """You are an outline generator. You will generate an outline to write an SEO-efficient article starting from a list of secondary keywords and a list of longtail keywords. H1 is the title of the whole article. You will provide a minimum of 3 H2 Titles and maximum 5 H2 Titles. Leave content empty, will be filled later."""
    
    human = """Secondary keywords: {s_kw}\nLongtail Keywords: {l_kw}\n\n###Important instructions###\You will provide a minimum of {min_h2} H2 Titles and maximum 6 H2 Titles. Each H2 title can have a minimum of 0 and a maximum of 2 H3 titles. NEVER include an introduction nor a conclusion. Those will be added later. Add the titles that are the most interesting, current and engaging.\n\n{schema}"""
    
    @classmethod
    def get_formatted_outline(cls, outline: dict, with_content=False) -> str:
        outline_str = ""
        for h2 in outline['h2_titles']:
            outline_str += f"## {h2['title']}\n"
            if with_content and h2.get('content'):
                outline_str += f"{h2['content']}\n\n"
            else:
                outline_str += "To be filled...\n\n"
            if h2.get('h3_titles'):
                for h3 in h2['h3_titles']:
                    outline_str += f"\t### {h3['title']}\n"
                    if with_content and h3.get('content'):
                        outline_str += f"{h3['content']}\n\n"
                    else:
                        outline_str += "\tTo be filled...\n\n"
        return outline_str


class H2BlockCreator:
    schema = """
    ### Instructions
    Based on the current outline and provided keywords, generate a new H2 block with optional related H3 blocks adhering to the following JSON schema:
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "H2Block",
      "type": "object",
      "properties": {
        "h2_title": {
          "type": "string",
          "description": "The title of the new H2 block"
        },
        "h2_content": {
          "type": ["string", "null"],
          "description": "The content related to the H2 block. Can be a string or null"
        },
        "h3_titles": {
          "type": ["array", "null"],
          "description": "The list of H3 titles related to the new H2 block. Can be null if no H3 titles are generated.",
          "items": {
            "type": "object",
            "properties": {
              "title": {
                "type": "string",
                "description": "The title of the H3 block"
              },
              "content": {
                "type": ["string", "null"],
                "description": "The content related to the H3 block. Can be a string or null"
              },
              "web_search": {
                "type": ["object", "null"],
                "description": "Optional web search results related to the H3 block"
              },
              "sources": {
                "type": ["array", "null"],
                "description": "Optional sources related to the H3 block",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["title"]
          }
        }
      },
      "required": ["h2_title"],
      "additionalProperties": false
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are a content creator specialized in developing article outlines. Based on the current outline and provided keywords, generate a new relevant H2 block. This new H2 block may include optional H3 blocks. Ensure the H2 block is engaging and relevant to the article's topic. Leave content empty; it will be filled later."""
    
    human = """Current Outline:\n{outline}\n\nSecondary keywords: {s_kw}\nLongtail Keywords: {l_kw}\n\n### Important instructions ###\nGenerate a new H2 block that fits well with the existing outline. The H2 block may have up to 2 related H3 blocks. Ensure the new H2 block is interesting and adds value to the article. Provide titles and optionally related H3 titles. Do not include content; only titles and structural elements.\n\n{schema}"""


def create_new_h2(state):
    sk = state["secondary_keywords"]
    longtail_keywords = state["longtail_keywords"]
    five_longest_lt_kws = sorted(longtail_keywords, key=len, reverse=True)[:5]
    
    llm_response = gpt4omini.invoke([
        ("system", H2BlockCreator.system),
        ("human", H2BlockCreator.human.format(outline=state["formatted_empty_outline"],s_kw=sk, l_kw=five_longest_lt_kws, min_h2=MIN_H2, schema=OutlineGenerator.schema)),
    ]).content
        
    h2 = json_fixer(llm_response)
    h2 = h2.get("h2_titles", h2)
    if isinstance(h2, list):
        h2 = h2[0]
    return h2


@check_and_load_state(["empty_outline"])
def get_outline(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Getting outline...')
    sk = state["secondary_keywords"]
    longtail_keywords = state["longtail_keywords"]
    five_longest_lt_kws = sorted(longtail_keywords, key=len, reverse=True)[:5]
    
    llm_response = gpt4omini.invoke([
        ("system", OutlineGenerator.system),
        ("human", OutlineGenerator.human.format(s_kw=sk, l_kw=five_longest_lt_kws, min_h2=MIN_H2, schema=OutlineGenerator.schema)),
    ]).content
        
    outline = json_fixer(llm_response)
    outline = outline.get("outline", outline)
    len_h2 = len(outline.get("h2_titles", []))
    formatted_empty_outline = OutlineGenerator.get_formatted_outline(outline)
    state["formatted_empty_outline"] = formatted_empty_outline
    
    while len_h2 < MIN_H2:
        print(Fore.LIGHTBLUE_EX + f'[+] Creating new h2 ({len_h2}/{MIN_H2} H2 currently)...')
        new_h2 = create_new_h2(state)
        outline.get("h2_titles").append(new_h2)
        len_h2 = len(outline.get("h2_titles", []))
    
    state["empty_outline"] = outline
    state["formatted_empty_outline"] = formatted_empty_outline
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