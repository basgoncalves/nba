"""
Load Full_Body_with_ball.osim using the OpenSim Python API and print
a quick summary of the model (bodies, joints, coordinates, muscles).

Run with the Python interpreter that has OpenSim's bindings installed
(typically the conda env shipped with the OpenSim GUI, or pip-installed
opensim wheels).
"""

from pathlib import Path
import opensim as osim

MODEL_PATH = Path(__file__).resolve().parent / "Full_Body_with_ball.osim"


def load_model(path: Path) -> osim.Model:
    """Load an .osim file and finalize it so the underlying SimTK system is built."""
    if not path.is_file():
        raise FileNotFoundError(f"Model not found: {path}")

    model = osim.Model(str(path))
    model.finalizeFromProperties()
    # initSystem returns the default state and forces the model to be fully realized.
    state = model.initSystem()
    return model, state


def summarize(model: osim.Model) -> None:
    print(f"Model name : {model.getName()}")
    print(f"Source file: {model.getInputFileName()}")
    print(f"Bodies     : {model.getBodySet().getSize()}")
    print(f"Joints     : {model.getJointSet().getSize()}")
    print(f"Coords     : {model.getCoordinateSet().getSize()}")
    print(f"Muscles    : {model.getMuscles().getSize()}")
    print(f"Forces     : {model.getForceSet().getSize()}")
    print(f"Markers    : {model.getMarkerSet().getSize()}")

    # First few coordinates as a sanity check
    coords = model.getCoordinateSet()
    print("\nFirst 10 coordinates:")
    for i in range(min(10, coords.getSize())):
        c = coords.get(i)
        print(f"  - {c.getName():30s}  default={c.getDefaultValue(): .4f}")


if __name__ == "__main__":
    model, state = load_model(MODEL_PATH)
    summarize(model)
