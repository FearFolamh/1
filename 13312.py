#import os
#from background import keep_alive  #импорт функции для поддержки работоспособности
#import pip
#from telegram import Update, ChatAdministratorRights, ChatPermissions
#from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
#from bd import PermissionDatabase
#from telegram.error import BadRequest
#import json
#import asyncio
#from background import keep_alive
#import requests
#import time
#import threading

import os
import threading
import time
import requests
from telegram import Update, ChatAdministratorRights, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from telegram.error import BadRequest
from flask import Flask
from bd import PermissionDatabase
#pip.main(['install', 'python-telegram-bot'])
#import telebot  # Moved import to the top of the file

BOT_TOKEN = '7585696521:AAESIUWXERzzFaCS3gNaF-xtuAaJCD42BaY'
TARGET_USER_ID = 347884248
GROUP_ID_FILE = 'group_ids.txt'
USER_ID_FILE = 'user_ids.txt'
GROUP_ID = 0

db = PermissionDatabase()
user_data = {}
welcome_thread_id = db.get_welcome_thread_message()

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is alive!"


def save_group_id(group_id: int):
    global GROUP_ID
    db.set_group_id(group_id)
    GROUP_ID = group_id
    # if os.path.exists(GROUP_ID_FILE):
    #     with open(GROUP_ID_FILE, 'r') as f:
    #         group_ids = f.readlines()
    # else:
    #     group_ids = []
    # group_ids = [id.strip() for id in group_ids]
    # if str(group_id) not in group_ids:
    #     group_ids.append(str(group_id))
    #     with open(GROUP_ID_FILE, 'a') as f:
    #         f.write(f"{group_id}\n")


def save_user_id(members: list):
    db.update_users(members)


def save_all_group_members(group_id: int, bot):
    try:
        members = bot.get_chat_administrators(group_id)
        members_list = []
        for member in members:
            #bot.send_message(chat_id=TARGET_USER_ID, text=f"{member}")
            user_id = member.user.id
            position = member.custom_title
            name = member.user.name
            username = member.user.username
            members_list.append({
                'user_id': user_id,
                'name': name,
                'username': username,
                'position': position
            })
        #bot.send_message(
        #chat_id=TARGET_USER_ID,
        #text=f"save_all_group_members >> Members: {members_list}")
        save_user_id(members_list)
    except Exception as e:
        print(f"Error while fetching members: {e}")


def get_thread_id(update: Update, context: CallbackContext):
    global welcome_thread_id
    if update.message.is_topic_message:  # Проверка, является ли сообщение частью ветки
        welcome_thread_id = update.message.message_thread_id
        db.set_welcome_thread_message(welcome_thread_id)
        context.bot.send_message(
            chat_id=GROUP_ID,
            text=
            f"Thread {update.message.reply_to_message.forum_topic_created.name}: "
            f"{welcome_thread_id} sets as Welcome-thread.")
    else:
        update.message.reply_text("Это сообщение не из ветки.")


def get_all_users_id(update: Update, context: CallbackContext):
    global GROUP_ID
    save_all_group_members(GROUP_ID, context.bot)
    #context.bot.send_message(chat_id=TARGET_USER_ID,
    #text=f"All admin-users saved.")


def new_chat_member(update: Update, context: CallbackContext) -> None:
    global welcome_thread_id
    new_members = update.message.new_chat_members
    if new_members:
        for new_member in new_members:
            group_id = update.message.chat.id
            name = new_member.name
            username = new_member.username
            if new_member.id == context.bot.id:
                save_group_id(group_id)
                save_all_group_members(group_id, context.bot)
            else:
                context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=new_member.id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                    ))

                try:
                    context.bot.send_message(
                        chat_id=group_id,
                        text=
                        f"Привет, {username or name}. Для регистрации введи команду /role <ваш ник в гусях>.",
                        message_thread_id=welcome_thread_id)
                except Exception as e:
                    print(
                        f"Не удалось отправить сообщение в ветку {welcome_thread_id}: {e}"
                    )

                user_data[new_member.id] = {
                    'user_id': new_member.id,
                    'position': ''
                }
                save_user_id([{
                    'user_id': new_member.id,
                    'name': name,
                    'username': username,
                    'position': ''
                }])


