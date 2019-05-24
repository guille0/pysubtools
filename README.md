## pysubtools
Library and tools for editing subtitles including left-aligning dialogue and moving single lines up.

##### Code bits
```
import pysubtools

f = pysubtools.load_sub('example.ass')
```

_Make sure there is at least 170 ms (recommended) of separation between subtitles_
```
f.separate(mstosplit=170, split_type='move_second')
```

_Look for subtitles containing dialogue (where all the lines start with 'prefixes')
and make the text left-aligned and centered (only works for .ass files)_
```
f.align_dialog(self, video_width=0, video_height=0, prefixes=('-', '–', '—'), style_suffix=' - alignedL')
```
_Look for subtitles where there is only one line and raise it slightly,
so it's closer to the center of the screen and easier to read_
```
f.single_lines_to_top()
```
_Shift times of all subtitles_
```
f.shift(mstoshift, which_time='both', first_line=1, last_line=0)
```
_Loop through all subtitles in a file and print the text_
```
[print(subtitle.Text) for subtitle in f]
```
_Make the 'default' style bold and shadowed_
```
default = f.find_style('Default')
default.Bold = 1
default.Shadow = 1
```
_Edit the opening information lines of an .ass file_
```
f.sections['Script Info']['Title'] = 'New title'
```
