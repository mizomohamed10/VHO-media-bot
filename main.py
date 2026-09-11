import io
import os
import time
import hashlib
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageOps
from flask import Flask, request
import cloudinary
from cloudinary.utils import cloudinary_url

# ==========================================
# 1. setting and keys
# ==========================================
TOKEN = 'YOUR_TOKEN_ID'

cloudinary.config(
    cloud_name = 'ahnhpsmm',
    api_key = '381414951474358',
    api_secret = 'yNxisro8IFd1UqKPKhdfV3COa_o',
    secure = True
)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
user_images = {}

# 🛡️ Authorized people
def get_allowed_users():
    try:
        with open("/home/photoroom/mysite/allowed_users.txt", "r") as file:
            return [int(line.strip()) for line in file if line.strip().isdigit()]
    except FileNotFoundError:
        return [5794534113]


# 📁 main frames 
FRAMES = {
    "f1": {"name": "🖼️ إطار VHO + CLUB (نادي واحد)", "path": "/home/photoroom/mysite/VHO+CLUB.png", "logos_needed": 1},
    "f2": {"name": "🌟 إطار VHO (عام)", "path": "/home/photoroom/mysite/VHO.png", "logos_needed": 0},
    "f3": {"name": "🎨 إطار CLUB + CLUB (ناديين)", "path": "/home/photoroom/mysite/CLUB+CLUB.png", "logos_needed": 2}
}

# 📁 Clubs
CLUBS = {
    "c1": {"name": "💻 نادي البرمجه", "path": "/home/photoroom/mysite/logos/Programing.png", "ready_frame": "/home/photoroom/mysite/ready_frame/programingclub.png"},
    "c2": {"name": "📚 نادي الكتاب", "path": "/home/photoroom/mysite/logos/BookCaf.png", "ready_frame": "/home/photoroom/mysite/ready_frame/bookcaf.png"},
    "c3": {"name": "🔤 نادي الإنجليزية", "path": "/home/photoroom/mysite/logos/EngHub.png", "ready_frame": "/home/photoroom/mysite/ready_frame/ENGLISH HUB.png"},
    "c4": {"name": "🐝 Hive", "path": "/home/photoroom/mysite/logos/Hive.png", "ready_frame": "/home/photoroom/mysite/ready_frame/frame_Hive.png"},
    "c5": {"name": "🧠 MHPSS", "path": "/home/photoroom/mysite/logos/MHPSS.png", "ready_frame": "/home/photoroom/mysite/ready_frame/MHPSS .png"},
    "c6": {"name": "🗣️ نادي المناظرات", "path": "/home/photoroom/mysite/logos/Hujha.png", "ready_frame": "/home/photoroom/mysite/ready_frame/huja.png"},
    "c7": {"name": "🌍 Youth for the earth", "path": "/home/photoroom/mysite/logos/YouthforEarth.png", "ready_frame": "/home/photoroom/mysite/ready_frame/envandclimate.png"},
    "c8": {"name": "🔬 Research", "path": "/home/photoroom/mysite/logos/Research.png", "ready_frame": "/home/photoroom/mysite/ready_frame/search&Dev.png"},
    "c9": {"name": "💪 مبادرة قادرين", "path": "/home/photoroom/mysite/logos/Gadreen.png", "ready_frame": "/home/photoroom/mysite/ready_frame/frame_Gadreen.png"},
    "c10": {"name": " برناج جسور", "path": "/home/photoroom/mysite/logos/bridges.png", "ready_frame": "/home/photoroom/mysite/ready_frame/bridgesprogram.png"},
    "c11": {"name": " فريق موريتانيا", "path": "/home/photoroom/mysite/logos/muritania.png", "ready_frame": "/home/photoroom/mysite/ready_frame/muritania.png"}
}

# ==========================================
# 2. Keyboards
# ==========================================
def kb_main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🖼️ تركيب إطار للفعالية", callback_data="menu_frame"),
        InlineKeyboardButton("✨ تعديل ألوان الصورة", callback_data="menu_edit")
    )
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))
    return markup

def kb_frames():
    markup = InlineKeyboardMarkup(row_width=1)
    for key, data in FRAMES.items():
        markup.add(InlineKeyboardButton(data["name"], callback_data=f"applyframe_{key}"))
    markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main"))
    return markup

def kb_clubs():
    markup = InlineKeyboardMarkup(row_width=2)
    club_keys = list(CLUBS.keys())
    for i in range(0, len(club_keys), 2):
        row = []
        row.append(InlineKeyboardButton(CLUBS[club_keys[i]]["name"], callback_data=f"addclub_{club_keys[i]}"))
        if i+1 < len(club_keys):
            row.append(InlineKeyboardButton(CLUBS[club_keys[i+1]]["name"], callback_data=f"addclub_{club_keys[i+1]}"))
        markup.add(*row)
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))
    return markup

