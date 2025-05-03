# -*- coding: utf-8 -*-
# meta developer: ZelearFox
# scope: hikka_only
# requires: base64

from .. import loader, utils
import base64
from typing import Dict, Tuple, Union

PRICES = {
    'cpu': 80,          # руб/ядро в месяц
    'ram': 80,          # руб/ГБ в месяц
    'disk': {
        'hdd': 3,       # руб/ГБ в месяц
        'nvme': 5       # руб/ГБ в месяц
    },
    'ip': 150,          # руб/IP в месяц (сверх бесплатного)
    'free_ips': 1       # количество бесплатных IP
}

@loader.tds
class ReFoxCloudConfigMod(loader.Module):
    """Модуль для декодирования и расчета стоимости конфигурации сервера"""

    strings = {
        "name": "ReFoxCloudConfig",
        "decode_help": "🔧 <b>Использование:</b> <code>.rfccfg [код]</code> - декодирует конфигурацию сервера и показывает стоимость",
        "invalid_code": "❌ <b>Некорректный код конфигурации!</b>",
        "invalid_values": "❌ <b>Недопустимые значения в конфигурации!</b>",
        "result": (
            "🖥 <b>Конфигурация сервера:</b>\n"
            "├ <b>Процессор:</b> {} ядер\n"
            "├ <b>RAM:</b> {} ГБ\n"
            "├ <b>Диск:</b> {} ГБ ({})\n"
            "├ <b>IP-адреса:</b> {}\n"
            "├ <b>Скидка:</b> {}%\n"
            "└ <b>Итоговая стоимость:</b> {}₽/месяц"
        )
    }

    async def decodeconfig(self, message):
        """Декодировать конфигурацию сервера из base64 кода"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("decode_help"))
            return

        try:
            config, price = self._decode_and_calculate(args)
            await utils.answer(
                message,
                self.strings("result").format(
                    config["cpu"],
                    config["ram"],
                    config["disk"],
                    "NVMe" if config["disk_type"] == "nvme" else "HDD",
                    config["ip"],
                    config["discount"],
                    price
                )
            )
        except ValueError as e:
            if "values" in str(e):
                await utils.answer(message, self.strings("invalid_values"))
            else:
                await utils.answer(message, self.strings("invalid_code"))
        except Exception:
            await utils.answer(message, self.strings("invalid_code"))

    def _decode_and_calculate(self, config_code: str) -> Tuple[Dict[str, Union[int, str]], int]:
        """Декодирует конфигурацию и считает стоимость"""
        try:
            decoded = base64.b64decode(config_code).decode('utf-8')
            parts = decoded.split(':')

            if len(parts) != 6:
                raise ValueError("Invalid config format")

            config = {
                'cpu': int(parts[0]),
                'ram': int(parts[1]),
                'disk': int(parts[2]),
                'ip': int(parts[3]),
                'discount': int(parts[4]),
                'disk_type': parts[5] if parts[5] in ('hdd', 'nvme') else 'hdd'
            }

            # Проверка допустимых значений
            if (config['cpu'] < 1 or config['ram'] < 1 or
                config['disk'] < 10 or config['ip'] < 1):
                raise ValueError("Invalid values")

            if config['discount'] < 0 or config['discount'] > 100:
                raise ValueError("Invalid values")

            # Расчет стоимости
            disk_price = PRICES['disk'][config['disk_type']]

            total = (
                (config['cpu'] * PRICES['cpu']) +
                (config['ram'] * PRICES['ram']) +
                (config['disk'] * disk_price) +
                (max(0, config['ip'] - PRICES['free_ips']) * PRICES['ip'])
            )

            discount_amount = total * (config['discount'] / 100)
            final_price = round(total - discount_amount)

            return config, final_price

        except (base64.binascii.Error, UnicodeDecodeError):
            raise ValueError("Decoding error")
        except (ValueError, KeyError):
            raise ValueError("Invalid values")
