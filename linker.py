from typing import Dict, List, Any
from colorama import Fore
from sentence_transformers import SentenceTransformer, util
import torch
from langchain_core.documents import Document
from utililty import nlp



sent_transformer_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# Function to extract key phrases using spaCy
def extract_key_phrases(text: str) -> List[str]:
    doc = nlp(text)
    return [chunk.text for chunk in doc.noun_chunks]


def create_links_in_paragraph(paragraph: str, matches: List[Dict[str, Any]]) -> str:
    for match in matches:
        par_phrase = f" {match['par_phrase']} "
        url = match['best_match']['url']
        markdown_link = f"[{par_phrase.strip()}]({url})"
        if markdown_link in paragraph:
            continue
        else:
            if url not in paragraph:
                paragraph = paragraph.replace(par_phrase.strip(), f" {markdown_link} ", 1)

    return paragraph


def get_most_similar_element(element:str, list_of_elements:list):

    # Initialize the model

    # List of sentences (corpus)


    # Generate embeddings for the corpus
    corpus_embeddings = sent_transformer_model.encode(list_of_elements, convert_to_tensor=True)

    # Generate embedding for the query
    query_embedding = sent_transformer_model.encode(element, convert_to_tensor=True)

    # Compute cosine similarity between the query embedding and corpus embeddings
    cosine_scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)

    # Get the most similar sentence
    top_score, top_idx = torch.max(cosine_scores, dim=1)

    # Print the most similar sentence and its score
    most_similar_sentence = list_of_elements[top_idx.item()]
    most_similar_score = top_score.item()

    if most_similar_score > 0.50:
        if len(most_similar_sentence) > 5:
            print(element)
            print(f"Most similar sentence: '{most_similar_sentence.strip()}' {type(most_similar_sentence)}")
            print(f"(Score: {most_similar_score:.4f})\n-------\n")
    return most_similar_sentence, most_similar_score



def map_phrases_to_sources(paragraph: str, sources: List[dict], similarity_threshold=0.5):
    paragraph_sentences = paragraph.split(".")

    all_sources_sentences = []
    for s in sources:
        sentences = s["page_content"].split(".")
        all_sources_sentences.extend(sentences)
    
    mapping= []
    for s in paragraph_sentences:
        if len(s) > 2:
            most_similar_source_sentence, score = get_most_similar_element(s, all_sources_sentences)
            if score >= similarity_threshold:
                mapping.append({"par_sent": s, "most_similar": most_similar_source_sentence, "score": score})
    
    return mapping


def get_source_by_string(string:str, sources:List[dict]) -> Document:
    for s in sources:
        if string.lower() in s["page_content"].lower():
            return s
        

def add_links_to_outline(state:dict, similarity_threshold=0.5) -> dict:
    print(Fore.LIGHTBLUE_EX + f'[+] Adding links to article...')
    outline_copy = state["outline"]  # copy outline so i keep the empty version
    for h2 in outline_copy["h2_titles"]:
        print(Fore.LIGHTBLUE_EX + f'\t[H2] Adding links to {h2["title"]}...')
        mapping = map_phrases_to_sources(h2["content"], h2["sources"], similarity_threshold=similarity_threshold)
        matches = []
        for m in mapping:
            par_sent_phrases = extract_key_phrases(m["par_sent"])
            most_similar_source_phrase = m["most_similar"]
            noun_phrase_for_link, score = get_most_similar_element(most_similar_source_phrase, par_sent_phrases)
            source = get_source_by_string(most_similar_source_phrase, h2["sources"])
            if source: # come fa a non esserci source? #TODO
                matches.append({"par_phrase": noun_phrase_for_link, "best_match": {"url": source["metadata"]["url"]}})
        h2["content"] = create_links_in_paragraph(h2["content"], matches)

        if h2["h3_titles"]:
            for h3 in h2["h3_titles"]:
                print(Fore.LIGHTBLUE_EX + f'\t[H3] Adding links to {h3["title"]}...')
                mapping = map_phrases_to_sources(h3["content"], h3["sources"], similarity_threshold=similarity_threshold)
                matches = []
                for m in mapping:
                    par_sent_phrases = extract_key_phrases(m["par_sent"])
                    most_similar_source_phrase = m["most_similar"]
                    noun_phrase_for_link, score = get_most_similar_element(most_similar_source_phrase, par_sent_phrases)
                    source = get_source_by_string(most_similar_source_phrase, h3["sources"])
                    if source:
                        matches.append({"par_phrase": noun_phrase_for_link, "best_match": {"url": source["metadata"]["url"]}})
                h3["content"] = create_links_in_paragraph(h3["content"], matches)
    state["outline"] = outline_copy
    return state


# outline_with_links = add_link_to_outline(filled_outline)