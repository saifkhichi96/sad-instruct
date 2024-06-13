---
# For reference on dataset card metadata, see the spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md?plain=1
# Doc / guide: https://huggingface.co/docs/hub/datasets-cards
---

# Dataset Card for Situational Instructions Database

<!-- Provide a quick summary of the dataset. -->

SID: Situational Instructions Database for dynamic task guidance in 3D environments.

## Dataset Details

### Dataset Description

<!-- Provide a longer summary of what this dataset is. -->

Situational Instructions Database (SID) is a dataset for dynamic task guidance. It contains situationally-aware
instructions for performing a wide range of everyday tasks or completing scenarios in 3D environments. The dataset
provides step-by-step instructions for these scenarios which are grounded in the context of the situation. This
context is defined through a scenario-specific scene graph that captures the objects, their attributes, and their
relations in the environment. The dataset is designed to enable research in the areas of grounded language learning,
instruction following, and situated dialogue.

- **Curated by:** Saif Khan
- **Language(s) (NLP):** English
- **License:** CC-BY-4.0

### Dataset Sources

<!-- Provide the basic links for the dataset. -->

- **Repository:** https://github.com/mindgarage/situational-instructions-database
- **Paper:** [Situational Instructions Database: Task Guidance in Dynamic Environments](#)
- **Demo:** https://blog.mindgarage.de/situational-instructions-database/

## Uses

<!-- Address questions around how the dataset is intended to be used. -->

### Direct Use

<!-- This section describes suitable use cases for the dataset. -->

- **Instruction Following:** The dataset can be used to train models for instruction following in dynamic environments.
- **Grounded Language Learning:** The dataset can be used to train models for grounded language learning tasks.
- **Situated Dialogue:** The dataset can be used to train models for situated dialogue tasks.

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the dataset will not work well for. -->

Any use that involves the dataset in a way that is not aligned with the license is out-of-scope.


## Dataset Structure

<!-- This section provides a description of the dataset fields, and additional information about the dataset structure such as criteria used to create the splits, relationships between data points, etc. -->

Each sample in the dataset consists of the following fields:
```json
{
    "scan": datasets.Value("string"),
    "scenario": datasets.Value("string"),
    "objects": datasets.Sequence(
        {
            "global_id": datasets.Value("string"), # global instance id from 3DSSG.zip/classes.txt
            "id": datasets.Value("string"), # instance id from 3RScans semseg.json
            "label": datasets.Value("string"),
            "ply_color": datasets.Value("string"), # ply color from 3RScans labels.instances.annotated.ply
            "affordances": datasets.Sequence(datasets.Value("string")),
            "attributes": {
                "texture": datasets.Sequence(datasets.Value("string")),
                "lexical": datasets.Sequence(datasets.Value("string")),
                "color": datasets.Sequence(datasets.Value("string")),
                "material": datasets.Sequence(datasets.Value("string")),
                "shape": datasets.Sequence(datasets.Value("string"))
            }
        }
    ),
    "instructions": datasets.Value("string"),
    "conversation": datasets.Sequence(
        {
            "role": datasets.Value("string"),
            "content": datasets.Value("string"),
        }
    )
}
```

## Dataset Creation

### Curation Rationale

<!-- Motivation for the creation of this dataset. -->

This dataset was created to address a gap in the availability of situationally-aware task guidance datasets. It is designed to enable research in the areas of grounded language learning, instruction following, and situated dialogue.

### Source Data

<!-- This section describes the source data (e.g. news text and headlines, social media posts, translated sentences, ...). -->

This dataset is built on top of the [3DSSG](https://github.com/3DSSG/3DSSG.github.io/) and [3RScan](https://github.com/WaldJohannaU/3RScan) datasets.


#### Data Collection and Processing

<!-- This section describes the data collection and processing process such as data selection criteria, filtering and normalization methods, tools and libraries used, etc. -->

For each scan in 3RScan, we propose a set of scenarios that can be performed in the environment. Pruning the corresponding 3DSSG scene graph, we obtain a scenario-specific scene graph that captures the objects, their attributes, and their relations in the environment. We then generate step-by-step instructions for these scenarios which are grounded in the context of the situation. These instructions are collected through a dialogue-based process. In addition to the instructions, we also collect conversations that occur during instruction following.

#### Who are the source data producers?

<!-- This section describes the people or systems who originally created the data. It should also include self-reported demographic or identity information for the source data creators if this information is available. -->

The source data producers are the authors of the 3DSSG and 3RScan datasets.

### Annotations

<!-- If the dataset contains annotations which are not part of the initial data collection, use this section to describe them. -->

#### Annotation process

<!-- This section describes the annotation process such as annotation tools used in the process, the amount of data annotated, annotation guidelines provided to the annotators, interannotator statistics, annotation validation, etc. -->

Please refer to the [paper](#) for more details on the annotation process.

#### Who are the annotators?

<!-- This section describes the people or systems who created the annotations. -->

The annotations were created through a combination of multiple LLM agents with some human evaluators in the loop. For more details, please refer to the [paper](#).

## Citation

<!-- If there is a paper or blog post introducing the dataset, the APA and Bibtex information for that should go in this section. -->

**BibTeX:**

```bibtex
@InProceedings{huggingface:dataset,
    title = {Situational Instructions Database (SID)},
    author={Khan, Muhammad Saif Ullah and Sinha, Sankalp and Afzal, Muhammad Zeshan and Stricker, Didier},
    year={2024}
}
```

**APA:**

Khan, M. S. U., Sinha, S., Afzal, M. Z., & Stricker, D. (2024). Situational Instructions Database (SID).

