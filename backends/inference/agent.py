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
    example_args = schema["examples"][0]  # We only take 1st example
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
    return {"arguments": fields, "required_arguments": required_args,"example_arguments": example_args}

def dict_list_to_markdown(dict_list: List[dict]):
    markdown_string = ""
    for index, item in enumerate(dict_list):
        markdown_string += f"# Tool {index + 1}: {item.get("name")}\n\n"
        for key, value in item.items():
            # If code
            if key == "arguments" or key == "example_arguments":
                markdown_string += f"## {key}\n```json\n{value}\n```\n\n"
            else:
                markdown_string += f"## {key}\n{value}\n\n"
    return markdown_string

# Filter out all "required_arg" props
def get_allowed_args(tool_args: dict):
    result = []
    for name, value in tool_args.items():
        if value.get("required_arg") == True:
            result.append(name)
    return result

def get_tool_props(tool_def: classes.ToolDefinition):
    tool_descr_str = tool_def["description"]
    tool_name_str = tool_def["name"]
    # Build components of prompt
    tool_args_json = json.dumps(tool_def["arguments"], indent=4)
    tool_args_str = f"```json\n{tool_args_json}\n```"
    tool_example_json = json.dumps(tool_def["example_arguments"], indent=4)
    tool_example = f"```json\n{tool_example_json}\n```"
    tool_allowed_keys = get_allowed_args(tool_def["arguments"])
    return {
        "name": tool_name_str,
        "description": tool_descr_str,
        "arguments": tool_args_str,
        "example_arguments": tool_example,
        "allowed_arguments": tool_allowed_keys,
    }

# Get the actual function using the provided path
def get_tool_function(path: str, tool: classes.ToolDefinition):
    is_url = path.startswith("https://")
    tool_code = load_function_file(filename=tool["path"])
    tool_func = tool_code["func"]
    # @TODO Construct api call for endpoint
    if is_url:
        return tool_func
    # Load local func
    else:
        return tool_func

# Pass the text response which includes the function params
def eval(tool: classes.ToolDefinition, args: dict):
    # pass llm response to function
    path = tool["path"]
    tool_function = get_tool_function(tool=tool, path=path)
    return tool_function(args)
