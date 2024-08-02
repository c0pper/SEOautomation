# from refiner import make_article
import json
from trend import ask_trend, get_news_for_trend
from topics import get_topics
from generate_keywords import get_primary_keyword, get_secondary_keywords, get_longtail_keywords
from outline import get_outline
from vectorestore import get_vectore_store_dir
from parapgraphs import search_web_for_outline_paragraphs, get_filled_outline
from linker import add_links_to_outline
from bold_words import add_bolds_to_outline
from refiner import get_intro, get_conclusion, get_title, finalize_article


    

def main():
    state = {
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
        "introduction": "",
        "conclusion": {},
        "article_title": "",
        "full_article": ""
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
    state = finalize_article(state)
    print(state)
    return state


if __name__ == "__main__":
    main()