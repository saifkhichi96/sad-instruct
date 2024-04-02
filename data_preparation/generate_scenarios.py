import json
import os
from json.decoder import JSONDecodeError
from tqdm import tqdm

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from prompting import PromptingStrategy


# Load the 3DSSG dataset
data_path = "data/3DSSG/raw/objects.json"
with open(data_path, 'r') as f:
    dataset = json.load(f)['scans']

save_path = "data/3DSSG/scenarios/"
os.makedirs(save_path, exist_ok=True)


def save_response(response, scan, save_file):
    # Try to decode the response as JSON
    scenarios = []
    response = response.split('\n')
    for scenario in response:
        try:
            # Remove extra whitespace and any trailing commas or brackets
            scenario = scenario.strip()
            if scenario.endswith(','):
                scenario = scenario[:-1]
            if scenario.startswith('['):
                scenario = scenario[1:]
            if scenario.endswith(']'):
                scenario = scenario[:-1]

            # Replace all single quotes with double quotes
            scenario = scenario.replace("'", '"')

            scenario = json.loads(scenario)
            scenarios.append(scenario)
        except JSONDecodeError:
            pass

    # Filter invalid scenarios
    valid_scenarios = []
    for scenario in scenarios:
        if 'scenario' in scenario and 'objects' in scenario:
            valid_scenarios.append(scenario)

    # Read existing data if file exists
    if os.path.exists(save_file):
        with open(save_file, 'r') as f:
            existing_data = json.load(f)
            valid_scenarios.extend(existing_data['scenarios'])

    # Write the valid scenarios to a file
    scan['scenarios'] = valid_scenarios
    with open(save_file, 'w') as f:
        json.dump(scan, f, indent=4)


for scan in tqdm(dataset):
    scan_id = scan['scan']
    objects = scan['objects']
    obj_labels = [{
        'label': obj['label'],
        'affordances': obj['affordances'] if 'affordances' in obj else [],
        'attributes': obj['attributes'],
    } for obj in objects]

    # Create a prompting strategy
    strategy = PromptingStrategy(init_cfg=dict(
        prompter_cfg='configs/prompter/gpt-3.5-turbo.yaml',
        system_prompt_cfg=dict(
            role="system",
            template="Given a list of objects in a real-world environment, you can list down different scenarios that can arise in the environment. A scenario can be a task that one or more people complete in the environment, such as cooking a meal in a kitchen or playing a game in a park. It can also be a situation that arises in the environment, such as a fire breaking out in a building or a storm approaching a beach. When a user provides you the list of objects, your task is to generate a list of ten scenarios. For each scenario, you should provide a one-sentence description of the scenario and a list of objects that are involved in the scenario. Your response should be formatted as valid JSON with the following structure: [{'scenario': '...', 'objects': ['...', ...]}, ...]. Do not output more than ten scenarios or any additional information.",
        ),
        user_prompt_cfg=dict(
            role="user",
            template="Objects in the scene: $object_list. Generate a list of up to ten scenarios that can arise in this environment using the specified format. "
        ),
    ))

    # Prompt the LLM for scenarios
    strategy.user_prompt.set('object_list', obj_labels)
    response = strategy.prompt(strategy.user_prompt)

    # Export the scenarios to a file
    save_file = os.path.join(save_path, f'{scan_id}.json')
    save_response(response, scan, save_file)
