from typing import Union

from .prompter import build_prompter_from_cfg
from .prompt_builder import Prompt, PromptBuilder


class PromptingStrategy:
    def __init__(self, init_cfg: Union[str, dict]) -> None:
        """ Initialize the prompting strategy with the given config. """
        if isinstance(init_cfg, str):
            # Load the config file
            with open(init_cfg, 'r') as f:
                init_cfg = eval(f.read())
        elif not isinstance(init_cfg, dict):
            raise ValueError('init_cfg must be a path to a config file or a dictionary.')

        # Build the prompter
        self.prompter = build_prompter_from_cfg(init_cfg['prompter_cfg'])

        # Build the system prompt (if specified)
        system_prompt = None
        if 'system_prompt_cfg' in init_cfg:
            system_prompt_cfg = init_cfg['system_prompt_cfg']
            system_prompt = PromptBuilder.from_cfg(system_prompt_cfg)
            self.prompter.system_prompt = system_prompt

        # Build the user prompt
        user_prompt_cfg = init_cfg['user_prompt_cfg']
        self.user_prompt = PromptBuilder.from_cfg(user_prompt_cfg)

    def prompt(self, prompt: Union[Prompt, str], role: str = 'user') -> str:
        if isinstance(prompt, str):
            prompt = Prompt(prompt, role)

        response = self.prompter.prompt(prompt)[0]
        return response