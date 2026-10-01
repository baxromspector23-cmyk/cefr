import os
import json
import random
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, MenuButtonWebApp, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://baxromspector23-cmyk.github.io/cefr/webapp.html")


# ─── DATA ────────────────────────────────────────────────────────────────────

PLACEMENT_QUESTIONS = [
    {"q": "My name ___ Ali.", "opts": ["am", "is", "are", "be"], "a": 1, "lvl": "A1",
     "e": "\"I\" bilan \"am\", \"he/she/it\" bilan \"is\", \"we/they\" bilan \"are\" ishlatiladi."},
    {"q": "I ___ a student.", "opts": ["am", "is", "are", "be"], "a": 0, "lvl": "A1",
     "e": "\"I\" bilan har doim \"am\" ishlatiladi."},
    {"q": "She ___ two brothers.", "opts": ["have", "has", "having", "had"], "a": 1, "lvl": "A1",
     "e": "\"She\" bilan hozirgi zamonda \"has\" ishlatiladi."},
    {"q": "What color is grass?", "opts": ["Blue", "Green", "Red", "Black"], "a": 1, "lvl": "A1",
     "e": "Grass (o't) odatda green (yashil) rangda bo'ladi."},
    {"q": "Yesterday, I ___ to school.", "opts": ["go", "goes", "went", "going"], "a": 2, "lvl": "A2",
     "e": "\"Yesterday\" o'tgan zamonni bildiradi. \"Go\" ning Past Simple shakli \"went\"."},
    {"q": "He usually ___ breakfast at 7.", "opts": ["have", "has", "had", "having"], "a": 1, "lvl": "A2",
     "e": "\"He\" bilan Present Simple'da \"has\" ishlatiladi."},
    {"q": "We were tired, ___ we went home early.", "opts": ["because", "so", "but", "if"], "a": 1, "lvl": "A2",
     "e": "Natijani bildirish uchun \"so\" mos keladi: charchagan edik, shuning uchun erta ketdik."},
    {"q": "If I have time, I ___ you.", "opts": ["call", "called", "will call", "calling"], "a": 2, "lvl": "B1",
     "e": "First Conditional: if + Present Simple → will + verb."},
    {"q": "This book is ___ than the last one.", "opts": ["interesting", "more interesting", "most interesting", "interest"], "a": 1, "lvl": "B1",
     "e": "Ikki narsani taqqoslashda uzun sifat bilan \"more + adjective\" ishlatiladi."},
    {"q": "I have lived here ___ 2020.", "opts": ["for", "since", "during", "from"], "a": 1, "lvl": "B1",
     "e": "Aniq boshlanish nuqtasi bilan Present Perfect'da \"since\" ishlatiladi."},
]

