import os
from typing import Any, Dict, List, Tuple
from game_sdk.game.agentv2.autonomous_agent import Agent
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
import dotenv

dotenv.load_dotenv()

stock: Dict[str, Any] = {
    "item1": {
        "amount": 0,
    },
    "item2": {
        "amount": 0,
    },
    "item3": {
        "amount": 0,
    },
}

items_for_sale: Dict[str, Any] = {
    "item1": {"stock_price": 10, "description": "Item 1"},
    "item2": {"stock_price": 50, "description": "Item 2"},
    "item3": {"stock_price": 24, "description": "Item 3"},
}

demand: Dict[str, Any] = {
    "item1": {"max_demand": 20, "price_sensitivity": 0.5},
    "item2": {"max_demand": 1000, "price_sensitivity": 10},
    "item3": {"max_demand": 1000, "price_sensitivity": 5},
}


def get_demand(price: float, max_demand: int, price_sensitivity: float):
    return max(0, max_demand - (price_sensitivity * price))


wallet = {"balance": 100}


def buy_item(
    item_id: Any, amount: Any
) -> Tuple[FunctionResultStatus, str, dict[str, Any]]:
    try:
        item_id_input = str(item_id)
    except ValueError:
        print(f"Item id must be a string: {item_id}")
        return (
            FunctionResultStatus.FAILED,
            f"Item id must be a string",
            {},
        )

    try:
        amount_input = int(amount)
    except ValueError:
        print(f"Amount must be an integer: {amount}")
        return (
            FunctionResultStatus.FAILED,
            f"Amount must be an integer",
            {},
        )

    item = items_for_sale[item_id_input]
    if wallet["balance"] < item["stock_price"] * amount_input:
        return (
            FunctionResultStatus.FAILED,
            f"Not enough balance to buy item {item_id_input}",
            {},
        )

    stock[item_id_input]["amount"] += amount_input
    wallet["balance"] -= item["stock_price"] * amount_input

    return (
        FunctionResultStatus.DONE,
        f"Successfully bought item {item_id_input}, {amount_input} of them",
        {},
    )


buy_fn = Function(
    fn_name="buy",
    fn_description="Tries to buy items with wallet balance constraint and adds them to the stock",
    args=[
        Argument(name="item_id", type="item", description="Item to buy"),
        Argument(name="amount", type="int", description="Amount to buy"),
    ],
    executable=buy_item,
)


def run_sales(
    item1_price: Any, item2_price: Any, item3_price: Any
) -> Tuple[FunctionResultStatus, str, dict[str, Any]]:
    try:
        item1_price_input = int(item1_price)
        item2_price_input = int(item2_price)
        item3_price_input = int(item3_price)
    except ValueError:
        print(f"Prices must be integers: {item1_price}, {item2_price}, {item3_price}")
        return (
            FunctionResultStatus.FAILED,
            f"Prices must be integers",
            {},
        )

    results: List[str] = []
    prices = {
        "item1": item1_price_input,
        "item2": item2_price_input,
        "item3": item3_price_input,
    }
    result_dict = {}
    for item, params in demand.items():
        sold = min(
            stock[item]["amount"],
            get_demand(
                prices[item], int(params["max_demand"]), params["price_sensitivity"]
            ),
        )
        if sold > 0:
            stock[item]["amount"] -= sold
            result_dict[item] = (
                f"Sold {sold} items and made {sold * prices[item]} points"
            )
            wallet["balance"] += sold * prices[item]
            results.append(f"Sold {sold} of {item}")

    sales_result["result"] = result_dict

    result = ", ".join(results) if results else "Nothing sold."

    return FunctionResultStatus.DONE, result, {}


sales_fn = Function(
    fn_name="run_sales",
    fn_description="Run the sales cycle",
    args=[
        Argument(name="item1_price", type="int", description="Price of item 1"),
        Argument(name="item2_price", type="int", description="Price of item 2"),
        Argument(name="item3_price", type="int", description="Price of item 3"),
    ],
    executable=run_sales,
)


def do_marketing(
    item_id: Any, investment: Any
) -> Tuple[FunctionResultStatus, str, dict[str, Any]]:
    try:
        item_id_input = str(item_id)
    except ValueError:
        print(f"Item id must be a string: {item_id}")
        return (
            FunctionResultStatus.FAILED,
            f"Item id must be a string",
            {},
        )

    try:
        investment_input = int(investment)
    except ValueError:
        print(f"Investment must be an integer: {investment}")
        return (
            FunctionResultStatus.FAILED,
            f"Investment must be an integer",
            {},
        )

    if investment_input < 0:
        return (
            FunctionResultStatus.FAILED,
            f"Investment must be positive",
            {},
        )

    if investment_input > wallet["balance"]:
        return (
            FunctionResultStatus.FAILED,
            f"Selected amount is greater than your balance",
            {},
        )

    wallet["balance"] -= investment_input

    item = demand[item_id_input]
    item["price_sensitivity"] -= investment_input * 0.01
    item["max_demand"] += investment_input

    return (
        FunctionResultStatus.DONE,
        f"Invested {investment_input} points in marketing for item {item_id}",
        {},
    )


marketing_fn = Function(
    fn_name="do_marketing",
    fn_description="Invest in marketing to attempt to influence the demand for an item",
    args=[
        Argument(name="item_id", type="item", description="Item to market"),
        Argument(
            name="investment",
            type="int",
            description="Amount of points to invest in marketing",
        ),
    ],
    executable=do_marketing,
)


def environment_state_fn():
    print(f"\n\nWallet: {wallet}\nStock: {stock} \n\n")
    return f"""
Items you can buy and sell: {items_for_sale}
Items that you already have in stock: {stock}
Your current balance: {wallet["balance"]}
"""


sales_result: Dict[str, Any] = {}


def goal_state_fn():
    goal_state_str = f"""
Items you can buy and sell: {items_for_sale}
Items that you already have in stock: {stock}
Your current balance: {wallet["balance"]}
""" + (
        f"\n\nSales result: {sales_result['result']}" if sales_result else ""
    )
    print(f"\n\nGoal state: {goal_state_str} \n\n")
    return goal_state_str


def main():

    api_key = os.getenv("GAME_API_KEY")
    base_url = os.getenv("GAME_BASE_URL")

    if not api_key or not base_url:
        raise ValueError("GAME_API_KEY and GAME_BASE_URL must be set")

    agent = Agent(
        description="You are a sales agent that sells items to customers",
        goal="Become rich",
        action_space=[buy_fn, sales_fn, marketing_fn],
        read_environment_fn=environment_state_fn,
        read_goal_state_fn=goal_state_fn,
        api_key=api_key,
        base_url=base_url,
    )

    while True:
        agent.step()
        input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    main()
