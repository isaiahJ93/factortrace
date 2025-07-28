# Find and fix the CSS in generate_html_report
import fileinput
for line in fileinput.input('xpath31/validator.py', inplace=True):
    if 'font-family' in line and 'body {' in line:
        print('                body { font-family: Arial, sans-serif; margin: 20px; }')
    else:
        print(line, end='')
