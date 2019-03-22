# Splits subtitles

    # Note: the prefix of all subtitles is "Dialogue: "
    # if it doesn't have that, programs don't recognize the subtitles
    # so no need to store it, just print string "Dialogue: " before subtitle

import tkinter as tk
from tkinter import filedialog
import string
import sys
import re
import datetime


def subtool():

    root = tk.Tk()
    root.withdraw()

    global attributes_lines

    file_path = filedialog.askopenfilename()

    formato = file_path[-4:]

    if formato == '.ass':
        names = ['layer','start','end','style','name',
        'marginl','marginr','marginv','effect','text']
        sub_file = open(file_path, 'r')
    else:
        close('Format not accepted.')

    line='hola'

    introlines = []

    while line:
        line = sub_file.readline()
        introlines.append(line)
        if line == '[Events]\n':
            line = sub_file.readline()
            introlines.append(line)
            break


    time = datetime.datetime.now() # Just to time it

    attributes_lines = interpret(sub_file, formato)

    sub_file.close()

    # interpet(formato) creates attributes_lines = a list of every attribute of every line

        ## TYPES OF ACTIONS ##

    # delete whitespace, punctuation, numbers at beginning of subtitle
    delete_whitespace = 1       # 0 = checks but doesn't delete
    delete_punctuation = 1 
    check_numbers = 0           # 0 = doesn't even check for numbers,
                                # 1 = check and tells but doesn't delete
                                # 2 = deletes them


    # moving all subs backwards (<0) or forwards (>0) in ms
    move_by = 0

    # splitting subs
    split_type = "split"
    split_type = "move_first"
    split_type = "move_second"
    # mstosplit = 0 -> don't split
    mstosplit = 17
    # characters per second max = 0 -> don't check them
    cpsmax = 20
    ignore_spaces = 1
    ignore_punctuation = 1

        ## CHANGES / CHECKS TO VALUES ##

    if mstosplit > 0:
        split_subs(mstosplit, split_type)
    
    if move_by != 0:
        move_splits(move_by)

    if cpsmax > 0:
        excess_cps = check_cps(cpsmax,ignore_spaces,ignore_punctuation)

    checked_chars = check_beginning(delete_whitespace, delete_punctuation, check_numbers)
    deleted_chars = checked_chars[1]
    checked_chars = checked_chars[0]

        ## WRITE FILE ##

    output = open('outputfile.ass','w')

    for i in range(len(introlines)):
        output.write(introlines[i])
    for i in range(len(attributes_lines)):
        sub_line = ''
        for j in range(1,len(names)):
            sub_line += ','
            sub_line += attributes_lines[i][names[j]]
        output.write(f"Dialogue: {attributes_lines[i][names[0]]},{sub_line}\n")
    
    output.close()
    
        ## PRINT INFO ##

    print(f'Succesfully written in {datetime.datetime.now()-time} seconds.')

    # cps checker

    # if they are more than 15, say number of lines, else print which lines they are
    if len(excess_cps) > 15:
        print(f'{len(excess_cps)} lines are over {cpsmax} characters per second.')
    elif len(excess_cps) > 1:
        print('Lines number ', end="")
        for i in excess_cps[:-2]:
            print(f'{i}, ', end="")
        print(f'{excess_cps[-2]} and {excess_cps[-1]} ', end="")
        print(f'are over {cpsmax} characters per second.')
    elif len(excess_cps) > 0:
        print(f'Line number {excess_cps[0]} is over {cpsmax} characters per second.')
    else:
        print(f'All lines are under {cpsmax} characters per second.')

    # introductory characters

    # checkers
    # if they are more than 15, say number of lines, else print which lines they are
    if len(checked_chars) > 15:
        print(f'{len(checked_chars)} lines with incorrect starting characters have been found.')
    elif len(checked_chars) > 1:
        print('Lines number ', end="")
        for i in checked_chars[:-2]:
            print(f'{i}, ', end="")
        print(f'{checked_chars[-2]} and {checked_chars[-1]} ', end="")
        print(f'have incorrect starting characters.')
    elif len(checked_chars) > 0:
        print(f'Line number {checked_chars[0]} has incorrect starting characters.')
    else:
        print(f'All lines have correct starting characters.')

    # deleters
    if deleted_chars != []:
        if len(deleted_chars) > 15:
            print(f'{len(deleted_chars)} lines with incorrect starting characters have been fixed.')
        elif len(deleted_chars) > 1:
            print('Lines number ', end="")
            for i in deleted_chars[:-2]:
                print(f'{i}, ', end="")
            print(f'{deleted_chars[-2]} and {deleted_chars[-1]} ', end="")
            print(f"'s incorrect starting characters have been fixed.")
        elif len(deleted_chars) > 0:
            print(f"Line number {deleted_chars[0]}'s incorrect starting characters have been fixed.")
        else:
            print(f'No starting characters have been fixed.')
    

        ## END ##



def close(message):
    print(message)
    sys.exit()


