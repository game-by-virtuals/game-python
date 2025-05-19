# Twitter Plugin for GAME SDK

The **Twitter Plugin** provides a lightweight interface for integrating Twitter (X) functionality into your GAME SDK agents. Built on top of [`virtuals_tweepy`](https://pypi.org/project/virtuals-tweepy/) by the Virtuals team — a maintained fork of [`Tweepy`](https://pypi.org/project/tweepy/)) — this plugin lets you easily post tweets, fetch data, and execute workflows through agent logic.

Use it standalone or compose multiple Twitter actions as part of a larger agent job.

---

## Installation

You can install the plugin using either `poetry` or `pip`:

```bash
# Using Poetry (from the plugin directory)
poetry install
```
or
```bash
# Using pip (recommended for integration projects)
pip install twitter_plugin_gamesdk
```

---

## Authentication Methods

We support two primary ways to authenticate:

### 1. GAME's Sponsored X Enterprise Access Token (Recommended)

Virtuals sponsors the community with a **Twitter Enterprise API access plan**, using OAuth 2.0 with PKCE. This provides:

- Higher rate limits: **35 calls / 5 minutes**
- Smoother onboarding
- Free usage via your `GAME_API_KEY`

#### a. Get Your Access Token

Run the following command to authenticate using your `GAME_API_KEY`:

```bash
poetry run twitter-plugin-gamesdk auth -k <GAME_API_KEY>
```

This will prompt:

```bash
Waiting for authentication...

Visit the following URL to authenticate:
https://x.com/i/oauth2/authorize?...

Authenticated! Here's your access token:
apx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### b. Store Your Access Token

We recommend storing environment variables in a `.env` file:

```
# .env

GAME_TWITTER_ACCESS_TOKEN=apx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then, use `load_dotenv()` to load them:

```python
import os
from dotenv import load_dotenv
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

load_dotenv()

options = {
    "credentials": {
        "game_twitter_access_token": os.environ.get("GAME_TWITTER_ACCESS_TOKEN")
    }
}

twitter_plugin = TwitterPlugin(options)
client = twitter_plugin.twitter_client

client.create_tweet(text="Tweeting with GAME Access Token!")
```

---

### 2. Use Your Own Twitter Developer Credentials

Use this option if you need access to Twitter endpoints requiring a different auth level (e.g., **OAuth 1.0a User Context** or **OAuth 2.0 App Only**).

> See [X API Auth Mapping](https://docs.x.com/resources/fundamentals/authentication/guides/v2-authentication-mapping) to determine which auth level is required for specific endpoints.

#### a. Get Your Developer Credentials

1. Sign in to the [Twitter Developer Portal](https://developer.x.com/en/portal/dashboard).
2. Create a project and app.
3. Generate the following keys and store them in your `.env` file:

```
# .env

TWITTER_API_KEY=...
TWITTER_API_SECRET_KEY=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

#### b. Initialize the Plugin

```python
import os
from dotenv import load_dotenv
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

load_dotenv()

options = {
    "credentials": {
        "api_key": os.environ.get("TWITTER_API_KEY"),
        "api_key_secret": os.environ.get("TWITTER_API_SECRET_KEY"),
        "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
    }
}

twitter_plugin = TwitterPlugin(options)
client = twitter_plugin.twitter_client

client.create_tweet(text="Tweeting with personal developer credentials!")
```

---

## Examples

Explore the [`examples/`](./examples) directory for sample scripts demonstrating how to:

- Post tweets
- Reply to mentions
- Quote tweets
- Fetch user timelines
- And more!

---

## API Reference

This plugin wraps [`virtuals_tweepy`](https://pypi.org/project/virtuals-tweepy/), which is API-compatible with [Tweepy’s client interface](https://docs.tweepy.org/en/stable/client.html). Refer to their docs for supported methods and parameters.

---
