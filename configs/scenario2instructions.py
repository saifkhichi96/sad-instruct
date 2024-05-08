dict(
    prompter_cfg="configs/prompter/hf-llama-3.yaml",
    system_prompt_cfg=dict(
        role="system",
        template="""
        def generate_instructions(scene_graph: Dict, scenario: str) -> List[str]:
            ''' Generates step-by-step instructions for the given scenario.

            The instructions should be detailed enough for a human to follow to effectively complete the task described
            in the scenario. For example, if the scenario is "Person A wants to make coffee" and the scene graph shows a
            kitchen with various objects, the instructions should include steps which Person A needs to take, starting
            from their current location, to make coffee.

            Args:
                scene_graph: A dictionary containing information about the location, setting, objects, their relations,
                    and attributes.
                scenario: A string describing a task to be completed in the scene.

            Returns:
                A list of strings, where each string is a single instruction.
            '''

            Given an input photo of a scene, along with its corresponding detected objects and predicted scene graph, generate step-by-step instructions for completing a specific task in the given scenario.
        """,
    ),
    user_prompt_cfg=dict(
        role="user",
        template="""
        print(generate_instructions($scene_graph, $scenario))

        Please only respond with a JSON list of strings containing the instructions, and do not output anything else.
        """,
        parameters=dict(
            # Parameter values (e.g. $scenario) can be specified here if desired
        ),
    ),
)
