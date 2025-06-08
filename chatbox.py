
from pyrogram import Client, filters
from pyrogram.types import Message
import tensorflow as tf
import numpy as np
from PIL import Image
from session import active_chatbox_sessions




def init_chatbox_handlers(
    app: Client,
    model,
    data_cat,
    img_width,
    img_height,
    nutrition_info,
    antioxidant_score,
    diet_notes,
    recipe_suggestions,
    calorie_info
):
    def prepare_image(image_path):
        image = Image.open(image_path).convert("RGB")
        image = image.resize((img_width, img_height))
        image_array = tf.keras.utils.img_to_array(image)
        return tf.expand_dims(image_array, 0)

    def get_prediction(image_path):
        img_bat = prepare_image(image_path)
        predict = model.predict(img_bat)
        score = tf.nn.softmax(predict[0])
        top_indices = np.argsort(score)[::-1][:5]
        predicted_label = data_cat[top_indices[0]].lower()
        confidence = 100 * score[top_indices[0]]
        return predicted_label, confidence, score, top_indices

    def get_chat_response(label, question):
        keyword_map = {
            'nutrition': 'nutrition',
            'antioxidant': 'antioxidant',
            'diet': 'diet',
            'recipe': 'recipe',
            'calorie': 'calorie',
            'calories': 'calorie',
        }

        category_data = {
            'nutrition': nutrition_info,
            'antioxidant': antioxidant_score,
            'diet': diet_notes,
            'recipe': recipe_suggestions,
            'calorie': calorie_info,
        }

        question = question.lower()
        matched = {canonical for kw, canonical in keyword_map.items() if kw in question}

        if not matched:
            return "🤖 Sorry, I can only answer about nutrition, antioxidant, diet, recipe, or calories."

        response = f"📘 Info for {label.capitalize()}:\n"
        for category in matched:
            data = category_data.get(category, {}).get(label)
            if not data:
                response += f"\n❌ No {category} data available."
                continue

            if category == "nutrition":
                response += "\n🍎 Nutrition per 100g:\n"
                for k, v in data.items():
                    response += f" - {k.capitalize()}: {v} g\n"
            elif category == "calorie":
                response += f"\n🔥 Calories: {data} kcal per 100g\n"
            elif category == "diet":
                response += f"\n📝 Diet Note: {data}\n"
            elif category == "recipe":
                response += f"\n👨‍🍳 Recipe Suggestion: {data}\n"
            elif category == "antioxidant":
                stars = "⭐" * int(data)
                response += f"\n🧪 Antioxidant Level: {stars} ({data}/5)\n"
        return response

    @app.on_message(filters.command("chatbox"))
    def chatbox_start(client, message: Message):
        print(">>> /chatbox command triggered")  # <-- ADD THIS LINE
        user_id = message.from_user.id
        active_chatbox_sessions[user_id] = {"awaiting_image": True}
        message.reply_text("📷 Please send an image of a fruit or vegetable to predict and ask a question.")

    @app.on_message(filters.photo)
    def handle_photo(client, message: Message):
        user_id = message.from_user.id
        session = active_chatbox_sessions.get(user_id)

        if not session or not session.get("awaiting_image"):
            return  # Ignore if not in chatbox mode
        print("Running CHATBOX handler")  # ✅ Debug print for chatbox
        image_path = client.download_media(message)
        label, confidence, score, top_indices = get_prediction(image_path)

        session["label"] = label
        session["awaiting_image"] = False

        response = f"🍓 Predicted: {label.capitalize()} ({confidence:.2f}% confidence)\n"
        response += "You can now ask about:\n- nutrition\n- antioxidant\n- diet\n- recipe\n- calories\n\nSend 'exit' to quit."
        message.reply_text(response)

    @app.on_message(filters.text & ~filters.command(["start", "predict", "chatbox"]))
    def handle_chatbox_questions(client, message: Message):
        user_id = message.from_user.id
        session = active_chatbox_sessions.get(user_id)

        if not session or session.get("awaiting_image"):
            return

        text = message.text.strip().lower()
        if text == "exit":
            message.reply_text("👋 Exiting chatbox. Use /chatbox to start again.")
            active_chatbox_sessions.pop(user_id, None)
            return

        label = session["label"]
        reply = get_chat_response(label, text)
        message.reply_text(reply)