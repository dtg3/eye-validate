from PIL import Image as Pil_image, ImageTk as Pil_imageTk
from tkinter import *
import tkinter.filedialog
import fixations
from token_mapper import *
import utils
import os
import ntpath
from zipfile import ZipFile
import io

def from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    # OPENCV colors are B G R not RGB
    b, g, r = rgb
    return f'#{r:02x}{g:02x}{b:02x}'


class ExampleApp(Frame):
    def __init__(self, master):
        Frame.__init__(self,master=None)
        self.master = master
        self.trial = None
        self.trial_adj = None
        self.trial_nearest = None
        self.canvas_width, self.canvas_height = self.get_app_dimensions()
        self.canvas = Canvas(self, width=self.canvas_width, height=self.canvas_height, cursor="cross")
        self.canvas.bind('d', self.next_fixation)
        self.canvas.bind('a', self.prev_fixation)
        self.canvas.bind('r', self.reset_fixation)
        self.canvas.bind('o', self.load_fixation)
        self.canvas.bind('1', self.toggle_adjusted)
        self.canvas.bind('2', self.toggle_nearest)
        self.canvas.bind('3', self.toggle_original)
        self.canvas.bind('4', self.toggle_lines)
        self.canvas.bind('5', self.toggle_numbers)

        self.frame1 = Frame(self)
        self.frame2 = Frame(self)
        
        self.open_btn = Button(self.frame1, text="Open Fixation Data", command=self.load_fixation)
        self.next_fix_btn = Button(self.frame2, text="Next Fixation", command=self.next_fixation)
        self.prev_fix_btn = Button(self.frame2, text="Previous Fixation", command=self.prev_fixation)
        self.reset_fix_btn = Button(self.frame1, text="Reset Fixation", command=self.reset_fixation)

        self.check_states = [IntVar(), IntVar(), IntVar(), IntVar(), IntVar()]
        self.chk_show_adjusted = Checkbutton(self.frame1, text="Show Ajusted", command=self.toggle_adjusted, variable=self.check_states[0])
        self.chk_show_nearest = Checkbutton(self.frame1, text="Show Nearest", command=self.toggle_nearest, variable=self.check_states[1])
        self.chk_show_original = Checkbutton(self.frame1, text="Show Original", command=self.toggle_original, variable=self.check_states[2])
        
        self.chk_show_lines = Checkbutton(self.frame1, text="Show Lines", command=self.toggle_lines, variable=self.check_states[3])
        self.chk_show_numbers = Checkbutton(self.frame1, text="Show Numbers", command=self.toggle_numbers, variable=self.check_states[4])
        self.chk_show_numbers.select()
        self.chk_show_lines.select()

        self.lbl_original = Label(self.frame1, text="  ", bg=from_rgb((255, 0, 170)))
        self.lbl_nearest = Label(self.frame1, text="  ", bg=from_rgb((0, 212, 255)))
        self.lbl_adjusted = Label(self.frame1, text="  ", bg=from_rgb((0, 127, 255)))

        self.lbl_instructions = Label(self.frame2, 
                                      text="Click on the image to reposition the green fixation if it appears out of place.",
                                      font=("Arial", 20))
        
        self.canvas.focus_set()     

        self.sbarv=Scrollbar(self,orient=VERTICAL)
        self.sbarh=Scrollbar(self,orient=HORIZONTAL)
        self.sbarv.config(command=self.canvas.yview)
        self.sbarh.config(command=self.canvas.xview)

        self.canvas.config(yscrollcommand=self.sbarv.set)
        self.canvas.config(xscrollcommand=self.sbarh.set)

        self.frame1.grid(row=0, column=0, sticky=E+W)
        self.frame2.grid(row=3, column=0, sticky=E+W)

        self.open_btn.grid(row=0, column=0, padx=(0,100), sticky=W)
        self.reset_fix_btn.grid(row=0, column=1, padx=(0,100), sticky=E)
        
        self.chk_show_adjusted.grid(row=0, column=2, sticky=E)
        self.lbl_adjusted.grid(row=0, column=3, padx=(0,10), sticky=E)
        self.chk_show_nearest.grid(row=0, column=4, sticky=E)
        self.lbl_nearest.grid(row=0, column=5, padx=(0,10), sticky=E)
        self.chk_show_original.grid(row=0, column=6, sticky=E)
        self.lbl_original.grid(row=0, column=7, padx=(0,100), sticky=E)
        
        self.chk_show_lines.grid(row=0, column=8, sticky=E)
        self.chk_show_numbers.grid(row=0, column=9, sticky=E)

        self.canvas.grid(row=1,column=0,sticky=N+S+E+W)
        self.sbarv.grid(row=1,column=1,stick=N+S)
        self.sbarh.grid(row=2,column=0,sticky=E+W)
        
        self.prev_fix_btn.grid(row=0, column=0, padx=(0,100), sticky=W)
        self.next_fix_btn.grid(row=0, column=1, padx=(0,100), sticky=W)
        self.lbl_instructions.grid(row=0, column=2, sticky=W)
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.canvas.config(scrollregion=(0,0,1920,1080))

        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw")
        self.json_file = None
        self.tk_img = None
        self.trial = None
        self.trial_num = 1

        self.support_zip = os.path.join(os.path.dirname(__file__), 'support_files.zip')

    def on_button_press(self, event):
        if not self.tk_img:
            return
        self.start_x = int(self.canvas.canvasx(event.x))
        self.start_y = int(self.canvas.canvasy(event.y))
        print("Location: ({}, {})".format(self.start_x, self.start_y))
        fix_list = self.trial.fixations[:self.trial_num]
        fix_list[-1].adjusted_x = self.start_x - fix_list[-1].fixation_x
        fix_list[-1].adjusted_y = self.start_y - fix_list[-1].fixation_y
        self.reload_image()

    def set_up(self):
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw")
        self.json_file = None
        self.tk_img = None
        self.trial = None
        self.trial_nearest = None
        self.trial_adj = None
        self.trial_num = 1
        self.start_x = 0
        self.start_y = 0

    def finish(self):
        token_stuff = TokenMapper(self.trial.mapping_data_file, self.get_text_content_from_support_zip(self.trial.mapping_data_file))

        for fix in self.trial.fixations:
            token_data = token_stuff.find_mapping(fix.calculated_adjusted_x(), fix.calculated_adjusted_y())
            fix.update_token_info(token_data)

        self.trial.create_json_dump(os.path.dirname(self.json_file.name), 'VALIDATION')
        self.trial.write_out_fixations(os.path.dirname(self.json_file.name), 'VALIDATION')
        self.canvas.delete(self.canvas_img)
        self.set_up()

    def on_button_release(self, event):
        pass

    def load_fixation(self, key_bind=None):
        self.set_up()

        self.json_file = tkinter.filedialog.askopenfile(filetypes = (("zip","*.zip"),("all files","*.*")))
        if not self.json_file:
            return
        
        with ZipFile(self.json_file.name, 'r') as zipObj:
            archive_data_files = zipObj.namelist()

            nearest_path = [i for i in archive_data_files if 'NEAREST' in i][0]
            golden_path = [i for i in archive_data_files if 'ADJUSTED' in i][0]

            with io.TextIOWrapper(zipObj.open(nearest_path), encoding='utf-8') as test:
                self.trial_nearest = fixations.load_json_trial_from_zip(test.read())
        
            with io.TextIOWrapper(zipObj.open(golden_path), encoding='utf-8') as test:
                data = test.read()
                self.trial = fixations.load_json_trial_from_zip(data)
                self.trial_adj = fixations.load_json_trial_from_zip(data)

            self.trial_num = 1
            self.reload_image()
    
    def reload_image(self):
        utils.plot_fixations_for_verification(self.get_image_content_from_support_zip(self.trial.stimulus_image), self.trial.fixations[:(self.trial_num + 2)], self.trial_adj.fixations[:(self.trial_num + 2)], self.trial_nearest.fixations[:(self.trial_num + 2)], self.trial_num - 1, self.check_states, 'temp_fix_image.jpg')
        im = Pil_image.open('temp_fix_image.jpg')
        self.tk_img = Pil_imageTk.PhotoImage(im)
        self.canvas.itemconfig(self.canvas_img, image=self.tk_img)

    def next_fixation(self, key_bind=None):
        if not self.tk_img:
            return
        self.trial_num += 1
        if self.trial_num > len(self.trial.fixations):
            self.finish()
        else:
            self.reload_image()
            self.x = 0
            self.y = 0         

    def prev_fixation(self, key_bind=None):
        if not self.tk_img:
            return
        if self.trial_num > 1:
            self.trial_num -= 1
            self.start_x = 0
            self.start_y = 0
            self.reload_image()
    
    def reset_fixation(self, key_bind=None):
        if not self.tk_img:
            return
        
        fix_list = self.trial.fixations[:self.trial_num]
        fix_adjustments = self.trial_adj.fixations[:self.trial_num]
        fix_list[-1].adjusted_x = fix_adjustments[-1].adjusted_x
        fix_list[-1].adjusted_y = fix_adjustments[-1].adjusted_y
        self.start_x = 0
        self.start_y = 0
        self.reload_image()

    def toggle_lines(self, key_bind=None):
        if key_bind:
            self.chk_show_lines.toggle()
        
        self.reload_image()
    
    def toggle_numbers(self, key_bind=None):
        if key_bind:
            self.chk_show_numbers.toggle()
        
        self.reload_image()
    
    def toggle_original(self, key_bind=None):
        if key_bind:
            self.chk_show_original.toggle()
        
        self.reload_image()

    def toggle_adjusted(self, key_bind=None):
        if key_bind:
            self.chk_show_adjusted.toggle()
        
        self.reload_image()
    
    def toggle_nearest(self, key_bind=None):
        if key_bind:
            self.chk_show_nearest.toggle()
        
        self.reload_image()
    
    def get_image_content_from_support_zip(self, path):
        image_data = None
        with ZipFile(self.support_zip, 'r') as zipObj:
            archive_data_files = zipObj.namelist()

            path = [i for i in archive_data_files if ntpath.basename(path) in i][0]

            image_data = zipObj.open(path).read()

        return image_data

    
    def get_text_content_from_support_zip(self, path):
        text_data = None
        with ZipFile(self.support_zip, 'r') as zipObj:
            archive_data_files = zipObj.namelist()

            path = [i for i in archive_data_files if ntpath.basename(path) in i][0]

            with io.TextIOWrapper(zipObj.open(path), encoding='utf-8') as text:
                text_data = text.read().splitlines()
        
        return text_data
        
    def get_app_dimensions(self):
        width = 1400
        height = 750
        try:
            with open('settings.txt', 'r') as settings_file:
                for line in settings_file:
                    if 'WIDTH' in line:
                        width = int(line.split('=')[1])
                    if 'HEIGHT' in line:
                        height = int(line.split('=')[1])
        except Exception as error:
            print("WARNING: Could not locate settings.txt in application directory")
        finally:
            return (width, height)

if __name__ == "__main__":
    root=Tk()
    app = ExampleApp(root)
    app.pack()
    root.mainloop()
