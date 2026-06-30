import logging
import asyncio
from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN

# ⚙️ Logging sozlamasi
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Xotira omborlari
user_referrals = {}       # {user_id: target_id} yoki {user_id: (target_id, reply_to_id)}
message_relations = {}    # {sent_message_id_in_target_chat: (original_sender_id, original_message_id)}
user_stats = {}           # {user_id: {"received": 0, "sent": 0}}
instruction_messages = {} # {user_id: instruction_message_id} -> Yo'riqnomalarni o'chirish uchun
sent_messages_map = {}    # {confirm_message_id_in_sender_chat: (target_chat_id, sent_message_id_in_target_chat, original_sender_msg_id)}


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    args = message.text.split()
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={user_id}"

    if user_id not in user_stats:
        user_stats[user_id] = {"received": 0, "sent": 0}

    clean_text = (
        f"<b>Sizning shaxsiy anonim havolangiz! 👇</b>\n"
        f"<blockquote>{share_link}</blockquote>\n\n"
        f"Ushbu havolani nusxalab, Instagram, Telegram profil biongizga yoki Story'larga joylashtiring!"
    )

    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == user_id:
            await message.answer(
                f"⚠️ {html.italic('Oʻz-oʻzingizga anonim xabar yubora olmaysiz.')}",
                parse_mode="HTML"
            )
            return

        user_referrals[user_id] = referrer_id
        msg = await message.answer(
            "💬 Do'stingizga yubormoqchi bo'lgan maxfiy xabaringizni yozing "
            "(Matn, rasm, video yoki ovozli xabar)..."
        )
        instruction_messages[user_id] = msg.message_id
        return

    kb = InlineKeyboardBuilder()
    kb.button(
        text="🔗 Havolani ulashish",
        url=f"https://t.me/share/url?url={share_link}"
    )
    kb.button(text="📊 Mening statistikalarim", callback_data="my_stats")
    kb.adjust(1)

    await message.answer(clean_text, parse_mode="HTML", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "my_stats")
async def show_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = user_stats.get(user_id, {"received": 0, "sent": 0})

    await callback.answer("Statistika yuklandi!")
    await callback.message.answer(
        f"📊 <b>Sizning hisobingiz statistikasi:</b>\n\n"
        f"• Qabul qilingan xatlar: {stats['received']} ta\n"
        f"• Yuborilgan anonim xatlar: {stats['sent']} ta",
        parse_mode="HTML"
    )


async def send_anonymous_media(target_id: int, message: Message, reply_to_id: int = None) -> Message:
    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖊 Javob qaytarish", callback_data=f"reply_{message.from_user.id}")]
    ])

    caption_text = "<i>💬 Sizga xabar keldi!</i>"
    if message.caption:
        caption_text += f"\n\n{message.caption}"

    if message.text:
        return await bot.send_message(
            chat_id=target_id,
            text=f"<i>💬 Sizga xabar keldi! </i>\n\n{message.text}",
            reply_markup=reply_kb,
            reply_to_message_id=reply_to_id,
            parse_mode="HTML"
        )
    elif message.photo:
        return await bot.send_photo(
            chat_id=target_id, photo=message.photo[-1].file_id, caption=caption_text,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id, parse_mode="HTML"
        )
    elif message.video:
        return await bot.send_video(
            chat_id=target_id, video=message.video.file_id, caption=caption_text,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id, parse_mode="HTML"
        )
    elif message.voice:
        return await bot.send_voice(
            chat_id=target_id, voice=message.voice.file_id,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id
        )
    elif message.video_note:
        return await bot.send_video_note(
            chat_id=target_id, video_note=message.video_note.file_id,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id
        )
    elif message.sticker:
        return await bot.send_sticker(
            chat_id=target_id, sticker=message.sticker.file_id,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id
        )
    else:
        return await bot.send_document(
            chat_id=target_id, document=message.document.file_id, caption=caption_text,
            reply_markup=reply_kb, reply_to_message_id=reply_to_id, parse_mode="HTML"
        )


