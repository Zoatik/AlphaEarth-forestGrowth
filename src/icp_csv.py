"""
Bridge Made by GPT 6.1 Sol.
Read ICP portal CSVs in the form expected by the original preprocessing.
"""

from pathlib import Path

import polars as pl

EXPORTS = {
    "gr": "595_gr_20261112121624",
    "cc": "595_cc_20260309084712",
    "si": "595_si_20260309085250",
    "dp": "595_dp_20260309084812",
    "ss": "595_ss_20260309084900",
}

DEP_COLUMNS = {
    "ph": "dep_ph",
    "conductivity": "dep_cond",
    "alkalinity": "dep_alk",
    "n_total": "dep_n_tot",
    "s_total": "dep_s_tot",
    "c_total": "dep_c_tot",
    "p_total": "dep_p_tot",
    **{
        name: f"dep_{name}"
        for name in (
            "k",
            "ca",
            "mg",
            "na",
            "n_nh4",
            "cl",
            "n_no3",
            "s_so4",
            "doc",
            "al",
            "mn",
            "fe",
            "p_po4",
            "cu",
            "zn",
            "hg",
            "pb",
            "co",
            "mo",
            "ni",
            "cd",
            "n_org",
            "cr",
            "n_no2",
            "hco3",
            "don",
        )
    },
}
SOIL_COLUMNS = {
    "ph": "ss_ph",
    "conductivity": "ss_cond",
    "alkalinity": "ss_alk",
    "n_total": "ss_n_tot",
    **{
        name: f"ss_{name}"
        for name in (
            "k",
            "ca",
            "mg",
            "n_no3",
            "s_so4",
            "al",
            "doc",
            "na",
            "n_nh4",
            "cl",
            "fe",
            "mn",
            "al_labile",
            "p",
            "cr",
            "ni",
            "zn",
            "cu",
            "pb",
            "cd",
            "si",
        )
    },
}


def read_csv(path: Path, columns: list[str] | None = None) -> pl.DataFrame:
    return pl.read_csv(
        path,
        separator=";",
        infer_schema=False,
        columns=columns,
        null_values=["NA", "NaN", "nan", "NULL"],
    )


def dictionary(root: Path, survey: str, name: str, label: str = "description") -> dict:
    table = read_csv(root / EXPORTS[survey] / "adds" / "dictionaries" / f"{name}.csv")
    # Prefer the latest dictionary entry if a code has several validity periods.
    table = table.with_columns(pl.col("valid_from_survey_year").cast(pl.Int64))
    table = table.sort("valid_from_survey_year").unique("code", keep="last")
    return dict(zip(table["code"].cast(pl.Int64).to_list(), table[label].to_list()))


def label(
    column: str,
    mapping: dict,
    output: str,
    default: str | None = None,
) -> pl.Expr:
    return (
        pl.col(column)
        .replace_strict(mapping, default=default, return_dtype=pl.String)
        .cast(pl.Categorical)
        .alias(output)
    )


def prepare(
    root: Path,
    survey: str,
    filename: str,
    fields: dict[str, tuple[str, pl.DataType]],
    dates: tuple[str, ...] = (),
) -> pl.DataFrame:
    path = root / EXPORTS[survey] / filename
    print(f"Reading CSV: {path}")
    table = read_csv(path, list(fields))
    table = table.select(
        [pl.col(raw).cast(dtype).alias(clean) for raw, (clean, dtype) in fields.items()]
    )
    for name in dates:
        parsed = (
            pl.col(name).str.to_date("%Y-%m-%d", strict=False).cast(pl.Datetime("ns"))
        )
        invalid = table.select(
            (pl.col(name).is_not_null() & parsed.is_null()).sum()
        ).item()
        if invalid:
            raise ValueError(f"{path}: {invalid} invalid dates in {name}")
        table = table.with_columns(parsed.alias(name))
    table = table.with_columns(
        pl.concat_str(
            pl.col("country_code").cast(pl.String).str.zfill(2),
            pl.col("plot_code").cast(pl.String).str.zfill(4),
            separator=".",
        ).alias("plot_id")
    )
    if "tree_number" in table.columns:
        table = table.with_columns(
            pl.concat_str(
                pl.col("plot_id"), pl.col("tree_number").str.zfill(5), separator="."
            ).alias("tree_id")
        )
    return table


