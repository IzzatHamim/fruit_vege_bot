import os
import random
import tempfile
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from collections import defaultdict

DATA_DIR = "Fruits_Vegetables/test"
data_cat = sorted(os.listdir(DATA_DIR))
user_state = defaultdict(lambda: {
    "score": 0, "total": 0, "in_guess_mode": False
})

def get_random_image_and_label():
    label = random.choice(data_cat)
    folder = os.path.join(DATA_DIR, label)
    filename = random.choice(os.listdir(folder))
    path = os.path.join(folder, filename)
    return path, label

def resize_image_for_telegram(img_path, size=(512, 512)):
    img = Image.open(img_path).resize(size)
    
    if img.mode == "RGBA":
        img = img.convert("RGB")  # ✅ Remove alpha channel

    temp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(temp.name, format="JPEG")
    return temp.name


def register_guess_handlers(app: Client):
    print(">>> register_guess_handlers function is running")  # New debug

    @app.on_message(filters.command("guess"))
    def handle_guess_command(client, message: Message):
        print(">>> /guess command triggered")  # You said this doesn’t print

        user_id = message.from_user.id
        img_path, label = get_random_image_and_label()
        resized = resize_image_for_telegram(img_path)

        # Save current label
        user_state[user_id]["current_label"] = label
        user_state[user_id]["current_img"] = img_path
        user_state[user_id]["in_guess_mode"] = True  # 👈 set mode


        client.send_photo(
            chat_id=message.chat.id,
            photo=resized,
            caption=(
                "🍓 *Guess this fruit or vegetable!*\n"
                "Reply to this image with your guess.\n\n"
                "💡 Need help? Type /hint for a clue!"
            )
        )


    @app.on_message(filters.text & filters.private & ~filters.command(["hint", "start", "predict", "chatbox", "exit"]))
    def handle_guess_reply(client, message: Message):

        user_id = message.from_user.id
        guess = message.text.strip().lower()

        # ✅ Only respond if in guess mode
        if not user_state[user_id].get("in_guess_mode") or "current_label" not in user_state[user_id]:
            return  # Ignore if not in guess session

        true_label = user_state[user_id]["current_label"].lower()
        user_state[user_id]["total"] += 1

        if guess == true_label:
            user_state[user_id]["score"] += 1
            result = f"✅ Correct! It was *{true_label.title()}*."
        else:
            result = f"❌ Wrong! You guessed *{guess}*, but it was *{true_label.title()}*."

        score_text = f"🎯 Score: {user_state[user_id]['score']} / {user_state[user_id]['total']}"
        message.reply_text(f"{result}\n\n{score_text}\n\nType /guess to play again or /exit to reset the score.")
    
        # Clean up
        user_state[user_id]["in_guess_mode"] = False
        del user_state[user_id]["current_label"]



    @app.on_message(filters.command("hint"))
    def handle_hint_command(client, message: Message):
        user_id = message.from_user.id
        if "current_label" not in user_state[user_id]:
            message.reply_text("❗ No active game. Use /guess first.")
            return

        label = user_state[user_id]["current_label"]
        hint = f"🧠 Hint: It starts with *'{label[0].upper()}'* and has *{len(label)}* letters."
        message.reply_text(hint)
      
    @app.on_message(filters.command("exit"))
    def handle_exit_command(client, message: Message):
        user_id = message.from_user.id
        user_state[user_id] = {
            "score": 0,
            "total": 0,
            "in_guess_mode": False
        }
        message.reply_text(
            "**👋 You've exited the Guess Game.**\n\n"
            "Score has been reset.\n\n"
            "I can help you identify fruits and vegetables and give useful information like:\n"
            "- 🥗 Nutrition facts\n"
            "- 🔥 Calorie values\n"
            "- 🧪 Antioxidant ratings\n"
            "- 📝 Dietary notes\n"
            "- 👨‍🍳 Recipe suggestions\n\n"
            "**Available Commands:**\n"
            "/predict - Send a fruit/veggie image for prediction\n"
            "/guess - Start the guessing game again"
        )

