# meta developer: ZelearFox

# scope: hikka_only
# scope: hikka_min 1.1.0
# requires: python-whois requests dnspython
# version: 1.0.0

from .. import loader, utils
import socket
import whois
import requests
import time
import dns.resolver
import dns.asyncresolver
from datetime import datetime

@loader.tds
class WhoisMod(loader.Module):
    """Модуль whois"""
    strings = {
        "name": "Whois",
        "domain_free": "Домен свободен для регистрации!",
        "ip_not_exists": "Данного айпи не существует",
        "invalid_arg": "❌ Неверный аргумент. Укажите домен или IP-адрес",
        "processing": "🔍 Обработка запроса..."
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.command(alias="whois")
    async def whoiscmd(self, message):
        """- Проверить whois информацию по домену или IP"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("invalid_arg"))
            return

        m = await utils.answer(message, self.strings("processing"))

        try:
            # Проверяем, является ли аргумент IP-адресом
            try:
                socket.inet_aton(args)
                is_ip = True
            except socket.error:
                is_ip = False

            if is_ip:
                # Обработка IP-адреса
                url = f"http://ip-api.com/json/{args}?fields=66842623&lang=ru"
                response = requests.get(url).json()

                if response["status"] == "fail":
                    await utils.answer(m, self.strings("ip_not_exists"))
                    return

                org = response.get("org", "Неизвестно")
                isp = response.get("isp", "Неизвестно")
                country = response.get("country", "Неизвестно")
                country_code = response.get("countryCode", "")
                region = response.get("regionName", "Неизвестно")
                city = response.get("city", "Неизвестно")
                zip_code = response.get("zip", "Неизвестно")
                timezone = response.get("timezone", "Неизвестно")
                lat = response.get("lat", "Неизвестно")
                lon = response.get("lon", "Неизвестно")
                asn = response.get("as", "Неизвестно")

                result = (
                    f"🌎 {args}\n"
                    f"├ ❇ Организация: {org}\n"
                    f"├ 🧲 Провайдер: {isp}\n"
                    f"├ 🇦🇺 Страна: {country} ({country_code})\n"
                    f"├ 🗺 Регион: {region}\n"
                    f"├ 🗾 Город: {city}\n"
                    f"├ ✉ Почтовый индекс: {zip_code}\n"
                    f"├ 🕑 Временная зона: {timezone}\n"
                    f"├ 🔯 Координаты: {lat} {lon}\n"
                    f"└ 🔗 ASN: {asn}\n"
                )
            else:
                # Обработка домена
                start_time = time.time()
                try:
                    w = whois.whois(args)
                except whois.parser.PywhoisError:
                    await utils.answer(m, self.strings("domain_free"))
                    return

                if not w.domain_name:
                    await utils.answer(m, self.strings("domain_free"))
                    return

                domain = args.lower()
                creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                expiry_date = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date
                registrar = w.registrar if w.registrar else "Неизвестно"

                statuses = []
                if w.status:
                    if isinstance(w.status, list):
                        statuses = [s for s in w.status if s]
                    else:
                        statuses = [w.status]
                statuses = statuses[0].split(', ')

                name_servers = []
                if w.name_servers:
                    if isinstance(w.name_servers, list):
                        name_servers = [ns.lower().rstrip('.') for ns in w.name_servers if ns]
                    else:
                        name_servers = [w.name_servers.lower().rstrip('.')]

                if creation_date:
                    creation_date_str = creation_date.strftime("%d %B %Y %H:%M").replace("October", "октября")
                else:
                    creation_date_str = "Неизвестно"

                if expiry_date:
                    expiry_date_str = expiry_date.strftime("%d %B %Y %H:%M").replace("October", "октября")
                else:
                    expiry_date_str = "Неизвестно"

                response_time = int((time.time() - start_time) * 1000)

                result = [
                    f"🌎 {domain}",
                    f"├ 🕒 Зарегистрирован: {creation_date_str}",
                    f"├ ⏳ Истекает: {expiry_date_str}",
                    f"├ 🎛 Регистратор: {registrar}",
                ]

                if statuses:
                    result.append("├ 📶 Статусы домена:")
                    for status in statuses:
                        result.append(f"├ {status}")

                if name_servers:
                    result.append("├ 📡 Серверы имен:")
                    for ns in name_servers:
                        result.append(f"├ {ns}.")

                result.append(f"└ ⏰ Время на запрос: {response_time} мс.")

                result = "\n".join(result)

            await utils.answer(m, result)
        except Exception as e:
            await utils.answer(m, f"❌ Ошибка: {str(e)}")

    @loader.command(alias="ip")
    async def ipcmd(self, message):
        """- Получить IP-адреса по домену"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите домен")
            return

        m = await utils.answer(message, self.strings("processing"))

        try:

            # Получаем A записи (IPv4)
            ipv4_list = []
            try:
                ipv4_list = socket.gethostbyname_ex(args)[2]
            except socket.gaierror:
                pass

            # Получаем AAAA записи (IPv6)
            ipv6_list = []
            try:
                addrinfo = socket.getaddrinfo(args, None, socket.AF_INET6)
                ipv6_list = list(set([x[4][0] for x in addrinfo]))
            except socket.gaierror:
                pass

            # Получаем NS записи (серверы имен)
            ns_list = []
            try:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 3
                resolver.lifetime = 3
                answers = resolver.resolve(args, 'NS')
                ns_list = [str(rdata) for rdata in answers]
            except Exception as e:
                try:
                    resolver = dns.asyncresolver.Resolver()
                    answers = await resolver.resolve(args, 'NS')
                    ns_list = [str(rdata) for rdata in answers]
                except:
                    pass

            # Формируем результат
            result = []

            if ipv4_list:
                for ip in ipv4_list:
                    result.append(f"⚡ IPv4: <code>{ip}</code>")

            if ipv6_list:
                for ip in ipv6_list:
                    result.append(f"🖥 IPv6: <code>{ip}</code>")

            if ns_list:
                for ns in ns_list[:2]:
                    result.append(f"📡 Сервер имен: <code>{ns}</code>")

            await utils.answer(m, "\n".join(result))
        except Exception as e:
            await utils.answer(m, f"❌ Ошибка: {str(e)}")
