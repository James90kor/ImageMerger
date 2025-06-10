import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageOps
import os
import webbrowser
# tkinterdnd2 라이브러리 임포트 시도
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    messagebox.showerror("라이브러리 오류", "tkinterdnd2 라이브러리를 찾을 수 없습니다.\n'pip install tkinterdnd2' 명령으로 설치해주세요.")
    exit()

class ImageMergerApp:
    def __init__(self, master):
        self.master = master # master는 이제 TkinterDnD.Tk() 인스턴스입니다.
        master.title("이미지 병합 프로그램 (고급)")
        master.geometry("800x650") # 새 옵션을 위해 높이 증가
        master.resizable(False, False)

        self.merge_options_list = [
            ("2개 이미지 병합 (가로)", "2_horiz"),
            ("2개 이미지 병합 (세로)", "2_vert"),
            ("3개 이미지 병합 (가로)", "3_horiz"),
            ("3개 이미지 병합 (세로)", "3_vert"),
            ("4개 이미지 병합 (2x2)", "4_grid")
        ]
        self.active_mode_value = self.merge_options_list[0][1] 
        self.current_gap_color = tk.StringVar(value="#FFFFFF")
        self.current_border_color = tk.StringVar(value="#000000") # 기본 테두리 색상: 검정

        self.image_paths_entries = []
        self.browse_buttons = []
        self.image_labels = []

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="groove", font=('Helvetica', 10))
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TEntry", padding=5, font=('Helvetica', 10))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Listbox", font=('Helvetica', 10))

        top_frame = ttk.Frame(master, padding=10)
        top_frame.pack(expand=True, fill=tk.BOTH)

        left_menu_frame = ttk.LabelFrame(top_frame, text="병합 방식 선택", padding=10)
        left_menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.right_options_frame = ttk.LabelFrame(top_frame, text="이미지 선택 및 옵션", padding=10)
        self.right_options_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        bottom_frame = ttk.Frame(master, padding="10 0 10 10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.mode_listbox = tk.Listbox(left_menu_frame, exportselection=False, 
                                       height=len(self.merge_options_list), 
                                       font=('Helvetica', 10), relief="groove", borderwidth=2)
        for item_text, _ in self.merge_options_list:
            self.mode_listbox.insert(tk.END, item_text)
        self.mode_listbox.select_set(0) 
        self.mode_listbox.pack(anchor=tk.NW, pady=3, fill=tk.X)
        self.mode_listbox.bind("<<ListboxSelect>>", self.on_mode_select)

        button_sub_frame = ttk.Frame(bottom_frame)
        button_sub_frame.pack(pady=(0,10))

        self.merge_btn = ttk.Button(button_sub_frame, text="이미지 합치기", command=self.process_image_merge)
        self.merge_btn.pack(side=tk.LEFT, padx=5)

        self.exit_btn = ttk.Button(button_sub_frame, text="종료", command=master.quit)
        self.exit_btn.pack(side=tk.LEFT, padx=5)

        self.footer_text = "제작: 알파카100 (https://alpaca100.tistory.com/)"
        self.footer_url = "https://alpaca100.tistory.com/"
        self.footer_label = tk.Label(bottom_frame, text=self.footer_text, fg="blue", cursor="hand2", font=('Helvetica', 9))
        self.footer_label.pack(pady=(5,0))
        self.footer_label.bind("<Button-1>", lambda e: self.open_link(self.footer_url))

        self.update_options_ui()

    def on_mode_select(self, event=None):
        selection_indices = self.mode_listbox.curselection()
        if selection_indices:
            selected_index = selection_indices[0]
            _, self.active_mode_value = self.merge_options_list[selected_index]
            self.update_options_ui()

    def update_options_ui(self):
        for widget in self.right_options_frame.winfo_children():
            widget.destroy()
        
        self.image_paths_entries.clear(); self.browse_buttons.clear(); self.image_labels.clear()

        mode = self.active_mode_value
        num_images = 2 if mode in ["2_horiz", "2_vert"] else 3 if mode in ["3_horiz", "3_vert"] else 4 if mode == "4_grid" else 0

        for i in range(num_images):
            label = ttk.Label(self.right_options_frame, text=f"이미지 {i+1}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            self.image_labels.append(label)

            entry = ttk.Entry(self.right_options_frame, width=60, state="readonly")
            entry.grid(row=i, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
            self.image_paths_entries.append(entry)
            entry.drop_target_register(DND_FILES)
            entry.dnd_bind('<<Drop>>', lambda event, e=entry: self.handle_drop(event, e))

            button = ttk.Button(self.right_options_frame, text="찾아보기", command=lambda e=entry: self.browse_file(e))
            button.grid(row=i, column=3, padx=5, pady=5)
            self.browse_buttons.append(button)
        
        current_row = num_images

        # -- 옵션 UI 생성 --
        self._create_option_widgets(current_row)
        self.right_options_frame.columnconfigure(1, weight=1)

    def _create_option_widgets(self, start_row):
        """오른쪽 프레임에 옵션 관련 위젯들을 생성합니다."""
        # 여백 크기
        ttk.Label(self.right_options_frame, text="여백 크기 (px):").grid(row=start_row, column=0, sticky=tk.W, padx=5, pady=(10,5))
        self.gap_spinbox = tk.Spinbox(self.right_options_frame, from_=0, to=100, width=7, increment=1, font=('Helvetica', 10))
        self.gap_spinbox.delete(0,"end"); self.gap_spinbox.insert(0,"10")
        self.gap_spinbox.grid(row=start_row, column=1, sticky=tk.W, padx=5, pady=(10,5))
        
        # 여백 색상
        ttk.Label(self.right_options_frame, text="여백 색상:").grid(row=start_row + 1, column=0, sticky=tk.W, padx=5, pady=5)
        self.gap_color_preview = self._create_color_picker(start_row + 1, self.current_gap_color)
        
        # 테두리 굵기
        ttk.Label(self.right_options_frame, text="테두리 굵기 (px):").grid(row=start_row + 2, column=0, sticky=tk.W, padx=5, pady=(10,5))
        self.border_spinbox = tk.Spinbox(self.right_options_frame, from_=0, to=50, width=7, increment=1, font=('Helvetica', 10))
        self.border_spinbox.delete(0,"end"); self.border_spinbox.insert(0,"0") # 기본값 0
        self.border_spinbox.grid(row=start_row + 2, column=1, sticky=tk.W, padx=5, pady=(10,5))

        # 테두리 색상
        ttk.Label(self.right_options_frame, text="테두리 색상:").grid(row=start_row + 3, column=0, sticky=tk.W, padx=5, pady=5)
        self.border_color_preview = self._create_color_picker(start_row + 3, self.current_border_color)

    def _create_color_picker(self, row, color_variable):
        """지정된 행에 색상 선택 위젯 세트를 생성하고 미리보기 레이블을 반환합니다."""
        preview_label = tk.Label(self.right_options_frame, text="    ", bg=color_variable.get(), relief="sunken", width=4, borderwidth=2)
        preview_label.grid(row=row, column=1, sticky=tk.W, padx=(5,0), pady=5)
        
        hex_entry = ttk.Entry(self.right_options_frame, textvariable=color_variable, width=10, font=('Helvetica', 10))
        hex_entry.grid(row=row, column=1, sticky=tk.W, padx=(50,5), pady=5)
        
        choose_button = ttk.Button(self.right_options_frame, text="색상표...", command=lambda: self._choose_color(color_variable, preview_label))
        choose_button.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)

        # 포커스가 벗어날 때 미리보기 업데이트 (버그 수정)
        hex_entry.bind("<FocusOut>", lambda event, var=color_variable, pl=preview_label: self._update_preview_from_entry(var, pl))
        return preview_label

    def _update_preview_from_entry(self, color_variable, preview_label):
        """Entry의 값으로 색상 미리보기를 업데이트합니다."""
        color_code = color_variable.get()
        try:
            preview_label.config(bg=color_code)
        except tk.TclError:
            pass # 잘못된 색상 코드는 무시

    def _choose_color(self, color_variable, preview_label):
        """색상 선택 대화상자를 열고 선택된 색상으로 변수와 미리보기를 업데이트합니다."""
        chosen_color = colorchooser.askcolor(title="색상 선택", initialcolor=color_variable.get())
        if chosen_color and chosen_color[1]:
            color_variable.set(chosen_color[1])
            preview_label.config(bg=chosen_color[1])

    def handle_drop(self, event, entry_widget):
        try:
            filepaths = self.master.splitlist(event.data)
            if filepaths:
                entry_widget.config(state="normal")
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, filepaths[0])
                entry_widget.config(state="readonly")
        except Exception as e:
            messagebox.showerror("드롭 처리 오류", f"파일 드롭 처리 중 오류 발생: {e}")

    def browse_file(self, entry_widget):
        file_path = filedialog.askopenfilename(title="이미지 파일 선택", filetypes=[("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.gif"), ("모든 파일", "*.*")])
        if file_path:
            entry_widget.config(state="normal"); entry_widget.delete(0, tk.END); entry_widget.insert(0, file_path); entry_widget.config(state="readonly")

    def open_link(self, url):
        try: webbrowser.open_new_tab(url)
        except Exception as e: messagebox.showerror("오류", f"링크를 여는 중 오류가 발생했습니다: {e}")

    def _validate_color(self, color_code, default_color):
        """색상 코드의 유효성을 검사하고, 유효하지 않으면 기본값을 반환합니다."""
        try:
            Image.new('RGB', (1,1), color_code)
            return color_code
        except ValueError:
            messagebox.showwarning("색상 오류", f"잘못된 색상 코드 '{color_code}'입니다.\n기본값 '{default_color}'로 대체합니다.")
            return default_color
    
    # [수정됨] _load_and_prepare_images: 테두리 관련 인자 제거
    def _load_and_prepare_images(self, num_expected):
        images, image_paths = [], [entry.get() for entry in self.image_paths_entries]
        if len(image_paths) != num_expected: return None
        for i, path in enumerate(image_paths):
            if not path:
                messagebox.showwarning("경고", f"{num_expected}개의 이미지를 모두 선택해주세요 (이미지 {i+1} 누락)."); return None
            try:
                img = Image.open(path)
                if img.mode == 'RGBA': img = img.convert('RGB')
                # [제거됨] 이 함수에서 테두리를 더 이상 추가하지 않음
                images.append(img)
            except Exception as e:
                messagebox.showerror("오류", f"이미지 로드/처리 중 오류 ({path}): {e}"); return None
        return images

    def process_image_merge(self):
        # 입력값 가져오기 및 검증
        try:
            gap = int(self.gap_spinbox.get())
            border_width = int(self.border_spinbox.get())
            if gap < 0 or border_width < 0:
                messagebox.showerror("입력 오류", "여백과 테두리 굵기는 0 이상이어야 합니다."); return
        except ValueError:
            messagebox.showerror("입력 오류", "여백과 테두리 굵기는 숫자여야 합니다."); return

        gap_color = self._validate_color(self.current_gap_color.get(), "#FFFFFF")
        border_color = self._validate_color(self.current_border_color.get(), "#000000")
        
        self.current_gap_color.set(gap_color); self.current_border_color.set(border_color)
        self._update_preview_from_entry(self.current_gap_color, self.gap_color_preview)
        self._update_preview_from_entry(self.current_border_color, self.border_color_preview)

        output_path = filedialog.asksaveasfilename(title="병합된 이미지 저장 위치 선택", defaultextension=".png", filetypes=[("PNG 파일", "*.png"), ("JPEG 파일", "*.jpg")])
        if not output_path: return

        # 모드에 따른 이미지 로드 및 병합
        mode = self.active_mode_value
        num_images = 2 if mode in ["2_horiz", "2_vert"] else 3 if mode in ["3_horiz", "3_vert"] else 4 if mode == "4_grid" else 0
        
        # [수정됨] _load_and_prepare_images 호출 시 테두리 인자 제거
        images = self._load_and_prepare_images(num_images)
        if not images: return

        # 병합 로직 수행
        merged_image = None
        if mode in ["2_horiz", "3_horiz"]: merged_image = self.merge_horizontal(images, gap, gap_color)
        elif mode in ["2_vert", "3_vert"]: merged_image = self.merge_vertical(images, gap, gap_color)
        elif mode == "4_grid": merged_image = self.merge_4_grid(images, gap, gap_color)
        
        if merged_image:
            # [추가됨] 병합 후 최종 이미지에 테두리 적용
            if border_width > 0:
                merged_image = ImageOps.expand(merged_image, border=border_width, fill=border_color)
            
            try:
                merged_image.save(output_path)
                messagebox.showinfo("성공", f"이미지가 성공적으로 병합되어 저장되었습니다:\n{output_path}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"이미지 저장 중 오류 발생: {e}")

    def merge_horizontal(self, images, gap, gap_color):
        min_height = min(img.height for img in images)
        resized_images = [img if img.height == min_height else img.resize((int(img.width * min_height / img.height), min_height), Image.Resampling.LANCZOS) for img in images]
        total_width = sum(img.width for img in resized_images) + gap * (len(resized_images) - 1)
        dst = Image.new('RGB', (total_width, min_height), gap_color)
        current_x = 0
        for img in resized_images:
            dst.paste(img, (current_x, 0)); current_x += img.width + gap
        return dst

    def merge_vertical(self, images, gap, gap_color):
        min_width = min(img.width for img in images)
        resized_images = [img if img.width == min_width else img.resize((min_width, int(img.height * min_width / img.width)), Image.Resampling.LANCZOS) for img in images]
        total_height = sum(img.height for img in resized_images) + gap * (len(resized_images) - 1)
        dst = Image.new('RGB', (min_width, total_height), gap_color)
        current_y = 0
        for img in resized_images:
            dst.paste(img, (0, current_y)); current_y += img.height + gap
        return dst

    def merge_4_grid(self, images, gap, gap_color):
        h1 = min(images[0].height, images[1].height)
        img0_r = images[0].resize((int(images[0].width * h1 / images[0].height), h1), Image.Resampling.LANCZOS)
        img1_r = images[1].resize((int(images[1].width * h1 / images[1].height), h1), Image.Resampling.LANCZOS)
        h2 = min(images[2].height, images[3].height)
        img2_r = images[2].resize((int(images[2].width * h2 / images[2].height), h2), Image.Resampling.LANCZOS)
        img3_r = images[3].resize((int(images[3].width * h2 / images[3].height), h2), Image.Resampling.LANCZOS)
        w_col1 = max(img0_r.width, img2_r.width); w_col2 = max(img1_r.width, img3_r.width)
        total_width = w_col1 + w_col2 + gap; total_height = h1 + h2 + gap
        dst = Image.new('RGB', (total_width, total_height), gap_color)
        dst.paste(img0_r, (0, 0)); dst.paste(img1_r, (w_col1 + gap, 0))
        dst.paste(img2_r, (0, h1 + gap)); dst.paste(img3_r, (w_col1 + gap, h1 + gap))
        return dst

if __name__ == "__main__":
    if 'TkinterDnD' in globals():
        root = TkinterDnD.Tk()
        app = ImageMergerApp(root)
        root.mainloop()
