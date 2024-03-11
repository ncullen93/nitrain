import os
from pathlib import Path
import datalad.api as dl
import nibabel
import numpy as np

def get_nitrain_dir():
    downloads_path = str(Path.home() / "Desktop/")
    return downloads_path    

def fetch_data(name, path=None):
    """
    Download example datasets from OpenNeuro and other sources.
    Datasets are pulled using `datalad` so the raw data will 
    not actually be dowloaded until it is needed. This makes it
    really fast.
    
    Arguments
    ---------
    name : string
        the dataset to download
        Options:
            - ds004711 [OpenNeuroDatasets/ds004711]
            
    Example
    -------
    >>> from nitrain.utils import download_data
    >>> ds = fetch_data('openneuro/ds004711')
    """
    
    if path is None:
        path = get_nitrain_dir()
    
    save_dir = os.path.join(path, name)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    ref = dl.clone(source=f'///{name}', path=save_dir)
    return ref


def files_to_array(files, dtype='float32'):
    # read in the images to a numpy array
    img_arrays = []
    for file in files:
        img = nibabel.load(file)
        img_array = img.get_fdata()
        img_arrays.append(img_array)
        
    img_arrays = np.array(img_arrays, dtype=dtype)
    return img_arrays