'''
This script prepares the serialized data for the LaSCo, Fashion-iq and CIRR datasets.
This allows blazing fast data loading during training and evaluation, with low IO overhead.

Author : Sankalp Sinha
Email : sankalpsinhawork@gmail.com
'''
import os
import json

from PIL import Image
from functools import partial
from litdata import optimize

from models.clip import tokenize


# 0. Parse the arguments
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Serialize LaSCo dataset')
    # For LaSCo
    parser.add_argument('--coco_images_dir', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/lasco/coco_images',
                        help='Absolute path to the directory containing the coco images: train2014 and val2014')
    parser.add_argument('--output_dir', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/lasco/serialized',
                        help='Absolute path to the directory where the serialized data will be stored for the LaSCo dataset')
    parser.add_argument('--annotation_path', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/lasco/annotations',
                        help='Path to the directory containing the annotations for the LaSCo dataset')
    # For Fashion-iq
    parser.add_argument('--fiq_images_dir', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/fashion-iq/images',
                        help='Absolute path to the directory containing the images for the Fashion-iq dataset')
    parser.add_argument('--fiq_output_dir', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/fashion-iq/serialized',
                        help='Absolute path to the directory where the serialized data will be stored for the Fashion-iq dataset')
    parser.add_argument('--fiq_caption_annotation_path', type=str, default='/home/ssinha/projects/active/cir/assets/cir_data/fashion-iq/annotations/captions',
                        help='Path to the directory containing the caption annotations for the Fashion-iq dataset')
    # Common
    parser.add_argument('--train_only', action='store_true',
                        help='Serialize only the training set')
    parser.add_argument('--val_only', action='store_true',
                        help='Serialize only the validation set')
    parser.add_argument('--cpus', type=int, default=4,
                        help='Number of workers to use for serialization')
    parser.add_argument('--dataset', type=str, default='lasco', choices=['lasco', 'fashion-iq', 'cirr'],
                        help='Name of the dataset')
    return parser.parse_args()


############################################################ Logic for LaSCo dataset ############################################################

# 1. Define a function to converts the annotations into a format that can be serialized
def serialize_data(coco_images_dir, annotations, tokenizer, index):
    '''
    This function converts each annotation of the LaSCo dataset serialized data and write it to disk
    '''
    data = {
        "index" : index, # This is used to keep track of the index of the data
        "qid" : annotations[index]["qid"], # unique identifier for the annotation
        "query-image-id" : annotations[index]["query-image"][0], # query image id in COCO val2014 annotations
        "target-image-id" : annotations[index]["target-image"][0], # target image id in COCO val2014 annotations
        "query-image-path" : annotations[index]["query-image"][1], # relative query image path
        "target-image-path" : annotations[index]["target-image"][1], # relative target image path
        "query-text" : annotations[index]["query-text"], # query text
        "query-image" : Image.open(os.path.join(coco_images_dir, annotations[index]["query-image"][1])), # query image
        "target-image" : Image.open(os.path.join(coco_images_dir, annotations[index]["target-image"][1])), # target image
        "query-text-tokens" : tokenizer(annotations[index]["query-text"], truncate=True), # query text tokens using CLIP tokenizer
    }
    yield data


# 3. Define a function to call the serialize_data function
def call_serialize_data(coco_images_dir, annotations, tokenizer, output_dir, num_workers):
    '''
    This function calls the serialize_data function to serialize each annotation in the LaSCo dataset
    '''
    os.makedirs(output_dir, exist_ok=True)
    optimize(
        fn=partial(serialize_data, coco_images_dir, annotations, tokenizer),
        inputs=list(range(len(annotations))),
        output_dir=output_dir,
        chunk_size = (2049 * 8012), # Number of tokens to store by chunks. This is roughly 64MB of tokens per chunk.
        num_workers=num_workers,
        fast_dev_run=False,
        )


