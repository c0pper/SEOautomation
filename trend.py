import serpapi
from utililty import check_and_load_state, search_google, text_getter, sanitize_string, save_state
import os
from colorama import Fore
from parapgraphs import get_search_type

def get_trends(geo:str="IT"):
    params = {
    "api_key": os.getenv("SERP_API_KEY"),
    "engine": "google_trends_trending_now",
    "frequency": "realtime",
    "geo": geo,
    "hl": "en",
    # "cat": "t"
    }

    search = serpapi.GoogleSearch(params)
    search = search.get_dict()
    return search


def ask_trend(state, geo:str="US"):
    print(Fore.LIGHTBLUE_EX + '[+] Asking trend')
    # trends = get_trends(geo)
    # try:
    #     searches = trends["daily_searches"][0]["searches"]
    #     for idx, s in enumerate(searches):
    #         print(f"{idx}. Query: {s['query']} (Traffic: {s['traffic']})")
    #         for art in s["articles"]:
    #             print(f"\tArt title: {art['title']}")
    #             print(f"\tArt snippet: {art['snippet']}")
    #             print(f"\tArt url: {art['link']}")
    #             print(f"\tArt source: {art['source']}")
    #             print(f"\t--------------------------------")

    #     selected_index = int(input("Please select a query by typing the number corresponding to the index: "))
    #     chosen_trend = searches[selected_index]
    #     print(f"\nYou selected query: {chosen_trend['query']} (Traffic: {chosen_trend['traffic']})")
    # except KeyError:
    #     searches = trends["realtime_searches"]
    #     for idx, s in enumerate(searches[:15]):
    #         query = ', '.join(s['queries'])
    #         print(f"{idx}. Query: {query}")
    #         for art in s["articles"]:
    #             print(f"\tArt title: {art['title']}")
    #             print(f"\tArt snippet: {art['snippet']}")
    #             print(f"\tArt url: {art['link']}")
    #             print(f"\tArt source: {art['source']}")
    #             print(f"\t--------------------------------")
                
    #     selected_index = int(input("Please select a query by typing the number corresponding to the index: "))
    #     chosen_trend = searches[selected_index]
    #     chosen_trend_query =  ", ".join(chosen_trend['queries'][:4])
    #     print(f"\nYou selected query: {chosen_trend_query}")


    # state["chosen_trend"]["name"] = chosen_trend_query
    # return state
    trend = input("Input a trend on which to write article: ")
    state["chosen_trend"]["name"] = trend
    state["tmp_name"] = "tmp_" + sanitize_string(trend)+".json"
    return state


@check_and_load_state(["chosen_trend.processed_news"])
def get_news_for_trend(state):
    trend = state["chosen_trend"]["name"]
    print(Fore.LIGHTBLUE_EX + f'[+] Getting news for trend {trend}')
    # news_results = search_google(trend, search_type="nws")["news_results"]
    search_type = get_search_type(trend)
    results = search_google(trend, search_type=search_type)
    if not results:
        raise ValueError(f"No news returned for trend {trend}")
    
    processed_news_results = [text_getter(n["link"]) for n in results if "youtube" not in n["link"]]
    processed_news_results = [list(pn)[0] for pn in processed_news_results]
    processed_news_results = [pn for pn in processed_news_results if isinstance(pn, dict)]
    processed_news_results = [pn for pn in processed_news_results if pn["text"] != "Unable to reach website."]
    
    state["chosen_trend"]["processed_news"] = processed_news_results
    state["chosen_trend"]["search_type"] = search_type
    return state


if __name__ == "__main__":
    state = {"chosen_trend": {}}
    state = ask_trend(state)
    state = get_news_for_trend(state)
    print(state)