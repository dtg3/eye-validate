import os
import ntpath
import posixpath
import json
import math
import statistics
from pathlib import Path
from datetime import datetime
from enum import Enum
from datetime import datetime


## UTILITY HELPER FUNCTIONS FOR CLASSES
def convert_value(value):
    if '.' in value:
        return float(value)
    elif value == 'None':
        return None
    else:
        return int(value)

def complex_handler(Obj):
    if hasattr(Obj, 'jsonable'):
        return Obj.jsonable()

def get_emip_base_filename(file_path):
    filename = ntpath.basename(file_path)
    return '_'.join(filename.strip().split('_')[:3])

def import_emip_data(filname):
    raw_gaze_collection = []
    with open(filname, 'r') as input_file:
        # Dump TSV Header
        input_file.readline()

        for line in input_file:
            line = line.strip()
            raw_gaze = RawGaze()
            raw_gaze.import_emip_data_record(line.split('\t'))
            raw_gaze_collection.append(raw_gaze)

    return raw_gaze_collection

# Parameters:
#   * delta_time = in milliseconds (1 / sample_rate)
#   * values from ported code:
#       * merge_fixation_time_interval=75
#       * merge_fixation_distance=0.5
def merge_classifications(trial, raw_gaze_collection, merge_fixation_time_interval=75, merge_fixation_distance=5, minimal_saccade_amplitude=0.5):

    fixation_candidate_list = []
    index = 0

    while (index < len(raw_gaze_collection)):
        start = index
        print(raw_gaze_collection[start])
        while (index < len(raw_gaze_collection) and raw_gaze_collection[start].movement_classification == raw_gaze_collection[index].movement_classification):
            index += 1
        
        end = index

        if raw_gaze_collection[start].movement_classification == MOVEMENT.NOISE:
            pass

        elif raw_gaze_collection[start].movement_classification == MOVEMENT.SACCADE:
            saccade_amplitude_x = max(gaze.x for gaze in raw_gaze_collection[start:end]) - min(gaze.x for gaze in raw_gaze_collection[start:end])
            saccade_amplitude_y = max(gaze.y for gaze in raw_gaze_collection[start:end]) - min(gaze.y for gaze in raw_gaze_collection[start:end])

            saccade_amplitude = math.sqrt(saccade_amplitude_x**2 + saccade_amplitude_y**2)

            if saccade_amplitude > minimal_saccade_amplitude:
                if (start > 0):
                    if (raw_gaze_collection[start-1].movement_classification != MOVEMENT.NOISE):
                        start -= 1

                if (end < len(raw_gaze_collection) - 1):
                    if (raw_gaze_collection[end].movement_classification != MOVEMENT.NOISE):
                        end += 1

                trial.add_saccade(Saccade(saccade_amplitude, raw_gaze_collection[start:end].copy()))
        
        elif raw_gaze_collection[start].movement_classification == MOVEMENT.FIXATION:
            fixation_candidate_list.append(raw_gaze_collection[start:end])

        elif raw_gaze_collection[start].movement_classification == MOVEMENT.PURSUIT:
            trial.add_smooth_pursuit(SmoothPursuit(raw_gaze_collection[start:end].copy()))
            
        else:
            print("WE SHOULD NOT BE HERE!")
            print(raw_gaze_collection[start])

        index += 1

    # CHECK FOR FIXATION MERGES
    if fixation_candidate_list:

        temp_list = fixation_candidate_list[0]

        for fix_index in range(1,len(fixation_candidate_list)):
            centroid_x1 = statistics.mean(gaze.x for gaze in temp_list)
            centroid_y1 = statistics.mean(gaze.y for gaze in temp_list)
            centroid_x2 = statistics.mean(gaze.x for gaze in fixation_candidate_list[fix_index])
            centroid_y2 = statistics.mean(gaze.y for gaze in fixation_candidate_list[fix_index])

            distance = math.sqrt( (centroid_x1 - centroid_x2)**2 + (centroid_y1 - centroid_y2)**2 )

            # EMIP Timestamps are in microseconds (convert to MS)
            time_ms = (fixation_candidate_list[fix_index][0].timestamp - temp_list[-1].timestamp) / 1000

            print("CANDIDATE DISTANCES: {}".format(distance))
            print("CANDIDATE TIME: {}".format(time_ms))

            if (distance <= merge_fixation_distance and time_ms <= merge_fixation_time_interval):
                temp_list.extend(fixation_candidate_list[fix_index])
                print('MERGE!')
            else:
                print("NUM POINTS: {}".format(len(temp_list)))
                print("TIME: {}".format((temp_list[-1].timestamp - temp_list[0].timestamp) / 1000))
                if ((temp_list[-1].timestamp - temp_list[0].timestamp) / 1000) >= 100:
                    fix_x = int(statistics.mean(gaze.x for gaze in temp_list))
                    fix_y = int(statistics.mean(gaze.y for gaze in temp_list))
                    trial.add_fixation(Fixation(trial.trial_participant, fix_x, fix_y, temp_list.copy(), (temp_list[-1].timestamp - temp_list[0].timestamp) / 1000))
                    print('SAVE!')
                else:
                    print('DISCARD!')
                
                temp_list = []
                temp_list = fixation_candidate_list[fix_index]
        
        if temp_list:
            if (temp_list[-1].timestamp - temp_list[0].timestamp) / 1000 >= 100:
                fix_x = int(statistics.mean(gaze.x for gaze in temp_list))
                fix_y = int(statistics.mean(gaze.y for gaze in temp_list))
                trial.add_fixation(Fixation(trial.trial_participant, fix_x, fix_y, temp_list.copy(), (temp_list[-1].timestamp - temp_list[0].timestamp) / 1000))


