# bot.py - Bot Game + Penghasil Uang (Gabungan)
# Fitur: Tap Game, Spin Wheel, Mining, Daily Challenge, Iklan, Referral, Reward

import os
import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============== KONFIGURASI ==============
# GANTI DENGAN TOKEN BOT @bonybot
BOT_TOKEN = "8688237846:AAHELmvf2-1ey9TSpKJ7hdOfALVcyzWyXwk"  # Ganti dengan token asli @bonybot

# Ganti dengan link Adsterra kamu
ADSTERRA_LINK = "https://www.profitablecpmratenetwork.com/kqfhq8g8?key=c071febea740ce726b657c77f4dafd7a"

# ID Telegram admin
ADMIN_ID = "7133296170"

# Konfigurasi Game
TAP_COOLDOWN = 2          # detik
SPIN_COOLDOWN = 21600     # 6 jam
MINING_INTERVAL = 3600    # 1 jam

# Bonus Referral
REFERRAL_BONUS = 20
REFERRED_BONUS = 10

# Data user
users = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== FUNGSI BANTU ==============
def get_user(user_id):
    """Ambil data user atau buat baru"""
    if user_id not in users:
        users[user_id] = {
            'points': 0,
            'username': '',
            'ads_watched': 0,
            'last_ad': None,
            # Tap Game
            'taps': 0,
            'tap_power': 1,
            'tap_level': 1,
            'last_tap': None,
            # Spin Wheel
            'spins': 0,
            'last_spin': None,
            'jackpot_hit': 0,
            # Mining
            'mining_level': 1,
            'last_mine': None,
            'mined_total': 0,
            # Daily Challenge
            'daily_streak': 0,
            'last_daily': None,
            'challenges_completed': [],
            # Referral
            'referrals': [],
            'referred_by': None,
            'referral_bonus': 0
        }
    return users[user_id]

def update_username(user_id, username):
    if user_id in users:
        users[user_id]['username'] = username
    else:
        get_user(user_id)
        users[user_id]['username'] = username

def get_mining_rate(level):
    return level * 5

def get_upgrade_cost(level):
    return level * 100

def get_tap_upgrade_cost(level):
    return level * 100

