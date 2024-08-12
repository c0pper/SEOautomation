from colorama import Fore
from outline import OutlineGenerator
from utililty import check_and_load_state, json_fixer, model


class TagGenerator:
    schema = """
    ### Instructions
    Based on the provided article outline and primary keyword, generate relevant WordPress tags adhering to the following JSON schema:
    {
        "article_tags": {
            "type": "array",
            "description": "A list of WordPress tags relevant to the article outline and primary keyword"
        }
        "required": ["article_tags"]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are TagGenerator, a specialized model designed to identify and suggest the most relevant WordPress tags based on a provided article outline and primary keyword. Your primary objective is to generate a list of tags that accurately reflect the content, themes, and specific details of the article, optimizing for searchability and content categorization on WordPress. Below are your guidelines and responsibilities:

    Relevance:
        Avoid overly broad or generic tags; aim for specific, descriptive, and relevant tags.

    Coverage:
        Include tags that reflect both the primary focus and any relevant subtopics, terminology, or key points.

    SEO Optimization:
        Consider search engine optimization by suggesting tags that are likely to improve the article's visibility.
        Use tags that align with common search queries related to the primary keyword and specific content details.
    """
    
    human = """Overall article outline: {outline}\n\nPrimary keyword:\n{p_k}\n\n{schema}"""


@check_and_load_state(["tags"])
def get_tags(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating tags...')
    outline = OutlineGenerator.print_formatted_outline(state["outline"])
    llm_response = model.invoke([
        ("system", TagGenerator.system),
        ("human", TagGenerator.human.format(outline=outline, p_k=state["primary_keyword"], schema=TagGenerator.schema)),
    ]).content
        
    tags = json_fixer(llm_response)
    state["tags"] = ",".join(tags.get("article_tags", tags))
    return state

