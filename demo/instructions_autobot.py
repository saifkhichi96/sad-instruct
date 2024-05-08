import argparse
import json

# Colorama for colored terminal output
from colorama import init, Fore, Style
init(autoreset=True)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from prompting import PromptingStrategy, Prompt


class InstructionsAutobot(PromptingStrategy):
    def __init__(self, scene_graph, scenario, num_iterations=2):
        super().__init__(init_cfg='configs/autobot.py')
        self.user_prompt.set('scenario', scenario)

        # Prompt the narrator for initial instructions
        self.narrator = Narrator(scene_graph, scenario)
        instructions = self.narrator.get_initial_instructions()
        self.user_prompt.set('instructions', instructions)

        self.num_iterations = num_iterations

    def start(self):
        print('### System ###')
        print(self.prompter.system_prompt)
        print(self.user_prompt.template)
        print('$scene_graph: [SceneGraph]')
        print('$scenario:', self.user_prompt.get('scenario'))

        print('### Narrator ###')
        print(self.user_prompt.get('instructions'))
        print('')

        # Get the humanoid's response
        autobot_response = self.prompt(self.user_prompt)

        for i in range(self.num_iterations):
            # Send the response to the narrator
            narrator_response = self.narrator.prompt(autobot_response)

            # Send the narrator's response to the humanoid
            autobot_response = self.prompt(narrator_response)

        # Export the conversation
        print('Exporting conversation...')
        self.export_conversation()

    @property
    def message_history(self):
        return self.prompter.messages

    def export_conversation(self):
        with open('out/conversation.txt', 'w') as f:
            history = self.message_history
            history = json.dumps(history, indent=4)
            f.write(history)


class Narrator(PromptingStrategy):
    def __init__(self, scene_graph, scenario):
        super().__init__(init_cfg='configs/scenario2instructions.py')
        self.user_prompt.set('scene_graph', scene_graph)
        self.user_prompt.set('scenario', scenario)

    def get_initial_instructions(self):
        return self.prompt(self.user_prompt)

    def prompt(self, prompt: Prompt | str, role: str = 'user') -> str:
        if isinstance(prompt, str):
            # Remove $ signs from the prompt, as it is reserved for variables
            # and this chatbot only supports variables in the initial prompts
            prompt = prompt.replace('$', '')

        return super().prompt(prompt, role)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene_graph', type=str,
                        help='Path to the scene graph JSON file')
    return parser.parse_args()


def main(scene_graph_path):
    # Load the scene graph
    print('----------------------------------------------------------')
    print("Loading scene graph... ", end='')
    scene_graph = json.load(open(scene_graph_path, 'r'))[-1]['content']
    print("Done!")

    # Get the scenario
    scenario = input("Enter the scenario: ")
    print('')

    print(Fore.GREEN + 'The autobot will now start and use the narrator to generate instructions.')
    print(Style.BRIGHT + Fore.MAGENTA +
          '----------------------------------------------------------')

    # Start the autobot
    robot = InstructionsAutobot(scene_graph, scenario)
    robot.start()

    # Print the conversation
    print(Fore.MAGENTA + '----------------------------------------------------------')
    print(Fore.GREEN + 'Conversation:')
    print(Fore.MAGENTA + '----------------------------------------------------------')
    for message in robot.message_history:
        print(message)


if __name__ == '__main__':
    args = parse_args()
    main(args.scene_graph)
