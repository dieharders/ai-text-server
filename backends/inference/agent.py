import json
import os
from typing import Any, List
from core import classes
import importlib.util
from core import common


# Load the code module and pydantic model for the tool (from `/public/tools/functions`)
def load_function_file(filename: str):
    func_name = os.path.splitext(filename)[0]
    path = common.dep_path(os.path.join("public", "tools", "functions", filename))
    # file name and function name must be the same!
    spec = importlib.util.spec_from_file_location(
        name=filename,
        location=path,
    )
    tool_code = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool_code)
    tool_func = getattr(tool_code, func_name)
    pydantic_model_name = "Params"
    pydantic_model = getattr(tool_code, pydantic_model_name)
    return {
        "func": tool_func,
        "model": pydantic_model.model_json_schema(),
        # "model": pydantic_model.__annotations__,
    }


# Return arguments in a (Pydantic) schema and example output
def construct_arguments(schema: Any):
    args: dict[str, dict[str, str]] = schema["properties"]
    example_args = schema["examples"][0]
    required_args = schema["required"]

    # Function to extract the field types and names from the Pydantic model
    def get_model_fields() -> dict:
        fields = {}
        for name, field in args.items():
            is_required = name in required_args
            data = {
                "type": field["type"],
                "required_arg": is_required,
            }
            if "enum" in field:
                data["allowed_values"] = field["enum"]
            fields[name] = data
        return fields

    # Get the fields
    fields = get_model_fields()

    # Return a json for example and args
    return {"arguments": fields, "example_arguments": example_args}


# Agent flow (always return non-streaming response)
class Agent:
    tool_choice = ""
    tool = None
    prompt = ""

    def __init__(
        self, tools: List[classes.ToolDefinition], prompt: str, tool_choice: str = "any"
    ):
        # Force the model to call at least one tool
        tool = None
        # @TODO Support a llm call (semantic search) to determine which tool to use
        # Or perhaps the user can create a "tool chooser" Ai that returns the tool to the
        # answering agent, in which case we need only pass one tool.
        if tool_choice == "any":
            # For now we pick the first tool
            tool = tools[0]
        # Choose the specified tool
        else:
            # name of tool you want model to always call
            tool_index = tools.index(tool_choice)
            tool = tools[tool_index]
        self.tool = tool
        self.tool_choice = tool_choice
        self.prompt = prompt

    # Get the actual function using the provided path
    def get_tool_function(self, path: str):
        is_url = path.startswith("https://")
        tool_code = load_function_file(filename=self.tool["path"])
        tool_func = tool_code["func"]
        # @TODO Construct api call for endpoint
        if is_url:
            return tool_func
        # Load local func
        else:
            return tool_func

    # Pass the text response which includes the function params
    def eval(self, args: dict):
        # pass llm response to function
        path = self.tool["path"]
        tool_function = self.get_tool_function(path)
        return tool_function(args)

    # Return a prompt injected with all tool's descriptions
    def build_tools_prompt(self, template: str):
        QUERY_INPUT = "{query_str}"
        # Get tool module
        tool_code = load_function_file(filename=self.tool["path"])
        # Get Pydantic model
        tool_pydantic_model = tool_code["model"]
        tool_schema = construct_arguments(tool_pydantic_model)
        # Construct new query
        tool_descr_str = self.tool["description"]
        tool_name_str = self.tool["name"]
        query = template.replace(QUERY_INPUT, self.prompt)
        # Build components of prompt
        tool_args_json = json.dumps(tool_schema["arguments"], indent=4)
        tool_args_str = f"```json\n{tool_args_json}\n```"
        tool_example_json = json.dumps(tool_schema["example_arguments"], indent=4)
        tool_example = f"```json\n{tool_example_json}\n```"
        tool_example_schema: dict = tool_schema["example_arguments"]
        args_allowed_keys = list(tool_example_schema.keys())
        return {
            "query": query,
            "arguments": tool_args_str,
            "example_arguments": tool_example,
            "allowed_arguments": args_allowed_keys,
            "tool_name": tool_name_str,
            "tool_description": tool_descr_str,
        }
