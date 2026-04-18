from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS


DIR_BASE = r"e:\code\tongjimodule"
INPUT_FILE = os.path.join(DIR_BASE, "project_v1", "data", "intermediate", "panel_master_with_index.csv")
OUTPUT_DIR = os.path.join(DIR_BASE, "project_v1", "outputs", "tables")


@dataclass(frozen=True)
class IndexBlock:
    name: str
    candidates: Tuple[str, ...]


INDEX_BLOCKS: Tuple[IndexBlock, ...] = (
    IndexBlock(
        name="infra",
        candidates=(
            "broadband_users",
            "mobile_internet_users",
            "5g_base_stations",
            "optical_cable_length",
            "iot_terminal_users",
        ),
    ),
    IndexBlock(
        name="energy_app",
        candidates=(
            "charging_infrastructure",
            "electricity_market_volume",
            "green_power_trade_volume",
            "renewable_installation_share",
            "green_certificate_volume",
        ),
    ),
    IndexBlock(
        name="digital_support",
        candidates=(
            "software_revenue",
            "digital_core_industry_share",
            "high_tech_industry_share",
            "express_delivery_revenue",
        ),
    ),
)


TARGET = "carbon_intensity_ln"
CONTROLS = ["pgdp_ln", "ind2_share", "urban_rate", "coal_share"]
BASE_INDEX = "energy_digital_index_100"


def _entropy_weight_index(df: pd.DataFrame, cols: List[str]) -> pd.Series:
    """Build an entropy-weighted index with robust guards for sparse columns."""
    data = df[cols].copy()
    # Keep interpolation local to each province to avoid borrowing information across entities.
    data = data.groupby(df["province"], group_keys=False).apply(
        lambda x: x.interpolate(method="linear", limit_direction="both")
    )
    data = data.fillna(data.median(numeric_only=True))

    # Min-max normalization per column.
    min_vals = data.min(axis=0)
    max_vals = data.max(axis=0)
    denom = (max_vals - min_vals).replace(0, np.nan)
    norm = (data - min_vals) / denom
    norm = norm.fillna(0.0)

    p = norm.div(norm.sum(axis=0).replace(0, np.nan), axis=1).replace(0, 1e-12).fillna(1e-12)
    n = len(norm)
    entropy = -(p * np.log(p)).sum(axis=0) / np.log(max(n, 2))
    divergence = 1.0 - entropy

    if float(divergence.sum()) <= 0:
        weights = pd.Series(1.0 / len(cols), index=cols)
    else:
        weights = divergence / divergence.sum()

    idx = (norm * weights).sum(axis=1)
    return idx


def _run_twfe(
    df: pd.DataFrame,
    y_col: str,
    x_cols: List[str],
    cov_type: str = "kernel",
) -> PanelOLS:
    reg_df = df.dropna(subset=[y_col] + x_cols + ["province", "year"]).copy()
    panel = reg_df.set_index(["province", "year"])
    y = panel[y_col]
    x = sm.add_constant(panel[x_cols], has_constant="add")
    model = PanelOLS(y, x, entity_effects=True, time_effects=True)

    if cov_type == "clustered":
        return model.fit(cov_type="clustered", cluster_entity=True)
    return model.fit(cov_type="kernel")


def _result_row(model_name: str, result: PanelOLS, focus_vars: Iterable[str]) -> List[Dict[str, float | str]]:
    rows: List[Dict[str, float | str]] = []
    for var in focus_vars:
        if var not in result.params.index:
            continue
        rows.append(
            {
                "model": model_name,
                "variable": var,
                "coef": float(result.params[var]),
                "std_err": float(result.std_errors[var]),
                "p_value": float(result.pvalues[var]),
                "t_stat": float(result.tstats[var]),
                "r2_within": float(result.rsquared_within),
                "nobs": int(result.nobs),
            }
        )
    return rows


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)

    required = ["province", "year", TARGET] + CONTROLS + [BASE_INDEX]
    missing_required = [col for col in required if col not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")

    # Keep only valid province-year observations for the modeling core.
    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["province", "year"])

    used_blocks: Dict[str, List[str]] = {}
    for block in INDEX_BLOCKS:
        available = [c for c in block.candidates if c in df.columns]
        if len(available) < 2:
            continue
        sub_idx = _entropy_weight_index(df, available)
        # Scale to 0-100 for readability consistent with existing index.
        df[f"idx_{block.name}_100"] = sub_idx * 100.0
        used_blocks[block.name] = available

    if len(used_blocks) < 2:
        raise ValueError("Too few valid index blocks. Need at least 2 blocks with >=2 indicators.")

    block_vars = [f"idx_{name}_100" for name in used_blocks]

    summary_rows: List[Dict[str, float | str]] = []
    model_texts: Dict[str, str] = {}

    # Baseline with the original broad index.
    res_base = _run_twfe(df, TARGET, [BASE_INDEX] + CONTROLS, cov_type="kernel")
    summary_rows.extend(_result_row("baseline_broad_index", res_base, [BASE_INDEX]))
    model_texts["baseline_broad_index"] = res_base.summary.as_text()

    # Separate regressions for each sub-index.
    for var in block_vars:
        model_name = f"single_{var}"
        res = _run_twfe(df, TARGET, [var] + CONTROLS, cov_type="kernel")
        summary_rows.extend(_result_row(model_name, res, [var]))
        model_texts[model_name] = res.summary.as_text()

    # Joint regression to detect sign flips and suppression effects.
    res_joint = _run_twfe(df, TARGET, block_vars + CONTROLS, cov_type="kernel")
    summary_rows.extend(_result_row("joint_three_blocks", res_joint, block_vars))
    model_texts["joint_three_blocks"] = res_joint.summary.as_text()

    # Split-period diagnosis for threshold-like temporal shifts.
    period_defs = {
        "period_2016_2019": (2016.0, 2019.0),
        "period_2020_2022": (2020.0, 2022.0),
    }
    for period_name, (start_year, end_year) in period_defs.items():
        df_sub = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
        if len(df_sub) < 50:
            continue
        for var in block_vars:
            model_name = f"{period_name}_{var}"
            res = _run_twfe(df_sub, TARGET, [var] + CONTROLS, cov_type="kernel")
            summary_rows.extend(_result_row(model_name, res, [var]))
            model_texts[model_name] = res.summary.as_text()

    df_summary = pd.DataFrame(summary_rows).sort_values(["model", "p_value"], na_position="last")
    df_blocks = pd.DataFrame(
        [
            {
                "block": name,
                "constructed_var": f"idx_{name}_100",
                "indicators": "; ".join(cols),
                "indicator_count": len(cols),
            }
            for name, cols in used_blocks.items()
        ]
    )

    summary_path = os.path.join(OUTPUT_DIR, "index_diagnosis_twfe_summary.csv")
    block_path = os.path.join(OUTPUT_DIR, "index_diagnosis_block_definition.csv")
    text_path = os.path.join(OUTPUT_DIR, "index_diagnosis_model_details.txt")

    df_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    df_blocks.to_csv(block_path, index=False, encoding="utf-8-sig")

    with open(text_path, "w", encoding="utf-8") as f:
        f.write("# Index Diagnosis Model Details\n\n")
        for model_name, text in model_texts.items():
            f.write(f"## {model_name}\n")
            f.write(text)
            f.write("\n\n")

    print("[Success] Index diagnosis completed.")
    print(f"Summary table -> {summary_path}")
    print(f"Block definitions -> {block_path}")
    print(f"Model details -> {text_path}")


if __name__ == "__main__":
    main()