def load_json_trial_from_zip(json_string):
    trial = None
    json_obj = json.loads(json_string)

    # Build the trial
    trial = Trial(json_obj['trial_participant'], json_obj['raw_gaze_data_file'], json_obj['stimulus_image'], json_obj['mapping_data_file'], json_obj['filter_name'], json_obj['filter_settings'])
        
    #create the fixations
    for f in json_obj['fixations']:
        # Get the gazes
        gazes = []
        for g in f['raw_gazes']:
            gaze = RawGaze(
                g['timestamp'],
                g['right_x'],
                g['right_y'],
                g['right_valid'],
                g['right_pupil'],
                g['right_eye_distance_from_tracker'],
                g['left_x'],
                g['left_y'],
                g['left_valid'],
                g['left_pupil'],
                g['pupil_confidence'],
                g['left_eye_distance_from_tracker'],
                g['x'],
                g['y'],
                g['adj_x'],
                g['adj_y'],
                g['movement_classification']
            )
            gazes.append(gaze)

        fix = Fixation(
            f['trial'],
            f['fixation_x'],
            f['fixation_y'],
            gazes.copy(),
            f['duration'],
            f['line_num'],
            f['col_num'],
            f['character'],
            f['token'],
            f['syntactic_context']
        )
        
        fix.fixation_id = f['fixation_id']
        fix.update_x_y_offsets(f['adjusted_x'], f['adjusted_y'])
        trial.fixations.append(fix)

    for s in json_obj['saccades']:
        # Get the gazes
        gazes = []
        for g in s['raw_gazes']:
            gaze = RawGaze(
                g['timestamp'],
                g['right_x'],
                g['right_y'],
                g['right_valid'],
                g['right_pupil'],
                g['right_eye_distance_from_tracker'],
                g['left_x'],
                g['left_y'],
                g['left_valid'],
                g['left_pupil'],
                g['pupil_confidence'],
                g['left_eye_distance_from_tracker'],
                g['x'],
                g['y'],
                g['adj_x'],
                g['adj_y'],
                g['movement_classification']
            )
            gazes.append(gaze)

        sacc = Saccade(
            s['saccade_id'],
            s['saccade_amplitude'],
            gazes.copy()
        )
        
        sacc.saccade_id = s['saccade_id']
        trial.saccades.append(sacc)
    
    for sp in json_obj['smooth_pursuits']:
        # Get the gazes
        gazes = []
        for g in sp['raw_gazes']:
            gaze = RawGaze(
                g['timestamp'],
                g['right_x'],
                g['right_y'],
                g['right_valid'],
                g['right_pupil'],
                g['right_eye_distance_from_tracker'],
                g['left_x'],
                g['left_y'],
                g['left_valid'],
                g['left_pupil'],
                g['pupil_confidence'],
                g['left_eye_distance_from_tracker'],
                g['x'],
                g['y'],
                g['adj_x'],
                g['adj_y'],
                g['movement_classification']
            )
            gazes.append(gaze)

        smooth = Saccade(
            sp['smooth_pursuit_id'],
            gazes.copy()
        )
        
        smooth.smooth_pursuit_id = sp['smooth_pursuit_id']
        trial.smooth_pursuits.append(smooth)
           
    return trial

class MOVEMENT(Enum):
    FIXATION = 1
    SACCADE = 2
    PURSUIT = 3
    NOISE = 4

