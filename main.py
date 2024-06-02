import logging
import os

from decouple import config
from swibots import (
    Client,
    BotCommand,
    BotContext,
    InlineKeyboardButton,
    InlineMarkup,
    regexp,
    CallbackQueryEvent,
    AppBar,
    AppPage,
    Text,
    BottomBar,
    BottomBarTile,
    StickyHeader,
    TextInput,
    Dropdown,
    ListItem,
    ListTile,
    ListView,
    Icon,
)

from database import (
    add_user,
    get_domain,
    get_username,
    get_users,
    set_domain,
    set_username,
)
from helpers import get_domains, get_mail_data, get_mails, remove_html_tags
from icons import Icons

file = "temp-mail-bot.log"

if os.path.exists(file):
    os.remove(file)

logging.basicConfig(
    format="%(asctime)s | %(name)s [%(levelname)s] : %(message)s",
    level=logging.INFO,
    datefmt="%m/%d/%Y, %H:%M:%S",
    handlers=[logging.FileHandler(file, encoding="utf-8"), logging.StreamHandler()],
)
logs = logging.getLogger("botzhub")

try:
    BOT_TOKEN = config("BOT_TOKEN")
    FSUB_COMMUNITY_ID = config("FSUB_COMMUNITY_ID")
    OWNER_ID = config("OWNER_ID", cast=int)
except Exception as e:
    logs.error(e)
    exit(1)

bot = Client(
    token=BOT_TOKEN,
    bot_description="Temporary Mail Bot!",
    is_app=False,
    auto_update_bot=True,
    app_bar=AppBar(
        "TempMail",
        left_icon=Icon(
            "https://img.icons8.com/?size=100&id=80728&format=png&color=000000"
        ),
    ),
)

bot.set_bot_commands(
    [
        BotCommand("start", "Start the bot."),
        BotCommand("logs", "[ADMIN] Get bot logs."),
        BotCommand("stats", "[ADMIN] Get bot stats."),
    ]
)


@bot.on_command("start")
async def start_bot(ctx: BotContext):
    mem = await ctx.get_community_member(FSUB_COMMUNITY_ID, ctx.event.user.id)
    add_user(ctx.event.user.id)
    if not mem:
        await ctx.event.message.respond(
            "You are not a member of the community!",
            inline_markup=InlineMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Join Community",
                            url="https://iswitch.click/96885ff2-d76f-4f57-997e-5b4423730802/227234c1-4818-4571-ac84-2a081e99add8",
                        )
                    ]
                ]
            ),
        )
        return
    await ctx.event.message.respond(
        "Welcome to temporary mail bot.\n\nClick the button below to run the minapp!",
        inline_markup=InlineMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Open MiniApp",
                        callback_data="home",
                    )
                ]
            ]
        ),
    )


@bot.on_command("logs")
async def get_logs(ctx: BotContext):
    if ctx.event.user.id != OWNER_ID:
        return await ctx.event.message.respond("Nice try!")
    xx = await ctx.event.message.respond("Sending logs...")
    await bot.send_document(
        user_id=ctx.event.user.id, document="ytdl-bot.log", caption="Logs"
    )
    await xx.delete()


def generate_bottom_bar(page: str):
    return BottomBar(
        options=[
            BottomBarTile(
                "Home",
                selected=True if page == "home" else False,
                icon=Icons.Home.LIGHT,
                dark_icon=Icons.Home.DARK,
                selection_icon=Icons.Home.SELECTED,
                callback_data="home" if page != "home" else None,
            ),
            BottomBarTile(
                "Mails",
                selected=True if page == "mails" else False,
                icon=Icons.Mails.LIGHT,
                dark_icon=Icons.Mails.DARK,
                selection_icon=Icons.Mails.SELECTED,
                callback_data="mails" if page != "mails" else None,
            ),
            BottomBarTile(
                "Settings",
                selected=True if page == "settings" else False,
                icon=Icons.Settings.LIGHT,
                dark_icon=Icons.Settings.DARK,
                selection_icon=Icons.Settings.SELECTED,
                callback_data="settings" if page != "settings" else None,
            ),
        ]
    )


@bot.on_callback_query(regexp("^home$"))
async def open_main_miniapp(ctx: BotContext[CallbackQueryEvent]):
    await ctx.event.answer(
        callback=AppPage(
            components=[
                StickyHeader("Welcome!"),
                Text(
                    "This is a temporary mail generator. You can use this bot to generate temporary emails."
                ),
                Text(
                    f"Current Email: {get_username(ctx.event.action_by.id)}@{get_domain(ctx.event.action_by.id)}"
                ),
                Text(
                    "You can customize this email from the settings tab!", color="red"
                ),
            ],
            bottom_bar=generate_bottom_bar("home"),
        )
    )


def generate_mails_list(mails):
    mails_list = [
        ListTile(
            title="Welcome to @TempMail_bot!",
            title_extra="31-05-2024 00:00",
            description="From: me@xditya.me",
            callback_data="read_welcome_mail",
            thumb="https://img.icons8.com/?size=100&id=124428&format=png&color=228BE6",
        )
    ]
    for mail in mails:
        mails_list.append(
            ListTile(
                title=mail.get("subject", "No Subject"),
                title_extra=mail.get("date", "No Date"),
                description="From: " + mail.get("from", "No Sender"),
                callback_data=f"read_mail_{mail['id']}",
                thumb="https://img.icons8.com/?size=100&id=124428&format=png&color=228BE6",
            )
        )
    return mails_list


