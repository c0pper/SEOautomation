from colorama import Fore
from utililty import check_and_load_state, json_fixer, gpt35, gpt4omini, estimate_reading_time, NARRATOR_WPM
from outline import OutlineGenerator
from refiner import stitch_h2_paragraphs


class GuidingQuestionsGenerator:
    schema = """
    ### Instructions
    Generate a list of guiding questions designed to expand an anecdote, making it more interesting and detailed, adhering to the following JSON schema:
    {
        "guiding_questions": [<a list of generated questions>]
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    style_instructions = """### Writing style instructions ###
- Be Thought-Provoking: Ensure questions encourage deeper reflection and provide more context.
- Focus on Details: Ask questions that help uncover interesting or unique details.
- Number of Questions: Provide between 5 and 10 questions.
"""
    
    system = """You are an expert in creating engaging content. You will generate a list of guiding questions to help expand an anecdote, making it more detailed and interesting."""
    
    human = """### Anecdote:\n{anecdote}\n\n\n### Based on the provided anecdote, generate a list of 5 to 10 guiding questions designed to expand the anecdote and make it more interesting and detailed.\n\n{style}\n\n{schema}"""


class AnecdoteGenerator:
    schema = """
    ### Instructions
    Generate either an interesting personal anecdote or a fun/interesting fact adhering to the following JSON schema:
    {
		"anecdote": "Here you will write the text content of the anecdote."
	}

    Only respond with valid JSON which can be parsed in Python.
    """
    
    style_instructions = """### Writing style instructions ###
- Content should be as long as possible, it is needed to increase the article lenght.
- Be Engaging: Ensure the content is interesting and holds the reader’s attention.
- Relevance: Ensure the anecdote is relevant to the article’s topic and context.
- Relatable Language: Use language that is relatable and accessible to a broad audience, including younger readers.
- Use Active Voice: Whenever possible, use active voice and first person to make the content more dynamic.
"""
    
    system = """You are an expert in enhancing articles with engaging content. You will generate either a personal anecdote  based on the provided article title, introduction, and outline."""
    
    human = """### Article title:\n{title}\n\n### Paragraph title:\n{p_title}\n\n### Paragraph content:\n{p_content}\n\n\n### Based on the provided article title, Paragraph title, and Paragraph content, help me expand the article by writing a relatable personal anecdote that could fill up as much time as possible.\n\n{style}\n\n{schema}"""


class AnecdoteExpander:
    schema = """
    ### Instructions
    Generate a rewritten longer content for an anecdote with the help of a list of guiding questions, adhering to the following JSON schema:
    {
        "longer_anecdote": "The content of the longer rewritten anecdote, incorporating answers to the guiding questions."
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    style_instructions = """### Writing style instructions ###
- Address each guiding question in detail to expand on the anecdote.
- Ensure the added content is interesting and keeps the reader's attention.
- Write in a way that is easy to understand, suitable for a broad audience.
- Ensure all rewritten content is relevant to the original anecdote and the guiding questions.
- The expanded content should be thorough and comprehensive; aim for clarity and detail.
"""
    
    system = """You are an expert in rewriting content with the aim of making it longer. You will rewrite an anecdote and make it longer with the help of a list of guiding questions, integrating in the original anecdote detailed and engaging information."""
    
    human = """### Original Anecdote:\n{anecdote}\n\n### Guiding Questions:\n{guiding_questions}\n\n\n### Based on the provided anecdote and guiding questions, rewrite the anecdote in a longer, more comprehensive form that incorporates detailed answers to the questions, enhancing and elaborating on the original anecdote.\n\n{style}\n\n{schema}"""


class AnecdotePlacementChooser:
    schema = """
    ### Instructions
    Based on the provided article title and list of current paragraph titles, choose the most suitable paragraph title where a personal anecdote would be most effective. Adhere to the following JSON schema:
    {
        "chosen_paragraph_title": "The title of the paragraph where the personal anecdote should be added"}
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    system = """You are an expert in content enhancement and personal engagement. You will select the most suitable paragraph title for adding a personal anecdote to an article. Consider where the anecdote would be most impactful, relevant, and engaging to the reader."""
    
    human = """Article Title: {article_title}\n\nCurrent Paragraph Titles:\n{paragraph_titles}\n\n### Important Instructions ###\nSelect the paragraph title that is the best fit for inserting a personal anecdote. Consider the relevance to the article's title, potential for emotional engagement, and the natural flow of the article.\n\n{schema}"""



