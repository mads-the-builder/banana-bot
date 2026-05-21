import os
import io
import re
import random
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

# Random acknowledgments for instant feedback
ACKNOWLEDGMENTS = [
    # Original 50
    "On it...",
    "Working on that...",
    "Let me peel into this...",
    "One sec...",
    "Got it...",
    "Coming right up...",
    "Peeling away...",
    "On the case...",
    "Give me a moment...",
    "Let's see what I can do...",
    "Working my magic...",
    "Hang tight...",
    "Processing...",
    "Let me work on that...",
    "Getting creative...",
    "Bananalyzing the image...",
    "Cooking something up...",
    "Let's do this...",
    "Challenge accepted...",
    "Diving in...",
    "Rolling up my peel...",
    "Firing up the bunch...",
    "Here we go...",
    "Spinning up...",
    "Let me take a crack at it...",
    "Working the magic...",
    "Lemme see here...",
    "Crunching pixels...",
    "Getting to work...",
    "Just a sec...",
    "Hold my peel...",
    "Tweaking things...",
    "Making it happen...",
    "You got it...",
    "Right away...",
    "Say no more...",
    "I'm on it...",
    "Let's make some edits...",
    "Time to shine...",
    "Adjusting...",
    "Transforming...",
    "Watch this...",
    "Enhancing...",
    "Let me fix that up...",
    "Working some banana magic...",
    "Applying changes...",
    "Almost there...",
    "Doing my thing...",
    "Leave it to me...",
    "Peeling back the layers...",
    # Banana puns
    "Splitting into action...",
    "Peeling good about this one...",
    "This is very a-peel-ing...",
    "Bunch of edits coming up...",
    "Ripe for the picking...",
    "Potassium-powered processing...",
    "Unpeeling the possibilities...",
    "Top banana on the job...",
    "Slipping into edit mode...",
    "Going ape on this...",
    "Yellow alert...",
    "Bananafying in progress...",
    "Smoothie operator here...",
    "Plantain my flag on this...",
    "Tropical transformation time...",
    "Getting fruity with it...",
    "Peel the magic...",
    "One ripe edit coming up...",
    "Monkeying with pixels...",
    "Peel-ease hold...",
    "Going full banana...",
    "Second banana? Never...",
    "Banana republic of pixels...",
    "Fruitful edits ahead...",
    "Split decision made...",
    "A-peel-ing to my skills...",
    "There's always money in edits...",
    "Curving into action...",
    "Cluster of changes forming...",
    "Bunch processing...",
    "Stem to stern, working...",
    "Peel position locked...",
    "Ripe timing...",
    "Going absolutely bananas...",
    "Appeeling edit incoming...",
    "Slick as a peel...",
    "Bananagram this...",
    "Tropical heat rising...",
    "Ready to split...",
    "Getting spotted...",
    "From green to golden...",
    "Peeling through your request...",
    "Bunches of fun ahead...",
    "Slipping into gear...",
    "Cavendish mode activated...",
    "Musa magic happening...",
    "Peel and reveal...",
    "Ripening your vision...",
    "Unbunch-lievable...",
    "Plantastic...",
    # Clever/image related
    "Pixels go brrr...",
    "*cracks knuckles*...",
    "Entering the edit zone...",
    "Channeling my inner artist...",
    "Canvas mode activated...",
    "Masterpiece in progress...",
    "Happy little edits coming...",
    "Layers on layers...",
    "Blending in progress...",
    "Sharpening my focus...",
    "Masking my excitement...",
    "Filtering through options...",
    "Rendering assistance...",
    "Magic wand waving...",
    "Transform and roll out...",
    "Warping into action...",
    "Content-aware filling...",
    "AI-yai-yai, here we go...",
    "Neural networks firing...",
    "Pixels assemble...",
    "Ctrl+Banana initiated...",
    "Running banana.exe...",
    "Loading creativity...",
    "Buffering brilliance...",
    "Compiling changes...",
    "Deploying edits...",
    "Queuing up magic...",
    "Initializing awesome...",
    "Booting up beauty...",
    "Executing vision...",
    # Casual/fun
    "Ooh this'll be good...",
    "Now we're cooking...",
    "Let's get tropical...",
    "Spicy edit incoming...",
    "Big things coming...",
    "Trust the process...",
    "In the zone...",
    "Feeling inspired...",
    "The vibes are right...",
    "Stars are aligned...",
    "Chef's kiss loading...",
    "No cap, working on it...",
    "Main character energy...",
    "It's giving... edit time...",
    "Slay incoming...",
    "This is gonna hit...",
    "Watch and learn...",
    "Built different...",
    "Different gravy...",
    "Absolute scenes coming...",
]