# returns all attributes in a list of lists which go from 0 to formato
def interpret(sub_file, formato):

    attributes_lines = []

    if formato == ".ass":

        line = sub_file.readline()
        line_pattern = re.compile (r"Dialogue: (\d),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*)")
        names = ['layer','start','end','style','name',
            'marginl','marginr','marginv','effect','text']
            
        while line:
            
            search_line = line_pattern.search(line)

            attributes = dict()

            for n in range(10):
                attributes[names[n]] = search_line.group(n+1)

            attributes_lines.append(attributes)
        
            line = sub_file.readline()
            
        print(attributes_lines)
        return attributes_lines
    
    else:

        close('Format not valid')

# returns time in miliseconds
def get_time(time):
    miliseconds = int(time[-2:])
    seconds = int(time[-5:-3])
    minutes = int(time[-8:-6])
    hours = int(time[:time.index(":")])
    return miliseconds+(100*(seconds+(60*(minutes+(60*hours)))))

# takes miliseconds
# and returns "hours:minutes:seconds:miliseconds"
def turn_to_time(time):
    b=time//100//60
    return f'{b//60}:{b%60:02}:{time//100%60:02}.{time%100:02}'

# Types of splitting subtitles:
# "move_first": moves the ending time of the first subtitle back
# "move_second": moves the starting time of the second subtitle forward
# "split": each subtitle is moved half of mstosplit (if odd number second sub will take +1ms)
def split_subs(mstosplit, split_type):

    global attributes_lines

    # this is just so the first sub doesn't get moved
    end = -get_time(attributes_lines[0]['start'])-mstosplit

    if split_type == "move_second":

        for i in range(len(attributes_lines)):

            start = get_time(attributes_lines[i]['start'])
            if start-end < mstosplit:
                attributes_lines[i]['start'] = turn_to_time(end+mstosplit)

            end = get_time(attributes_lines[i]['end'])
    
    if split_type == "move_first":

        for i in range(len(attributes_lines)):

            start = get_time(attributes_lines[i]['start'])
            if start-end < mstosplit:
                attributes_lines[i-1]['end'] = turn_to_time(start-mstosplit)

            end = get_time(attributes_lines[i]['end'])
    
    if split_type == "split":

        ## try saving things as variables or not
        ## to test the fastest way

        for i in range(len(attributes_lines)):

            start = get_time(attributes_lines[i]['start'])
            if start-end < mstosplit:
                middle = end+((start-end)//2)
                attributes_lines[i-1]['end'] = turn_to_time(middle-mstosplit//2)
                attributes_lines[i]['start'] = turn_to_time(middle+mstosplit//2+mstosplit%2)

            end = get_time(attributes_lines[i]['end'])

    return 1

def move_splits(move_by):
    for i in range(len(attributes_lines)):
        attributes_lines[i]['start'] = turn_to_time(get_time(attributes_lines[i]['start'])+move_by)
        attributes_lines[i]['end'] = turn_to_time(get_time(attributes_lines[i]['end'])+move_by)
    return 1

def check_cps(cpsmax, ignore_spaces, ignore_punctuation):
    excess_cps = []
    unwanted_characters = "\\N"

    if ignore_punctuation == 1:
        unwanted_characters += string.punctuation
    if ignore_spaces == 1:
        unwanted_characters += string.whitespace

    for i in range(len(attributes_lines)):
        if (len(attributes_lines[i]['text'].translate(str.maketrans("","",unwanted_characters)))
        / (get_time(attributes_lines[i]['end'])-get_time(attributes_lines[i]['start']))*100) > cpsmax:
            excess_cps.append(i+1)
    return excess_cps


def check_beginning(delete_whitespace, delete_punctuation, check_numbers):

    deleted_chars = []
    checked_chars = []

    # deleters

    if delete_whitespace == 1 or delete_punctuation == 1 or check_numbers == 2:

        unwanted_characters = ""
        
        if delete_whitespace == 1:
            unwanted_characters += string.whitespace
        if delete_punctuation == 1:
            unwanted_characters += ',!?`´:;/\\'
        if check_numbers == 2:
            unwanted_characters += '1234567890'

        for i in range(len(attributes_lines)):
            newline = attributes_lines[i]['text'].lstrip(unwanted_characters)
            if attributes_lines[i]['text'] != newline:
                attributes_lines[i]['text'] = newline
                deleted_chars.append(i+1)

    # checkers
    
    if delete_whitespace == 0 or delete_punctuation == 0 or check_numbers == 1:

        unwanted_characters = ""

        if delete_whitespace == 0:
            unwanted_characters += string.whitespace
        if delete_punctuation == 0:
            unwanted_characters += ',!?`´:;/\\'
        if check_numbers == 1:
            unwanted_characters += '1234567890'

        for i in range(len(attributes_lines)):
            newline = attributes_lines[i]['text'].lstrip(unwanted_characters)
            if attributes_lines[i]['text'] != newline:
                checked_chars.append(i+1)
        
        
    return [checked_chars, deleted_chars]
    

if __name__ == '__main__':
    subtool()