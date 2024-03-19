import os
import textwrap


from ..platform import (_upload_dataset_to_platform, 
                        _upload_job_script_to_platform,
                        _upload_model_to_platform,
                        _launch_training_job_on_platform,
                        _convert_to_platform_dataset, 
                        _get_user_from_token)

class CloudTrainer:
    """
    The CloudTrainer class lets you train deep learning models
    on GPU resources in the cloud.
    """
    
    def __init__(self, model, task, name, resource='gpu-small', token=None):
        """
        Initialize a cloud trainer
        
        Examples
        --------
        >>> download = fetch_data('openneuro/ds004711')
        >>> data = FolderDataset(download.path)
        >>> loader = DatasetLoader(data, batch_size=32)
        >>> model_fn = fetch_architecture('autoencoder')
        >>> model = model_fn((120, 60, 30))
        >>> trainer = CloudTrainer(model, name='t1-brain-age', resource='gpu-small')
        >>> job = trainer.fit(loader, epochs=10)
        >>> print(job.status)
        >>> print(job.model)
        """
        
        # check for platform credentials
        if token is None:
            token = os.environ.get('NITRAIN_API_TOKEN')
            if token is None:
                raise Exception('No api token given or found. Set `NITRAIN_API_TOKEN` or create an account to get your token.')

        self.user = _get_user_from_token(token)
        self.model = model
        self.task = task
        self.name = name
        self.resource = resource
        self.token = token
    
    def fit(self, loader, epochs):
        """
        Launch a training job on the platform.
        
        This function is used in the same was as for `ModelTrainer`, except that
        calling `fit()` with a `CloudTrainer` will launch a training job on the platform.
        
        If the dataset for the loader passed into this function is not a `PlatformDataset` then the
        dataset will be temporarily uploaded to the cloud for training and then deleted after. To save
        time on repeated training jobs, the loader can be cached by setting `cache=True` when 
        initializing the trainer.
        
        Arguments
        ---------
        loader : an instance of DatasetLoader or similar class
            The batch generator used to train the mode
            
        epochs : integer
            The number of epochs to train the model for.
            
        Returns
        -------
        None. The status of the job can be checked by calling `trainer.status` and the
        fitted model can be eventually retrieved by calling `trainer.model`.
        """
        job_name = f'{self.user}__{self.name}'
        job_dir = f'{self.user}/{self.name}'
        # Generate training script
        
        # imports
        repr_imports = '''
        from nitrain import datasets, loaders, models, trainers, transforms as tx
        '''
        
        # dataset
        platform_dataset = _convert_to_platform_dataset(loader.dataset, job_dir)
        repr_dataset = f'''
        dataset = {repr(platform_dataset)}
        '''
        
        # loader
        repr_loader = f'''
        loader = {repr(loader)}
        '''
        
        # model
        repr_model = f'''
        model = models.load_model("/gcs/ants-dev/models/{job_dir}")
        '''
        
        # trainer
        repr_trainer = f'''
        trainer = trainers.ModelTrainer(model=model, task="{self.task}")
        trainer.fit(loader, epochs={epochs})
        '''
        
        # save model
        repr_save = f'''
        trainer.save("/gcs/ants-dev/models/{job_dir}")
        '''
        
        # write training script to file
        script_file = f'/Users/ni5875cu/Desktop/{job_name}.py'
        with open(script_file, 'w') as f:
            f.write(textwrap.dedent(repr_imports))
            f.write(textwrap.dedent(repr_dataset))
            f.write(textwrap.dedent(repr_loader))
            f.write(textwrap.dedent(repr_model))
            f.write(textwrap.dedent(repr_trainer))
            f.write(textwrap.dedent(repr_save))
        
        # upload training script to platform: /ants-dev/jobs/{job_name}.py
        _upload_job_script_to_platform(script_file, f'{job_name}.py')
        
        # upload original dataset to platform: /ants-dev/datasets/{user}/{name}/
        _upload_dataset_to_platform(loader.dataset, job_dir)
        
        # upload untrained model to platform: /ants-dev/models/{user}/{name}.keras
        _upload_model_to_platform(self.model, job_dir)
        
        # launch job
        _launch_training_job_on_platform(job_name, job_dir)
        
    
    @property
    def status(self):
        """
        Check status of launched training job
        """
        pass

