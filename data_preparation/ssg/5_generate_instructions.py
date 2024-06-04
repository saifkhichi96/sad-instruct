import json
import os
import time
from time import strftime, gmtime

from tqdm import tqdm

from openai import RateLimitError

# Colorama for colored terminal output
from colorama import init, Fore
init(autoreset=True)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from prompting import PromptingStrategy, Prompt, SceneGraph


class InstructionsGenerator:
    def __init__(self, scene_graph, scenario, num_iterations=5, output_dir='out', verbose=True):
        self.scene_graph = scene_graph
        self.scenario = scenario

        # Create the LLM Agents
        self.robot = Robot(scenario)
        self.oracle = Oracle(scene_graph, scenario)
        self.summarizer = PromptingStrategy(init_cfg='configs/summarizer.py')

        # Set output directory
        self.output_dir = output_dir
        self.verbose = verbose

        self.num_iterations = num_iterations
        self.conversation_id = strftime("%Y%m%d-%H%M%S", gmtime())

        self.history = [
            {
                'role': 'system',
                'content': self.oracle.prompter.system_prompt
            },
            {
                'role': 'user',
                'content': f'Hello, given the scene {{{scene_graph}}}, I would like to know the instructions for: {scenario}'
            }
        ]

    def print_message(self, message, color=Fore.BLACK):
        if self.verbose:
            print(color + message + Fore.RESET)

    def generate(self):
        # Set print color to green
        self.print_message(f'Robot: {self.history[1]["content"]}', Fore.GREEN)

        # Get the initial instructions from the Oracle
        instructions = self.oracle.get_initial_instructions()
        self.print_message(f'Oracle: {instructions}', Fore.MAGENTA)
        self.history.append({
            'role': 'assistant',
            'content': instructions
        })

        # Set the instructions for the robot
        self.robot.set_instructions(instructions)

        # Get the humanoid's response
        question = self.robot.prompt(self.robot.user_prompt)
        self.print_message(f'Robot: {question}', Fore.GREEN)
        self.history.append({
            'role': 'user',
            'content': question
        })

        for i in range(self.num_iterations):
            answer = self.oracle.prompt(question)
            self.print_message(f'Oracle: {answer}', Fore.MAGENTA)
            self.history.append({
                'role': 'assistant',
                'content': answer
            })

            # Send the Oracle's response to the humanoid
            question = self.robot.prompt(f"""The oracle said: {answer}. What do you want to know next? If you have all the information for completing the task, respond with 'done'""")
            self.print_message(f'Robot: {question}', Fore.GREEN)
            self.history.append({
                'role': 'user',
                'content': question
            })

            if "done." in question.lower() or "'done'" in question.lower():
                break

        # Summarize the conversation
        self.print_message('Summarizing conversation...', Fore.YELLOW)
        summarizer_prompt = f"Here is the conversation history: {json.dumps(self.history)}."
        summarizer_prompt += f" Keeping in mind the scenario: {self.scenario}, summarize the conversation. Final instructions should be arranged logically and have all the necessary steps without any irrelevant information or redundant steps."
        summary = self.summarizer.prompt(json.dumps(self.history))

        try:
            pretty_summary = json.dumps(json.loads(summary), indent=4)
            self.print_message(f'{pretty_summary}', Fore.MAGENTA)
        except json.JSONDecodeError:
            self.print_message(f'{summary}', Fore.MAGENTA)

        # Export the conversation
        self.print_message('Exporting conversation...', Fore.YELLOW)
        self.export_conversation(summary)

        return summary, self.history

    @property
    def message_history(self):
        return self.prompter.messages

    def export_conversation(self, summary):
        history_file = f'{self.output_dir}/conversation_{self.conversation_id}.json'
        history_dir = os.path.dirname(history_file)
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        with open(history_file, 'w') as f:
            history = self.history
            history = json.dumps(history, indent=4)
            f.write(history)

        summary_file = f'{self.output_dir}/conversation_{self.conversation_id}_summary.json'
        with open(summary_file, 'w') as f:
            f.write(summary)


