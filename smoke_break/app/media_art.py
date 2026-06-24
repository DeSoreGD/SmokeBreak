from __future__ import annotations

from pathlib import Path


def embedded_art_bytes(audio_path: str) -> bytes | None:
    if not audio_path:
        return None
    path = Path(audio_path)
    if not path.exists():
        return None

    art = embedded_art_with_mutagen(path)
    if art:
        return art
    return embedded_art_from_id3(path)


def embedded_art_with_mutagen(path: Path) -> bytes | None:
    try:
        from mutagen import File
        from mutagen.id3 import APIC
        from mutagen.mp4 import MP4Cover
    except ImportError:
        return None

    try:
        audio = File(path)
    except Exception:
        return None
    if audio is None:
        return None

    tags = getattr(audio, "tags", None)
    if not tags:
        return None

    for value in tags.values():
        if isinstance(value, APIC):
            return bytes(value.data)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, (MP4Cover, bytes, bytearray)):
                    return bytes(item)
        if isinstance(value, (bytes, bytearray)) and len(value) > 32:
            return bytes(value)

    pictures = getattr(audio, "pictures", None)
    if pictures:
        for picture in pictures:
            data = getattr(picture, "data", None)
            if data:
                return bytes(data)

    return None


def embedded_art_from_id3(path: Path) -> bytes | None:
    if path.suffix.lower() != ".mp3":
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 20 or data[:3] != b"ID3":
        return None

    version = data[3]
    tag_size = synchsafe_to_int(data[6:10])
    offset = 10
    tag_end = min(len(data), offset + tag_size)

    while offset + 10 <= tag_end:
        frame_id = data[offset:offset + 4]
        if frame_id == b"\x00\x00\x00\x00":
            break
        raw_size = data[offset + 4:offset + 8]
        frame_size = synchsafe_to_int(raw_size) if version == 4 else int.from_bytes(raw_size, "big")
        frame_start = offset + 10
        frame_end = frame_start + frame_size
        if frame_size <= 0 or frame_end > tag_end:
            break
        if frame_id == b"APIC":
            return parse_apic_frame(data[frame_start:frame_end])
        offset = frame_end
    return None


def parse_apic_frame(frame: bytes) -> bytes | None:
    if len(frame) < 8:
        return None
    encoding = frame[0]
    mime_end = frame.find(b"\x00", 1)
    if mime_end == -1 or mime_end + 2 >= len(frame):
        return None
    description_start = mime_end + 2
    if encoding in {1, 2}:
        terminator = b"\x00\x00"
        description_end = frame.find(terminator, description_start)
        image_start = description_end + 2 if description_end != -1 else description_start
    else:
        description_end = frame.find(b"\x00", description_start)
        image_start = description_end + 1 if description_end != -1 else description_start
    image = frame[image_start:]
    if image.startswith((b"\xff\xd8\xff", b"\x89PNG", b"RIFF", b"GIF8")):
        return image
    return image if len(image) > 128 else None


def synchsafe_to_int(raw: bytes) -> int:
    value = 0
    for byte in raw:
        value = (value << 7) | (byte & 0x7F)
    return value
