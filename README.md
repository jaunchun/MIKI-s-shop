# MIKI's shop - low-poly horror game

C++ engine (window, input, OpenGL renderer) built as the Python module `engine`; game logic and maps in Python and JSON.

**Everything is explained in [DOCS.md](DOCS.md)**: building maps, adding entities, debug and cheats, changing the engine.

Quick start (CLion):
1. Open this folder as the project root. Create a venv: `python -m venv .venv`
2. Settings > Build, Execution, Deployment > CMake > CMake options:
   `-DPython_EXECUTABLE=<project>/.venv/Scripts/python.exe` (put the whole option in quotes if the path has spaces)
3. Tools > CMake > Reload CMake Project, pick the `engine` target, Build.
4. In the terminal (venv active): `python main.py`