READINGS = {
    "A1": [
        {"title": "My Family", "text": "My name is Tom. I live with my mother, father, and little sister. My mother likes tea, and my father likes coffee. My sister likes the color pink.", "qs": [
            {"type": "mcq", "q": "Who does Tom live with?", "opts": ["His friends", "His family", "His teacher", "His neighbors"], "a": 1, "e": "Matnda Tom onasi, otasi va singlisi bilan yashashi aytilgan."},
            {"type": "tf",  "q": "Tom's father likes coffee. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, matnda otasi coffee yoqtirishi aniq aytilgan."},
            {"type": "gap", "q": "Tom's sister likes the color ___. (So'zni yozing)", "a": "pink", "e": "Matnda singlisi pink rangni yoqtirishi aytilgan."},
        ]},
        {"title": "Breakfast", "text": "I get up at seven every morning. I eat bread and an egg for breakfast. I drink milk too. Then I go to school at eight o'clock.", "qs": [
            {"type": "mcq", "q": "What does the student drink?", "opts": ["Juice", "Water", "Milk", "Tea"], "a": 2, "e": "Nonushtada u milk (sut) ichadi."},
            {"type": "tf",  "q": "The student goes to school at eight. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, matnda maktabga soat 8da borishi aytilgan."},
            {"type": "gap", "q": "The student eats bread and an ___ for breakfast. (So'zni yozing)", "a": "egg", "e": "Non va tuxum — \"bread and an egg\"."},
        ]},
        {"title": "My Room", "text": "My room is small but nice. My bed is blue and my desk is white. I have three books on the desk. There is a small plant near the window.", "qs": [
            {"type": "mcq", "q": "What color is the bed?", "opts": ["White", "Blue", "Green", "Yellow"], "a": 1, "e": "Matnda karavot ko'k (blue) deb aytilgan."},
            {"type": "tf",  "q": "There are three books on the desk. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, matnda stol ustida 3 ta kitob borligi aytilgan."},
            {"type": "gap", "q": "There is a small ___ near the window. (So'zni yozing)", "a": "plant", "e": "Deraza yonida kichik plant (o'simlik) bor."},
        ]},
        {"title": "A School Day", "text": "Anna is ten years old. She likes English and music at school. Her best friend is Sara. They eat lunch together at school.", "qs": [
            {"type": "mcq", "q": "How old is Anna?", "opts": ["Eight", "Nine", "Ten", "Eleven"], "a": 2, "e": "Anna ten years old — u 10 yoshda."},
            {"type": "tf",  "q": "Anna and Sara eat lunch together. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, ular maktabda tushlikni birga yeyishadi."},
            {"type": "gap", "q": "Anna likes English and ___. (So'zni yozing)", "a": "music", "e": "Anna English va music fanlarini yoqtiradi."},
        ]},
        {"title": "Fruit", "text": "I like fruit. Apples are my favorite fruit because they are sweet. My brother likes bananas. We often eat fruit after dinner.", "qs": [
            {"type": "mcq", "q": "What is the speaker's favorite fruit?", "opts": ["Bananas", "Apples", "Oranges", "Grapes"], "a": 1, "e": "Apples (olmalar) sevimli mevasi."},
            {"type": "tf",  "q": "The brother likes bananas. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, ukasi bananlarni yoqtirishi aytilgan."},
            {"type": "gap", "q": "They often eat fruit after ___. (So'zni yozing)", "a": "dinner", "e": "Meva kechki ovqatdan keyin yeyiladi."},
        ]},
    ],
    "A2": [
        {"title": "A Busy Morning", "text": "Last Monday, I woke up late because my alarm did not ring. I quickly got dressed and left home without breakfast. I missed the first bus, so I walked to the station.", "qs": [
            {"type": "mcq", "q": "Why did the speaker wake up late?", "opts": ["The bus was late", "The alarm did not ring", "It was Sunday", "The station was closed"], "a": 1, "e": "Uyg'otgich jiringlamagani uchun u kech uyg'ongan."},
            {"type": "tf",  "q": "The speaker ate breakfast before leaving. True or False?", "opts": ["True ✅", "False ❌"], "a": 1, "e": "Yo'q, matnda u nonushtasiz uydan chiqqani aytilgan."},
            {"type": "gap", "q": "The speaker missed the first ___. (So'zni yozing)", "a": "bus", "e": "U birinchi avtobusni o'tkazib yuborgan."},
        ]},
        {"title": "Weekend Plans", "text": "My friends and I planned a picnic last weekend. We wanted to go to the park on Saturday, but it rained all morning. We changed our plan and watched a film at my house. On Sunday, we finally went to the park.", "qs": [
            {"type": "mcq", "q": "What did they do on Saturday?", "opts": ["Went to the park", "Watched a film", "Played football", "Visited a museum"], "a": 1, "e": "Yomg'ir sababli ular uyda film ko'rishgan."},
            {"type": "tf",  "q": "They went to the park on Sunday. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, yakshanba kuni ular parkka borishgan."},
            {"type": "gap", "q": "It ___ all morning on Saturday. (So'zni yozing)", "a": "rained", "e": "O'tgan zamon: rained (yomg'ir yog'di)."},
        ]},
        {"title": "My Daily Routine", "text": "I usually start work at nine in the morning. I check my emails and make a list of tasks. After lunch, I often have meetings. In the evening, I cook dinner and read for thirty minutes.", "qs": [
            {"type": "mcq", "q": "What does the speaker do after lunch?", "opts": ["Goes home", "Has meetings", "Eats breakfast", "Goes shopping"], "a": 1, "e": "Tushlikdan keyin uchrashuvlar o'tkazadi."},
            {"type": "tf",  "q": "The speaker reads in the evening. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, kechqurun 30 daqiqa kitob o'qiydi."},
            {"type": "gap", "q": "The speaker starts work at ___. (So'zni yozing)", "a": "nine", "e": "U ishni soat to'qqizda (nine) boshlaydi."},
        ]},
        {"title": "A New Hobby", "text": "Last year, I started learning photography. At first, taking good pictures was difficult, but I practiced every weekend. Now I enjoy taking pictures of nature and people.", "qs": [
            {"type": "mcq", "q": "When did the speaker start photography?", "opts": ["Last week", "Last month", "Last year", "Two years ago"], "a": 2, "e": "U fotografiyani o'tgan yili boshlagan."},
            {"type": "tf",  "q": "Taking good pictures was easy at first. True or False?", "opts": ["True ✅", "False ❌"], "a": 1, "e": "Yo'q, boshida qiyin bo'lgani aytilgan."},
            {"type": "gap", "q": "The speaker practiced every ___. (So'zni yozing)", "a": "weekend", "e": "U har hafta oxiri (weekend) mashq qilgan."},
        ]},
        {"title": "A Small Trip", "text": "Last summer, my family visited a small town near the mountains. We stayed there for three days. On the first day, we walked around the town and visited a local market. The next day, we went hiking.", "qs": [
            {"type": "mcq", "q": "How long did the family stay?", "opts": ["One day", "Two days", "Three days", "One week"], "a": 2, "e": "Ular u yerda uch kun qolishgan."},
            {"type": "tf",  "q": "The family visited a local market. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, birinchi kuni mahalliy bozorga borishgan."},
            {"type": "gap", "q": "They went ___ on the second day. (So'zni yozing)", "a": "hiking", "e": "Ikkinchi kuni ular hiking (piyoda sayr) ga chiqishgan."},
        ]},
    ],
    "B1": [
        {"title": "Learning a Language", "text": "Learning a new language can be challenging, but it opens many opportunities. People who speak another language communicate with more people and understand different cultures. Regular practice is important because progress comes from small improvements over time.", "qs": [
            {"type": "mcq", "q": "What can learning a new language open?", "opts": ["Only hobbies", "Many opportunities", "Fewer conversations", "More free time"], "a": 1, "e": "Matnda til o'rganish ko'plab imkoniyatlarni ochishi aytilgan."},
            {"type": "tf",  "q": "Regular practice is important for language progress. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, matn muntazam mashq muhimligini ta'kidlaydi."},
            {"type": "gap", "q": "Progress comes from small ___ over time. (So'zni yozing)", "a": "improvements", "e": "\"Small improvements\" — kichik yaxshilanishlar."},
        ]},
        {"title": "City or Countryside?", "text": "Living in a city can be convenient because shops, schools, and transport are usually nearby. However, cities can also be noisy and crowded. The countryside offers more space and quiet, although services may be farther away.", "qs": [
            {"type": "mcq", "q": "Why can city life be convenient?", "opts": ["It is always quiet", "Services are nearby", "There are no people", "It has more space"], "a": 1, "e": "Do'kon, maktab va transport yaqin bo'lishi shaharni qulay qiladi."},
            {"type": "tf",  "q": "The countryside is always closer to services. True or False?", "opts": ["True ✅", "False ❌"], "a": 1, "e": "Yo'q, matnda qishloqda xizmatlar uzoqroq bo'lishi mumkinligi aytilgan."},
            {"type": "gap", "q": "Cities can be noisy and ___. (So'zni yozing)", "a": "crowded", "e": "Shaharlar \"noisy and crowded\" (shovqinli va gavjum) deb tasvirlangan."},
        ]},
        {"title": "The Value of Exercise", "text": "Regular exercise supports both physical and mental well-being. It does not always require a gym — walking or cycling can also be useful. For many people, the biggest challenge is creating a routine. Starting with manageable activities makes it easier to continue.", "qs": [
            {"type": "mcq", "q": "What is the biggest challenge mentioned?", "opts": ["Finding a gym", "Creating a routine", "Buying a bicycle", "Learning a sport"], "a": 1, "e": "Ko'pchilik uchun eng katta qiyinchilik muntazam tartib yaratish."},
            {"type": "tf",  "q": "Exercise always requires a gym. True or False?", "opts": ["True ✅", "False ❌"], "a": 1, "e": "Yo'q, matn yurish va velosiped ham foydali ekanini aytadi."},
            {"type": "gap", "q": "Starting with ___ activities makes it easier. (So'zni yozing)", "a": "manageable", "e": "\"Manageable\" — boshqarish oson bo'lgan mashg'ulotlar."},
        ]},
        {"title": "Technology and Study", "text": "Digital tools make studying more flexible. Students can use videos, dictionaries, and online exercises whenever they have time. However, technology can also create distractions. A useful approach is to choose one task and turn off unnecessary notifications.", "qs": [
            {"type": "mcq", "q": "What is one disadvantage of technology?", "opts": ["It is expensive", "It creates distractions", "It removes books", "It stops studying"], "a": 1, "e": "Matnda texnologiya chalg'itishi mumkinligi aytilgan."},
            {"type": "tf",  "q": "Students can use digital tools whenever they have time. True or False?", "opts": ["True ✅", "False ❌"], "a": 0, "e": "Ha, matnda raqamli vositalardan bo'sh vaqt mavjud bo'lganda foydalanish mumkin."},
            {"type": "gap", "q": "Students can turn off unnecessary ___. (So'zni yozing)", "a": "notifications", "e": "Chalg'imaslik uchun bildirishnomalarni o'chirish tavsiya qilinadi."},
        ]},
        {"title": "Planning for the Future", "text": "Thinking about the future helps people make better decisions today. A student may want to improve their English, learn a skill, or prepare for university. Plans do not need to be perfect. It is more useful to set a clear goal, take small steps, and review progress regularly.", "qs": [
            {"type": "mcq", "q": "What can future planning help people do?", "opts": ["Avoid problems", "Make better decisions", "Become perfect", "Stop learning"], "a": 1, "e": "Kelajak haqida o'ylash bugungi qarorlarni yaxshilashga yordam beradi."},
            {"type": "tf",  "q": "Plans must be perfect. True or False?", "opts": ["True ✅", "False ❌"], "a": 1, "e": "Yo'q, matn rejalar mukammal bo'lishi shart emasligini aytadi."},
            {"type": "gap", "q": "It is useful to set a clear ___. (So'zni yozing)", "a": "goal", "e": "\"Set a clear goal\" — aniq maqsad qo'yish."},
        ]},
    ],
}

