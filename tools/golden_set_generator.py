import os
import io
import random
from zipfile import ZipFile


class Token:
    def __init__(self, line_number, col_start, col_end, token, syntactic_context, srcml1, srcml2):
        self.line_number = line_number
        self.col_range = (col_start, col_end)
        self.token = token
        self.syntactic_context = syntactic_context
        self.srcml1 = srcml1
        self.srcml2 = srcml2


    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        
        return (self.line_number == other.line_number and 
                self.col_range == other.col_range and 
                self.token == other.token and
                self.syntactic_context == other.syntactic_context and
                self.srcml1 == other.srcml1 and self.srcml2 == other.srcml2)
    

    def __ne__(self, other):
        return not self.__eq__(other)
    

    def __str__(self):
        return (f"{self.line_number}\n"
                f"{self.col_range}\n"
                f"{self.token}\n"
                f"{self.syntactic_context}\n"
                f"{self.syntactic_context}\n"
                f"{self.srcml1}\n"
                f"{self.srcml2}")
    

def build_token(mapping_group):
    
    first_mapping = mapping_group[0].strip().split()
    last_mapping = mapping_group[-1].strip().split()

    line_number = int(first_mapping[0])
    col_start = int(first_mapping[1])
    col_end = int(last_mapping[1])
    token = first_mapping[7]
    syntactic_context = first_mapping[8]
    srcml1 = first_mapping[9] if len(first_mapping) == 11 else None
    srcml2 = first_mapping[10] if len(first_mapping) == 11 else None

    for line in mapping_group[1:]:
        current_line = line.strip().split()

        if (line_number != int(current_line[0]) or token != current_line[7] or 
            syntactic_context != current_line[8] or srcml1 != (current_line[9] if len(current_line) == 11 else None) or
            srcml2 != (current_line[10] if len(current_line) == 11 else None)):
            print("Map Grouping is Incorrect")
            print(mapping_group)
            exit(1)
    
    return Token(line_number, col_start, col_end, token, syntactic_context, srcml1, srcml2)



def get_mapping_from_support_zip(path):
        mapping_data = {}
        with ZipFile(path, 'r') as zipObj:
            archive_data_files = zipObj.namelist()
    
            map_file_paths = [i for i in archive_data_files if '.txt' in i]

            for map_file in map_file_paths:
                stimulus = os.path.basename(map_file).split('_')[0]

                if 'rect' in stimulus:
                    stimulus = stimulus.replace('rect', 'rectangle')

                mapping_data[stimulus] = []
                with io.TextIOWrapper(zipObj.open(map_file), encoding='utf-8') as text:
                    current_index = 0
                    lines = text.read().splitlines()[1:]
                    while current_index < len(lines):
                        data_fields = lines[current_index].strip().split()
                        offset = len(data_fields[7]) if data_fields[2] != '[SPACE]' else 1
                        
                        group = []
                        for position in range(current_index, current_index + offset):
                            group.append(lines[position])
                        
                        mapping_data[stimulus].append(build_token(group))
                        current_index += offset                    
        
        return mapping_data


def get_all_trial_file_paths(root_directory, extensions=None, filters=None):
    trial_content = {}
    for root, directories, files in os.walk(root_directory):
        for file in files:
            if (not extensions or file[file.rfind(".") + 1:] in extensions) and (not filters or not any(s in file for s in filters)):
                
                content_path = os.path.join(root, file)
                preprocessed_filename = file.split("_")

                trial_id = int(preprocessed_filename[0]) 
                stimulus = preprocessed_filename[1] + ('2' if preprocessed_filename[2] == 'java2' else '')

                if (trial_id, stimulus) not in trial_content:
                    trial_content[(trial_id, stimulus)] = []

                trial_content[(trial_id, stimulus)].append(content_path)

    return trial_content

def match_token(line, mapping_set):
    #print(line)
    data = line.strip().split()

    for item in mapping_set:
        if data[6] != "None" and data[7] != "None" and int(data[6]) == item.line_number and item.col_range[0] <= int(data[7]) <= item.col_range[1]:
            return item
        
    print("DIDN'T FIND A MAPPING!")
    return None

def main():

    mapping_data = get_mapping_from_support_zip(os.path.join('..', 'support_files.zip'))
    validation_data = get_all_trial_file_paths(os.path.join('..', 'output_validation'), extensions=['tsv'])

    os.makedirs(os.path.join('..', 'goldenset'), exist_ok=True)

    for key in validation_data:
        if len(validation_data[key]) < 2:
            continue
        while len(validation_data[key]) > 2:
            print(f"Too Many Validation Files ({len(validation_data[key])})!")
            print(f"Removing: {validation_data[key].pop(random.randrange(len(validation_data[key])))}")
        
        print(f"PROCESSING GOLDENSET FROM: {validation_data[key][0]} <=> {validation_data[key][1]}")
        output_filename = os.path.basename(validation_data[key][0])
        output_filename = output_filename[:output_filename.find("fixations")] + "GOLDENSET.tsv"
        fpath = os.path.join('..', 'goldenset', output_filename)
        with open(fpath, 'w') as output:
            with open(validation_data[key][0], 'r') as input_validation1:
                with open(validation_data[key][1], 'r') as input_validation2:
                    for line_num in range(6):
                        line_data = input_validation1.readline()
                        input_validation2.readline()
                        
                        if line_num != 1:
                            output.write(line_data)
                    
                    mapping_set = mapping_data[key[1]]

                    for line in input_validation1:
                        v1 = match_token(line, mapping_set)
                        v2 = match_token(input_validation2.readline(), mapping_set)
                        if v1 and v2 and v1 == v2:
                            output.write(line)

if __name__ == "__main__":
    main()
