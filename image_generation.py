#This is an example that uses the websockets api and the SaveImageWebsocket node to get images directly without
#them being saved to disk

import os
import re
from colorama import Fore
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from utililty import model

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



def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
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

def generate_and_save_images(state, workflow, seed=5, steps=6, batch_size=4):
    print(Fore.LIGHTBLUE_EX + f'[+] Generating images...')
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))

    positive_prompt = state["sd_prompt"]
    workflow["6"]["inputs"]["text"] = positive_prompt
    workflow["3"]["inputs"]["seed"] = seed
    workflow["3"]["inputs"]["steps"] = steps
    workflow["5"]["inputs"]["batch_size"] = batch_size

    images = get_images(ws, workflow)

    sanitized_name = re.sub(r'[^A-Za-z0-9 ]+', '', state["article_title"]).lower().replace(" ", "_")
    directory = f"articles/{sanitized_name}"[:30]
    if not os.path.exists(directory):
        os.makedirs(directory)
    for node_id in images:
        for idx, image_data in enumerate(images[node_id]):
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            image.save(f"{directory}/image{idx}.png")

    image_idx = input(f"Which image to use in article? 0-{batch_size-1}")
    state["article_image"] = f"{sanitized_name}/image{image_idx}.png"
    return state