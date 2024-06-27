from typing import List
from core import classes


# Agent flow (always return non-streaming response)
class Agent:
    tool_choice = ""
    tool = None
    prompt = ""

    def __init__(
        self, tools: List[classes.ToolSetting], prompt: str, tool_choice: str = "any"
    ):
        # Force the model to call at least one tool
        tool = None
        if tool_choice == "any":
            # @TODO We may support an llm call to determine which tool is appropriate
            # For now we pick the first tool
            tool = tools[0]
        # Choose the specified tool
        else:
            tool_index = tools.index(
                tool_choice
            )  # name of tool you want model to always call
            tool = tools[tool_index]
        self.tool = tool
        self.tool_choice = tool_choice
        self.prompt = prompt

    # Get the actual function using the provided path
    def get_tool_function(self, path: str):
        is_url = path.startswith("https://")
        def tool_func(a, b):
            return a + b
        # @TODO Construct api call for cloud func
        if is_url:
            return tool_func
        # @TODO Load a local func from `/tools/functions`
        else:
            return tool_func

    # Pass the text response which includes the function params
    def eval(self, response_args: str):
        # pass llm response to function
        path = self.tool["path"]
        tool_function = self.get_tool_function(path)
        # @TODO Convert response text from json to an object containing args
        args = response_args
        return tool_function(**args)

    # Return a prompt injected with all tool's descriptions
    def get_tools_prompt(self):
        prompt_instruction = (
            f"Consider this prompt when using the function defined below: {self.prompt}"
        )
        pre_instruction = f"Read the following description for the '{self.tool["name"]}' function and shape your response in a way that maps inputs from the given prompt to arguments."
        # @TODO This must construct an example based on the tool's params. Parse out only the args.
        response_example = f"```\n{self.tool["args"]}\n```"
        post_instruction = f"Ensure your response is in json format. Here is an example:\n{response_example}"
        resp = (
            prompt_instruction
            + "\n\n"
            + pre_instruction
            + "\n"
            + self.tool["description"]
            + "\n"
            + post_instruction
        )
        return resp
