import formats
import re
from pathlib import Path
from tkinter import filedialog, Tk
from copy import deepcopy
from PIL import ImageFont
from matplotlib import font_manager

import logging

# Method ideas:
# 
# Maybe some cool effects for subtitle styles (turn them 3D or something cool)
# 
# Correct errors in text?
# 
# Add SSA files? easy but not needed really

# TODO Add trys and excepts to check for common errors

def main():

    logging.basicConfig(filename='debug.log', level=logging.INFO)

    asssub1 = load_sub(filedialog.askopenfilename(defaultextension=".srt"))

    # asssub1.sections['Script Info']['Title'] = 'Fuckdick'
    asssub1.align_dialog()
    # asssub1.single_lines_to_top()

    asssub1.shift(300, which_time='both', first_line=10)

    # root = Tk()
    # root.filename = filedialog.asksaveasfilename(title = "Select file",
    #                 filetypes = (("jpeg files","*.ass"),("all files","*.*")))

    savedfile = '/home/guille/Bureau/outputfilee.ass'
    if not asssub1.save(savedfile):
        print(f'didnt save')
    else:
        print(f'Saved to {savedfile}')


def load_sub(path):

    if Path(path).suffix == '.ass':
        subtitle_file = AssSubFile()

    if Path(path).suffix == '.srt':
        subtitle_file = SrtSubFile()

    if subtitle_file:
        subtitle_file.interpret(path)
        return subtitle_file


def get_font(font, bold='0', italic='0'):

        if bold == '0':
            weight = 400    # Not bold
        else:
            weight = 700    # Bold

        if italic == '0':
            style = 'normal'
        else:
            style = 'italic'

        properties = font_manager.FontProperties(
            family=font, style=style, weight=weight)

        fontsearch = font_manager.findfont(properties)

        # LOGS HERE
        logging.info(f"Searching for font '{font}', of style {style} and weight {weight}.")
        logging.info(f"Using font {fontsearch}.")

        return fontsearch


def check_text_width(text, font, size, spacing=0):

    font_obj = ImageFont.truetype(font=font, size=int(size/1.125))

    spacing = (len(text)-1)*(spacing)

    width = font_obj.getsize(text)[0]

    logging.info(f"Width: {width}. Text: {text}.")

    return width+spacing


