""" ComfyUI client module """

import json
import requests
import time
from pathlib import Path
from config import TIMEOUT_COMFY_SEC, BATCH_SIZE
from typing import List, Dict

class ComfyClient:
    def __init__(self, comfy_url: str, output_dir: Path):
        self.url = comfy_url
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def queue_prompt(self, prompt: Dict) -> str:
        response = requests.post(f"{self.url}/prompt", json=prompt)
        return response.json()['prompt_id']

    def wait_for_completion(self, prompt_id: str, client_id: str) -> bool:
        ws_url = f"{self.url.replace('http', 'ws')}/ws?clientId={client_id}"
        # Note: WebSocket handling would require websocket-client lib, simplified for text.
        # In real, use websocket-client to listen for 'execution_end'
        time.sleep(5)  # Placeholder, simulate
        return True

    def generate_image(self, positive: str, negative: str, seed: int, width=1920, height=1080, steps=30, cfg=6.5):
        with open('workflows/comfy_template.json') as f:
            template = json.load(f)

        graph = self.build_graph(positive, negative, width, height, seed, steps, cfg, "euler", "normal")
        prompt_id = self.queue_prompt(graph)
        self.wait_for_completion(prompt_id, "test_client")

        # Copy generated images to output_dir
        # Placeholder: Only build_graph is implemented

    def build_graph(self, positive: str, negative: str, width, height, seed, steps, cfg, sampler, scheduler) -> Dict:
        with open('workflows/comfy_template.json') as f:
            graph = json.load(f)
        # Replace variables
        for node in graph.values():
            if 'inputs' in node:
                for key, value in node['inputs'].items():
                    if isinstance(value, str):
                        value = value.replace('$POSITIVE_PROMPT', positive)
                        value = value.replace('$NEGATIVE_PROMPT', negative)
                        value = value.replace('$WIDTH', str(width))
                        value = value.replace('$HEIGHT', str(height))
                        value = value.replace('$SEED', str(seed))
                        value = value.replace('$STEPS', str(steps))
                        value = value.replace('$CFG', str(cfg))
                        value = value.replace('$SAMPLER_NAME', sampler)
                        value = value.replace('$SCHEDULER', scheduler)
                        value = value.replace('$INDEX', str(segment_index))  # Need to pass segment_index
                        node['inputs'][key] = value
        return {"prompt": graph, "client_id": "test_client"}