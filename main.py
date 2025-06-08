
import os
from pyrogram import Client, filters
from dotenv import load_dotenv
import tensorflow as tf

# External files
from data import nutrition_info, calorie_info, diet_notes, recipe_suggestions, antioxidant_score
from predict_handler import register_predict_handler
from chatbox import init_chatbox_handlers
from guess import register_guess_handlers


# Load environment variables
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Initialize bot
app = Client("fruit_classifier_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Load model
model = tf.keras.models.load_model("Image_classify.keras")

# Configuration
img_width, img_height = 180, 180
data_cat = [
    'apple', 'banana', 'beetroot', 'bell pepper', 'cabbage', 'capsicum', 'carrot', 'cauliflower',
    'chilli pepper', 'corn', 'cucumber', 'eggplant', 'garlic', 'ginger', 'grapes', 'jalepeno',
    'kiwi', 'lemon', 'lettuce', 'mango', 'onion', 'orange', 'paprika', 'pear', 'peas',
    'pineapple', 'pomegranate', 'potato', 'raddish', 'soy beans', 'spinach', 'sweetcorn',
    'sweetpotato', 'tomato', 'turnip', 'watermelon'
]

# /start command handler
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "**👋 Welcome to Fruit & Veggie Bot!**\n\n"
        "I can help you identify fruits and vegetables and give useful information like:\n"
        "- 🥗 Nutrition facts\n"
        "- 🔥 Calorie values\n"
        "- 🧪 Antioxidant ratings\n"
        "- 📝 Dietary notes\n"
        "- 👨‍🍳 Recipe suggestions\n\n"
        "**Available Commands:**\n"
        "/predict - Send a fruit/veggie image for prediction\n"
        "/guess - Guess the Fruit Game!"
        
    )
    
register_predict_handler(
    app=app,
    model=model,
    data_cat=data_cat,
    img_width=img_width,
    img_height=img_height,
    nutrition_info=nutrition_info,
    calorie_info=calorie_info,
    diet_notes=diet_notes,
    recipe_suggestions=recipe_suggestions,
    antioxidant_score=antioxidant_score
)
register_guess_handlers(app)


# Register the prediction handler





# Start the bot
app.run()