SPEAKING = {
    "A1": [
        {"q": "What is your name?", "uz": "Ismingiz nima?", "model": "My name is Ali. I am a student.", "keywords": ["name", "am", "is"], "adj": ["good", "happy", "nice", "small", "big"]},
        {"q": "How old are you?", "uz": "Yoshingiz nechada?", "model": "I am sixteen years old. I am a happy student.", "keywords": ["am", "old"], "adj": ["happy", "young", "good"]},
        {"q": "Do you have a pet?", "uz": "Uy hayvoningiz bormi?", "model": "Yes, I have a small cat. It is very cute.", "keywords": ["have", "is"], "adj": ["small", "cute", "big"]},
        {"q": "What do you eat for breakfast?", "uz": "Nonushtaga nima yeysiz?", "model": "I eat bread and eggs for breakfast. They are tasty.", "keywords": ["eat"], "adj": ["tasty", "good", "nice"]},
        {"q": "What color do you like?", "uz": "Qaysi rangni yoqtirasiz?", "model": "I like blue. Blue is a beautiful color.", "keywords": ["like", "is"], "adj": ["beautiful", "nice", "favorite"]},
    ],
    "A2": [
        {"q": "Describe your daily routine.", "uz": "Kundalik tartibingizni tasvirlab bering.", "model": "I usually wake up at seven. I have a quick breakfast and go to school. In the evening, I read a book.", "keywords": ["wake", "have", "go", "usually"], "adj": ["quick", "busy", "good"]},
        {"q": "What did you do yesterday?", "uz": "Kecha nima qildingiz?", "model": "Yesterday, I went to school and studied English. It was a busy day.", "keywords": ["went", "studied", "was"], "adj": ["busy", "tired", "good"]},
        {"q": "Tell me about your family.", "uz": "Oilangiz haqida gapirib bering.", "model": "My family is small. I live with my parents and my younger brother. We are friendly and close.", "keywords": ["live", "is", "are"], "adj": ["small", "friendly", "close"]},
        {"q": "What do you usually do at weekends?", "uz": "Dam olish kunlari nima qilasiz?", "model": "At weekends, I usually meet my friends. We often play football and have a good time.", "keywords": ["usually", "meet", "play"], "adj": ["good", "fun", "great"]},
        {"q": "Describe your favorite place.", "uz": "Sevimli joyingizni tasvirlab bering.", "model": "My favorite place is a quiet park near my home. It is beautiful and relaxing.", "keywords": ["is"], "adj": ["quiet", "beautiful", "relaxing", "favorite"]},
    ],
    "B1": [
        {"q": "What are the advantages of learning English?", "uz": "Ingliz tilini o'rganishning afzalliklari nima?", "model": "Learning English has many advantages. It helps people communicate internationally and find more opportunities.", "keywords": ["can", "help", "has", "advantages"], "adj": ["many", "important", "useful", "great"]},
        {"q": "Describe your hometown.", "uz": "Tug'ilib o'sgan shahringizni tasvirlab bering.", "model": "My hometown is a lively place with friendly people. It has busy streets and interesting places to visit.", "keywords": ["is", "has"], "adj": ["lively", "friendly", "interesting", "busy"]},
        {"q": "What would you like to do in the future?", "uz": "Kelajakda nima qilishni xohlaysiz?", "model": "In the future, I would like to improve my English and learn about technology. I hope to build useful skills.", "keywords": ["would", "like", "hope"], "adj": ["useful", "important", "good"]},
        {"q": "How can students improve their English?", "uz": "O'quvchilar ingliz tilini qanday yaxshilashlari mumkin?", "model": "Students can improve English by practicing regularly. They can read simple texts and listen to English every day.", "keywords": ["can", "improve", "practice"], "adj": ["simple", "regular", "daily"]},
        {"q": "Do you prefer studying alone or with others?", "uz": "Yolg'iz yoki boshqalar bilan o'qishni afzal ko'rasizmi?", "model": "I prefer studying with others because we can share ideas. It makes difficult tasks more interesting.", "keywords": ["prefer", "can", "because"], "adj": ["interesting", "difficult", "useful"]},
    ],
}