class Saccade:
    def __init__(self, amplitude=None, raw_gazes=None):
        self.saccade_id = None
        self.saccade_amplitude = amplitude
        self.raw_gazes = raw_gazes
    
    def jsonable(self):
        return self.__dict__


class SmoothPursuit:
    def __init__(self, raw_gazes=None):
        self.smooth_pursuit_id = None
        self.raw_gazes = raw_gazes

    def jsonable(self):
        return self.__dict__
        

class Fixation:
    def __init__(self, trial, x, y, raw_gazes, duration, line_num = None, col_num = None, character = None, token = None, syntactic_context = None):
        self.trial = trial
        self.fixation_id = None
        self.fixation_x = x
        self.fixation_y = y
        self.adjusted_x = 0
        self.adjusted_y = 0
        self.duration = duration
        self.line_num = line_num
        self.col_num = col_num
        self.character = character
        self.token = token
        self.syntactic_context = syntactic_context
        self.raw_gazes = raw_gazes

    def update_token_info(self, token_mapping):
        self.line_num = token_mapping.line_num
        self.col_num = token_mapping.col_num
        self.character = token_mapping.character
        self.token = token_mapping.source_token
        self.syntactic_context = token_mapping.syntactic_context
    
    def update_x_y_offsets(self, adj_x, adj_y):
        self.adjusted_x = adj_x
        self.adjusted_y = adj_y

    def calculated_adjusted_x(self):
        return self.fixation_x + self.adjusted_x
    
    def calculated_adjusted_y(self):
        return self.fixation_y + self.adjusted_y
        
    def jsonable(self):
        return self.__dict__



class Trial:
    def __init__(self, participant_id, raw_gaze_data_path, stimulus_image_path, mapping_data_file, filter_name=None, filter_settings=None):
        self.trial_participant = participant_id
        
        self.raw_gaze_data_file = None
        if ntpath.isabs(raw_gaze_data_path) or posixpath.isabs(raw_gaze_data_path):
            self.raw_gaze_data_file = raw_gaze_data_path
        else:
            self.raw_gaze_data_file = str(Path(raw_gaze_data_path).resolve())

        self.stimulus_image = None
        if ntpath.isabs(stimulus_image_path) or posixpath.isabs(stimulus_image_path):
            self.stimulus_image = stimulus_image_path
        else:
            self.stimulus_image = str(Path(stimulus_image_path).resolve())
        
        self.mapping_data_file = None
        if ntpath.isabs(mapping_data_file) or posixpath.isabs(mapping_data_file):
            self.mapping_data_file = mapping_data_file
        else:
            self.mapping_data_file = str(Path(mapping_data_file).resolve())

        self.filter_name = filter_name
        self.filter_settings = filter_settings
        self.fixations = []
        self.saccades = []
        self.smooth_pursuits = []
    

    def jsonable(self):
        return self.__dict__


    def add_filter(self, filter_name, filter_settings):
        self.filter_name = filter_name
        self.filter_settings = filter_settings


    def add_fixation(self, fixation):
        if not self.fixations:
            fixation.fixation_id = 1
        else:
            fixation.fixation_id = self.fixations[-1].fixation_id + 1

        self.fixations.append(fixation)

    def add_saccade(self, saccade):
        if not self.saccades:
            saccade.saccade_id = 1
        else:
            saccade.saccade_id = self.saccades[-1].saccade_id + 1

        self.saccades.append(saccade)
    
    def add_smooth_pursuit(self, smooth_pursuit):
        if not self.smooth_pursuits:
            smooth_pursuit.smooth_pursuit_id = 1
        else:
            smooth_pursuit.smooth_pursuit_id = self.smooth_pursuits[-1].smooth_pursuit_id + 1

        self.smooth_pursuits.append(smooth_pursuit)


    def write_out_fixations(self, output_directory, file_mod=None):
        filename = get_emip_base_filename(self.raw_gaze_data_file)
        if file_mod:
            filename +=  '_fixations_' + file_mod + '_' + str(datetime.now().timestamp()) + '.tsv'
        else:
            filename +=  '_fixations.tsv'
            
        output_file = os.path.join(output_directory, filename)
        
        with open(output_file, 'w') as output:
            output.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')
            output.write(self.raw_gaze_data_file + '\n')
            output.write(self.filter_name + '\n')
            output.write(self.filter_settings + '\n')
            output.write('\n')
            output.write('FIX_ID\tFIX_X\tFIX_Y\tFIX_X_ADJUST\tFIX_Y_ADJUST\tFIX_DURATION\tFIX_LINE\tFIX_COL\tFIX_CHAR\tFIX_TOKEN\tFIX_SYNTACTIC_CONTEXT\n')
            for fix in self.fixations:
                output.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                    fix.fixation_id,
                    fix.fixation_x,
                    fix.fixation_y,
                    fix.adjusted_x,
                    fix.adjusted_y,
                    fix.duration,
                    fix.line_num,
                    fix.col_num,
                    fix.character,
                    fix.token,
                    fix.syntactic_context)
                )


    def create_json_dump(self, output_directory, file_mod=None):
        filename = get_emip_base_filename(self.raw_gaze_data_file)
        if file_mod:
            filename +='_trial_data_' + file_mod + '_' + str(datetime.now().timestamp()) + '.json'
        else:
            filename +='_trial_data.json'

        output_file = os.path.join(output_directory, filename)

        with open(output_file, 'w') as output:
            output.write(json.dumps(self, default=complex_handler, sort_keys=False, indent=4))
     
            
            
