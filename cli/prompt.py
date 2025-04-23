import argparse

from prompting import build_llm_from_cfg, Prompt

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description='Prompt an LLM.')
    parser.add_argument('backend', type=str,
                        help='Path to the LLM backend configuration file.')
    parser.add_argument('--system', type=str, default="", help='System prompt.')
    parser.add_argument('--prompt', type=str, help='User prompt.', required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    # Read CLI arguments
    cfg = args.backend
    system_prompt = args.system
    user_prompt = args.prompt

    # Build the prompter
    prompter = build_llm_from_cfg(cfg)
    print(f"Using {prompter.__class__.__name__}({prompter.model})")

    # Set the system prompt
    if system_prompt != "":
        print(f"SYSTEM: {system_prompt}")
        prompter.system_prompt = system_prompt

    # Build the prompt
    print(f"USER: {user_prompt}")
    user_prompt = Prompt(user_prompt)

    # Prompt the LLM
    print(f"LLM: ", end="", flush=True)
    response = prompter.prompt(user_prompt)
    if isinstance(response, list):
        response = response[0]
    print(response)

if __name__ == '__main__':
    main()