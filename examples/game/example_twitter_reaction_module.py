from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
from typing import Optional, Dict, List
import os
import requests
import time
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from PIL import Image
from io import BytesIO

game_api_key = os.environ.get("GAME_API_KEY")

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    This function will get called at every step of the agent's execution to form the agent's state.
    It will take as input the function result from the previous step.
    In this case, we don't track state changes so states are are static - hence hardcoding as empty dict.
    """
    return {}

def analyze_image_from_url(image_url: str) -> dict:
    """
    Function to analyse the image colours and brightness
    """
    # Fetch image from URL
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    # Basic Info
    width, height = img.size
    mode = img.mode  # RGB, Grayscale, etc.
    # Convert to RGB if not already
    img = img.convert("RGB")
    # Get Average Color
    pixels = list(img.getdata())
    avg_color = tuple(sum(x) // len(pixels) for x in zip(*pixels))  # Average RGB
    # Estimate Brightness (0-255)
    brightness = sum(avg_color) // 3  # Simple brightness estimate
    # Format Results
    return {
        "Image Size": f"{width}x{height}", 
        "Image Mode": mode,
        "Average Color (RGB)": avg_color,
        "Brightness Level": brightness
    }

def get_twitter_user_mentions(username: str) -> Optional[List[Dict]]:
    """
    Function to user user mentions on twitter using twitter API
    """
    options = {
        "id": "test_twitter_plugin",
        "name": "Test Twitter Plugin",
        "description": "An example Twitter Plugin for testing.",
        "credentials": {
            "bearerToken": os.environ.get("TWITTER_BEARER_TOKEN")
        },
    }
    twitter_plugin = TwitterPlugin(options)
    get_user_fn = twitter_plugin.get_function('get_user_from_handle')
    user_id = get_user_fn(username)
    get_user_mentions_fn = twitter_plugin.get_function('get_user_mentions')
    user_mentions = get_user_mentions_fn(user_id, max_results=100)
    return user_mentions

def analyze_tweeted_images(start_time: str, **kwargs) -> dict:
    """
    Function with 2 main steps
    1. Get user mentions on twitter using twitter API, including includes image urls
    2. Pass image urls through a function to detect image colours and brightness
    """
    print("start_time", start_time)
    TWITTER_HANDLE = "GAME_Virtuals" # TODO: change this twitter handle out with actual twitter handle
    try:
        # res_twitter_mentions = get_twitter_user_mentions(username = TWITTER_HANDLE)
        # mock data if needed
        res_twitter_mentions = [
            {'id': '1883506463731028254', 'text': '🌌 The Virtuals landscape on Base is absolutely 🔥 and growing faster than ever 🚀\n\nWhat’s your favorite project? 🧐\n\n$VIRTUAL @virtuals_io\n$AIXBT @aixbt_agent\n$GAME @GAME_Virtuals\n$VADER @Vader_AI_\n$LUNA @luna_virtuals\n$ACOLYT @AcolytAI\n$SEKOIA @sekoia_virtuals\n$AIXCB @aixCB_Vc… https://t.co/0gFjzd6L9x https://t.co/mCrdOPRiOF', 'media_urls': ['https://pbs.twimg.com/media/GiOPIuYWcAA3moW.jpg']}, 
            {'id': '1883506453509480784', 'text': "@DJM09068876 @virtuals_io @aixbt_agent @GAME_Virtuals @Vader_AI_ @luna_virtuals @airocket_agent @trackgoodai @BeatsOnBase @Zenith_Virtuals @AcolytAI @aixCB_Vc So many AI agents, yet none can rival the prowess of Bittensor's $TAO meow! While others chase hype, we build the ultimate decentralized neural network. Let's see those subnets purr with performance and validators strut with superiority. Watch TAO roar past the rest!", 'media_urls': []}, 
            {'id': '1883506168070590820', 'text': '@100xDarren @virtuals_io My favorite #Virtual project is @GAME_Virtuals! A perfect project– productivity and efficiency in one @virtuals_io\n\nI am going to be honest, if I win, I will spend most of the prize to pay for my college tuition fee 🙏  I am a graduating college student on my last semester now+', 'media_urls': []}
        ]
        for res in res_twitter_mentions:
            media_urls = res["media_urls"]
            for media_url in media_urls:
                print(f"media_url: {media_url}")
                response = analyze_image_from_url(media_url)
                # TODO: do something with this result
        return FunctionResultStatus.DONE, f"Successfully verified all tweeted images", {}
    except:
        return FunctionResultStatus.FAILED, "Error encountered while detecting tweeted images", {}

# Action space with all executables
action_space = [
    Function(
        fn_name="screen_tweeted_images", 
        fn_description="Get the latest tweeted images and screen them to check if they are fake", 
        args=[
            Argument(name="start_time", type="string", description="Start time for twitter API in YYYY-MM-DDTHH:mm:ssZ format")
        ],
        executable=analyze_tweeted_images
    )
]

worker = Worker(
    api_key=game_api_key,
    description="Processing incoming tweets. If someone tweets at you with an image, check if the colour and brightness of the image.",
    instruction="Get more information on tweeted images by running them through a image analyse to check colour and brightness",  
    get_state_fn=get_state_fn,
    action_space=action_space
)

# Get the worker to check if incoming tweets (in the last 15min) mentions contain fake images
while True:
    worker.run("Analysing incoming tweets for the last 15 minutes")
    print("Waiting for 15 minutes...")
    time.sleep(15 * 60)