# ─── STATE ───────────────────────────────────────────────────────────────────

user_states = {}

def get_state(uid):
    if uid not in user_states:
        user_states[uid] = {
            "mode": None,           # placement / reading / speaking / menu
            "level": None,          # A1 / A2 / B1
            "placement_index": 0,
            "placement_score": 0,
            "session": None,        # current session dict
            "wrong": [],
            "progress": {"answered": 0, "correct": 0, "reading": {"answered": 0, "correct": 0}, "speaking": {"answered": 0, "correct": 0}},
        }
    return user_states[uid]

def save_level(uid, level):
    user_states[uid]["level"] = level

# ─── KEYBOARDS ───────────────────────────────────────────────────────────────

def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Web App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📖 Reading mashqi", callback_data="start_reading"),
         InlineKeyboardButton("🗣 Speaking mashqi", callback_data="start_speaking")],
        [InlineKeyboardButton("📊 Natijalarim", callback_data="show_progress"),
         InlineKeyboardButton("🔄 Darajani qayta aniqlash", callback_data="rerun_placement")],
    ])

def opts_kb(options, prefix="opt"):
    rows = []
    for i, opt in enumerate(options):
        rows.append([InlineKeyboardButton(opt, callback_data=f"{prefix}_{i}")])
    return InlineKeyboardMarkup(rows)

