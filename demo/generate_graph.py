import argparse
import json
import os.path as osp
import time
import re
import matplotlib.image as mpimg

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Local imports
from .prompting import LLM
from .scene_graph import SceneGraph


def generate_graph(image_path, save_dir=None):
    # Load the image
    image = mpimg.imread(image_path)

    llm = LLM(init_cfg='configs/image2scenegraph.py')
    llm.user_prompt.image_url = image_path

    print('### System ###')
    print(llm.backend.system_prompt)
    print('')

    print('### User ###')
    print(llm.user_prompt.template)
    print('IMAGE URL:', image_path)

    print('### Assistant ###')
    response = llm.prompt(llm.user_prompt)

    # Post-process the response
    response = response.lower().strip()
    response = re.sub(r'\n+', ' ', response)
    response = re.sub(r' +', ' ', response)
    response = response.replace(' -', '-')
    response = response.replace('- ', '-')
    response = response.replace('_', '-')
    response = re.sub(r'-+', '-', response)
    print(response)

    if save_dir:
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        save_file = image_path.split('/')[-1].split('.')[0] + f'_{timestamp}.json'
        save_path = osp.join(save_dir, save_file)
        history = llm.backend.messages
        with open(save_path, 'w') as f:
            history = json.dumps(history, indent=4)
            f.write(history)

    try:
        graph = SceneGraph.parse(response)
        save_path = save_path.replace('.json', '.png')
        graph.visualize(save_path, orig_img=image)
        print('Scene graph saved at:', save_path)
    except Exception as e:
        print('Error:', e)
        import traceback
        traceback.print_exc()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str,
                        help='Path to the image file.')
    parser.add_argument('--save_dir', type=str, default='out',
                        help='Directory to save the conversation.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    generate_graph(args.image_path,
                   args.save_dir)
