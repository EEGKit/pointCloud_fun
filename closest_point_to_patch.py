# Description: find the closest points of a point cloud to a surface patch.
# Algorithm:
# 1. Load the surface patch and the point cloud.
# 2. Divide the patch to 32x32 smaller patches.
# 3. For each smaller patch, find the closest point in the point cloud.
# 4. Determine if the closest point is at either side of the patch.
# 5. Find the index of the closest points in the point cloud and correlate that to the index of the small patch.
# %% initilize
# load the patch and the point cloud
import vtk
import numpy as np
from scipy.spatial import cKDTree

PLOT_PATCH = False
# load the patch
# Create a vtkPLYReader object
ply_reader = vtk.vtkPLYReader()
ply_reader.SetFileName('projected_patch.ply')
ply_reader.Update()

# Get the output of the PLY reader
patch = ply_reader.GetOutput()

# Load the point cloud
point_cloud = np.loadtxt('jcFS_ss_no-orientation.dip')

# make a polydata object from the point cloud
points = vtk.vtkPoints()
for point in point_cloud:
    points.InsertNextPoint(point)

polydata = vtk.vtkPolyData()
polydata.SetPoints(points)

# %% plot the patch and the point cloud
# patch mapper and actor
if PLOT_PATCH:
    patch_mapper = vtk.vtkPolyDataMapper()
    patch_mapper.SetInputData(patch)
    patch_actor = vtk.vtkActor()
    patch_actor.SetMapper(patch_mapper)

    # point cloud mapper and actor
    # Create a VTK glyph to visualize the points
    glyph = vtk.vtkGlyph3D()
    glyph.SetInputData(polydata)
    glyph.Update()

    # set the shape of the glyph
    sphere_source = vtk.vtkSphereSource()
    sphere_source.SetRadius(0.25)  # Set the radius of the sphere
    glyph.SetSourceConnection(sphere_source.GetOutputPort())
    glyph.Update()

    # Increase the glyph size
    # glyph.SetScaleFactor(2.0)  # Adjust the scale factor as desired

    # Create a VTK mapper and actor
    pc_mapper = vtk.vtkPolyDataMapper()
    pc_mapper.SetInputConnection(glyph.GetOutputPort())

    pc_actor = vtk.vtkActor()
    pc_actor.SetMapper(pc_mapper)
    pc_actor.GetProperty().SetColor(0, 0, 1)  # Set point color to blue

    # create a renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.5, 0.5, 0.5)  # Set the background color to white
    renderer.AddActor(patch_actor)
    renderer.AddActor(pc_actor)

    # create a render window
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    # create an interactor
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    # initialize the interactor
    interactor.Initialize()
    render_window.Render()
    interactor.Start()

# %% divide the patch to smaller patches
# get the bounds of the patch
bounds = patch.GetBounds()

# divide the patch to 32x32 smaller patches
PATCH_SIZE = 32
n_patches = 32
patch_bounds = []

for i in range(n_patches):
    for j in range(n_patches):
        patch_bounds.append([bounds[0] + i * PATCH_SIZE, bounds[0] + (i + 1) * PATCH_SIZE,
                             bounds[2] + j * PATCH_SIZE, bounds[2] + (j + 1) * PATCH_SIZE,
                             bounds[4], bounds[4]])

# %% find the closest points in the point cloud to the smaller patches
# Build a KD-Tree from the point cloud
tree = cKDTree(point_cloud)

# List to store closest points for each patch
closest_points_to_patch = []

previous_closest_point_index = None
local_search_radius = PATCH_SIZE * 1.5  # Adjust as needed


# %% define a function to compute the distance between two points
def compute_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)


# %% main loop to find the closest points
for patch_bound in patch_bounds:
    # Compute the center of the bounding box
    center = [
        (patch_bound[0] + patch_bound[1]) / 2,
        (patch_bound[2] + patch_bound[3]) / 2,
        (patch_bound[4] + patch_bound[5]) / 2
    ]

    if previous_closest_point_index is None:
        # For the first patch, search the entire point cloud
        _, index = tree.query(center)
    else:
        # For subsequent patches, search within a local neighborhood
        indices = tree.query_ball_point(point_cloud[previous_closest_point_index], local_search_radius)
        
        if not indices:
            # If no points are found in the local neighborhood, search the entire point cloud
            _, index = tree.query(center)
        else:
            distances = [compute_distance(center, point_cloud[i]) for i in indices]
            index = indices[np.argmin(distances)]

    closest_point = point_cloud[index]
    closest_points_to_patch.append(closest_point)
    previous_closest_point_index = index