# System prompt for conversational mode
CHAT_SYSTEM_PROMPT = """You are banana_bot 🍌, a friendly Slack bot that edits images.

When responding:
- Be brief and friendly (1-2 sentences max)
- If someone is just chatting (saying hi, thanks, good work, etc), respond naturally
- If someone asks you to edit an image, tell them to @mention you and attach the image
- If someone asks you to generate an image from scratch, politely explain you only do edits — they'll need to use another tool for generation
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


def parse_options(prompt: str) -> tuple[str, str, str | None]:
    """Parse resolution and aspect ratio from prompt. Returns (clean_prompt, resolution, aspect_ratio)."""
    resolution = "2K"
    aspect_ratio = None
    
    # Aspect ratio mappings
    ratio_shortcuts = {
        "wide": "16:9",
        "tall": "9:16", 
        "square": "1:1",
    }
    valid_ratios = ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3"]
    
    words = prompt.split()
    clean_words = []
    
    for word in words:
        lower = word.lower()
        if lower == "4k" and resolution == "2K":
            resolution = "4K"
        elif lower in ratio_shortcuts and aspect_ratio is None:
            aspect_ratio = ratio_shortcuts[lower]
        elif lower in valid_ratios and aspect_ratio is None:
            aspect_ratio = lower
        else:
            clean_words.append(word)
    
    return " ".join(clean_words).strip(), resolution, aspect_ratio


def download_slack_image(url: str) -> Image.Image:
    """Download an image from Slack's CDN and return as PIL Image."""
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    )
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def edit_image(images: list[Image.Image], prompt: str, resolution: str = "2K", aspect_ratio: str | None = None) -> tuple[bytes | None, str | None, str | None]:
    """Edit image(s) with a prompt. Returns (image_data, text_response, mime_type)."""
    
    # Build contents: prompt first, then all images
    contents = [prompt] + images
    
    # Build image config
    image_config_params = {"image_size": resolution}
    if aspect_ratio:
        image_config_params["aspect_ratio"] = aspect_ratio
    
    response = gemini.models.generate_content(
        model=MODEL,
        contents=contents,
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
            image_config=types.ImageConfig(**image_config_params),
            tools=[{"google_search": {}}]  # Enable search grounding
        )
    )
    
    text_response = None
    image_data = None
    mime_type = None
    
    for part in response.parts:
        if part.text:
            text_response = part.text
        elif part.inline_data:
            image_data = part.inline_data.data
            mime_type = part.inline_data.mime_type
    
    return image_data, text_response, mime_type


def find_last_image_in_thread(client, channel_id: str, thread_ts: str, bot_user_id: str) -> str | None:
    """Find the most recent image in a thread (bot-posted or user-uploaded)."""
    try:
        result = client.conversations_replies(channel=channel_id, ts=thread_ts)
        messages = result.get("messages", [])
        
        # Go through messages in reverse (most recent first)
        for msg in reversed(messages):
            files = msg.get("files", [])
            for f in files:
                if f.get("mimetype", "").startswith("image/"):
                    return f.get("url_private")
        
        return None
    except Exception as e:
        print(f"Error fetching thread: {e}")
        return None


@app.event("app_mention")
def handle_mention(event, client, say):
    """Handle @mentions - IMAGE EDITING."""
    user_id = event["user"]
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts") or event.get("ts")  # Reply in thread or start new one
    text = event.get("text", "")
    files = event.get("files", [])
    
    # Get bot's own user ID for thread scanning
    bot_user_id = client.auth_test()["user_id"]
    
    # Remove the bot mention from the text to get the prompt
    prompt = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
    
    if not prompt:
        # Empty mention - respond briefly
        try:
            response = chat_response("Someone just mentioned me with no message")
            say(f"🍌 {response}", thread_ts=thread_ts)
        except:
            say("🍌 Hey! What's up?", thread_ts=thread_ts)
        return
    
    # Parse resolution and aspect ratio from prompt
    prompt, resolution, aspect_ratio = parse_options(prompt)
    
    # Build label for output
    labels = []
    if resolution == "4K":
        labels.append("4K")
    if aspect_ratio:
        labels.append(aspect_ratio)
    label_str = f" ({', '.join(labels)})" if labels else ""
    
    # Collect ALL images from attached files
    image_urls = []
    for f in files:
        if f.get("mimetype", "").startswith("image/"):
            image_urls.append(f.get("url_private"))
    
    # If no attached images, check thread for previous image
    if not image_urls and event.get("thread_ts"):
        thread_image = find_last_image_in_thread(client, channel_id, event["thread_ts"], bot_user_id)
        if thread_image:
            image_urls = [thread_image]
    
    if not image_urls:
        # No image found anywhere - respond conversationally
        try:
            response = chat_response(prompt if prompt else "hey")
            say(f"🍌 {response}", thread_ts=thread_ts)
        except Exception as e:
            say(f"🍌 To edit an image, mention me and attach the image you want to change!", thread_ts=thread_ts)
        return
    
    say(f"🍌 {random.choice(ACKNOWLEDGMENTS)}", thread_ts=thread_ts)
    
    try:
        # Download all images
        pil_images = [download_slack_image(url) for url in image_urls]
        
        result_image, result_text, mime_type = edit_image(pil_images, prompt, resolution, aspect_ratio)
        
        if not result_image:
            say(f"Gemini couldn't edit the image. {result_text or 'Try a different prompt.'}", thread_ts=thread_ts)
            return
        
        # Use correct extension based on mime type
        ext = "jpg" if mime_type == "image/jpeg" else "png"
        
        comment = f"🍌 *Edit{label_str}* by <@{user_id}>: _{prompt}_"
        if result_text:
            comment += f"\n\n{result_text}"
        
        client.files_upload_v2(
            channel=channel_id,
            thread_ts=thread_ts,
            content=result_image,
            filename=f"banana-bot-edit.{ext}",
            initial_comment=comment
        )
        
    except Exception as e:
        say(f"Error editing image: {e}", thread_ts=thread_ts)


