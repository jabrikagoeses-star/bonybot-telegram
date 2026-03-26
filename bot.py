import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============== KONFIGURASI ==============
# Ganti dengan token dari @BotFather
BOT_TOKEN = "8688237846:AAHELmvf2-1ey9TSpKJ7hdOfALVcyzWyXwk"

# Ganti dengan link Adsterra 
ADSTERRA_LINK = "https://www.profitablecpmratenetwork.com/kqfhq8g8?key=c071febea740ce726b657c77f4dafd7a"

# ID Telegram admin untuk menerima notifikasi withdraw
ADMIN_ID = "7133296170"  

# Konfigurasi Referral
REFERRAL_BONUS = 20  # Bonus poin untuk yang mengajak
REFERRED_BONUS = 10  # Bonus poin untuk yang diajak

# Data user
users = {}

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============== FUNGSI BANTU ==============
def get_user(user_id):
    """Ambil data user atau buat baru"""
    if user_id not in users:
        users[user_id] = {
            'points': 0,
            'ads_watched': 0,
            'last_ad': None,
            'join_date': datetime.now(),
            'username': '',
            'referrals': [],
            'referred_by': None,
            'referral_bonus': 0
        }
    return users[user_id]

def update_username(user_id, username):
    """Update username user"""
    if user_id in users:
        users[user_id]['username'] = username
    else:
        get_user(user_id)
        users[user_id]['username'] = username

def generate_referral_link(bot_username, user_id):
    """Generate link referral untuk user"""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

