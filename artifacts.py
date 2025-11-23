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
    
    not_impl = parse_unimplemented_aps(parsed, raw_ap, raw_ace)
    save_not_implemented_csv(not_impl)

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
    BANNED_FILES = tuple()
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

# ---------------------
#  Artifact extraction
# ---------------------

def extract_artifact_index(artifact_cls: str) -> int:
    idx_str = artifact_cls.split('.')[-1]
    try:
        return int(idx_str)
    except Exception as e:
        raise ValueError(f"Failed to extract index from artifact path '{artifact_cls}': {e}")

def build_artifact_instance(decision: dict[str, Any]) -> DTRArtifact:
    artifact_cls = decision['Object']['ObjectPath']
    artifact = DTRArtifact(
        artifact_path=artifact_cls,
        probability=decision['Probability'],
        evoaps_name_idx=('', 0),
        has_branch_conditions=False
    )
    return artifact

def set_branch_conditions(artifact: "DTRArtifact", decision: dict[str, Any]) -> None:
    bc = decision.get('BranchConditions')
    if not bc:
        return
    conditions = bc.get('Conditions')
    if conditions:
        artifact.has_branch_conditions = True

def resolve_evoaps_info(dtr: dict[str, Any], artifact_cls: str) -> tuple[str, int]:
    idx = extract_artifact_index(artifact_cls)
    decision_entry = dtr[idx]
    evoaps_path = decision_entry['Properties']['ArtifactPairing']['ObjectPath']
    evoaps_name, evoaps_idx = os.path.basename(evoaps_path).split('.')
    return evoaps_name, int(evoaps_idx)

def parse_decisions_into_artifacts(dtr: dict[str, Any]) -> list["DTRArtifact"]:
    decisions_obj = dtr[0]
    artifacts = []

    for decision in decisions_obj['Properties']['Decisions']:
        artifact = build_artifact_instance(decision)
        set_branch_conditions(artifact, decision)

        artifact_cls = artifact.artifact_path
        try:
            evoaps_name, evoaps_idx = resolve_evoaps_info(dtr, artifact_cls)
        except Exception as e:
            fm.printdanger(f"WARN: Failed to get evoaps for {artifact_cls}! {e}")
            continue

        artifact.evoaps_name_idx = (evoaps_name, evoaps_idx)
        artifacts.append(artifact)

    return artifacts


# ---------------------
#  EvoAP extraction
# ---------------------

def apply_basic_properties(name_to_data, evoaps_name, artifact):
    evoaps_inner_name = evoaps_name.removeprefix('AP_')
    name_to_data[evoaps_name]['InnerName'] = evoaps_inner_name
    name_to_data[evoaps_name]['Probability'] = artifact.probability
    name_to_data[evoaps_name]['HasBranchConditions'] = artifact.has_branch_conditions
    name_to_data[evoaps_name]['PotentiallyMishandled'] = False

def apply_evoaps_properties(name_to_data, evoaps_name, evoaps_properties):
    for k, v in evoaps_properties.items():
        match k:
            case 'Cause' | 'Effect':
                asset_path_name = v['AssetPathName']
                sub_path_string = v['SubPathString']
                if sub_path_string:
                    fm.printdanger(
                        f"WARN: Unhandled behavior: SubPathString not empty!"
                        f" asset_path_name={asset_path_name}, sub_path_string={sub_path_string}"
                    )
                    name_to_data[evoaps_name]['PotentiallyMishandled'] = True

                asset_display = (
                    asset_path_name.split('/')[-1].split('.')[-1].removesuffix('_C')
                )
                name_to_data[evoaps_name][k] = asset_display

            case 'NativeClass':
                pass

            case _:
                name_to_data[evoaps_name][k] = str(v)

