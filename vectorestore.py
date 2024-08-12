from colorama import Fore
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import re
import os
from hashlib import md5
from utililty import check_and_load_state, text_getter


text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)

def split_docs(docs):
    splitted_docs = []
    for d in docs:
        splits = text_splitter.split_text(d.page_content)
        splitted_d = [Document(page_content=spl, metadata={"title": d.metadata["title"], "url": d.metadata["url"], "query": d.metadata["query"]}) for spl in splits]
        for sd in splitted_d:
            if len(sd.page_content) > 50:  # scarto i titoli
                splitted_docs.append(sd)
    return splitted_docs


@check_and_load_state(["vectore_store.name", "vectore_store.directory"])
def get_vectore_store_dir(state):
    vectorstore_trend_name = state["topic"]["name"].lower().replace(" ", "_")
    hash_id = md5(vectorstore_trend_name.encode()).hexdigest()
    vectorstore_id = re.sub(r'[^A-Za-z0-9_]+', '', vectorstore_trend_name) + "_" + hash_id
    persist_directory=f"vectorstores/{vectorstore_id}"
    
    state["vectore_store"]["name"] = vectorstore_trend_name
    state["vectore_store"]["directory"] = persist_directory
    return state



def organic_results_to_splitted_docs(web_search:dict) -> list:
    urls = [res["link"] for res in web_search["results"]["organic_results"]]
    docs = [list(text_getter(url))[0] for url in urls]
    docs = [d for d in docs if isinstance(d, dict)]
    docs = [Document(page_content=d["text"], metadata={'title':d["title"], 'url': d["url"], 'query': web_search["generated_query"]}) for d in docs if d and "youtube" not in d['url']]
    splitted_docs = split_docs(docs)
    return splitted_docs


def get_vectore_store(state):
    persist_directory = state["vectore_store"]["directory"]
    if not os.path.exists(persist_directory):
        print("Initializing vectorstore from scratch")
        vectorstore = Chroma.from_documents([Document(page_content="")], OpenAIEmbeddings(), persist_directory=persist_directory)
    else:
        print("Loading vectorstore from storage")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=OpenAIEmbeddings())

    return vectorstore


def fill_vectorstore(outline_with_searches:dict, vectorstore: Chroma):
    n_doc = len(vectorstore.get()['documents'])
    maximum_batch_size = 166
    if n_doc < 2:
        print(Fore.LIGHTBLUE_EX + f'[+] Populating vectorstore...')
        outline_copy = outline_with_searches.copy()  # copy outline so i keep the empty version
        total_titles = len(outline_copy["h2_titles"])
        
        for index, h2 in enumerate(outline_copy.get("h2_titles", [])):
            print(f"\t[+] Adding docs for ## {h2['title']} ({index + 1}/{total_titles})...")
            splitted_docs = organic_results_to_splitted_docs(h2["web_search"])
            vectorstore.add_documents(splitted_docs if len(splitted_docs) < maximum_batch_size else splitted_docs[:maximum_batch_size])

            if h2.get('h3_titles'):
                for h3 in h2["h3_titles"]:
                    print(f"\t\t[+] Adding docs for ### {h3['title']}...")
                    splitted_docs = organic_results_to_splitted_docs(h3["web_search"])
                    vectorstore.add_documents(splitted_docs if len(splitted_docs) < maximum_batch_size else splitted_docs[:maximum_batch_size])
    else:
        print(Fore.LIGHTBLUE_EX + f'[+] Skipping vectorstore population... already found {n_doc} documents')