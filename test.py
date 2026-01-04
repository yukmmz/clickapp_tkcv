from scipy.io import loadmat

matfilepath = './data/temp.mat'

data = loadmat(matfilepath)
craw = data.get('coords_raw', None)
creal = data.get('coords_real', None)
if craw is None or creal is None:
    raise ValueError('Invalid .mat file: missing coords_raw or coords_real')

coords_raw = craw[0]
coords_real = creal[0]

print(f'type(coords_real): {type(coords_real)}') # <class 'numpy.ndarray'>
print(f'coords_real.shape: {coords_real.shape}') # (N_frames,)
print(f'type(coords_real[0]): {type(coords_real[0])}') # <class 'numpy.ndarray'>
print(f'coords_real[0].shape: {coords_real[0].shape}') # (N_clicked_points, 2)
print(f'coords_real[0][0, :]: {coords_real[0][0, :]}') # [x, y] of the first clicked point in frame 0
## (same for coords_raw)
