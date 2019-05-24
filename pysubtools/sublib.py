from pathlib import Path
from copy import deepcopy
from PIL import ImageFont
from matplotlib import font_manager
from .formats import Srt, Ass


def load_sub(path):

    subtitle_file = None

    if Path(path).suffix == '.ass':
        subtitle_file = AssSubFile()

    if Path(path).suffix == '.srt':
        subtitle_file = SrtSubFile()

    if subtitle_file is not None:
        subtitle_file.interpret(path)
        return subtitle_file

    print(f'Could not load file. Can\'t understand format {Path(path.suffix)}.')


def get_font(font, bold='0', italic='0'):

    if bold == '0':
        weight = 400
    else:
        weight = 700

    if italic == '0':
        style = 'normal'
    else:
        style = 'italic'

    properties = font_manager.FontProperties(family=font, style=style, weight=weight)
    fontsearch = font_manager.findfont(properties)

    return fontsearch


def check_text_width(text, font, size, spacing=0):

    font_obj = ImageFont.truetype(font=font, size=int(size/1.125))

    spacing = (len(text)-1)*(spacing)

    width = font_obj.getsize(text)[0]

    return width+spacing


class SubFile:

    def __init__(self):
        # self.sections contains info about the file, used in .ass files
        self.sections = dict()
        self.styles = []
        self.lines = []

    def __str__(self):
        return (
                f'Information on subtitle file:\n'
                f'Individual subtitles: {len(self.lines)}\n'
                f'Styles: {len(self.styles)}\n'
                f'First line: {self.lines[0].Text}\n'
                f'Last line: {self.lines[-1].Text}'
                )

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, i):
        return self.lines[i]

    def save(self, path):

        if Path(path).suffix == '.ass':
            with open(path, 'w') as f:

                # Write the introductory lines (ignorable if there's none)
                for name, section in self.sections.items():
                    f.write(f'[{name}]\n')
                    for key, value in section.items():
                        f.write(f'{key}: {value}\n')
                    # Empty line at the end of each section
                    f.write('\n')

                # Write the styles
                f.write(Ass.style_intro)

                if len(self.styles) == 0:
                    # Adds default style if there's none
                    self.styles.append(Style())

                for st in self.styles:
                    f.write(st.to_line())

                # Write the subtitles
                f.write(Ass.sub_intro)

                for line in self.lines:
                    f.write(line.line_to_ass())

            return 1

        if Path(path).suffix == '.srt':

            with open(path, 'w') as f:

                for i, line in enumerate(self.lines):
                    f.write(line.line_to_srt(i+1))

            return 1

    def remove_line(self, line_number):
        ''' Simple method to remove a line.
            First line would be 1.'''
        self.lines.pop(line_number-1)

    def separate(self, mstosplit=170, split_type='move_second'):
        ''' If subtitles are at a distance of less than 'mstosplit',
            they get separated by 'mstosplit' miliseconds.
            Default is 170ms (1/6 of a second, universally recommended amount).'''

        if split_type == 'move_second':

            for prevline, line in zip(self.lines, self.lines[1:]):

                if line.Start-prevline.End < mstosplit:
                    line.Start = prevline.End+mstosplit

        if split_type == 'move_first':

            for prevline, line in zip(self.lines, self.lines[1:]):

                if line.Start-prevline.End < mstosplit:
                    prevline.End = line.Start-mstosplit

        if split_type == 'split':

            for prevline, line in zip(self.lines, self.lines[1:]):

                if line.Start-prevline.End < mstosplit:
                    middle = prevline.End+((line.Start-prevline.End)//2)
                    prevline.End = middle-mstosplit//2
                    line.Start = middle+mstosplit//2 + mstosplit % 2

    def shift(self, mstoshift, which_time='both', first_line=1, last_line=0):

        # Shifts lines, first line and last line (included)
        # By default changes from line 1 to last line

        if last_line == 0 or last_line > len(self.lines):
            last_line = len(self.lines)

        first_line = max(1, first_line)

        if which_time == 'both':
            for line in self.lines[first_line-1:last_line]:
                line.Start += mstoshift
                line.End += mstoshift

        elif which_time == 'start':
            for line in self.lines[first_line-1:last_line]:
                line.Start += mstoshift

        elif which_time == 'end':
            for line in self.lines[first_line-1:last_line]:
                line.End += mstoshift

    def align_dialog(self, video_width=0, video_height=0,
                     prefixes=('-', '–', '—'), style_suffix=' - alignedL'):
        ''' Takes the subtitles whose lines all start with -, –, —,
            and aligns them to the left, using ASS styles.

            ARGS:
                video_width, video_height: required, but will try to get them
                    from a .ass file's [Script Info] if not specified.
                prefixes: list, tuple of expressions that introduce dialogue.
                    defaut is ('-', '–', '—').
                style_suffix: this is added to the current style name
                    to create the new, left aligned style.
                    By default it would create 'Stylename - alignedL'.

            NOTE: Requires a font, which is taken from the .ass file.
            If no font is found it uses the default (Arial, 20p)

            NOTE: Does not work if saved as .srt file
            since they don't support positioning or alignment.

            NOTE: If '{style} - alignedL' already exists as a style it will use it.
            '''

        try:
            video_width = video_width or int(self.sections['Script Info']['PlayResX'])
            video_height = video_height or int(self.sections['Script Info']['PlayResY'])

        except Exception:
            raise Exception('Could not extract video resolution from subtitle file.\n'
                            'Are you sure it\'s a .ass file linked to a video?')

        for line in self.lines:
            if '\\N' in line.Text:
                newtext = line.Text.split('\\N')

                for newline in newtext:
                    if not newline.startswith(prefixes):
                        break
                else:

                    for style in self.styles:
                        if style.Name == line.Style:

                            # Checks if style already exists
                            for style_already_exists in self.styles:
                                if style_already_exists.Name == f'{line.Style}{style_suffix}':
                                    style_to_use = style_already_exists
                                    break

                            else:
                                # Creates new style
                                style_to_use = deepcopy(style)
                                self.styles.append(style_to_use)
                                style_to_use.Name = f'{line.Style}{style_suffix}'

                                # 7, 8, 9 = TOP aligned
                                # 4, 5, 6 = MID aligned
                                # 1, 2, 3 = BOT aligned

                                # 7, 4, 1 = LEFT aligned

                                if int(style_to_use.Alignment) >= 7:
                                    style_to_use.Alignment = '7'
                                elif int(style_to_use.Alignment) >= 4:
                                    style_to_use.Alignment = '4'
                                else:
                                    style_to_use.Alignment = '1'

                    # Info needed to calculate width of line
                    # '{\pos}' overrides MarginL and MarginR
                    # so we dont have to edit or import them

                    Alignment = int(style_to_use.Alignment)
                    Fontname = style_to_use.Fontname
                    Fontsize = int(style_to_use.Fontsize)
                    Spacing = int(style_to_use.Spacing)
                    Bold = style_to_use.Bold
                    Italic = style_to_use.Italic

                    # MarginV from line overrides the style's MarginV
                    # But if the line's MarginV is 0, we use the style's

                    if line.MarginV == '0':
                        MarginV = int(style_to_use.MarginV)
                    else:
                        MarginV = line.MarginV

                    if Alignment == 7:
                        y = MarginV
                    elif Alignment == 4:
                        y = video_height / 2
                    else:
                        y = video_height - MarginV

                    # Check for the widest line
                    # and use that as a basis for centering the subtitle

                    font = get_font(font=Fontname, bold=Bold, italic=Italic)
                    widths = []

                    for newline in newtext:
                        widths.append(check_text_width(
                            text=newline, font=font,
                            size=Fontsize, spacing=Spacing))

                    widths.sort(reverse=True)
                    biggest_width = widths[0]

                    x = video_width/2 - biggest_width/2

                    outputline = f'{{\\pos({x},{y})}}'

                    # Rewrite the text

                    for newline in newtext:
                        outputline += f'{newline}\\N'

                    line.Text = outputline[:-2]     # Removes the last \N
                    line.Style = style_to_use.Name

    def single_lines_to_top(self):
        ''' Takes subtitles that are in a single line
            and makes that line be the top line (default is bottom)

            NOTE: Does not work if saved as .srt file
            since they don't support positioning or empty lines.
        '''

        # Adds a new line with a space in it
        # The space is actually an EM QUAD (U+2001)
        # since some software automatically deletes other spaces.
        for line in self.lines:
            if '\\N' not in line.Text:
                line.Text += '\\N '

    def remove_style(self, style, replacement='Default'):
        ''' Removes style and applies 'replacement'
            to the lines that used it.
            ARGS:
                style: must be a Style instance
                replacement: must be a string, the name of the style
        '''
        if not self.find_style(replacement):
            replacement = 'Default'

        for line in self.lines:
            if line.Style == style.Name:
                line.Style = replacement

        for i, s in enumerate(self.styles):
            if s == style:
                self.styles.pop(i)
                break

    def find_style(self, name):
        '''Returns the instance of Style with the name 'name'.'''
        for style in self.styles:
            if style.Name == name:
                return style


class AssSubFile(SubFile):

    def interpret(self, path, enc='utf-8-sig'):

        # Particularities in .ass files:
        line_pattern = Ass.line_pattern
        style_pattern = Ass.style_pattern
        section_pattern = Ass.section_pattern
        key_pattern = Ass.key_pattern
        cprefixes = Ass.comment_prefixes

        sectname = 'Script Info'    # Defaults to [Script Info]

        with open(path, encoding=enc) as text:

            for line in text:

                if line.lstrip().startswith(cprefixes):
                    # Ignore commented lines
                    continue
                # Check if the line is a section
                q = section_pattern.match(line)

                if q:
                    sectname = q.group(1)
                    # If 2 sections are called the same
                    # it only keeps the 2nd one
                    if sectname != 'Events' and sectname != 'V4+ Styles':
                        self.sections[sectname] = dict()

                    continue

                if sectname == 'Events':                # Interpret it as a subtitle
                    sl = line_pattern.search(line)      # (ignores Format line)
                    if sl:
                        li = list(sl.groups())
                        li[2] = Ass.get_time(li[2])
                        li[3] = Ass.get_time(li[3])
                        self.lines.append(SubLine(li))

                elif sectname == 'V4+ Styles':          # Interpret line as a style
                    sl = style_pattern.search(line)     # (ignores Format line)
                    if sl:
                        self.styles.append(Style(sl.groups()))

                else:
                    q = key_pattern.match(line)

                    if q:
                        name, val = q.group(1, 2)
                        self.sections[sectname][name] = val


class SrtSubFile(SubFile):

    def interpret(self, path):
        # Reads all subtitle lines from an srt file
        # Times get turned to ms

        with open(path) as f:

            replacedict = Srt.tags_to_ass
            # To replace .srt tags into .ass formatting

            line_pattern = Srt.line_pattern
            # Gets the pattern of .srt files

            whole_file = f.read()

            for match in line_pattern.finditer(whole_file):

                for key, value in replacedict.items():
                    text = match.group(3).replace(key.lower(), value)
                    # .lower() just in case there's <B> in caps or w/e

                text = Srt.srt_colors.sub(
                    Srt.colors_to_ass, text)
                # Turns colors to ass formatting
                # <font color=#123456> to {\c&H563412}
                # also changes RGB (srt) to BGR (ass)

                self.lines.append(SubLine(
                    Start=Srt.get_time(match.group(1)),
                    End=Srt.get_time(match.group(2)),
                    Text=text))
                # Gives a default style to avoid problems
                self.styles.append(Style())


class Style:

    style_df = Ass.style_df     # Dictionary with default values

    # Style takes either a list of variables (23 or less).
    # Or takes keywords for variables.
    # e.g. Style(Name='TestStyle') will make every variable the default except for Name.

    def __init__(self, style_as_list='', **kwargs):

        # Copies the defaults so we can overwrite them
        attributes = self.style_df.copy()

        if style_as_list:
            # Overwrites defaults with new values from list
            d = dict(zip(self.style_df.keys(), style_as_list))
            attributes.update(d)

        else:
            # Overwrites defaults with whatever came from kwargs
            attributes.update(
                (k, kwargs[k]) for k in attributes.keys() & kwargs.keys())

        # Sets all of the values as object attributes if the keys are valid
        for arg, val in attributes.items():
            setattr(self, arg, val)

    def to_line(self):  # turns the style into a .ass line
        # Gets self's attributes, if they are actual style variables
        get_attrs = (getattr(self, item) for item in self.style_df.keys())
        
        return f'Style: {",".join(get_attrs)}\n'


class SubLine:
    ''' Line of subtitles, which contains start time, end time, text
    and (optional) extra variables for advanced subtitle formats.

    Times (Start and End) are saved in ms '''

    sub_df = Ass.sub_df

    def __init__(self, sub_as_list='', **kwargs):

        attributes = self.sub_df.copy()     # Gets the defaults

        if sub_as_list:
            # Overwrites defaults with whatever came from list
            d = dict(zip(self.sub_df.keys(), sub_as_list))
            attributes.update(d)

        else:
            # Overwrites defaults with whatever came from kwargs
            attributes.update((k, kwargs[k]) for k in attributes.keys() & kwargs.keys())

        for arg, val in attributes.items():
            setattr(self, arg, val)     # and sets all of the values as object attributes

    def line_to_ass(self):
        # pylint: disable=maybe-no-member
        return (
            f'{self.Type}: {self.Layer},'
            f'{Ass.turn_to_time(self.Start)},'
            f'{Ass.turn_to_time(self.End)},'
            f'{self.Style},{self.Name},{self.MarginL},{self.MarginR},'
            f'{self.MarginV},{self.Effect},{self.Text}\n'
        )

    def line_to_srt(self, i):
        # pylint: disable=maybe-no-member

        replacedict = Ass.tags_to_srt

        for key, value in replacedict.items():
            text = self.Text.replace(key, value)

        text = Ass.ass_colors.sub(Ass.colors_to_srt, text)

        return (
            f'{i}\n'
            f'{Srt.turn_to_time(self.Start)}'
            f' --> '
            f'{Srt.turn_to_time(self.End)}\n' +
            '{text}\n\n'.format(text=text)
        )

    def shift(self, amount_start, amount_end):
        # pylint: disable=maybe-no-member
        self.Start += amount_start
        self.End += amount_end


if __name__ == '__main__':
    print('Don\'t run this! Use test.py if you want to test out the library.')
