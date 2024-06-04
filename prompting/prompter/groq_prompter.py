""" Interfaces for interacting with the Groq LLMs. """

# Python imports
import os
from typing import List, Optional

# Third party imports
from openai import OpenAI

# Local imports
from ..prompt import Prompt
from .base_prompter import BasePrompter


class GroqPrompter(BasePrompter):
    """ Prompter for Groq's API.

    Requires the `GROQ_API_KEY` environment variable to be set.

    Args:
        model (str): Model to use. Defaults to `mixtral-8x7b-32768`.
    """

    CHAT_MODELS = [
        "gemma-7b-it",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
    ]

    COMPLETION_MODELS = [

    ]

    def __init__(self,
                 model: str = "mixtral-8x7b-32768",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key is None:
            raise ValueError("GROQ_API_KEY environment variable must be set.")

        self.client = OpenAI(
            max_retries=self.max_retries,
            timeout=self.timeout,
            base_url="http://localhost:8000/v1",
            api_key=api_key,
        )

        # assert model in self.CHAT_MODELS + self.COMPLETION_MODELS, \
        #     f"Model {model} not supported. Please choose one of {self.CHAT_MODELS + self.COMPLETION_MODELS}"

        self.model = model
        self.system_prompt = None
        self.messages = []
        self.use_history = True

    @property
    def system_prompt(self) -> Optional[Prompt]:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, system_prompt: Prompt) -> None:
        assert system_prompt is None or system_prompt.role == "system", \
            "System prompt must have role 'system'."

        if system_prompt is None:
            self._system_prompt = None
        else:
            self._system_prompt = {"role": system_prompt.role,
                                   "content": system_prompt.build()}

    def _parse_response(self, response: str) -> str:
        return response

    def _ask_chat(self, prompt: Prompt) -> List[str]:
        messages = []
        if self.use_history:
            messages.extend(self.messages)

        # Add system prompt if it exists
        if self.system_prompt and len(messages) == 0:
            messages.append(self.system_prompt)

        # Add user prompt
        if prompt.image_url is not None and 'vision' in self.model:
            prompt_content = {
                "role": prompt.role,
                "content": [
                    {
                        "type": "text",
                        "text": prompt.build(),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": prompt.image_url
                        }
                    }
                ]
            }
        else:
            prompt_content = {
                "role": prompt.role,
                "content": prompt.build()
            }
        messages.append(prompt_content)

        # Ask OpenAI
        choices = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            frequency_penalty=self.repetition_penalty,
        ).choices
        responses = [c.message.content for c in choices]
        response = responses[0]

        # Save history and return the first response
        if self.use_history:
            messages.append({"role": "assistant", "content": response})
            self.messages = messages

        return responses

    def _ask_completion(self, prompt: Prompt) -> List[str]:
        choices = self.client.completions.create(
            model=self.model,
            prompt=prompt.build(),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        ).choices
        responses = [c.text for c in choices]

        # Return the first response
        return responses[0]

    def _ask(self, prompt: Prompt) -> str:
        return self._ask_chat(prompt)
        # if self.model in self.CHAT_MODELS:
        #     return self._ask_chat(prompt)
        # elif self.model in self.COMPLETION_MODELS:
        #     return self._ask_completion(prompt)
        # else:
        #     # Should never happen because of the assert in __init__
        #     raise RuntimeError(f"Model {self.model} not supported.")

    def prompt(self, prompt: Prompt) -> List[str]:
        # OpenAI API handles retries internally, so we don't need to
        # call out base class's `prompt` method which calls `self._ask`
        # with a short exponential backoff.
        return self._ask(prompt)