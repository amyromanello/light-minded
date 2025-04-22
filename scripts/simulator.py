# Based on the work here https://github.com/amine0110/nifti-to-stl

import nibabel as nib
import numpy as np
from skimage import measure
import colorsys
import json
import os
import re

# Path to the nifti file (.nii, .nii.gz)
file_path = "hack/BN_Atlas_246_1mm.nii.gz"
table_path = "hack/bn_246_table.md"

# Create output directory for the WebGL data
os.makedirs("web/webgl_output", exist_ok=True)


# Parse the bn_246_table.md file to extract metadata
def parse_brain_regions_table(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Skip the header row and separator row
    data_rows = lines[2:]

    # Create a dictionary to store the metadata for each region ID
    region_metadata = {}

    for row in data_rows:
        # Split the row by the pipe character and strip whitespace
        columns = [col.strip() for col in row.split("|")[1:-1]]

        if len(columns) < 10:
            continue

        # Extract the metadata
        lobe = columns[0]
        gyrus = columns[1]
        hemisphere_name = columns[2]
        left_id = int(columns[3]) if columns[3].strip().isdigit() else None
        right_id = int(columns[4]) if columns[4].strip().isdigit() else None
        network = columns[8]
        network_id = columns[9].strip() if columns[9].strip().isdigit() else None

        # Add the metadata for the left hemisphere
        if left_id is not None:
            region_metadata[left_id] = {
                "lobe": lobe,
                "gyrus": gyrus,
                "hemisphere": "Left",
                "hemisphere_name": hemisphere_name,
                "network": network,
                "network_id": network_id,
            }

        # Add the metadata for the right hemisphere
        if right_id is not None:
            region_metadata[right_id] = {
                "lobe": lobe,
                "gyrus": gyrus,
                "hemisphere": "Right",
                "hemisphere_name": hemisphere_name,
                "network": network,
                "network_id": network_id,
            }

    return region_metadata


# Load the brain region metadata
region_metadata = parse_brain_regions_table(table_path)
print(f"Loaded metadata for {len(region_metadata)} brain regions")

# Extract the numpy array
nifti_file = nib.load(file_path)
np_array = nifti_file.get_fdata()

unique_vals = np.unique(np_array)
print(f"Distinct values in array: {unique_vals}")
print(f"Number of unique values: {len(unique_vals)}")

# Create a list to store all mesh data for the viewer
all_meshes = []

# Process each unique value
for idx, i in enumerate(unique_vals):
    if i == 0:  # Skip background value (typically 0)
        continue

    print(f"Processing value: {int(i)} ({idx}/{len(unique_vals)})")

    # Create a binary mask for this value
    masked_array = (np_array == i).astype(np.uint8)

    # Generate mesh using marching cubes
    try:
        verts, faces, normals, values = measure.marching_cubes(masked_array, 0)

        # Calculate HSL color based on the value's position in the range
        # Map the index to a hue value between 0 and 360 degrees
        hue = (idx / (len(unique_vals) - 1)) * 360
        # Convert HSL to RGB (saturation=1.0, lightness=0.5)
        rgb = colorsys.hls_to_rgb(hue / 360, 0.5, 1.0)

        # Scale RGB values to 0-255 range and convert to hex
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )

        # Create a mesh object for Three.js
        mesh_data = {
            "id": int(i),
            "color": color_hex,
            "hue": hue,
            "vertices": verts.tolist(),
            "faces": faces.tolist(),
            "normals": normals.tolist(),
        }

        # Add the metadata from the table if available
        region_id = int(i)
        if region_id in region_metadata:
            mesh_data.update(
                {
                    "lobe": region_metadata[region_id]["lobe"],
                    "gyrus": region_metadata[region_id]["gyrus"],
                    "hemisphere": region_metadata[region_id]["hemisphere"],
                    "hemisphere_name": region_metadata[region_id]["hemisphere_name"],
                    "network": region_metadata[region_id]["network"],
                    "network_id": region_metadata[region_id]["network_id"],
                }
            )

        # Save individual mesh data to a JSON file
        with open(f"web/webgl_output/mesh_{int(i)}.json", "w") as f:
            json.dump(mesh_data, f)

        # Add to the collection of all meshes
        all_meshes.append(mesh_data)

        print(f"  Created mesh for value {int(i)} with color {color_hex}")

    except Exception as e:
        print(f"  Error processing value {int(i)}: {e}")

