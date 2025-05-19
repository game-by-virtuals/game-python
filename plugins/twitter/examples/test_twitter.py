import os
import requests
from dotenv import load_dotenv
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

def run_twitter_actions():
    load_dotenv()
    token = os.getenv("GAME_TWITTER_ACCESS_TOKEN")
    print("Token:", token)
    if not token:
        raise RuntimeError("Please set GAME_TWITTER_ACCESS_TOKEN in your .env")

    # ——— Initialization options ———
    # # Option A: Using your own X API credentials (uncomment to use)
    # options = {
    #     "credentials": {
    #         "api_key": os.environ.get("TWITTER_API_KEY"),
    #         "api_key_secret": os.environ.get("TWITTER_API_KEY_SECRET"),
    #         "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
    #         "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
    #     },
    # }

    # Option B: Using GAME Twitter API Access Token (Recommended, higher rate limits: 35 calls/5 minutes)
    options = {
        "credentials": {
            "game_twitter_access_token": token
        }
    }

    twitter_plugin = TwitterPlugin(options)
    client = twitter_plugin.twitter_client

    try:
        # 1. Who am I?
        me = client.get_me()
        me_data = me["data"]
        user_id = me_data["id"]
        print(f"🙋 Logged in as: @{me_data['username']} ({me_data['name']})")

        # 2. Post a tweet
        tweet = client.create_tweet(text="Hello Web3 🧵 #GameByVirtuals")
        tweet_id = tweet["data"]["id"]
        print(f"✅ Tweet posted: https://x.com/i/web/status/{tweet_id}")

        # 3. Like it
        client.like(tweet_id=tweet_id)
        print("❤️ Tweet liked!")

        # 4. Reply to it
        reply = client.create_tweet(
            text="Replying to my own tweet 😎",
            in_reply_to_tweet_id=tweet_id
        )
        print(f"💬 Replied: https://x.com/i/web/status/{reply['data']['id']}")

        # 5. Quote it
        quote = client.create_tweet(
            text="Excited to be testing the new Game Twitter Plugin!",
            quote_tweet_id=tweet_id
        )
        print(f"🔁 Quoted: https://x.com/i/web/status/{quote['data']['id']}")

        # 5. Upload local media and tweet
        with open("sample_media/virtuals-logo.png", "rb") as img:
            media_id = client.upload_media(media=img, media_type="image/png")
        local = client.create_tweet(
            text="Check this out! Uploaded with local media!",
            media_ids=[media_id]
        )
        print(f"🖼️ Local media tweet: https://x.com/i/web/status/{local['data']['id']}")

        # 7. Upload URL media and tweet
        url = "https://assets.coingecko.com/coins/images/51063/large/Gaming_Agent_1fe70d54ba.jpg"
        resp = requests.get(url)
        resp.raise_for_status()
        media_id_url = client.upload_media(media=resp.content, media_type="image/jpeg")
        url_tweet = client.create_tweet(
            text="Check this out! Uploaded with URL media!",
            media_ids=[media_id_url]
        )
        print(f"🖼️ URL media tweet: https://x.com/i/web/status/{url_tweet['data']['id']}")

        # 8. Search tweets
        search = client.search_recent_tweets(query="#GameByVirtuals", max_results=10)
        hits = search.get("data", [])
        print(f"🔍 Found {len(hits)} tweets for #GameByVirtuals:")
        for i, t in enumerate(hits, 1):
            print(f"  {i}. https://x.com/i/web/status/{t['id']}")

        # 9. Mentions timeline
        mentions = client.get_users_mentions(id=user_id, max_results=20)
        mdata = mentions.get("data", [])
        print(f"🔔 You have {len(mdata)} recent mentions:")
        for i, t in enumerate(mdata, 1):
            print(f"  {i}. https://x.com/i/web/status/{t['id']}")

        # 10. Followers
        followers = client.get_users_followers(id=user_id, max_results=20)
        fdata = followers.get("data", [])
        print(f"👥 You have {len(fdata)} followers:")
        for i, u in enumerate(fdata, 1):
            print(f"  {i}. @{u['username']} ({u['name']})")

        # 11. Following
        following = client.get_users_following(id=user_id, max_results=20)
        gdata = following.get("data", [])
        print(f"➡️ You are following {len(gdata)} users:")
        for i, u in enumerate(gdata, 1):
            print(f"  {i}. @{u['username']} ({u['name']})")

        # 12. Get my public metrics
        metrics = client.get_me(user_fields=["public_metrics"])
        print("📊 My metrics:", metrics["data"]["public_metrics"])

        # 13. Read-only lookup of another user
        other = client.get_user(username="GAME_Virtuals")
        print("🔎 Lookup @GAME_Virtuals:", other["data"])

        # 14. Get metrics for another handle
        game_virtuals = client.get_user(username="GAME_Virtuals", user_fields=["public_metrics"])
        print("📊 @GAME_Virtuals metrics:", game_virtuals["data"]["public_metrics"])

        # 15. Advanced mentions for GAME_Virtuals
        adv_user = client.get_user(username="GAME_Virtuals")
        adv_mentions = client.get_users_mentions(
            id=adv_user["data"]["id"],
            max_results=10,
            tweet_fields=["id", "created_at", "text"],
            expansions=["attachments.media_keys"],
            media_fields=["url"]
        )
        print("🔔 Advanced mentions for @GAME_Virtuals:", adv_mentions)

    except Exception as e:
        print("❌ Error during Twitter actions:", e)

if __name__ == "__main__":
    run_twitter_actions()
