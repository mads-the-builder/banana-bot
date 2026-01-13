# Banana Bot

A Slack bot that edits images using Google's Gemini AI. Mention the bot with an image and a prompt, and it'll return an edited version.

## Features

- **Image editing** — Describe what you want changed and Banana Bot does it
- **Multiple images** — Attach several images to merge or combine them
- **Thread iteration** — Reply in a thread to keep editing the last result
- **DM support** — Message the bot directly (no @mention needed)
- **Resolution options** — Default 2K, or add `4k` to your prompt
- **Aspect ratios** — Use `wide`, `tall`, `square`, or specific ratios like `16:9`

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch**, name it, and select your workspace

#### Enable Socket Mode
1. Go to **Socket Mode** in the sidebar
2. Toggle it **On**
3. Create an app-level token with `connections:write` scope — save this as `SLACK_APP_TOKEN`

#### Set Bot Token Scopes
Go to **OAuth & Permissions** and add these bot token scopes:
- `chat:write`
- `files:read`
- `files:write`
- `im:history`
- `im:read`
- `im:write`

#### Enable Events
Go to **Event Subscriptions**, toggle **On**, and subscribe to these bot events:
- `app_mention`
- `message.im`

#### Install the App
1. Go to **Install App** and click **Install to Workspace**
2. Copy the **Bot User OAuth Token** — save this as `SLACK_BOT_TOKEN`

### 2. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key — save this as `GEMINI_API_KEY`

### 3. Configure Environment

Create a `.env` file:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
GEMINI_API_KEY=your-gemini-key
```

### 4. Install & Run

```bash
pip install -r requirements.txt
python app.py
```

## Usage

| Command | Description |
|---------|-------------|
| `@banana_bot make the sky purple` + image | Basic edit |
| `@banana_bot 4k enhance this photo` + image | 4K output |
| `@banana_bot wide make it a panorama` + image | 16:9 aspect ratio |
| `@banana_bot combine these into one` + multiple images | Merge images |
| Reply in thread with new prompt | Iterate on previous edit |
| DM the bot directly | No @mention needed |

## License

MIT