@app.event("message")
def handle_dm(event, client, say):
    """Handle direct messages — no @mention needed."""
    # Ignore bot messages to prevent loops
    if event.get("bot_id"):
        return
    
    # Ignore message subtypes except file_share (which is how images come through)
    subtype = event.get("subtype")
    if subtype and subtype != "file_share":
        return
    
    # Only handle DMs (channel type "im")
    channel_type = event.get("channel_type")
    if channel_type != "im":
        return
    
    user_id = event["user"]
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts") or event.get("ts")
    text = event.get("text", "").strip()
    files = event.get("files", [])
    
    if not text:
        say("🍌 Hey! Send me an image with a prompt and I'll edit it for you.", thread_ts=thread_ts)
        return
    
    # Parse resolution and aspect ratio from prompt
    prompt, resolution, aspect_ratio = parse_options(text)
    
    # Build label for output
    labels = []
    if resolution == "4K":
        labels.append("4K")
    if aspect_ratio:
        labels.append(aspect_ratio)
    label_str = f" ({', '.join(labels)})" if labels else ""
    
    # Collect ALL images from attached files
    image_urls = []
    for f in files:
        if f.get("mimetype", "").startswith("image/"):
            image_urls.append(f.get("url_private"))
    
    # If no attached images, check thread for previous image
    if not image_urls and event.get("thread_ts"):
        bot_user_id = client.auth_test()["user_id"]
        thread_image = find_last_image_in_thread(client, channel_id, event["thread_ts"], bot_user_id)
        if thread_image:
            image_urls = [thread_image]
    
    if not image_urls:
        # No image found — respond conversationally
        try:
            response = chat_response(prompt if prompt else "hey")
            say(f"🍌 {response}", thread_ts=thread_ts)
        except Exception as e:
            say(f"🍌 To edit an image, send it along with your prompt!", thread_ts=thread_ts)
        return
    
    say(f"🍌 {random.choice(ACKNOWLEDGMENTS)}", thread_ts=thread_ts)
    
    try:
        # Download all images
        pil_images = [download_slack_image(url) for url in image_urls]
        
        result_image, result_text, mime_type = edit_image(pil_images, prompt, resolution, aspect_ratio)
        
        if not result_image:
            say(f"Gemini couldn't edit the image. {result_text or 'Try a different prompt.'}", thread_ts=thread_ts)
            return
        
        # Use correct extension based on mime type
        ext = "jpg" if mime_type == "image/jpeg" else "png"
        
        comment = f"🍌 *Edit{label_str}*: _{prompt}_"
        if result_text:
            comment += f"\n\n{result_text}"
        
        client.files_upload_v2(
            channel=channel_id,
            thread_ts=thread_ts,
            content=result_image,
            filename=f"banana-bot-edit.{ext}",
            initial_comment=comment
        )
        
    except Exception as e:
        say(f"Error editing image: {e}", thread_ts=thread_ts)


if __name__ == "__main__":
    print("⚡ Banana Bot is running!")
    print("   • @banana_bot [prompt] + image — edit at 2K")
    print("   • @banana_bot 4k [prompt] — edit at 4K")
    print("   • @banana_bot 16:9 [prompt] — set aspect ratio")
    print("   • Attach multiple images to merge/combine")
    print("   • Reply in thread to iterate on previous edits")
    print("   • DMs supported — no @mention needed")
    print("   • Search grounding enabled for real-time data")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
