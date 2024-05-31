import argparse
import json
import os
import logging

from tqdm import tqdm

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from prompting import PromptingStrategy


logger = logging.getLogger('sid')
logger.setLevel(logging.INFO)


def parse_response(response):
    scenarios = []
    for line in response.split('\n'):
        # Preprocess to make the JSON parsable
        line = line.strip()
        if line.endswith(','):
            line = line[:-1]
        if line.startswith('['):
            line = line[1:]
        if line.endswith(']'):
            line = line[:-1]
        line = line.replace("'", '"')

        # Parse the JSON with error handling
        try:
            item = json.loads(line)
            assert isinstance(item, dict)

            scenario = item['scenario']
            assert isinstance(scenario, str)

            objects = item['objects']
            assert isinstance(objects, list)
            assert all(isinstance(o, str) for o in objects)

            scenarios.append(item)
        except Exception:
            pass

    return scenarios


def prompt_llm(object_list):
    cfg = dict(
        prompter_cfg=dict(
            type='GroqPrompter',
            init_cfg=dict(
                model='NousResearch/Meta-Llama-3-8B-Instruct',
                temperature=1.0,
                repetition_penalty=1.2,
                max_tokens=512,
            )),
        system_prompt_cfg=dict(
            role="system",
            template="Given a list of objects in a real-world environment, you can list down different scenarios that can arise in the environment. A scenario can be a task that one or more people complete in the environment, such as cooking a meal in a kitchen or playing a game in a park. It can also be a situation that arises in the environment, such as a fire breaking out in a building or a storm approaching a beach. When a user provides you the list of objects, your task is to generate a list of ten scenarios. For each scenario, you should provide a one-sentence description of the scenario and a list of objects that are involved in the scenario. Your response should be formatted as valid JSON with the following structure: [{'scenario': '...', 'objects': ['...', ...]}, ...]. Do not output more than ten scenarios or any additional information.",
        ),
        user_prompt_cfg=dict(
            role="user",
            template="Objects in the scene: $object_list. Generate a list of up to ten scenarios that can arise in this environment using the specified format. "
        ),
    )
    llm = PromptingStrategy(init_cfg=cfg)
    llm.user_prompt.set('object_list', object_list)
    return llm.prompt(llm.user_prompt)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        default="data/3DSSG/raw/",
                        help="Path to the 3DSSG dataset")
    parser.add_argument('--min_scenarios', type=int, default=5,
                        help="Minimum number of scenarios to generate for each scan")
    return parser.parse_args()


def main():
    args = parse_args()
    MIN_SCENARIOS = args.min_scenarios

    # Check if the objects file exists
    objects_file = os.path.join(args.data_dir, "objects.json")
    if not os.path.exists(objects_file):
        logger.error(f"File not found: {objects_file}")
        return

    # Load the 3DSSG dataset
    with open(objects_file, 'r') as f:
        objects = json.load(f)['scans']
        logger.info(f"Loaded {len(objects)} scans from {objects_file}")

    # Define save path
    scenarios_file = os.path.join(args.data_dir, "scenarios.json")
    logger.info(f"Saving scenarios to {scenarios_file}")

    # Read existing scenarios (if any)
    scenarios = []
    if os.path.exists(scenarios_file):
        with open(scenarios_file, 'r') as f:
            scenarios = json.load(f)['scans']
    logger.info(f"Found scenarios for {len(scenarios)} scans")

    # Index the existing scenarios
    dataset = {item['scan']: item for item in scenarios}

    try:
        # Continue generating scenarios for the remaining scans
        for item in tqdm(objects, desc="Generating scenarios"):
            # Look for existing scenarios
            scan_id = item['scan']
            existing_data = dataset.get(scan_id, {}).get('scenarios', [])

            # Get objects in the scene
            objects = [{
                'label': o['label'],                      # 'chair'
                'affordances': o.get('affordances', []),  # ['sit']
                'attributes': o['attributes'],            # {'color': ['red'], 'shape': ['round']}
            } for o in item['objects']]
            available_objects = {o['label'] for o in objects}

            # Filter out scenarios with non-matching or non-string objects
            # This is to avoid scenarios with objects that are not in the scene, or invalid objects (from an earlier version of the script)
            existing_data_ = []
            s_ids = []  # to remove duplicates (because of an earlier bug in the script)
            for s in existing_data:
                if s['scenario'] in s_ids:
                    continue

                keep = True
                for o in s['objects']:
                    if not isinstance(o, str):
                        keep = False
                        break
                    if o not in available_objects:
                        keep = False
                        break

                if keep:
                    s_ids.append(s['scenario'])
                    existing_data_.append(s) 
            existing_data = existing_data_

            # Prompt the LLM for scenarios
            num_attempts = 0
            while len(existing_data) < MIN_SCENARIOS:
                num_attempts += 1
                if num_attempts > 3:
                    break

                response = prompt_llm(objects)
                new_scenarios = parse_response(response)

                # Filter out scenarios with non-matching objects
                new_scenarios = [s for s in new_scenarios if all(o in available_objects for o in s['objects'])]

                # Add the new scenarios
                existing_data += new_scenarios

            # Extend the existing scenarios
            dataset[scan_id] = dataset.get(scan_id, {'scan': scan_id})
            dataset[scan_id]['scenarios'] = existing_data[:MIN_SCENARIOS]  # Limit to MIN_SCENARIOS
    except KeyboardInterrupt:
        logger.info("Interrupted. Saving the progress...")
    except Exception as e:
        logger.error(f"Error: {e}. Saving the progress...")

    # Compute and print stats
    num_scans = len(dataset)
    num_scenarios = sum(len(item['scenarios']) for item in dataset.values())
    print(f"Loaded {num_scenarios} scenarios from {num_scans} scans")

    # Convert the dataset to a list
    scenarios = list(dataset.values())

    # Save the scenarios
    with open(scenarios_file, 'w') as f:
        json.dump({'scans': scenarios}, f, indent=4)


if __name__ == "__main__":
    main()
