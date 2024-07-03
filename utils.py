import numpy as np
import cv2

def plot_fixations_for_verification(image_path, fixations, neartest_fixations, current_fixation_index, output_modes, output_file):
    img = cv2.imdecode(np.frombuffer(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    img2 = img.copy()

    alpha = 0.25
    radius = 4

    for fix in fixations:
        if fix.fixation_x < -1 or fix.fixation_y < -1 or fix != fixations[current_fixation_index]:
            continue
        for gaze in fix.raw_gazes:
            if gaze.x > -1 and gaze.y > -1:
                img2 = cv2.circle(img2, (gaze.calculated_adjusted_x(), gaze.calculated_adjusted_y()), radius, (0, 0, 255), -1)
    
    img2 = cv2.addWeighted(img2, alpha, img, 1 - alpha, 0)
    
    fix_prev2 = None
    fix_prev1 = None
    fix_current = fixations[current_fixation_index]
    fix_current_nearest = None
    fix_current_original = None

    if output_modes[1].get():
        fix_current_nearest = neartest_fixations[current_fixation_index]

    if output_modes[2].get():
        fix_current_original = fixations[current_fixation_index]
    
    fix_next1 = None
    fix_next2 = None

    for fix in fixations:
        #print('({}, {}) + adj ({}, {}) = ({}, {})'.format(fix.fixation_x, fix.fixation_y, fix.adjusted_x, fix.adjusted_y, fix.calculated_adjusted_x(), fix.calculated_adjusted_y()))
        if fix.fixation_x > -1 and fix.fixation_y > -1:
            if current_fixation_index + 1 < len(fixations) and fix == fixations[current_fixation_index + 1]:
                # Draw fix + 1
                fix_next1 = fix

            elif current_fixation_index + 2 < len(fixations) and fix == fixations[current_fixation_index + 2]:
                # Draw fix + 2
                fix_next2 = fix

            elif current_fixation_index > 0 and fix == fixations[current_fixation_index - 1]:
                # Draw fix - 1
                fix_prev1 = fix

            elif current_fixation_index > 1 and fix == fixations[current_fixation_index - 2]:
                # Draw fix - 2
                fix_prev2 = fix
            # else:
                # Skip the grey dots
                # img2 = cv2.circle(img2, (fix.calculated_adjusted_x(), fix.calculated_adjusted_y()), radius, (150, 150, 150), -1)


    ORIGINAL_COLOR = (255, 0, 170)
    NEAREST_COLOR = (0, 212, 255)
    PREV_COLOR = (0, 0, 255)
    NEXT_COLOR = (255, 64, 0)
    CURRENT_COLOR = (0, 255, 106)
    BLACK_COLOR = (0, 0, 0)
    BLACK_OUTLINE_THICKNESS = 2

    # Render special fixations

    # LINES
    if output_modes[3].get():
        if fix_prev2 and fix_prev1:
            img2 = cv2.line(img2, (fix_prev2.fixation_x, fix_prev2.fixation_y), (fix_prev1.fixation_x, fix_prev1.fixation_y), PREV_COLOR, 2)
        
        if fix_next1 and fix_next2:
            img2 = cv2.line(img2, (fix_next1.fixation_x, fix_next1.fixation_y), (fix_next2.fixation_x, fix_next2.fixation_y), NEXT_COLOR, 2)
        
        if fix_prev1 and fix_current_original:
            img2 = cv2.line(img2, (fix_prev1.fixation_x, fix_prev1.fixation_y), (fix_current_original.fixation_x, fix_current_original.fixation_y), ORIGINAL_COLOR, 2)        

        if fix_current_original and fix_next1:
            img2 = cv2.line(img2, (fix_current_original.fixation_x, fix_current_original.fixation_y), (fix_next1.fixation_x, fix_next1.fixation_y), ORIGINAL_COLOR, 2)

        if fix_prev1 and fix_current_nearest:
            img2 = cv2.line(img2, (fix_prev1.fixation_x, fix_prev1.fixation_y), (fix_current_nearest.calculated_adjusted_x(), fix_current_nearest.calculated_adjusted_y()), NEAREST_COLOR, 2)

        if fix_current_nearest and fix_next1:
            img2 = cv2.line(img2, (fix_current_nearest.calculated_adjusted_x(), fix_current_nearest.calculated_adjusted_y()), (fix_next1.fixation_x, fix_next1.fixation_y), NEAREST_COLOR, 2)

        if fix_prev1 and fix_current:
            img2 = cv2.line(img2, (fix_prev1.fixation_x, fix_prev1.fixation_y), (fix_current.calculated_adjusted_x(), fix_current.calculated_adjusted_y()), CURRENT_COLOR, 2)
        
        if fix_current and fix_next1:
            img2 = cv2.line(img2, (fix_current.calculated_adjusted_x(), fix_current.calculated_adjusted_y()), (fix_next1.fixation_x, fix_next1.fixation_y), CURRENT_COLOR, 2)

    # DOTS
    if fix_prev2:
        img2 = cv2.circle(img2, (fix_prev2.fixation_x, fix_prev2.fixation_y), radius, PREV_COLOR, -1)
        img2 = cv2.circle(img2, (fix_prev2.fixation_x, fix_prev2.fixation_y), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
        if output_modes[4].get():
            img2 = cv2.putText(img2, "-2", (fix_prev2.fixation_x, fix_prev2.fixation_y), cv2.FONT_HERSHEY_COMPLEX_SMALL, .75, (0, 0, 0), 1)
    if fix_prev1:
        img2 = cv2.circle(img2, (fix_prev1.fixation_x, fix_prev1.fixation_y), radius, PREV_COLOR, -1)
        img2 = cv2.circle(img2, (fix_prev1.fixation_x, fix_prev1.fixation_y), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
        if output_modes[4].get():
            img2 = cv2.putText(img2, "-1", (fix_prev1.fixation_x, fix_prev1.fixation_y), cv2.FONT_HERSHEY_COMPLEX_SMALL, .75, (0, 0, 0), 1)
    if fix_next1:
        img2 = cv2.circle(img2, (fix_next1.fixation_x, fix_next1.fixation_y), radius, NEXT_COLOR, -1)
        img2 = cv2.circle(img2, (fix_next1.fixation_x, fix_next1.fixation_y), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
        if output_modes[4].get():
            img2 = cv2.putText(img2, "+1", (fix_next1.fixation_x, fix_next1.fixation_y), cv2.FONT_HERSHEY_COMPLEX_SMALL, .75, (0, 0, 0), 1)
    if fix_next2:
        img2 = cv2.circle(img2, (fix_next2.fixation_x, fix_next2.fixation_y), radius, NEXT_COLOR, -1)
        img2 = cv2.circle(img2, (fix_next2.fixation_x, fix_next2.fixation_y), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
        if output_modes[4].get():
            img2 = cv2.putText(img2, "+2", (fix_next2.fixation_x, fix_next2.fixation_y), cv2.FONT_HERSHEY_COMPLEX_SMALL, .75, (0, 0, 0), 1)
    
    if fix_current_original:
        img2 = cv2.circle(img2, (fix_current_original.fixation_x, fix_current_original.fixation_y), radius, ORIGINAL_COLOR, -1)
        img2 = cv2.circle(img2, (fix_current_original.fixation_x, fix_current_original.fixation_y), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
    
    if fix_current_nearest:
        img2 = cv2.circle(img2, (fix_current_nearest.calculated_adjusted_x(), fix_current_nearest.calculated_adjusted_y()), radius, NEAREST_COLOR, -1)
        img2 = cv2.circle(img2, (fix_current_nearest.calculated_adjusted_x(), fix_current_nearest.calculated_adjusted_y()), radius, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)
    
    if fix_current:
        img2 = cv2.circle(img2, (fix_current.calculated_adjusted_x(), fix_current.calculated_adjusted_y()), radius - 1, CURRENT_COLOR, -1)
        img2 = cv2.circle(img2, (fix_current.calculated_adjusted_x(), fix_current.calculated_adjusted_y()), radius - 1, BLACK_COLOR, BLACK_OUTLINE_THICKNESS)

    cv2.imwrite(output_file, img2)