def preapre_lasco(args):
    '''
    This function prepares the serialized LaSCo dataset
    Input:
    - args.annotation_path: Path to the directory containing the annotations for the LaSCo dataset
    - args.coco_images_dir: Absolute path to the directory containing the coco images: train2014 and val2014
    - args.output_dir: Absolute path to the directory where the serialized data will be stored
    - args.train_only: Serialize only the training set
    - args.val_only: Serialize only the validation set
    - args.num_workers: Number of workers to use for serialization
    '''
    # 1. Load the annotations
    train_annotations = json.load(open(os.path.join(args.annotation_path, 'lasco_train.json'), "r"))
    val_annotations = json.load(open(os.path.join(args.annotation_path, 'lasco_val.json'), "r"))

    # 2. Nmber of triplets in the training and validation set
    print(f'-'*50)
    print(f'Num Train Triplets : {len(train_annotations)}')
    print(f'Num Val Triplets : {len(val_annotations)}')
    print(f'Num Total Triplets : {len(val_annotations) + len(train_annotations)}')
    print(f'-'*50)

    # 3. Serialize the data
    if args.train_only:
        print(f'Serializing the training set only...')
        call_serialize_data(coco_images_dir = args.coco_images_dir,
                            annotations = train_annotations,
                            tokenizer = tokenize,
                            output_dir = os.path.join(args.output_dir, 'train'),
                            num_workers = args.cpus)
    elif args.val_only:
        print(f'Serializing the validation set only...')
        call_serialize_data(coco_images_dir = args.coco_images_dir,
                            annotations = val_annotations,
                            tokenizer = tokenize,
                            output_dir = os.path.join(args.output_dir, 'val'),
                            num_workers = args.cpus)
    else:
        print(f'Serializing the validation set...')
        call_serialize_data(coco_images_dir = args.coco_images_dir,
                            annotations = val_annotations,
                            tokenizer = tokenize,
                            output_dir = os.path.join(args.output_dir, 'val'),
                            num_workers = args.cpus)
        print(f'Serializing the training set...')
        call_serialize_data(coco_images_dir = args.coco_images_dir,
                            annotations = train_annotations,
                            tokenizer = tokenize,
                            output_dir = os.path.join(args.output_dir, 'train'),
                            num_workers = args.cpus)

############################################################ Logic for Fashion-iq dataset ############################################################

def serialize_fashion_iq_data(fiq_images_dir, annotations, tokenizer, split, index):
    '''
    This function converts each annotation of the Fashion-iq dataset serialized data and write it to disk
    '''
    # NOTE: Here candidate -> query, target -> target
    if split == 'train' or split == 'val':
        data = {
            "index" : index, # This is used to keep track of the index of the data
            "query-image-id" : annotations[index]["candidate"], # unique identifier for the annotation
            "target-image-id" : annotations[index]["target"], # target image id in COCO val2014 annotations
            "captions" : annotations[index]["captions"], # query text
            "query-image" : Image.open(os.path.join(fiq_images_dir, annotations[index]["candidate"]) + '.png'), # relative query image path
            "target-image" : Image.open(os.path.join(fiq_images_dir, annotations[index]["target"]) + '.png'), # relative target image path
            "captions-tokens" : tokenizer(annotations[index]["captions"], truncate=True), # query text tokens using CLIP tokenizer
        }
    else:
        data = {
            "index" : index, # This is used to keep track of the index of the data
            "captions" : annotations[index]["captions"], # query text
            "query-image-id" : annotations[index]["candidate"], # unique identifier for the annotation
            "query-image" : Image.open(os.path.join(fiq_images_dir, annotations[index]["candidate"]) + '.png'), # relative query image path
            "captions-tokens" : tokenizer(annotations[index]["captions"], truncate=True), # query text tokens using CLIP tokenizer
        }
    yield data


def prepare_fashion_iq(args):
    # 0. Fetch the annotation files
    files = os.listdir(args.fiq_caption_annotation_path)
    assert len(files) == 9, f'Expected 8 caption annotation json files in the directory, found {len(files)}. Refer to : https://github.com/XiaoxiaoGuo/fashion-iq'

    # 1. Process each annotation file
    for file in sorted(files):
        if file.endswith('.json'):
            category, split = file.split('.')[1:3]
            print(f'Serializing:- Category : {category} | Split : {split}...')
            annotations = json.load(open(os.path.join(args.fiq_caption_annotation_path, file), "r"))
            print(f'Num Annotations : {len(annotations)}')

            # build the output directory
            output_dir = os.path.join(args.fiq_output_dir, category, split)
            os.makedirs(output_dir, exist_ok=True)

            optimize(
                fn=partial(serialize_fashion_iq_data, args.fiq_images_dir, annotations, tokenize, split),
                inputs=list(range(len(annotations))),
                output_dir=output_dir,
                chunk_size = (2049 * 8012), # Number of tokens to store by chunks. This is roughly 64MB of tokens per chunk.
                num_workers=args.cpus,
                fast_dev_run=False,
                )
            print(f"Done serializing {category} | {split} for Fashion-iq dataset !")
    
############################################################ Logic for CIRR dataset ############################################################
# TODO: Add logic for serializing CIRR dataset
def prepare_ciir(args):
    raise NotImplementedError('CIRR dataset serialization is not implemented yet')


if __name__ == '__main__':
    args = parse_args()
    if args.dataset == 'lasco':
        preapre_lasco(args)
    elif args.dataset == 'fashion-iq':
        prepare_fashion_iq(args)
    elif args.dataset == 'cirr':
        prepare_ciir(args)
    else:
        raise ValueError(f'Invalid dataset name: {args.dataset}')
