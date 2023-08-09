import geopandas as gpd
import pandas as pd
import numpy as np
import os
import shutil
from zipfile import ZipFile
from glob import glob
import subprocess

# Define Data Paths
data_path = os.getenv('DATA_PATH', '/data')
inputs_path = os.path.join(data_path,'inputs')
grids_path = os.path.join(inputs_path,'grids')
boundary_path = os.path.join(inputs_path,'boundary')
outputs_path = os.path.join(data_path, 'outputs')
outputs_path_ = data_path + '/' + 'outputs'
if not os.path.exists(outputs_path):
    os.mkdir(outputs_path_)
greenareas_path = os.path.join(outputs_path, 'green_areas')
greenareas_path_ = outputs_path + '/' + 'green_areas'
if not os.path.exists(greenareas_path):
    os.mkdir(greenareas_path_)
vector_path = os.path.join(inputs_path, 'vectors')

# Identify input polygons and shapes (boundary of city, and OS grid cell references)
boundary_1 = glob(boundary_path + "/*.*", recursive = True)
print('Boundary File:',boundary_1)

# Identify the name of the boundary file for the city name
file_path = os.path.splitext(boundary_1[0])
print('File_path:',file_path)
filename=file_path[0].split("/")
print('filename:',filename)
location = filename[-1]
print('Location:',location)

vector_output = os.path.join(outputs_path, location + '.gpkg')
print('Vector Output File Name:', vector_output)

boundary = gpd.read_file(boundary_1[0])
grid_5km = glob(grids_path + "/*_5km.gpkg", recursive = True)
print('Grid File_5km:',grid_5km)
grid_5km = gpd.read_file(grid_5km[0])

grid_50km = glob(grids_path + "/*_50km.gpkg", recursive = True)
print('Grid File_50km:',grid_50km)
grid_50km = gpd.read_file(grid_50km[0])

# Ensure all of the polygons are defined by the same crs
boundary.set_crs(epsg=27700, inplace=True)
grid_5km.set_crs(epsg=27700, inplace=True)
grid_50km.set_crs(epsg=27700, inplace=True)

# Identify which of the 50km OS grid cells fall within the chosen city boundary
cells_needed_50 = gpd.overlay(boundary,grid_50km, how='intersection')
#print('grid_50:',cells_needed_50.head())

# Establish which zip files need to be unzipped
files_to_unzip=[]
files_to_unzip=pd.DataFrame(files_to_unzip)
files_to_unzip=['XX' for n in range(len(cells_needed_50))]
for i in range(0,len(cells_needed_50)):
    name=cells_needed_50.tile_name[i].lower()
    name_path = os.path.join(vector_path, name + '.zip')
    files_to_unzip[i] = name_path

print('files_to_unzip_50km:',files_to_unzip)

# Unzip the required files
for i in range (0,len(files_to_unzip)):
    if os.path.exists(files_to_unzip[i]) :
        with ZipFile(files_to_unzip[i],'r') as zip:
            # extract the files into the inputs directory
            zip.extractall(vector_path)

# Identify which of the 5km OS grid cells fall within the chosen city boundary
cells_needed_5 = gpd.overlay(boundary,grid_5km, how='intersection')
grid_5=cells_needed_5['tile_name']
grid_5=pd.DataFrame(grid_5)
#print('grid_5:', grid_5)

# Establish which zip files need to be unzipped
files_to_unzip2=[]
files_to_unzip2=pd.DataFrame(files_to_unzip2)
files_to_unzip2=['XX' for n in range(len(grid_5))]
for i in range(0,len(grid_5)):
    #name_folder=grid_5.tile_name[i].lower()
    name_file=grid_5.tile_name[i]
    name_path = os.path.join(vector_path, name_file + '.zip')#(vector_path, name_folder ,name_file + '.zip')
    files_to_unzip2[i] = name_path

#print('files_to_unzip_50km:',files_to_unzip2)

# Unzip the required files
for i in range (0,len(files_to_unzip2)):
    if os.path.exists(files_to_unzip2[i]) :
        with ZipFile(files_to_unzip2[i],'r') as zip:
            # extract the files into the inputs directory
            zip.extractall(vector_path)


data_to_merge = glob(vector_path + "/*.shp", recursive = True)
#print('data_to_merge:',data_to_merge)

#Create a geodatabase and merge the data from each gpkg together
original = []
original=gpd.GeoDataFrame(original)


for cell in data_to_merge:
    gdf = gpd.read_file(cell)
    gdf = gdf.drop('fid', axis=1)
    original = pd.concat([gdf, original],ignore_index=True)

# Print to a gpkg file
original.reset_index(inplace=True, drop=True)
original = original.set_crs(27700)
original.to_file(os.path.join(vector_output),driver='GPKG',index=False)


print('Running vector clip')

vector = gpd.read_file(vector_output)
clipped = gpd.clip(vector,boundary)

# Print to a gpkg file
clipped.to_file(os.path.join(outputs_path, location + '_clip.gpkg'),driver='GPKG',index=False)

# Remove unclipped file
os.remove(vector_output)

# Move the clipped file into a new folder and remove the _clip
src=os.path.join(outputs_path, location + '_clip.gpkg')
dst=os.path.join(greenareas_path, location + '.gpkg')
shutil.copy(src,dst)

# Remove duplicate file
os.remove(os.path.join(outputs_path, location + '_clip.gpkg'))
