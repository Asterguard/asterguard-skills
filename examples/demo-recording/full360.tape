# VHS tape — records the full-360 skills walkthrough to a GIF.
#   brew install vhs && vhs examples/demo-recording/full360.tape   (run from repo root)
Output docs/media/full-360-demo.gif
Output docs/media/full-360-demo.mp4

Require bash
Set Shell bash
Set FontSize 14
Set Width 1180
Set Height 720
Set Padding 18
Set Theme "Dracula"
Set TypingSpeed 35ms
Set PlaybackSpeed 1.0

# Prime the shell without showing the path.
Hide
Type "cd `git rev-parse --show-toplevel 2>/dev/null || pwd` && clear"
Enter
Show
Sleep 600ms

Type "./examples/demo-recording/full360-demo.sh"
Sleep 500ms
Enter

# Let the narrated player run (it paces itself to ~22s), then hold on the last frame.
Sleep 24s
Sleep 2s
