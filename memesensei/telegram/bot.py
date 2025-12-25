from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, List

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


@dataclass
class CoreClient:
    base_url: str

    def get(self, path: str):
        return requests.get(f"{self.base_url}{path}").json()

    def post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", **kwargs).json()


class TelegramController:
    def __init__(self, bot_token: str, admin_ids: Iterable[int], core_base_url: str):
        self.bot_token = bot_token
        self.admin_ids = set(admin_ids)
        self.core = CoreClient(core_base_url)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    async def _require_admin(self, update: Update) -> bool:
        if update.effective_user and update.effective_user.id in self.admin_ids:
            return True
        if update.effective_message:
            await update.effective_message.reply_text("Not authorized")
        logger.warning("unauthorized telegram access", extra={"user": update.effective_user.id if update.effective_user else None})
        return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        status = self.core.get("/status")
        await update.message.reply_text(f"MemeSensei online. Mode: {'DRY' if status['dry_run'] else 'LIVE'}")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        status = self.core.get("/status")
        await update.message.reply_text(str(status))

    async def positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        positions = self.core.get("/positions")
        await update.message.reply_text(str(positions))

    async def pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        pnl = self.core.get("/trades")
        await update.message.reply_text(str(pnl))

    async def recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        decisions = self.core.get("/decisions")
        await update.message.reply_text(str(decisions[:5]))

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        res = self.core.post("/control/pause")
        await update.message.reply_text(str(res))

    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        res = self.core.post("/control/resume")
        await update.message.reply_text(str(res))

    async def killswitch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        res = self.core.post("/control/killswitch")
        await update.message.reply_text(str(res))

    async def setrisk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        if len(context.args) != 2:
            await update.message.reply_text("Usage: /setrisk key value")
            return
        key, value = context.args
        res = self.core.post("/control/setrisk", params={"key": key, "value": float(value)})
        await update.message.reply_text(str(res))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._require_admin(update):
            return
        await update.message.reply_text("/status /positions /pnl /recent /pause /resume /killswitch /setrisk")

    def build_application(self):
        app = ApplicationBuilder().token(self.bot_token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("positions", self.positions))
        app.add_handler(CommandHandler("pnl", self.pnl))
        app.add_handler(CommandHandler("recent", self.recent))
        app.add_handler(CommandHandler("pause", self.pause))
        app.add_handler(CommandHandler("resume", self.resume))
        app.add_handler(CommandHandler("killswitch", self.killswitch))
        app.add_handler(CommandHandler("setrisk", self.setrisk))
        app.add_handler(CommandHandler("help", self.help))
        return app




def main():  # pragma: no cover - runtime entrypoint
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    admins = [int(x) for x in os.getenv("ADMIN_TELEGRAM_USER_IDS", "").split(",") if x]
    core_url = os.getenv("CORE_API_URL", "http://localhost:8000")
    controller = TelegramController(bot_token=token, admin_ids=admins, core_base_url=core_url)
    app = controller.build_application()
    app.run_polling()


if __name__ == "__main__":  # pragma: no cover - runtime entrypoint
    main()
