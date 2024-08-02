import os
import re
from colorama import Fore
from pydantic import BaseModel, Field
from outline import OutlineGenerator
from parapgraphs import style_instructions
from utililty import json_fixer, use_component, model
from outline import ParagraphWriter


# class IntroductionWriter(BaseModel):
#     """Component responsible for writing the article introduction."""

#     introduction:str = Field(description="The written content of the introduction based on a provided outline and primary keyword")

#     @classmethod
#     def get_system_prompt(cls) -> str:
#         return """You are IntroductionWriter, a specialized model designed to craft compelling and informative introductions based on a provided outline and primary keyword. Your primary objective is to create introductions that engage the reader, provide a clear overview, and set the context for the topic being discussed. Below are your guidelines and responsibilities:

#     Engagement:
#         Begin with a captivating opening sentence to grab the reader's attention.
#         Use engaging language to maintain reader interest throughout the introduction.

#     Clarity and Precision:
#         Clearly state the main topic and its significance.
#         Provide a concise and accurate summary of what will be covered, ensuring the reader understands the scope and importance of the topic.

#     Contextualization:
#         Offer necessary background information to set the context.
#         Highlight key points, relevant data, or significant issues related to the topic.

#     Structure:
#         Follow a logical structure, starting from a broad introduction and narrowing down to the specifics.
#         Ensure smooth transitions between sentences and ideas to maintain coherence.
        
#     Search Engine Optimization:
#         Very important: clearly mention the primary keyword of the article"""
    
#     @classmethod
#     def get_user_prompt(cls):
#         return """Overall article outline: {outline}\n\nPrimary keyword:\n{p_k}\n\n{style}"""
class IntroductionWriter:
    schema = """
    ### Instructions
    Based on the provided outline and primary keyword, write an introduction adhering to the following JSON schema:
    {
        "introduction": {
            "type": "string",
            "description": "The written content of the introduction based on a provided outline and primary keyword"
        }
        "required": ["introduction"]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are IntroductionWriter, a specialized model designed to craft compelling and informative introductions based on a provided outline and primary keyword. Your primary objective is to create introductions that engage the reader, provide a clear overview, and set the context for the topic being discussed. Below are your guidelines and responsibilities:

    Engagement:
        Begin with a captivating opening sentence to grab the reader's attention.
        Use engaging language to maintain reader interest throughout the introduction.

    Clarity and Precision:
        Clearly state the main topic and its significance.
        Provide a concise and accurate summary of what will be covered, ensuring the reader understands the scope and importance of the topic.

    Contextualization:
        Offer necessary background information to set the context.
        Highlight key points, relevant data, or significant issues related to the topic.

    Structure:
        Follow a logical structure, starting from a broad introduction and narrowing down to the specifics.
        Ensure smooth transitions between sentences and ideas to maintain coherence.

    Search Engine Optimization:
        Very important: clearly mention the primary keyword of the article.
    """
    
    human = """Overall article outline: {outline}\n\nPrimary keyword:\n{p_k}\n\n{style}\n\n{schema}"""





# class ConclusionWriter(BaseModel):
#     """Component responsible for writing the article conclusion and keypoints."""

#     conclusion:str = Field(description="The written content of the conclusion based on a provided article outline")
#     keypoints:List[str] = Field(description="A list of keypoint from the article")

#     @classmethod
#     def get_system_prompt(cls) -> str:
#         return """You are ConclusionWriter, a specialized model designed to craft compelling and conclusive endings and keypoints for the provided article outline. Your primary objective is to create conclusions that effectively summarize the content, reinforce the key points, and leave a lasting impression on the reader. Below are your guidelines and responsibilities:

#     Summary:
#         Concisely summarize the main points discussed in the content.
#         Ensure that all significant aspects of the topic are briefly recapped.

#     Reinforcement:
#         Reinforce the importance of the topic and the key arguments presented.
#         Highlight any important takeaways or lessons learned.

#     Closure:
#         Provide a sense of closure to the discussion, ensuring the reader feels the topic has been comprehensively covered.
#         End with a strong closing sentence that leaves a lasting impression.

#     Call to Action (if applicable):
#         If relevant, include a call to action, encouraging the reader to take specific steps or further explore the topic.
#         Ensure the call to action is clear, relevant, and motivating."""
    
