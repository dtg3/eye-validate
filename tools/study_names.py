import os
from zipfile import ZipFile

for folder, subfolders, files in os.walk(os.path.join('data_set')):
    for file in files:
        if file.endswith('.json'):
            filepath = os.path.join(folder, file)
            filename = os.path.basename(filepath)[:-13]
            print(filename)