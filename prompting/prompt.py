import base64
import os
import re
from typing import Any


class Prompt:
    def __init__(self, template: str, role: str = 'user', parameters: dict = {}):
        self.template = template
        self.role = role
        self.parameters = self._read_params()
        self._image_url = None

        # Update the parameters with the given values
        for param, value in parameters.items():
            self.set(param, value)

        # Build options
        self.ignore_missing = False

    def _read_params(self) -> dict:
        """ Read the parameters from the template string. """
        params = set(re.findall(r'\$\w+', self.template))
        return {param[1:]: None for param in params}

    @property
    def image_url(self):
        return self._image_url

    @image_url.setter
    def image_url(self, url: str):
        # Function to encode the image
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        if re.match(r'^https?://', url):
            self._image_url = url

        elif os.path.isfile(url):
            accepted_formats = ['.jpg', '.jpeg', '.png']
            ext = os.path.splitext(url)[1].lower()
            if ext not in accepted_formats:
                raise ValueError(f'Invalid image format. Accepted formats: {accepted_formats}')

            mime_type = 'jpeg' if ext in ['.jpg', '.jpeg'] else 'png'

            base64_image = encode_image(url)
            self._image_url = f"data:image/{mime_type};base64,{base64_image}"

        else:
            raise ValueError('Invalid image URL provided.')

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
