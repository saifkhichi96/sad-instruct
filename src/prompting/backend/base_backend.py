import logging
import time
import traceback
from typing import List, Optional

from ..prompt import Prompt


class BaseBackend:
    """ Base class for LLM prompters.

    Args:
        temperature (float): Temperature to use for sampling. Defaults to 0.5.
        repetition_penalty (float): Repetition penalty to use for sampling. Defaults to 1.0.
        top_k (int): Top-k value to use for sampling. Defaults to 0.
        top_p (float): Top-p value to use for sampling. Defaults to 0.9.
        max_tokens (int): Maximum number of tokens to generate. Defaults to 512.
        max_retries (int): Number of times to retry the API call in case of failure.
            Defaults to 0.
    """

    BACKOFF_TIME = 10 # seconds

    def __init__(self,
                 temperature: float = 0.5,
                 repetition_penalty: float = 1.0,
                 top_k: int = 0,
                 top_p: float = 0.9,
                 max_tokens: int = 512,
                 max_retries: int = 2,
                 timeout: Optional[int] = None,
                 ) -> None:
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.top_k = top_k
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.max_retries = max(max_retries, 0)
        self.timeout = timeout

    def _ask(self, prompt: Prompt) -> List[str]:
        raise NotImplementedError

    def prompt(self, prompt: Prompt) -> List[str]:
        current_try = 0
        while current_try <= self.max_retries:
            try:
                return self._ask(prompt)
            except Exception as e:
                # Log exception
                logging.error(f"[{self.__class__.__name__}] {type(e)}: {e}")
                logging.debug(traceback.format_exc())

                # Calculate exponential backoff for retry
                backoff = self.BACKOFF_TIME * (2 ** current_try)
                num_retries = self.max_retries - current_try
                logging.info(
                    f"Retrying in {backoff}s ({num_retries} retries left)...")

                # Wait and retry
                time.sleep(backoff)
                current_try = current_try + 1
