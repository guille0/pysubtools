from tkinter import filedialog
import pysubtools


def main():

    f = pysubtools.load_sub(filedialog.askopenfilename())

    # file.sections['Script Info']['Title'] = 'Changing the title'
    # f.remove_line(3)
    # f.separate()
    f.shift(20)
    # f.align_dialog()
    # f.single_lines_to_top()

    output = filedialog.asksaveasfilename(title='Select file',
             filetypes=(('ass files', '*.ass'),('srt files', '*.srt')))

    if output:
        f.save(output)
        print(f'Saved to {output}')

if __name__ == '__main__':
    main()