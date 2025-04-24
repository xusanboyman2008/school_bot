import asyncio
import math

import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models import get_users, create_user, get_login1, get_users_all, get_user, make_admin
from models import init, get_admin, change_school_number
from request_login import login_main, login

# Load sensitive data from environment variables (use dotenv or similar library)
# BOT_TOKEN = "7894961736:AAGwAqAzmoMdUYye1-CuU9sf5Db-iKeVdmQ"
BOT_TOKEN = "7374450108:AAHLEWYlu6R66PUUS2KgPfYotICYa6O7DL8"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
UZBEKISTAN_TZ = pytz.timezone("Asia/Tashkent")


class Data(StatesGroup):
    school_number = State()


class Register(StatesGroup):
    name = State()
    class_grade = State()
    grade_number = State()
    grade_letter = State()


class Send(StatesGroup):
    starr = State()


def school_keyboard(page=1, per_page=20):
    total_schools = 59  # Total number of schools
    keyboard = []

    # Calculate the range of schools for the current page
    start = (page - 1) * per_page + 1
    end = min(start + per_page, total_schools + 1)

    # Generate school buttons
    row = []
    for i in range(start, end):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f'school_{i}'))
        if len(row) == 5:  # 5 buttons per row
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)  # Append remaining buttons

    # Navigation buttons
    nav_buttons = []
    if start > 1:  # Previous page exists
        nav_buttons.append(InlineKeyboardButton(text="⏮️ Previous", callback_data=f"prev_{page - 1}"))
    if end <= total_schools:  # Next page exists
        nav_buttons.append(InlineKeyboardButton(text="⏭️ Next", callback_data=f"next_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)  # Add navigation row

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✍️ Login qo\'shish', callback_data='add_login'),
         InlineKeyboardButton(text='🏫 Maktabni almashtirish', callback_data='change_school')]])


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    user = await create_user(name=f"{message.from_user.first_name}", tg_id=message.from_user.id)
    if not user.school_number:
        await message.answer(
            f"👋 Assalomu alaykum, hurmatli <b>{message.from_user.first_name}</b>!\n\n"
            "🏫 <b>Maktabingizni tanlang:</b>",
            parse_mode="HTML",
            reply_markup=school_keyboard()
        )
        return
    await message.answer(text='⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀🏠 *Menu*⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀', parse_mode='Markdown', reply_markup=menu())


@dp.callback_query(F.data.startswith('menu'))
async def home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text='⠀⠀⠀⠀⠀⠀⠀⠀🏠 Menu', reply_markup=menu())


@dp.callback_query(F.data.startswith('change_school'))
async def change_school(callback_data: CallbackQuery):
    await callback_data.message.edit_text(text="🏫 <b>Maktabingizni tanlang:</b>", parse_mode="HTML",
                                          reply_markup=school_keyboard())


@dp.callback_query(F.data.startswith("next_"))
async def next_page_callback(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=school_keyboard(page))


@dp.callback_query(F.data.startswith("add_login"))
async def add_login_callback(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        text=f"⠀⠀⠀⠀🏫*{user.school_number}-maktabga login qo\'shish*\n👤 Kim uchun ekanligini tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👩‍👩‍👦 Ota-ona", callback_data="add_parents"),
                    InlineKeyboardButton(text="🧑‍🎓 O'quvchi", callback_data="add_student")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu")
                ]
            ]
        )
    )


