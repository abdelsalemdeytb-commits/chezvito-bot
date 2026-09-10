import os
from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


WHATSAPP_NUMBER = "33780836905"
DELIVERY_FEE = 5

PRODUCTS = {
    "p1": {"name": "Produit 1", "price": 10},
    "p2": {"name": "Produit 2", "price": 15},
    "p3": {"name": "Produit 3", "price": 8},
}


def money(amount):
    return f"{amount:.2f}".replace(".", ",") + " €"


def menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"➕ {p['name']} — {money(p['price'])}",
                callback_data=f"add:{pid}"
            )
        ]
        for pid, p in PRODUCTS.items()
    ] + [
        [InlineKeyboardButton("🧾 Voir ma commande", callback_data="cart")],
        [InlineKeyboardButton("🗑️ Vider la commande", callback_data="clear")]
    ])


def get_cart(context):
    return context.user_data.setdefault("cart", {})


def cart_text(cart):
    if not cart:
        return "🛒 Votre panier est vide."

    lines = ["🛒 *Votre commande*"]
    subtotal = 0

    for pid, quantity in cart.items():
        product = PRODUCTS[pid]
        amount = product["price"] * quantity
        subtotal += amount

        lines.append(
            f"• {product['name']} × {quantity} = {money(amount)}"
        )

    total = subtotal + DELIVERY_FEE

    lines.extend([
        "",
        f"Sous-total : {money(subtotal)}",
        f"Livraison : {money(DELIVERY_FEE)}",
        f"*Total : {money(total)}*"
    ])

    return "\n".join(lines)


def whatsapp_url(cart):
    subtotal = sum(
        PRODUCTS[pid]["price"] * quantity
        for pid, quantity in cart.items()
    )

    total = subtotal + DELIVERY_FEE

    products = []

    for pid, quantity in cart.items():
        products.append(
            f"- {PRODUCTS[pid]['name']} x{quantity}"
        )

    message = (
        "Bonjour ChezVito 👋\n\n"
        "Je souhaite passer cette commande :\n"
        + "\n".join(products)
        + f"\n\nSous-total : {money(subtotal)}"
        + f"\nLivraison : {money(DELIVERY_FEE)}"
        + f"\nTotal : {money(total)}"
    )

    return (
        f"https://wa.me/{WHATSAPP_NUMBER}"
        f"?text={quote(message)}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = {}

    await update.message.reply_text(
        "👋 Bienvenue chez *ChezVito* !\n\n"
        "Choisissez vos produits :",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ *Menu ChezVito*\n\n"
        "Choisissez un produit :",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart = get_cart(context)

    if query.data.startswith("add:"):
        product_id = query.data.split(":")[1]

        cart[product_id] = cart.get(product_id, 0) + 1

        await query.edit_message_text(
            f"✅ {PRODUCTS[product_id]['name']} ajouté.\n\n"
            + cart_text(cart),
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

    elif query.data == "cart":
        buttons = []

        if cart:
            buttons.append([
                InlineKeyboardButton(
                    "📲 Commander sur WhatsApp",
                    url=whatsapp_url(cart)
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "🛍️ Continuer mes achats",
                callback_data="back"
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                "🗑️ Vider la commande",
                callback_data="clear"
            )
        ])

        await query.edit_message_text(
            cart_text(cart),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "clear":
        context.user_data["cart"] = {}

        await query.edit_message_text(
            "🗑️ Commande vidée.\n\n"
            "Choisissez vos produits :",
            reply_markup=menu_keyboard()
        )

    elif query.data == "back":
        await query.edit_message_text(
            "🛍️ *Menu ChezVito*\n\n"
            "Choisissez un produit :",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "La variable TELEGRAM_BOT_TOKEN est absente."
        )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
