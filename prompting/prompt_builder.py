import os
from typing import Union, Dict

from .prompt import Prompt


class PromptBuilder:
    @staticmethod
    def from_cfg(prompt_cfg: Union[Dict, str], parameters: Dict = {}) -> Prompt:
        # Load the prompt file (if necessary)
        if isinstance(prompt_cfg, str):
            if not os.path.isfile(prompt_cfg):
                raise ValueError(f'Invalid prompt config file: {prompt_cfg}')

            with open(prompt_cfg, 'r') as f:
                prompt_cfg = eval(f.read())

        # Extract components from the file
        template = prompt_cfg.get('template', '').strip()
        role = prompt_cfg.get('role', 'user')
        params = prompt_cfg.get('parameters', {})
        params.update(parameters)

        # Check that the prompt is a non-empty string
        if not isinstance(template, str) or len(template) == 0:
            raise ValueError('Prompt must be a non-empty string.')

        # Build and return the Prompt object
        return Prompt(template, role, params)
