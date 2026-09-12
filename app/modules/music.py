"""Module E - Music Licensing Check (real, not mocked).

Uses AudD (https://audd.io) to identify a track in an uploaded audio file.
AudD tells you WHAT SONG IT IS -- it does not, and cannot, tell you whether
the brand has a valid commercial license to use it. This module is built to
never blur that line: a positive identification is reported as an unresolved
"go verify licensing" flag, never as "cleared".

The standard AudD endpoint accepts audio files (not video) up to 10MB. This
build asks the user to upload the reel's audio track directly (mp3/wav/m4a/
ogg) rather than extracting audio from video server-side, since that would
require an ffmpeg binary this environment doesn't have -- the same
"paste transcript instead of parsing video" honesty trade-off the build spec
allows for Module A/B's content input.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.config import AUDD_API_KEY, AUDD_ENDPOINT, RISK_MEDIUM
from app.pipeline import Issue

MODULE = "music"


class AudDConfigError(RuntimeError):
    pass


class AudDRequestError(RuntimeError):
    pass


@dataclass
class MusicIdentification:
    identified: bool
    artist: str = ""
    title: str = ""
    album: str = ""
    label: str = ""
    release_date: str = ""
    message: str = ""
    raw: dict = field(default_factory=dict)


def identify_track(audio_bytes: bytes, filename: str) -> MusicIdentification:
    """Calls AudD's recognition endpoint. Raises AudDConfigError if no API key
    is configured, AudDRequestError on a network/API failure -- callers should
    surface both honestly rather than pretending a result exists."""
    if not AUDD_API_KEY:
        raise AudDConfigError(
            "AUDD_API_KEY is not set. Get a free-tier key at https://dashboard.audd.io/ "
            "and add it to your .env file to enable music licensing checks."
        )

    try:
        resp = httpx.post(
            AUDD_ENDPOINT,
            data={"api_token": AUDD_API_KEY, "return": "apple_music,spotify"},
            files={"file": (filename, audio_bytes)},
            timeout=30.0,
        )
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as e:
        raise AudDRequestError(f"AudD request failed: {e}") from e

    if payload.get("status") != "success":
        raise AudDRequestError(f"AudD returned an error: {payload.get('error', payload)}")

    result = payload.get("result")
    if not result:
        return MusicIdentification(
            identified=False,
            message="No copyrighted track detected. This is not a guarantee that the audio "
            "is unlicensed or original -- AudD's database, like any fingerprinting service, "
            "can miss tracks (short clips, heavy processing, background/ambient mixing, or "
            "tracks outside its catalog).",
            raw=payload,
        )

    artist = result.get("artist", "")
    title = result.get("title", "")
    label = result.get("label", "")
    return MusicIdentification(
        identified=True,
        artist=artist,
        title=title,
        album=result.get("album", ""),
        label=label,
        release_date=result.get("release_date", ""),
        message=(
            f"Track identified: {artist} - {title}"
            + (f", {label}" if label else "")
            + ". Commercial usage rights not verified -- confirm licensing before publication."
        ),
        raw=payload,
    )


def run_music_check(audio_bytes: bytes | None, filename: str) -> tuple[list[Issue], dict]:
    """Full Module E pipeline. Returns (issues_for_dashboard, detail_dict).

    Deliberately never returns a risk of NONE for an identified track --
    "identified" always means "unresolved, go check the license", which is
    represented as a MEDIUM-risk issue so it shows up in the dashboard and
    the score, and surfaces the license-later document generator."""
    if audio_bytes is None:
        return [], {"note": "No audio file was provided for music identification."}

    try:
        ident = identify_track(audio_bytes, filename)
    except AudDConfigError as e:
        return [], {"error": str(e), "configured": False}
    except AudDRequestError as e:
        return [], {"error": str(e), "configured": True}

    detail = {
        "configured": True,
        "identified": ident.identified,
        "artist": ident.artist,
        "title": ident.title,
        "album": ident.album,
        "label": ident.label,
        "release_date": ident.release_date,
        "message": ident.message,
    }

    if not ident.identified:
        return [], detail

    issue = Issue(
        module=MODULE,
        title=f"Unlicensed-status track identified: {ident.artist} - {ident.title}",
        risk=RISK_MEDIUM,
        evidence=f"Audio fingerprint match: {ident.artist} - {ident.title}"
        + (f" ({ident.label})" if ident.label else ""),
        legal_citation="AudD audio identification (not a legal source -- a factual identification only)",
        legal_text="AudD confirms which recording is present in the audio. It does not confirm "
        "whether the brand or influencer holds a synchronization/commercial usage license for "
        "that recording. Using an unlicensed commercial recording in paid advertising content "
        "can expose the brand to copyright infringement claims independent of ASCI/CCPA "
        "compliance.",
        explanation=ident.message,
        suggested_fix="Confirm with the brand's legal/marketing team that a commercial "
        "sync license covers this track for this campaign's channels and duration before "
        "publishing, or replace the audio with licensed/royalty-free music.",
        extra={
            "artist": ident.artist,
            "title": ident.title,
            "album": ident.album,
            "label": ident.label,
            "release_date": ident.release_date,
            "requires_license_later_doc": True,
        },
    )
    return [issue], detail
