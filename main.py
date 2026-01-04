import os
import click_app as ca

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    plot_mat = False
    matfilepath = './data/temp.mat'

    if not plot_mat:
        # run the click GUI
        print('Click GUI version:', ca.__version__)
        print('Starting Click GUI...')
        ca.run_gui()
    else:
        # plot from saved .mat file
        out = ca.load_click_mat(matfilepath)
        coords_raw = out['coords_raw']
        coords_real = out['coords_real']
        while True:
            frame_idx = int(input(f'Enter frame index (0 to {len(coords_real)-1}, -1 to exit): '))
            if frame_idx == -1:
                break
            ca.plot_clicks_on_frame(coords_real, frame_idx)