import re
from outline import OutlineGenerator
from utililty import nlp
import yake


def contains_noun(text):
    # Process the text with spaCy
    doc = nlp(text)
    # Check for nouns
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:  # NOUN for common nouns, PROPN for proper nouns
            return True
    return False


def remove_links(paragraph):
    # Regular expression pattern to match HTML links
    link_pattern = r'<a\s+[^>]*>(.*?)<\/a>'
    
    # Substitute the links with their inner text
    cleaned_paragraph = re.sub(link_pattern, r'\1', paragraph)
    
    return cleaned_paragraph


def is_word_in_url(text, word):
    # Regular expression pattern to match URLs
    url_pattern = r'https?://[^\s]+'
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    # Check if the word appears in any of the URLs
    for url in urls:
        if word in url:
            return True
    return False


def create_bolds_in_paragraph(paragraph: str, percent_bold_words_per_para:int=4, language="en") -> str:
    n_keywords = int((len(paragraph.split()) * percent_bold_words_per_para) / 100)
    max_ngram_size = 3
    deduplication_threshold = 0.1
    custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=n_keywords, features=None)

    para_keywords = custom_kw_extractor.extract_keywords(paragraph)
    exclude = ["href", "a", "http", "https"]
    for kw in para_keywords:
        word = kw[0]
        if word not in exclude:
            url_word = is_word_in_url(paragraph, word)
            if contains_noun(word) and not url_word:
                bold_word = f"**{word}**"
                wp_bold_word = f"<strong>{word}</strong>"
                paragraph = paragraph.replace(word.strip(), wp_bold_word, 1)

    return paragraph



def add_bolds_to_outline(state: dict, percent_bold_words_per_para=10) -> dict:
    outline_copy = state["outline"]  # copy outline so i keep the empty version
    for h2 in outline_copy["h2_titles"]:
        h2["content"] = create_bolds_in_paragraph(h2["content"], percent_bold_words_per_para)

        if h2.get("h3_titles"):
            for h3 in h2["h3_titles"]:
                h3["content"] = create_bolds_in_paragraph(h3["content"], percent_bold_words_per_para)
    state["outline"] = outline_copy
    return state


# outline_w_bolds = add_bolds_to_outline(outline_with_links, percent_bold_words_per_para=50)