# from refiner import make_article
import json
from trend import ask_trend, get_news_for_trend
from topics import get_topics
from generate_keywords import get_primary_keyword, get_secondary_keywords, get_longtail_keywords
from outline import get_outline
from vectorestore import get_vectore_store_dir

    

def main():
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
        "secondary_keywords": [],
        "longtail_keywords": [],
        "outline": {},
        "vectore_store": {
            "name": "",
            "directory": ""
        }
    }
    
    state = ask_trend(state)
    state = get_news_for_trend(state)
    state = get_topics(state)
    state = get_primary_keyword(state)
    state = get_secondary_keywords(state)
    state = get_longtail_keywords(state)
    state = get_outline(state)
    state = get_vectore_store_dir(state)
    print(state)
    return state


if __name__ == "__main__":
    main()