from time import time

from bot import LOGGER, subprocess_lock
from bot.helper.ext_utils.files_utils import get_path_size
from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)


class SevenZStatus:
    def __init__(self, listener, gid, status=""):
        self.listener = listener
        self._size = self.listener.size
        self._gid = gid
        self._start_time = time()
        self._proccessed_bytes = 0
        self.cstatus = status

    def gid(self):
        return self._gid

    def speed_raw(self):
        return self._proccessed_bytes / (time() - self._start_time)

    async def progress_raw(self):
        await self.processed_raw()
        try:
            return self._proccessed_bytes / self._size * 100
        except Exception:
            return 0

    async def progress(self):
        return f"{round(await self.progress_raw(), 2)}%"

    def speed(self):
        return f"{get_readable_file_size(self.speed_raw())}/s"

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self._size)

    def eta(self):
        try:
            seconds = (self._size - self._proccessed_bytes) / self.speed_raw()
            return get_readable_time(seconds)
        except Exception:
            return "-"

    def status(self):
        if self.cstatus == "Extract":
            return MirrorStatus.STATUS_EXTRACT
        return MirrorStatus.STATUS_ARCHIVE

    def processed_bytes(self):
        return get_readable_file_size(self._proccessed_bytes)

    async def processed_raw(self):
        if self.listener.new_dir:
            self._proccessed_bytes = await get_path_size(self.listener.new_dir)
        else:
            self._proccessed_bytes = (
                await get_path_size(self.listener.dir) - self._size
            )

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling {self.cstatus}: {self.listener.name}")
        self.listener.is_cancelled = True
        async with subprocess_lock:
            if (
                self.listener.subproc is not None
                and self.listener.subproc.returncode is None
            ):
                self.listener.subproc.kill()
        await self.listener.on_upload_error(f"{self.cstatus} stopped by user!")