def load_inputs(root: Path) -> tuple[pl.DataFrame, ...]:
    common = {
        "survey_year": ("survey_year", pl.Int64),
        "code_country": ("country_code", pl.Int64),
        "partner_code": ("partner_code", pl.Int64),
        "code_plot": ("plot_code", pl.Int64),
    }
    tree = {
        "tree_number": ("tree_number", pl.String),
        "code_tree_species": ("tree_species_code", pl.Int64),
    }
    growth = prepare(
        root,
        "gr",
        "gr_ipm.csv",
        {
            **common,
            **tree,
            "date_assessment": ("date", pl.String),
            "diameter": ("diameter", pl.Float64),
            "code_diameter_qc": ("diameter_quality_code", pl.Int64),
            "code_diameter": ("diameter_method_code", pl.Int64),
            "code_removal": ("removal_code", pl.Int64),
        },
        ("date",),
    )
    # Negative code sentinels have no label in the historical intermediate data.
    growth = growth.with_columns(
        [
            pl.when(pl.col(c) >= 0).then(pl.col(c)).otherwise(None).alias(c)
            for c in ["diameter_quality_code", "diameter_method_code", "removal_code"]
        ]
    )
    species = dictionary(root, "gr", "d_tree_spec")
    growth = growth.with_columns(
        label(
            "country_code",
            dictionary(root, "gr", "d_country", "lib_country"),
            "country",
        ),
        label("tree_species_code", species, "specie", default="? no mapping ?"),
        label(
            "diameter_quality_code",
            dictionary(root, "gr", "d_gr_quality_code"),
            "diameter_quality",
        ),
        label(
            "diameter_method_code",
            dictionary(root, "gr", "d_diameter"),
            "diameter_method",
        ),
        label(
            "removal_code",
            dictionary(root, "gr", "d_removal_mortality_ccgr"),
            "removal_info",
        ),
    )

    plots = prepare(
        root,
        "si",
        "si_plt.csv",
        {
            "code_country": common["code_country"],
            "code_plot": common["code_plot"],
            "latitude": ("plot_latitude", pl.Int64),
            "longitude": ("plot_longitude", pl.Int64),
            "slope": ("plot_slope", pl.Int64),
            "code_orientation": ("orientation_code", pl.Int64),
            "code_altitude": ("altitude_code", pl.Int64),
        },
    )
    # Preserve the original altitude-class representatives rather than substituting
    # altitude_m (which would change the original model inputs).
    altitude = read_csv(root / EXPORTS["si"] / "adds/dictionaries/d_altitude.csv")
    altitude_codes = altitude["code"].cast(pl.Int64).to_list()
    altitude_max = altitude["value_max"].cast(pl.Float64).to_list()
    altitude_values = {
        code: (24.5 if code == 1 else upper - 25)
        for code, upper in zip(altitude_codes, altitude_max)
        if upper is not None
    }
    plots = plots.with_columns(
        label(
            "orientation_code",
            dictionary(root, "si", "d_orientation"),
            "plot_orientation",
        ),
        pl.col("altitude_code")
        .replace_strict(altitude_values, default=None, return_dtype=pl.Float64)
        .alias("plot_altitude"),
        pl.when(pl.col("plot_slope") >= 0)
        .then(pl.col("plot_slope"))
        .otherwise(None)
        .alias("plot_slope"),
    )
    if plots["plot_id"].n_unique() != plots.height:
        raise ValueError(
            "si_plt.csv contains duplicate plot IDs; resolve before joining"
        )

    crown = prepare(
        root,
        "cc",
        "cc_trc.csv",
        {
            **common,
            **tree,
            "date_survey": ("date", pl.String),
            "code_defoliation": ("defoliation", pl.Float64),
            "code_social_class": ("social_class_code", pl.Int64),
        },
        ("date",),
    )
    crown = crown.with_columns(
        label("tree_species_code", species, "specie", default="? no mapping ?"),
        pl.when(pl.col("social_class_code") > 0)
        .then(pl.col("social_class_code"))
        .otherwise(None)
        .alias("social_class_code"),
    )
    deposition = prepare(
        root,
        "dp",
        "dp_dem.csv",
        {
            **common,
            "date_start": ("date_start", pl.String),
            "date_end": ("date_end", pl.String),
            "sampler_id": ("sampler_id", pl.Int64),
            "code_sampler": ("sampler_code", pl.Int64),
            "code_vsampling": ("vsampling_code", pl.Int64),
            "quantity": ("quantity", pl.Float64),
            **{raw: (clean, pl.Float64) for raw, clean in DEP_COLUMNS.items()},
        },
        ("date_start", "date_end"),
    )
    # The original dp_pld join only appended unused monitoring metadata. All
    # columns consumed downstream, including quantity, are already in dp_dem.csv.
    soil = prepare(
        root,
        "ss",
        "ss_ssm.csv",
        {
            **common,
            "date_start": ("date_start", pl.String),
            "date_end": ("date_end", pl.String),
            "sample_vol": ("sample_vol", pl.Float64),
            **{raw: (clean, pl.Float64) for raw, clean in SOIL_COLUMNS.items()},
        },
        ("date_start", "date_end"),
    )
    return growth, plots, crown, deposition, soil
