# Based on the work here https://github.com/amine0110/nifti-to-stl

import nibabel as nib
import numpy as np
from stl import mesh
from skimage import measure

# Path to the nifti file (.nii, .nii.gz)
file_path = "hack/BN_Atlas_246_1mm.nii.gz"

# Extract the numpy array
nifti_file = nib.load(file_path)
np_array = nifti_file.get_fdata()

unique_vals = np.unique(np_array)
print(f"Distinct values in array: {unique_vals}")

for i in unique_vals:
    output_file = f"segmentation_{int(i)}.stl"
    print(f"Creating mask for value: {int(i)} file: {output_file}")

    masked_array = (np_array == i).astype(np.uint8)

    verts, faces, normals, values = measure.marching_cubes(masked_array, 0)
    obj_3d = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))

    for i, f in enumerate(faces):
        obj_3d.vectors[i] = verts[f]

    # Save the STL file with the name and the path
    obj_3d.save(output_file)
