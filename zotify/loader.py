import itertools
import threading
import time
from zotify.termoutput import Printer, PrintChannel

class Loader:
    def __init__(self, channel, desc=""):
        self.desc = desc
        self.channel = channel
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.steps = ["-", "\\", "|", "/"]
        self.done = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        self.thread.start()

    def stop(self):
        self.done = True
        self.thread.join()

    def _animate(self):
        for c in itertools.cycle(self.steps):
            if self.done:
                break
            Printer.print_loader(self.channel, f"\r\t{c} {self.desc} ")
            time.sleep(0.1)
        Printer.print_loader(self.channel, "\r")
