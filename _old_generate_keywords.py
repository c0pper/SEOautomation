

from typing import List
from pydantic import BaseModel, Field
from topics import chosen_topic
from utililty import use_component
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate



model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

class PrimaryKeyword(BaseModel):
    """ primary keyword is the central term or phrase that best represents the main topic of a piece of content."""

    keyword: str = Field(description="The primary keyword")

class PrimaryKeywordGenerator(BaseModel):
    # """A component responsible for generating a primary keyword for an article starting from a list of related articles."""

    primary_keyword: PrimaryKeyword = Field(
        description="The generated primary keyword"
    )
    
primary_keyword_gen_system = """You are a primary keyword generator. You will generate a primary keyword to guide the writing of an SEO-efficient article starting from a list of articles."""
primary_keyword_gen_human = """Articles:\n\n {articles}"""
primary_keyword_gen_template = ChatPromptTemplate.from_messages(
    [
        ("system", primary_keyword_gen_system),
        ("human", primary_keyword_gen_human)
    ]
)
  

class SecondaryKeyword(BaseModel):
    """A secondary keyword is a term or phrase that is related to the primary keyword and supports the main topic of your content. It's used to cover subtopics, provide additional context, and enhance the overall relevancy of the content. While they are not the main focus of the article, secondary keywords help to capture additional search traffic and improve the depth and breadth of the content."""

    keyword: str = Field(description="The secondary keyword")

class SecondaryKeywordGenerator(BaseModel):
    """A component responsible for generating a list of secondary keywords starting from a primary keyword and a list of related articles."""

    secondary_keywords: List[SecondaryKeyword] = Field(
        description="A list of generated secondary keywords."
    )

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You are a secondary keyword generator. You will generate a list of secondary keywords to guide the writing of an SEO-efficient article based on the provided primary keyword and a list of related articles.\n\n Example: For an article with the primary keyword "how to bake a cake," potential secondary keywords could be:\n    "cake baking tips"\n    "best cake baking recipes"\n    "cake baking ingredients"\n    "cake baking tools"\n    "common cake baking mistakes.\n\nAVOID generic keywords such as "Obama news", be specific."""
    
    @classmethod
    def get_user_prompt(cls):
        return """Primary keyword: {kw}\n\nRelated articles:\n{articles}\n\n###Additional instructions###\n AVOID any generic keywords such as 'Obama news', be specific."""
    
    @classmethod
    def remove_news(cls, kw: list):
        for k in kw.secondary_keywords:
            if "news" in k.keyword:
                kw.secondary_keywords.remove(k)
        return kw
    

class LongtailKeyword(BaseModel):
    """A longtail keyword is a keyword that is not in the top 10 search results."""

    keyword: str = Field(description="The longtail keyword")


class LongtailKeywordsGenerator(BaseModel):
    """A component responsible for generating longtail keywords starting from a primary keyword, a list of secondary keywords and a list of related articles. """

    longtail_keywords: list[LongtailKeyword] = Field(
        description="A list of generated longtail keywords."
    )

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You will generate longtail keywords starting from a primary keyword, a list of secondary keywords and a list of related articles. For example, if the primary keyword was 'bake a cake,' potential long-tail keywords could be:\n\n    'how to bake a chocolate cake from scratch'\n    'easy homemade vanilla cake recipe'\n    'gluten-free cake baking tips'\n    'best tools for cake baking beginners'\n    'how to bake a moist red velvet cake'"""
    
    @classmethod
    def get_user_prompt(cls):
        return """Primary keyword: {kw}\n\Secondary keywords: {skw}\n\nRelated articles:\n{articles}"""
    
    def remove_dups(self, secondary_kws: SecondaryKeywordGenerator) -> 'LongtailKeywordsGenerator':
        sec_keys = [k.keyword for k in secondary_kws.secondary_keywords]
        for lt in self.longtail_keywords:
            if lt.keyword in sec_keys:
                self.longtail_keywords.remove(lt)
        return self
    

pk_articles = chosen_topic.articles
formatted_articles = "\n----\n".join([f'Title: {a.title}\nSnippet: {a.snippet}' for a in pk_articles])
structured_llm = model.with_structured_output(PrimaryKeywordGenerator)
generator = primary_keyword_gen_template | structured_llm
generated_topics = generator.invoke({"articles": formatted_articles})

pk = use_component(PrimaryKeywordGenerator, {"articles": formatted_articles}, human_prompt=pk_human)
print(f"Primary keyword:{pk}")

sec_keys = use_component(
    SecondaryKeywordGenerator, 
    {"kw": pk.primary_keyword.keyword, "articles": formatted_articles}
)
sec_keys = SecondaryKeywordGenerator.remove_news(sec_keys)
sec_keys_list = [k.keyword for k in sec_keys.secondary_keywords]
print(sec_keys)
print(f'Secondary keywords{"; ".join(sec_keys_list)}')

longtail_keys = use_component(
    LongtailKeywordsGenerator, 
    {"kw": pk.primary_keyword.keyword, "skw": "; ".join(sec_keys_list), "articles": formatted_articles}
)
longtail_keys = longtail_keys.remove_dups(sec_keys)