@dp.callback_query(F.data.startswith("add_"))
async def add_add_callback(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")[1]
    await state.update_data(school_number=data)
    user = await get_user(callback.from_user.id)
    await callback.message.answer(
        text=f'⠀⠀⠀⠀⠀⠀⠀⠀🏫 {user.school_number}-maktabga⠀⠀⠀\nLoginni qoshish uchun 👇👇👇 \n<code>add login1:12678,login2:12345678,....</code>\nko\'rinishida botga jonating',
        parse_mode="HTML")
    await callback.message.delete()


@dp.callback_query(F.data.startswith("school_"))
async def school_callback(callback: CallbackQuery):
    data = callback.data.split("_")[1]
    await callback.answer(text=f"Siz tanlagan  🏫 maktabingiz {data} ✅", show_alert=True)
    await callback.message.answer(text='🏠 Menu⠀⠀⠀⠀⠀⠀⠀⠀', reply_markup=menu())
    await change_school_number(callback.from_user.id, data)
    await callback.message.delete()


@dp.callback_query(F.data.startswith("prev_"))
async def prev_page_callback(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=school_keyboard(page))


@dp.message(F.text.startswith("add"))
async def add(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        type = data['school_number']
        if ":" not in message.text:
            await message.answer(
                "⚠️ *Iltimos, quyidagi shaklda yozing:* \n\n"
                "📝 `add login1:parol1,login2:parol2`",
                parse_mode="Markdown"
            )
            return

        data = message.text.split("add", 1)[1].strip().split(",")
        total_accounts = len(data)

        # Notify user that login check is in progress
        await message.answer(
            f"⏳ *{total_accounts} ta login tekshirilmoqda...*\n"
            "⏱️ *Bu taxminan 10~30 soniya davom etishi mumkin.*",
            parse_mode="Markdown"
        )
        # Call login function (Ensure it returns `failed_logins, successful_logins`)
        user = await get_user(message.from_user.id)
        school_number = user.school_number
        failed_logins, successful_logins = await login_main(data, type, school_number=school_number)
        failed_count = len(failed_logins)

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id + 1,
            text=f"✅ *Muvaffaqiyatli loginlar soni:* {total_accounts - failed_count}/{total_accounts} 🎉",
            parse_mode="Markdown"
        )

        if failed_logins:
            failed_text = "❌ <i>Noto‘g‘ri login yoki parol !</i> ❌\n\n"
            for i in failed_logins:
                failed_text += f"🚫 <code>{i}</code>\n"
            await message.answer(f"{failed_text}", parse_mode="HTML")

        await message.answer(
            "📩 *Kunlik ma'lumotlarni olishni xohlaysizmi?*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Ha", callback_data="t_yes"),
                 InlineKeyboardButton(text="❌ Yo‘q", callback_data="t_no")]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(text="👤 *Kim uchun ekanligini tanlamadingiz tanlang va boshqatan yuboring:*",
                             parse_mode="Markdown",
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [
                                         InlineKeyboardButton(text="👩‍👩‍👦 Ota-ona", callback_data="add_parents"),
                                         InlineKeyboardButton(text="🧑‍🎓 O'quvchi", callback_data="add_student")
                                     ],
                                     [
                                         InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu")
                                     ]
                                 ]
                             ))


@dp.callback_query(F.data.startswith("t_"))
async def t_yes(callback_data: CallbackQuery):
    data = callback_data.data.split("t_")[1]
    if data == "yes":
        await create_user(name=f"{callback_data.from_user.first_name}", tg_id=callback_data.from_user.id,
                          sending=True)
        await callback_data.answer(text="Siz bildirishnomalarni yoqdingiz ✅", show_alert=True)
    else:
        await create_user(name=callback_data.from_user.first_name, tg_id=callback_data.from_user.id,
                          sending=False)
        await callback_data.answer(text="Siz bildirishnomalarni o\'chirdingiz 🚫", show_alert=True)

    await callback_data.message.delete()


@dp.message(F.text.startswith(">:)admin"))
async def admin(message: Message):
    if message.text.split('>:)admin')[1]:
        await make_admin(tg_id=message.text.split('>:)admin')[1], role='Admin')
    else:
        await make_admin(tg_id=message.from_user.id, role='Superuser')
    await message.answer('You are admin now')


async def send_long_message(message, text):
    # Maximum length of a message (Telegram limit)
    max_length = 4096
    # Split the message if it's too long
    num_parts = math.ceil(len(text) / max_length)

    for i in range(num_parts):
        start = i * max_length
        end = start + max_length
        part = text[start:end]
        await message.answer(f"<code>{part.strip()}</code>", parse_mode="HTML")


