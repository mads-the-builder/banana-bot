import os
import io
import re
import requests
from dotenv import load_dotenv
from PIL import Image
from google import genai

load_dotenv()
from google.genai import types
from google.genai.types import GenerateContentConfig, Modality
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Configuration - set these as environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")  # xoxb-...
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")  # xapp-...
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize Gemini client
gemini = genai.Client(api_key=GEMINI_API_KEY)

MODEL = "gemini-3-pro-image-preview"

# System prompt for conversational mode
CHAT_SYSTEM_PROMPT = """You are banana_bot 🍌, a friendly Slack bot that can generate and edit images.

When responding:
- Be brief and friendly (1-2 sentences max)
- If someone is just chatting (saying hi, thanks, good work, etc), respond naturally
- If someone asks you to generate/create an image from scratch, tell them to use /banana [prompt]
- If someone asks you to edit an image, tell them to @mention you and attach the image
- Don't use emojis excessively, just be chill
- You can be a little playful/silly since you're a banana"""


def chat_response(message: str) -> str:
    """Get a text-only chat response from the model."""
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",  # faster model for chat
        contents=[message],
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT],
            system_instruction=CHAT_SYSTEM_PROMPT
        )
    )
    
    for part in response.parts:
        if part.text:
            return part.text
    
    return "🍌"


def parse_resolution(prompt: str) -> tuple[str, str]:
    """Check if prompt starts with '4k' and return (clean_prompt, resolution)."""
    if prompt.lower().startswith("4k "):
        return prompt[3:].strip(), "4K"
    return prompt, "2K"


def download_slack_image(url: str) -> Image.Image:
    """Download an image from Slack's CDN and return as PIL Image."""
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    )
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def generate_image(prompt: str, resolution: str = "2K") -> tuple[bytes | None, str | None]:
    """Generate an image from text prompt only."""
    response = gemini.models.generate_content(
        model=MODEL,
        contents=[prompt],
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
            image_config=types.ImageConfig(image_size=resolution)
        )
    )
    
    text_response = None
    image_data = None
    
    for part in response.parts:
        if part.text:
            text_response = part.text
        elif part.inline_data:
            image_data = part.inline_data.data
    
    return image_data, text_response


def edit_image(image: Image.Image, prompt: str, resolution: str = "2K") -> tuple[bytes | None, str | None]:
    """Edit an existing image with a prompt."""
    response = gemini.models.generate_content(
        model=MODEL,
        contents=[prompt, image],
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
            image_config=types.ImageConfig(image_size=resolution)
        )
    )
    
    text_response = None
    image_data = None
    
    for part in response.parts:
        if part.text:
            text_response = part.text
        elif part.inline_data:
            image_data = part.inline_data.data
    
    return image_data, text_response


@app.command("/banana")
def handle_banana_command(ack, command, client, respond):
    """Handle the /banana slash command - TEXT TO IMAGE GENERATION ONLY."""
    ack()
    
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    prompt = command["text"].strip()
    
    if not prompt:
        respond(
            "🍌 *Banana Bot*\n\n"
            "*Generate an image:*\n"
            "`/banana a cat astronaut floating in space`\n\n"
            "*Generate in 4K:*\n"
            "`/banana 4k a cat astronaut floating in space`\n\n"
            "*Edit an image:*\n"
            "Upload an image and mention me:\n"
            "`@banana_bot make it look like a watercolor`"
        )
        return
    
    # Parse resolution from prompt
    prompt, resolution = parse_resolution(prompt)
    res_label = " (4K)" if resolution == "4K" else ""
    
    respond(f"🍌 Generating{res_label}: *{prompt}*...")
    
    try:
        result_image, result_text = generate_image(prompt, resolution)
        
        if not result_image:
            respond(f"Gemini couldn't generate an image. {result_text or 'Try a different prompt.'}")
            return
        
        comment = f"🍌 *Generated{res_label}* by <@{user_id}>: _{prompt}_"
        if result_text:
            comment += f"\n\n{result_text}"
        
        client.files_upload_v2(
            channel=channel_id,
            content=result_image,
            filename="banana-bot-generated.png",
            initial_comment=comment
        )
        
    except Exception as e:
        respond(f"Error generating image: {e}")


@app.event("app_mention")
def handle_mention(event, client, say):
    """Handle @mentions - IMAGE EDITING."""
    user_id = event["user"]
    channel_id = event["channel"]
    text = event.get("text", "")
    files = event.get("files", [])
    
    # Remove the bot mention from the text to get the prompt
    prompt = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
    
    if not prompt:
        # Empty mention - respond briefly
        try:
            response = chat_response("Someone just mentioned me with no message")
            say(f"🍌 {response}")
        except:
            say("🍌 Hey! What's up?")
        return
    
    # Parse resolution from prompt
    prompt, resolution = parse_resolution(prompt)
    res_label = " (4K)" if resolution == "4K" else ""
    
    # Find an image in the attached files
    image_url = None
    for f in files:
        if f.get("mimetype", "").startswith("image/"):
            image_url = f.get("url_private")
            break
    
    if not image_url:
        # No image - let the model respond conversationally
        # It will redirect to /banana if they're asking for generation
        try:
            response = chat_response(prompt if prompt else "hey")
            say(f"🍌 {response}")
        except Exception as e:
            say(f"🍌 Hey! Need something? Use `/banana` to generate images, or mention me with an attached image to edit it.")
        return
    
    say(f"🍌 Editing image{res_label}: *{prompt}*...")
    
    try:
        pil_image = download_slack_image(image_url)
        result_image, result_text = edit_image(pil_image, prompt, resolution)
        
        if not result_image:
            say(f"Gemini couldn't edit the image. {result_text or 'Try a different prompt.'}")
            return
        
        comment = f"🍌 *Edit{res_label}* by <@{user_id}>: _{prompt}_"
        if result_text:
            comment += f"\n\n{result_text}"
        
        client.files_upload_v2(
            channel=channel_id,
            content=result_image,
            filename="banana-bot-edit.png",
            initial_comment=comment
        )
        
    except Exception as e:
        say(f"Error editing image: {e}")


if __name__ == "__main__":
    print("⚡ Banana Bot is running!")
    print("   • /banana [prompt] — generate at 2K")
    print("   • /banana 4k [prompt] — generate at 4K")
    print("   • @bot [prompt] + image — edit at 2K")
    print("   • @bot 4k [prompt] + image — edit at 4K")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
