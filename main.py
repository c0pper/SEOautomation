# from refiner import make_article
import json
from random import randint
from image_scraping import scrape_freepik
from trend import ask_trend, get_news_for_trend
from topics import get_topics
from generate_keywords import get_primary_keyword, get_secondary_keywords, get_longtail_keywords
from outline import get_outline
from vectorestore import get_vectore_store_dir
from parapgraphs import search_web_for_outline_paragraphs, get_filled_outline
from linker import add_links_to_outline
from bold_words import add_bolds_to_outline
from refiner import get_intro, get_conclusion, get_title, finalize_article
from image_generation import get_sd_prompt, generate_and_save_images
from utililty import create_wordpress_post


    

def main():
    state = {
        "tmp_name": "",
        "img_mode": "",
        "chosen_trend": {
            "name": "where's my phone google",
            "processed_news": [],
        },
        "topic": {
            'name': '', 
            'articles': []
        },
        "primary_keyword": "",
        "secondary_keywords": [],
        "longtail_keywords": [],
        "outline": {},
        "vectore_store": {
            "name": "",
            "directory": ""
        },
        "article_directory": "",
        "introduction": "",
        "conclusion": {},
        "article_title": "",
        "full_article": "",
        "sd_prompt": "",
        "img_query": "",
        "article_images": []
    }
    
    state = ask_trend(state)
    state = get_news_for_trend(state)
    state = get_topics(state)
    state = get_primary_keyword(state)
    state = get_secondary_keywords(state)
    state = get_longtail_keywords(state)
    state = get_outline(state)
    state = get_vectore_store_dir(state)
    state = search_web_for_outline_paragraphs(state, gl="us", hl="en")
    state = get_filled_outline(state)
    state = add_links_to_outline(state)
    state = add_bolds_to_outline(state, percent_bold_words_per_para=50)
    state = get_intro(state)
    state = get_conclusion(state)
    state = get_title(state)
    if state["img_mode"] == "gen":
        state = get_sd_prompt(state)
        state = generate_and_save_images(
            state, 
            workflow=json.load(open("image_generator_api.json", "r")), 
            seed=randint(0, 10000),
            steps=6,
            batch_size=4
        )
    else:
        state = scrape_freepik(state)
    state = finalize_article(state)
    return state


if __name__ == "__main__":
    state = main()
    create_wordpress_post(state["article_title"], state["full_article"], tags=None, categories=None)