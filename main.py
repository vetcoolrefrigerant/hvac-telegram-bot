import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from hvac_calculator import calculate_heating_load, calculate_cooling_load

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# States
MODE, INDOOR_TEMP, OUTDOOR_TEMP, AREA_WALLS, U_WALLS, AREA_WINDOWS, U_WINDOWS, AREA_ROOF, U_ROOF, VOLUME, ACH, OCCUPANTS = range(12)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Heating Load", "Cooling Load"]]
    await update.message.reply_text(
        "👋 Welcome to your HVAC Calculator Bot!\n\n"
        "What do you want to calculate?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = update.message.text
    await update.message.reply_text("Indoor design temperature (°F)?\nExample: 75", reply_markup=ReplyKeyboardRemove())
    return INDOOR_TEMP

async def indoor_temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['t_indoor'] = float(update.message.text)
    await update.message.reply_text("Outdoor temperature (°F)?\nExample: 95 for summer, 20 for winter")
    return OUTDOOR_TEMP

async def outdoor_temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['t_outdoor'] = float(update.message.text)
    await update.message.reply_text("Wall area (sq ft)?")
    return AREA_WALLS

async def area_walls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_walls'] = float(update.message.text)
    await update.message.reply_text("U-value of walls?\n(Example: 0.06 for good insulation)")
    return U_WALLS

async def u_walls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_walls'] = float(update.message.text)
    await update.message.reply_text("Window area (sq ft)?")
    return AREA_WINDOWS

async def area_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_windows'] = float(update.message.text)
    await update.message.reply_text("U-value of windows?\n(Example: 0.35)")
    return U_WINDOWS

async def u_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_windows'] = float(update.message.text)
    await update.message.reply_text("Roof area (sq ft)?")
    return AREA_ROOF

async def area_roof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_roof'] = float(update.message.text)
    await update.message.reply_text("U-value of roof?\n(Example: 0.04)")
    return U_ROOF

async def u_roof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_roof'] = float(update.message.text)
    await update.message.reply_text("Room volume (cubic ft)?\n(Example: length × width × height)")
    return VOLUME

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['volume'] = float(update.message.text)
    await update.message.reply_text("Air changes per hour (ACH)?\n(Example: 0.5 for normal house)")
    return ACH

async def ach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ach'] = float(update.message.text)
    await update.message.reply_text("Number of occupants?")
    return OCCUPANTS

async def occupants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['occupants'] = int(update.message.text)
    
    data = context.user_data
    mode = data['mode']

    if mode == "Heating Load":
        result = calculate_heating_load(data)
        text = f"🔥 **Heating Load Results**\n\n" \
               f"Total Heat Loss: {result['total_btu_hr']} BTU/hr\n" \
               f"Recommended Airflow: {result['cfm']} CFM"
    else:
        result = calculate_cooling_load(data)
        text = f"❄️ **Cooling Load Results**\n\n" \
               f"Total: {result['total_btu_hr']} BTU/hr\n" \
               f"({result['tons']} Tons)\n" \
               f"Supply Airflow: {result['cfm']} CFM"

    await update.message.reply_text(text, parse_mode='Markdown')
    await update.message.reply_text("Type /start to do another calculation.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Calculation cancelled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mode_selected)],
            INDOOR_TEMP: [MessageHandler(filters.TEXT & ~filters.COMMAND, indoor_temp)],
            OUTDOOR_TEMP: [MessageHandler(filters.TEXT & ~filters.COMMAND, outdoor_temp)],
            AREA_WALLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_walls)],
            U_WALLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_walls)],
            AREA_WINDOWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_windows)],
            U_WINDOWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_windows)],
            AREA_ROOF: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_roof)],
            U_ROOF: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_roof)],
            VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume)],
            ACH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ach)],
            OCCUPANTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, occupants)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))

    print("✅ HVAC Bot is now fully running! Go test it in Telegram.")
    app.run_polling()

if __name__ == '__main__':
    main()