import json
import os
import re
from typing import List, Union
from colorama import Fore
from pydantic import BaseModel, Field
from outline import OutlineGenerator
from parapgraphs import style_instructions
from utililty import json_fixer, use_component, model
from outline import ParagraphWriter


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



def stitch_h2_paragraphs(outline: dict, middle_image:str) -> str:
    article_body = ""
    h2_titles = outline["h2_titles"]
    total_h2 = len(h2_titles)

    for i, h2 in enumerate(h2_titles):
        # If this is the last H2, add the image before it
        if i == total_h2 - 1:
            article_body += f"{middle_image}\n\n"
        # Add H2 title
        article_body += f"{to_wp_tags(h2['title'], 'h2')}\n"
        # Add H2 content
        article_body += f"{to_wp_tags(h2['content'], 'paragraph')}\n\n"
        # If there are H3 titles, add them
        if h2["h3_titles"]:
            for h3 in h2["h3_titles"]:
                # Add H3 title
                article_body += f"{to_wp_tags(h3['title'], 'h3')}\n"
                # Add H3 content
                article_body += f"{to_wp_tags(h3['content'], 'paragraph')}\n\n"

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


def get_article_directory(title):
    sanitized_name = re.sub(r'[^A-Za-z0-9 ]+', '', title).lower().replace(" ", "_")
    directory = f"articles/{"_".join(sanitized_name.split("_")[:5])}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


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
    
    directory = get_article_directory(state["article_title"])
    state["article_directory"] = directory
    
    return state


def save_article_as_markdown(article:str, article_directory):
    filename = article_directory.split("/")[-1]
    file_path = os.path.join(article_directory, filename+".md")
    
    # Write the article content to the file in markdown format
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(article)
    
    print(f"Article saved at {file_path}")


def save_article_state_as_json(state:dict, article_directory): 
    filename = article_directory.split("/")[-1]   
    file_path = os.path.join(article_directory, filename+".json")
    
    # Write the article content to the file in markdown format
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(state, file, indent=4)
    
    print(f"State saved at {file_path}")
    
    
def to_wp_tags(content: Union[List, str], md_attribute, img_id=None, img_width=None) -> str:
    if md_attribute == "h2":
        return f"""<!-- wp:heading -->
<h2 class="wp-block-heading">{content}</h2>
<!-- /wp:heading -->"""

    elif md_attribute == "h3":
        return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{content}</h2>
<!-- /wp:heading -->"""

    elif md_attribute == "paragraph":
        return f"""<!-- wp:paragraph -->
<p>{content}</p>
<!-- /wp:paragraph -->"""

    elif md_attribute == "ul":
        if not isinstance(content, list):
            raise TypeError("Need list for this operation")
        wp_list_open = '<!-- wp:list -->\n<ul class="wp-block-list">'
        wp_list_close = '</ul>\n<!-- /wp:list -->'
        
        list_items = '\n'.join(
            f'<!-- wp:list-item -->\n<li>{keypoint}</li>\n<!-- /wp:list-item -->' 
            for keypoint in content
        )
        
        # Combine everything into the final output
        return f'{wp_list_open}\n{list_items}\n{wp_list_close}'

    elif md_attribute == "image":
        return f"""<!-- wp:image {{"id":{img_id},"sizeSlug":"large","linkDestination":"none"}} -->
<figure class="wp-block-image size-large"><img src="{content}?w={img_width}" alt="" class="wp-image-{img_id}" /></figure>
<!-- /wp:image -->"""


def get_wp_images_snippets(state):
    image1_url = state["article_images"][0].get("URL")
    image2_url = state["article_images"][1].get("URL")
    
    wp_image1 = to_wp_tags(image1_url, "image", state["article_images"][0].get("ID"))
    wp_image2 = to_wp_tags(image2_url, "image", state["article_images"][1].get("ID"))
    return wp_image1, wp_image2


def finalize_article(state):
    print(Fore.GREEN + f'[+] Finalizing article...')
    intro = state["introduction"]
    conclusion = state["conclusion"]
    wp_image1, wp_image2 = get_wp_images_snippets(state)
    article = stitch_h2_paragraphs(state["outline"], middle_image=wp_image2)

    # Add Key points
    if not isinstance(conclusion['keypoints'], list):
        conclusion['keypoints'] = conclusion['keypoints'].split(",")
    keypoints = f"{to_wp_tags('Key points', 'h2')}\n{to_wp_tags(conclusion['keypoints'], 'ul')}\n\n"

    article_intro_concl = wp_image1 + "\n\n" + keypoints + "\n\n" + to_wp_tags(intro, "paragraph") + "\n\n" + article + f"\n\n{to_wp_tags('Conclusion', 'h2')}\n" + to_wp_tags(conclusion["conclusion"], "paragraph")
    article_intro_concl = re.sub(' +', ' ', article_intro_concl)
    print(article_intro_concl)
    
    save_article_as_markdown(article_intro_concl, state["article_directory"])
    save_article_state_as_json(article_intro_concl, state["article_directory"])
    
    state["full_article"] = article_intro_concl
    
    return state
