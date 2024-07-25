from outline import OutlineGenerator
from linker import outline_with_links
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


def create_bolds_in_paragraph(paragraph: str, percent_bold_words_per_para:int=4, language="en") -> str:
    n_keywords = int((len(paragraph.split()) * percent_bold_words_per_para) / 100)
    max_ngram_size = 3
    deduplication_threshold = 0.1
    custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=n_keywords, features=None)

    para_keywords = custom_kw_extractor.extract_keywords(paragraph)
    for kw in para_keywords:
        word = kw[0]
        if contains_noun(word):
            bold_word = f"**{word}**"
            paragraph = paragraph.replace(word.strip(), bold_word, 1)

    return paragraph



def add_bolds_to_outline(outline: OutlineGenerator, percent_bold_words_per_para=10) -> OutlineGenerator:
    outline_copy = outline  # copy outline so i keep the empty version
    for h2 in outline_copy.h2_titles:
        h2.content.paragraph = create_bolds_in_paragraph(h2.content.paragraph, percent_bold_words_per_para)

        if h2.h3_titles:
            for h3 in h2.h3_titles:
                h3.content.paragraph = create_bolds_in_paragraph(h3.content.paragraph, percent_bold_words_per_para)
    return outline_copy


outline_w_bolds = add_bolds_to_outline(outline_with_links, percent_bold_words_per_para=50)