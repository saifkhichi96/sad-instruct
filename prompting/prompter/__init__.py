import os
from typing import Dict, Union

from .base_prompter import BasePrompter
from .groq_prompter import GroqPrompter
from .huggingface_prompter import HuggingFacePrompter
from .openai_prompter import OpenAIPrompter


__all__ = [
    "BasePrompter",
    "GroqPrompter",
    "HuggingFacePrompter",
    "OpenAIPrompter",
]

__dict__ = {
    "BasePrompter": BasePrompter,
    "GroqPrompter": GroqPrompter,
    "HuggingFacePrompter": HuggingFacePrompter,
    "OpenAIPrompter": OpenAIPrompter,
}


def build_prompter(type: str, init_cfg: Dict, **kwargs) -> BasePrompter:
    """Initialize a prompter.

    Args:
        type: The type of prompter to initialize.
        init_cfg: Keyword arguments to pass to the prompter constructor.
        **kwargs: Additional attributes to pass to the prompter constructor. These
            attributes will be set on the prompter object after it is initialized, 
            and will override any attributes set by init_cfg.

    Returns:
        The initialized prompter.
    """
    if type not in __dict__:
        raise ValueError(f"Unknown prompter type: {type}")

    # Create the prompter
    prompter_cls = __dict__.get(type)
    prompter = prompter_cls(**init_cfg)

    # Set any additional attributes
    for key, value in kwargs.items():
        if not hasattr(prompter, key):
            raise ValueError(f"Prompter does not have attribute: {key}")

        setattr(prompter, key, value)

    return prompter


def build_prompter_from_cfg(cfg: Union[Dict, str]) -> BasePrompter:
    """Initialize a prompter from a configuration dictionary.

    Args:
        cfg: The configuration dictionary or path to a configuration file. If a path
            is provided, the file will be loaded as a YAML file.

    Returns:
        The initialized prompter.
    """
    if isinstance(cfg, str):
        assert os.path.isfile(cfg), f"Invalid configuration file: {cfg}"
        import yaml

        with open(cfg, "r") as f:
            cfg = yaml.safe_load(f)

    return build_prompter(**cfg)