def generate_guiding_questions(anecdote):
    llm_response = gpt35.invoke([
        ("system", GuidingQuestionsGenerator.system),
        ("human", GuidingQuestionsGenerator.human.format(
            anecdote=anecdote, 
            style=GuidingQuestionsGenerator.style_instructions, 
            schema=GuidingQuestionsGenerator.schema)),
    ]).content
        
    guiding_questions = json_fixer(llm_response)
    guiding_questions = guiding_questions.get("guiding_questions", guiding_questions)
    return guiding_questions


def expand_anecdote(anecdote, questions):
    llm_response = gpt4omini.invoke([
        ("system", AnecdoteExpander.system),
        ("human", AnecdoteExpander.human.format(
            anecdote=anecdote,
            guiding_questions=questions,
            style=AnecdoteExpander.style_instructions, 
            schema=AnecdoteExpander.schema)),
    ]).content
        
    longer_anecdote = json_fixer(llm_response)
    longer_anecdote = longer_anecdote.get("longer_anecdote", longer_anecdote)
    return longer_anecdote


def choose_anecdote_paragraph(article_title, paragraph_titles):
    llm_response = gpt4omini.invoke([
        ("system", AnecdotePlacementChooser.system),
        ("human", AnecdotePlacementChooser.human.format(
            article_title=article_title,
            paragraph_titles=paragraph_titles,
            schema=AnecdotePlacementChooser.schema)),
    ]).content
        
    chosen_paragraph_title = json_fixer(llm_response)
    chosen_paragraph_title = chosen_paragraph_title.get("chosen_paragraph_title", chosen_paragraph_title)
    assert chosen_paragraph_title in paragraph_titles
    return chosen_paragraph_title


def needs_padding_after_anecdote(anecdote, start_reading_time):
    _, anecdote_reading_time = estimate_reading_time(anecdote)
    new_reading_time = start_reading_time + anecdote_reading_time
    return new_reading_time < 600


@check_and_load_state(["anecdote"])
def get_anecdote(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating anecdote...')
    start_reading_time = state["reading_time"]
    guiding_questions = []
    anecdote = None
    
    while state["needs_padding"]:
        
        if not anecdote:
                # create anecdote
                h2_titles = [h2["title"] for h2 in state["filled_outline"]["h2_titles"]]
                paragraph_title = choose_anecdote_paragraph(
                    article_title=state["article_title"],
                    paragraph_titles=h2_titles
                )
                paragraph = [h2 for h2 in state["filled_outline"]["h2_titles"] if h2["title"] == paragraph_title]
                
                llm_response = gpt4omini.invoke([
                    ("system", AnecdoteGenerator.system),
                    ("human", AnecdoteGenerator.human.format(
                        title=state["article_title"], 
                        p_title=paragraph["title"],
                        p_content=paragraph["content"],
                        style=AnecdoteGenerator.style_instructions, 
                        schema=AnecdoteGenerator.schema)),
                ]).content
                    
                anecdote = json_fixer(llm_response)
                anecdote = anecdote.get("anecdote", anecdote)
                
                state["needs_padding"] = needs_padding_after_anecdote(anecdote, start_reading_time)
        
        if state["needs_padding"]:
            if not guiding_questions:
                guiding_questions = generate_guiding_questions(anecdote)
                
            # expand anecdote
            # two_q = guiding_questions[:2]
            # guiding_questions.pop(0)
            # guiding_questions.pop(0)
            anecdote = expand_anecdote(anecdote, guiding_questions)
            
            state["needs_padding"] = needs_padding_after_anecdote(anecdote, start_reading_time)
            
        
        state["anecdote"] = {}
        state["anecdote"]["content"] = anecdote
        state["anecdote"]["related_paragraph"] = {"title": paragraph["title"], "content": paragraph["content"]}
    
        paragraph["content"] = anecdote + "\n\n" + paragraph["content"]
        
    return state


if __name__ == "__main__":
    choose_anecdote_paragraph(
        article_title="2024 Perseid Meteor Shower Peak: Best Viewing Spots and Photography Tips",
        paragraph_titles=[
            "Best Viewing Spots for Perseid Meteor Shower Photography",
            "2024 Predictions and Peak Locations for Perseid Meteor Shower",
            "Live Streaming and Best Time to Watch Perseid Meteor Shower 2024"
        ]
    )