@bot.on_callback_query(regexp("^mails$"))
async def open_mails_miniapp(ctx: BotContext[CallbackQueryEvent]):
    mails, error = get_mails(
        f"{get_username(ctx.event.action_by.id)}@{get_domain(ctx.event.action_by.id)}"
    )
    if mails is None:
        return await ctx.event.answer(show_alert=True, text=error)
    mails_list = generate_mails_list(mails)
    await ctx.event.answer(
        callback=AppPage(
            components=[
                StickyHeader("Mails (click to refresh)", callback_data="mails"),
                ListView(
                    options=mails_list,
                ),
            ],
            bottom_bar=generate_bottom_bar("mails"),
        )
    )


@bot.on_callback_query(regexp("^settings$"))
async def open_settings_miniapp(ctx: BotContext[CallbackQueryEvent]):
    username = get_username(ctx.event.action_by.id)
    if not username:
        set_username(ctx.event.action_by.id, ctx.event.action_by.username)
        username = ctx.event.action_by.username
    domains = get_domains()

    def get_index():
        try:
            return domains.index(get_domain(ctx.event.action_by.id))
        except ValueError:
            return None

    await ctx.event.answer(
        callback=AppPage(
            components=[
                StickyHeader(text="Settings Page"),
                TextInput(
                    label="Username",
                    value=username,
                    placeholder="Enter new username",
                    callback_data="set_username",
                ),
                Text("Select a domain", opacity=0.8),
                Dropdown(
                    placeholder=get_domain(ctx.event.action_by.id) or "Select a domain",
                    options=[
                        ListItem(i, callback_data=f"set_domain_{i}") for i in domains
                    ],
                    selected=get_index(),
                ),
                Text("Note:\nChanging domain will reset your mailbox!", opacity=0.5),
            ],
            bottom_bar=generate_bottom_bar("settings"),
        )
    )


@bot.on_callback_query(regexp("^set_username$"))
async def on_username_change(ctx: BotContext[CallbackQueryEvent]):
    username = ctx.event.details.input_value
    set_username(ctx.event.action_by.id, username)


@bot.on_callback_query(regexp("^set_domain_(.*)$"))
async def on_set_domain_callback(ctx: BotContext[CallbackQueryEvent]):
    domain = ctx.event.callback_data.split("_")[-1]
    set_domain(ctx.event.action_by.id, domain)
    return await ctx.event.answer(show_alert=True, text="Domain set successfully!")


@bot.on_callback_query(regexp("^read_welcome_mail$"))
async def read_welcome_mail_callback(ctx: BotContext[CallbackQueryEvent]):
    username = get_username(ctx.event.action_by.id)
    domain = get_domain(ctx.event.action_by.id)
    return await ctx.event.answer(
        callback=AppPage(
            components=[
                StickyHeader("Back to Mails", callback_data="mails"),
                Text("From: me@xditya.me"),
                Text(f"To: {username}@{domain}"),
                Text("Date: 31-05-2024 00:00"),
                Text("Subject: Welcome to @TempMail_bot!"),
                Text(
                    f"Body:\nGreetings {ctx.event.action_by.name}!\nWelcome to @TempMail_bot, your one stop solution for temporary emails!\n\nGet random disposible emails right at your fingertips.\n\nA project by https://xditya.me :)"
                ),
            ],
            bottom_bar=generate_bottom_bar("mails"),
        )
    )


@bot.on_callback_query(regexp("^read_mail_(.*)$"))
async def read_mail_callback(ctx: BotContext[CallbackQueryEvent]):
    mail_id = ctx.event.callback_data.split("_")[-1]
    username = get_username(ctx.event.action_by.id)
    domain = get_domain(ctx.event.action_by.id)
    mail_data = get_mail_data(username, domain, mail_id)
    if not mail_data:
        return await ctx.event.answer(show_alert=True, text="Error reading mail!")

    # images = []
    # if mail_data.get("attachments") != []:
    #     for attachment in mail_data.get("attachments"):
    #         images.append(
    #             Image(
    #                 url=attachment.get("link"),
    #             )
    #         )
    body = mail_data.get("body", "No Body")
    body = remove_html_tags(body)
    return await ctx.event.answer(
        callback=AppPage(
            components=[
                StickyHeader("Back to Mails", callback_data="mails"),
                Text(f"From: {mail_data.get('from', 'No Sender')}"),
                Text(f"To: {username}@{domain}"),
                Text(f"Date: {mail_data.get('date', 'No Date')}"),
                Text(f"Subject: {mail_data.get('subject', 'No Subject')}"),
                Text(f"Body:\n{body}"),
            ],
            bottom_bar=generate_bottom_bar("mails"),
        )
    )


@bot.on_command("stats")
async def stats_cmd(ctx: BotContext):
    if ctx.event.user.id != OWNER_ID:
        return await ctx.event.message.respond("Nice try!")
    users = get_users()
    await ctx.event.message.respond(f"Total Users: {len(users)}")


bot.run()
