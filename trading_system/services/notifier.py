class DiscordNotifier:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def notify(self, message: str):
        if self.enabled:
            print(f"[discord] {message}")