def kb_edit_main():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🪄 تحسين إضاءة ذكي (AI)", callback_data="auto_enhance"))
    markup.add(InlineKeyboardButton("✨ تعديل احترافي يدوي (AI)", callback_data="start_ai_flow"))
    markup.add(InlineKeyboardButton("⬜ إزالة الخلفية (بيضاء)", callback_data="remove_bg"))
    markup.add(InlineKeyboardButton("🖤 أبيض وأسود", callback_data="filter_bw"))
    markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main"))
    return markup

def kb_step1():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🔆 زيادة", callback_data="s1_up"), InlineKeyboardButton("🔅 تقليل", callback_data="s1_down"))
    markup.add(InlineKeyboardButton("⏭️ تخطي", callback_data="s2_start"))
    return markup

def kb_val_step1(sign):
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(InlineKeyboardButton("15%", callback_data=f"s1_v_{sign}15"), InlineKeyboardButton("30%", callback_data=f"s1_v_{sign}30"), InlineKeyboardButton("50%", callback_data=f"s1_v_{sign}50"))
    markup.add(InlineKeyboardButton("⏭️ تخطي", callback_data="s2_start"))
    return markup

def kb_step2():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🌗 زيادة", callback_data="s2_up"), InlineKeyboardButton("🌫️ تقليل", callback_data="s2_down"))
    markup.add(InlineKeyboardButton("⏭️ تخطي", callback_data="s3_start"))
    return markup

def kb_val_step2(sign):
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(InlineKeyboardButton("15%", callback_data=f"s2_v_{sign}15"), InlineKeyboardButton("30%", callback_data=f"s2_v_{sign}30"), InlineKeyboardButton("50%", callback_data=f"s2_v_{sign}50"))
    markup.add(InlineKeyboardButton("⏭️ تخطي", callback_data="s3_start"))
    return markup

def kb_step3():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🎨 تعزيز", callback_data="s3_pop"), InlineKeyboardButton("❄️ تبريد", callback_data="s3_cool"), InlineKeyboardButton("🔥 تدفئة", callback_data="s3_warm"))
    markup.add(InlineKeyboardButton("🚀 معالجة!", callback_data="process_ai"))
    return markup

def kb_val_step3(effect_type):
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(InlineKeyboardButton("خفيف", callback_data=f"s3_v_{effect_type}_15"), InlineKeyboardButton("متوسط", callback_data=f"s3_v_{effect_type}_30"), InlineKeyboardButton("قوي", callback_data=f"s3_v_{effect_type}_50"))
    markup.add(InlineKeyboardButton("🚀 معالجة!", callback_data="process_ai"))
    return markup

# ==========================================
# 3. Receiving images (secured)
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in get_allowed_users():
        bot.reply_to(message, f"⛔ عذراً، هذا البوت مخصص حصرياً لفريق ميديا Volunteers Hub Organization.\n\nمعرفك (ID) هو: <code>{user_id}</code>\nإذا كنت من الفريق، يرجى إرسال هذا الرقم الى @zezo_2490 لإضافتك للنظام.", parse_mode="HTML")
        return

    bot.reply_to(message, "أهلاً بك! 📸\nأرسل لي صورة لأقوم بتعديلها أو دمجها مع إطارات المنظمة.")

@bot.message_handler(content_types=['photo', 'document'])
def handle_incoming_media(message):
    user_id = message.from_user.id
    if user_id not in get_allowed_users():
        bot.reply_to(message, f"⛔ عذراً، غير مصرح لك باستخدام البوت.\nالـ ID الخاص بك هو: <code>{user_id}</code>", parse_mode="HTML")
        return

    chat_id = message.chat.id
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        user_images[chat_id] = {'file_id': file_id, 'is_document': False, 'ai_transforms': [], 'selected_clubs': []}
    else:
        if not message.document.mime_type.startswith('image/'):
            bot.reply_to(message, "يرجى إرسال ملف صورة صالح.")
            return
        file_id = message.document.file_id
        user_images[chat_id] = {'file_id': file_id, 'is_document': True, 'ai_transforms': [], 'selected_clubs': []}

    bot.reply_to(message, "تم استلام الصورة بنجاح! ✨\nماذا ترغب أن تفعل بها؟", reply_markup=kb_main_menu())

