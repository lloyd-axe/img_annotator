import tkinter as tk
from tkinter import filedialog, simpledialog, Listbox
from PIL import Image, ImageTk
import os
import uuid
import pandas as pd

from ToolsConstants import ANNOTATION, IMAGE_NAME, IMAGE_PATH, BBOX_COORDS, CANVAS_COORDS, TEXT_COORDS, BBOX_UUID,\
    XUL, XLR, YUL, YLR

class BoundingBoxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bounding Box Annotation App")

        self.image_paths = []
        self.current_image_index = 0
        self.image_path = None
        self.tk_image = None

        self.bbox_data = pd.DataFrame({
            IMAGE_NAME: [],
            IMAGE_PATH: [],
            BBOX_UUID: [],
            BBOX_COORDS: [],
            ANNOTATION: []
        })
        self.application_cache = {}
        self.coords_name = [XUL, YUL, XLR, YLR]  # UL = upper left, LR = Lower Right

        # Create Canvas for displaying the image
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create Listbox for annotations
        self.annotations_listbox = Listbox(root)
        self.annotations_listbox.pack(side=tk.RIGHT, padx=10)

        # Create label for displaying file name
        self.filename_label = tk.Label(root, text="")
        self.filename_label.pack(side=tk.TOP, pady=10)

        # Create Buttons
        self.open_button = tk.Button(root, text="Open Image", command=self.open_images)
        self.open_button.pack(side=tk.LEFT, padx=10)

        self.prev_button = tk.Button(root, text="Previous", command=self.show_previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(root, text="Next", command=self.show_next_image)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Initialize slideshow with the first image if available
        self.show_image()

        self.save_button = tk.Button(root, text="Save Annotations", command=self.save_annotations)
        self.save_button.pack_forget()  # Hide the button initially

        clear_button = tk.Button(root, text="Clear Annotations", command=self.clear_annotations)
        clear_button.pack(side=tk.LEFT, padx=10)

        self.delete_button = tk.Button(root, text="Delete Box", command=self.delete_selected_bbox)
        self.delete_button.pack(side=tk.LEFT, padx=10)
        self.annotations_listbox.bind("<<ListboxSelect>>", self.on_select_annotation)

        self.canvas.bind("<Button-1>", self.start_bbox)
        self.canvas.bind("<B1-Motion>", self.draw_bbox)
        self.canvas.bind("<ButtonRelease-1>", self.stop_bbox)

    def open_images(self):
        image_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if image_paths:
            self.image_paths = image_paths
            self.current_image_index = 0
            self.show_image()

    def show_image(self):
        if self.image_paths:
            self.image_path = self.image_paths[self.current_image_index]
            image = Image.open(self.image_path)
            self.tk_image = ImageTk.PhotoImage(image)
            self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
            img_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            print('img_id', img_id)
            # Display the file name above the image
            filename = os.path.basename(self.image_path)
            self.filename_label.config(text=filename)

            # Retrieve and draw saved bounding boxes & text for the current image
            for k, v in self.application_cache.items():
                if v[IMAGE_PATH] == self.image_path:
                    image_cache = v.copy()
                    image_cache.pop(IMAGE_PATH, None)
                    self.draw_saved_bbox(**image_cache)

            # Update annotations listbox
            self.annotations_listbox.delete(0, tk.END)
            for k, v in self.application_cache.items():
                if v[IMAGE_PATH] == self.image_path:
                    self.annotations_listbox.insert(tk.END, v[ANNOTATION])

    def draw_saved_bbox(self, canvas_coords, annotation, text_coords):
        rect_id = self.canvas.create_rectangle(canvas_coords, outline='red')
        print('rect id', rect_id)
        self.canvas.create_text(text_coords, text=annotation, anchor=tk.W, fill='red')

    def show_previous_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self.show_image()

    def show_next_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self.show_image()

    def start_bbox(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline='red'
        )
        print('rect id', self.rect)
        self.save_button.pack_forget()  # Hide the button when a new box is started

    def draw_bbox(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def stop_bbox(self, event):
        # Update the position of the "Save Annotations" button
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.save_button.place(x=cur_x, y=cur_y)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # Show popup with a textbox
        annotation_text = simpledialog.askstring("Annotation", "Enter annotation:")
        if annotation_text:
            self.add_annotation(annotation_text)

    def add_annotation(self, annotation_text):
        # Save bounding box coordinates and annotation to a file or process them as needed
        box_uuid = str(uuid.uuid4())
        canvas_coords = self.canvas.coords(self.rect)
        bbox_coords = {self.coords_name[n]: canvas_coords[n] for n in range(len(self.coords_name))}
        text_coords = bbox_coords[XUL] + 2, bbox_coords[YUL] + 5
        annotation_label = f'{annotation_text}|{self.rect}'
        self.canvas.create_text(text_coords, text=annotation_label, anchor=tk.W, fill='red')
        image_name = os.path.basename(self.image_path)

        # Add data for the output file
        print('Added the following:')
        new_row_data = {
            IMAGE_NAME: image_name,
            IMAGE_PATH: self.image_path,
            BBOX_UUID: box_uuid,
            BBOX_COORDS: bbox_coords,
            ANNOTATION: annotation_text
        }
        self.bbox_data = pd.concat([self.bbox_data, pd.DataFrame([new_row_data])], ignore_index=True)
        print(new_row_data)

        # Data to maintain draw boxes during each session
        self.application_cache[box_uuid] = {
            IMAGE_PATH: self.image_path,
            CANVAS_COORDS: canvas_coords,
            ANNOTATION: annotation_label,
            TEXT_COORDS: text_coords,
        }
        self.annotations_listbox.insert(tk.END, annotation_label)

    def save_annotations(self):
        # Save bounding box coordinates and annotation to a file or process them as needed
        print(self.bbox_data.to_dict(orient='records'))

    def clear_annotations(self):
        self.canvas.delete("all")
        self.save_button.pack_forget()  # Hide the button when clearing annotations

    def on_select_annotation(self, event):
        selected_index = self.annotations_listbox.curselection()
        if selected_index:
            self.selected_annotation_index = selected_index[0]

    def delete_selected_bbox(self):
        self.canvas.delete("all")
        if hasattr(self, 'selected_annotation_index'):
            selected_annotation = self.annotations_listbox.get(self.selected_annotation_index)
            new_application_cache = {}
            bboc_uuid_to_del = None
            for bbox_uuid, data in self.application_cache.items():
                if data[ANNOTATION] != selected_annotation:
                    new_application_cache[bbox_uuid] = data
                else:
                    bboc_uuid_to_del = bbox_uuid
            self.application_cache = new_application_cache
            self.bbox_data = self.bbox_data[self.bbox_data[BBOX_UUID] != bboc_uuid_to_del]

            for k, v in new_application_cache.items():
                if v[IMAGE_PATH] == self.image_path:
                    self.annotations_listbox.insert(tk.END, v[ANNOTATION])

                self.annotations_listbox.delete(self.selected_annotation_index)
            self.show_image()
        else:
            print("No annotation selected")

if __name__ == "__main__":
    root = tk.Tk()
    app = BoundingBoxApp(root)
    root.mainloop()