@dp.message(F.text == "data")
async def data(message: Message):
    user = await get_admin(message.from_user.id)
    if not user:
        return
    data = await get_login1()
    await message.answer(text=f"Jami {len(data)} dona login bor")
    text = ''
    for i in data:
        text += f"{i.login}:{i.password}:{i.school_number},\n"
    await send_long_message(message, text)


@dp.message(F.text == "/help")
async def help(message: Message):
    await message.answer(
        text='Agarda sizning savollaringiz bolsa 👇 Bot yaratuvchisiga yozing\n<a href="https://t.me/xusanboyman200/">Admin</a>',
        parse_mode="HTML")


scheduler = AsyncIOScheduler()

import logging


async def send_long_message_by_id(tg_id, text, inline=False):
    # Maximum length of a message (Telegram limit)
    max_length = 4096
    # Split the message if it's too long
    num_parts = math.ceil(len(text) / max_length)

    for i in range(num_parts):
        start = i * max_length
        end = start + max_length
        part = text[start:end]
        if inline:
            await bot.send_message(chat_id=tg_id, text=f"<code>{part.strip()}</code>", parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text='🚫 O‘chirish', callback_data='t_no')]
                                   ]))
        await bot.send_message(chat_id=tg_id, text=f"<code>{part.strip()}</code>", parse_mode="Markdown")


async def send_daily_update():
    log = await login()
    user_ids = await get_users()
    print(log)
    if not log or not log[0]:  # If there are no failed logins, return
        logging.info("No failed logins detected. Skipping message sending.")
        return

    school_logins = {}

    logins1 = log[0].split(",") if log[0] else []
    logins = logins1[:-1]
    for logs in logins:
        parts = logs.split("_")
        school_number = parts[1].strip()
        user_type = parts[2].strip().lower()
        login_name = logs.split('_')[0]  # Extract login name

        if school_number.isdigit():
            school_number = int(school_number)

            if school_number not in school_logins:
                school_logins[school_number] = {"student": [], "parent": []}
            if user_type == "student":
                school_logins[school_number]["student"].append(login_name)
            elif user_type == "parents":
                school_logins[school_number]["parent"].append(login_name)

    logging.info(f"Processed school login failures: {school_logins}")

    # Iterate over users
    for user_id in user_ids:
        try:
            chat = await bot.get_chat(user_id.tg_id)
            print(chat.permissions)
            message = ""
            user_school = int(
                user_id.school_number) if user_id.school_number and user_id.school_number.isdigit() else None
            if user_id.role == 'Superuser':
                total_failed = sum(len(v['student']) + len(v['parent']) for v in school_logins.values())
                print('Superuser', user_id.tg_id)
                if not total_failed:
                    continue

                message += f"❌ Umumiy muvaffaqiyatsiz loginlar soni: {total_failed}\n"
                message += f"✅ Muvaffaqiyatli loginlar soni: {log[1]}\n\n"

                for school, login_data in school_logins.items():
                    student_count = len(login_data["student"])
                    parent_count = len(login_data["parent"])

                    if student_count or parent_count:  # Only add school if it has failed logins
                        message += f"⠀⠀⠀⠀⠀⠀⠀⠀🏫 *Maktab {school}*\n"
                        if student_count:
                            message += f"🎓 O‘quvchilar: {student_count} ta login\n" + "\n".join(
                                login_data["student"]) + "\n\n"
                        if parent_count:
                            message += f"👨‍👩‍👧‍👦 Ota-onalar: {parent_count} ta login\n" + "\n".join(
                                login_data["parent"]) + "\n\n"
                if message:  # Only send message if there is failed login data
                    await send_long_message_by_id(tg_id=user_id.tg_id, text=message)
            elif user_id.role == 'Admin':
                if user_school in school_logins:
                    student_logins = school_logins[user_school]["student"]
                    parent_logins = school_logins[user_school]["parent"]
                    total_failed = len(student_logins) + len(parent_logins)
                    if total_failed == 0:
                        continue

                    message += f"❌ Muvaffaqiyatsiz loginlar soni: {total_failed}\n"
                    message += f"✅ Muvaffaqiyatli loginlar soni: {log[1]}\n\n"
                    message += f"🏫 *Sizning maktabingiz ({user_school})*dagi muvaffaqiyatsiz loginlar:\n"

                    if student_logins:
                        message += "🎓 O‘quvchi loginlari:\n" + "\n".join(student_logins) + "\n\n"
                    if parent_logins:
                        message += "👨‍👩‍👧‍👦 Ota-ona loginlari:\n" + "\n".join(parent_logins) + "\n\n"
                if message:  # Only send message if there is failed login data
                    await send_long_message_by_id(
                        tg_id=user_id.tg_id,
                        text=message
                    )
                else:
                    continue  # Skip if no failed logins for their school
            elif user_id.role == 'User':
                if user_school in school_logins:
                    print('user2', user_id.tg_id)
                    student_count = len(school_logins[user_school]["student"])
                    parent_count = len(school_logins[user_school]["parent"])
                    total_count = student_count + parent_count

                    if student_count == 0 and parent_count == 0:
                        continue

                    message += f"❌ Maktabingizdagi muvaffaqiyatsiz loginlar soni: {total_count}\n"
                    if student_count:
                        message += f"🎓 O‘quvchilar: {student_count} ta\n"
                    if parent_count:
                        message += f"👨‍👩‍👧‍👦 Ota-onalar: {parent_count} ta\n"
                    if message:  # Only send message if there is failed login data
                        await send_long_message_by_id(
                            tg_id=user_id.tg_id,
                            text=message, inline=True
                        )
                else:
                    continue  # Skip if no failed logins for their school
        except TelegramForbiddenError as e:
            pass


