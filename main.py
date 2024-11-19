# Compilation mode, support OS-specific options
# nuitka-project: --standalone
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --macos-create-app-bundle
#    nuitka-project: --macos-app-icon=logo.icns

# The PySide6 plugin covers qt-plugins
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-qt-plugins=qml
# nuitka-project: --output-dir=dist

from gui.__main__ import main

if __name__ == "__main__":
    main()
