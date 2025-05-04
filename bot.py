import logging, sqlite3, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

# ====== Configuration ======
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNELS = ["@Yonoappsgames", "@Payalearning6778", "@Neerajloot899"]
REWARD_PER_REFERRAL = 10
DATABASE_PATH = 'bot_data.sqlite'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY,
                 referred_by INTEGER,
                 rewards INTEGER DEFAULT 0
                 )''')
    conn.commit(); conn.close()

def add_user(user_id: int, referrer: int = None):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)',
              (user_id, referrer))
    conn.commit(); conn.close()

def give_reward(referrer_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET rewards = rewards + ? WHERE user_id = ?',
              (REWARD_PER_REFERRAL, referrer_id))
    conn.commit(); conn.close()

def get_rewards(user_id: int) -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('SELECT rewards FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def start(update: Update, context: CallbackContext):
    user = update.effective_user; args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    add_user(user.id, referrer_id)
    if referrer_id and referrer_id != user.id: give_reward(referrer_id)

    keyboard = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.strip('@')}")]
                for ch in CHANNELS]
    keyboard.append([InlineKeyboardButton("I've Joined ✅", callback_data='check_join')])
    markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"Welcome {user.first_name}!\nRefer friends: https://t.me/{context.bot.username}?start={user.id}\n"
        f"You earn ₹{REWARD_PER_REFERRAL} per referral once they join all channels.",
        reply_markup=markup
    )

def button_handler(update: Update, context: CallbackContext):
    q = update.callback_query; user = q.from_user; q.answer()
    for ch in CHANNELS:
        m = context.bot.get_chat_member(ch, user.id)
        if m.status in ['left', 'kicked']:
            return q.edit_message_text(f"Please join {ch} to proceed.")
    rewards = get_rewards(user.id)
    q.edit_message_text(
        f"🎉 Thank you for joining!\nYour reward balance: ₹{rewards}\nUse /withdraw to request payout."
    )

def withdraw(update: Update, context: CallbackContext):
    u = update.effective_user; bal = get_rewards(u.id)
    if bal <= 0:
        update.message.reply_text("You have no reward balance yet.")
    else:
        update.message.reply_text(f"You have ₹{bal}. Send your UPI/Paytm to receive payout.")

def main():
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('withdraw', withdraw))
    dp.add_handler(CallbackContext.handler('callback_query', button_handler))
    updater.start_polling(); logger.info("Bot started..."); updater.idle()

if __name__ == '__main__':
    main()