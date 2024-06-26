import os
import unittest
from main import run_tests

import tempfile

import numpy as np
import numpy.testing as nptest

import ants
import nitrain as nt
from nitrain import transforms as tx
from nitrain.readers import ImageReader
from nitrain.samplers import SliceSampler

class TestClass_Predictor(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_image_to_image_segmentation(self):
        base_dir = nt.fetch_data('example-01')

        dataset = nt.Dataset(inputs=ImageReader('*/img3d.nii.gz'),
                            outputs=ImageReader('*/img3d_seg.nii.gz'),
                            transforms={
                                    ('inputs','outputs'): tx.Resample((40,40,40))
                            },
                            base_dir=base_dir)
        
        arch_fn = nt.fetch_architecture('unet', dim=2)
        model = arch_fn((40,40,1),
                        number_of_outputs=1,
                        number_of_layers=4,
                        number_of_filters_at_base_layer=16,
                        mode='sigmoid')
        
        # inference on test data
        predictor = nt.Predictor(model, 
                                 task='segmentation',
                                 sampler=SliceSampler(axis=-1))
        y_pred = predictor.predict(dataset)
        
    def test_image_to_image_regression(self):
        base_dir = nt.fetch_data('example-01')

        dataset = nt.Dataset(inputs=ImageReader('*/img3d.nii.gz'),
                            outputs=ImageReader('*/img3d_100.nii.gz'),
                            transforms={
                                    ('inputs','outputs'): tx.Resample((40,40,40))
                            },
                            base_dir=base_dir)

        arch_fn = nt.fetch_architecture('unet', dim=2)
        model = arch_fn((40,40,1),
                        number_of_outputs=1,
                        number_of_layers=4,
                        number_of_filters_at_base_layer=16,
                        mode='regression')
        
        # inference on test data
        predictor = nt.Predictor(model,
                                 task='regression',
                                 sampler=SliceSampler(axis=-1))
        y_pred = predictor.predict(dataset)
        
        self.assertTrue(ants.is_image(y_pred[0]))
        self.assertEqual(y_pred[0].shape, (40,40,40))
        self.assertEqual(len(y_pred), len(dataset))
        
        
if __name__ == '__main__':
    run_tests()
