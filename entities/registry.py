"""Entity classes a map can create by name:  { "type": "Patroller", "args": { ... } }

To make your own entity available to maps, import it and add it to TYPES."""
from entities.door import Door
from entities.patroller import Patroller
from entities.pickup import Pickup

TYPES = {
    "Door": Door,
    "Pickup": Pickup,
    "Patroller": Patroller,
}
