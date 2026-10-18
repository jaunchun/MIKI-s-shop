"""Game settings. Edit this file to change the basics."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))     # the project folder

DEBUG = True                                          # False = no cheats, no debug keys, no terminal commands
MAP = os.path.join(ROOT, "maps", "school.json")       # which map to load at start school.json is main
TITLE = "MIKI's shop"
WINDOW_W = 1280
WINDOW_H = 720
