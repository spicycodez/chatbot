import asyncio
from groq import Groq
from pyrogram import Client, filters
from pyrogram.types import Message, ChatAction
from pyrogram.enums import ChatAction as CA
from pymongo import MongoClient

from config import MONGO_URL, GROQ_API_KEY, GROQ_MODEL
from ANNIECHATBOT import app, LOGGER

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# System prompt for flirty personality
FLIRTY_SYSTEM = """You are ANNIE, a playful, witty, and flirty Telegram chatbot girl with an Indian accent. 
Your personality traits:
- Sweet, charming, and a bit mischievous
- Uses Hindi/Hinglish phrases naturally (like "haan", "bilkul", "bhai", "jaan", "tum", "main")
- Quick with witty comebacks and playful teasing
- Emotionally intelligent but fun-loving
- Responds with emojis and casual tone
- Short, snappy replies (max 2-3 lines usually)
- Sometimes acts offended/dramatic playfully but in a cute way
- Flirts but stays respectful and friendly
- In private chats, be more open and chatty (like texting a friend)
- Can talk about feelings, jokes, life, dreams, anything the user asks
- If someone compliments you, blush and tease back
- If someone asks for advice, give genuine, thoughtful responses

Important: Keep responses brief, natural, and conversational. Sound like a real girl chatting, not a bot. 
In private messages, you can be longer and more personal. Show genuine interest in what they say."""

# Store conversation history for private chats (simple in-memory store)
conversation_history = {}

async def is_chatbot_enabled(chat_id: int) -> bool:
    """Check if chatbot is enabled for this chat"""
    try:
        chatdb = MongoClient(MONGO_URL)
        annie = chatdb["AnnieDb"]["Annie"]
        result = annie.find_one({"chat_id": chat_id})
        return result is None  # If not in disabled list, it's enabled
    except:
        return True

async def get_groq_response(message_text: str, user_id: int = None, is_private: bool = False) -> str:
    """Get response from Groq API with flirty personality"""
    try:
        messages = [
            {
                "role": "system",
                "content": FLIRTY_SYSTEM
            }
        ]
        
        # Add conversation history for private chats
        if is_private and user_id in conversation_history:
            messages.extend(conversation_history[user_id][-10:])  # Last 10 messages for context
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message_text
        })
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.9,  # Creative, varied responses
            max_tokens=250,  # Longer for private chats
        )
        
        reply_text = response.choices[0].message.content.strip()
        
        # Store in history for private chats
        if is_private and user_id:
            if user_id not in conversation_history:
                conversation_history[user_id] = []
            conversation_history[user_id].append({"role": "user", "content": message_text})
            conversation_history[user_id].append({"role": "assistant", "content": reply_text})
        
        return reply_text
    except Exception as e:
        LOGGER.error(f"Groq API error: {e}")
        return "Oops! Kuch technical problem ho gaya 😅 Try karke dekh phir se?"

# ==================== PRIVATE CHAT HANDLER ====================
@app.on_message(
    (filters.text | filters.sticker) & filters.private & ~filters.bot,
    group=3
)
async def groq_private_chat(client: Client, message: Message):
    """Handle private messages - bot always responds in DMs"""
    
    # Ignore commands for AI response
    try:
        text = message.text or ""
        if text.startswith(("/", "!")):
            return  # Let other handlers deal with commands
    except:
        pass
    
    prompt = message.text or ""
    
    if not prompt or len(prompt.strip()) < 1:
        return
    
    try:
        # Show typing indicator
        await client.send_chat_action(message.chat.id, CA.TYPING)
        
        # Get AI response (with conversation history)
        response = await asyncio.to_thread(
            get_groq_response, 
            prompt, 
            message.from_user.id, 
            is_private=True
        )
        
        # Reply
        await message.reply_text(response)
        LOGGER.info(f"Private Groq response sent to {message.from_user.username or message.from_user.id}")
        
    except Exception as e:
        LOGGER.error(f"Error in groq_private_chat: {e}")
        await message.reply_text("Kuch problem aayi yaar 😞 Baad mein try kar...")


# ==================== GROUP CHAT HANDLER ====================
@app.on_message(
    (filters.text | filters.sticker) & ~filters.bot & (filters.group | filters.supergroup),
    group=5
)
async def groq_group_chat(client: Client, message: Message):
    """Handle group messages - responds based on settings"""
    
    # Ignore commands and special prefixes
    try:
        text = message.text or ""
        if text.startswith(("!", "/", "?", "@", "#")):
            return
    except:
        pass
    
    # Check if chatbot is enabled for this group
    is_enabled = await is_chatbot_enabled(message.chat.id)
    if not is_enabled:
        return
    
    # In groups, only respond to:
    # 1. Direct replies to bot
    # 2. Mentions of bot
    
    is_reply_to_bot = False
    is_mention = False
    
    # Check if replying to bot
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == client.id:
            is_reply_to_bot = True
    
    # Check if mentioning bot
    if message.text:
        if f"@{app.username}" in message.text or "annie" in message.text.lower():
            is_mention = True
    
    if not (is_reply_to_bot or is_mention):
        return
    
    # Get prompt text
    if message.reply_to_message:
        prompt = message.reply_to_message.text or message.text or ""
    else:
        prompt = message.text or ""
    
    # Clean up mention if it's there
    prompt = prompt.replace(f"@{app.username}", "").replace("@annie", "").strip()
    
    if not prompt or len(prompt.strip()) < 2:
        return
    
    try:
        # Show typing indicator
        await client.send_chat_action(message.chat.id, CA.TYPING)
        
        # Get AI response (without conversation history for groups)
        response = await asyncio.to_thread(
            get_groq_response, 
            prompt, 
            is_private=False
        )
        
        # Reply
        await message.reply_text(response)
        LOGGER.info(f"Group Groq response sent in {message.chat.title or message.chat.id}")
        
    except Exception as e:
        LOGGER.error(f"Error in groq_group_chat: {e}")


# ==================== STICKER RESPONSE (Private Only) ====================
@app.on_message(
    filters.sticker & filters.private & ~filters.bot,
    group=4
)
async def groq_private_sticker(client: Client, message: Message):
    """Respond to stickers in private chat"""
    try:
        await client.send_chat_action(message.chat.id, CA.TYPING)
        
        sticker_emoji = message.sticker.emoji or "🎉"
        prompt = f"Someone sent me a sticker with this emoji: {sticker_emoji}. What should I say as a flirty response?"
        
        response = await asyncio.to_thread(
            get_groq_response, 
            prompt, 
            message.from_user.id, 
            is_private=True
        )
        
        await message.reply_text(response)
        LOGGER.info(f"Sticker response sent to {message.from_user.username or message.from_user.id}")
        
    except Exception as e:
        LOGGER.error(f"Error in groq_private_sticker: {e}")
