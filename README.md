# Official Repository of Situational Awareness Database (SAD)

Situational Awareness Database (SAD) is a dataset for dynamic task guidance. It contains situationally-aware
instructions for performing a wide range of everyday tasks or completing scenarios in 3D environments. The dataset
provides step-by-step instructions for these scenarios which are grounded in the context of the situation. This
context is defined through a scenario-specific scene graph that captures the objects, their attributes, and their
relations in the environment. The dataset is designed to enable research in the areas of grounded language learning,
instruction following, and situated dialogue.

For complete documentation, please see the [dataset card](DATASET_CARD.md).

## Access Information

The complete dataset is available [online](https://huggingface.co/datasets/saifkhichi96/sad-instruct). To access the dataset, you need to sign up for a free account on Hugging Face and request access to the dataset. Access requests are manually reviewed and approved.

> [!NOTE]
> A demo is available [here](https://blog.mindgarage.de/situational-instructions-database/) to provide an overview of the dataset. This can be used to explore some samples from the dataset before requesting access.

This repository also contains source code for generating the dataset from scratch.

## Metadata

We provide the Croissant 🥐 metadata for SAD [here](croissant.json).

## Citation

 If you find the dataset useful, please cite the following paper:

```bibtex
@article{khan2025situational,
  author = { Khan, MSU and Afzal, MZ and Stricker, D},
  title = {SituationalLLM: Proactive Language Models with Scene Awareness for Dynamic, Contextual Task Guidance [version 1; peer review: awaiting peer review]},
  journal = {Open Research Europe},
  volume = {5},
  year = {2025},
  number = {61},
  doi = {10.12688/openreseurope.18551.1}
}
```

## License

The dataset is licensed under [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/deed.en) and the code under MIT License. By using the dataset, you agree to the terms of the license.
