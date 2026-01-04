import os
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, colorchooser
from PIL import Image, ImageTk
from scipy.io import savemat

from . import __version__
# Configuration constants (moved into ClickGUI as class attributes)


__all__ = [
    'load_click_mat',
    'plot_clicks_on_frame',
	'ClickGUI',
	'run_gui',
]


def load_click_mat(filepath):
    """
    click_gui.py で作成した.matファイルを読み込んで、
    保存前と同じ形式のデータにする関数
	
	coords_raw[i] is np.ndarray of shape (n_points, 2) where n_points may vary across frames
	same for coords_real
    """
    from scipy.io import loadmat
    data = loadmat(filepath)
    coords_raw = data.get('coords_raw', None)
    coords_real = data.get('coords_real', None)
    if coords_raw is None or coords_real is None:
        raise ValueError('Invalid .mat file: missing coords_raw or coords_real')
	


    coords_raw = coords_raw[0]
    coords_real = coords_real[0]    

    out = {
        'coords_raw': coords_raw,
        'coords_real': coords_real
    }
    return out


def plot_clicks_on_frame(coords, frame=0):
	"""
	指定されたフレームのクリック点を表示する関数
	coords_raw: クリック点のリスト [[x1, y1], [x2, y2], ...]
	"""
	if frame < 0 or frame >= len(coords):
		# raise ValueError('Invalid frame index')
		print('Invalid frame index')
		return

	points = coords[frame]
	if len(points) == 0:
		print('No points to plot on this frame.')
		return
	
	x_vals = points[:, 0]
	y_vals = points[:, 1]

	plt.figure()
	plt.scatter(x_vals, y_vals, c='red', marker='o')
	plt.title('Click Points on Frame')
	plt.xlabel('X Coordinate')
	plt.ylabel('Y Coordinate')
	plt.grid()
	plt.show()