class RawGaze:
    def __init__(self, timestamp=None, right_x=None, right_y=None, right_valid=None, right_pupil=None, right_eye_distance_from_tracker=None, left_x=None, left_y=None, left_valid=None, left_pupil=None, pupil_confidence=None, left_eye_distance_from_tracker=None, x=None, y=None, adj_x=None, adj_y=None, movement_classification=None):
        self.timestamp = timestamp
        self.right_x = right_x
        self.right_y = right_y
        self.right_valid = right_valid
        self.right_pupil = right_pupil
        self.right_eye_distance_from_tracker = right_eye_distance_from_tracker
        self.left_x = left_x
        self.left_y = left_y
        self.left_valid = left_valid
        self.left_pupil = left_pupil
        self.pupil_confidence = pupil_confidence
        self.left_eye_distance_from_tracker = left_eye_distance_from_tracker

        # Average of left and right values if both eyes are valid
        self.x = x
        self.y = y

        # Store an offset for repositioning values (drift)
        self.adj_x = adj_x
        self.adj_y = adj_y

        self.movement_classification = movement_classification

    def is_valid(self):
        return self.right_valid == 1 or self.left_valid == 1
    
    def jsonable(self):
        return self.__dict__

    def import_emip_data_record(self, data_record):
        # data_record is a preprocessed EMIP record
        # The data format is:
        #       TIMESTAMP
        #       RIGHT_X
        #       RIGHT_Y
        #       RIGHT_VALID
        #       RIGHT_PUPIL
        #       RIGHT_DISTANCE_FROM_TRACKER
        #       LEFT_X
        #       LEFT_Y
        #       LEFT_VALID
        #       LEFT_PUPIL
        #       PUPIL_CONFIDENCE
        #       LEFT_DISTANCE_FROM_TRACKER
        #       X
        #       Y
        #       ADJ_X
        #       ADJ_Y
        self.timestamp = convert_value(data_record[0])
        self.right_x = convert_value(data_record[1])
        self.right_y = convert_value(data_record[2])
        self.right_valid = convert_value(data_record[3])
        self.right_pupil = convert_value(data_record[4])
        self.right_eye_distance_from_tracker = convert_value(data_record[5])
        self.left_x = convert_value(data_record[6])
        self.left_y = convert_value(data_record[7])
        self.left_valid = convert_value(data_record[8])
        self.left_pupil = convert_value(data_record[9])
        self.pupil_confidence = convert_value(data_record[10])
        self.left_eye_distance_from_tracker = convert_value(data_record[11])

        # Average of left and right values if both eyes are valid
        self.x = convert_value(data_record[12])
        self.y = convert_value(data_record[13])

        # Store an offset for repositioning values (drift)
        self.adj_x = convert_value(data_record[14])
        self.adj_y = convert_value(data_record[15])
    
    def calculated_adjusted_x(self):
        if self.adj_x == None:
            return self.x
        else:
            return self.x + self.adj_x
    
    def calculated_adjusted_y(self):
        if self.adj_x == None:
            return self.y
        else:
            return self.y + self.adj_y

    ## OVERIDE METHODS
    def __str__(self):
        return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            self.timestamp,
            self.right_x,
            self.right_y,
            self.right_valid,
            self.right_pupil,
            self.right_eye_distance_from_tracker,
            self.left_x,
            self.left_y,
            self.left_valid,
            self.left_pupil,
            self.pupil_confidence,
            self.left_eye_distance_from_tracker,
            self.x,
            self.y,
            self.adj_x,
            self.adj_y,
            self.movement_classification.name if self.movement_classification else None
        ) 
