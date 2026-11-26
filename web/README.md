# Video Compressor (web version)

A browser version of Video Compressor. Pick a video, pick a size, and it squeezes the video under that size. Nothing is uploaded. All the work happens in your browser.

## How it differs from the desktop app

- Much, much slower. It reads the video one frame at a time, so a 1 minute video can take a while.
- One encoding pass with the browser's built-in H.264 encoder, instead of FFmpeg's two passes.
- Caps frame rate at 30 fps.
- The tab has to stay open and in front while it works.
- Needs a recent browser with WebCodecs (Chrome, Edge, Safari).
- Audio is re-encoded when the browser can decode it. When it can't (for example iPhone .mov files in Safari), the original AAC audio is copied into the new file without re-encoding.
- The sizing rules (bitrate budget, resolution steps, retry when the result is too big) match the desktop app.

## Running it

WebCodecs only works on secure pages, so opening `index.html` straight from disk may not work. Either:

- turn on GitHub Pages for this repo and open the `web` page, or
- serve the folder locally, for example `python -m http.server` inside `web/`, then open `http://localhost:8000`.

Every run writes a detailed log you can copy or save from the page.

## Libraries (loaded from jsDelivr)

- [mp4-muxer](https://github.com/Vanilagy/mp4-muxer) 5.1.3 (MIT) writes the MP4 file.
- [mp4box.js](https://github.com/gpac/mp4box.js) 0.5.4 (BSD-3-Clause) reads the audio out of MP4 and MOV files.
