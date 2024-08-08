from time import sleep
from typing import List
from colorama import Fore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import os
import requests

from utililty import check_and_load_state, model


class FreepikKeywordGenerator:
    """Generate effective keywords or keyphrases for searching images on Freepik.com for blog articles."""

    system = """You are an AI specialized in generating concise and highly effective keyphrases for searching images on Freepik.com. Your task is to craft a single keyphrase that is the most relevant and powerful for finding images that perfectly align with the content and theme of the blog articles."""

    human = """Article introduction:
{introduction}

Task:
Based on the introduction, craft a keyword or keyphrase suitable for searching images on Freepik.com.

Generate only the keyword or keyphrase, without any additional text."""



@check_and_load_state(["img_query"])
def get_img_query(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating Freepik keyword...')
    keywords = model.invoke([
        ("system", FreepikKeywordGenerator.system),
        ("human", FreepikKeywordGenerator.human.format(introduction=state["introduction"])),
    ]).content
    if keywords.endswith("."):
        keywords = keywords[:-1]

    state["img_query"] = keywords
    return state


def save_pics_freepik(urls: list, directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)

    saved_images_paths = []
    for i, url in enumerate(urls):
        try:
            response = requests.get(url)
            response.raise_for_status()  
            
            file_extension = url.split('.')[-1]
            if '?' in file_extension:  # Handle cases where URL parameters follow the extension
                file_extension = file_extension.split('?')[0]
            
            # Create a file name using the index
            file_name = f"image_{i + 1}.{file_extension}"
            file_path = os.path.join(directory, file_name)
            
            # Write the image content to a file
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
            print(f"Saved: {file_path}")
            saved_images_paths.append(file_path)
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
            
    return saved_images_paths
        

def scrape_freepik(state) -> List:
    driver = webdriver.Firefox()
    # Open Google search page
    driver.get(f'https://www.freepik.com/search?format=search&last_filter=selection&last_value=1&query={state["img_query"]}&selection=1')
    
    sleep(1)
    figures = retry_on_stale_element(lambda: driver.find_elements(By.TAG_NAME, "figure"))
        
    image_urls = []
    for figure in figures:
        # Find the <a> tag within the figure
        a_tag = retry_on_stale_element(lambda: figure.find_element(By.TAG_NAME, "a"))
        # Find the <img> tag within the <a> tag
        img_tag = retry_on_stale_element(lambda: a_tag.find_element(By.TAG_NAME, "img"))
        # Get the src attribute from the img tag
        img_src = img_tag.get_attribute("src")
        image_urls.append(img_src)
        
    
    driver.quit()
    saved_images_paths = save_pics_freepik(image_urls, f'{state["article_directory"]}/images')
    return saved_images_paths


def retry_on_stale_element(func, max_retries=3, wait_time=1):
    """Retries the provided function if a StaleElementReferenceException occurs."""
    for attempt in range(max_retries):
        try:
            return func()
        except StaleElementReferenceException as e:
            print(f"StaleElementReferenceException caught on attempt {attempt + 1}. Retrying...")
            sleep(wait_time)  # Wait before retrying
    raise Exception(f"Failed after {max_retries} retries due to StaleElementReferenceException.")