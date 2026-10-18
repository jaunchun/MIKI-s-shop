import glob
import os
import sys
import traceback

# let Python find the MinGW runtime DLLs that ship with CLion's compiler
if sys.platform == "win32":
    for d in glob.glob(r"C:\Program Files\JetBrains\CLion*\bin\mingw\bin"):
        os.add_dll_directory(d)

from core.game import Game
from core.mapload import MapError


def main():
    try:
        game = Game()
    except MapError as e:
        print(f"[map] {e}")
        sys.exit(1)

    code = 0
    try:
        game.run()
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
        code = 1
    game.shutdown(code)


if __name__ == "__main__":
    main()