class ClickGUI:
	# Configuration constants (colors, radii, mode names) as class attributes
	MODE_NONE = 'none'
	MODE_CALIB = 'calib'
	MODE_ADD = 'add'
	MODE_DEL = 'del'

	CALIB_POINT_COLOR = (0, 255, 0)  # BGR for OpenCV
	DATA_POINT_COLOR = (255, 0, 0)
	CALIB_POINT_RADIUS = 4
	DATA_POINT_RADIUS = 4
	SHOW_CALIB_POINT = True
	def __init__(self, master=None, video_path=None):
		self.master = master or tk.Tk()
		self.master.title(f'Click GUI ver{__version__}')

		# top log
		# top log (scrollable)
		log_frame = tk.Frame(self.master)
		log_frame.pack(fill='x')
		self.log_text = tk.Text(log_frame, height=8, wrap='none')
		self.log_text.pack(side='left', fill='x', expand=True)
		scrollbar = tk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
		scrollbar.pack(side='right', fill='y')
		self.log_text.config(yscrollcommand=scrollbar.set)

		# toolbar
		toolbar = tk.Frame(self.master)
		toolbar.pack(fill='x')
		# left-aligned controls
		left = tk.Frame(toolbar)
		left.pack(side='left')
		# right-aligned mode controls
		right = tk.Frame(toolbar)
		right.pack(side='right')
		# left buttons
		tk.Button(left, text='Open (Ctrl+O)', command=self.open_file).pack(side='left')
		tk.Button(left, text='Save (Ctrl+S)', command=self.save).pack(side='left')
		tk.Button(left, text='Settings (E)', command=self.open_settings).pack(side='left')
		tk.Button(left, text='Help (H)', command=self.help_dialog).pack(side='left')
		# right (mode) buttons
		tk.Label(right, text='Mode:').pack(side='left')
		self.btn_calib = tk.Button(right, text='Calib (C)', command=self.enter_calib_mode)
		self.btn_calib.pack(side='left')
		self.btn_add = tk.Button(right, text='Add (A)', command=self.enter_add_mode)
		self.btn_add.pack(side='left')
		self.btn_del = tk.Button(right, text='Del (D)', command=self.enter_del_mode)
		self.btn_del.pack(side='left')

		# image display
		# Label ではなく Canvas を使用し、ウィンドウ追従するように設定
		self.canvas = tk.Canvas(self.master, bg="white")
		self.canvas.pack(fill=tk.BOTH, expand=True) # expand=Trueで広がるようにする
		self.canvas.bind('<Button-1>', self.on_canvas_click)
		self.canvas.bind('<Configure>', self.on_resize) # リサイズ検知

		# 座標変換・リサイズ用の変数
		self.scale = 1.0
		self.offset_x = 0
		self.offset_y = 0
		self.canvas_w = 640 # 初期値
		self.canvas_h = 480 # 初期値

		# navigation buttons under the plot
		nav_frame = tk.Frame(self.master)
		nav_frame.pack()
		tk.Button(nav_frame, text='Prev (←, Z)', command=self.prev_frame).pack(side='left')
		tk.Button(nav_frame, text='Next (→, X)', command=self.next_frame).pack(side='left')
		# Jump button between Next and frame label
		tk.Button(nav_frame, text='Jump (j)', command=self.jump_dialog).pack(side='left', padx=(6, 0))
		# frame counter label to the right of Next/Jump
		self.frame_label = tk.Label(nav_frame, text='Frame: 0/0')
		self.frame_label.pack(side='left', padx=8)


		# state
		self.cap = None
		self.frame_count = 0
		self.current_frame_idx = 0
		self.current_image = None
		self.photo = None

		# do not start in calibration mode immediately; enter calib after opening a video

		# calibration
		self.calib_img = []
		self.calib_real = []
		self._transform = None

		# coords per frame
		self.coords_raw = []
		self.coords_real = []

		# keyboard bindings (shortcuts)
		self.master.bind('<Right>', lambda e: self.next_frame())
		self.master.bind('<Left>', lambda e: self.prev_frame())
		self.master.bind('<z>', lambda e: self.prev_frame())
		self.master.bind('<x>', lambda e: self.next_frame())
		self.master.bind('<a>', lambda e: self.enter_add_mode())
		self.master.bind('<d>', lambda e: self.enter_del_mode())
		self.master.bind('<c>', lambda e: self.enter_calib_mode())
		self.master.bind('<j>', lambda e: self.jump_dialog())
		self.master.bind('<Control-s>', lambda e: self.save())
		self.master.bind('<Control-o>', lambda e: self.open_file())
		self.master.bind('<e>', lambda e: self.open_settings())

		if video_path:
			self.load_video(video_path)
	
	
	def on_resize(self, event):
		"""ウィンドウサイズが変わったときに呼ばれる"""
		self.canvas_w = event.width
		self.canvas_h = event.height
		# 動画が読み込み済みなら再描画してサイズを合わせる
		if self.cap and self.current_image is not None:
			self.show_frame(self.current_frame_idx, log_flag=False)


	def log(self, msg):
		self.log_text.insert('end', msg + '\n')
		self.log_text.see('end')

	def open_file(self):
		path = filedialog.askopenfilename(filetypes=[('Video', '*.mp4;*.avi;*.mov;*.mkv'), ('All', '*.*')])
		if path:
			self.log(f'Opening {path}')
			self.load_video(path)

	def load_video(self, path):
		if not os.path.exists(path):
			self.log('File not found')
			return
		if self.cap:
			self.cap.release()
		self.cap = cv2.VideoCapture(path)
		if not self.cap.isOpened():
			self.log('Unable to open video')
			return
		self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
		self.current_frame_idx = 0
		self.coords_raw = [[] for _ in range(self.frame_count)]
		self.coords_real = [[] for _ in range(self.frame_count)]
		self.log(f'Video loaded: {self.frame_count} frames')
		# enter calibration mode after loading a video so highlight is correct
		self.enter_calib_mode()
		self.show_frame(self.current_frame_idx, log_flag=True)

	def read_frame(self, idx):
		if not self.cap:
			return None
		self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
		ret, frame = self.cap.read()
		if not ret:
			return None
		return frame

	
	def show_frame(self, idx, log_flag=False):
		frame = self.read_frame(idx)
		if frame is None:
			self.log('Failed to read frame')
			return
		self.current_image = frame.copy()
		disp = frame.copy()
		
		# draw overlays (元の解像度の画像に円を描く)
		self.draw_overlays(disp, idx)
		
		# --- ここからリサイズ処理 ---
		vid_h, vid_w = disp.shape[:2]
		
		# キャンバスサイズに合わせてスケールを計算（アスペクト比維持）
		if self.canvas_w > 1 and self.canvas_h > 1:
			scale_w = self.canvas_w / vid_w
			scale_h = self.canvas_h / vid_h
			self.scale = min(scale_w, scale_h)
		else:
			self.scale = 1.0

		new_w = int(vid_w * self.scale)
		new_h = int(vid_h * self.scale)
		
		# センタリング用のオフセット計算
		self.offset_x = (self.canvas_w - new_w) // 2
		self.offset_y = (self.canvas_h - new_h) // 2

		# 画像リサイズ
		disp_resized = cv2.resize(disp, (new_w, new_h))
		disp_rgb = cv2.cvtColor(disp_resized, cv2.COLOR_BGR2RGB)
		
		img = Image.fromarray(disp_rgb)
		self.photo = ImageTk.PhotoImage(img)
		
		# Canvasに描画 (前の画像を消してから描画)
		self.canvas.delete("all")
		self.canvas.create_image(self.offset_x, self.offset_y, image=self.photo, anchor=tk.NW)
		# ---------------------------

		if log_flag:
			self.log(f'Showing frame {idx+1}/{self.frame_count}')
		try:
			self.frame_label.config(text=f'Frame: {idx+1}/{self.frame_count}')
		except Exception:
			pass


	def draw_overlays(self, img, idx):
		# draw calibration points in red (optional)
		if getattr(self, 'SHOW_CALIB_POINT', True):
			for (x, y) in self.calib_img:
				cv2.circle(img, (int(x), int(y)), self.CALIB_POINT_RADIUS, self.CALIB_POINT_COLOR, -1)
		# draw added points in green
		pts = self.coords_raw[idx] if 0 <= idx < len(self.coords_raw) else []
		for (x, y) in pts:
			cv2.circle(img, (int(x), int(y)), self.DATA_POINT_RADIUS, self.DATA_POINT_COLOR, -1)

	def on_canvas_click(self, event):
		if self.current_image is None:
			return
		
		# --- 座標変換処理 ---
		screen_x = event.x
		screen_y = event.y

		# 画面座標 -> 元の動画座標への逆変換
		# (画面座標 - 余白) / 倍率 = 元の座標
		original_x = (screen_x - self.offset_x) / self.scale
		original_y = (screen_y - self.offset_y) / self.scale

		# 動画の範囲内かチェック
		img_h, img_w = self.current_image.shape[:2]
		if not (0 <= original_x < img_w and 0 <= original_y < img_h):
			# 黒帯部分をクリックした場合は無視
			return

		# 後続の処理のために x, y を上書き
		x = original_x
		y = original_y
		# ------------------

		self.log(f'Clicked at image coords ({x:.1f}, {y:.1f}) in mode {self.mode}')
		
		if self.mode == self.MODE_NONE:
			messagebox.showwarning('Warning', 'Click ignored: select a mode first')
			return
		if self.mode == self.MODE_CALIB:
			self.handle_calib_click(x, y)
		elif self.mode == self.MODE_ADD:
			self.handle_add_click(x, y)
		elif self.mode == self.MODE_DEL:
			self.handle_del_click(x, y)

	def handle_calib_click(self, x, y):
		self.calib_img.append((x, y))
		self.log(f'Calibration image point recorded: {(x, y)}')
		# immediately redraw so the red calibration marker is visible before the popup
		self.show_frame(self.current_frame_idx)
		# ask for real coordinate
		ans = simpledialog.askstring('Real coord', 'Enter real-world coordinate as "x,y":')
		if ans:
			try:
				xr, yr = [float(s.strip()) for s in ans.split(',')]
			except Exception:
				messagebox.showerror('Error', 'Invalid format, use x,y')
				self.calib_img.pop()
				# update display to remove the temporary marker
				self.show_frame(self.current_frame_idx)
				return
			self.calib_real.append((xr, yr))
			self.log(f'Calibration real point recorded: {(xr, yr)}')
		else:
			self.calib_img.pop()
			# update display to remove the temporary marker
			self.show_frame(self.current_frame_idx)
			return
		if len(self.calib_img) >= 2:
			self.compute_transform()
			# enter add mode via the method so UI/highlight updates occur
			self.enter_add_mode()
			self.log('Calibration complete')
			self.show_frame(self.current_frame_idx)

	def compute_transform(self):
		p0 = np.array(self.calib_img[0], dtype=float)
		p1 = np.array(self.calib_img[1], dtype=float)
		r0 = np.array(self.calib_real[0], dtype=float)
		r1 = np.array(self.calib_real[1], dtype=float)
		# Use simple per-axis linear mapping (no rotation):
		# X = r0_x + (x - p0_x) * scale_x
		# Y = r0_y + (y - p0_y) * scale_y
		dx_img = p1[0] - p0[0]
		dy_img = p1[1] - p0[1]
		dx_real = r1[0] - r0[0]
		dy_real = r1[1] - r0[1]
		if dx_img == 0:
			self.log('Warning: image points have identical x; using scale_x=1.0')
			scale_x = 1.0
		else:
			scale_x = dx_real / dx_img
		if dy_img == 0:
			self.log('Warning: image points have identical y; using scale_y=1.0')
			scale_y = 1.0
		else:
			scale_y = dy_real / dy_img
		self._transform = {'p0': p0, 'r0': r0, 'scale_x': scale_x, 'scale_y': scale_y}
		self.log(f'Computed linear transform: scale_x={scale_x:.6f}, scale_y={scale_y:.6f}')
		# recompute all real coordinates from raw coords using new transform
		self.update_coords_real_from_raw()


	def update_coords_real_from_raw(self):
		"""Recompute coords_real from coords_raw using current calibration transform.
		If no transform is available, coords_real entries become [None, None].
		"""
		if not hasattr(self, 'coords_raw') or self.coords_raw is None:
			return
		# ensure coords_real has same frame count
		if len(self.coords_real) != len(self.coords_raw):
			self.coords_real = [[] for _ in range(len(self.coords_raw))]
		for i, pts in enumerate(self.coords_raw):
			new_real = []
			for (x, y) in pts:
				if self._transform is None:
					new_real.append([None, None])
				else:
					real = self.pixel_to_real(x, y)
					new_real.append(real if real is not None else [None, None])
			self.coords_real[i] = new_real
		self.log('Recomputed coords_real from coords_raw using current calibration')

	def pixel_to_real(self, x, y):
		if self._transform is None:
			return None
		p = np.array([x, y], dtype=float)
		p_rel = p - self._transform['p0']
		real_x = float(self._transform['r0'][0] + p_rel[0] * self._transform.get('scale_x', 1.0))
		real_y = float(self._transform['r0'][1] + p_rel[1] * self._transform.get('scale_y', 1.0))
		return [real_x, real_y]

	def handle_add_click(self, x, y):
		i = self.current_frame_idx
		self.coords_raw[i].append([x, y])
		real = self.pixel_to_real(x, y)
		if real is None:
			self.log('Not calibrated: real coordinates unavailable')
			self.coords_real[i].append([None, None])
		else:
			self.coords_real[i].append(real)
			n_points = len(self.coords_raw[i])
			self.log(f'[{n_points}] Added point real coords: ({real[0]:.3f}, {real[1]:.3f})')
		self.show_frame(i)

	def handle_del_click(self, x, y):
		i = self.current_frame_idx
		pts = self.coords_raw[i]
		if not pts:
			self.log('No points to delete on this frame')
			return
		dists = [math.hypot(px - x, py - y) for (px, py) in pts]
		idx = int(np.argmin(dists))
		removed_raw = pts.pop(idx)
		removed_real = self.coords_real[i].pop(idx) if idx < len(self.coords_real[i]) else None
		self.log(f'Deleted point raw {removed_raw}, real {removed_real}')
		self.show_frame(i)

	def enter_calib_mode(self):
		self.mode = self.MODE_CALIB
		self.calib_img = []
		self.calib_real = []
		self._transform = None
		self.log('Entered calibration mode: click two image points and enter real coords')
		self._update_mode_highlight()

	def enter_add_mode(self):
		# require calibration before allowing add mode
		if self._transform is None:
			messagebox.showwarning('Not calibrated', 'Please calibrate before entering Add mode')
			return
		self.mode = self.MODE_ADD
		self.log('Entered add mode: click to add points')
		self._update_mode_highlight()

	def enter_del_mode(self):
		self.mode = self.MODE_DEL
		self.log('Entered delete mode: click near a point to delete it')
		self._update_mode_highlight()

	def _update_mode_highlight(self):
		# update button appearances to reflect current mode
		bg_default = None
		try:
			bg_default = self.master.cget('bg')
		except Exception:
			bg_default = None
		# reset all (if they exist)
		for b in ('btn_calib', 'btn_add', 'btn_del'):
			if hasattr(self, b):
				try:
					getattr(self, b).config(relief='raised', bg=bg_default)
				except Exception:
					pass
		# highlight active
		try:
			# compute lighter hex colors from configured BGRs
			calib_bg = self._bgr_to_hex(self._lighten_bgr(self.CALIB_POINT_COLOR, 0.6))
			add_bg = self._bgr_to_hex(self._lighten_bgr(self.DATA_POINT_COLOR, 0.6))
			# apply highlights
			if self.mode == self.MODE_CALIB:
				self.btn_calib.config(relief='sunken', bg=calib_bg)
			elif self.mode == self.MODE_ADD:
				self.btn_add.config(relief='sunken', bg=add_bg)
			elif self.mode == self.MODE_DEL:
				self.btn_del.config(relief='sunken', bg='lightcoral')
		except Exception:
			pass

	def prev_frame(self):
		if self.frame_count == 0:
			return
		self.current_frame_idx = max(0, self.current_frame_idx - 1)
		self.show_frame(self.current_frame_idx, log_flag=True)

	def next_frame(self):
		if self.frame_count == 0:
			return
		self.current_frame_idx = min(self.frame_count - 1, self.current_frame_idx + 1)
		self.show_frame(self.current_frame_idx, log_flag=True)

	def jump_dialog(self):
		"""Ask user for a frame number and jump to it if valid."""
		if self.frame_count == 0:
			messagebox.showwarning('No video', 'No video loaded to jump within')
			return
		ans = simpledialog.askstring('Jump', f'Enter frame number (1-{self.frame_count}):', parent=self.master)
		if ans is None:
			return
		try:
			n = int(ans)
		except Exception:
			messagebox.showerror('Error', 'Invalid frame number')
			return
		if n < 1 or n > self.frame_count:
			messagebox.showwarning('Out of range', f'Frame must be between 1 and {self.frame_count}')
			return
		# convert to 0-based index and jump
		self.current_frame_idx = n - 1
		self.show_frame(self.current_frame_idx, log_flag=True)

	def save(self):
		path = filedialog.asksaveasfilename(defaultextension='.mat', filetypes=[('MAT', '*.mat')])
		if not path:
			return
		try:
			savemat(path, {'coords_raw': np.array(self.coords_raw, dtype=object), 'coords_real': np.array(self.coords_real, dtype=object)})
			self.log(f'Saved .mat to {path}')
		except Exception as e:
			self.log(f'Error saving: {e}')

	def help_dialog(self):
		txt = (
			'Usage:\n'
			'- Open: choose video file.\n'
			'- Calib (c): click two image points and enter real coords as x,y.\n'
			'- Add (a): click to add points; real coords computed if calibrated.\n'
			'- Del (d): click near a point to delete it.\n'
			'- Prev/Next (←/→ or Z/X): navigate frames.\n'
			'- Jump (j): enter frame number to jump to.\n'
			'- Settings (E): open settings dialog to adjust colors and sizes.\n'
			'- Save (Ctrl+S): save coords to .mat (requires scipy) or .npz fallback.\n'
		)
		messagebox.showinfo('Help', txt)

	def _bgr_to_hex(self, bgr):
		# bgr is (B, G, R)
		rgb = (int(bgr[2]), int(bgr[1]), int(bgr[0]))
		return '#%02x%02x%02x' % rgb

	def _hex_to_bgr(self, hexstr):
		if hexstr.startswith('#'):
			hexstr = hexstr[1:]
		if len(hexstr) != 6:
			raise ValueError('Invalid color hex')
		r = int(hexstr[0:2], 16)
		g = int(hexstr[2:4], 16)
		b = int(hexstr[4:6], 16)
		return (b, g, r)

	def _lighten_bgr(self, bgr, factor=0.6):
		"""Return a lighter BGR tuple moved toward white by factor [0..1]."""
		b, g, r = bgr
		r_l = int(r + (255 - r) * factor)
		g_l = int(g + (255 - g) * factor)
		b_l = int(b + (255 - b) * factor)
		return (b_l, g_l, r_l)

	def open_settings(self):
		win = tk.Toplevel(self.master)
		win.title('Settings')
		# Radii
		lbl1 = tk.Label(win, text='Calibration marker radius:')
		lbl1.grid(row=0, column=0, sticky='w', padx=6, pady=6)
		ent_calib = tk.Entry(win)
		ent_calib.insert(0, str(self.CALIB_POINT_RADIUS))
		ent_calib.grid(row=0, column=1, padx=6, pady=6)

		lbl2 = tk.Label(win, text='Data marker radius:')
		lbl2.grid(row=1, column=0, sticky='w', padx=6, pady=6)
		ent_add = tk.Entry(win)
		ent_add.insert(0, str(self.DATA_POINT_RADIUS))
		ent_add.grid(row=1, column=1, padx=6, pady=6)

		# Colors
		lbl3 = tk.Label(win, text='Calibration color:')
		lbl3.grid(row=2, column=0, sticky='w', padx=6, pady=6)
		calib_color_var = tk.StringVar(value=self._bgr_to_hex(self.CALIB_POINT_COLOR))
		lbl_calib_col = tk.Label(win, text=calib_color_var.get(), width=10)
		lbl_calib_col.grid(row=2, column=1, padx=6, pady=6)
		def pick_calib():
			res = colorchooser.askcolor(color=calib_color_var.get(), parent=win)
			if res and res[1]:
				calib_color_var.set(res[1])
				lbl_calib_col.config(text=res[1])
		btn_calib = tk.Button(win, text='Choose', command=pick_calib)
		btn_calib.grid(row=2, column=2, padx=6, pady=6)

		lbl4 = tk.Label(win, text='Data marker color:')
		lbl4.grid(row=3, column=0, sticky='w', padx=6, pady=6)
		add_color_var = tk.StringVar(value=self._bgr_to_hex(self.DATA_POINT_COLOR))
		lbl_add_col = tk.Label(win, text=add_color_var.get(), width=10)
		lbl_add_col.grid(row=3, column=1, padx=6, pady=6)
		def pick_add():
			res = colorchooser.askcolor(color=add_color_var.get(), parent=win)
			if res and res[1]:
				add_color_var.set(res[1])
				lbl_add_col.config(text=res[1])
		btn_add = tk.Button(win, text='Choose', command=pick_add)
		btn_add.grid(row=3, column=2, padx=6, pady=6)

		# Show calibration points toggle
		show_calib_var = tk.BooleanVar(value=getattr(self, 'SHOW_CALIB_POINT', True))
		chk_show = tk.Checkbutton(win, text='Show calibration points', variable=show_calib_var)
		chk_show.grid(row=4, column=0, columnspan=2, sticky='w', padx=6, pady=6)

		def apply():
			# validate and apply
			try:
				calib_r = int(ent_calib.get())
			except Exception:
				messagebox.showerror('Error', 'Invalid calibration radius')
				return
			try:
				data_r = int(ent_add.get())
			except Exception:
				messagebox.showerror('Error', 'Invalid add radius')
				return
			# convert colors
			try:
				calib_bgr = self._hex_to_bgr(calib_color_var.get())
				add_bgr = self._hex_to_bgr(add_color_var.get())
			except Exception:
				messagebox.showerror('Error', 'Invalid color value')
				return
			# set attributes
			self.CALIB_POINT_RADIUS = calib_r
			self.DATA_POINT_RADIUS = data_r
			self.CALIB_POINT_COLOR = calib_bgr
			self.DATA_POINT_COLOR = add_bgr
			# apply show calibration toggle
			self.SHOW_CALIB_POINT = bool(show_calib_var.get())
			# refresh UI: update mode button highlights and redraw frame
			self._update_mode_highlight()
			self.log(f'Updated settings: calib_r={calib_r}, data_r={data_r}, calib_col={calib_color_var.get()}, add_col={add_color_var.get()}')
			self.show_frame(self.current_frame_idx)
			win.destroy()

		# entries are ent_calib and ent_add

		btn_apply = tk.Button(win, text='Apply', command=apply)
		btn_apply.grid(row=5, column=1, padx=6, pady=8)
		btn_cancel = tk.Button(win, text='Cancel', command=win.destroy)
		btn_cancel.grid(row=5, column=2, padx=6, pady=8)



def run_gui(video_path=None):
	root = tk.Tk()
	app = ClickGUI(root, video_path=video_path)
	root.mainloop()


if __name__ == '__main__':
	import sys
	vp = sys.argv[1] if len(sys.argv) > 1 else None
	run_gui(video_path=vp)

