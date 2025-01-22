import os
from game_sdk.hosted_game.agent import Agent, Function, FunctionArgument, FunctionConfig

agent = Agent(
    api_key=os.environ.get("VIRTUALS_API_KEY"),
    goal="search for best songs",
    description="Test Description",
    world_info="Test World Info"
)

# running reaction module for other platforms
# adding custom functions for platform specifics
agent.add_custom_function(
    Function(
        fn_name="custom_search_internet",
        fn_description="search the internet for the best songs",
        args=[
            FunctionArgument(
                name="query",
                type="string",
                description="The query to search for"
            )
        ],
        config=FunctionConfig(
            method="get",
            url="https://google.com",
            platform="telegram",  # this function will only be used for telegram
            success_feedback="I found the best songs",
            error_feedback="I couldn't find the best songs",
        )
    )
)

# add function to call bitmindlabs.ai/detect-image
agent.add_custom_function(
    Function(
        fn_name="detect_image",
        fn_description="detect the image",
        args=[
            FunctionArgument(
                name="image",
                type="string",
                description="The image url to detect"
            )
        ],
        config=FunctionConfig(
            method="post",
            headers={
                "Authorization": f"Bearer {os.environ.get('BITMINDLABS_API_KEY')}",
                "Content-Type": "application/json"
            },
            payload={
                "image": "{{URL}}"
            },
            url="https://bitmindlabs.ai/detect-image",
            platform="twitter",
            success_feedback="I detected the image",
            error_feedback="I couldn't detect the image",
        )
    )
)


# running reaction module only for platform telegram
agent.react(
    session_id="session-telegram",
    # specify the platform telegram
    platform="telegram",
    # specify the event that triggers the reaction
    event="message from user: give me some great music?",
    # specify the task that the agent should do
    task="reply with a music recommendation",
)
