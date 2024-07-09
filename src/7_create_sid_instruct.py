import json
import os
import random
random.seed(42)

import tiktoken
from tqdm import tqdm

# Local imports
from utils import SceneGraph, load_3dssg


def create_sample(messages):
    return {
        "messages": [{
            "role": m['role'],
            "content": m['content']
        } for m in messages]
    }


def create_scene_graph_pruning(scene_graph, scenario, pruned_scene_graph):
    messages = [
        {
            "role": "user",
            "content": f"Given the scene graph {scene_graph}, prune it to get a specialized graph for the scenario: {scenario}"
        },
        {
            "role": "assistant",
            "content": f"{pruned_scene_graph}"
        }
    ]
    return create_sample(messages)


def create_scenario_objects(scene_graph, scenario, pruned_scene_graph):
    scene_objects_ = list(scene_graph.objects.keys())
    scene_objects_ = set([o.split('-')[0] for o in scene_objects_])
    scene_objects = ', '.join(scene_objects_)

    scenario_objects_ = list(pruned_scene_graph.objects.keys())
    scenario_objects_ = set([o.split('-')[0] for o in scenario_objects_])
    scenario_objects = ', '.join(scenario_objects_)

    not_scenario_objects = ', '.join(list(scene_objects_ - scenario_objects_))

    # Positive samples.
    messages = [
        {
            "role": "user",
            "content": f"Given the scene graph {scene_graph}, which objects do I need to perform the task: {scenario}?"
        },
        {
            "role": "assistant",
            "content": scenario_objects
        }
    ]
    s1 = create_sample(messages)
    messages = [
        {
            "role": "user",
            "content": f"Given an indoor scene comprising {scene_objects}, which items are required for task: {scenario}?"
        },
        {
            "role": "assistant",
            "content": scenario_objects
        }
    ]
    s2 = create_sample(messages)

    # Negative samples.
    messages = [
        {
            "role": "user",
            "content": f"Given the scene graph {scene_graph}, which objects do I not need for the task: {scenario}?"
        },
        {
            "role": "assistant",
            "content": not_scenario_objects
        }
    ]
    s3 = create_sample(messages)
    messages = [
        {
            "role": "user",
            "content": f"Given an indoor scene with {scene_objects}, which objects are irrelevant for the scenario: {scenario}?"
        },
        {
            "role": "assistant",
            "content": not_scenario_objects
        }
    ]
    s4 = create_sample(messages)

    # Object existence.
    sn = []
    for name in scene_objects_:
        messages = [
            {
                "role": "user",
                "content": f"In a real-world scene containing {scene_objects}, do I need the object {name} to complete the task: {scenario}?"
            },
            {
                "role": "assistant",
                "content": "Yes" if name in pruned_scene_graph.objects else "No"
            }
        ]
        sn.append(create_sample(messages))

    s = [s1, s2, s3, s4]
    s.extend(sn)
    return s


def create_instruction_sample(scene_graph, scenario, pruned_scene_graph, instructions):
    instructions = list(json.loads(instructions).values())
    instructions_ = ''
    for i, instruction in enumerate(instructions):
        instructions_ += f"{i + 1}. {instruction}\n"

    messages = [
        {
            "role": "user",
            "content": f"Given the scene {scene_graph}, what steps do I need to perform the task: {scenario}?"
        },
        {
            "role": "assistant",
            "content": instructions_
        }
    ]
    s1 = create_sample(messages)
    messages = [
        {
            "role": "user",
            "content": f"How do I perform the task: {scenario} in a real-world scene, given a partial scene graph {pruned_scene_graph}?"
        },
        {
            "role": "assistant",
            "content": instructions_
        }
    ]
    s2 = create_sample(messages)

    return [s1, s2], instructions_


def count_tokens(data_path):
    with open(data_path) as f:
        data = json.load(f)

    user_messages = ''
    assistant_messages = ''
    for item in data:
        for message in item['messages']:
            if message['role'] == 'user':
                user_messages += message['content'] + '\n'
            else:
                assistant_messages += message['content'] + '\n'

    encoding = tiktoken.get_encoding("cl100k_base")
    user_tokens = encoding.encode(user_messages) 
    assistant_tokens = encoding.encode(assistant_messages) 

    return len(user_tokens) / 1e6, len(assistant_tokens) / 1e6



def jsonl2gemma(infile, outfile):
    """ Convert JSONL-based GPT-format instruct data to Gemma format CSV."""
    # Check input file
    if not os.path.exists(infile) or not infile.endswith('.jsonl'):
        raise ValueError(
            f'Input file {infile} does not exist or is not a JSONL file')

    # Load GPT data
    with open(infile, 'r') as f:
        data = [json.loads(l) for l in f.readlines()]

    # Convert to Gemma format
    converted = 'prompt\n'
    for d in data:
        messages = d['messages']
        content = '"<bos>'
        for m in messages:
            text = m['content']
            text = text.replace('"', '""')

            role = m['role']
            if role != 'user':
                role = 'model'

            content += f'<start_of_turn>{role}\n{text}<end_of_turn>\n'
        content += '<eos>"'
        converted += f'{content}\n'

    # Write to file
    outdir = os.path.dirname(outfile)
    os.makedirs(outdir, exist_ok=True)
    with open(outfile, 'w') as f:
        f.write(converted)


