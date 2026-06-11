import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from hvac_calculator import calculate_heating_load, calculate_cooling_load, generate_pdf_report

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# States
MODE, INDOOR, OUTDOOR, WALLS, U_WALLS, WINDOWS, U_WINDOWS, ROOF, U_ROOF, VOLUME, ACH, OCCUPANTS = range(12)

U_VALUE_KB = [["0.04", "0.06", "0.08"], ["0.12", "0.25", "0.35"]]
ACH_KB = [["0.3", "0.5", "0.8"], ["1.0", "1.5"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Heating Load", "Cooling Load"]]
    await update.message.reply_text(
        "Welcome to VetCool HVAC Calculator!\n\nChoose mode:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['mode'] = update.message.text
    await update.message.reply_text("Indoor temperature (°F)? Example: 75", reply_markup=ReplyKeyboardRemove())
    return INDOOR

async def indoor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['t_indoor'] = float(update.message.text)
        await update.message.reply_text("Outdoor temperature (°F)?")
        return OUTDOOR
    except:
        await update.message.reply_text("Please enter a number.")
        return INDOOR

async def outdoor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['t_outdoor'] = float(update.message.text)
    await update.message.reply_text("Wall area (sq ft)?")
    return WALLS

async def walls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_walls'] = float(update.message.text)
    await update.message.reply_text("U-value of walls?", reply_markup=ReplyKeyboardMarkup(U_VALUE_KB, one_time_keyboard=True, resize_keyboard=True))
    return U_WALLS

async def u_walls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_walls'] = float(update.message.text)
    await update.message.reply_text("Window area (sq ft)?")
    return WINDOWS

async def windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_windows'] = float(update.message.text)
    await update.message.reply_text("U-value of windows?", reply_markup=ReplyKeyboardMarkup([["0.25", "0.35", "0.50"]], one_time_keyboard=True, resize_keyboard=True))
    return U_WINDOWS

async def u_windows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_windows'] = float(update.message.text)
    await update.message.reply_text("Roof area (sq ft)?")
    return ROOF

async def roof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['area_roof'] = float(update.message.text)
    await update.message.reply_text("U-value of roof?", reply_markup=ReplyKeyboardMarkup(U_VALUE_KB, one_time_keyboard=True, resize_keyboard=True))
    return U_ROOF

async def u_roof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_roof'] = float(update.message.text)
    await update.message.reply_text("Room volume (cubic ft)?")
    return VOLUME

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['volume'] = float(update.message.text)
    await update.message.reply_text("Air changes per hour (ACH)?", reply_markup=ReplyKeyboardMarkup(ACH_KB, one_time_keyboard=True, resize_keyboard=True))
    return ACH

async def ach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ach'] = float(update.message.text)
    await update.message.reply_text("Number of occupants?")
    return OCCUPANTS

async def occupants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['occupants'] = int(update.message.text)
    
    data = context.user_data
    mode = data.get('mode', '')

    if "Heating" in mode:
        result = calculate_heating_load(data)
        text = f"HEATING LOAD RESULTS\n\nTotal: {result['total_btu_hr']} BTU/hr\nAirflow: {result['cfm']} CFM"
    else:
        result = calculate_cooling_load(data)
        text = f"COOLING LOAD RESULTS\n\nTotal: {result['total_btu_hr']} BTU/hr ({result['tons']} Tons)\nAirflow: {result['cfm']} CFM"

    await update.message.reply_text(text)

    # PDF
    try:
        pdf_file = generate_pdf_report(data, result, mode)
        with open(pdf_file, 'rb') as f:
            await update.message.reply_document(document=f, filename=pdf_file, caption="VetCool HVAC Report")
        os.remove(pdf_file)
    except:
        await update.message.reply_text("PDF generation failed.")

    await update.message.reply_text("Type /start for a new calculation.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mode_selected)],
            INDOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, indoor)],
            OUTDOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, outdoor)],
            WALLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, walls)],
            U_WALLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_walls)],
            WINDOWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, windows)],
            U_WINDOWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_windows)],
            ROOF: [MessageHandler(filters.TEXT & ~filters.COMMAND, roof)],
            U_ROOF: [MessageHandler(filters.TEXT & ~filters.COMMAND, u_roof)],
            VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, volume)],
            ACH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ach)],
            OCCUPANTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, occupants)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))

    print("✅ VetCool Telegram Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()