import random
import asyncio

from dotenv import dotenv_values

from pyrogram import Client, filters, errors, idle
from pyrogram.handlers import MessageHandler

from loguru import logger
import sys

from gpt3 import Gpt3


class PyrogramClient(Client):
    def __init__(self):

        super().__init__(
            name=config["NAME"],
            phone_number=config["PHONE_NUMBER"],
            api_id=config["API_ID"],
            api_hash=config["API_HASH"]
        )


class ChatexUtils(PyrogramClient):
    def __init__(self):
        super().__init__()

        self.channels = None

    def add_handling_function(self, func):
        chats_id = [channel["chat_id"] for channel in self.channels]
        self.add_handler(MessageHandler(func, filters.chat(chats_id)))

    @staticmethod
    def is_msg_from_channel(message, linked_channel_id):
        return message.sender_chat and message.sender_chat.id == linked_channel_id

    def get_group_by_chat_id(self, chat_id):
        return next((g for g in self.channels if g["chat_id"] == chat_id), {})


class MsgHelper:
    def __init__(self):
        self.message = None

    @staticmethod
    def get_random_chosen(from_, to):
        return random.choices([True, False], [from_, to])[0]

    @staticmethod
    async def wait(from_: float = 10, to: float = 60):
        await asyncio.sleep(random.uniform(from_, to))

    async def handle_sending(self, function, param):
        for _ in range(3):
            try:
                await getattr(self.message, function)(param)
            except (errors.exceptions.flood_420.SlowmodeWait, errors.exceptions.flood_420.FloodWait) as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.error(f'error: {e} | channel: {self.message.chat.title} | params: {param}')
                await self.wait(5, 9)
            else:
                msg = ""
                if self.message.text is not None:
                    msg = self.message.text.replace('\n', '')[:30]
                logger.success(f"Replied to msg \"{msg}...\" "
                               f"of channel \"{self.message.chat.title}\" with {param}")
                return True


class PostCommenter(MsgHelper):
    def __init__(self, message):
        super().__init__()
        self.message = message

    async def reply_to_post_with_text(self, post_to_reply):
        # logger.info("Enter reply_to_post_with_text func!")

        await PostCommenter.wait(float(config["DELAY_FROM"]), float(config["DELAY_TO"]))
        await self.reply_with_text(post_to_reply)

    async def reply_with_text(self, post_to_reply):
        comment = await PostCommenter.create_comment(post_to_reply)

        await self.handle_sending("reply_text", comment)

    @staticmethod
    async def create_comment(post_text):
        question = f"""
            Post: {post_text}
            Prompt to this post: {config["PROMPT"]}
            Your answer on prompt:
        """
        answer = Gpt3.ask(question, temperature=1, top_p=0.5,  presence_penalty=0.5)

        return answer


class Chatex(ChatexUtils):
    def __init__(self):
        super().__init__()

        self.channels = None

    async def starting(self):
        logger.info("Starting...")
        self.channels = await self.get_channels()

        self.new_msg_waiter()
        await self.start()
        await idle()

    async def get_channels(self):
        channels_list = file_to_list("donors.txt")

        channels = []

        async with self:
            for channel_id in channels_list:
                channel_id = int(channel_id)
                chat = await self.get_chat(channel_id)
                channels.append({"id": channel_id, "chat_id": chat.linked_chat.id})

        return channels

    def new_msg_waiter(self):
        self.add_handling_function(self.define_action)

    async def define_action(self, _, message):
        message_text = message.text or ""
        channel = self.get_group_by_chat_id(message.chat.id)

        if not Chatex.is_msg_from_channel(message, channel["id"]) \
                and not message.mentioned:
            return

        await PostCommenter(message).reply_to_post_with_text(message_text)


def file_to_list(
        filename: str
):
    with open(filename, 'r+') as f:
        return list(filter(bool, f.read().splitlines()))


async def main():
    logger.remove(0)
    logger.add(sys.stdout, colorize=True,
               format="<white>{time:HH:mm:ss.SSS}</white> <blue>{level}</blue> <level>{message}</level>")
    logger.add("out.log", format="<green>{time:HH:mm:ss.SSS}</green> <blue>{level}</blue> <level>{message}</level>")

    Gpt3.set_api_key(config["OPENAI_API_KEY"])

    chatex = Chatex()
    await chatex.starting()


if __name__ == "__main__":
    config = dotenv_values()

    asyncio.run(main())
