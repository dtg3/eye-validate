import os
from zipfile import ZipFile

for folder, subfolders, files in os.walk(os.path.join('data_set')):
    for file in files:
        if file.endswith('.json'):
            filepath = os.path.join(folder, file)
            zipname = os.path.basename(filepath).replace('_NEAREST.json', '.zip')
            with ZipFile(os.path.join('studies', zipname), 'w') as zip_obj:
                zip_obj.write(filepath, os.path.basename(filepath))