from time import sleep
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests


def save_pics(urls: list, directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)

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
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
        

def scrape_freepik(query:str) -> List:
    driver = webdriver.Firefox()
    # Open Google search page
    driver.get(f"https://www.freepik.com/search?format=search&last_filter=selection&last_value=1&query={query}&selection=1")
    
    sleep(1)
    figures = driver.find_elements(By.TAG_NAME, "figure")
        
    image_urls = []
    for figure in figures:
        # Find the <a> tag within the figure
        a_tag = figure.find_element(By.TAG_NAME, "a")
        # Find the <img> tag within the <a> tag
        img_tag = a_tag.find_element(By.TAG_NAME, "img")
        # Get the src attribute from the img tag
        img_src = img_tag.get_attribute("src")
        image_urls.append(img_src)
        
    
    driver.quit()
    save_pics(image_urls, state[""])
    return image_urls


q = "thailand"
scrape_freepik(q)