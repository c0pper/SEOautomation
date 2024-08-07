from colorama import Fore
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from outline import OutlineGenerator, ParagraphWriter
from utililty import check_and_load_filled_outline_state, check_and_load_web_search_state, json_fixer, save_state, search_google, use_component, model
from vectorestore import get_vectore_store, fill_vectorstore

style_instructions = """### Writing style instructions ###
- Use Short Sentences: Keep sentences short and to the point.
- Where applicable, use bullet points, and numbered lists for readability.
- Active Voice: Use active voice where possible.
- Transitional Words: Use words like “therefore,” “however,” and “moreover” to improve flow.
- Make sure a 13 yeard old could understand your writing.
- The perfect paragraph should be between 50 and 150 words long.
- Banned words: vibrant, delve, unravel, journey, multifaceted, bustling, landscape, testament, realm, embark, crucial, vital, ensure.
"""


# class SearchQueryGenerator(BaseModel):
#     """Generate an search query to be used for finding information on the web about a topic."""

#     query:str = Field(description="The generated search query")

#     @classmethod
#     def get_system_prompt(cls) -> str:
#         return """You are SearchQueryGenerator, a specialized model designed to generate effective and relevant search queries for finding information on the web about a given topic. Your primary objective is to craft a search query that yield the most pertinent and comprehensive results, facilitating the discovery of valuable information. Below are your guidelines and responsibilities:\n\n- Identify key elements, related subtopics, and potential search keywords that encapsulate the topic comprehensively.\n- Generate a clear, concise, and targeted search query.\n- Ensure the query is specific enough to filter out irrelevant information yet broad enough to capture all relevant data.\n- """
    
#     @classmethod
#     def get_user_prompt(cls):
#         return """Topic: {paragraph_title}"""
    
class SearchQueryGenerator:
    schema = """
    ### Instructions
    Based on the provided topic, generate a search query adhering to the following json schema:
    {
        "query": {
            "type": "string",
            "description": "The generated search query"
        },
        "required": ["query"]
    }

    Only respond with valid json which can be parsed in python.
    """

    system = """You are SearchQueryGenerator, a specialized model designed to generate effective and relevant search queries for finding information on the web about a given topic. Your primary objective is to craft a search query that yields the most pertinent and comprehensive results, facilitating the discovery of valuable information. Below are your guidelines and responsibilities:\n\n- Identify key elements, related subtopics, and potential search keywords that encapsulate the topic comprehensively.\n- Generate a clear, concise, and targeted search query.\n- Ensure the query is specific enough to filter out irrelevant information yet broad enough to capture all relevant data."""
    
    human = """Topic: {paragraph_title}\n\n{schema}"""

    
@check_and_load_web_search_state
def search_web_for_outline_paragraphs(state: dict, gl="us", hl="en") -> dict:
    outline = state["outline"]
    total_h2 = len(outline['h2_titles'])
    total_h3 = sum([len(h2['h3_titles']) for h2 in outline['h2_titles'] if h2.get('h3_titles')])
    
    print(f"[+] Preparing to make {total_h3+total_h2} searches")

    outline_copy = outline.copy()  # copy outline so I keep the empty version
    for h2 in outline_copy['h2_titles']:
        llm_response = model.invoke([
            ("system", SearchQueryGenerator.system),
            ("human", SearchQueryGenerator.human.format(paragraph_title=h2['title'], schema=SearchQueryGenerator.schema)),
        ]).content
            
        generated_query = json_fixer(llm_response)
        generated_query = generated_query.get("query", generated_query)
        print(f"\t[H2] Searching for {generated_query}")
        
        h2_results = search_google(generated_query, hl=hl, gl=gl, search_type="nws")
        h2['web_search'] = {
            "generated_query": generated_query,
            "results": h2_results if "organic_results" in h2_results else {"organic_results": h2_results}
        }

        if h2.get('h3_titles'):
            for h3 in h2['h3_titles']:
                llm_response = model.invoke([
                    ("system", SearchQueryGenerator.system),
                    ("human", SearchQueryGenerator.human.format(paragraph_title=h3['title'], schema=SearchQueryGenerator.schema)),
                ]).content
                    
                generated_query = json_fixer(llm_response)
                generated_query = generated_query.get("query", generated_query)
                print(f"\t\t[H3] Searching for {generated_query}")
                
                h3_results = search_google(generated_query, hl=hl, gl=gl, search_type="nws")
                h3['web_search'] = {
                    "generated_query": generated_query,
                    "results": h3_results if "organic_results" in h3_results else {"organic_results": h3_results}
                }
    state["outline"] = outline_copy
    return state


def write_paragraph(title, outline, vectorstore, n_sources):
    print(Fore.LIGHTBLUE_EX + f'[+] Writing paragraph "{title}"...')
    sources = vectorstore.similarity_search(title, k=n_sources)
    sources = [{'page_content': doc.page_content, 'metadata': doc.metadata} for doc in sources]
    print(Fore.LIGHTBLUE_EX + f"\tSources len: {[len(d['page_content']) for d in sources]}")
    context = "\n\n-----\n\n".join([d["page_content"] for d in sources])
    formatted_outline = OutlineGenerator.print_formatted_outline(outline)
    print(f"\tLen input dict: {len(formatted_outline) + len(context) + len(title) + len(ParagraphWriter.style_instructions) + len(ParagraphWriter.schema)}")
    
    llm_response = model.invoke([
        ("system", ParagraphWriter.system),
        ("human", ParagraphWriter.human.format(
            outline=formatted_outline, 
            context=context,
            p_title=title,
            style=ParagraphWriter.style_instructions,
            schema=ParagraphWriter.schema
        )),
    ]).content
                    
    content = json_fixer(llm_response)
    content = content.get("paragraph", content)
    
    return content, sources


def fill_outline_paragraphs(outline: dict, vectorstore: Chroma, n_sources: int) -> dict:
    print(Fore.GREEN + f'[+] Filling outline paragrpahs...')
    outline_copy = outline.copy()  # copy outline so I keep the empty version

    for h2 in outline_copy['h2_titles']:
        print(h2['title'])
        h2_content, h2_sources = write_paragraph(title=h2['title'], outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources)
        h2['content'] = h2_content
        h2['sources'] = h2_sources

        if 'h3_titles' in h2:
            for h3 in h2['h3_titles']:
                print(h3['title'])
                h3_content, h3_sources = write_paragraph(title=h3['title'], outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources)
                h3['content'] = h3_content
                h3['sources'] = h3_sources

    return outline_copy


@check_and_load_filled_outline_state
def get_filled_outline(state):
    print(Fore.GREEN + f'[+] Starting filling outline with content...')
    vectorstore = get_vectore_store(state)
    fill_vectorstore(state["outline"], vectorstore)
    filled_outline = fill_outline_paragraphs(state["outline"], vectorstore=vectorstore, n_sources=4)
    
    state["outline"] = filled_outline
    return state