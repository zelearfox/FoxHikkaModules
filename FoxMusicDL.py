# meta developer: ZelearFox
# scope: hikka_only
# scope: hikka_min 1.3.0

from telethon.tl.types import Message
from .. import loader, utils


@loader.tds
class MusicDLMod(loader.Module):
    """Download music with fox style!"""

    strings = {
        "name": "FoxMusicDL",
        "args": "🦊 <b>Fox needs to know what song to find! Provide a title.</b>",
        "loading": "🦊 <b>Fox is searching for music by request:</b> <code>{}</code>\n\n<i>Please wait while fox digs through the forest...</i>",
        "404": "🦊 <b>Fox couldn't find</b> <code>{}</code><b>. Maybe try another song?</b>",
        "error": "🦊 <b>Fox encountered a problem while searching:</b> <code>{}</code>",
        "success": "🦊 <b>Fox found the song!</b> {}",
    }

    strings_ru = {
        "args": "🦊 <b>Лису нужно знать, какую песню искать! Укажите название.</b>",
        "loading": "🦊 <b>Лис ищет музыку по запросу:</b> <code>{}</code>\n\n<i>Пожалуйста, подождите, пока лис обыщет весь лес...</i>",
        "404": "🦊 <b>Лис не смог найти</b> <code>{}</code><b>. Может, попробуешь другую песню?</b>",
        "error": "🦊 <b>Лис столкнулся с проблемой при поиске:</b> <code>{}</code>",
        "success": "🦊 <b>Лис нашёл песню!</b>",
    }

    async def client_ready(self, *_):
        try:
            self.musicdl = await self.import_lib(
                "https://foxmodules.zlr.su/libs/musicdl.py",
                suspend_on_error=True,
            )
        except Exception as e:
            self.musicdl = None
            raise loader.LoadError(f"🦊 <b>Fox couldn't load music library:</b> <code>{e}</code>")

    @loader.command(ru_doc="<название> - Скачать песню с помощью лиса")
    async def fmdl(self, message: Message):
        """<name> - Download track with fox power"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        message = await utils.answer(message, self.strings("loading").format(args))
        
        try:
            if not self.musicdl:
                await utils.answer(message, self.strings("error").format("Music library not loaded"))
                return

            result = await self.musicdl.dl(args, only_document=True)

            if not result:
                await utils.answer(message, self.strings("404").format(args))
                return

            await self._client.send_file(
                message.peer_id,
                result,
                caption=self.strings("success"),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
            
            if message.out:
                await message.delete()
                
        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))
            if message.out:
                await message.delete()