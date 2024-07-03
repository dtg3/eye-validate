import os
import ntpath
import io
from fixations import load_json_trial_from_file
from token_mapper import TokenMapper
from zipfile import ZipFile

SUPPORT_ZIP = os.path.join("support_files.zip")

def get_text_content_from_support_zip(path):
        text_data = None
        with ZipFile(SUPPORT_ZIP, 'r') as zipObj:
            archive_data_files = zipObj.namelist()

            path = [i for i in archive_data_files if ntpath.basename(path) in i][0]

            with io.TextIOWrapper(zipObj.open(path), encoding='utf-8') as text:
                text_data = text.read().splitlines()
        
        return text_data

def fix_json_mapping_and_stimulus_info(filepath):
    meta_data = os.path.basename(filepath)
    stimulus_name = None
    mapping_name = None
    if 'rectangle' in meta_data:
        stimulus_name = 'rectangle_java'
        mapping_name = 'rect'
    elif 'vehicle' in meta_data:
        stimulus_name = 'vehicle_java'
        mapping_name = 'vehicle'
    else:
        raise Exception("Study filename is invalid!") 

    if 'java2' in meta_data:
            stimulus_name += '2'
            mapping_name += '2'
    
    stimulus_name += '.jpg'
    mapping_name += '_complete_mapping.txt'

    return stimulus_name, mapping_name

def create_mapping_objects():
    pass

def create_directory_path(path):
    dir_path = os.path.split(path)[0]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

for folder, subfolders, files in os.walk(os.path.join('new_intermediate')):
    for file in files:
        if file.endswith('.json') and 'NEAREST' not in file and 'ADJUSTED' not in file and 'BROKEN' not in file:
            filepath = os.path.join(folder, file)
            print(f"PROCESSING: {filepath}")
            stimulus_name, mapping_name = fix_json_mapping_and_stimulus_info(filepath)
            trial_data = load_json_trial_from_file(filepath, stimulus_name, mapping_name)
            
            new_output_path = os.path.join('data_set', *(filepath.replace('.json', '_NEAREST.json').split('\\')[1:]))
            create_directory_path(new_output_path)

            mapper = TokenMapper(trial_data.mapping_data_file, get_text_content_from_support_zip(trial_data.mapping_data_file))

            for fixation in trial_data.fixations: 
                mapping = mapper.find_nearest_mapping_slow(fixation.fixation_x, fixation.fixation_y)
                fixation.update_token_info(mapping)
                center = mapping.compute_center()
                fixation.update_x_y_offsets(center[0] - fixation.fixation_x, center[1] - fixation.fixation_y)
            
            filename_attribute =  'NEAREST'

            trial_data.create_json_dump(os.path.dirname(new_output_path), filename_attribute)
            trial_data.write_out_fixations(os.path.dirname(new_output_path), filename_attribute)
            

            


                        


        