def create_sid_instruct(sid_path):
    # Define paths.
    scenarios_file = os.path.join(sid_path, 'raw', 'scenarios_refined.json')
    instructions_file = os.path.join(sid_path, 'instructions_lq.json')

    # Check files exist.
    assert os.path.exists(scenarios_file), f"{scenarios_file} not found."
    assert os.path.exists(instructions_file), f"{instructions_file} not found."

    # Load data.
    objects, relations = load_3dssg(os.path.join(sid_path, 'raw'))
    ssg = {
        k: SceneGraph(**{
            'objects': v,
            'relations': relations.get(k, [])
        }) for k, v in objects.items()
    }

    # Split scans into train and test.
    train_scans = random.sample(list(ssg.keys()), int(0.8 * len(ssg)))
    test_scans = list(set(ssg.keys()) - set(train_scans))
    print(f"Train scans: {len(train_scans)}")
    print(f"Test scans: {len(test_scans)}")

    # # Save splits info.
    # with open(os.path.join(sid_path, 'sid_train_scans.txt'), 'w') as f:
    #     f.write('\n'.join(train_scans))
    # with open(os.path.join(sid_path, 'sid_test_scans.txt'), 'w') as f:
    #     f.write('\n'.join(test_scans))

    print(f"Loaded {len(ssg)} scene graphs.")
    with open(scenarios_file, 'r') as f:
        scenarios = json.load(f)['scans']
        scenarios = {(i['scan'], i['scenario']): SceneGraph(**{
            'objects': i['scenario_objects'],
            'relations': i['scenario_relations']
        }) for i in scenarios}
        print(f"Loaded {len(scenarios)} scenarios.")
    with open(instructions_file, 'r') as f:
        instructions = json.load(f)
        instructions = {(i['scan_id'], i['scenario']): i for i in instructions}
        print(f"Loaded {len(instructions)} instructions.")

    # Create samples.
    train_samples = []
    test_samples = []
    num_train_scenarios = 0
    num_test_scenarios = 0
    for (scan_id, scenario), instruct in tqdm(instructions.items()):
        # Count scenarios.
        if scan_id in train_scans:
            num_train_scenarios += 1
        else:
            num_test_scenarios += 1

        samples = []

        scene_graph = ssg[scan_id]
        pruned_scene_graph = scenarios[(scan_id, scenario)]

        # samples.append(create_scene_graph_pruning(scene_graph, scenario, pruned_scene_graph))
        # samples.extend(create_scenario_objects(scene_graph, scenario, pruned_scene_graph))

        instruct_ = instruct['instructions']
        s, instruct_ = create_instruction_sample(scene_graph, scenario, pruned_scene_graph, instruct_)
        samples.extend(s)

        conversation = instruct['conversation'].copy()

        # Remove the first system message.
        conversation.pop(0)

        # If the last message is a user message, remove it.
        if conversation[-1]['role'] == 'user':
            conversation.pop()

        conversation.extend([
            {
                "role": "user",
                "content": f"Thank you. I think I have all the information I need to perform the task: {scenario}. Can you summarize the steps?"
            },
            {
                "role": "assistant",
                "content": instruct_
            }
        ])

        samples.append(create_sample(conversation))

        if scan_id in train_scans:
            train_samples.extend(samples)
        else:
            test_samples.extend(samples)

    print(f"Train scenarios: {num_train_scenarios}")
    print(f"Test scenarios: {num_test_scenarios}")

    # Save samples.
    print(f"Writing train samples: {len(train_samples)}")
    with open(os.path.join(sid_path, 'sid_instruct_train2.json'), 'w') as f:
        json.dump(train_samples, f)
    print(f"Writing test samples: {len(test_samples)}")
    with open(os.path.join(sid_path, 'sid_instruct_test2.json'), 'w') as f:
        json.dump(test_samples, f)

    # Write as JSONL.
    print("Writing JSONL files for fine-tuning GPT...")
    with open(os.path.join(sid_path, 'sid_instruct_train2.jsonl'), 'w') as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + '\n')
    with open(os.path.join(sid_path, 'sid_instruct_test2.jsonl'), 'w') as f:
        for sample in test_samples:
            f.write(json.dumps(sample) + '\n')

    # Write as Gemma CSV.
    print("Writing CSV files for fine-tuning Gemma...")
    jsonl2gemma(os.path.join(sid_path, 'sid_instruct_train2.jsonl'), os.path.join(sid_path, 'sid_instruct_train2.csv'))
    jsonl2gemma(os.path.join(sid_path, 'sid_instruct_test2.jsonl'), os.path.join(sid_path, 'sid_instruct_test2.csv'))

    # Count tokens.
    print("Counting train tokens...")
    in_tokens, out_tokens = count_tokens(os.path.join(sid_path, 'sid_instruct_train2.json'))
    print(f"Train input tokens: {in_tokens:.2f}M")
    print(f"Train output tokens: {out_tokens:.2f}M")
    print(f"Train total tokens: {in_tokens + out_tokens:.2f}M")

    print("Counting test tokens...")
    in_tokens, out_tokens = count_tokens(os.path.join(sid_path, 'sid_instruct_test2.json'))
    print(f"Test input tokens: {in_tokens:.2f}M")
    print(f"Test output tokens: {out_tokens:.2f}M")
    print(f"Test total tokens: {in_tokens + out_tokens:.2f}M")


if __name__ == '__main__':
    create_sid_instruct('data/3DSSG')
