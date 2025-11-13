import json
import os
from typing import Any
from dataclasses import dataclass

DEBUG = True

cwd = os.path.dirname(os.path.realpath(__file__))
pdfile = os.path.join(cwd, 'pdfile')
witw = os.path.join(cwd, 'PenDriverPro/Plugins/PDFeature_Fig')
artifacts = os.path.join(witw, 'Content/Gameplay/Inventory/Items/Artifacts')  # TODO: Figure out the full path
evoaps = os.path.join(witw, 'Content/Gameplay/StatusEffects/ArtifactEffects/EvoAPs')

def run():

    raw_dtr = load_dtr(artifacts)
    raw_ap = load_ap(evoaps)


def load_dtr(file_src) -> dict[str, list[dict]]:
    """Load DTR_ files; file_src must be the full path as a string."""

    if DEBUG:
        print('Loading DTR_ files from:', file_src)

    # Getting files
    must_load = []
    for f in os.listdir(file_src):
        file_name = os.path.basename(f)
        if file_name.startswith('DTR_') and file_name.endswith('.json'):
            must_load.append(f)
        elif DEBUG:
            print('Skipping DTR_ file:', f)

    # Setup dict
    result: dict[str, list[dict]] = {
        'Shadows': [],
        'Currents': [],
        'Wilds': [],
    }

    # Load files
    for fname in must_load:
        name = os.path.splitext(fname)[0].removeprefix('DTR_') # PenDriverPro/.../DTR_ArtifactEffects_Shadows.uasset -> Shadows
        assert name in result, f'Unknown artifact type {name!r} from {fname!r}!'
        with open(os.path.join(file_src, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
            result[name] = data


    assert all(v for v in result.values()), (
        f'Not all artifact types were loaded! Missing {', '.join(repr(k) for k, v in result.items() if not v)}.'
    )
    return result



def load_ap(file_src):
    """Load AP_ files; file_src must be the full path as a string."""

    if DEBUG:
        print('Loading AP_ files from:', file_src)

    # Getting files
    must_load = []
    BANNED_FILES = ('AP_Test.json',)  # TODO: Proper names
    for f in os.listdir(file_src):
        file_name = os.path.basename(f)
        if file_name.startswith('AP_') and file_name.endswith('.json') and file_name not in BANNED_FILES:
            must_load.append(f)
        elif DEBUG:
            print('Skipping AP_ file:', f)

    # Setup dict (no base values, as of writing theres 151 files)
    result = {}
    # Load files
    for fname in must_load:
        name = os.path.splitext(fname)[0].removeprefix('AP_') # PenDriverPro/.../AP_AlwaysBatteryUp.uasset -> AlwaysBatteryUp
        with open(os.path.join(file_src, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
            result[name] = data

    return result


def parse_dtr(dtr: dict[str, Any]):
    pass




@dataclass(slots=True)
class AP:
    pip_cost: int
    cause_name: str  # AssetPathName / SubPahString. Double check having both is rquired?
    effect_name: str
    effectincreases: bool | None
    multiplier: float

def parse_ap(parsed_dtr, ap: dict[str, list[dict[str, Any]]]) -> dict[str, AP]:
    result = {}
    # For each proprety, map their inner name to their AP
    for artifact_name, artifact in ap.items():
        properties: dict = artifact[0]['Properties']  # Go where all relevant data is
        cause_cls = properties['Cause']['AssetPathName']  # Get cause class (to get name later)
        effect_cls = properties['Effect']['AssetPathName']  # Get effect class (to get name later)
        result.update({artifact_name: {  # Create AP
            'pip_cost': properties['PipCost'],  # Synergy
            'cause_name': '',  # TODO
            'effect_name': '',  # TODO
            'effectincreases' : properties.get('EffectIncreases'),  # Not mandatory? -> .get
            'multiplier': properties['Multiplier']  # Multiplier (effect strength?)
        }})
    return result