def determine_name_and_description(name_to_data, evoaps_name, evoaps_properties, ace):
    cause_inc = evoaps_properties.get('CauseMustIncrease', False)
    effect_inc = evoaps_properties.get('EffectIncreases', False)

    cause_key = name_to_data[evoaps_name]['Cause']
    effect_key = name_to_data[evoaps_name]['Effect']

    cause_cls = ace.get(cause_key)
    effect_cls = ace.get(effect_key)
    if cause_cls is None:
        raise KeyError(f"Missing cause ACE class: {cause_key}")
    if effect_cls is None:
        raise KeyError(f"Missing effect ACE class: {effect_key}")

    cause_name = cause_cls.cause_up_name if cause_inc else cause_cls.cause_down_name
    effect_name = effect_cls.effect_up_name if effect_inc else effect_cls.effect_down_name
    name_to_data[evoaps_name]['Name'] = cause_name + ' ' + effect_name

    cause_desc = cause_cls.cause_increase if cause_inc else cause_cls.cause_decrease
    effect_desc = effect_cls.effect_increase if effect_inc else effect_cls.effect_decrease
    name_to_data[evoaps_name]['Description'] = cause_desc + ' ' + effect_desc


def process_single_artifact(name_to_data, artifact, ap, ace):
    evoaps_name, evoaps_idx = artifact.evoaps_name_idx
    evoaps = ap[evoaps_name][evoaps_idx]
    evoaps_properties = evoaps['Properties']

    apply_basic_properties(name_to_data, evoaps_name, artifact)
    apply_evoaps_properties(name_to_data, evoaps_name, evoaps_properties)
    determine_name_and_description(name_to_data, evoaps_name, evoaps_properties, ace)


# ---------------------
#  Main Function
# ---------------------

def parse_artifact_type(
    dtr: dict[str, Any],
    ap: dict[str, Any],
    ace: dict[str, ACEName]
) -> defaultdict[str, dict[str, str]]:

    artifacts = parse_decisions_into_artifacts(dtr)

    name_to_data: defaultdict[str, dict[str, str]] = defaultdict(dict)

    for artifact in artifacts:
        process_single_artifact(name_to_data, artifact, ap, ace)

    return name_to_data

def parse_unimplemented_aps(parsed, raw_ap, raw_ace):
    """
    Returns { evoaps_name: parsed_row } for all EvoAP entries that
    appear in raw_ap but were never referenced in any biome's parsed output.
    """

    # Collect AP names that appear in parsed output
    used = set()
    for biome_table in parsed.values():
        used.update(biome_table.keys())

    not_used = [name for name in raw_ap.keys() if name not in used]

    result = {}

    for evoaps_name in sorted(not_used):
        for idx in range(len(raw_ap[evoaps_name])):
            parsed_row = parse_single_evoap_without_dtr(
                evoaps_name, idx, raw_ap, raw_ace
            )
            result[f"{evoaps_name}.{idx}"] = parsed_row

    return result

def save_not_implemented_csv(not_impl, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "NotImplemented.csv")

    # Determine columns from all rows
    all_columns = set()
    for row in not_impl.values():
        all_columns.update(row.keys())

    # Recommended ordering
    base = [
        "Name",
        "Description",
        "InnerName",
        "Cause",
        "Effect",
        "PipCost",
        "Multiplier",
        "Probability",
        "HasBranchConditions",
        "CauseMustIncrease",
        "EffectIncreases",
        "PotentiallyMishandled",
    ]

    columns = base + sorted(c for c in all_columns if c not in base)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for key, row in not_impl.items():
            writer.writerow({col: row.get(col, "") for col in columns})

def parse_single_evoap_without_dtr(evoaps_name, idx, raw_ap, raw_ace):
    """
    Build a DTRArtifact with probability=0 and no branch conditions,
    then run it through the same formatting pipeline.
    """

    # Fake artifact
    dummy = DTRArtifact(
        artifact_path="",             # irrelevant for missing artifacts
        probability=0.0,              # required field
        evoaps_name_idx=(evoaps_name, idx),
        has_branch_conditions=False
    )

    evoaps = raw_ap[evoaps_name][idx]
    evoaps_properties = evoaps["Properties"]

    row = defaultdict(dict)

    # Reuse existing parsing logic
    apply_basic_properties(row, evoaps_name, dummy)
    apply_evoaps_properties(row, evoaps_name, evoaps_properties)
    determine_name_and_description(row, evoaps_name, evoaps_properties, raw_ace)

    return row[evoaps_name]