def next_kb(label="➡️ Keyingi savol", data="next"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=data)]])

# ─── PLACEMENT ───────────────────────────────────────────────────────────────

async def start_placement(update, context, uid):
    st = get_state(uid)
    st["mode"] = "placement"
    st["placement_index"] = 0
    st["placement_score"] = 0
    await send_placement_question(update, context, uid)

async def send_placement_question(update, context, uid):
    st = get_state(uid)
    idx = st["placement_index"]
    q = PLACEMENT_QUESTIONS[idx]
    text = (
        f"📝 *Daraja aniqlash testi*\n"
        f"Savol {idx+1} / {len(PLACEMENT_QUESTIONS)}\n\n"
        f"*{q['q']}*"
    )
    kb = opts_kb(q["opts"], prefix="place")
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

async def handle_placement_answer(update, context, uid, choice):
    st = get_state(uid)
    idx = st["placement_index"]
    q = PLACEMENT_QUESTIONS[idx]
    correct = choice == q["a"]
    if correct:
        st["placement_score"] += 1

    feedback = "✅ *To'g'ri!*" if correct else f"❌ *Xato.* To'g'ri javob: *{q['opts'][q['a']]}*"
    exp = q["e"]

    await update.callback_query.message.reply_text(
        f"{feedback}\n\n💡 _{exp}_",
        parse_mode="Markdown",
        reply_markup=next_kb("➡️ Keyingi savol", "place_next") if idx < 9 else next_kb("📊 Natijani ko'rish", "place_next")
    )