#     @classmethod
#     def get_user_prompt(cls):
#         return """Overall article outline: {outline}\n\n{style}"""

class ConclusionWriter:
    schema = """
    ### Instructions
    Based on the provided article outline, write a conclusion and key points adhering to the following JSON schema:
    {
        "conclusion": {
            "type": "string",
            "description": "The written content of the conclusion based on a provided article outline"
        },
        "keypoints": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of key points from the article"
        }
        "required": ["conclusion", "keypoints"],
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are ConclusionWriter, a specialized model designed to craft compelling and conclusive endings and key points for the provided article outline. Your primary objective is to create conclusions that effectively summarize the content, reinforce the key points, and leave a lasting impression on the reader. Below are your guidelines and responsibilities:

    Summary:
        Concisely summarize the main points discussed in the content.
        Ensure that all significant aspects of the topic are briefly recapped.

    Reinforcement:
        Reinforce the importance of the topic and the key arguments presented.
        Highlight any important takeaways or lessons learned.

    Closure:
        Provide a sense of closure to the discussion, ensuring the reader feels the topic has been comprehensively covered.
        End with a strong closing sentence that leaves a lasting impression.

    Call to Action (if applicable):
        If relevant, include a call to action, encouraging the reader to take specific steps or further explore the topic.
        Ensure the call to action is clear, relevant, and motivating.
    """
    
    human = """Overall article outline: {outline}\n\n{style}\n\n{schema}"""



# class ArticleTitleGenerator(BaseModel):
#     """Component responsible for creating compelling, catchy, and SEO-efficient titles for articles based on the article outline and primary, secondary and longtail keywords provided."""

#     title:str = Field(description="The generated article title")

#     @classmethod
#     def get_system_prompt(cls) -> str:
#         return """You are ArticleTitleGenerator, a specialized component designed to create compelling, catchy, and SEO-efficient titles for articles based on the article outline and primary, secondary and longtail keywords provided. Your primary objective is to generate titles that attract readers' attention, accurately represent the article's content, and optimize for search engine visibility. Below are your guidelines and responsibilities:

#     Relevance and Accuracy:
#         Ensure the title accurately reflects the main content and message of the article.
#         Avoid clickbait; the title should set appropriate expectations for the reader.

#     SEO Efficiency:
#         Incorporate relevant keywords naturally to enhance search engine optimization.

#     Catchiness and Engagement:
#         Craft titles that are engaging and intriguing to encourage clicks and shares.
#         Use powerful and emotive language to draw in the reader.

#     Length and Format:
#         Keep the title concise, ideally between 50-60 characters, ensuring it is fully visible in search engine results.
#         Use title case format, capitalizing the first and last words, and all major words in between.

#     Clarity and Readability:
#         Ensure the title is easy to read and understand at a glance.
#         Avoid jargon or complex language that might confuse readers.

#     Uniqueness and Originality:
#         Create unique titles that stand out from similar articles on the same topic.
#         Avoid duplicating titles from other sources or previous articles."""
    
#     @classmethod
#     def get_user_prompt(cls):
#         return """Overall article outline: {outline}


#         Primary keyword: {p_k}
#         Secondary keywords: {sec_k}
#         """

class ArticleTitleGenerator:
    schema = """
    ### Instructions
    Based on the provided article outline and keywords, generate a compelling, catchy, and SEO-efficient article title adhering to the following JSON schema:
    {
        "title": {
            "type": "string",
            "description": "The generated article title"
        }
        "required": ["title"]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are ArticleTitleGenerator, a specialized component designed to create compelling, catchy, and SEO-efficient titles for articles based on the article outline and primary, secondary and longtail keywords provided. Your primary objective is to generate titles that attract readers' attention, accurately represent the article's content, and optimize for search engine visibility. Below are your guidelines and responsibilities:

    Relevance and Accuracy:
        Ensure the title accurately reflects the main content and message of the article.
        Avoid clickbait; the title should set appropriate expectations for the reader.

    SEO Efficiency:
        Incorporate relevant keywords naturally to enhance search engine optimization.

    Catchiness and Engagement:
        Craft titles that are engaging and intriguing to encourage clicks and shares.
        Use powerful and emotive language to draw in the reader.

    Length and Format:
        Keep the title concise, ideally between 50-60 characters, ensuring it is fully visible in search engine results.
        Use title case format, capitalizing the first and last words, and all major words in between.

    Clarity and Readability:
        Ensure the title is easy to read and understand at a glance.
        Avoid jargon or complex language that might confuse readers.

    Uniqueness and Originality:
        Create unique titles that stand out from similar articles on the same topic.
        Avoid duplicating titles from other sources or previous articles.
    """
    
    human = """Overall article outline: {outline}

    Primary keyword: {p_k}
    Secondary keywords: {sec_k}\n\n{style}\n\n{schema}"""



