from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import re
import os
from hashlib import md5
from outline import OutlineGenerator
from topics import chosen_topic
from utililty import text_getter


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



vectorstore_trend_name = chosen_topic.topic.lower().replace(" ", "_")
hash_id = md5(vectorstore_trend_name.encode()).hexdigest()
vectorstore_id = re.sub(r'[^A-Za-z0-9 ]+', '', vectorstore_trend_name) + "_" + hash_id
persist_directory=f"vectorstores/{vectorstore_id}"

if not os.path.exists(persist_directory):
    print("Initializing vectorstore")
    vectorstore = Chroma.from_documents([Document(page_content="")], OpenAIEmbeddings(), persist_directory=persist_directory)
else:
    print("Loading vectorstore")
    vectorstore = Chroma(persist_directory=persist_directory)
vectorstore = Chroma.from_documents([Document(page_content="")], OpenAIEmbeddings(), persist_directory=persist_directory)
vectorstore.get()["ids"]


def organic_results_to_splitted_docs(web_search:dict) -> list:
    urls = [res["link"] for res in web_search["results"]["organic_results"]]
    docs = [list(text_getter(url))[0] for url in urls]
    docs = [d for d in docs if isinstance(d, dict)]
    docs = [Document(page_content=d["text"], metadata={'title':d["title"], 'url': d["url"], 'query': web_search["generated_query"]}) for d in docs if d]
    splitted_docs = split_docs(docs)
    return splitted_docs


def fill_vectorstore(outline_with_searches:OutlineGenerator, vectorstore: Chroma):
    outline_copy = outline_with_searches  # copy outline so i keep the empty version
    total_titles = len(outline_copy.h2_titles)
    
    for index, h2 in enumerate(outline_copy.h2_titles):
        print(f"[+] Adding docs for ## {h2.title} ({index + 1}/{total_titles})...")
        splitted_docs = organic_results_to_splitted_docs(h2.web_search)
        vectorstore.add_documents(splitted_docs)

        if h2.h3_titles:
            for h3 in h2.h3_titles:
                print(f"[+] Adding docs for ### {h3.title}...")
                splitted_docs = organic_results_to_splitted_docs(h3.web_search)
                vectorstore.add_documents(splitted_docs)