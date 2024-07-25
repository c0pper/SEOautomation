from typing import List, Optional, Union
from pydantic import BaseModel, Field
from generate_keywords import pk, sec_keys, sec_keys_list, longtail_keys
from utililty import use_component


class ParagraphWriter(BaseModel):
    """Component responsible for writing a paragraph based on provided information."""

    paragraph:str = Field(description="The written content of the H1 paragraph")

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You are an expert SEO article writer. You will write the content of a paragraph based on the provided overall outline and paragraph title"""
    
    @classmethod
    def get_user_prompt(cls):
        return """Overall article outline: {outline}\n\nContext:\n{context}\n\n\nBased on the provided context, write a 50-100 words paragraph about '{p_title}'\n\n{style}"""
    


class H3Title(BaseModel):
    """A component responsible for generating the title of an H3Title"""
    
    title:str = Field(description="The title of this H2Title")
    content:Union[str|ParagraphWriter|None] = None
    web_search:Union[None|dict] = None
    sources:Union[None|list] = None


class H2Title(BaseModel):
    """A component responsible for generating the title of an H2Title"""
    
    title:str = Field(description="The title of this H2Title")
    content:Union[str|ParagraphWriter|None] = None
    h3_titles:Optional[List[H3Title]] = Field(description="The list of H3Titles that will be generated. They are related to the H2 title.")
    web_search:Union[None|dict] = None
    sources:Union[None|list] = None


class OutlineGenerator(BaseModel):
    """Generate an outline to write an SEO-efficient article starting from a list of secondary keywords and a list of longtail keywords."""

    h2_titles:List[H2Title] = Field(description="The generated H2Titles")

    @classmethod
    def get_system_prompt(cls) -> str:
        return """You are an outline generator. You will generate an outline to write an SEO-efficient article starting from a list of secondary keywords and a list of longtail keywords. H1 is the title of the whole article. You will provide a minimum of 3 H2 Titles and maximum 5 H2 Titles. Leave content empty, will be filled later."""
    
    @classmethod
    def get_user_prompt(cls):
        return """Secondary keywords: {s_kw}\nLongtail Keywords: {l_kw}\n\n###Important instructions###\You will provide a minimum of 3 H2 Titles and maximum 5 H2 Titles. Each H2 title can have a minimum of 0 and a maximum of 2 H3 titles. NEVER include an introduction nor a conclusion. Those will be added later. Add the titles that are the most interesting, current and engaging."""
        
    def print_formatted_outline(self) -> str:
        outline_str = ""
        for h2 in self.h2_titles:
            outline_str += f"## {h2.title}\n"
            try:
                outline_str += f"{h2.content.paragraph}\n\n"
            except AttributeError:
                outline_str += f"To be filled...\n\n"
            if h2.h3_titles:
                for h3 in h2.h3_titles:
                    outline_str += f"\t### {h3.title}\n"
                    try:
                        outline_str += f"{h3.content.paragraph}\n\n"
                    except:
                        outline_str += f"To be filled...\n\n"
        return outline_str

    
try:
    longtail_keywords = longtail_keys.longtail_keywords
except AttributeError:
    longtail_keywords = longtail_keys[0].longtail_keywords
five_longest_lt_kws = "; ".join(sorted([k.keyword for k in longtail_keywords], key=len, reverse=True)[:5])

empty_outline = use_component(
    OutlineGenerator, 
    {
        "s_kw": sec_keys_list,
        "l_kw": five_longest_lt_kws
    }
)
