# from refiner import make_article
import json
from trend import ask_trend, get_news_for_trend
from topics import get_topics
    

def main():
    state = {
        "chosen_trend": {
            "name": "",
            "processed_news": [],
        },
        "topic": ""
    }
    
    state = ask_trend(state)
    state = get_news_for_trend(state)
    state = get_topics(state)
    print(state)
    return state


if __name__ == "__main__":
    main()