
## 使い方（Mac では動作未確認）

### 仮想環境構築
おそらく python3.12 であればどのバージョンでも動作すると思います。動作確認は Python 3.12.10 で行っています。
インストールされていない場合は、以下の手順でインストールしてください。
1. [Python 3.12.10](https://www.python.org/downloads/release/python-31210/) をインストール。その際、"Add Python to PATH" にチェックを入れること。
1. コマンドプロンプト (Windows) または ターミナル (Mac) で、`python3.12 --version` を実行してもしバージョンが表示されない場合、python3.12の実行ファイル python.exe をコピペして、python3.12.exe にリネームする。  
   Windows の場合、C:\Users\<ユーザー名>\AppData\Local\Programs\Python\Python312 にあるはず。  
   Mac の場合、/usr/local/bin/python3.12 にあるはず。
1. bat ファイル (Windows) または command ファイル (Mac) をダブルクリックして実行し、仮想環境を構築する。  
   - Windows  
       build.bat をダブルクリックして実行する。
   - Mac  
       1. ターミナルで`chmod +x build.command`を実行して実行権限を与える。
       2. build.command をダブルクリックして実行する。


### GUIの起動
- Windows  
    run.bat をダブルクリックして実行する。
- Mac    
    1. 一度だけ、ターミナルで`chmod +x run.command`を実行して実行権限を与える。
    2. run.command をダブルクリックして実行する。


### GUIの使い方
**注意点**  
- マルチディスプレイ環境では、ウィンドウが起動時に表示されたディスプレイのみでクリック作業をすること。
- キャリブレーション後は、できるだけウィンドウサイズを変えないようにしてほしいです。（ウィンドウズの変更方法によっては異常が出る可能性があるため）


**3つのモード**  
GUIの右上のボタンの内、ハイライトされているボタンが現在のモードを示す。
- Calibration mode  
    画像上の2点をクリックして、対応する実世界座標を入力することで、画像座標と実世界座標の対応関係を設定するモード。C ボタンを押して入る。キャリブレーションが完了すると自動的に Add modeに入る。
- Add mode  
    各フレームで任意の点をクリックして、クリックされた点の画面上の座標と実世界座標を保存するモード。
- Delete mode  
    各フレームで任意の点をクリックして、クリックされた点に最も近い点を削除するモード。


**作業フロー**
1. （推奨：）全画面表示にする。
1. Ctrl+o で該当の動画ファイルを選択
1. （自動的に Calibration mode に入る。）
1. キャリブレーション点をクリックして、ポップアップに実世界座標を入力。これを2点繰り返す。x,y 座標が異なる2点を選ぶこと。
1. （自動的に Add mode に入る。）
1. 各フレームで任意の点をクリックして追加。消したい点があれば Delete mode に入り、該当の点をクリックして削除。


**ショートカットキー**
- Ctrl+o : 動画ファイルを開く
- Ctrl+s : データを保存
- a : Add mode に入る
- d : Delete mode に入る
- c : Calibration mode に入る
- → or X : 次のフレームへ
- ← or Z : 前のフレームへ
- j : ジャンプダイアログを表示して、指定したフレームへジャンプ
- e: settings ダイアログを表示（マーカーサイズやマーカー色の変更）
- h : ヘルプダイアログを表示
  

### 結果(.mat ファイル)の可視化
main.py で `plot_mat = True` とし、 `mat_path` に保存した .mat ファイルのパスを指定して実行すると、保存したデータを可視化できます。

### 結果(.mat ファイル)の構造
以下のように読み込んで、構造を確認できます。
```python
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
```

- `coords_raw`: 各フレームでクリックされた画像上の座標を保存した numpy.ndarray （画面座標系なのでおそらく不要なデータ）。
- `coords_real`: 各フレームでクリックされた実世界座標を保存した numpy.ndarray （こちらが欲しいデータのはず）。
- `coords_real[i][j, :]` は `i` 番目のフレームで、 `j` 番目にクリックされた点の実世界座標 [x, y] の numpy.ndarray。



## Working memo

### ボタン追加時
以下を変更する
- ボタンのラベルにショートカットキーを追記
- キーボードショートカットのバインド
- Help ダイアログ
- README.md の使い方セクション
- 