# ============== COMMAND START ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah /start dengan referral"""
    user = update.effective_user
    user_id = user.id
    
    # Cek apakah ada parameter referral (format: /start ref_123456)
    args = context.args
    referrer_id = None
    
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0].split('_')[1])
        except:
            pass
    
    # Inisialisasi user baru
    if user_id not in users:
        users[user_id] = {
            'points': 0,
            'ads_watched': 0,
            'last_ad': None,
            'join_date': datetime.now(),
            'username': user.username or "Unknown",
            'referrals': [],
            'referred_by': None,
            'referral_bonus': 0
        }
        
        # Jika ada referral, kasih bonus
        if referrer_id and referrer_id != user_id and referrer_id in users:
            # Bonus untuk yang diajak
            users[user_id]['points'] += REFERRED_BONUS
            users[user_id]['referred_by'] = referrer_id
            
            # Bonus untuk yang mengajak
            users[referrer_id]['points'] += REFERRAL_BONUS
            users[referrer_id]['referral_bonus'] += REFERRAL_BONUS
            if user_id not in users[referrer_id]['referrals']:
                users[referrer_id]['referrals'].append(user_id)
            
            # Notifikasi ke yang mengajak
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 *REFERRAL BONUS!*\n\n"
                         f"@{user.username} bergabung menggunakan link referralmu!\n"
                         f"✨ Kamu mendapat +{REFERRAL_BONUS} poin!\n"
                         f"💰 Total referral bonus: {users[referrer_id]['referral_bonus']} poin",
                    parse_mode='Markdown'
                )
            except:
                pass
    
    user_data = get_user(user_id)
    
    # Keyboard dengan menu referral
    keyboard = [
        [InlineKeyboardButton("💰 Dapatkan Poin", callback_data="watch_ad")],
        [InlineKeyboardButton("📊 Status Saya", callback_data="status")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🎁 Tukar Poin", callback_data="reward")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Pesan sambutan
    welcome = f"🎉 *Halo @{user.username}!*\n\n"
    
    if referrer_id and referrer_id != user_id and referrer_id in users:
        welcome += f"✨ Kamu bergabung melalui referral @{users[referrer_id].get('username', 'someone')}!\n"
        welcome += f"🎁 Kamu mendapat +{REFERRED_BONUS} poin bonus!\n\n"
    
    welcome += f"💰 Poin kamu: {user_data['points']}\n\n"
    welcome += f"📢 *Cara kerja:*\n"
    welcome += f"1. Klik Dapatkan Poin\n"
    welcome += f"2. Lihat iklan\n"
    welcome += f"3. Dapat 10 poin\n"
    welcome += f"4. Ajak teman dapat bonus +{REFERRAL_BONUS} poin!\n\n"
    welcome += f"Selamat mencoba! 🚀"
    
    await update.message.reply_text(
        welcome,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    logger.info(f"User: @{user.username} (ID: {user.id})")

# ============== TAMPILKAN IKLAN ==============
async def watch_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menampilkan iklan"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    update_username(user_id, query.from_user.username or "Unknown")
    
    # Cek cooldown (30 detik)
    if user_data['last_ad']:
        time_diff = (datetime.now() - user_data['last_ad']).total_seconds()
        if time_diff < 30:
            remaining = int(30 - time_diff)
            await query.edit_message_text(
                f"⏳ *Tunggu {remaining} detik* sebelum iklan berikutnya!",
                parse_mode='Markdown'
            )
            await asyncio.sleep(2)
            await show_menu(query, user_id)
            return
    
    # Tombol iklan
    keyboard = [
        [InlineKeyboardButton("👆 KLIK IKLAN", url=ADSTERRA_LINK)],
        [InlineKeyboardButton("✅ Saya Sudah Lihat", callback_data="claim_reward")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎬 *Iklan Siap!*\n\n"
        "1. Klik tombol di atas\n"
        "2. Iklan akan terbuka\n"
        "3. Tutup iklan\n"
        "4. Klik 'Saya Sudah Lihat'\n\n"
        "💰 Hadiah: 10 Poin",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============== KLAIM POIN ==============
async def claim_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk klaim poin setelah lihat iklan"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    # Tambah poin
    user_data['points'] += 10
    user_data['ads_watched'] += 1
    user_data['last_ad'] = datetime.now()
    
    await query.edit_message_text(
        f"✅ *BERHASIL!*\n\n"
        f"✨ +10 Poin\n"
        f"💰 Total Poin: {user_data['points']}\n"
        f"📺 Iklan Ditonton: {user_data['ads_watched']}",
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(2)
    await show_menu(query, user_id)

# ============== STATUS AKUN ==============
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk melihat status"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    status_text = f"""
📊 *STATUS AKUN*

👤 *Username:* @{query.from_user.username or 'Belum diatur'}
💰 *Total Poin:* {user_data['points']}
📺 *Iklan Ditonton:* {user_data['ads_watched']}
👥 *Total Referral:* {len(user_data.get('referrals', []))}
🎁 *Bonus Referral:* {user_data.get('referral_bonus', 0)} poin

🎁 *HADIAH:*
└─ 100 poin = Rp 5.000
└─ 200 poin = Rp 10.000  
└─ 500 poin = Rp 25.000
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        status_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============== REFERRAL ==============
async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu referral"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    # Dapatkan username bot
    bot_username = context.bot.username
    
    # Generate link referral
    referral_link = generate_referral_link(bot_username, user_id)
    
    # Hitung statistik
    total_referrals = len(user_data.get('referrals', []))
    total_bonus = user_data.get('referral_bonus', 0)
    
    # Daftar referral
    referral_list = ""
    if total_referrals > 0:
        for i, ref_id in enumerate(user_data['referrals'][:5], 1):
            ref_data = users.get(ref_id, {})
            ref_name = ref_data.get('username', f'User_{ref_id}')
            referral_list += f"{i}. @{ref_name}\n"
        if total_referrals > 5:
            referral_list += f"... dan {total_referrals - 5} lainnya"
    else:
        referral_list = "Belum ada referral"
    
    text = f"""
👥 *REFERRAL PROGRAM*

🎁 *Dapatkan bonus dengan mengajak teman!*

📋 *Cara Kerja:*
1. Bagikan link referralmu ke teman
2. Teman klik link dan mulai menggunakan bot
3. Kamu dapat *+{REFERRAL_BONUS} poin* setiap teman!
4. Teman juga dapat *+{REFERRED_BONUS} poin* awal!

🔗 *LINK REFERRALMU:*
`{referral_link}`

📊 *Statistik:*
├─ Total referral: *{total_referrals}*
└─ Bonus referral: *{total_bonus} poin*

👥 *Daftar Referral:*
{referral_list}

💡 *Tips:* Share link ke grup atau media sosialmu!
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Copy Link", callback_data="copy_link")],
        [InlineKeyboardButton("🏆 Leaderboard Referral", callback_data="ref_leaderboard")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def copy_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle copy link"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    bot_username = context.bot.username
    referral_link = generate_referral_link(bot_username, user_id)
    
    await query.edit_message_text(
        f"📋 *Link Referral Kamu*\n\n"
        f"`{referral_link}`\n\n"
        f"📱 *Cara copy:* Tekan lama link → Copy\n\n"
        f"Share link ini ke teman-temanmu! 🚀",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Kembali", callback_data="referral")
        ]])
    )

async def ref_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard referral"""
    query = update.callback_query
    await query.answer()
    
    # Urutkan user berdasarkan jumlah referral
    user_list = []
    for uid, data in users.items():
        if 'referrals' in data:
            user_list.append({
                'id': uid,
                'username': data.get('username', f'User_{uid}'),
                'referrals': len(data.get('referrals', []))
            })
    
    # Sort descending
    user_list.sort(key=lambda x: x['referrals'], reverse=True)
    top_users = user_list[:10]
    
    text = "🏆 *LEADERBOARD REFERRAL* 🏆\n\n"
    
    if top_users:
        for i, user in enumerate(top_users, 1):
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            text += f"{medal} @{user['username']} - *{user['referrals']} referral*\n"
    else:
        text += "Belum ada data referral\n"
    
    text += "\n🎁 *Ajak teman dan masuk leaderboard!*"
    
    keyboard = [[InlineKeyboardButton("◀️ Kembali", callback_data="referral")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============== TUKAR POIN ==============
async def show_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menampilkan menu tukar poin"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    points = user_data['points']
    
    keyboard = []
    
    if points >= 100:
        keyboard.append([InlineKeyboardButton("💵 Rp 5.000 (100 poin)", callback_data="reward_100")])
    if points >= 200:
        keyboard.append([InlineKeyboardButton("💵 Rp 10.000 (200 poin)", callback_data="reward_200")])
    if points >= 500:
        keyboard.append([InlineKeyboardButton("💵 Rp 25.000 (500 poin)", callback_data="reward_500")])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton("❌ Belum ada hadiah", callback_data="no_action")])
    
    keyboard.append([InlineKeyboardButton("◀️ Kembali", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reward_text = f"""
🎁 *TUKAR POIN*

💰 Poin kamu: *{points}*

📋 Daftar Hadiah:
• 100 poin = Rp 5.000
• 200 poin = Rp 10.000  
• 500 poin = Rp 25.000

⚡ Pilih hadiah di bawah!
"""
    
    await query.edit_message_text(
        reward_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============== KLAIM HADIAH ==============
async def claim_reward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk klaim hadiah"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    reward_type = query.data
    
    reward_map = {
        'reward_100': {'poin': 100, 'nominal': 'Rp 5.000'},
        'reward_200': {'poin': 200, 'nominal': 'Rp 10.000'},
        'reward_500': {'poin': 500, 'nominal': 'Rp 25.000'}
    }
    
    reward = reward_map.get(reward_type)
    user_data = get_user(user_id)
    
    if user_data['points'] >= reward['poin']:
        user_data['points'] -= reward['poin']
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 *WITHDRAW REQUEST!*\n\n"
                     f"👤 User: @{query.from_user.username}\n"
                     f"💰 Hadiah: {reward['nominal']}\n"
                     f"📊 Sisa poin: {user_data['points']}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Gagal kirim notifikasi: {e}")
        
        await query.edit_message_text(
            f"✅ *WITHDRAW TERKIRIM!*\n\n"
            f"🎁 Hadiah: {reward['nominal']}\n"
            f"💰 Sisa poin: {user_data['points']}\n\n"
            f"Admin akan menghubungi kamu dalam 1x24 jam.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"❌ *GAGAL!* Poin tidak cukup.",
            parse_mode='Markdown'
        )
    
    await asyncio.sleep(2)
    await show_menu(query, user_id)

# ============== MENU UTAMA ==============
async def show_menu(query, user_id):
    """Menampilkan menu utama"""
    user_data = get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton(f"💰 Dapatkan Poin ({user_data['points']} poin)", callback_data="watch_ad")],
        [InlineKeyboardButton("📊 Status Saya", callback_data="status")],
        [InlineKeyboardButton("🎁 Tukar Poin", callback_data="reward")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🏠 *MENU UTAMA*\n\n"
        f"💰 Poin: {user_data['points']}\n"
        f"📺 Iklan: {user_data['ads_watched']}\n\n"
        f"👇 Pilih menu:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk kembali ke menu"""
    query = update.callback_query
    await query.answer()
    await show_menu(query, query.from_user.id)

async def no_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol yang tidak memiliki aksi"""
    query = update.callback_query
    await query.answer("Fitur sedang dalam pengembangan!")
    await asyncio.sleep(1)
    await show_menu(query, query.from_user.id)

# ============== MAIN ==============
def main():
    """Menjalankan bot"""
    print("=" * 50)
    print("🤖 BOT PENGHASIL UANG - STARTING...")
    print("=" * 50)
    print("⚠️  Pastikan BOT_TOKEN dan ADMIN_ID sudah diisi!")
    print("📱 Fitur Referral Aktif!")
    print("=" * 50)
    
    # Buat aplikasi
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Tambah command handler
    app.add_handler(CommandHandler("start", start))
    
    # Tambah callback handler
    app.add_handler(CallbackQueryHandler(watch_ad, pattern="watch_ad"))
    app.add_handler(CallbackQueryHandler(claim_reward, pattern="claim_reward"))
    app.add_handler(CallbackQueryHandler(show_status, pattern="status"))
    app.add_handler(CallbackQueryHandler(show_reward, pattern="reward"))
    app.add_handler(CallbackQueryHandler(show_referral, pattern="referral"))
    app.add_handler(CallbackQueryHandler(claim_reward_handler, pattern="reward_"))
    app.add_handler(CallbackQueryHandler(copy_link_handler, pattern="copy_link"))
    app.add_handler(CallbackQueryHandler(ref_leaderboard, pattern="ref_leaderboard"))
    app.add_handler(CallbackQueryHandler(menu, pattern="menu"))
    app.add_handler(CallbackQueryHandler(no_action, pattern="no_action"))
    
    # Jalankan bot
    print("\n✅ Bot berjalan! Tekan Ctrl+C untuk berhenti.\n")
    app.run_polling()

if __name__ == "__main__":
    main()