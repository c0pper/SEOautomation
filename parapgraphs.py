from colorama import Fore
from langchain_chroma import Chroma
from outline import OutlineGenerator
from utililty import check_and_load_filled_outline_state, check_and_load_web_search_state, json_fixer, search_google, model, N_SOURCES_FROM_VECTORSTORE
from vectorestore import get_vectore_store, fill_vectorstore


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


class VideoScriptSegmentWriter:
    schema = """
    ### Instructions
    Generate the script segment adhering to the following JSON schema:
    {
        "paragraph": {
            "type": "string",
            "description": "The content of the paragraph"
        },
        "required": ["paragraph"],
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    style_instructions = """### Writing style instructions ###
- Use Short Sentences: Keep sentences concise and direct.
- Active Voice: Utilize active voice whenever possible.
- Use Visual Cues: Incorporate visual descriptions or cues to guide the viewer's imagination.
- Use Engaging Language: Keep the tone conversational and engaging to hold the viewer’s attention.
- Simple Language: Ensure the language is simple and accessible, suitable for a 13-year-old.
- Length: Make the paragraph as comprehensive as possible.
- Banned words: vibrant, delve, unravel, journey, multifaceted, bustling, landscape, testament, realm, embark, crucial, vital, ensure.
"""
    
    system = """You are an expert in creating engaging and comprehensive YouTube video scripts. You will write the content of a video script segment based on the provided overall outline and paragraph title title."""
    
    human = """### Overall video outline:\n {outline}\n\n### Context:\n{context}\n\n\n### Based on the provided context, write a comprehensive paragraph for the video script about '{p_title}'\n\n{style}\n\n{schema}"""


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


class SearchQueryClassifier:
    schema = """
    ### Instructions
    Generate the classification for the search query adhering to the following JSON schema:
    {
        "search_type": {
            "type": "string",
            "description": "The recommended search type for the query. Can be 'news' or 'regular'."
        }
        "required": ["search_type"]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are an expert in search query classification. You will determine whether a query should be searched in the news results or in the regular search to obtain the best results."""
    
    human = """### Query details:\n {query}\n\n### Based on the provided query and context, determine whether to search for '{query}' in 'news' results or 'regular' search results. Provide a clear recommendation.\n\n{schema}"""


def get_search_type(query: str):
    search_type = model.invoke([
        ("system", SearchQueryClassifier.system),
        ("human", SearchQueryClassifier.human.format(query=query, schema=SearchQueryClassifier.schema)),
    ]).content
    search_type = json_fixer(search_type)
    search_type = search_type.get("search_type", search_type)
    return search_type


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
        search_type = get_search_type(generated_query)
        print(f"\t[H2] Searching for {generated_query}")
        
        h2_results = search_google(generated_query, hl=hl, gl=gl, search_type=search_type)
        h2['web_search'] = {
            "generated_query": generated_query,
            "results": h2_results if "organic_results" in h2_results else {"organic_results": h2_results}
        }

        if h2.get('h3_titles'):
            for h3 in h2['h3_titles']:
                h3_title_w_hierarchy = f"{h2['title']} -> {h3['title']}"
                llm_response = model.invoke([
                    ("system", SearchQueryGenerator.system),
                    ("human", SearchQueryGenerator.human.format(paragraph_title=h3_title_w_hierarchy, schema=SearchQueryGenerator.schema)),
                ]).content
                    
                generated_query = json_fixer(llm_response)
                generated_query = generated_query.get("query", generated_query)
                if isinstance(generated_query, dict):
                    generated_query = " ".join([generated_query[key] for key in generated_query.keys()])
                search_type = get_search_type(generated_query)
                print(f"\t\t[H3] Searching for {generated_query}")
                
                h3_results = search_google(generated_query, hl=hl, gl=gl, search_type=search_type)
                h3['web_search'] = {
                    "generated_query": generated_query,
                    "results": h3_results if "organic_results" in h3_results else {"organic_results": h3_results}
                }
    state["outline"] = outline_copy
    return state


def write_paragraph(title:str, outline:dict, vectorstore, n_sources:int, generate_yt_script:bool):
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
    
    if generate_yt_script:
        llm_response = model.invoke([
            ("system", VideoScriptSegmentWriter.system),
            ("human", VideoScriptSegmentWriter.human.format(
                outline=formatted_outline, 
                context=context,
                p_title=title,
                style=VideoScriptSegmentWriter.style_instructions,
                schema=VideoScriptSegmentWriter.schema
            )),
        ]).content
                        
        script = json_fixer(llm_response)
        script = script.get("paragraph", script)
    else:
        script = None
    
    return content, sources, script


def fill_outline_paragraphs(outline: dict, vectorstore: Chroma, n_sources: int, generate_yt_script:bool) -> dict:
    print(Fore.GREEN + f'[+] Filling outline paragrpahs...')
    outline_copy = outline.copy()  # copy outline so I keep the empty version

    for h2 in outline_copy['h2_titles']:
        print(h2['title'])
        h2_content, h2_sources, h2_script = write_paragraph(title=h2['title'], outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources, generate_yt_script=generate_yt_script)
        h2['content'] = h2_content
        h2['sources'] = h2_sources
        h2['yt_script'] = h2_script

        if 'h3_titles' in h2:
            for h3 in h2['h3_titles']:
                print(h3['title'])
                h3_content, h3_sources, h3_script = write_paragraph(title=h3['title'], outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources, generate_yt_script=generate_yt_script)
                h3['content'] = h3_content
                h3['sources'] = h3_sources
                h3['yt_script'] = h3_script

    return outline_copy


@check_and_load_filled_outline_state
def get_filled_outline(state):
    print(Fore.GREEN + f'[+] Starting filling outline with content...')
    vectorstore = get_vectore_store(state)
    fill_vectorstore(state["outline"], vectorstore)
    filled_outline = fill_outline_paragraphs(state["outline"], vectorstore=vectorstore, n_sources=N_SOURCES_FROM_VECTORSTORE, generate_yt_script=state["generate_yt_script"])
    
    state["outline"] = filled_outline
    return state