def stitch_h2_paragraphs(outline: dict) -> str:
    article_body = ""

    for h2 in outline["h2_titles"]:
        # Add H2 title
        article_body += f"## {h2['title']}\n"
        # Add H2 content
        article_body += f"{h2['content']}\n\n"
        # If there are H3 titles, add them
        if h2["h3_titles"]:
            for h3 in h2["h3_titles"]:
                # Add H3 title
                article_body += f"### {h3['title']}\n"
                # Add H3 content
                article_body += f"{h3['content']}\n\n"

    return article_body.strip()

def get_intro(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating intro...')
    outline = OutlineGenerator.print_formatted_outline(state["outline"])
    llm_response = model.invoke([
        ("system", IntroductionWriter.system),
        ("human", IntroductionWriter.human.format(outline=outline, p_k=state["primary_keyword"], style=ParagraphWriter.style_instructions, schema=IntroductionWriter.schema)),
    ]).content
        
    introduction = json_fixer(llm_response)
    state["introduction"] = introduction.get("introduction", introduction)
    return state

def get_conclusion(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating conclusion...')
    outline = OutlineGenerator.print_formatted_outline(state["outline"])
    llm_response = model.invoke([
        ("system", ConclusionWriter.system),
        ("human", ConclusionWriter.human.format(outline=outline, style=ParagraphWriter.style_instructions, schema=ConclusionWriter.schema)),
    ]).content
        
    conclusion = json_fixer(llm_response)
    state["conclusion"] = conclusion
    return state

def get_title(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating title...')
    outline = OutlineGenerator.print_formatted_outline(state["outline"])
    llm_response = model.invoke([
        ("system", ArticleTitleGenerator.system),
        ("human", ArticleTitleGenerator.human.format(
            outline=outline, p_k=state["primary_keyword"], 
            sec_k=state["secondary_keywords"], 
            style=ParagraphWriter.style_instructions, 
            schema=ArticleTitleGenerator.schema
            )
        ),
    ]).content
        
    title = json_fixer(llm_response)
    state["article_title"] = title.get("title", title)
    return state


def save_article_as_markdown(article:str, filename:str):
    directory = "articles"
    sanitized_name = re.sub(r'[^A-Za-z0-9 ]+', '', filename).lower().replace(" ", "_")+".md"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, sanitized_name)
    
    # Write the article content to the file in markdown format
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(article)
    
    print(f"Article saved at {file_path}")


def finalize_article(state):
    print(Fore.GREEN + f'[+] Finalizing article...')
    # intro = use_component(IntroductionWriter, {"outline": outline_w_bolds.print_formatted_outline(), "p_k": pk.primary_keyword.keyword, "style": style_instructions})
    # conclusion = use_component(ConclusionWriter, {"outline": outline_w_bolds.print_formatted_outline(), "style": style_instructions})
    # article = stitch_h2_paragraphs(outline_w_bolds)
    # article_title = use_component(ArticleTitleGenerator, {"outline": outline_w_bolds, "p_k": pk.primary_keyword.keyword, "sec_k": sec_keys_list})
    intro = state["introduction"]
    conclusion = state["conclusion"]
    article = stitch_h2_paragraphs(state["outline"])
    article_title = state["article_title"]

    # Add Key points
    nl = "\n"
    if not isinstance(conclusion['keypoints'], list):
        conclusion['keypoints'] = conclusion['keypoints'].split(",")
    keypoints = f"## Key points\n{nl.join(f'- {c}' for c in conclusion['keypoints'])}\n\n"

    article_intro_concl = "# " + article_title + "\n\n" + keypoints + "\n\n" + intro + "\n\n" + article + "\n\n## Conclusion\n" + conclusion["conclusion"]
    print(article_intro_concl)
    save_article_as_markdown(article_intro_concl, f"{article_title}")
    state["full_article"] = article_intro_concl
    return state