# ============== MENU UTAMA ==============
async def show_menu(query, user_id):
    user_data = get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🖱️ TAP GAME", callback_data="tap_game")],
        [InlineKeyboardButton("🎡 SPIN WHEEL", callback_data="spin_wheel")],
        [InlineKeyboardButton("⛏️ MINING", callback_data="mining")],
        [InlineKeyboardButton("📋 DAILY CHALLENGE", callback_data="daily")],
        [InlineKeyboardButton("💰 LIHAT IKLAN", callback_data="watch_ad")],
        [InlineKeyboardButton("👥 REFERRAL", callback_data="referral")],
        [InlineKeyboardButton("💸 TUKAR POIN", callback_data="reward")],
        [InlineKeyboardButton("📊 STATUS", callback_data="status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🏆 *GAME & EARNING CENTER* 🏆

👤 @{user_data.get('username', 'Pengguna')}
💰 Total Poin: *{user_data['points']}*

🎮 *Game & Fitur:*
🖱️ Tap Game - Klik cepat dapat poin
🎡 Spin Wheel - Jackpot hingga 100 poin
⛏️ Mining - Tambang pasif per jam
📋 Daily Challenge - Misi harian
💰 Lihat Iklan - Dapat 10 poin/iklan
👥 Referral - Ajak teman dapat bonus

Pilih menu di bawah! 🚀
"""
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_menu(query, query.from_user.id)

# ============== LIHAT IKLAN ==============
async def watch_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    if user_data['last_ad']:
        time_diff = (datetime.now() - user_data['last_ad']).total_seconds()
        if time_diff < 30:
            remaining = int(30 - time_diff)
            await query.answer(f"Tunggu {remaining} detik!", show_alert=True)
            return
    
    keyboard = [
        [InlineKeyboardButton("👆 KLIK IKLAN", url=ADSTERRA_LINK)],
        [InlineKeyboardButton("✅ Saya Sudah Lihat", callback_data="claim_ad")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎬 *IKLAN SIAP!*\n\n1. Klik tombol di atas\n2. Iklan akan terbuka\n3. Tutup iklan\n4. Klik 'Saya Sudah Lihat'\n\n💰 Hadiah: 10 Poin",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def claim_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    user_data['points'] += 10
    user_data['ads_watched'] += 1
    user_data['last_ad'] = datetime.now()
    
    await query.edit_message_text(
        f"✅ +10 Poin!\n💰 Total: {user_data['points']}\n📺 Iklan: {user_data['ads_watched']}",
        parse_mode='Markdown'
    )
    await asyncio.sleep(2)
    await show_menu(query, user_id)

# ============== TAP GAME ==============
async def tap_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("👆 TAP!", callback_data="tap_action")],
        [InlineKeyboardButton(f"⚡ Upgrade (+{user_data['tap_power']+1}) - {get_tap_upgrade_cost(user_data['tap_level'])} poin", callback_data="upgrade_tap")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="tap_leaderboard")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🖱️ *TAP GAME* 🖱️

💎 Poin: *{user_data['points']}*
⚡ Power: *+{user_data['tap_power']}* per tap
📊 Total Tap: *{user_data['taps']}*
🎯 Level: *{user_data['tap_level']}*

Tekan TAP sebanyak-banyaknya!
"""
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def tap_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    if user_data['last_tap']:
        time_diff = (datetime.now() - user_data['last_tap']).total_seconds()
        if time_diff < TAP_COOLDOWN:
            remaining = int(TAP_COOLDOWN - time_diff)
            await query.answer(f"Tunggu {remaining} detik!", show_alert=True)
            return
    
    earn = user_data['tap_power']
    user_data['points'] += earn
    user_data['taps'] += 1
    user_data['last_tap'] = datetime.now()
    
    await query.answer(f"+{earn} poin!", show_alert=False)
    await tap_game(update, context)

async def upgrade_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    cost = get_tap_upgrade_cost(user_data['tap_level'])
    
    if user_data['points'] >= cost:
        user_data['points'] -= cost
        user_data['tap_power'] += 1
        user_data['tap_level'] += 1
        await query.answer(f"⚡ Power +{user_data['tap_power']}!", show_alert=True)
    else:
        await query.answer(f"Butuh {cost} poin!", show_alert=True)
    
    await tap_game(update, context)

async def tap_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_list = []
    for uid, data in users.items():
        user_list.append({
            'username': data.get('username', f'User_{uid}'),
            'taps': data.get('taps', 0)
        })
    
    user_list.sort(key=lambda x: x['taps'], reverse=True)
    top_users = user_list[:10]
    
    text = "🏆 *LEADERBOARD TAP* 🏆\n\n"
    for i, user in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{user['username']} - *{user['taps']} taps*\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Kembali", callback_data="tap_game")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ============== SPIN WHEEL ==============
async def spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    can_spin = True
    remaining_text = ""
    if user_data['last_spin']:
        time_diff = (datetime.now() - user_data['last_spin']).total_seconds()
        if time_diff < SPIN_COOLDOWN:
            can_spin = False
            remaining = int(SPIN_COOLDOWN - time_diff)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            remaining_text = f"\n⏳ Spin berikutnya: {hours} jam {minutes} menit"
    
    keyboard = []
    if can_spin:
        keyboard.append([InlineKeyboardButton("🎡 SPIN SEKARANG!", callback_data="spin_action")])
    keyboard.append([InlineKeyboardButton("🎰 Jackpot History", callback_data="jackpot_history")])
    keyboard.append([InlineKeyboardButton("◀️ Kembali", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎡 *SPIN WHEEL* 🎡

💰 Poin: *{user_data['points']}*
🎯 Total spin: *{user_data['spins']}*
💎 Jackpot: *{user_data['jackpot_hit']}* kali

🎁 Hadiah: 5-50 poin, JACKPOT: *100 poin!*

Spin gratis setiap 6 jam!{remaining_text}
"""
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def spin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    if user_data['last_spin']:
        time_diff = (datetime.now() - user_data['last_spin']).total_seconds()
        if time_diff < SPIN_COOLDOWN:
            remaining = int(SPIN_COOLDOWN - time_diff)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await query.answer(f"Tunggu {hours} jam {minutes} menit!", show_alert=True)
            return
    
    rewards = [5, 10, 15, 20, 25, 50, 100]
    reward = random.choice(rewards)
    
    user_data['points'] += reward
    user_data['spins'] += 1
    user_data['last_spin'] = datetime.now()
    
    if reward == 100:
        user_data['jackpot_hit'] += 1
        message = "🎉 *JACKPOT!* 🎉\n✨ +100 POIN!"
    else:
        message = f"🎡 *SPIN!*\n✨ +{reward} POIN"
    
    await query.edit_message_text(
        f"{message}\n\n💰 Total: {user_data['points']}\n\nSpin lagi dalam 6 jam!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🎡 Spin Lagi", callback_data="spin_wheel"),
            InlineKeyboardButton("◀️ Menu", callback_data="menu")
        ]])
    )

async def jackpot_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_list = []
    for uid, data in users.items():
        if data.get('jackpot_hit', 0) > 0:
            user_list.append({
                'username': data.get('username', f'User_{uid}'),
                'jackpots': data.get('jackpot_hit', 0)
            })
    
    user_list.sort(key=lambda x: x['jackpots'], reverse=True)
    top_users = user_list[:10]
    
    text = "💎 *JACKPOT HALL OF FAME* 💎\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. @{user['username']} - *{user['jackpots']} jackpot*\n"
    
    if not top_users:
        text += "Belum ada jackpot! Ayo spin!"
    
    keyboard = [[InlineKeyboardButton("◀️ Kembali", callback_data="spin_wheel")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ============== MINING ==============
async def mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    last_mine = user_data.get('last_mine')
    can_claim = False
    pending = 0
    
    if last_mine:
        time_diff = (datetime.now() - last_mine).total_seconds()
        if time_diff >= MINING_INTERVAL:
            can_claim = True
            pending = int(time_diff / MINING_INTERVAL) * get_mining_rate(user_data['mining_level'])
    else:
        can_claim = True
    
    keyboard = []
    if can_claim and pending > 0:
        keyboard.append([InlineKeyboardButton(f"⛏️ CLAIM (+{pending} poin)", callback_data="claim_mining")])
    elif can_claim:
        keyboard.append([InlineKeyboardButton("⛏️ START MINING", callback_data="start_mining")])
    keyboard.append([InlineKeyboardButton(f"⚡ Upgrade Level {user_data['mining_level']+1} - {get_upgrade_cost(user_data['mining_level'])} poin", callback_data="upgrade_mining")])
    keyboard.append([InlineKeyboardButton("🏆 Top Miner", callback_data="mining_leaderboard")])
    keyboard.append([InlineKeyboardButton("◀️ Kembali", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    rate = get_mining_rate(user_data['mining_level'])
    text = f"""
⛏️ *MINING SIMULATOR* ⛏️

💰 Poin: *{user_data['points']}*
⚙️ Level: *{user_data['mining_level']}*
📈 Rate: *{rate} poin/jam*
📊 Total Mined: *{user_data['mined_total']}*

⏱️ *Waktu Mining:*
"""
    
    if last_mine:
        next_mine = last_mine + timedelta(seconds=MINING_INTERVAL)
        time_left = next_mine - datetime.now()
        if time_left.total_seconds() > 0:
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            text += f"{hours} jam {minutes} menit lagi"
        else:
            text += "⚡ READY TO CLAIM!"
    else:
        text += "Tekan START MINING!"
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def start_mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    user_data['last_mine'] = datetime.now()
    await query.answer("⛏️ Mining dimulai! Kembali 1 jam!", show_alert=True)
    await mining(update, context)

async def claim_mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    last_mine = user_data.get('last_mine')
    if not last_mine:
        await query.answer("Mulai mining dulu!", show_alert=True)
        await mining(update, context)
        return
    
    time_diff = (datetime.now() - last_mine).total_seconds()
    if time_diff < MINING_INTERVAL:
        remaining = int(MINING_INTERVAL - time_diff)
        minutes = remaining // 60
        await query.answer(f"Tunggu {minutes} menit!", show_alert=True)
        return
    
    periods = int(time_diff / MINING_INTERVAL)
    rate = get_mining_rate(user_data['mining_level'])
    earned = periods * rate
    
    user_data['points'] += earned
    user_data['mined_total'] += earned
    user_data['last_mine'] = datetime.now()
    
    await query.answer(f"+{earned} poin!", show_alert=True)
    await mining(update, context)

async def upgrade_mining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    cost = get_upgrade_cost(user_data['mining_level'])
    
    if user_data['points'] >= cost:
        user_data['points'] -= cost
        user_data['mining_level'] += 1
        await query.answer(f"⚡ Level {user_data['mining_level']}!", show_alert=True)
    else:
        await query.answer(f"Butuh {cost} poin!", show_alert=True)
    
    await mining(update, context)

async def mining_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_list = []
    for uid, data in users.items():
        user_list.append({
            'username': data.get('username', f'User_{uid}'),
            'mined': data.get('mined_total', 0),
            'level': data.get('mining_level', 1)
        })
    
    user_list.sort(key=lambda x: x['mined'], reverse=True)
    top_users = user_list[:10]
    
    text = "🏆 *TOP MINERS* 🏆\n\n"
    for i, user in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{user['username']} - Level {user['level']} - *{user['mined']} mined*\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Kembali", callback_data="mining")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ============== DAILY CHALLENGE ==============
async def daily_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    today = datetime.now().date()
    last_daily = user_data.get('last_daily')
    
    if not last_daily or last_daily.date() != today:
        user_data['challenges_completed'] = []
    
    challenges = [
        {"name": "🖱️ Tap 10x", "target": 10, "current": user_data.get('taps', 0), "reward": 30},
        {"name": "🎡 Spin 1x", "target": 1, "current": user_data.get('spins', 0), "reward": 30},
        {"name": "⛏️ Claim Mining", "target": 1, "current": user_data.get('mined_total', 0) // 10, "reward": 30},
        {"name": "💰 Lihat Iklan", "target": 1, "current": user_data.get('ads_watched', 0), "reward": 30},
    ]
    
    streak = user_data.get('daily_streak', 0)
    streak_bonus = streak * 10
    completed = user_data.get('challenges_completed', [])
    
    keyboard = []
    for i, challenge in enumerate(challenges):
        if i in completed:
            status = "✅"
        else:
            status = "⬜"
            progress = min(challenge['current'], challenge['target'])
            status += f" {progress}/{challenge['target']}"
        keyboard.append([InlineKeyboardButton(f"{status} {challenge['name']} (+{challenge['reward']})", callback_data=f"claim_challenge_{i}")])
    
    if len(completed) == len(challenges):
        keyboard.append([InlineKeyboardButton(f"🎁 CLAIM ALL! +{sum(c['reward'] for c in challenges) + streak_bonus} poin", callback_data="claim_all_daily")])
    
    keyboard.append([InlineKeyboardButton("◀️ Kembali", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
📋 *DAILY CHALLENGE* 📋

🔥 Streak: *{streak} hari* (+{streak_bonus} bonus)

Progress: *{len(completed)}/{len(challenges)}* selesai

🎁 Hadiah total: {sum(c['reward'] for c in challenges)} poin + bonus streak
"""
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def claim_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    challenge_id = int(query.data.split('_')[2])
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    if challenge_id in user_data.get('challenges_completed', []):
        await query.answer("Sudah di-claim!", show_alert=True)
        return
    
    challenges = [
        {"name": "Tap 10x", "target": 10, "current": user_data.get('taps', 0)},
        {"name": "Spin 1x", "target": 1, "current": user_data.get('spins', 0)},
        {"name": "Claim Mining", "target": 1, "current": user_data.get('mined_total', 0) // 10},
        {"name": "Lihat Iklan", "target": 1, "current": user_data.get('ads_watched', 0)},
    ]
    
    challenge = challenges[challenge_id]
    rewards = [30, 30, 30, 30]
    
    if challenge['current'] >= challenge['target']:
        reward = rewards[challenge_id]
        user_data['points'] += reward
        user_data['challenges_completed'].append(challenge_id)
        await query.answer(f"+{reward} poin!", show_alert=True)
    else:
        await query.answer(f"Butuh {challenge['target'] - challenge['current']} lagi", show_alert=True)
    
    await daily_challenge(update, context)

async def claim_all_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    completed = user_data.get('challenges_completed', [])
    if len(completed) < 4:
        await query.answer("Selesaikan semua challenge!", show_alert=True)
        return
    
    rewards = [30, 30, 30, 30]
    total_reward = sum(rewards)
    
    streak = user_data.get('daily_streak', 0)
    streak_bonus = streak * 10
    total_reward += streak_bonus
    
    user_data['points'] += total_reward
    user_data['daily_streak'] = streak + 1
    user_data['last_daily'] = datetime.now()
    user_data['challenges_completed'] = []
    
    await query.answer(f"+{total_reward} poin! Streak +1!", show_alert=True)
    await daily_challenge(update, context)

# ============== START ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)
    update_username(user_id, user.username or "Unknown")
    
    args = context.args
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0].split('_')[1])
            if referrer_id != user_id and referrer_id in users:
                user_data['points'] += REFERRED_BONUS
                users[referrer_id]['points'] += REFERRAL_BONUS
                users[referrer_id]['referral_bonus'] += REFERRAL_BONUS
                if user_id not in users[referrer_id]['referrals']:
                    users[referrer_id]['referrals'].append(user_id)
        except:
            pass
    
    keyboard = [[InlineKeyboardButton("🎮 MULAI GAME", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎉 *SELAMAT DATANG DI GAME & EARNING CENTER!* 🎉

Halo @{user.username or 'Pengguna'}!

🎮 *Fitur Lengkap:*
🖱️ Tap Game - Klik cepat dapat poin
🎡 Spin Wheel - Jackpot hingga 100 poin
⛏️ Mining - Tambang pasif per jam
📋 Daily Challenge - Misi harian
💰 Lihat Iklan - Dapat 10 poin
👥 Referral - Ajak teman dapat bonus
💸 Tukar Poin - Pulsa/OVO/DANA

💰 Poin awal: *{user_data['points']}*

Klik tombol di bawah untuk mulai! 🚀
"""
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ============== STATUS ==============
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    text = f"""
📊 *STATUS LENGKAP*

👤 @{user_data.get('username', 'Pengguna')}
💰 Total Poin: {user_data['points']}

🖱️ *Tap Game:*
├─ Power: +{user_data['tap_power']}/tap
├─ Level: {user_data['tap_level']}
└─ Total Tap: {user_data['taps']}

🎡 *Spin Wheel:*
├─ Total Spin: {user_data['spins']}
└─ Jackpot: {user_data['jackpot_hit']}x

⛏️ *Mining:*
├─ Level: {user_data['mining_level']}
├─ Rate: {get_mining_rate(user_data['mining_level'])}/jam
└─ Total Mined: {user_data['mined_total']}

📋 *Daily:*
├─ Streak: {user_data.get('daily_streak', 0)} hari
└─ Challenge: {len(user_data.get('challenges_completed', []))}/4

💰 *Iklan:*
├─ Ditonton: {user_data.get('ads_watched', 0)} kali
└─ Total: {user_data.get('ads_watched', 0) * 10} poin

👥 *Referral:*
├─ Total: {len(user_data.get('referrals', []))}
└─ Bonus: {user_data.get('referral_bonus', 0)} poin
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Kembali", callback_data="menu")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ============== REFERRAL ==============
async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = f"""
👥 *REFERRAL PROGRAM*

🎁 Bonus: *+{REFERRAL_BONUS} poin* setiap teman!

🔗 *LINK REFERRALMU:*
`{referral_link}`

📊 Statistik:
├─ Total referral: *{len(user_data.get('referrals', []))}*
└─ Bonus: *{user_data.get('referral_bonus', 0)} poin*

Share link ke teman-temanmu! 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Copy Link", callback_data="copy_link")],
        [InlineKeyboardButton("◀️ Kembali", callback_data="menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def copy_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.edit_message_text(
        f"📋 *Link Referral*\n\n`{referral_link}`\n\nTekan lama → Copy\nShare ke teman! 🚀",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Kembali", callback_data="referral")
        ]])
    )

# ============== TUKAR POIN ==============
async def show_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    keyboard.append([InlineKeyboardButton("◀️ Kembali", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎁 *TUKAR POIN*

💰 Poin: *{points}*

📋 Hadiah:
• 100 poin = Rp 5.000
• 200 poin = Rp 10.000  
• 500 poin = Rp 25.000

Pilih hadiah di bawah!
"""
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def claim_reward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                text=f"🆕 *WITHDRAW*\n👤 @{query.from_user.username}\n💰 {reward['nominal']}\n📊 Sisa: {user_data['points']} poin",
                parse_mode='Markdown'
            )
        except:
            pass
        
        await query.edit_message_text(
            f"✅ *WITHDRAW TERKIRIM!*\n\n🎁 {reward['nominal']}\n💰 Sisa: {user_data['points']}\n\nAdmin akan hubungi kamu.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(f"❌ Poin tidak cukup! Butuh {reward['poin']} poin.", parse_mode='Markdown')
    
    await asyncio.sleep(2)
    await show_menu(query, user_id)

# ============== MAIN ==============
def main():
    print("=" * 50)
    print("🤖 BOT GAME + PENGHASIL UANG - STARTING...")
    print("=" * 50)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command
    app.add_handler(CommandHandler("start", start))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(menu, pattern="menu"))
    app.add_handler(CallbackQueryHandler(watch_ad, pattern="watch_ad"))
    app.add_handler(CallbackQueryHandler(claim_ad, pattern="claim_ad"))
    app.add_handler(CallbackQueryHandler(tap_game, pattern="tap_game"))
    app.add_handler(CallbackQueryHandler(tap_action, pattern="tap_action"))
    app.add_handler(CallbackQueryHandler(upgrade_tap, pattern="upgrade_tap"))
    app.add_handler(CallbackQueryHandler(tap_leaderboard, pattern="tap_leaderboard"))
    app.add_handler(CallbackQueryHandler(spin_wheel, pattern="spin_wheel"))
    app.add_handler(CallbackQueryHandler(spin_action, pattern="spin_action"))
    app.add_handler(CallbackQueryHandler(jackpot_history, pattern="jackpot_history"))
    app.add_handler(CallbackQueryHandler(mining, pattern="mining"))
    app.add_handler(CallbackQueryHandler(start_mining, pattern="start_mining"))
    app.add_handler(CallbackQueryHandler(claim_mining, pattern="claim_mining"))
    app.add_handler(CallbackQueryHandler(upgrade_mining, pattern="upgrade_mining"))
    app.add_handler(CallbackQueryHandler(mining_leaderboard, pattern="mining_leaderboard"))
    app.add_handler(CallbackQueryHandler(daily_challenge, pattern="daily"))
    app.add_handler(CallbackQueryHandler(claim_challenge, pattern="claim_challenge_"))
    app.add_handler(CallbackQueryHandler(claim_all_daily, pattern="claim_all_daily"))
    app.add_handler(CallbackQueryHandler(show_referral, pattern="referral"))
    app.add_handler(CallbackQueryHandler(copy_link_handler, pattern="copy_link"))
    app.add_handler(CallbackQueryHandler(show_reward, pattern="reward"))
    app.add_handler(CallbackQueryHandler(claim_reward_handler, pattern="reward_"))
    app.add_handler(CallbackQueryHandler(show_status, pattern="status"))
    
    print("✅ Bot Game + Penghasil Uang berjalan!")
    app.run_polling()

if __name__ == "__main__":
    main()