# ==========================================
# 4. Management of Interactions
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if user_id not in get_allowed_users():
        bot.answer_callback_query(call.id, "⛔ غير مصرح لك!")
        return

    chat_id = call.message.chat.id

    if call.data == "cancel":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="تم الإلغاء 🗑️")
        if chat_id in user_images: del user_images[chat_id]
        return
    if chat_id not in user_images: return

    if call.data == "back_to_main":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="ماذا ترغب أن تفعل بالصورة؟ ✨", reply_markup=kb_main_menu())

    elif call.data == "menu_frame":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="اختر الإطار المناسب للفعالية: 🖼️", reply_markup=kb_frames())

    elif call.data == "menu_edit":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="اختر نوع التعديل: 🎨", reply_markup=kb_edit_main())

    # Path for frames
    elif call.data.startswith("applyframe_"):
        frame_key = call.data.split("_")[1]
        user_images[chat_id]['selected_frame'] = frame_key
        logos_needed = FRAMES[frame_key]["logos_needed"]
        user_images[chat_id]['selected_clubs'] = []

        if logos_needed == 0:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري تركيب الإطار العام... ⏳🎨")
            execute_frame_processing(chat_id, call.message.message_id)
        else:
            msg = "اختر النادي:" if logos_needed == 1 else "اختر النادي **الأول** لإضافته:"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=msg, reply_markup=kb_clubs(), parse_mode="Markdown")

    elif call.data.startswith("addclub_"):
        club_key = call.data.split("_")[1]
        frame_key = user_images[chat_id].get('selected_frame')
        logos_needed = FRAMES[frame_key]["logos_needed"]

        user_images[chat_id]['selected_clubs'].append(club_key)

        if len(user_images[chat_id]['selected_clubs']) < logos_needed:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="اختر النادي **الثاني** لإضافته:", reply_markup=kb_clubs(), parse_mode="Markdown")
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري دمج الإطار... ⏳🎨")
            execute_frame_processing(chat_id, call.message.message_id)

    # Path for AI-based editing
    elif call.data == "auto_enhance":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري تحسين الإضاءة... 🤖✨")
        execute_cloudinary_processing(chat_id, call.message.message_id, [{'effect': 'improve'}])
    elif call.data == "remove_bg":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري إزالة الخلفية... ⬜🪄")
        execute_cloudinary_processing(chat_id, call.message.message_id, [{'effect': 'background_removal'}, {'background': 'white'}])
    elif call.data == "filter_bw":
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري تطبيق الأبيض والأسود... ⏳")
        try:
            file_info = bot.get_file(user_images[chat_id]['file_id'])
            image = Image.open(io.BytesIO(bot.download_file(file_info.file_path))).convert('L')
            out = io.BytesIO()
            image.save(out, format='JPEG')
            out.seek(0)
            out.name = 'BW.jpg'
            if user_images[chat_id]['is_document']: bot.send_document(chat_id, out)
            else: bot.send_photo(chat_id, out)
            bot.delete_message(chat_id, call.message.message_id)
            del user_images[chat_id]
        except Exception: pass
    elif call.data == "start_ai_flow":
        user_images[chat_id]['ai_transforms'] = [{'effect': 'enhance'}]
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="الخطوة 1: الإضاءة 💡", reply_markup=kb_step1())
    elif call.data in ["s1_up", "s1_down"]:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🎚️ اختر النسبة:", reply_markup=kb_val_step1("" if call.data == "s1_up" else "-"))
    elif call.data.startswith("s1_v_") or call.data == "s2_start":
        if call.data.startswith("s1_v_"): user_images[chat_id]['ai_transforms'].append({'effect': f"brightness:{call.data.replace('s1_v_', '')}"})
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="الخطوة 2: التباين 🌗", reply_markup=kb_step2())
    elif call.data in ["s2_up", "s2_down"]:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🎚️ اختر النسبة:", reply_markup=kb_val_step2("" if call.data == "s2_up" else "-"))
    elif call.data.startswith("s2_v_") or call.data == "s3_start":
        if call.data.startswith("s2_v_"): user_images[chat_id]['ai_transforms'].append({'effect': f"contrast:{call.data.replace('s2_v_', '')}"})
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="الخطوة 3: الألوان 🎨", reply_markup=kb_step3())
    elif call.data in ["s3_pop", "s3_cool", "s3_warm"]:
        em = {"s3_pop": "sat", "s3_cool": "blue", "s3_warm": "red"}
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🎚️ اختر القوة:", reply_markup=kb_val_step3(em[call.data]))
    elif call.data.startswith("s3_v_") or call.data == "process_ai":
        if call.data.startswith("s3_v_"):
            p = call.data.split('_')
            user_images[chat_id]['ai_transforms'].append({'effect': f'saturation:{p[3]}' if p[2]=="sat" else f'tint:{p[3]}:{p[2]}'})
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="جاري المعالجة... 🤖✨")
        execute_cloudinary_processing(chat_id, call.message.message_id, user_images[chat_id]['ai_transforms'])

