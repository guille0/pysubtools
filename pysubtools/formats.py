import re


class Srt:

    time = r"[,.:，．。：]"
    timestamp = time.join([r"\d+"] * 4)
    number = r"\d+"
    proprietary = r"[^\r\n]*"
    text = r".*?"
    end = r"\r?\n"

    line_pattern = re.compile(
        rf"{number}\s*{end}({timestamp})"               # Number and 1st time
        rf" +-[ -]> "                                   # Separator (-->)
        rf"+({timestamp}) ?{proprietary}{end}({text})"  # 2nd time and text
        # Now checking where the text should end
        rf"(?:{end}|\Z)(?:{end}|\Z|(?=(?:{number}\s*{end}{timestamp})))"
        rf"(?=(?:{number}\s*{end}{timestamp}|\Z))", re.DOTALL)

    time_pattern = re.compile(time.join([r"(\d+)"] * 4))

    srt_colors = re.compile(r'<font color=#(.{2})(.{2})(.{2})>')

    tags_to_ass = {
            '\n'        :   '\\N',
            '<b>'       :   '{\\b1}',
            '</b>'      :   '{\\b0}',
            '<i>'       :   '{\\i1}',
            '</i>'      :   '{\\i0}',
            '<u>'       :   '{\\u1}',
            '</u>'      :   '{\\u0}',
            '</font>'   :   '{\\c&HFFFFFF&}'
            # </font> = go to default font, which is white in .srt files
        }

    @staticmethod
    def colors_to_ass(color):
        # for some reason .ass files save color as Blue Green Red
        # so we have to swap these
        return f'{{\\c&H{color.group(3)}{color.group(2)}{color.group(1)}&}}'

    @classmethod
    def get_time(cls, time):
        '''returns time in miliseconds
           from '0:00:00,000' '''
        sl = cls.time_pattern.search(time)
        return(int(sl.group(4))+(1000*(int(sl.group(3)) +
               (60*(int(sl.group(2))+(60*int(sl.group(1))))))))

    @staticmethod
    def turn_to_time(time):
        ''' Takes miliseconds
        and returns "hours:minutes:seconds,miliseconds"
        with padding (:03 means pad with 0s if it's less than 3 digits)'''
        b = time//1000//60
        return f'{b//60:02}:{b%60:02}:{time//1000%60:02},{time%1000:03}'


class Ass:

    style_intro = ('[V4+ Styles]\nFormat: Name, Fontname, Fontsize,'
                   'PrimaryColour, SecondaryColour, OutlineColour, BackColour,'
                   'Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY,'
                   'Spacing, Angle, BorderStyle, Outline, Shadow,'
                   'Alignment, MarginL, MarginR, MarginV, Encoding\n')

    style_df = {'Name': 'Default', 'Fontname': 'Arial', 'Fontsize': '20',
                'PrimaryColour': '&H00FFFFFF', 'SecondaryColour': '&H000000FF',
                'OutlineColour': '&H00000000', 'BackColour': '&H00000000',
                'Bold': '0', 'Italic': '0', 'Underline': '0', 'StrikeOut': '0',
                'ScaleX': '100', 'ScaleY': '100', 'Spacing': '0', 'Angle': '0',
                'BorderStyle': '1', 'Outline': '2', 'Shadow': '2', 'Alignment': '2',
                'MarginL': '10', 'MarginR': '10', 'MarginV': '10', 'Encoding': '1'}

    sub_intro = ('\n[Events]\nFormat: Layer, Start, End, Style,'
                 'Name, MarginL, MarginR, MarginV, Effect, Text\n')

    sub_df = {'Type': 'Dialogue', 'Layer': '0', 'Start': '0:00:00.00',
              'End': '0:00:05.00', 'Style': 'Default',
              'Name': '', 'MarginL': '0', 'MarginR': '0',
              'MarginV': '0', 'Effect': '', 'Text': ''}

    tags_to_srt = {
            '\\N'       :   '\n',
            '{\\b1}'    :   '<b>',
            '{\\b0}'    :   '</b>', 
            '{\\i1}'    :   '<i>',
            '{\\i0}'    :   '</i>',  
            '{\\u1}'    :   '<u>',
            '{\\u0}'    :   '</u>'
        }

    atr = ',(.*?)'

    line_pattern = re.compile(rf"(Dialogue|Comment): (.*?){atr*9}\n")
    time_pattern = re.compile(r"(\d+):(\d+):(\d+).(\d+)")
    style_pattern = re.compile(rf"Style: (.*?){atr*22}\n")
    section_pattern = re.compile(r"^\[(.*?)\]$")
    key_pattern = re.compile(r"(.*?)\s*:\s*(.*)$")
    comment_prefixes = (';', '#')
    ass_colors = re.compile(r'{\\c&H(.{2})(.{2})(.{2})&}')

    @staticmethod
    def colors_to_srt(color):
        # for some reason .ass files save color as Blue Green Red
        # so we have to swap these
        return f'<font color=#{color.group(3)}{color.group(2)}{color.group(1)}>'

    @classmethod
    def get_time(cls, time):
        '''returns time in miliseconds
           from '0:00:00.00' '''
        sl = cls.time_pattern.search(time)

        # 10* at the beginning because .ass only gives 2 digits,
        # so have to turn into miliseconds
        return (10*(int(sl.group(4))+(100*(int(sl.group(3)) +
                (60*(int(sl.group(2))+(60*int(sl.group(1)))))))))

    @staticmethod
    def turn_to_time(time):
        ''' Takes miliseconds
        and returns "hours:minutes:seconds.centiseconds"
        with padding (:02 means pad with 0s if it's less than 2 digits)'''

        # Aegisub floors the number when turning 3 digits into 2,
        # so i'll do the same. e.g. 119 turns to 11, not 12
        time = time//10

        b = time//100//60

        return f'{b//60}:{b%60:02}:{time//100%60:02}.{time%100:02}'