def assign_role(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Использование: /role <ваша роль в гусях>")
        return
    role = context.args[0].lower()
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    set_admin_rights(update, context, user_id, role)
    update.message.reply_text(
        f"Роль '{role}' успешно назначена для {update.message.from_user.first_name}."
    )
    user_data.pop(user_id, None)
    save_all_group_members(chat_id, context.bot)


def set_admin_rights(update: Update, context: CallbackContext, user_id: int,
                     role: str):
    admin_rights = ChatAdministratorRights(
        can_pin_messages=True,
        is_anonymous=False,
        can_manage_chat=False,
        can_post_messages=False,
        can_edit_messages=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_manage_video_chats=False,
    )
    try:
        # Проверяем, что бот имеет права администратора
        bot_member = context.bot.get_chat_member(GROUP_ID, context.bot.id)
        if not bot_member.can_promote_members:
            update.message.reply_text(
                "Бот должен иметь право назначать администраторов.")
            return

        context.bot.promote_chat_member(
            chat_id=GROUP_ID,
            user_id=user_id,
            can_pin_messages=admin_rights.can_pin_messages,
            is_anonymous=admin_rights.is_anonymous,
            can_manage_chat=admin_rights.can_manage_chat,
            can_post_messages=admin_rights.can_post_messages,
            can_edit_messages=admin_rights.can_edit_messages,
            can_delete_messages=admin_rights.can_delete_messages,
            can_restrict_members=admin_rights.can_restrict_members,
            can_promote_members=admin_rights.can_promote_members,
            can_change_info=admin_rights.can_change_info,
            can_invite_users=admin_rights.can_invite_users,
            can_manage_video_chats=admin_rights.can_manage_video_chats,
        )
        context.bot.set_chat_administrator_custom_title(chat_id=GROUP_ID,
                                                        user_id=user_id,
                                                        custom_title=role)
    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")


def configure_admin_rights(update: Update, context: CallbackContext):
    users = db.get_all_users()
    for user_id, role in users:
        set_admin_rights(update, context, user_id, role)


def handle_message(update, context):
    user = update.message.from_user
    if user.id in user_data.keys():
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=update.message.message_id)
            print(
                f"Message from user {user.id} {user.name} deleted (wrong thread)."
            )
        except Exception as e:
            print(f"Failed to delete message from user {user.id}: {e}")


def main():
    global welcome_thread_id
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.new_chat_members,
                       new_chat_member))
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_handler(CommandHandler("set_welcome_thread", get_thread_id))
    dispatcher.add_handler(
        CommandHandler("save_all_users_roles", get_all_users_id))
    dispatcher.add_handler(
        CommandHandler("configure_admin_rights", configure_admin_rights))
    dispatcher.add_handler(CommandHandler("role", assign_role))
    global GROUP_ID
    GROUP_ID = db.get_group_id()
    updater.start_polling()
    updater.idle()


def ping():
    while True:
        try:
            requests.get(
                "https://110f15b8-d15d-43a1-96c8-e017f546b001-00-1myaitagx13xm.kirk.replit.dev:8080/"
            )  # Запрос к своему проекту
            requests.get("https://google.com")  # Дополнительный запрос
        except Exception as e:
            print(f"Ping error: {e}")
        time.sleep(300)  # Каждые 5 минут


if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=app.run,
                                    kwargs={
                                        'host': '0.0.0.0',
                                        'port': 8080
                                    })
    flask_thread.start()

    # Запуск ping-запросов
    ping_thread = threading.Thread(target=ping)
    ping_thread.start()

    # Запуск бота
    main()
