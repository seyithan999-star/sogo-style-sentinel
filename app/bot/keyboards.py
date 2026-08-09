from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def feedback_keyboard(product_id: str) -> InlineKeyboardMarkup:
    def cb(action: str) -> str:
        return f"fb:{action}:{product_id}"

    rows = [
        [
            InlineKeyboardButton(text="❤️ Çok Beğendim", callback_data=cb("love")),
            InlineKeyboardButton(text="👍 Beğendim", callback_data=cb("like")),
        ],
        [
            InlineKeyboardButton(text="⭐ Favori", callback_data=cb("favorite")),
            InlineKeyboardButton(text="💾 Kaydet", callback_data=cb("save")),
        ],
        [
            InlineKeyboardButton(text="👎 Beğenmedim", callback_data=cb("dislike")),
            InlineKeyboardButton(text="🚫 Gösterme", callback_data=cb("hide")),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