@dp.message()
async def process_anonymous_message(message: Message):
    user_id = message.from_user.id
    target_id = None
    reply_to_msg_id = None

    # Yo'riqnomani avtomatik o'chirish
    if user_id in instruction_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=instruction_messages[user_id])
            del instruction_messages[user_id]
        except Exception:
            pass

    if user_id in user_referrals:
        res = user_referrals[user_id]
        target_id, reply_to_msg_id = res if isinstance(res, tuple) else (res, None)
    elif message.reply_to_message:
        reply_id = message.reply_to_message.message_id
        if reply_id in message_relations:
            target_id, reply_to_msg_id = message_relations[reply_id]

    if target_id:
        try:
            sent_msg = await send_anonymous_media(target_id, message, reply_to_msg_id)
            message_relations[sent_msg.message_id] = (user_id, message.message_id)

            # Statistika yangilash
            if user_id not in user_stats:
                user_stats[user_id] = {"received": 0, "sent": 0}
            if target_id not in user_stats:
                user_stats[target_id] = {"received": 0, "sent": 0}
            user_stats[user_id]["sent"] += 1
            user_stats[target_id]["received"] += 1

            confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✍️ Yana bitta yuborish",
                    callback_data=f"again_{target_id}_{reply_to_msg_id if reply_to_msg_id else 0}"
                )],
                [InlineKeyboardButton(text="🗑 Xabarni o'chirish", callback_data="cancel_msg")]
            ])

            confirm_msg = await message.reply(
                text="✔️ Xabar yuborildi, javob kuting!",
                reply_markup=confirm_kb
            )

            sent_messages_map[confirm_msg.message_id] = (target_id, sent_msg.message_id, message.message_id)

            if user_id in user_referrals:
                del user_referrals[user_id]

        except Exception as e:
            logging.error(f"Xatolik: {e}")
            await message.answer("❌ Xabarni yetkazib bo'lmadi. Foydalanuvchi botni bloklagan bo'lishi mumkin.")
    else:
        bot_info = await bot.get_me()
        share_link = f"https://t.me/{bot_info.username}?start={user_id}"
        await message.answer(
            f"💡 Anonim xabar yuborish uchun do'stingizning havolasidan kiring.\n\n"
            f"O'zingiz xabar olishingiz uchun havolangiz: 👇\n<blockquote>{share_link}</blockquote>",
            parse_mode="HTML"
        )


@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    original_sender_id = int(callback.data.split("_")[1])
    current_msg_id = callback.message.message_id

    actual_reply_id = None
    if current_msg_id in message_relations:
        actual_reply_id = message_relations[current_msg_id][1]

    user_referrals[callback.from_user.id] = (original_sender_id, actual_reply_id)

    await callback.answer()
    msg = await callback.message.answer("💬 Javobingizni yozing...")
    instruction_messages[user_id] = msg.message_id


@dp.callback_query(F.data.startswith("again_"))
async def again_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    data_parts = callback.data.split("_")
    target_id = int(data_parts[1])
    reply_to_msg_id = int(data_parts[2])
    actual_reply_id = None if reply_to_msg_id == 0 else reply_to_msg_id

    user_referrals[user_id] = (target_id, actual_reply_id)

    await callback.answer()
    msg = await callback.message.answer("💬 Navbatdagi anonim xabaringizni yozib yuborishingiz mumkin...")
    instruction_messages[user_id] = msg.message_id


@dp.callback_query(F.data == "cancel_msg")
async def cancel_message_handler(callback: CallbackQuery):
    confirm_msg_id = callback.message.message_id
    sender_chat_id = callback.from_user.id

    if confirm_msg_id in sent_messages_map:
        target_chat_id, sent_msg_id, original_sender_msg_id = sent_messages_map[confirm_msg_id]

        # 1. Qabul qiluvchidan xabarni o'chirish
        try:
            await bot.delete_message(chat_id=target_chat_id, message_id=sent_msg_id)
        except Exception:
            pass

        # 2. Yuboruvchining o'zidan ham xabarini o'chirish
        try:
            await bot.delete_message(chat_id=sender_chat_id, message_id=original_sender_msg_id)
        except Exception:
            pass

        if sent_msg_id in message_relations:
            del message_relations[sent_msg_id]

        del sent_messages_map[confirm_msg_id]

        # 3. Tasdiqlash xabarini o'chirish
        try:
            await callback.message.delete()
            await callback.answer(
                "🗑 Xabar har ikki tomondan (sizdan ham, undan ham) butunlay o'chirildi!",
                show_alert=True
            )
        except Exception:
            pass
    else:
        await callback.answer("⚠️ Xabar allaqachon o'chirilgan yoki muddati o'tgan.", show_alert=True)


async def main():
    print("✅ Anonim Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
