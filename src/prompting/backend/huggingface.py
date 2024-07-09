""" Interfaces for interacting with the HuggingFace LLMs. """

# Python imports
import json
import logging
import os
from typing import Dict, List

# Third party imports
from requests import request

# Local imports
from ..prompt import Prompt
from .base_backend import BaseBackend


class HuggingFaceBackend(BaseBackend):
    """ Prompter for HuggingFace's LLM API.

    Requires the `HUGGINGFACE_API_KEY` environment variable to be set. See the HuggingFace
    API docs for more information.

    Args:
        model (str): Model to use. Defaults to `gpt2-xl`.
    """

    def __init__(self, model: str = "gpt2-xl", **kwargs) -> None:
        super().__init__(**kwargs)
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if self.api_key is None:
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set.")

        self.model = model

    def _make_header(self) -> Dict:
        return {"Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"}

    def _make_payload(self, prompt: Prompt) -> str:
        return json.dumps({
            "inputs": prompt.build(),
            "parameters": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty,
                "num_return_sequences": 1,
                "max_new_tokens": self.max_tokens,
                "return_full_text": False,
            },
            "options": {
                "use_cache": False,
                "wait_for_model": True,
            }
        })

    def _ask(self, prompt: Prompt) -> List[str]:
        # Make a POST request to the API
        response = request("POST",
                           f"https://api-inference.huggingface.co/models/{self.model}",
                           headers=self._make_header(),
                           data=self._make_payload(prompt))

        # Parse the response
        response = response.content.decode("utf-8")
        response = json.loads(response)

        # Check for errors
        if "error" in response:
            error_message = response["error"]
            error_type = response["error_type"]

            if error_type == "validation":
                logging.error(f"Validation error in HuggingFace API most likely due to prompt being too long.")
                logging.debug(f"Prompt: {prompt}")
                logging.debug(f"Response: {response}")
                raise Exception(f"({error_type}) {error_message}")

            raise Exception(f"({error_type}) {error_message}")

        # Return the first response
        responses = [r["generated_text"] for r in response]
        return responses[0]
