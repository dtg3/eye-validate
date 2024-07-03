import math

class Mapping:
    def __init__(self, line_num, col_num, character, x1, y1, x2, y2, token=None, syntactic_context=None, srcml1=None, srcml2=None):
        self.line_num = int(line_num) if line_num else line_num
        self.col_num = int(col_num) if col_num else col_num
        self.character = character
        self.bounding_x1 = int(x1) if x1 else x1
        self.bounding_y1 = int(y1) if y1 else y1
        self.bounding_x2 = int(x2) if x2 else x2
        self.bounding_y2 = int(y2) if y2 else y2
        self.source_token = token
        self.syntactic_context = syntactic_context
        self.srcml1 = srcml1
        self.srcml2 = srcml2

    def compute_center(self):
        return ( (self.bounding_x1 + self.bounding_x2) / 2, (self.bounding_y1 + self.bounding_y2) / 2 )
    
    def distance_from_bounding_center(self, x, y):
        center_point = self.compute_center()
        return math.sqrt( ((center_point[0] - x) ** 2) + ((center_point[1] - y) ** 2) )
    
    def __str__(self):
        return (f"MAPPING_LINE/COL: ({self.line_num}, {self.col_num})\n"
                f"MAPPING_CHAR: {self.character}\n"
                f"MAPPING_BOUNDING_X1: {self.bounding_x1}\n"
                f"MAPPING_BOUNDING_Y1: {self.bounding_y1}\n"
                f"MAPPING_BOUNDING_X2: {self.bounding_x2}\n"
                f"MAPPING_BOUNDING_Y2: {self.bounding_y2}\n"
                f"MAPPING_SOURCE_TOKEN: {self.source_token}\n"
                f"MAPPING_SYNTACTIC_CONTEXT: {self.syntactic_context}\n"
                f"MAPPING_SRCML1: {self.srcml1}\n"
                f"MAPPING_SRCML2: {self.srcml2}")

class TokenMapper:
    def __init__(self, mapping_file_path, mapping_file_context):
        self.mapping_file_path = mapping_file_path
        self.token_map = self.map_tokens(mapping_file_context)

    def map_tokens(self, mapping_data):
        map = {}
        for entry in mapping_data[1:]:
            stimulus_mapping = Mapping(*(entry.strip().split()))
            if not (stimulus_mapping.bounding_y1, stimulus_mapping.bounding_y2) in map:
                map[(stimulus_mapping.bounding_y1, stimulus_mapping.bounding_y2)] = []
            
            map[(stimulus_mapping.bounding_y1, stimulus_mapping.bounding_y2)].append(stimulus_mapping)
        
        return map

    def find_mapping(self, x, y):
        line_mappings = sorted(self.token_map.keys())
        low = 0
        high = (len(line_mappings)) - 1
        mid = 0
    
        while low <= high:
            mid = (high + low) // 2

            # If y is greater, ignore left half
            if line_mappings[mid][1] < y:
                low = mid + 1
    
            # If y is smaller, ignore right half
            elif line_mappings[mid][0] > y:
                high = mid - 1
    
            # means y is present at mid
            else:
                break

        # If we reach here, then the element was not present
        if low > high:
            return Mapping(None, None, None, None, None, None, None)

        column_mappings = self.token_map[line_mappings[mid]]
        low = 0
        high = (len(column_mappings)) - 1
        mid = 0

        while low <= high:
            mid = (high + low) // 2

            # If y is greater, ignore left half
            if column_mappings[mid].bounding_x2 < x:
                low = mid + 1
    
            # If y is smaller, ignore right half
            elif column_mappings[mid].bounding_x1 > x:
                high = mid - 1
    
            # means y is present at mid
            else:
                return column_mappings[mid]

        # If we reach here, then the element was not present
        return Mapping(None, None, None, None, None, None, None)

    def find_nearest_mapping_slow(self, x, y):
        shortest_distance = None
        mapping_value = None
        
        for key in self.token_map.keys():
            for element in self.token_map[key]:
                distance = element.distance_from_bounding_center(x, y)
                if shortest_distance == None or shortest_distance > distance:
                    shortest_distance = distance
                    mapping_value = element

        return mapping_value


    def find_nearest_mapping(self, x, y):
        line_mappings = sorted(self.token_map.keys())
        prev_line = None
        current_line = None

        for line in line_mappings:
            current_line = line
            if current_line[1] >= y >= current_line[0]:
                prev_line = line
                break

            if current_line[1] < y:
                prev_line = current_line
            else:
                if prev_line == None:
                    prev_line = current_line
                break

        distances = {}

        column_mappings = self.token_map[prev_line]
        
        for column in column_mappings:
            distance = column.distance_from_bounding_center(x, y)
            
            if not distance in distances.keys():
                distances[distance] = []
            
            distances[distance].append(column)
        
        if prev_line != current_line:
            column_mappings = self.token_map[current_line]
        
            for column in column_mappings:
                distance = column.distance_from_bounding_center(x, y)
            
                if not distance in distances.keys():
                    distances[distance] = []
            
                distances[distance].append(column)

        matches = distances[min(distances.keys())]
        
        return matches[0]
