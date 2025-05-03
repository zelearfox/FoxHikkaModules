# meta developer: ZelearFox
# scope: hikka_only
# scope: hikka_min 1.3.0

from telethon.tl.types import Message
from .. import loader, utils
import requests
import time

@loader.tds
class FoxMinecraftMod(loader.Module):
    """Инструменты для Minecraft"""

    strings = {
        "name": "FoxMinecraft"
    }

    @loader.command(
        ru_doc="[адрес] - Получить информацию о Minecraft Java сервере",
    )
    async def mcstat(self, message: Message):
        """Получить статус майнкрафт сервера"""

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, '❌ Вы не указали адрес сервера')
            return
        adress = args.split(' ')[0]

        await utils.answer(message, '⏳ Получаю информацию...')

        start_time = time.time()
        resp = requests.get(f'https://api.mcstatus.io/v2/status/java/{adress}')

        if resp.ok == True:
            server = resp.json()
            out = [
                    f"<a href='https://api.mcstatus.io/v2/widget/java/{adress}?rounded=false&rand={utils.rand(10)}'>🖥</a> Сервер Minecraft Java Edition"
                ]
            
            if server['online'] == True:
                out.append("├ 📡 Статус: 🟢 Онлайн")
            else:
                out.append("├ 📡 Статус: 🔴 Оффлайн")
            
            out.append(f"├ 🛡 Хост: {server['host']}:{server['port']}")

            if server['ip_address'] != None:
                out.append(f"├ 🔌 IP: {server['ip_address']}")

            if server['srv_record'] != None:
                out.append(f"├ 📝 SRV: {server['srv_record']['host']}:{server['srv_record']['port']}")
            
            if 'version' in server:
                out.append(f"├ 📌 Версия: {server['version']['name_clean']}")
                out.append(f"├ ⚙️ Протокол: {server['version']['protocol']}")

            
            if 'players' in server:
                out.append(f"├ 👥 Игроки: {server['players']['online']}/{server['players']['max']}")
            
            end_time = time.time()
            out.append(f"└ ⏰ Время на запрос: {int((end_time - start_time) * 1000)} мс.")
            return await utils.answer(
                message,
                '\n'.join(out),
                link_preview=True
            )
        else:
            return await utils.answer(message, "❌ Запрашиваемый сервер недоступен")
    
    @loader.command(
        ru_doc="[адрес] - Получить информацию о Minecraft Bedrock сервере",
    )
    async def mcbestat(self, message: Message):
        """Получить статус Minecraft Bedrock сервера"""

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, '❌ Вы не указали адрес сервера')
            return
        adress = args.split(' ')[0]

        await utils.answer(message, '⏳ Получаю информацию...')

        start_time = time.time()
        resp = requests.get(f'https://api.mcstatus.io/v2/status/bedrock/{adress}')

        if resp.ok == True:
            server = resp.json()
            out = [
                    "🖥 Сервер Minecraft Bedrock Edition"
                ]
            
            if server['online'] == True:
                out.append("├ 📡 Статус: 🟢 Онлайн")
            else:
                out.append("├ 📡 Статус: 🔴 Оффлайн")
            
            out.append(f"├ 🛡 Хост: {server['host']}:{server['port']}")

            if server['ip_address'] != None:
                out.append(f"├ 🔌 IP: {server['ip_address']}")

            if 'server_id' in server:
                out.append(f"├ 🪪 ID: {server['server_id']}")
            
            if 'version' in server:
                out.append(f"├ 📌 Версия: {server['version']['name']}")
                out.append(f"├ ⚙️ Протокол: {server['version']['protocol']}")
            
            if 'edition' in server:
                out.append(f"├ 🔗 Выпуск: {server['edition']}")
            
            if 'players' in server:
                out.append(f"├ 👥 Игроки: {server['players']['online']}/{server['players']['max']}")

            if 'gamemode' in server:
                out.append(f"├ 🛠 Режим игры: {server['gamemode']}")
            
            end_time = time.time()
            out.append(f"└ ⏰ Время на запрос: {int((end_time - start_time) * 1000)} мс.")
            return await utils.answer(message, '\n'.join(out))
        else:
            return await utils.answer(message, "❌ Запрашиваемый сервер недоступен")
    
    @loader.command(
        ru_doc="[ник] - Получить информацию о Игроке",
    )
    async def mcplayer(self, message: Message):
        """Получить информацию об игроке"""

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, '❌ Вы не указали ник игрока')
            return
        nickname = args.split(' ')[0]

        await utils.answer(message, '⏳ Получаю информацию...')
    
        start_time = time.time()
        resp = requests.get(f"https://api.minetools.eu/uuid/{nickname}")

        if resp.ok:
            data = resp.json()
            if data['status'] == 'OK':
                resp2 = requests.get(f"https://api.minetools.eu/profile/{data['id']}")
                if resp2.ok:
                    data2 = resp2.json()
                    if 'status' not in data2:
                        player = data2['decoded']

                        out = [
                            "👤 Информация об игроке"
                        ]

                        out.append(f"├ 🔖 Ник: {player['profileName']}")

                        out.append(f"├ 🪪 ID: {player['profileId']}")

                        if 'textures' in player:
                            if 'SKIN' in player['textures']:
                                out.append(f"├ 💎 Скин: <a href='{player['textures']['SKIN']['url']}'>ССЫЛКА</a>")
                            if 'CAPE' in player['textures']:
                                out.append(f"├ 📍 Плащ: <a href='{player['textures']['CAPE']['url']}'>ССЫЛКА</a>")

                        end_time = time.time()
                        out.append(f'└ ⏰ Время на запрос: {int((end_time - start_time) * 1000)} мс.')
                        return await utils.answer(message, '\n'.join(out))
                    else:
                        return await utils.answer(message, "❌ Запрашиваемый игрок не неайден")
                else:
                    return await utils.answer(message, "❌ Запрашиваемый игрок не неайден")
            else:
                return await utils.answer(message, "❌ Запрашиваемый игрок не неайден")
        else:
            return await utils.answer(message, "❌ Запрашиваемый игрок не неайден")
