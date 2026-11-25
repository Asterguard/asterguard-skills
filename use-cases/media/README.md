# Use-case media

The `s1–s4` scenario videos are **hosted externally** — the same place as the launch films:

```
https://agenticrisklabs.io/videos/s1.mp4   (… s2, s3, s4)
```

They are **not committed to this repo**. Video is binary and churns git history; keeping it on
the host (like the launch films linked from the root README) keeps the repo text-only and the
clone small. The scenario docs and the use-cases README link the hosted URLs directly.

## Recording one

Use the helper — it prints the scenario's beats, sets up capture, and keeps the file local:

```bash
scripts/record-usecase.sh s1
```

It writes to `use-cases/media/.local/` (gitignored). When the cut is final:

1. Upload it to the video host as `videos/s<N>.mp4`.
2. The docs already point at `https://agenticrisklabs.io/videos/s<N>.mp4` — nothing to change.
3. Fill the scenario doc's **Result** with the real ASR and the canary hit (the proof).

Terminal-only beats can be scripted with a [`vhs`](https://github.com/charmbracelet/vhs) tape at
`use-cases/media/tapes/s<N>.tape` (text, committable); the helper renders it when present.
