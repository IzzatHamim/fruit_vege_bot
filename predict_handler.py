
from pyrogram import filters
from PIL import Image
import numpy as np
import tensorflow as tf

import os
from session import active_chatbox_sessions



# This function must be called in main.py with all required objects passed in
def register_predict_handler(app, model, data_cat, img_width, img_height,
                              nutrition_info, calorie_info, diet_notes,
                              recipe_suggestions, antioxidant_score):

    def find_nutrition_info(label):
        label = label.lower().strip().replace('_', ' ')
        return nutrition_info.get(label)

    def calorie_comparison(food, cal_per_100g):
        comparison = ""
        for snack, cal in calorie_info.items():
            if snack not in data_cat:
                equivalent_grams = (cal_per_100g / cal) * 100
                comparison += f" - {snack}: approx. {equivalent_grams:.0f}g\n"
        return comparison

    def prepare_image(image_path):
        image = Image.open(image_path).convert('RGB')
        image = image.resize((img_width, img_height))
        img_array = tf.keras.utils.img_to_array(image)
        return tf.expand_dims(img_array, 0)

    @app.on_message(filters.command("predict"))
    def start_predict(client, message):
        print(">>> /predict command triggered")
        message.reply_text("📷 Please send a photo of the fruit or vegetable to analyze.")

    @app.on_message(filters.photo)
    def handle_image(client, message):
        user_id = message.from_user.id

    # Skip predict if user is in chatbox mode
        if user_id in active_chatbox_sessions and active_chatbox_sessions[user_id].get("awaiting_image", False):
            return

        print("Running PREDICT handler")  # ✅ Debug print for prediction

        file_path = client.download_media(message)
        img_bat = prepare_image(file_path)

        prediction = model.predict(img_bat)
        score = tf.nn.softmax(prediction[0])
        label = data_cat[np.argmax(score)]
        confidence = 100 * np.max(score)

        response = f"🥗 **Prediction:** {label.capitalize()} ({confidence:.2f}% confidence)\n\n"

        # Nutrition info
        nutrition = find_nutrition_info(label)
        if nutrition:
            response += "🍎 **Nutrition per 100g:**\n"
            for k, v in nutrition.items():
                response += f" - {k.capitalize()}: {v} g\n"
        else:
            response += "❌ Nutrition info not available.\n"

        # Calorie comparison
        if label in calorie_info:
            cal_value = calorie_info[label]
            response += f"\n🔥 **Calories:** {cal_value} kcal per 100g\n"
            response += "**Snack Calorie Equivalent:**\n"
            response += calorie_comparison(label, cal_value)
        else:
            response += "\n❌ Calorie info not available.\n"

        # Dietary notes
        if label in diet_notes:
            response += f"\n📝 **Dietary Note:** {diet_notes[label]}\n"

        # Recipes
        if label in recipe_suggestions:
            response += f"\n👨‍🍳 **Recipes:** {recipe_suggestions[label]}\n"

        # Antioxidants
        score_value = antioxidant_score.get(label.lower(), None)
        if score_value:
            response += f"\n🧪 **Antioxidant Level:** {'⭐' * score_value} ({score_value}/5)\n"

        # Top 5 predictions
        top_indices = np.argsort(score)[-5:][::-1]
        response += "\n🔍 **Top 5 Predictions:**\n"
        for i in top_indices:
            response += f" - {data_cat[i]}: {100 * score[i]:.2f}%\n"
        
        response += "\n\n👉 Type /predict to predict another image, or /guess to play the guessing game!"

        message.reply_text(response)
        
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

