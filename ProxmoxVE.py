# meta developer: ZelearFox
# meta pic: https://img.icons8.com/color/48/000000/proxmox.png
# meta banner: https://i.imgur.com/ABCD123.png

# scope: hikka_only
# scope: hikka_min 1.3.0
# requires: requests

from .. import loader, utils
import requests
import json
from typing import Optional, Tuple, Dict, Any
from hikka.types import Message
from urllib.parse import quote

@loader.tds
class ProxmoxVEMod(loader.Module):
    """Управление Proxmox VE через API"""

    strings = {
        "name": "ProxmoxVE",
        "author": "ZelearFox",
        "version": "2.1.0",
        "description": "Полное управление Proxmox VE через API",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "PVE_HOST",
                None,
                lambda: "Хост Proxmox VE (с портом)",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "PVE_USER",
                None,
                lambda: "Пользователь (user@realm)",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "PVE_TOKEN_NAME",
                None,
                lambda: "Имя API токена",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "PVE_TOKEN_VALUE",
                None,
                lambda: "Значение API токена",
                validator=loader.validators.String()
            ),
        )

    async def _make_pve_request(self, method: str, path: str, data: Optional[dict] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Улучшенный запрос к API Proxmox"""
        if not all([self.config["PVE_HOST"], self.config["PVE_USER"],
                  self.config["PVE_TOKEN_NAME"], self.config["PVE_TOKEN_VALUE"]]):
            return None, "🔴 Настройте модуль через .pveset"

        url = f"https://{self.config['PVE_HOST']}/api2/json{path}"
        headers = {
            "Authorization": f"PVEAPIToken={self.config['PVE_USER']}!{self.config['PVE_TOKEN_NAME']}={self.config['PVE_TOKEN_VALUE']}",
            "Accept": "application/json"
        }

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=data,
                verify=False,
                timeout=15
            )

            if response.status_code == 200:
                return response.json().get("data"), None
            return None, f"🔴 Ошибка API ({response.status_code}): {response.text}"
        except Exception as e:
            return None, f"🔴 Ошибка соединения: {str(e)}"

    async def _get_vm_status(self, vmid: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Получение статуса конкретной VM"""
        data, error = await self._make_pve_request("GET", "/cluster/resources?type=vm")
        if error:
            return None, error

        vm = next((item for item in data if item["vmid"] == vmid), None)
        if not vm:
            return None, f"🔴 VM с ID {vmid} не найдена"
        return vm, None

    async def _get_vm_config(self, node: str, vmid: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Получение конфигурации VM"""
        return await self._make_pve_request("GET", f"/nodes/{node}/qemu/{vmid}/config")

    async def _get_vm_stats(self, node: str, vmid: int) -> Tuple[Optional[Dict], Optional[str]]:
        """Получение статистики VM"""
        return await self._make_pve_request("GET", f"/nodes/{node}/qemu/{vmid}/status/current")

    @loader.command(alias="pvels")
    async def pvelist(self, message: Message):
        """Список всех виртуальных машин"""
        data, error = await self._make_pve_request("GET", "/cluster/resources?type=vm")
        if error:
            await utils.answer(message, error)
            return

        if not data:
            await utils.answer(message, "🔴 Нет доступных виртуальных машин")
            return

        result = "🖥️ <b>Список VM в Proxmox:</b>\n\n"
        for vm in sorted(data, key=lambda x: x["vmid"]):
            if vm["type"] in ("qemu", "lxc"):
                status_emoji = {
                    "running": "🟢",
                    "stopped": "🔴",
                    "paused": "🟡"
                }.get(vm["status"], "⚪")

                result += (
                    f"{status_emoji} <b>{vm['vmid']}</b> - {vm['name']} "
                    f"(Тип: {vm['type'].upper()}, Узел: {vm.get('node', 'N/A')}, "
                    f"Статус: {vm['status'].upper()})\n"
                )

        await utils.answer(message, result)

    @loader.command(alias="pveinfo")
    async def pveinfo(self, message: Message):
        """Подробная информация о VM"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)

        # Получаем базовую информацию
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        # Получаем дополнительную информацию
        node = vm["node"]
        config, config_error = await self._get_vm_config(node, vmid)
        stats, stats_error = await self._get_vm_stats(node, vmid)

        # Форматируем статус
        status_map = {
            "running": "🟢 ЗАПУЩЕНА",
            "stopped": "🔴 ОСТАНОВЛЕНА",
            "paused": "🟡 ПРИОСТАНОВЛЕНА"
        }
        status = status_map.get(vm["status"], f"⚪ {vm['status'].upper()}")

        # Ресурсы
        cpu_usage = float(stats.get("cpu", 0)) * 100 if stats else 0
        mem_used = int(vm.get("mem", 0)) / (1024 ** 3)  # GB
        mem_total = int(vm.get("maxmem", 0)) / (1024 ** 3)  # GB
        mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0

        # Сеть
        net_in = 0
        net_out = 0
        if stats and "netin" in stats:
            net_in = int(stats["netin"]) / (1024 ** 2)  # MB
            net_out = int(stats["netout"]) / (1024 ** 2)  # MB

        # Конфигурация
        cores = config.get("cores", "N/A") if config else "N/A"
        sockets = config.get("sockets", "N/A") if config else "N/A"
        memory = int(config.get("memory", 0)) / 1024 if config else 0  # GB

        info = (
            f"📊 <b>Подробная информация о VM {vmid}:</b>\n\n"
            f"<b>Имя:</b> {vm['name']}\n"
            f"<b>Тип:</b> {vm['type'].upper()}\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Узел:</b> {node}\n\n"

            f"<b>Ресурсы:</b>\n"
            f"• CPU: {cpu_usage:.2f}% ({cores} ядер, {sockets} сокетов)\n"
            f"• Память: {mem_used:.2f} GB / {mem_total:.2f} GB ({mem_percent:.1f}%)\n"
            f"• Выделено: {memory:.2f} GB RAM\n\n"

            f"<b>Сеть:</b>\n"
            f"• Входящий трафик: {net_in:.2f} MB\n"
            f"• Исходящий трафик: {net_out:.2f} MB\n"
        )

        await utils.answer(message, info)

    @loader.command(alias="pvenovnc")
    async def pvenovnc(self, message: Message):
        """Получить ссылку на консоль noVNC"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        if vm["status"] != "running":
            await utils.answer(message, "🔴 VM должна быть запущена для доступа к консоли")
            return

        host = self.config["PVE_HOST"].split(":")[0]
        port = self.config["PVE_HOST"].split(":")[1] if ":" in self.config["PVE_HOST"] else "8006"

        novnc_url = (
            f"https://{host}:{port}/?console=kvm&novnc=1&vmid={vmid}"
            f"&node={vm['node']}&resize=scale&vmname={quote(vm['name'])}"
        )

        await utils.answer(
            message,
            f"🔗 <b>Ссылка на консоль VM {vmid}:</b>\n\n{novnc_url}\n\n"
            "⚠️ Для доступа потребуется авторизация в Proxmox"
        )

    @loader.command(alias="pvestart")
    async def pvestart(self, message: Message):
        """Запустить виртуальную машину"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        if vm["status"] == "running":
            await utils.answer(message, f"🔴 VM {vmid} уже запущена")
            return
        elif vm["status"] == "paused":
            await utils.answer(message, f"🔴 VM {vmid} приостановлена. Сначала снимите с паузы")
            return

        _, error = await self._make_pve_request(
            "POST",
            f"/nodes/{vm['node']}/qemu/{vmid}/status/start"
        )

        await utils.answer(
            message,
            f"🟢 VM {vmid} успешно запущена" if not error
            else f"🔴 Ошибка: {error}"
        )

    @loader.command(alias="pvestop")
    async def pvestop(self, message: Message):
        """Остановить виртуальную машину"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        if vm["status"] == "stopped":
            await utils.answer(message, f"🔴 VM {vmid} уже остановлена")
            return
        elif vm["status"] == "paused":
            await utils.answer(message, f"🔴 VM {vmid} приостановлена. Сначала снимите с паузы")
            return

        _, error = await self._make_pve_request(
            "POST",
            f"/nodes/{vm['node']}/qemu/{vmid}/status/stop"
        )

        await utils.answer(
            message,
            f"🟢 VM {vmid} успешно остановлена" if not error
            else f"🔴 Ошибка: {error}"
        )

    @loader.command(alias="pvereboot")
    async def pvereboot(self, message: Message):
        """Перезагрузить виртуальную машину"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        if vm["status"] != "running":
            await utils.answer(message, f"🔴 VM {vmid} не запущена (текущий статус: {vm['status']})")
            return

        _, error = await self._make_pve_request(
            "POST",
            f"/nodes/{vm['node']}/qemu/{vmid}/status/reboot"
        )

        await utils.answer(
            message,
            f"🟢 VM {vmid} успешно перезагружается" if not error
            else f"🔴 Ошибка: {error}"
        )

    @loader.command(alias="pvepause")
    async def pvepause(self, message: Message):
        """Приостановить/возобновить виртуальную машину"""
        args = utils.get_args_raw(message)
        if not args.isdigit():
            await utils.answer(message, "🔴 Укажите числовой ID виртуальной машины")
            return

        vmid = int(args)
        vm, error = await self._get_vm_status(vmid)
        if error:
            await utils.answer(message, error)
            return

        if vm["status"] == "stopped":
            await utils.answer(message, f"🔴 VM {vmid} остановлена. Сначала запустите её")
            return

        action = "resume" if vm["status"] == "paused" else "suspend"
        action_name = "возобновлена" if action == "resume" else "приостановлена"

        _, error = await self._make_pve_request(
            "POST",
            f"/nodes/{vm['node']}/qemu/{vmid}/status/{action}"
        )

        await utils.answer(
            message,
            f"🟢 VM {vmid} успешно {action_name}" if not error
            else f"🔴 Ошибка: {error}"
        )

    @loader.command(alias="pveset")
    async def pveset(self, message: Message):
        """Настройка подключения к Proxmox"""
        args = utils.get_args_raw(message)

        if not args:
            current = (
                f"⚙️ <b>Текущие настройки:</b>\n\n"
                f"<b>Хост:</b> {self.config['PVE_HOST'] or 'Не задан'}\n"
                f"<b>Пользователь:</b> {self.config['PVE_USER'] or 'Не задан'}\n"
                f"<b>Токен:</b> {self.config['PVE_TOKEN_NAME'] or 'Не задан'}\n"
                f"<b>Ключ:</b> {'*****' if self.config['PVE_TOKEN_VALUE'] else 'Не задан'}\n\n"
                f"Формат: .pveset хост:порт user@realm token_name token_value\n"
                f"Пример: .pveset pve.example.com:443 root@pve mytoken 12ab-34cd"
            )
            await utils.answer(message, current)
            return

        parts = args.split()
        if len(parts) != 4:
            await utils.answer(message, "🔴 Неверный формат. Требуется 4 параметра")
            return

        self.config["PVE_HOST"] = parts[0]
        self.config["PVE_USER"] = parts[1]
        self.config["PVE_TOKEN_NAME"] = parts[2]
        self.config["PVE_TOKEN_VALUE"] = parts[3]

        await utils.answer(message, "🟢 Настройки успешно сохранены!")