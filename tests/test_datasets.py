import os
import unittest

from tempfile import mkdtemp
import shutil
import pandas as pd

import ntimage as nti
import nitrain as nt
from nitrain import readers, transforms as tx

from main import run_tests

class TestClass_Dataset(unittest.TestCase):
    def setUp(self):
        pass
         
    def tearDown(self):
        pass
    
    def test_memory(self):
        dataset = nt.Dataset(
            inputs = [nti.ones((128,128))*i for i in range(10)],
            outputs = [i for i in range(10)]
        )
        self.assertEqual(len(dataset), 10)
        
        x, y = dataset[4]
        
        self.assertEqual(y, 4)
        self.assertTrue(nti.is_ntimage(x))
        self.assertEqual(x.mean(), 4)
        
        # test repr
        r = dataset.__repr__()
    
    def test_memory_double_inputs(self):
        dataset = nt.Dataset(
            inputs = [readers.ImageReader([nti.ones((128,128))*i for i in range(10)]),
                      readers.ImageReader([nti.ones((128,128))*i*2 for i in range(10)])],
            outputs = [i for i in range(10)]
        )
        self.assertEqual(len(dataset), 10)
        
        x, y = dataset[4]
        
        self.assertTrue(len(x), 2)
        self.assertTrue(nti.is_ntimage(x[0]))
        self.assertTrue(nti.is_ntimage(x[1]))
        self.assertEqual(x[0].mean(), 4)
        self.assertEqual(x[1].mean(), 8)
        self.assertEqual(y, 4)

class TestClass_CSVDataset(unittest.TestCase):
    def setUp(self):
        # set up directory
        tmp_dir = mkdtemp()
        img2d = nti.load(nti.example_data('r16'))
        img3d = nti.load(nti.example_data('mni'))
        
        filenames_2d = []
        filenames_3d = []
        for i in range(5):
            sub_dir = os.path.join(tmp_dir, f'sub_{i}')
            os.mkdir(sub_dir)
            filepath_2d = os.path.join(sub_dir, 'img2d.nii.gz')
            filenames_2d.append(filepath_2d)
            nti.save(img2d, filepath_2d)
            
            filepath_3d = os.path.join(sub_dir, 'img3d.nii.gz')
            filenames_3d.append(filepath_3d)
            nti.save(img3d, filepath_3d)
        
        # write csv file
        ids = [f'sub_{i}' for i in range(5)]
        age = [i + 50 for i in range(5)]
        df = pd.DataFrame({'sub_id': ids, 'age': age, 
                           'filenames_2d': filenames_2d,
                           'filenames_3d': filenames_3d})
        df.to_csv(os.path.join(tmp_dir, 'participants.csv'), index=False)
        
        self.tmp_dir = tmp_dir
         
    def tearDown(self):
       shutil.rmtree(self.tmp_dir)
    
    def test_2d(self):
        tmp_dir = self.tmp_dir
        dataset = nt.Dataset(
            inputs=readers.ColumnReader(file='participants.csv',
                                        column='filenames_2d',
                                        is_image=True),
            outputs=readers.ColumnReader(file='participants.csv',
                                         column='age'),
            base_dir=tmp_dir
        )
        self.assertEqual(len(dataset), 5)
        self.assertTrue(dataset.inputs.values[0].endswith('.nii.gz'))
        self.assertEqual(dataset.outputs.values[2], 52)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        self.assertTrue(nti.is_ntimage(x[0]))
        self.assertEqual(y, [50, 51])
        
        # test repr
        r = dataset.__repr__()
        
    def test_3d(self):
        tmp_dir = self.tmp_dir
        dataset = nt.Dataset(
            inputs=readers.ColumnReader(column='filenames_3d', is_image=True),
            outputs=readers.ColumnReader(column='age'),
            base_file=os.path.join(tmp_dir, 'participants.csv')
        )
        self.assertEqual(len(dataset), 5)
        self.assertTrue(dataset.inputs.values[0].endswith('.nii.gz'))
        self.assertEqual(dataset.outputs.values[2], 52)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        self.assertTrue(nti.is_ntimage(x[0]))
        self.assertEqual(y, [50, 51])

    def test_missing_file(self):
        with self.assertRaises(Exception):
            # file arg is needed somewhere
            dataset = nt.Dataset(
                inputs=readers.ColumnReader(column='filenames_3d', is_image=True),
                outputs=readers.ColumnReader(column='age')
            )

class TestClass_FolderDataset(unittest.TestCase):
    def setUp(self):
        # set up directory
        tmp_dir = mkdtemp()
        self.tmp_dir = tmp_dir
        img2d = nti.load(nti.example_data('r16'))
        img3d = nti.load(nti.example_data('mni'))
        for i in range(5):
            sub_dir = os.path.join(tmp_dir, f'sub_{i}')
            os.mkdir(sub_dir)
            nti.save(img2d, os.path.join(sub_dir, 'img2d.nii.gz'))
            nti.save(img3d, os.path.join(sub_dir, 'img3d.nii.gz'))
        
        # write csv file
        ids = [f'sub_{i}' for i in range(5)]
        age = [i + 50 for i in range(5)]
        df = pd.DataFrame({'sub_id': ids, 'age': age})
        df.to_csv(os.path.join(tmp_dir, 'participants.csv'), index=False)
        
    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
    
    def test_2d(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x={'pattern': '*/img2d.nii.gz'},
            y={'file': 'participants.csv', 'column': 'age'}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        
        # test repr
        r = dataset.__repr__()
        
    def test_double_image_input(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x=[{'pattern': '*/img2d.nii.gz'},{'pattern': '*/img2d.nii.gz'}],
            y={'file': 'participants.csv', 'column': 'age'}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.x[0]) == 2)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        self.assertTrue(len(x[0]) == 2)

    def test_2d_image_to_image(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x={'pattern': '*/img2d.nii.gz'},
            y={'pattern': '*/img2d.nii.gz'}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)

    def test_2d_image_to_image_and_x_transforms(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x={'pattern': '*/img2d.nii.gz'},
            y={'pattern': '*/img2d.nii.gz'},
            transforms={'x': [tx.Resample((69,69))]}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        
        self.assertTrue(x[0].shape==(69,69))
        self.assertTrue(y[0].shape!=(69,69))
        
    def test_2d_image_to_image_and_co_transforms(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x={'pattern': '*/img2d.nii.gz'},
            y={'pattern': '*/img2d.nii.gz'},
            transforms={'co': [tx.Resample((69,69))]}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)
        
        self.assertTrue(x[0].shape==(69,69))
        self.assertTrue(y[0].shape==(69,69))
        
    def test_3d(self):
        dataset = nt.FolderDataset(
            base_dir=self.tmp_dir,
            x={'pattern': '*/img3d.nii.gz'},
            y={'file': 'participants.csv', 'column': 'age'}
        )
        self.assertTrue(len(dataset.x) == 5)
        self.assertTrue(len(dataset.y) == 5)
        
        x, y = dataset[:2]
        self.assertTrue(len(x) == 2)


if __name__ == '__main__':
    run_tests()
