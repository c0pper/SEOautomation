import io
import os
import random
import re
import shutil
from colorama import Fore
import requests
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from utililty import check_and_load_state, model
from PIL import Image

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


class ImagePromptGenerator:
    """Generate detailed and effective prompts for Stable Diffusion to create images for blog articles."""

    system = """You are an AI specialized in crafting detailed and effective prompts for Stable Diffusion to generate images for blog articles. Your task is to provide clear, descriptive prompts that guide the image generation model to produce high-quality, relevant images that enhance the content and engagement of the articles."""

    human = """Article introduction:
{introduction}

Task:
Based on the introduction craft a prompt for stable diffusion to create an image appropriate for the article

Generate only the prompt text, without any additional text."""


@check_and_load_state(["sd_prompt"])
def get_sd_prompt(state):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating SD prompt...')
    prompt = model.invoke([
        ("system", ImagePromptGenerator.system),
        ("human", ImagePromptGenerator.human.format(introduction=state["introduction"])),
    ]).content
    if prompt.endswith("."):
        prompt = prompt[:-1]
    prompt = prompt + ", high-resolution image, sharp focus, illustration, hyperdetailed photography"

    state["sd_prompt"] = prompt
    return state



def _queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def _get_images(ws, prompt):
    prompt_id = _queue_prompt(prompt)['prompt_id']
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            print(f"\t\tStage: {message['type']}")
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        current_node = data['node']
        else:
            if current_node == 'save_image_websocket_node':
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output

    return output_images


workflow = json.load(open("image_generator_api.json", "r"))

def _save_images(images, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    saved_image_paths = []
    for node_id in images:
        for idx, image_data in enumerate(images[node_id]):
            image = Image.open(io.BytesIO(image_data))
            image_path = f"{directory}/image{idx}.png"
            image.save(image_path)
            saved_image_paths.append(image_path)
    return saved_image_paths


def _prompt_for_image_selection(batch_size):
    try:
        image1_idx = input(f"Choose first image to use in article -> 0-{batch_size-1} OR leave empty to generate again\n")
        image2_idx = input(f"Choose second image to use in article -> 0-{batch_size-1} OR leave empty to generate again\n")
        if image1_idx == '' or image2_idx == '':
            return None, None
        image1_idx = int(image1_idx)
        image2_idx = int(image2_idx)
        if 0 <= image1_idx < batch_size and 0 <= image2_idx < batch_size:
            return image1_idx, image2_idx
        else:
            print(Fore.YELLOW, "Invalid selection, please choose indices within the range.")
            return None, None
    except ValueError:
        print(Fore.YELLOW, "Invalid input, please enter numeric indices or leave empty to regenerate.")
        return None, None


def _clear_images_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(Fore.YELLOW, f"Failed to delete {file_path}. Reason: {e}")


@check_and_load_state(["article_images"])
def generate_and_save_images(state, workflow, seed=random.randint(1,10000), steps=6, batch_size=4):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating images...')
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))

    positive_prompt = state["sd_prompt"]
    workflow["6"]["inputs"]["text"] = positive_prompt
    workflow["3"]["inputs"]["seed"] = seed
    workflow["3"]["inputs"]["steps"] = steps
    workflow["5"]["inputs"]["batch_size"] = batch_size

    image1_idx = None
    image2_idx = None
    while not image1_idx and not image2_idx:
        directory = f'{state["article_directory"]}/images'
        _clear_images_directory(directory)
        images = _get_images(ws, workflow)

        saved_image_paths = _save_images(images, directory)
        print(Fore.LIGHTBLUE_EX, f"Saved images to {directory}")

        image1_idx, image2_idx = _prompt_for_image_selection(batch_size)
        
    state["article_images"] = [
        {
            "local_path": saved_image_paths[image1_idx],
            "upload_response": _upload_image_to_wordpress(saved_image_paths[image1_idx])
        }, 
        {
            "local_path": saved_image_paths[image2_idx],
            "upload_response": _upload_image_to_wordpress(saved_image_paths[image2_idx])
        }
    ]
    
    
    
    ws.close()
    return state


def _upload_image_to_wordpress(image_path, site="93simon7.wordpress.com"):
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site}/media/new"
    token = os.getenv("WP_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        'media[]': open(image_path, 'rb')
    }
    
    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        response = response.json()
        return response["media"][0]
    else:
        response.raise_for_status()
        