async def finish_placement(update, context, uid):
    st = get_state(uid)
    score = st["placement_score"]
    level = "A1" if score <= 4 else "A2" if score <= 7 else "B1"
    st["level"] = level
    st["mode"] = "menu"

    level_names = {"A1": "Boshlang'ich (A1)", "A2": "Boshlang'ichdan yuqori (A2)", "B1": "O'rta daraja (B1)"}
    tips = {
        "A1": "Hozir oddiy jumlalar va kundalik so'zlardan boshlang.",
        "A2": "Siz asosiy grammatikani bilasiz. O'tgan zamon va sifatlarni mashq qiling.",
        "B1": "Yaxshi daraja! Murakkab jumlalar va fikr ifodalashni mashq qiling.",
    }

    await update.callback_query.message.reply_text(
        f"🎉 *Test yakunlandi!*\n\n"
        f"Natija: *{score} / {len(PLACEMENT_QUESTIONS)}*\n"
        f"Darajangiz: *{level_names[level]}*\n\n"
        f"💡 _{tips[level]}_\n\n"
        f"Quyidan mashqni tanlang 👇",
        parse_mode="Markdown",
        reply_markup=menu_kb()
    )

# ─── READING ─────────────────────────────────────────────────────────────────

async def start_reading(update, context, uid):
    st = get_state(uid)
    level = st["level"] or "A1"
    passages = random.sample(READINGS[level], min(3, len(READINGS[level])))
    st["mode"] = "reading"
    st["session"] = {
        "passages": passages,
        "p_idx": 0,
        "q_idx": 0,
        "correct": 0,
        "wrong": 0,
        "answered": 0,
        "waiting_gap": False,
    }
    await send_reading_question(update, context, uid)

async def send_reading_question(update, context, uid):
    st = get_state(uid)
    sess = st["session"]
    p = sess["passages"][sess["p_idx"]]
    q = p["qs"][sess["q_idx"]]
    total_p = len(sess["passages"])
    p_num = sess["p_idx"] + 1
    q_num = sess["q_idx"] + 1

    header = (
        f"📖 *Reading mashqi* — Matn {p_num}/{total_p}, Savol {q_num}/3\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📄 *{p['title']}*\n\n"
        f"_{p['text']}_\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❓ *{q['q']}*"
    )

    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text

    if q["type"] in ("mcq", "tf"):
        sess["waiting_gap"] = False
        await send(header, parse_mode="Markdown", reply_markup=opts_kb(q["opts"], prefix="read"))
    else:
        sess["waiting_gap"] = True
        await send(header + "\n\n✏️ *Javobingizni yozing (inglizcha):*", parse_mode="Markdown")

async def handle_reading_answer(update, context, uid, choice=None, text_answer=None):
    st = get_state(uid)
    sess = st["session"]
    p = sess["passages"][sess["p_idx"]]
    q = p["qs"][sess["q_idx"]]

    if q["type"] in ("mcq", "tf"):
        correct = choice == q["a"]
        given_text = q["opts"][choice]
    else:
        given_text = (text_answer or "").strip().lower()
        correct = given_text == q["a"].lower()

    sess["answered"] += 1
    st["progress"]["answered"] += 1
    st["progress"]["reading"]["answered"] += 1
    if correct:
        sess["correct"] += 1
        st["progress"]["correct"] += 1
        st["progress"]["reading"]["correct"] += 1
    else:
        sess["wrong"] += 1
        if not any(w["key"] == f"r_{p['title']}_{sess['q_idx']}" for w in st["wrong"]):
            st["wrong"].append({"key": f"r_{p['title']}_{sess['q_idx']}", "type": "reading", "q": q["q"], "correct": q["a"] if q["type"] == "gap" else q["opts"][q["a"]]})

    feedback = "✅ *To'g'ri!*" if correct else f"❌ *Xato.* To'g'ri javob: *{q['a'] if q['type'] == 'gap' else q['opts'][q['a']]}*"
    exp = q["e"]

    # Determine what's next
    is_last_q = sess["q_idx"] == 2
    is_last_p = sess["p_idx"] == len(sess["passages"]) - 1

    if is_last_q and is_last_p:
        next_label, next_data = "📊 Seans natijasi", "end_session"
    else:
        next_label, next_data = "➡️ Keyingi savol", "read_next"

    sess["waiting_gap"] = False

    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(
        f"{feedback}\n\n💡 _{exp}_",
        parse_mode="Markdown",
        reply_markup=next_kb(next_label, next_data)
    )