class SubFile:

    def __init__(self):

        self.sections = dict()
        self.styles = []
        self.lines = []

    def __str__(self):
        return (
                f"Information on subtitle file:\n"
                f"Individual subtitles: {len(self.lines)}\n"
                f"Styles: {len(self.styles)}\n"
                f"First line: {self.lines[0].Text}\n"
                f"Last line: {self.lines[-1].Text}"
                )

    def save(self, path):

        # Writes the subtitles into the file 'path'

        if Path(path).suffix == '.ass':
            with open(path, 'w') as f:

                # Write the introductory lines (ignorable if there's none)
                for name, section in self.sections.items():
                    f.write(f'[{name}]\n')
                    for key, value in section.items():
                        f.write(f'{key}: {value}\n')
                    f.write('\n')
                    # Empty line at the end of each section

                # Write the styles
                f.write(formats.Ass.style_intro)

                if len(self.styles) == 0:
                    # Adds default style if there's none
                    self.styles.append(Style())

                for st in self.styles:
                    f.write(st.to_line())

                # Write the subtitles
                f.write(formats.Ass.sub_intro)

                for line in self.lines:
                    f.write(line.line_to_ass())

            return 1

        if Path(path).suffix == '.srt':

            with open(path, 'w') as f:

                for i, line in enumerate(self.lines):
                    f.write(line.line_to_srt(i+1))

            return 1

    def removeline(self, line_number):

        # Simple method to remove a subtitle

        self.lines.pop(line_number)

    def separate(self, mstosplit, split_type='move_second'):

        # If subtitles are at a distance of less than 'mstosplit',
        # it separates them by 'mstosplit' miliseconds

        # This is just so the first sub doesn't get moved:
        # end = -self.lines[0].Start-mstosplit
        # end = self.lines[0].End

        if split_type == "move_second":

            for line in self.lines:

                start = line.Start
                if start-end < mstosplit:
                    line.Start = end+mstosplit

                end = line.End

        if split_type == "move_first":

            for prevline, line in zip(self.lines, self.lines[1:]):

                if line.Start-prevline.End < mstosplit:
                    prevline.End = line.Start-mstosplit

        if split_type == "split":

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

    def align_dialog(self, prefixes=('-', '–', '—'),
                     style_suffix=' - alignedL'):
        ''' Takes the subtitles whose lines all start with -, –, —,
            and aligns them to the left, using ASS styles.

            ARGS: 
                prefixes: list, tuple of expressions that introduce dialogue.
                          defaut is ('-', '–', '—').
                style_suffix: this is added to the current style name
                              to create the new, left aligned style.
                              default is ' - alignedL'.
                              which would give 'Style - alignedL'.

            NOTE: Does not work if saved as .srt file
            since they don't support positioning or alignment.

            NOTE: If {stylename} + ' - alignedL' already exists
            it will assume it's correct and use it. '''

        for line in self.lines:
            if '\\N' in line.Text:
                newtext = line.Text.split('\\N')

                for newline in newtext:
                    if not newline.startswith(prefixes):
                        break
                else:

                    # We need the video resolution to position the text

                    videow = int(self.sections['Script Info']['PlayResX'])
                    videoh = int(self.sections['Script Info']['PlayResY'])

                    for style in self.styles:
                        if style.Name == line.Style:

                            # Checks if style already exists

                            for style_already_exists in self.styles:
                                if style_already_exists.Name == f'{line.Style}{style_suffix}':
                                    style_to_use = style_already_exists
                                    break

                            else:   # Creates new style

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

                    Alignment = int(style_to_use.Alignment)
                    Fontname = style_to_use.Fontname
                    Fontsize = int(style_to_use.Fontsize)
                    Spacing = int(style_to_use.Spacing)
                    MarginV = int(style_to_use.MarginV)
                    Bold = style_to_use.Bold
                    Italic = style_to_use.Italic

                    # 'pos' overrides MarginL, MarginR and MarginV,
                    # so we dont have to edit or import them

                    # MarginV from line overrides the style's MarginV
                    # But if the line's MarginV is 0, we take the style's

                    if line.MarginV != '0':
                        MarginV = line.MarginV

                    if Alignment == 7:
                        y = MarginV
                    elif Alignment == 4:
                        y = videoh / 2
                    else:
                        y = videoh - MarginV

                    # Check for the widest line
                    # and use that as a basis for centering the subtitle
                    # Have a try except for not getting the font #TODO
                    font = get_font(font=Fontname, bold=Bold, italic=Italic)
                    widths = []

                    for newline in newtext:
                        widths.append(check_text_width(
                            text=newline, font=font,
                            size=Fontsize, spacing=Spacing))

                    widths.sort(reverse=True)
                    biggest_width = widths[0]

                    logging.info(f"Picked {biggest_width}"
                    f"as the longest of {widths}.")

                    x = videow/2 - biggest_width/2

                    outputline = f'{{\\pos({x},{y})}}'

                    # Rewrite the text

                    for newline in newtext:
                        outputline += f"{newline}\\N"

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
        line_pattern = formats.Ass.line_pattern
        style_pattern = formats.Ass.style_pattern
        section_pattern = formats.Ass.section_pattern
        key_pattern = formats.Ass.key_pattern
        cprefixes = formats.Ass.comment_prefixes

        sectname = 'Script Info'    # Defaults to [Script Info]

        with open(path, encoding=enc) as text:

            for line in text:

                if line.lstrip().startswith(cprefixes):
                    # Ignore commented lines
                    continue

                q = section_pattern.match(line)         # Check if the line is a section

                if q:
                    sectname = q.group(1)               # If 2 sections are called the same
                    # it only keeps the 2nd one
                    if sectname != 'Events' and sectname != 'V4+ Styles':
                        self.sections[sectname] = dict()

                    continue

                if sectname == 'Events':                # Interpret it as a subtitle
                    sl = line_pattern.search(line)      # (ignores Format line)
                    if sl:
                        li = list(sl.groups())
                        li[2] = formats.Ass.get_time(li[2])
                        li[3] = formats.Ass.get_time(li[3])
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

            replacedict = formats.Srt.tags_to_ass
            # To replace .srt tags into .ass formatting

            line_pattern = formats.Srt.line_pattern
            # Gets the pattern of .srt files

            whole_file = f.read()

            for match in line_pattern.finditer(whole_file):

                for key, value in replacedict.items():
                    text = match.group(3).replace(key.lower(), value)
                    # .lower() just in case there's <B> in caps or w/e

                text = formats.Srt.srt_colors.sub(
                    formats.Srt.colors_to_ass, text)
                # Turns colors to ass formatting
                # <font color=#123456> to {\c&H563412}
                # also changes RGB (srt) to BGR (ass)

                self.lines.append(SubLine(
                    Start=formats.Srt.get_time(match.group(1)),
                    End=formats.Srt.get_time(match.group(2)),
                    Text=text))


class Style:

    style_df = formats.Ass.style_df     # Dictionary with default values

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

    sub_df = formats.Ass.sub_df

    def __init__(self, sub_as_list='', **kwargs):

        attributes = self.sub_df.copy()     # Gets the defaults

        if sub_as_list:
            # Overwrites defaults with whatever came from list
            d = dict(zip(self.sub_df.keys(), sub_as_list))
            attributes.update(d)

        else:
            # Overwrites defaults with whatever came from kwargs
            attributes.update( (k, kwargs[k])
            for k in attributes.keys() & kwargs.keys())     
            

        for arg, val in attributes.items():
            setattr(self, arg, val)     # and sets all of the values as object attributes

    def line_to_ass(self):
        # pylint: disable=maybe-no-member
        return (
            f"{self.Type}: {self.Layer},"
            f"{formats.Ass.turn_to_time(self.Start)},"
            f"{formats.Ass.turn_to_time(self.End)},"
            f"{self.Style},{self.Name},{self.MarginL},{self.MarginR},"
            f"{self.MarginV},{self.Effect},{self.Text}\n"
        )

    def line_to_srt(self, i):
        # pylint: disable=maybe-no-member

        replacedict = formats.Ass.tags_to_srt

        for key, value in replacedict.items():
            text = self.Text.replace(key, value)

        text = formats.Ass.ass_colors.sub(formats.Ass.colors_to_srt, text)

        return (
            f"{i}\n"
            f"{formats.Srt.turn_to_time(self.Start)}"
            f" --> "
            f"{formats.Srt.turn_to_time(self.End)}\n" +
            "{text}\n\n".format(text=text)
        )

    def shift(self, amount_start, amount_end):
        # pylint: disable=maybe-no-member
        self.Start += amount_start
        self.End += amount_end


if __name__ == '__main__':
    main()