# Save the index file with references to all meshes
with open("web/webgl_output/mesh_index.json", "w") as f:
    json.dump({"meshes": all_meshes}, f)

print(f"Processed {len(all_meshes)} meshes")

# Create an HTML file with Three.js for visualization
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Brain Region 3D Visualization</title>
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { display: block; }
        #info {
            position: absolute;
            top: 10px;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            pointer-events: none;
        }
        #loading {
            position: absolute;
            top: 50%;
            width: 100%;
            text-align: center;
            color: white;
            font-size: 24px;
            font-family: Arial, sans-serif;
        }
        #controls {
            position: absolute;
            bottom: 10px;
            left: 10px;
            color: white;
            font-family: Arial, sans-serif;
            background-color: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
        }
        #region-list-panel {
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            font-family: Arial, sans-serif;
            background-color: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 5px;
            width: 300px;
            max-height: 80vh;
            overflow-y: auto;
        }
        #region-list-panel h3 {
            margin-top: 0;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.3);
            padding-bottom: 5px;
        }
        #grouping-controls {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        #grouping-controls label {
            margin-right: 10px;
        }
        #region-list {
            max-height: 60vh;
            overflow-y: auto;
            padding-right: 10px;
        }
        .region-group {
            margin-bottom: 10px;
        }
        .group-header {
            font-weight: bold;
            cursor: pointer;
            padding: 5px;
            background-color: rgba(255,255,255,0.1);
            border-radius: 3px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-header:hover {
            background-color: rgba(255,255,255,0.2);
        }
        .group-toggle {
            margin-right: 5px;
        }
        .region-item {
            padding: 3px 5px 3px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        .region-item:hover {
            background-color: rgba(255,255,255,0.1);
            border-radius: 3px;
        }
        .region-color {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .region-checkbox {
            margin-right: 8px;
        }
        #region-info {
            position: absolute;
            top: 10px;
            right: 10px;
            color: white;
            font-family: Arial, sans-serif;
            background-color: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 5px;
            width: 300px;
            display: none;
        }
        #region-info h3 {
            margin-top: 0;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.3);
            padding-bottom: 5px;
        }
        #region-info table {
            width: 100%;
            border-collapse: collapse;
        }
        #region-info td {
            padding: 3px 0;
        }
        #region-info td:first-child {
            font-weight: bold;
            width: 40%;
        }
        #color-indicator {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            vertical-align: middle;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div id="info">Brain Region 3D Visualization</div>
    <div id="loading">Loading brain regions...</div>
    <div id="controls">
        <div>
            <input type="checkbox" id="autoRotate" checked>
            <label for="autoRotate">Auto Rotate</label>
        </div>
        <div>
            <label for="opacity">Opacity: </label>
            <input type="range" id="opacity" min="0" max="1" step="0.01" value="0.8">
        </div>
    </div>
    
    <div id="region-list-panel">
        <h3>Region List</h3>
        <div id="grouping-controls">
            <div>Group by:</div>
            <div>
                <input type="radio" id="group-by-lobe" name="grouping" value="lobe" checked>
                <label for="group-by-lobe">Lobe</label>
                
                <input type="radio" id="group-by-gyrus" name="grouping" value="gyrus">
                <label for="group-by-gyrus">Gyrus</label>
                
                <input type="radio" id="group-by-network" name="grouping" value="network">
                <label for="group-by-network">Network</label>
            </div>
        </div>
        <div id="region-list">
            <!-- Region groups will be populated here -->
        </div>
    </div>
    
    <div id="region-info">
        <h3>Region Information <span id="color-indicator"></span></h3>
        <table>
            <tr><td>ID:</td><td id="region-id"></td></tr>
            <tr><td>Lobe:</td><td id="region-lobe"></td></tr>
            <tr><td>Gyrus:</td><td id="region-gyrus"></td></tr>
            <tr><td>Hemisphere:</td><td id="region-hemisphere"></td></tr>
            <tr><td>Name:</td><td id="region-name"></td></tr>
            <tr><td>Network:</td><td id="region-network"></td></tr>
            <tr><td>Network ID:</td><td id="region-network-id"></td></tr>
        </table>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x111111);
        
        // Camera setup
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 200;
        
        // Renderer setup
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        
        // Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);
        
        // Meshes collection
        const meshes = [];
        let loadedCount = 0;
        let totalCount = 0;
        
        // Region visibility management
        const regionVisibility = new Map(); // Maps region ID to visibility state
        
        // Function to toggle region visibility
        function toggleRegionVisibility(regionId, visible) {
            regionVisibility.set(regionId, visible);
            
            // Find the mesh with this ID and update its visibility
            const mesh = meshes.find(m => m.userData.id === regionId);
            if (mesh) {
                mesh.visible = visible;
            }
        }
        
        // Function to toggle all regions in a group
        function toggleGroupVisibility(groupName, groupValue, visible) {
            // Find all meshes in this group and update their visibility
            meshes.forEach(mesh => {
                if (mesh.userData[groupName] === groupValue) {
                    mesh.visible = visible;
                    regionVisibility.set(mesh.userData.id, visible);
                    
                    // Update checkboxes in the UI
                    const checkbox = document.getElementById(`region-${mesh.userData.id}`);
                    if (checkbox) {
                        checkbox.checked = visible;
                    }
                }
            });
        }
        
        // Function to populate the region list based on grouping
        function populateRegionList(groupBy) {
            const regionList = document.getElementById('region-list');
            regionList.innerHTML = ''; // Clear existing content
            
            // Group meshes by the selected property
            const groups = {};
            
            meshes.forEach(mesh => {
                if (!mesh.userData[groupBy]) return;
                
                const groupValue = mesh.userData[groupBy];
                if (!groups[groupValue]) {
                    groups[groupValue] = [];
                }
                groups[groupValue].push(mesh);
            });
            
            // Sort group names alphabetically
            const sortedGroupNames = Object.keys(groups).sort();
            
            // Create HTML for each group
            sortedGroupNames.forEach(groupName => {
                const groupDiv = document.createElement('div');
                groupDiv.className = 'region-group';
                
                // Create group header
                const headerDiv = document.createElement('div');
                headerDiv.className = 'group-header';
                
                // Create group checkbox
                const groupCheckbox = document.createElement('input');
                groupCheckbox.type = 'checkbox';
                groupCheckbox.className = 'group-toggle';
                groupCheckbox.checked = true; // Default to visible
                groupCheckbox.addEventListener('change', function() {
                    toggleGroupVisibility(groupBy, groupName, this.checked);
                });
                
                // Create group label
                const groupLabel = document.createElement('span');
                groupLabel.textContent = `${groupName} (${groups[groupName].length})`;
                
                headerDiv.appendChild(groupCheckbox);
                headerDiv.appendChild(groupLabel);
                
                // Make the header clickable to expand/collapse
                const groupItems = document.createElement('div');
                groupItems.className = 'group-items';
                groupItems.style.display = 'none'; // Start collapsed
                
                headerDiv.addEventListener('click', function(e) {
                    // Don't toggle when clicking the checkbox
                    if (e.target !== groupCheckbox) {
                        groupItems.style.display = groupItems.style.display === 'none' ? 'block' : 'none';
                    }
                });
                
                // Add region items
                groups[groupName].sort((a, b) => a.userData.id - b.userData.id).forEach(mesh => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'region-item';
                    
                    // Create region checkbox
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'region-checkbox';
                    checkbox.id = `region-${mesh.userData.id}`;
                    checkbox.checked = regionVisibility.get(mesh.userData.id) !== false; // Default to visible
                    checkbox.addEventListener('change', function() {
                        toggleRegionVisibility(mesh.userData.id, this.checked);
                    });
                    
                    // Create color indicator
                    const colorSpan = document.createElement('span');
                    colorSpan.className = 'region-color';
                    colorSpan.style.backgroundColor = mesh.material.color.getStyle();
                    
                    // Create region label
                    const label = document.createElement('span');
                    label.textContent = `${mesh.userData.hemisphere_name} (${mesh.userData.id})`;
                    
                    itemDiv.appendChild(checkbox);
                    itemDiv.appendChild(colorSpan);
                    itemDiv.appendChild(label);
                    groupItems.appendChild(itemDiv);
                });
                
                groupDiv.appendChild(headerDiv);
                groupDiv.appendChild(groupItems);
                regionList.appendChild(groupDiv);
            });
        }
        
        // Event listeners for grouping radio buttons
        document.getElementById('group-by-lobe').addEventListener('change', function() {
            if (this.checked) populateRegionList('lobe');
        });
        
        document.getElementById('group-by-gyrus').addEventListener('change', function() {
            if (this.checked) populateRegionList('gyrus');
        });
        
        document.getElementById('group-by-network').addEventListener('change', function() {
            if (this.checked) populateRegionList('network');
        });
        
        // Load the index file
        fetch('./webgl_output/mesh_index.json')
            .then(response => response.json())
            .then(data => {
                totalCount = data.meshes.length;
                document.getElementById('loading').textContent = `Loading brain regions... (0/${totalCount})`;
                
                // Center point calculation
                let centerX = 0, centerY = 0, centerZ = 0;
                let vertexCount = 0;
                
                // First pass to calculate center
                data.meshes.forEach(meshData => {
                    meshData.vertices.forEach(vertex => {
                        centerX += vertex[0];
                        centerY += vertex[1];
                        centerZ += vertex[2];
                        vertexCount++;
                    });
                });
                
                // Calculate average center
                if (vertexCount > 0) {
                    centerX /= vertexCount;
                    centerY /= vertexCount;
                    centerZ /= vertexCount;
                }
                
                // Second pass to create meshes
                data.meshes.forEach(meshData => {
                    // Create geometry
                    const geometry = new THREE.BufferGeometry();
                    
                    // Extract vertices and adjust to center
                    const vertices = [];
                    meshData.vertices.forEach(vertex => {
                        vertices.push(
                            vertex[0] - centerX,
                            vertex[1] - centerY,
                            vertex[2] - centerZ
                        );
                    });
                    
                    // Extract faces (indices)
                    const indices = [];
                    meshData.faces.forEach(face => {
                        indices.push(face[0], face[1], face[2]);
                    });
                    
                    // Set attributes
                    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
                    geometry.setIndex(indices);
                    geometry.computeVertexNormals();
                    
                    // Create material with the HSL-derived color
                    const material = new THREE.MeshPhongMaterial({
                        color: new THREE.Color(meshData.color),
                        transparent: true,
                        opacity: 0.8,
                        side: THREE.DoubleSide
                    });
                    
                    // Create mesh
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.userData = {
                        id: meshData.id,
                        hue: meshData.hue
                    };
                    
                    // Add additional metadata if available
                    if (meshData.lobe) {
                        mesh.userData.lobe = meshData.lobe;
                        mesh.userData.gyrus = meshData.gyrus;
                        mesh.userData.hemisphere = meshData.hemisphere;
                        mesh.userData.hemisphere_name = meshData.hemisphere_name;
                        mesh.userData.network = meshData.network;
                        mesh.userData.network_id = meshData.network_id;
                    }
                    
                    scene.add(mesh);
                    meshes.push(mesh);
                    
                    loadedCount++;
                    document.getElementById('loading').textContent = 
                        `Loading brain regions... (${loadedCount}/${totalCount})`;
                        
                    if (loadedCount === totalCount) {
                        document.getElementById('loading').style.display = 'none';
                        
                        // Initialize the region list with the default grouping (lobe)
                        populateRegionList('lobe');
                    }
                });
            })
            .catch(error => {
                console.error('Error loading mesh data:', error);
                document.getElementById('loading').textContent = 'Error loading brain regions';
            });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // Controls event listeners
        document.getElementById('autoRotate').addEventListener('change', function() {
            controls.autoRotate = this.checked;
        });
        
        document.getElementById('opacity').addEventListener('input', function() {
            const opacity = parseFloat(this.value);
            meshes.forEach(mesh => {
                mesh.material.opacity = opacity;
            });
        });
        
        // Raycaster for mouse interaction
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let hoveredObject = null;
        let selectedObject = null;
        
        // Mouse move event for hover effect
        function onMouseMove(event) {
            // Calculate mouse position in normalized device coordinates
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            
            // Update the raycaster
            raycaster.setFromCamera(mouse, camera);
            
            // Find intersections
            const intersects = raycaster.intersectObjects(meshes);
            
            // Reset previously hovered object
            if (hoveredObject && (!intersects.length || intersects[0].object !== hoveredObject)) {
                if (hoveredObject !== selectedObject) {
                    hoveredObject.material.emissive.setHex(0x000000);
                }
                hoveredObject = null;
                document.body.style.cursor = 'auto';
            }
            
            // Set new hovered object
            if (intersects.length > 0 && intersects[0].object !== selectedObject) {
                hoveredObject = intersects[0].object;
                hoveredObject.material.emissive.setHex(0x333333);
                document.body.style.cursor = 'pointer';
            }
        }
        
        // Mouse click event for selection
        function onClick(event) {
            // Calculate mouse position in normalized device coordinates
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            
            // Update the raycaster
            raycaster.setFromCamera(mouse, camera);
            
            // Find intersections
            const intersects = raycaster.intersectObjects(meshes);
            
            // Reset previously selected object
            if (selectedObject) {
                selectedObject.material.emissive.setHex(0x000000);
                selectedObject = null;
            }
            
            // Hide region info panel if no intersection
            if (intersects.length === 0) {
                document.getElementById('region-info').style.display = 'none';
                return;
            }
            
            // Set new selected object
            selectedObject = intersects[0].object;
            selectedObject.material.emissive.setHex(0x666666);
            
            // Display region info
            const userData = selectedObject.userData;
            document.getElementById('region-id').textContent = userData.id;
            
            // Set color indicator
            const colorIndicator = document.getElementById('color-indicator');
            colorIndicator.style.backgroundColor = selectedObject.material.color.getStyle();
            
            // Set metadata if available
            if (userData.lobe) {
                document.getElementById('region-lobe').textContent = userData.lobe;
                document.getElementById('region-gyrus').textContent = userData.gyrus;
                document.getElementById('region-hemisphere').textContent = userData.hemisphere;
                document.getElementById('region-name').textContent = userData.hemisphere_name;
                document.getElementById('region-network').textContent = userData.network;
                document.getElementById('region-network-id').textContent = userData.network_id;
                document.getElementById('region-info').style.display = 'block';
            } else {
                document.getElementById('region-lobe').textContent = 'N/A';
                document.getElementById('region-gyrus').textContent = 'N/A';
                document.getElementById('region-hemisphere').textContent = 'N/A';
                document.getElementById('region-name').textContent = 'N/A';
                document.getElementById('region-network').textContent = 'N/A';
                document.getElementById('region-network-id').textContent = 'N/A';
                document.getElementById('region-info').style.display = 'block';
            }
        }
        
        // Add event listeners
        window.addEventListener('mousemove', onMouseMove, false);
        window.addEventListener('click', onClick, false);
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        // Start animation
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.5;
        animate();
    </script>
</body>
</html>
"""

# Write the HTML file
with open("web/brain_regions_3d.html", "w") as f:
    f.write(html_content)

print("Created WebGL visualization HTML file: web/brain_regions_3d.html")
