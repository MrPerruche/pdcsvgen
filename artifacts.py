import json
import os
import csv
from collections import defaultdict
from typing import Any
from dataclasses import dataclass

import fm

DEBUG = True

cwd = os.path.dirname(os.path.realpath(__file__))
pdfile = os.path.join(cwd, 'pdfiles')
witw = os.path.join(pdfile, 'PenDriverPro/Plugins/PDFeature_Fig')
artifacts = os.path.join(witw, 'Content/Gameplay/Inventory/Items/Artifacts')
evoaps = os.path.join(witw, 'Content/Gameplay/StatusEffects/ArtifactEffects/EvoAPs')
aces = os.path.join(witw, 'Content/Gameplay/StatusEffects/ArtifactEffects/ACEs')



def run():

    raw_dtr = load_dtr(artifacts)
    raw_ap = load_ap(evoaps)
    raw_ace = load_ace(aces)
    parsed = {biome: parse_artifact_type(dtr, raw_ap, raw_ace) for biome, dtr in raw_dtr.items()}
    save_parsed_to_csv(parsed)


def save_parsed_to_csv(parsed: dict[str, dict[str, dict[str, str]]], output_dir="output"):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for biome, data in parsed.items():
        if not data:
            continue  # Skip if empty

        # Get all column names by combining keys from all lines
        all_columns = set()
        for line_data in data.values():
            all_columns.update(line_data.keys())
        base_columns = ['Name', 'Description', 'InnerName', 'Cause', 'Effect', 'PipCost', 'Multiplier', 'Probability']
        extra_columns = sorted(c for c in all_columns if c not in base_columns)
        all_columns = base_columns + extra_columns

        # Write CSV
        csv_path = os.path.join(output_dir, f"{biome}.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_columns)
            writer.writeheader()
            for line, line_data in data.items():
                # Include the line key if you want
                row = {col: line_data.get(col, "") for col in all_columns}
                writer.writerow(row)


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
        name = os.path.splitext(fname)[0].removeprefix('DTR_ArtifactEffects_') # PenDriverPro/.../DTR_ArtifactEffects_Shadows.uasset -> Shadows
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
    BANNED_FILES = ('AP_TestPair.json',)
    for f in os.listdir(file_src):
        file_name = os.path.basename(f)
        if file_name.startswith('AP_') and file_name.endswith('.json') and file_name not in BANNED_FILES:
            must_load.append(f)
        elif DEBUG:
            print('Skipping AP_ file:', f)

    # Setup dict (no base values, as of writing theres 151 files)
    result: dict[str, list[dict]] = {}
    # Load files
    for fname in must_load:
        name = os.path.splitext(fname)[0] # PenDriverPro/.../AP_AlwaysBatteryUp.uasset -> AlwaysBatteryUp
        with open(os.path.join(file_src, fname), 'r', encoding='utf-8') as f:
            data: list[dict] = json.load(f)
            result[name] = data

    return result


@dataclass(slots=True)
class ACEName:
    cause_up_name: str | None
    cause_down_name: str | None
    effect_up_name: str | None
    effect_down_name: str | None
    cause_increase: str | None
    cause_decrease: str | None
    effect_increase: str | None
    effect_decrease: str | None

def load_ace(file_src):
    """Load ACE_ files; file_src must be the full path as a string."""
    
    if DEBUG:
        print('Loading ACE_ files from:', file_src)
    
    # Getting files
    must_load = []
    for f in [
        *os.listdir(file_src),
        *['Doors/' + v for v in os.listdir(file_src+'/Doors')],
        *['SurfaceConditions/' + v for v in os.listdir(file_src+'/SurfaceConditions')]
    ]:
        file_name = os.path.basename(f)
        if file_name.startswith('ACE_') and file_name.endswith('.json'):
            must_load.append(f)
        elif DEBUG:
            print('Skipping ACE_ file:', f)
    
    # Setup dict (no base values, as of writing theres 151 files)
    result: dict[str, ACEName] = {}
    # Load files
    for fname in must_load:
        name = os.path.splitext(os.path.basename(fname))[0] # PenDriverPro/.../ACE_AlwaysBatteryUp.uasset -> ACE_AlwaysBatteryUp
        with open(os.path.join(file_src, fname), 'r', encoding='utf-8') as f:
            data: list[dict] = json.load(f)
            relevant_obj = data[-1]["Properties"]
            args = [
                relevant_obj.get('CauseUpName'),
                relevant_obj.get('CauseDownName'),
                relevant_obj.get('EffectUpName'),
                relevant_obj.get('EffectDownName'),
                relevant_obj.get('CauseIncrease'),
                relevant_obj.get('CauseDecrease'),
                relevant_obj.get('EffectIncrease'),
                relevant_obj.get('EffectDecrease'),
            ]
            result[name] = ACEName(*(None if arg is None else arg['SourceString'] for arg in args))
    
    return result
            

@dataclass(slots=True)
class DTRArtifact:
    artifact_path: str
    probability: float
    evoaps_name_idx: tuple[str, int]
    has_branch_conditions: bool

def parse_artifact_type(dtr: dict[str, Any], ap: dict[str, Any], ace: dict[str, ACEName]) -> defaultdict[str, dict[str, str]]:
    """"""
    # Not optimizing, this is a script to generate a csv that'll be used 3 times ever if we're lucky.
    
    # 1. Parse decisions
    decisions_obj = dtr[0]
    artifacts = []
    for decision in decisions_obj['Properties']['Decisions']:
        
        # 1.1. Create teh artiact instance
        artifact_cls = decision['Object']['ObjectPath']
        artifact = DTRArtifact(
            artifact_path=artifact_cls,
            probability=decision['Probability'],
            evoaps_name_idx=('', 0),
            has_branch_conditions=False
        )
        
        # 1.2. Ensure there is no peculiar decision behavior
        branch_conditions = decision.get('BranchConditions')
        if branch_conditions is not None:
            conditions = branch_conditions.get('Conditions')
            if conditions:
                artifact.has_branch_conditions = True

        # 1.3.1. Get index
        idx_str = artifact_cls.split('.')[-1]
        try:
            idx = int(idx_str)
        except IndexError as e:
            fm.printdanger(f'WARN: Failed to get index for {decision.artifact_path}! {e}')
            continue
        # 1.3.2. Set evoaps
        decision_entry = dtr[idx]  # Get decision details of the artifact
        evoaps_path = decision_entry['Properties']['ArtifactPairing']['ObjectPath']  # Get evoaps cls path & idx
        evoaps_name, evoaps_idx = os.path.basename(evoaps_path).split('.')  # Split file name to get file name & index
        artifact.evoaps_name_idx = (evoaps_name, int(evoaps_idx))  # Format and set to our artifact instance
        
        # 1.4. Add artifact
        artifacts.append(artifact)
    
    # 2. For each DTRArtifact, write down all properties
    name_to_data: dict[str, dict[str, str]] = defaultdict(dict)
    for artifact in artifacts:
        # 2.1. get EvoAPs
        evoaps_name, evoaps_idx = artifact.evoaps_name_idx
        evoaps_inner_name = evoaps_name.removeprefix('AP_')
        evoaps = ap[evoaps_name][evoaps_idx]
        evoaps_properties = evoaps['Properties']
        
        # 2.2. Write down non-properties
        # 2.2.1. Basic stuff
        name_to_data[evoaps_name]['InnerName'] = evoaps_inner_name
        name_to_data[evoaps_name]['Probability'] = artifact.probability
        name_to_data[evoaps_name]['HasBranchConditions'] = artifact.has_branch_conditions
        name_to_data[evoaps_name]['PotentiallyMishandled'] = False
        # 2.3. Write down all properties
        for k, v in evoaps_properties.items():
            match k:
                # Format cause & effect to be more readable
                case 'Cause' | 'Effect':
                    asset_path_name = v['AssetPathName']
                    sub_path_string = v['SubPathString']
                    if sub_path_string:
                        fm.printdanger(f"WARN: Unhandled behavior: SubPathString is not empty! {asset_path_name=}, {sub_path_string=}")
                        name_to_data[evoaps_name]['PotentiallyMishandled'] = True
                    asset_path_display_name = asset_path_name.split('/')[-1].split('.')[-1].removesuffix('_C')
                    name_to_data[evoaps_name].update({k: asset_path_display_name})
                case 'NativeClass':
                    pass
                case _:
                    name_to_data[evoaps_name].update({k: str(v)})
        
        # 2.4. Throw names on top
        cause_increase = evoaps_properties.get('CauseMustIncrease')
        effect_increase = evoaps_properties.get('EffectIncreases')
        if cause_increase is None: cause_increase = False
        if effect_increase is None: effect_increase = False
        cause_cls = ace.get(name_to_data[evoaps_name]['Cause'])
        effect_cls = ace.get(name_to_data[evoaps_name]['Effect'])
        if cause_cls is None:
            raise KeyError(f'Cause class not found: {name_to_data[evoaps_name]["Cause"]} when {ace=}')
        if effect_cls is None:
            raise KeyError(f'Effect class not found: {name_to_data[evoaps_name]["Effect"]} when {ace=}')
        # 2.4.1. Name (_name)
        cause_name = cause_cls.cause_up_name if cause_increase else cause_cls.cause_down_name
        effect_name = effect_cls.effect_up_name if effect_increase else effect_cls.effect_down_name
        name_to_data[evoaps_name]['Name'] = cause_name + ' ' + effect_name
        # 2.4.2. Description (increase/decrease)
        cause_description = cause_cls.cause_increase if cause_increase else cause_cls.cause_decrease
        effect_description = effect_cls.effect_increase if effect_increase else effect_cls.effect_decrease
        name_to_data[evoaps_name]['Description'] = cause_description + ' ' + effect_description
    
    return name_to_data
    
    