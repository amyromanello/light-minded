"""Main module."""
from neuroquery import fetch_neuroquery_model, NeuroQueryModel
from nilearn.plotting import view_img
from nilearn.image import threshold_img
import nibabel as nib
from pathlib import Path

# The model used here is the same as the one deployed on the neuroquery website


def query_get_user_input():
    query = """I'm feeling happy!"""
    return query

def query_run(query):
    encoder = NeuroQueryModel.from_data_dir(fetch_neuroquery_model())
    result = encoder(query) # result is dict with various fields (niis, tables, etc.)
    return result

def query_view_result(result):
    view_img(result["brain_map"], threshold=3.1).open_in_browser()
    print(result["similar_words"].head(15))
    print("\nsimilar studies:\n")
    print(result["similar_documents"].head())

def query_save_result(result):
    #TODO: this is super messy, needs to be refactored
    brain_map = result["brain_map"]
    output_path = Path("hack/test_outputs/brain_map.nii.gz").resolve()
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        nib.save(brain_map, output_path)

    print(f"Saved brain map to {output_path}")

    z_map = result["z_map"]
    output_path = Path("hack/test_outputs/z_map.nii.gz").resolve()
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        nib.save(z_map, output_path)

    print(f"Saved z-map to {output_path}")

    brain_map_thresh = threshold_img(result["brain_map"], 3.1,
                                     cluster_threshold=0,
                                     two_sided=True, mask_img=None, copy=True,
                                     copy_header=True)

    output_path = Path("hack/test_outputs/brain_map_thresh.nii.gz").resolve()
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        nib.save(brain_map_thresh, output_path)

    print(f"Saved thresholded brain map to {output_path}")



def main():
    print("Light speed ahead!")

    query = query_get_user_input()
    print(f"User input: {query}")

    result = query_run(query)
    query_view_result(result)
    query_save_result(result)


    #TODO: user prompts, multiple prompts to create a series of outputs
    #TODO: parcellate data with chosen atlas
    #TODO: create json file to pass to LEDs

    #TODO: fine-tune threshold settings?
    #TODO: output settings/locations/logging

if __name__ == "__main__":
    main()

