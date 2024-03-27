import argparse
import json
from json.decoder import JSONDecodeError

# Colorama for colored terminal output
from colorama import init, Fore, Style
init(autoreset=True)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from prompting import PromptingStrategy


class SceneGraphChatbot(PromptingStrategy):
    def __init__(self, image_path):
        super().__init__(init_cfg='configs/image2scenegraph.py')
        self.user_prompt.image_url = image_path

        print('### System ###')
        print(self.prompter.system_prompt)
        print('')

        self.started = False
        self.kill = False

    def start(self):
        self.started = True
        self.kill = False

        print('### User ###')
        print(self.user_prompt.template)
        print('$scene_graph: [SceneGraph]')
        print('$scenario:', self.user_prompt.get('scenario'))
        print('')

        response = self.prompt(self.user_prompt)
        self.print_response(response)

        while not self.kill:
            print('### User ###')
            prompt = input(">>> ")
            if prompt == "exit":
                self.kill = True
            else:
                print('')

                # Remove $ signs from the prompt, as it is reserved for variables
                # and this chatbot only supports variables in the initial prompts
                prompt = prompt.replace('$', '')

                response = self.prompt(prompt)
                self.print_response(response)

    def print_response(self, response):
        print(Fore.YELLOW + '### Chatbot ###')

        # Try to decode the response as JSON
        try:
            response = json.loads(response)
        except JSONDecodeError:
            # Fallback to splitting on newlines
            response = response.split('\n')

        for instruction in response:
            print(Fore.CYAN + f"- {instruction}")
        print('')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str,
                        help='Path to the image file.')
    return parser.parse_args()


def main(image_path):
    print(Fore.GREEN + 'The chatbot will now start. Type "exit" to exit.')
    print(Style.BRIGHT + Fore.MAGENTA + '----------------------------------------------------------')

    # Start the chatbot
    chatbot = SceneGraphChatbot(image_path)
    chatbot.start()


if __name__ == '__main__':
    args = parse_args()
    main(args.image_path)