# ==========================================
# 5. Function for Merging Frames (Smart System)
# ==========================================
def execute_frame_processing(chat_id, message_id):
    try:
        data = user_images[chat_id]
        frame_info = FRAMES[data['selected_frame']]
        clubs = data.get('selected_clubs', [])

        file_info = bot.get_file(data['file_id'])
        user_img = Image.open(io.BytesIO(bot.download_file(file_info.file_path))).convert("RGBA")

        # 💡 smart tire steering
        if len(clubs) == 1:
            # case : one club (ready frame)
            ready_frame_path = CLUBS[clubs[0]]["ready_frame"]
            if not os.path.exists(ready_frame_path): raise Exception(f"الإطار الجاهز غير موجود في الخادم! ({ready_frame_path})")
            frame_img = Image.open(ready_frame_path).convert("RGBA")
        else:
            # case : two frames 
            frame_img = Image.open(frame_info["path"]).convert("RGBA")

        frame_w, frame_h = frame_img.size

        
        user_img_resized = ImageOps.fit(user_img, frame_img.size, method=Image.Resampling.LANCZOS)
        user_img_resized.paste(frame_img, (0, 0), mask=frame_img)

        # merge logos manually
        if len(clubs) == 2:
            target_y = int(frame_h * 0.03)

            path_1 = CLUBS[clubs[0]]["path"]
            path_2 = CLUBS[clubs[1]]["path"]
            if not os.path.exists(path_1) or not os.path.exists(path_2): raise Exception("أحد شعارات الأندية غير موجود!")

            club_1 = Image.open(path_1).convert("RGBA")
            club_2 = Image.open(path_2).convert("RGBA")

            logo_w = int(frame_w * 0.08)

            ratio1 = logo_w / club_1.width
            club_1 = club_1.resize((logo_w, int(club_1.height * ratio1)), Image.Resampling.LANCZOS)

            ratio2 = logo_w / club_2.width
            club_2 = club_2.resize((logo_w, int(club_2.height * ratio2)), Image.Resampling.LANCZOS)

            target_x_1 = int(frame_w * 0.84)
            target_x_2 = int(frame_w * 0.92)

            user_img_resized.paste(club_1, (target_x_1, target_y), mask=club_1)
            user_img_resized.paste(club_2, (target_x_2, target_y), mask=club_2)

        # save and sends
        final_img = user_img_resized.convert("RGB")
        max_dimension = 2560
        if final_img.width > max_dimension or final_img.height >max_dimension:
            final_img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        output_stream = io.BytesIO()
        final_img.save(output_stream, format='JPEG', quality=95)
        output_stream.seek(0)
        output_stream.name = 'Framed_Image.jpg'

        if data['is_document']: bot.send_document(chat_id, output_stream, caption="تم التجهيز بنجاح! 🚀")
        else: bot.send_photo(chat_id, output_stream, caption="تم التجهيز بنجاح! 🚀")

        bot.delete_message(chat_id, message_id)
        del user_images[chat_id]

    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء التركيب: {str(e)}")

# ==========================================
# 6. cloud treatment (Cloudinary) و Webhook
# ==========================================
def execute_cloudinary_processing(chat_id, message_id, transforms):
    try:
        data = user_images[chat_id]
        file_info = bot.get_file(data['file_id'])
        original_bytes = bot.download_file(file_info.file_path)
        timestamp = int(time.time())
        api_secret = 'yNxisro8IFd1UqKPKhdfV3COa_o'
        string_to_sign = f"timestamp={timestamp}{api_secret}"
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
        upload_url = "https://api.cloudinary.com/v1_1/ahnhpsmm/image/upload"
        upload_data = {'api_key': '381414951474358', 'timestamp': timestamp, 'signature': signature}
        files = {'file': ('img.jpg', original_bytes, 'image/jpeg')}
        upload_response = requests.post(upload_url, data=upload_data, files=files).json()
        if 'error' in upload_response: raise Exception(upload_response['error']['message'])
        enhanced_url, _ = cloudinary_url(upload_response['public_id'], transformation=transforms)
        output_stream = io.BytesIO(requests.get(enhanced_url).content)
        output_stream.name = 'Edited.jpg'
        if data['is_document']: bot.send_document(chat_id, output_stream, caption="تمت المعالجة! 🚀")
        else: bot.send_photo(chat_id, output_stream, caption="تمت المعالجة! 🚀")
        bot.delete_message(chat_id, message_id)
        del user_images[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"خطأ: {str(e)}")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://photoroom.pythonanywhere.com/' + TOKEN)
    return "البوت يعمل بكفاءة! 🚀", 200