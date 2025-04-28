# Main module
from neuroquery import fetch_neuroquery_model, NeuroQueryModel
from nilearn.plotting import view_img
from nilearn.image import threshold_img, resample_to_img, load_img
import nibabel as nib
from nilearn.maskers import NiftiLabelsMasker
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from pathlib import Path
import json
import datetime


# The model used here is the same as the one deployed on the neuroquery website

def query_get_user_input():
    query = input("How're you feeling today?: ")
    return query


def query_run(query):
    encoder = NeuroQueryModel.from_data_dir(fetch_neuroquery_model())
    result = encoder(query)  # result is dict with various fields (niis, tables, etc.)
    return result


def query_view_result(result):
    view_img(result["brain_map"], threshold=3.1).open_in_browser()
    print(result["similar_words"].head(15))
    print("\nsimilar studies:\n")
    print(result["similar_documents"].head())


def parcellate_map(z_map_thresh, atlas_path):
    """
    Parcellate thresholded z-map using provided atlas.
    Parameters:
    - z_map_thresh: thresholded z-map image
    - atlas_path: path to atlas file

    Returns:
    - DataFrame with ROI values
    """
    # load atlas
    atlas_img = load_img(atlas_path)

    # create masker object
    masker = NiftiLabelsMasker(labels_img=atlas_img)

    # extract ROI values
    roi_values = masker.fit_transform(z_map_thresh)

    # get unique region IDs from atlas
    atlas_data = atlas_img.get_fdata()
    region_ids = sorted(np.unique(atlas_data))
    if 0 in region_ids:  # remove 0 vals
        region_ids = [id for id in region_ids if id != 0]

    # create df with region IDs and values
    roi_df = pd.DataFrame({
        'roi_id': region_ids,
        'z_score': roi_values[0][:len(region_ids)]
    })

    # ddd absolute value for sorting
    roi_df['abs_z_score'] = abs(roi_df['z_score'])

    return roi_df


def map_to_colors(values, cmap_name='Spectral', vmin=None, vmax=None):
    """
    Map values to colors using a divergent colormap.

    Parameters:
    - values: array of values to map
    - cmap_name: name of matplotlib colormap (RdBu_r, coolwarm, seismic, etc)
    - vmin, vmax: min/max values for color mapping

    Returns:
    - Array of RGB values
    """
    # set a range for colormap if not specified
    if vmin is None:
        vmin = -max(abs(np.min(values)), abs(np.max(values)))
    if vmax is None:
        vmax = max(abs(np.min(values)), abs(np.max(values)))

    # create colormap
    cmap = plt.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # map values to colors
    mapper = cm.ScalarMappable(norm=norm, cmap=cmap)
    rgb_values = mapper.to_rgba(values)[:, :3]

    return rgb_values


def prepare_roi_json(roi_df, rgb_values):
    """
    Prepare ROI data in the format required by data_format.json
    Parameters:
    - roi_df: DataFrame with roi_id and z_score
    - rgb_values: Array of RGB values

    Returns:
    - Dictionary formatted according to data_format.json
    """
    roi_data = []

    for i, (_, row) in enumerate(roi_df.iterrows()):
        roi_entry = {
            "roi_id": int(row['roi_id']),
            "r": float(rgb_values[i][0]),
            "g": float(rgb_values[i][1]),
            "b": float(rgb_values[i][2])
        }
        roi_data.append(roi_entry)

    return {"data": roi_data}


