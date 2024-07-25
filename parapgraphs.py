from pydantic import BaseModel, Field
from outline import OutlineGenerator, ParagraphWriter
from utililty import search_google, use_component
from outline import empty_outline
from vectorestore import vectorstore, fill_vectorstore

style_instructions = """### Writing style instructions ###
- Use Short Sentences: Keep sentences short and to the point.
- Where applicable, use bullet points, and numbered lists for readability.
- Active Voice: Use active voice where possible.
- Transitional Words: Use words like “therefore,” “however,” and “moreover” to improve flow.
- Make sure a 13 yeard old could understand your writing.
- The perfect paragraph should be between 50 and 150 words long.
- Banned words: vibrant, delve, unravel, journey, multifaceted, bustling, landscape, testament, realm, embark, crucial, vital, ensure.
"""


class SearchQueryGenerator(BaseModel):
    """Generate an search query to be used for finding information on the web about a topic."""

    query:str = Field(description="The generated search query")

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You are SearchQueryGenerator, a specialized model designed to generate effective and relevant search queries for finding information on the web about a given topic. Your primary objective is to craft a search query that yield the most pertinent and comprehensive results, facilitating the discovery of valuable information. Below are your guidelines and responsibilities:\n\n- Identify key elements, related subtopics, and potential search keywords that encapsulate the topic comprehensively.\n- Generate a clear, concise, and targeted search query.\n- Ensure the query is specific enough to filter out irrelevant information yet broad enough to capture all relevant data.\n- """
    
    @classmethod
    def get_user_prompt(cls):
        return """Topic: {paragraph_title}"""
    

def search_web_for_outline_paragraphs(outline:OutlineGenerator, gl="us", hl="en") -> OutlineGenerator:
    total_h2 = len(outline.h2_titles)
    total_h3 = sum([len(h2.h3_titles) for h2 in outline.h2_titles if h2.h3_titles])
    print(f"[+] Preparing to make {total_h3+total_h2} searches")

    outline_copy = outline  # copy outline so i keep the empty version
    for h2 in outline_copy.h2_titles:
        generated_query = use_component(SearchQueryGenerator, {"paragraph_title": h2.title}).query
        h2_results = search_google(generated_query, hl=hl, gl=gl)
        h2.web_search = {
            "generated_query": generated_query,
            "results": h2_results
        }

        if h2.h3_titles:
            for h3 in h2.h3_titles:
                generated_query = use_component(SearchQueryGenerator, {"paragraph_title": h3.title}).query
                h3_results = search_google(generated_query, hl=hl, gl=gl)
                h3.web_search = {
                    "generated_query": generated_query,
                    "results": h3_results
        }
    return outline_copy

def write_paragraph(title, outline, vectorstore, n_sources):
    sources = vectorstore.similarity_search(title, k=n_sources)
    print(f"sources l: {[len(d.page_content) for d in sources]}")
    context = "\n\n-----\n\n".join([d.page_content for d in sources])
    content = use_component(
        component_cls=ParagraphWriter, 
        input_dict={"outline": outline.print_formatted_outline(), "context": context, "p_title": title, "style": style_instructions}
    )
    print(f"len input dict: {len(outline.print_formatted_outline()) + len(context) + len(title) + len(style_instructions)}")
    return content, sources


def fill_outline_paragraphs(outline:OutlineGenerator, vectorstore:Chroma, n_sources:int) -> OutlineGenerator:
    outline_copy = outline  # copy outline so i keep the empty version
    for h2 in outline_copy.h2_titles:
        print(h2.title)
        h2_content, h2_sources = write_paragraph(title=h2.title, outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources)
        # h2_content = ParagraphWriter(paragraph=lorem.paragraph())
        h2.content = h2_content
        h2.sources = h2_sources
        # print("\n\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        # print(outline_copy.print_formatted_outline())

        if h2.h3_titles:
            for h3 in h2.h3_titles:
                print(h3.title)
                h3_content, h3_sources = write_paragraph(title=h3.title, outline=outline_copy, vectorstore=vectorstore, n_sources=n_sources)
                # h3_content = ParagraphWriter(paragraph=lorem.paragraph())
                h3.content = h3_content
                h3.sources = h3_sources
    return outline_copy




outline_with_searches = search_web_for_outline_paragraphs(empty_outline)
fill_vectorstore(outline_with_searches)
filled_outline = fill_outline_paragraphs(outline_with_searches, vectorstore=vectorstore, n_sources=4)