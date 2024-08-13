


from utililty import check_and_load_state, json_fixer, gpt35


class VideoScriptSegmentWriter:
    schema = """
    ### Instructions
    Generate the script segment adhering to the following JSON schema:
    {
        "paragraph": {
            "type": "string",
            "description": "The content of the paragraph"
        },
        "required": ["paragraph"],
    }

    Only respond with valid JSON which can be parsed in Python.
    """
    
    style_instructions = """### Writing style instructions ###
- Use Short Sentences: Keep sentences concise and direct.
- Active Voice: Utilize active voice whenever possible.
- Use Visual Cues: Incorporate visual descriptions or cues to guide the viewer's imagination.
- Use Engaging Language: Keep the tone conversational and engaging to hold the viewer’s attention.
- Simple Language: Ensure the language is simple and accessible, suitable for a 13-year-old.
- Length: Make the paragraph as comprehensive as possible.
- Banned words: vibrant, delve, unravel, journey, multifaceted, bustling, landscape, testament, realm, embark, crucial, vital, ensure.
"""
    
    system = """You are an expert in creating engaging and comprehensive YouTube video scripts. You will write the content of a video script segment based on the provided overall outline and paragraph title."""
    
    human = """### Overall video outline:\n {outline}\n\n### Segment title:\n{p_title}\n\n### Segment content:\n{content}\n### Based on the provided information, write a comprehensive paragraph for the video script\n\n{style}\n\n{schema}"""
    

      
@check_and_load_state(["yt_introduction"])
def get_formatted_yt_script(state: dict) -> str:
    yt_script = ""
    outline = state["filled_outline"]
    
    # Intro
    llm_response = gpt35.invoke([
        ("system", VideoScriptSegmentWriter.system),
        ("human", VideoScriptSegmentWriter.human.format(
            outline=state["formatted_empty_outline"], 
            p_title="Introduction",
            content=state["introduction"],
            style=VideoScriptSegmentWriter.style_instructions,
            schema=VideoScriptSegmentWriter.schema
        )),
    ]).content
        
    script_semgent = json_fixer(llm_response)
    script_semgent = script_semgent.get("paragraph", script_semgent)
    
    yt_script += f"{script_semgent}\n\n"
    state["yt_introduction"] = script_semgent
    
    for h2 in outline['h2_titles']:
        llm_response = gpt35.invoke([
            ("system", VideoScriptSegmentWriter.system),
            ("human", VideoScriptSegmentWriter.human.format(
                outline=state["formatted_empty_outline"], 
                p_title=h2.get('title'),
                content=h2.get('content'),
                style=VideoScriptSegmentWriter.style_instructions,
                schema=VideoScriptSegmentWriter.schema
            )),
        ]).content
            
        script_semgent = json_fixer(llm_response)
        script_semgent = script_semgent.get("paragraph", script_semgent)
        
        yt_script += f"{script_semgent}\n\n"
        h2["yt_script"] = script_semgent
        
        if h2.get('h3_titles'):
            for h3 in h2['h3_titles']:
                llm_response = gpt35.invoke([
                    ("system", VideoScriptSegmentWriter.system),
                    ("human", VideoScriptSegmentWriter.human.format(
                        outline=state["formatted_empty_outline"], 
                        p_title=h3.get('title'),
                        content=h3.get('content'),
                        style=VideoScriptSegmentWriter.style_instructions,
                        schema=VideoScriptSegmentWriter.schema
                    )),
                ]).content
                    
                script_semgent = json_fixer(llm_response)
                script_semgent = script_semgent.get("paragraph", script_semgent)
                
                yt_script += f"\t{script_semgent}\n\n"
                h3["yt_script"] = script_semgent
                
    state["filled_outline"] = outline
                
    # Conclusion
    llm_response = gpt35.invoke([
        ("system", VideoScriptSegmentWriter.system),
        ("human", VideoScriptSegmentWriter.human.format(
            outline=state["formatted_empty_outline"], 
            p_title="Conclusion",
            content=state["conclusion"],
            style=VideoScriptSegmentWriter.style_instructions,
            schema=VideoScriptSegmentWriter.schema
        )),
    ]).content
        
    script_semgent = json_fixer(llm_response)
    script_semgent = script_semgent.get("paragraph", script_semgent)
    
    yt_script += f"{script_semgent}\n\n"
    state["yt_conclusion"] = script_semgent
    
    state["yt_script"] = yt_script
    
    return state