# ─── SPEAKING ────────────────────────────────────────────────────────────────

async def start_speaking(update, context, uid):
    st = get_state(uid)
    level = st["level"] or "A1"
    questions = random.sample(SPEAKING[level], min(3, len(SPEAKING[level])))
    st["mode"] = "speaking"
    st["session"] = {
        "questions": questions,
        "idx": 0,
        "correct": 0,
        "wrong": 0,
        "answered": 0,
        "waiting_answer": True,
    }
    await send_speaking_question(update, context, uid)

async def send_speaking_question(update, context, uid):
    st = get_state(uid)
    sess = st["session"]
    q = sess["questions"][sess["idx"]]
    total = len(sess["questions"])
    num = sess["idx"] + 1

    text = (
        f"🗣 *Speaking mashqi* — Savol {num}/{total}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"❓ *{q['q']}*\n"
        f"🇺🇿 _{q['uz']}_\n\n"
        f"✏️ Inglizcha javobingizni yozing:"
    )
    sess["waiting_answer"] = True

    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(text, parse_mode="Markdown")

async def handle_speaking_answer(update, context, uid, answer):
    st = get_state(uid)
    sess = st["session"]
    q = sess["questions"][sess["idx"]]
    lower = answer.lower()

    has_verb = any(kw in lower for kw in q["keywords"])
    has_adj = any(adj in lower for adj in q["adj"])
    is_complete = len(answer.split()) >= 4

    checks = [
        ("Fe'l ishlatilgan", has_verb),
        ("Kamida 1 ta sifat ishlatilgan", has_adj),
        ("Gap to'liq (4+ so'z)", is_complete),
    ]
    score = sum(1 for _, ok in checks if ok)
    passed = score >= 2

    sess["answered"] += 1
    st["progress"]["answered"] += 1
    st["progress"]["speaking"]["answered"] += 1
    if passed:
        sess["correct"] += 1
        st["progress"]["correct"] += 1
        st["progress"]["speaking"]["correct"] += 1
    else:
        sess["wrong"] += 1
        if not any(w["key"] == f"s_{sess['idx']}" for w in st["wrong"]):
            st["wrong"].append({"key": f"s_{sess['idx']}", "type": "speaking", "q": q["q"]})

    checklist = "\n".join(
        f"{'✅' if ok else '❌'} {label}" for label, ok in checks
    )
    verdict = "🌟 *Yaxshi javob!*" if passed else "📝 *Yana mashq qiling.*"

    is_last = sess["idx"] == len(sess["questions"]) - 1
    next_label = "📊 Seans natijasi" if is_last else "➡️ Keyingi savol"
    next_data = "end_session" if is_last else "speak_next"

    sess["waiting_answer"] = False
    await update.message.reply_text(
        f"{verdict} ({score}/3 mezon)\n\n"
        f"{checklist}\n\n"
        f"📌 *Namuna javob:*\n_{q['model']}_",
        parse_mode="Markdown",
        reply_markup=next_kb(next_label, next_data)
    )

# ─── SESSION END ─────────────────────────────────────────────────────────────

async def show_session_end(update, context, uid):
    st = get_state(uid)
    sess = st["session"]
    answered = sess.get("answered", 0)
    correct = sess.get("correct", 0)
    wrong = sess.get("wrong", 0)
    pct = round(correct / answered * 100) if answered else 0

    msg = (
        f"🏁 *Seans yakunlandi!*\n\n"
        f"✅ To'g'ri: *{correct}*\n"
        f"❌ Xato: *{wrong}*\n"
        f"🎯 Aniqlik: *{pct}%*\n"
    )
    if st["wrong"]:
        msg += f"\n⚠️ Saqlanmagan xato savollar: *{len(st['wrong'])}* ta"

    await update.callback_query.message.reply_text(
        msg, parse_mode="Markdown", reply_markup=menu_kb()
    )
    st["mode"] = "menu"