def img_mod(z_map, threshold=3.1, atlas_path=None):
    """
    Modify z-map with resampling, thresholding, and atlas application
    """
    # set default atlas path relative to project root
    if atlas_path is None:
        atlas_path = Path(__file__).parent.parent.parent / "atlases" / "mni" / "bna" / "BN_218_combined_1mm.nii.gz"
    else:
        atlas_path = Path(atlas_path)

    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found at: {atlas_path}\n"
                              f"Please ensure the atlas file exists at the specified location.")

    # resample z-map to atlas resolution
    print("Resampling z-map to atlas resolution...")
    atlas = load_img(str(atlas_path))  # Convert Path to string for nilearn
    z_map_resamp = resample_to_img(z_map, atlas, force_resample=True)


    # threshold resampled z-map
    print("Thresholding z-map...")
    z_map_thresh = threshold_img(
        z_map_resamp,
        threshold=threshold,
        cluster_threshold=0,
        two_sided=True,
        copy_header=True
    )

    # parcellate data into ROIs
    print(f"Applying atlas: {Path(atlas_path).name}")
    roi_df = parcellate_map(z_map_thresh, atlas_path)

    # map values to colors
    print("Mapping ROI values to colors...")
    rgb_values = map_to_colors(
        roi_df['z_score'].values,
        cmap_name='RdBu_r',
        vmin=-5,
        vmax=5
    )

    # put roi data into json
    roi_json = prepare_roi_json(roi_df, rgb_values)

    return {
        "z_map_resamp.nii.gz": z_map_resamp,
        "z_map_thresh.nii.gz": z_map_thresh,
        "roi_df": roi_df,
        "rgb_values": rgb_values,
        "roi_json": roi_json
    }


def main():
    print("Light speed ahead!")

    # set up results storage
    all_maps = {}
    all_roi_data = {}
    all_metadata = []

    while True:
        query = query_get_user_input()
        if query.lower() in ['quit', 'exit', 'q']:
            break

        print(f"Processing query: {query}")
        result = query_run(query)

        # view results - open browser window
        query_view_result(result)

        #apply atlas and get maps
        processed_results = img_mod(result["z_map"])

        # set query key for consistent naming
        query_key = f"query_{len(all_metadata)}"

        # save maps for later
        all_maps[query_key] = {
            "brain_map.nii.gz": result["brain_map"],
            "z_map.nii.gz": result["z_map"],
            "z_map_resamp.nii.gz": processed_results["z_map_resamp.nii.gz"],
            "z_map_thresh.nii.gz": processed_results["z_map_thresh.nii.gz"]
        }

        # store ROI data
        all_roi_data[query_key] = processed_results["roi_json"]

        # store metadata
        metadata = {
            "query": query,
            "timestamp": datetime.datetime.now().isoformat(),
            "similar_words": result["similar_words"].head(15).to_dict(),
            "similar_documents": result["similar_documents"].head().to_dict(),
            "threshold_settings": {
                "z_score": 3.1,
                "cluster_threshold": 0
            }
        }
        all_metadata.append(metadata)

        if input("\nWould you like to enter another feeling? (y/n): ").lower() != 'y':
            break

    # save results at the end
    output_dir = Path("hack/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # paths to all saved files
    saved_paths = {}

    # save all brain maps
    for query_key, maps in all_maps.items():
        for map_name, img in maps.items():
            filename = f"{query_key}_{map_name}"
            output_path = output_dir / filename
            nib.save(img, output_path)
            saved_paths[filename] = str(output_path)
            print(f"Saved {filename} to {output_path}")

    # save all ROI data in JSON format
    for query_key, roi_data in all_roi_data.items():
        filename = f"{query_key}_roi_data.json"
        output_path = output_dir / filename
        with open(output_path, "w") as f:
            json.dump(roi_data, f, indent=2)
        saved_paths[filename] = str(output_path)
        print(f"Saved {filename} to {output_path}")

    # save paths in metadata
    for i, metadata in enumerate(all_metadata):
        query_key = f"query_{i}"
        metadata["output_files"] = {
            k: v for k, v in saved_paths.items() if k.startswith(query_key)
        }

    # save final results / metadata json
    results_path = output_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(all_metadata, f, indent=2)
    print(f"\nSaved all results to {results_path}")


if __name__ == "__main__":
    main()

    # TODO: build out user prompts, multiple prompts to create a series of outputs
    #  (perhaps create SQLite db for long-term storage)
    # TODO: fine-tune threshold ?
    # TODO: output settings, integrate with setup/launch/ future config file

