import argparse
import json
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True,
                        default='data/3DSSG/finetune/ft_train_gpt.jsonl',
                        help='Path to the GPT-style fine-tuning data')
    parser.add_argument('--output', type=str, required=True,
                        default='data/3DSSG/finetune/ft_train_gemma.csv',
                        help='Path to the Gemma-style fine-tuning data')
    return parser.parse_args()


def gpt2gemma(infile, outfile):
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
        content = ''
        for m in messages:
            text = m['content']
            text = text.replace('"', '""')

            role = m['role']
            if role != 'user':
                role = 'model'

            content += f'"<start_of_turn>{role}\n{text}<end_of_turn>"\n'
        converted += f'{content}\n'

    # Write to file
    outdir = os.path.dirname(outfile)
    os.makedirs(outdir, exist_ok=True)
    with open(outfile, 'w') as f:
        f.write(converted)


def main():
    args = parse_args()
    gpt2gemma(args.input, args.output)


if __name__ == '__main__':
    main()
