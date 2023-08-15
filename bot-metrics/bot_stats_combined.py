import os
import sys
from glob import glob

if len(sys.argv) > 2:
    print('Only one argument folder allowed')
else:
    pass

path_to_bot_folder = os.path.join(os.getcwd(), sys.argv[1])
if os.path.exists(path_to_bot_folder):
    result = [y for x in os.walk(path_to_bot_folder) for y in glob(os.path.join(x[0], '*.py'))]
    stats = {}
    stats['input_text'] = 0
    stats['list_selection'] = 0
    stats['click_element'] = 0
    stats['get_attribute'] = 0
    stats['loops'] = 0
    stats['condition'] = 0
    total_count = 0
    for file in result:
        a = open(file).readlines()
        count = len(a)
        total_count += count
        for b in a:
            if 'input_text' in b:
                stats['input_text'] += 1
            elif 'click_element' in b:
                stats['click_element'] += 1
            elif 'get_attribute' in b:
                stats['get_attribute'] += 1
            elif 'for' in b or 'while' in b:
                stats['loops'] += 1
            elif 'if' in b:
                stats['condition'] += 1
            elif 'select_from_list' in b:
                stats['list_selection'] += 1
else:
    print('That folder does not exists')

print(f'Total lines: {total_count}')
print(f'Actions:')
print(f'* Input text: {stats["input_text"]}')
print(f'* Dropdown selections: {stats["list_selection"]}')
print(f'* Click element: {stats["click_element"]}')
print(f'* Get attribute: {stats["get_attribute"]}')
print(f'* Loops: {stats["loops"]}')
print(f'* Condition statements: {stats["condition"]}')
