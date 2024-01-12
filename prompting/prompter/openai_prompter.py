""" Interfaces for interacting with the OpenAI LLMs. """

# Python imports
from typing import List, Optional

# Third party imports
from openai import OpenAI

# Local imports
from ..prompt import Prompt
from .base_prompter import BasePrompter


class OpenAIPrompter(BasePrompter):
    """ Prompter for OpenAI's LLM API.

    Requires the `OPENAI_API_KEY` environment variable to be set. See the
    [OpenAI API docs](https://github.com/openai/openai-python/blob/main/api.md)
    for more information.

    Args:
        model (str): Model to use. Defaults to `gpt-3.5-turbo`.
    """

    CHAT_MODELS = [
        "gpt-4-1106-preview",
        "gpt-4-vision-preview",
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-4-32k-0613",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0301",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-16k-0613",
    ]

    COMPLETION_MODELS = [
        "babbage-002",
        "davinci-002",
        "gpt-3.5-turbo-instruct",
        "text-davinci-003",
        "text-davinci-002",
        "text-davinci-001",
        "code-davinci-002",
        "text-curie-001",
        "text-babbage-001",
        "text-ada-001",
    ]

    def __init__(self,
                 model: str = "gpt-3.5-turbo",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = OpenAI(
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

        assert model in self.CHAT_MODELS + self.COMPLETION_MODELS, \
            f"Model {model} not supported. Please choose one of {self.CHAT_MODELS + self.COMPLETION_MODELS}"

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
        messages.append({"role": prompt.role, "content": prompt.build()})

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
        if self.model in self.CHAT_MODELS:
            return self._ask_chat(prompt)
        elif self.model in self.COMPLETION_MODELS:
            return self._ask_completion(prompt)
        else:
            # Should never happen because of the assert in __init__
            raise RuntimeError(f"Model {self.model} not supported.")

    def prompt(self, prompt: Prompt) -> List[str]:
        # OpenAI API handles retries internally, so we don't need to
        # call out base class's `prompt` method which calls `self._ask`
        # with a short exponential backoff.
        return self._ask(prompt)