class Robot(PromptingStrategy):
    def __init__(self, scenario):
        super().__init__(init_cfg='configs/robot.py')
        self.user_prompt.set('scenario', scenario)

    def set_instructions(self, instructions):
        self.user_prompt.set('instructions', instructions)


class Oracle(PromptingStrategy):
    def __init__(self, scene_graph, scenario):
        super().__init__(init_cfg='configs/oracle.py')
        self.user_prompt.set('scene_graph', f"{{{scene_graph}}}")
        self.user_prompt.set('scenario', scenario)

    def get_initial_instructions(self):
        return self.prompt(self.user_prompt)

    def prompt(self, prompt: Prompt | str, role: str = 'user') -> str:
        if isinstance(prompt, str):
            # Remove $ signs from the prompt, as it is reserved for variables
            # and this chatbot only supports variables in the initial prompts
            prompt = prompt.replace('$', '')

        return super().prompt(prompt, role)


def main():
    # Load the dataset
    print('----------------------------------------------------------')
    print("Loading dataset... ", end='')
    dataset = json.load(open('data/3DSSG/raw/scenarios_refined.json', 'r'))['scans']
    num_samples = len(dataset)

    # Load existing instructions if any
    save_path = 'data/3DSSG/instructions_lq.json'
    start_idx = 0
    if os.path.exists(save_path):
        instructions = json.load(open(save_path, 'r'))
        print(f"Loaded {len(instructions)} instructions from {save_path}")
    else:
        # Create an empty list to store the generated instructions
        instructions = []

    # Filter out bad instructions and index the instructions for faster lookup
    filtered = []
    index = []
    for item in instructions:
        key = f"{item['scan_id']}-{item['scenario']}"
        instruct = item['instructions']
        if not instruct.startswith('Error: Error code'):
            filtered.append(item)
            index.append(key)
    instructions = filtered
    num_instructions = len(instructions)
    print(f"{num_instructions} of {num_samples} already generated. {num_samples - num_instructions} remaining.")

    # Initialize empty lists for sorting
    generated_instructions = []
    non_generated_instructions = []

    # Iterate over the dataset and separate generated and non-generated instructions
    for item in dataset:
        key = f"{item['scan']}-{item['scenario']}"
        if key in index:
            generated_instructions.append(item)
        else:
            non_generated_instructions.append(item)

    # Combine the lists, putting generated instructions first
    non_generated_instructions = sorted(non_generated_instructions, key=lambda x: x['scan'])
    dataset = generated_instructions + non_generated_instructions

    # Iterate over the dataset
    num_skipped = 0
    for item in tqdm(dataset[start_idx:], desc='Generating instructions'):
        scan_id = item['scan']
        scenario = item['scenario']
        key = f"{scan_id}-{scenario}"
        if key in index:
            continue

        scene_graph = SceneGraph(**{
            "objects": item['scenario_objects'],
            "relations": item['scenario_relations']
        })

        # Start the autobot
        generator = InstructionsGenerator(
            scene_graph,
            scenario, 
            num_iterations=3,
            output_dir='out/3DSSG_Correct_LQ_Filtered',
            verbose=False
        )
        attempt = True
        num_attempts = 0
        while attempt:
            try:
                summary, history = generator.generate()
                attempt = False
                instructions.append({
                    'scan_id': scan_id,
                    'scenario': scenario,
                    'instructions': summary,
                    'conversation': history
                })
            except RateLimitError:
                num_attempts += 1
                if num_attempts > 3:
                    attempt = False
                    print(f"Rate limit exceeded. Skipping {key}...")
                    num_skipped += 1
                    # if num_skipped > 10:
                    #     print("Too many rate limit errors. Exiting...")
                    #     exit()
                else:
                    wait_time = 30
                    print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"Error generating instructions for {key}: {e}")
                attempt = False
                num_skipped += 1
                # if num_skipped > 10:
                #     print("Too many errors. Exiting...")
                #     exit()
            
        # Save the instructions at each 100th iteration
        with open(save_path, 'w') as f:
            json.dump(instructions, f, indent=4)

    # Save final instructions
    with open(save_path, 'w') as f:
        json.dump(instructions, f, indent=4)

if __name__ == '__main__':
    main()
