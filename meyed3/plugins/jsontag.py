import base64
import inspect
from json import dumps

import meyed3.id3.headers
import meyed3.id3.tag
import meyed3.plugins
from meyed3.utils.log import getLogger

log = getLogger(__name__)


class JsonTagPlugin(meyed3.plugins.LoaderPlugin):
    NAMES = ["json"]
    SUMMARY = "Outputs all tags as JSON."

    def __init__(self, arg_parser):
        super().__init__(arg_parser, cache_files=True, track_images=False)
        g = self.arg_group
        g.add_argument("-c", "--compact", action="store_true",
                       help="Output in compact form, wound new lines or indentation.")
        g.add_argument("-s", "--sort", action="store_true", help="Output JSON in sorted by key.")

    def handleFile(self, f, *args, **kwargs):
        super().handleFile(f)
        if self.audio_file and self.audio_file.info and self.audio_file.tag:
            json = audioFileToJson(self.audio_file)
            print(dumps(json, indent=2 if not self.args.compact else None,
                        sort_keys=self.args.sort))


def audioFileToJson(audio_file):
    tag = audio_file.tag

    tdict = {"path": audio_file.path}

    info = {"time_secs": int(audio_file.info.time_secs * 100.0) / 100.0,
            "size_bytes": int(audio_file.info.size_bytes)}
    tdict["info"] = info

    # Tag fields
    for name in [m for m in dir(tag) if not m.startswith("_") and m not in _tag_exclusions]:
        member = getattr(tag, name)

        if name not in _tag_map:
            if not inspect.ismethod(member) and not inspect.isfunction(member):
                log.warning(f"Unhandled Tag member: {name}")
            continue
        elif member is None:
            continue
        elif member.__class__ is not _tag_map[name]:
            log.warning(f"Unexpected type for member {name}: {member.__class__}")
            continue

        if isinstance(member, (str, int, bool)):
            tdict[name] = member
        elif isinstance(member, meyed3.core.Date):
            tdict[name] = str(member)
        elif isinstance(member, meyed3.id3.Genre):
            tdict[name] = member.name
        elif isinstance(member, bytes):
            tdict[name] = base64.b64encode(member).decode("ascii")
        elif isinstance(member, meyed3.id3.tag.ArtistOrigin):
            ...  # TODO
        elif isinstance(member, (list, tuple)):
            ...  # TODO
        elif isinstance(member, meyed3.id3.tag.AccessorBase):
            ...  # TODO
        elif isinstance(member, (meyed3.id3.tag.TagHeader, meyed3.id3.tag.ExtendedTagHeader,
                                 meyed3.id3.tag.FileInfo, meyed3.id3.frames.FrameSet)):
            ...  # TODO
        else:
            log.warning(f"Unhandled tag member {name}, type {member.__class__.__name__})")

    tdict["_eyeD3"] = meyed3.__about__.__version__
    return tdict


_tag_map = {
    'album': str,
    'album_artist': str,
    'album_type': str,
    'artist': str,
    'original_artist': str,
    'artist_origin': list,
    'artist_url': str,
    'audio_file_url': str,
    'audio_source_url': str,
    'best_release_date': meyed3.core.Date,
    'bpm': int,
    'cd_id': bytes,
    'chapters': meyed3.id3.tag.ChaptersAccessor,
    'comments': meyed3.id3.tag.CommentsAccessor,
    'commercial_url': str,
    'composer': str,
    'copyright_url': str,
    'disc_num': tuple,
    'encoding_date': meyed3.core.Date,
    'extended_header': meyed3.id3.headers.ExtendedTagHeader,
    'file_info': meyed3.id3.tag.FileInfo,
    'frame_set': meyed3.id3.frames.FrameSet,
    'genre': meyed3.id3.Genre,
    'header': meyed3.id3.headers.TagHeader,
    'images': meyed3.id3.tag.ImagesAccessor,
    'internet_radio_url': str,
    'lyrics': meyed3.id3.tag.LyricsAccessor,
    'non_std_genre': meyed3.id3.Genre,
    'objects': meyed3.id3.tag.ObjectsAccessor,
    'original_release_date': meyed3.core.Date,
    'payment_url': str,
    'play_count': int,
    'popularities': meyed3.id3.tag.PopularitiesAccessor,
    'privates': meyed3.id3.tag.PrivatesAccessor,
    'publisher': str,
    'publisher_url': str,
    'recording_date': meyed3.core.Date,
    'release_date': meyed3.core.Date,
    'table_of_contents': meyed3.id3.tag.TocAccessor,
    'tagging_date': meyed3.core.Date,
    'terms_of_use': str,
    'title': str,
    'track_num': tuple,
    'unique_file_ids': meyed3.id3.tag.UniqueFileIdAccessor,
    'user_text_frames': meyed3.id3.tag.UserTextsAccessor,
    'user_url_frames': meyed3.id3.tag.UserUrlsAccessor,
    'version': tuple,
}

_tag_exclusions = {
    "read_only": bool,
}
