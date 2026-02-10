This branch uses Spotify Basic Pitch: pip install basic-pitch
NOTE: Basic Pitch only functions using python 3.10!

This program can take in an mp3 file and extract the notes, storing them in a .mid file. However, only one instrument should be present in the mp3!

Once a song has been broken down into tracks, each individual instrument must be broken down into short, easily recordable samples. Melodic samples must be broken down into notes, so the app can reconstruct the entire melody from a single recording. Basic Pitch performs this operation. It does NOT break down percussion/bass tracks effectively.

To run: python3.10 src/basic_pitch_to_midi.py