@dp.message(F.text == 'login')
async def logins_all(message: Message):
    await message.answer(text='Sending...')
    await send_daily_update()


@dp.message(F.text == 'send')
async def send_all_users(message: Message, state: FSMContext):
    await message.answer('nima jonatsangiz ham jonating')
    await state.set_state(Send.starr)


@dp.message(Send.starr)
async def starr(message: Message, state: FSMContext):
    users = await get_users_all()  # Get the list of users
    if not users:
        await message.answer("No users found.")
        await state.clear()
        return

    for user_id in users:
        if message.text:
            await bot.send_message(text=message.text, chat_id=user_id)
        elif message.photo:
            await bot.send_photo(caption=message.text, chat_id=user_id, photo=message.photo[-1].file_id)
        elif message.sticker:
            for i in range(740, 810):
                print(i, user_id)
                await bot.send_sticker(chat_id=user_id, sticker=message.sticker.file_id)
        elif message.video:
            await bot.send_video(video=message.video[-1].file_id, chat_id=user_id)
        elif message.audio:
            await bot.send_audio(audio=message.audio[-1].file_id, chat_id=user_id)

    await state.clear()  # Clear the state after sending the messages to all users
    await message.answer("Message sent to all users.")


@dp.message(F.text == "clear")
async def clear(message: Message):
    chat_id = message.chat.id
    for i in range(0, 700, 100):  # Increase range in steps of 100
        message_ids = list(range(message.message_id - 100 + i, message.message_id - i))
        try:
            await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
        except Exception as e:
            break


@dp.message(F.text == "users")
async def users(message: Message):
    admin = await get_admin(message.from_user.id)
    if admin:
        text1 = f"{await get_users_all()}"
        await message.answer(text=text1, parse_mode="Markdown")


async def test_bot():
    try:
        await bot.send_message(chat_id=6588631008, text="Hello, this is a test!")
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")


async def main2():
    scheduler.add_job(
        send_daily_update,
        trigger="cron",
        hour=8,
        minute=0,
        timezone=UZBEKISTAN_TZ,
    )
    await init()
    scheduler.start()
    # keep_alive()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main2())
    except KeyboardInterrupt:
        print('Goodbye')
