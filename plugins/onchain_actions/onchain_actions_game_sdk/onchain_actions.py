from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from goat import ToolBase, WalletClientBase, get_tools
from typing import List, Any


def create_game_function(tool: ToolBase):
    args = []
    for field_name, field in tool.parameters.__fields__.items():
        args.append(Argument(
            name=field_name,
            required=field.is_required(),
            description=field.description or "",
        ))

    return Function(
        fn_name=tool.name,
        fn_description=tool.description,
        args=args,
        executable=lambda **args: _execute_tool(tool, **args),
    )

def _execute_tool(tool: ToolBase, **args):
    try:        
        result = tool.execute(args)
        return (
            FunctionResultStatus.DONE,
            f"{tool.name} executed successfully",
            { "result": result },
        )
    except Exception as e:
        print(e)
        return (
            FunctionResultStatus.FAILED,
            f"Error executing tool: {e}",
            args,
        )

def get_onchain_actions(wallet: WalletClientBase, plugins: List[Any]):
    tools = get_tools(wallet=wallet, plugins=plugins)   
    functions = [create_game_function(tool) for tool in tools]
    return functions
