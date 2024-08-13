from colorama import Fore
from outline import OutlineGenerator
from utililty import check_and_load_state, json_fixer, gpt35


class CategoryGenerator:
    schema = """
    ### Instructions
    Based on the provided article outline and primary keyword, generate relevant WordPress categories adhering to the following JSON schema:
    {
        "categories": {
            "type": "array",
            "description": "A list of WordPress categories relevant to the article outline and primary keyword"
        }
        "required": ["categories"]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are CategoryGenerator, a specialized model designed to identify and suggest the most relevant WordPress categories based on a provided article outline and primary keyword. Your primary objective is to generate a list of categories that accurately reflect the content and themes of the article, optimizing for organization and discoverability on WordPress. Below are your guidelines and responsibilities:
    
        Relevance:
            Ensure each category is directly related to the main topic and themes outlined in the article.
    
        Coverage:
            Include categories that reflect both the primary focus and any significant subtopics.
    
        SEO Optimization:
            Consider search engine optimization by suggesting categories that are likely to improve the article's visibility.
            Use categories that align with common search queries related to the primary keyword.
    """
    
    human = """Overall article outline: {outline}\n\nPrimary keyword:\n{p_k}\n\n{schema}"""


@check_and_load_state(["categories"])
def get_categories(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating categories...')
    outline = state["formatted_empty_outline"]
    llm_response = gpt35.invoke([
        ("system", CategoryGenerator.system),
        ("human", CategoryGenerator.human.format(outline=outline, p_k=state["primary_keyword"], schema=CategoryGenerator.schema)),
    ]).content
        
    categories = json_fixer(llm_response)
    state["categories"] = ",".join(categories.get("categories", categories))
    return state
