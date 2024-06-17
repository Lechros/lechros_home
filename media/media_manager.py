import asyncio
import uuid
from typing import Optional, Callable

from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

from media.media_item import MediaItem

MediaState = dict[str, MediaItem]
ChangeListener = Callable[[MediaState], None]


# Windows event doesn't fire correctly, use polling to detect changes.

class MediaManager:
    """윈도우 전역 미디어 플레이어에서 재생중인 미디어를 관리합니다."""

    running: bool
    interval: float
    state: MediaState

    on_change: dict[str, ChangeListener]

    def __init__(self, interval: float = 1):
        self.running = False
        self.interval = interval
        self.state = MediaState()
        self.on_change = {}

    # region Media State
    async def start_loop(self):
        self.running = True
        while self.running:
            await self._loop()
            await asyncio.sleep(self.interval)

    def stop_loop(self):
        self.running = False

    def get_media_item(self, item_id: str) -> Optional[MediaItem]:
        return self.state[self._normalize_item_id(item_id)]

    async def _loop(self):
        prev_state = self.state
        self.state = await self._get_current_state()

        if prev_state != self.state:
            self._run_change_listeners(self.state)

    async def _get_current_state(self) -> MediaState:
        state = {}
        # always request new instance to get accurate playback status
        for session in (await self._get_manager()).get_sessions():
            item = await MediaItem.create_async(session)
            id = self._normalize_item_id(item.app_id)
            state[id] = item
        return state

    @staticmethod
    def _normalize_item_id(item_id: str) -> str:
        return item_id.strip().lower()

    # endregion

    # region Change Event
    def add_change_listener(self, listener: ChangeListener) -> str:
        id = str(uuid.uuid4())
        self.on_change[id] = listener
        return id

    def remove_change_listener(self, id: str):
        del self.on_change[id]

    def _run_change_listeners(self, state: MediaState):
        for listener in self.on_change.values():
            listener(state)

    # endregion

    # region Playback Control
    async def play(self, item_id: str):
        item = self._find_media_item(item_id)
        if item is not None:
            item.session.try_play_async()

    async def play_all(self):
        for item in self.state.values():
            await item.session.try_play_async()

    async def pause(self, item_id: str):
        item = self._find_media_item(item_id)
        if item is not None:
            item.session.try_pause_async()

    async def pause_all(self):
        for item in self.state.values():
            await item.session.try_pause_async()

    # endregion

    @staticmethod
    async def _get_manager() -> GlobalSystemMediaTransportControlsSessionManager:
        return await GlobalSystemMediaTransportControlsSessionManager.request_async()
