from setuptools import setup

APP = ['memdam/recorder/main.py']
DATA_FILES = ['heart.png', 'bin/wacaw']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,
    },
    'includes': ['sip', 'PyQt4'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
