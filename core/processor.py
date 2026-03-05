import pandas as pd
import xarray as xr
import numpy as np

def extract_file_metadata(ds: xr.Dataset) -> dict:
    """Pull only the columns that exist in the `files` table."""
    return {
        "platform_number": safe_str(ds.attrs.get("platform_number")),
        "data_centre":     safe_str(ds.attrs.get("data_centre")),
    }

def extract_profiles(ds: xr.Dataset) -> list[dict]:
    """
    Convert the dataset to a DataFrame, filter to primary measurement rows,
    and return a list of profile dicts (each containing a 'measurements' list).
    """
    df_full = ds.to_dataframe().reset_index()
    # ARGO files produce a cartesian product across dimensions; keep only
    # the primary measurement rows (n_param=0, n_calib=0, n_history=0).
    filter_cols = {"n_param", "n_calib", "n_history"}
    present = filter_cols.intersection(df_full.columns)
    mask = pd.Series(True, index=df_full.index)
    for col in present:
        mask &= df_full[col] == 0
    df = df_full[mask].copy()
    profiles = []
    for prof_idx, group in df.groupby("n_prof"):
        first = group.iloc[0]
        profile = {
            **extract_profile_header(first),
            "measurements": extract_measurements(group),
        }
        profiles.append(profile)
    return profiles

def extract_profile_header(row: pd.Series) -> dict:
    """
    Maps NetCDF profile fields to the `profiles` table columns.
    juld (Julian days since 1950-01-01) is converted to observed_at (TIMESTAMP).
    Fields not in the schema (juld_location, positioning_system) are dropped.
    """
    juld = safe_float(row.get("juld"))
    observed_at = None
    if juld is not None:
        try:
            observed_at = (
                pd.Timestamp("1950-01-01") + pd.Timedelta(days=juld)
            ).isoformat()
        except Exception:
            observed_at = None
    return {
        "cycle_number":     safe_int(row.get("cycle_number")),
        "direction":        safe_str(row.get("direction")),
        "latitude":         safe_float(row.get("latitude")),
        "longitude":        safe_float(row.get("longitude")),
        "position_qc":      safe_int_from_bytes(row.get("position_qc")),
        "observed_at":      observed_at,   # maps to profiles.observed_at
    }

def extract_measurements(group: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in group.iterrows():
        # Skip rows where ALL core values are NaN (completely empty depth levels)
        core_cols = ("pres", "pres_adjusted", "temp", "temp_adjusted", "psal", "psal_adjusted")
        if all(pd.isna(row.get(col, np.nan)) for col in core_cols):
            continue
        rows.append({
            "depth_level":            safe_int(row.get("n_levels")),
            "pressure":               safe_float(row.get("pres")),
            "pressure_qc":            safe_int_from_bytes(row.get("pres_qc")),
            "pressure_adjusted":      safe_float(row.get("pres_adjusted")),
            "pressure_adjusted_qc":   safe_int_from_bytes(row.get("pres_adjusted_qc")),
            "temperature":            safe_float(row.get("temp")),
            "temperature_qc":         safe_int_from_bytes(row.get("temp_qc")),
            "temperature_adjusted":   safe_float(row.get("temp_adjusted")),
            "temperature_adjusted_qc":safe_int_from_bytes(row.get("temp_adjusted_qc")),
            "salinity":               safe_float(row.get("psal")),
            "salinity_qc":            safe_int_from_bytes(row.get("psal_qc")),
            "salinity_adjusted":      safe_float(row.get("psal_adjusted")),
            "salinity_adjusted_qc":   safe_int_from_bytes(row.get("psal_adjusted_qc")),
        })
    return rows

    # ── Type-coercion utilities ───────────────────────────────────────────────


def safe_str(value) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, (bytes, np.bytes_)):
            return value.decode("utf-8").strip() or None
        s = str(value).strip()
        return s if s else None
    except Exception:
        return None


def safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value) -> int | None:
    if value is None:
        return None
    try:
            if pd.isna(value):
                return None
    except Exception:
            pass
    try:
            return int(float(value))
    except (ValueError, TypeError):
            return None


def safe_int_from_bytes(value) -> int | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        if isinstance(value, (bytes, np.bytes_)):
            s = value.decode("utf-8").strip()
            return int(s) if s.isdigit() else None
        return int(float(value))
    except (ValueError, TypeError):
        return None