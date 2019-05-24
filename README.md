## pysubtools
Library and tools for editing subtitles including left-aligning dialogue and moving single lines up.

##### Code bits
```
import pysubtools

f = pysubtools.load_sub('example.ass')

# Make sure there is at least 170 ms (recommended) of separation between subtitles
f.separate(mstosplit=170, split_type='move_second')

# Looks for subtitles containing dialogue (where all the lines start with 'prefixes')
# and makes the text left-aligned and centered (only works for .ass files)
f.align_dialog(self, video_width=0, video_height=0, prefixes=('-', '–', '—'), style_suffix=' - alignedL')

# Looks for subtitles where there is only one line and raises it slightly,
# so it's closer to the center of the screen and easier to read
f.single_lines_to_top()

# Shift times of all subtitles
f.shift(mstoshift, which_time='both', first_line=1, last_line=0)

# Loop through all subtitles in a file and print the text
[print(subtitle.Text) for subtitle in f]

# Make the 'default' style bold and shadowed
default = f.find_style('Default')
default.Bold = 1
default.Shadow = 1

# Edit the opening lines of an .ass file
f.sections['Script Info']['Title'] = 'New title'
```
