from typing import Union

from .backend import build_llm_from_cfg
from .prompt import Prompt


class LLM:
    """ Large Language Model (LLM).

    This class provides an interface for interacting with a large language models (LLMs)
    using different backends (e.g., HuggingFace, OpenAI, Groq, VLLM).

    Args:
        init_cfg (Union[str, dict]): The initialization configuration for the LLM.
            This can be a path to a config file or a dictionary.
    """
    def __init__(self, init_cfg: Union[str, dict]) -> None:
        if isinstance(init_cfg, str):
            # Load the config file
            with open(init_cfg, 'r') as f:
                init_cfg = eval(f.read())
        elif not isinstance(init_cfg, dict):
            raise ValueError('init_cfg must be a path to a config file or a dictionary.')

        # Build the prompter
        self.backend = build_llm_from_cfg(init_cfg['backend_cfg'])

        # Build the system prompt (if specified)
        system_prompt = None
        if 'system_prompt_cfg' in init_cfg:
            system_prompt_cfg = init_cfg['system_prompt_cfg']
            system_prompt = Prompt.from_cfg(system_prompt_cfg)
            self.backend.system_prompt = system_prompt

        # Build the user prompt
        user_prompt_cfg = init_cfg.get('user_prompt_cfg', None)
        self.user_prompt = None
        if user_prompt_cfg:
            self.user_prompt = Prompt.from_cfg(user_prompt_cfg)

    def prompt(self, prompt: Union[Prompt, str], role: str = 'user') -> str:
        if isinstance(prompt, str):
            prompt = Prompt(prompt, role)

        response = self.backend.prompt(prompt)[0]
        return response