# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['D:/04_DevelopReleas/02_ncINFO/GeoMarineSir'],
    binaries=[],
    datas=[
        ('D:/04_DevelopReleas/02_ncINFO/GeoMarineSir/style.qss','.'),
        ('E:/Users/chens/anaconda3/envs/ncinfo_dev/Lib/site-packages/cartopy','cartopy'),
        ('E:/Users/chens/anaconda3/envs/ncinfo_dev/Lib/site-packages/geopandas','geopandas'),
        ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'doctest', 'unittest', 'pydoc',
        'tkinter', 'sqlite3', # 排除不需要的标准库
        'numpy.random.tests', # 排除大型库中的测试文件
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GeospatialTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
