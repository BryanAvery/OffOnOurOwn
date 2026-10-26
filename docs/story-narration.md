# ElevenLabs story narration

This is an opt-in first phase. Existing stories remain unchanged.

## Configuration

1. Add repository Actions secret `ELEVENLABS_API_KEY`.
2. Add repository Actions variable `ELEVENLABS_VOICE_ID` with the ID of your chosen warm British male voice (for example, audition George in ElevenLabs).
3. Add `audio_generate: true` to a story's YAML front matter.
4. Run the **Generate story narration** workflow manually from the Actions tab.
5. Once generated, add `audio: /audio/stories/<slug>.mp3` to the story front matter to show the player.

The workflow only generates missing MP3s. To regenerate after editing a story, remove its old MP3 first. This avoids accidental charges. Do not store the API key in the repository.

## Limitations and next steps

The script currently supports YAML front matter and stories in `content/stories`. Verify the content structure before opting in. Long stories may exceed ElevenLabs model character limits: split into chunks and join with ffmpeg before enabling them. Improve narration cleaning for Hugo shortcodes and photo captions as required. For larger audio libraries, consider object storage rather than keeping all MP3s in Git.

The workflow runs manually to prevent unapproved API spending. Review generation charges and voice licence before running.
