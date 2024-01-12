import re
from typing import Any


class Prompt:
    def __init__(self, template: str, role: str = 'user', parameters: dict = {}):
        self.template = template
        self.role = role
        self.parameters = self._read_params()

        # Update the parameters with the given values
        for param, value in parameters.items():
            self.set(param, value)

        # Build options
        self.ignore_missing = False

    def _read_params(self) -> dict:
        """ Read the parameters from the template string. """
        params = set(re.findall(r'\$\w+', self.template))
        return {param[1:]: None for param in params}

    def set(self, parameter: str, value: Any):
        if parameter not in self.parameters:
            raise ValueError(f'Unknown parameter ${parameter} specified. '
                             f'Available parameters: {self.parameters.keys()}')

        self.parameters[parameter] = value

    def get(self, parameter: str, default: Any = None) -> Any:
        return self.parameters.get(parameter, default)

    def build(self) -> str:
        """ Build the prompt string. """
        prompt = self.template
        for param, value in self.parameters.items():
            if value is None:
                if not self.ignore_missing:
                    raise ValueError(f'Parameter ${param} is not set.')
                else:
                    continue

            prompt = prompt.replace(f'${param}', str(value))

        return prompt

    def __str__(self) -> str:
        return self.build()


class PromptBuilder:
    @staticmethod
    def from_file(path: str, parameters: dict = {}) -> Prompt:
        # Load the prompt file
        with open(path, 'r') as f:
            prompt_cfg = eval(f.read())

        # Extract components from the file
        template = prompt_cfg.get('template', '').strip()
        parameters = prompt_cfg.get('parameters', parameters)

        # Check that the prompt is a non-empty string
        if not isinstance(template, str) or len(template) == 0:
            raise ValueError('Prompt must be a non-empty string.')

        # Build and return the Prompt object
        return Prompt(template, parameters)