# ─── PROGRESS ────────────────────────────────────────────────────────────────

async def show_progress(update, context, uid):
    st = get_state(uid)
    p = st["progress"]
    level = st["level"] or "—"
    answered = p["answered"]
    correct = p["correct"]
    pct = round(correct / answered * 100) if answered else 0
    r = p["reading"]
    s = p["speaking"]
    r_pct = round(r["correct"] / r["answered"] * 100) if r["answered"] else 0
    s_pct = round(s["correct"] / s["answered"] * 100) if s["answered"] else 0

    level_names = {"A1": "Boshlang'ich", "A2": "Boshlang'ichdan yuqori", "B1": "O'rta daraja"}

    text = (
        f"📊 *Mening natijalarim*\n\n"
        f"🏅 Daraja: *{level}* — {level_names.get(level, '')}\n\n"
        f"📝 Jami savollar: *{answered}*\n"
        f"🎯 Umumiy aniqlik: *{pct}%*\n"
        f"⚠️ Xato savollar: *{len(st['wrong'])}* ta\n\n"
        f"📖 Reading: *{r_pct}%* ({r['answered']} savol)\n"
        f"🗣 Speaking: *{s_pct}%* ({s['answered']} savol)"
    )
    send = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send(text, parse_mode="Markdown", reply_markup=menu_kb())

# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_state(uid)
    name = update.effective_user.first_name or "O'quvchi"

    # Set bottom-left Menu Button to open Web App
    try:
        await context.bot.set_chat_menu_button(
            chat_id=update.effective_chat.id,
            menu_button=MenuButtonWebApp(text="📱 Web App", web_app=WebAppInfo(url=WEBAPP_URL))
        )
    except Exception:
        pass

    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Web App-da ochish (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("🚀 Chatda testni boshlash", callback_data="start_placement")]
    ])

    await update.message.reply_text(
        f"👋 Salom, *{name}*!\n\n"
        f"Men sizga ingliz tilini CEFR uslubida o'rganishga yordam beraman.\n\n"
        f"📱 Endi botimizda qulay **Telegram Web App** mavjud! Xohlasangiz pastdagi tugma orqali ilovani ochishingiz yoki chatning o'zida test topshirishingiz mumkin.",
        parse_mode="Markdown",
        reply_markup=inline_kb
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    st = get_state(uid)
    data = query.data

    if data == "start_placement" or data == "rerun_placement":
        await start_placement(update, context, uid)

    elif data.startswith("place_"):
        if data == "place_next":
            st["placement_index"] += 1
            if st["placement_index"] >= len(PLACEMENT_QUESTIONS):
                await finish_placement(update, context, uid)
            else:
                await send_placement_question(update, context, uid)
        else:
            choice = int(data.split("_")[1])
            await handle_placement_answer(update, context, uid, choice)

    elif data == "start_reading":
        await start_reading(update, context, uid)

    elif data.startswith("read_"):
        if data == "read_next":
            sess = st["session"]
            if sess["q_idx"] < 2:
                sess["q_idx"] += 1
            else:
                sess["q_idx"] = 0
                sess["p_idx"] += 1
            await send_reading_question(update, context, uid)
        else:
            choice = int(data.split("_")[1])
            await handle_reading_answer(update, context, uid, choice=choice)

    elif data == "start_speaking":
        await start_speaking(update, context, uid)

    elif data == "speak_next":
        st["session"]["idx"] += 1
        st["session"]["waiting_answer"] = True
        await send_speaking_question(update, context, uid)

    elif data == "end_session":
        await show_session_end(update, context, uid)

    elif data == "show_progress":
        await show_progress(update, context, uid)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_state(uid)
    text = update.message.text.strip()
    mode = st.get("mode")
    sess = st.get("session")

    if mode == "reading" and sess and sess.get("waiting_gap"):
        await handle_reading_answer(update, context, uid, text_answer=text)

    elif mode == "speaking" and sess and sess.get("waiting_answer"):
        await handle_speaking_answer(update, context, uid, answer=text)

    else:
        await update.message.reply_text(
            "Mashqni boshlash uchun /start buyrug'ini yuboring.",
            reply_markup=menu_kb() if st.get("level") else None
        )

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
