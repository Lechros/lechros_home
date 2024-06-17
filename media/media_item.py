import base64
from datetime import timedelta
from typing import Self, Optional

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSession as MediaSession,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
)
from winrt.windows.storage.streams import Buffer, IRandomAccessStreamReference, InputStreamOptions, DataReader


class MediaItem:
    """개별 앱에서 재생 중인 미디어의 정보를 나타냅니다."""

    session: MediaSession
    app_id: str
    title: str
    start_time: timedelta
    end_time: timedelta
    position: timedelta
    playback_status: PlaybackStatus

    def __eq__(self, other: Self) -> bool:
        return (
                self.app_id == other.app_id and
                self.title == other.title and
                self.start_time == other.start_time and
                self.end_time == other.end_time and
                self.position == other.position and
                self.playback_status == other.playback_status
        )

    async def get_thumbnail_base64_encoded(self) -> Optional[str]:
        try:
            media = await self.session.try_get_media_properties_async()
            thumbnail: IRandomAccessStreamReference = media.thumbnail

            if thumbnail is None:
                return None

            buffer = Buffer(5_000_000)

            stream = await thumbnail.open_read_async()
            stream.read_async(buffer, buffer.capacity, InputStreamOptions.READ_AHEAD)

            reader = DataReader.from_buffer(buffer)
            read_buffer = reader.read_buffer(buffer.length)

            return base64.b64encode(read_buffer).decode()

        except OSError as e:
            print(e)
            return None

    @classmethod
    async def create_async(cls, session: MediaSession) -> Self:
        media = await session.try_get_media_properties_async()
        timeline = session.get_timeline_properties()
        playback = session.get_playback_info()

        item = cls()
        item.session = session
        item.app_id = session.source_app_user_model_id
        item.title = media.title
        item.start_time = timeline.start_time
        item.end_time = timeline.end_time
        item.position = timeline.position
        item.playback_status = playback.playback_status

        return item
