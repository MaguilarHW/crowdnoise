Things worked on:

- Created `scrape_audio`, which downloads audio from YouTube or Internet Archive when given a song title.
- Created `split_stems`, which reads audio files from `resources/` and separates them with Demucs.

Current `split_stems` behavior:

- Uses Demucs model `htdemucs_6s` (6-stem separation).
- Writes split outputs as MP3 files under `output/htdemucs_6s/<song title>/`.
- Skips `.gitkeep` in `resources/` so Demucs only receives real audio files.
- Skips tracks that are already split (detects existing stem audio files in the output folder).
- Generates `songdetails.json` for each split song in its output directory.

`songdetails.json` format:

```json
{
  "schema_version": 1,
  "song_id": "kanye-west-homecoming",
  "title": "Kanye West - Homecoming",
  "sr": 44100,
  "song_length_ms": 32000,
  "instruments": {
    "bass": { "original_path": "output/htdemucs_6s/Kanye West - Homecoming/bass.mp3" },
    "drums": { "original_path": "output/htdemucs_6s/Kanye West - Homecoming/drums.mp3" },
    "other": { "original_path": "output/htdemucs_6s/Kanye West - Homecoming/other.mp3" },
    "vocals": { "original_path": "output/htdemucs_6s/Kanye West - Homecoming/vocals.mp3" }
  }
}
```