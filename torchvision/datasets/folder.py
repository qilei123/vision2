from .vision import VisionDataset

from PIL import Image

import os
import os.path
import sys
import torch
import json
import numpy as np
import cv2
DEBUG = False
HEATMAP=True
REFERRABLE=True
def has_file_allowed_extension(filename, extensions):
    """Checks if a file is an allowed extension.

    Args:
        filename (string): path to a file
        extensions (tuple of strings): extensions to consider (lowercase)

    Returns:
        bool: True if the filename ends with one of given extensions
    """
    return filename.lower().endswith(extensions)


def is_image_file(filename):
    """Checks if a file is an allowed image extension.

    Args:
        filename (string): path to a file

    Returns:
        bool: True if the filename ends with a known image extension
    """
    return has_file_allowed_extension(filename, IMG_EXTENSIONS)


def make_dataset(dir, class_to_idx, extensions=None, is_valid_file=None):
    images = []
    dir = os.path.expanduser(dir)
    if not ((extensions is None) ^ (is_valid_file is None)):
        raise ValueError("Both extensions and is_valid_file cannot be None or not None at the same time")
    if extensions is not None:
        def is_valid_file(x):
            return has_file_allowed_extension(x, extensions)
    for target in sorted(class_to_idx.keys()):
        d = os.path.join(dir, target)
        if not os.path.isdir(d):
            continue
        for root, _, fnames in sorted(os.walk(d)):
            for fname in sorted(fnames):
                path = os.path.join(root, fname)
                if is_valid_file(path):
                    item = (path, class_to_idx[target])
                    images.append(item)

    return images


def resize_flip(filename,input_size,srcarray):
    srcarray=cv2.resize(srcarray,(input_size,input_size))
    if '_vflip' in filename:
        srcarray = cv2.flip(srcarray,1)
    elif '_hflip' in filename:
        srcarray = cv2.flip(srcarray,0)
    elif '_vhflip' in filename:
        srcarray = cv2.flip(srcarray,1)
        srcarray = cv2.flip(srcarray,0)
    return srcarray

class DatasetFolder(VisionDataset):
    """A generic data loader where the samples are arranged in this way: ::

        root/class_x/xxx.ext
        root/class_x/xxy.ext
        root/class_x/xxz.ext

        root/class_y/123.ext
        root/class_y/nsdf3.ext
        root/class_y/asd932_.ext

    Args:
        root (string): Root directory path.
        loader (callable): A function to load a sample given its path.
        extensions (tuple[string]): A list of allowed extensions.
            both extensions and is_valid_file should not be passed.
        transform (callable, optional): A function/transform that takes in
            a sample and returns a transformed version.
            E.g, ``transforms.RandomCrop`` for images.
        target_transform (callable, optional): A function/transform that takes
            in the target and transforms it.
        is_valid_file (callable, optional): A function that takes path of an Image file
            and check if the file is a valid_file (used to check of corrupt files)
            both extensions and is_valid_file should not be passed.

     Attributes:
        classes (list): List of the class names.
        class_to_idx (dict): Dict with items (class_name, class_index).
        samples (list): List of (sample path, class_index) tuples
        targets (list): The class_index value for each image in the dataset
    """

    def __init__(self, root, loader, extensions=None, transform=None, target_transform=None, is_valid_file=None,
                        input_size=2000, with_heatmap = False,with_heatmap_v2=False,with_heatmap_v3 = False,with_heatmap_v4 = False,
                        DR_REFERRABLE=False):
        super(DatasetFolder, self).__init__(root)
        self.transform = transform
        self.target_transform = target_transform
        self.input_size=input_size
        self.with_heatmap = with_heatmap
        self.with_heatmap_v2 = with_heatmap_v2
        self.with_heatmap_v3 = with_heatmap_v3
        self.with_heatmap_v4 = with_heatmap_v4
        self.DR_REFERRABLE = DR_REFERRABLE
        classes, class_to_idx = self._find_classes(self.root)
        samples = make_dataset(self.root, class_to_idx, extensions, is_valid_file)
        
        if len(samples) == 0:
            raise (RuntimeError("Found 0 files in subfolders of: " + self.root + "\n"
                                "Supported extensions are: " + ",".join(extensions)))

        self.loader = loader
        self.extensions = extensions

        self.classes = classes
        self.class_to_idx = class_to_idx
        self.samples = samples
        self.targets = [s[1] for s in samples]
        if self.with_heatmap or self.with_heatmap_v2:
            self.heatmap_Hemorrhages_jsons=[]
            self.heatmap_Microaneurysms_jsons=[]
            self.heatmap_Hard_Exudate_jsons=[]
            self.heatmap_Cotton_Wool_Spot_jsons = []
            for stage in range(5):
                self.heatmap_Hemorrhages_jsons.append(json.load(open(os.path.join(self.root.replace('_aug','')+'_heatmap',str(stage),'Hemorrhages','positive_heatmap.json'))))
                self.heatmap_Microaneurysms_jsons.append(json.load(open(os.path.join(self.root.replace('_aug','')+'_heatmap',str(stage),'Microaneurysms','positive_heatmap.json'))))
                self.heatmap_Hard_Exudate_jsons.append(json.load(open(os.path.join(self.root.replace('_aug','')+'_heatmap',str(stage),'Hard_Exudate','positive_heatmap.json'))))
                self.heatmap_Cotton_Wool_Spot_jsons.append(json.load(open(os.path.join(self.root.replace('_aug','')+'_heatmap',str(stage),'Cotton_Wool_Spot','positive_heatmap.json'))))

    def _find_classes(self, dir):
        """
        Finds the class folders in a dataset.

        Args:
            dir (string): Root directory path.

        Returns:
            tuple: (classes, class_to_idx) where classes are relative to (dir), and class_to_idx is a dictionary.

        Ensures:
            No class is a subdirectory of another.
        """
        if sys.version_info >= (3, 5):
            # Faster and available in Python 3.5 and above
            classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        else:
            classes = [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
        classes.sort()
        class_to_idx = {classes[i]: i for i in range(len(classes))}
        #print(class_to_idx)
        #print(classes)
        if self.DR_REFERRABLE:
            class_to_idx={'0': 0, '1': 0, '2': 1, '3': 1, '4': 1}
            classes=['0','1']
        return classes, class_to_idx
    def create_heatmap_from_json(self,category_id,input_size,image_filename,original_image_filename,heatmap_path):
        stage=0
        if '/0/' in heatmap_path:
            stage=0
        elif '/1/' in heatmap_path:
            stage=1
        elif '/2/' in heatmap_path:
            stage=2
        elif '/3/' in heatmap_path:
            stage=3
        elif '/4/' in heatmap_path:
            stage=4
        if category_id==1:
            heatmap_json = self.heatmap_Hemorrhages_jsons[stage][original_image_filename]
        elif category_id==2:
            heatmap_json = self.heatmap_Microaneurysms_jsons[stage][original_image_filename]
        elif category_id==3:
            heatmap_json = self.heatmap_Hard_Exudate_jsons[stage][original_image_filename]
        elif category_id==4:
            heatmap_json = self.heatmap_Cotton_Wool_Spot_jsons[stage][original_image_filename]

        heatmap = np.zeros((heatmap_json['image_shape'][0],heatmap_json['image_shape'][1]))
        bbox_count=0
        if 'bboxes' in heatmap_json.keys():
            for bbox in heatmap_json['bboxes']:
                
                patch_heatmap = np.load(os.path.join(heatmap_path,original_image_filename+'_'+str(bbox_count)+'.npy'))
                heatmap[int(bbox[1]):int(bbox[1]+bbox[3]),int(bbox[0]):int(bbox[0]+bbox[2])] = patch_heatmap
                bbox_count+=1

        heatmap = resize_flip(image_filename,self.input_size,heatmap)
        return heatmap

    def get_heatmap(self,image_path,input_size):

        lesion_category = ['Hemorrhages','Microaneurysms','Hard_Exudate','Cotton_Wool_Spot']

        image_filename = os.path.basename(image_path)
        
        original_image_filename = image_filename

        heat_map_folder = image_path.replace(image_filename,'')
        if '/train_aug/' in heat_map_folder:
            heat_map_npy_path = heat_map_folder.replace('/train_aug/','/train_heatmap/')
        elif '/train/' in heat_map_folder:
            heat_map_npy_path = heat_map_folder.replace('/train/','/train_heatmap/')
        elif '/val_aug/' in heat_map_folder:
            heat_map_npy_path = heat_map_folder.replace('/val_aug/','/val_heatmap/')
        elif '/val/' in heat_map_folder:
            heat_map_npy_path = heat_map_folder.replace('/val/','/val_heatmap/')
        
        if '_vflip' in image_filename:
            original_image_filename = image_filename.replace('_vflip','')
        if '_hflip' in image_filename:
            original_image_filename = image_filename.replace('_hflip','')
        if '_vhflip' in image_filename:
            original_image_filename = image_filename.replace('_vhflip','')

        if True or '/0/' in image_path:
            heatmap1 = self.create_heatmap_from_json(1,input_size,image_filename,original_image_filename,
                                os.path.join(heat_map_npy_path,lesion_category[0],'positive_heatmap_v2'))
            heatmap2 = self.create_heatmap_from_json(2,input_size,image_filename,original_image_filename,
                                os.path.join(heat_map_npy_path,lesion_category[1],'positive_heatmap_v2'))
            heatmap3 = self.create_heatmap_from_json(3,input_size,image_filename,original_image_filename,
                                os.path.join(heat_map_npy_path,lesion_category[2],'positive_heatmap_v2'))
            heatmap4 = self.create_heatmap_from_json(4,input_size,image_filename,original_image_filename,
                                os.path.join(heat_map_npy_path,lesion_category[3],'positive_heatmap_v2'))
            heatmap1 = torch.stack([torch.from_numpy(heatmap1)],0)
            heatmap2 = torch.stack([torch.from_numpy(heatmap2)],0)
            heatmap3 = torch.stack([torch.from_numpy(heatmap3)],0)
            heatmap4 = torch.stack([torch.from_numpy(heatmap4)],0)
            heatmap = torch.cat((heatmap1,heatmap2,heatmap3,heatmap4),0)

            return heatmap
        else:
            heatmap1 = np.load(os.path.join(heat_map_npy_path,lesion_category[0],'positive_heatmap',original_image_filename+'.npy'))
            heatmap1 = resize_flip(image_filename,self.input_size,heatmap1)
            
            heatmap2 = np.load(os.path.join(heat_map_npy_path,lesion_category[1],'positive_heatmap',original_image_filename+'.npy'))
            heatmap2 = resize_flip(image_filename,self.input_size,heatmap2)
            
            heatmap3 = np.load(os.path.join(heat_map_npy_path,lesion_category[2],'positive_heatmap',original_image_filename+'.npy'))
            heatmap3 = resize_flip(image_filename,self.input_size,heatmap3)
            
            heatmap4 = np.load(os.path.join(heat_map_npy_path,lesion_category[3],'positive_heatmap',original_image_filename+'.npy'))
            heatmap4 = resize_flip(image_filename,self.input_size,heatmap4)
            
            heatmap1 = torch.stack([torch.from_numpy(heatmap1)],0)
            heatmap2 = torch.stack([torch.from_numpy(heatmap2)],0)
            heatmap3 = torch.stack([torch.from_numpy(heatmap3)],0)
            heatmap4 = torch.stack([torch.from_numpy(heatmap4)],0)
            heatmap = torch.cat((heatmap1,heatmap2,heatmap3,heatmap4),0)

            return heatmap
            
    def __getitem__(self, index):
        """
        Args:
            index (int): Index

        Returns:
            tuple: (sample, target) where target is class_index of the target class.
        """
    
        path, target = self.samples[index]
        sample = self.loader(path)
        if DEBUG:
            print('----------------')
            print(path)
            print(sample)
            print('----------------')
        if self.transform is not None:
            sample = self.transform(sample)
        if self.target_transform is not None:
            target = self.target_transform(target)
        if DEBUG:
            #sample_test = torch.cat((sample, sample), 0)
            #print(sample.size())
            #heatmap = self.get_heatmap(path,2000)
            #heatmap = self.get_heatmap(path,2000)
            #if not heatmap==None:
                #print(heatmap.size())
            print(path)
            print(target)
            pass
        if self.with_heatmap:
            heatmap = self.get_heatmap(path,self.input_size)
            heatmap = heatmap.type(sample.dtype)
            #print(heatmap.size())
            #print(sample.size())

            sample = torch.cat((sample,heatmap),0)
            #print(sample.size())
            #print(sample.size())
        if self.with_heatmap_v2:
            heatmap = self.get_heatmap(path,self.input_size)
            heatmap = heatmap.type(sample.dtype)
            #print(heatmap.size())
            #print(sample.size())

            sample1 = sample[:]*heatmap[0]
            sample2 = sample[:]*heatmap[1]
            sample3 = sample[:]*heatmap[2]
            sample4 = sample[:]*heatmap[3]
            
            sample = torch.cat((sample,sample1,sample2,sample3,sample4),0)
        if self.with_heatmap_v3:
            heatmap = self.get_heatmap(path,self.input_size)
            heatmap = heatmap.type(sample.dtype)
            #print(heatmap.size())
            #print(sample.size())
            sample = sample+sample*heatmap[0]+sample*heatmap[1]+sample*heatmap[2]+sample*heatmap[3]
            sample = sample/5
            #sample = torch.cat((sample,heatmap),0)  
        if self.with_heatmap_v4:
            heatmap = self.get_heatmap(path,self.input_size)
            heatmap = heatmap.type(sample.dtype)
            sample = torch.cat((sample,sample*heatmap[0],sample*heatmap[1],sample*heatmap[2],sample*heatmap[3]),0)

        return sample, target

    def __len__(self):
        return len(self.samples)



IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp')


def pil_loader(path):
    # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
    with open(path, 'rb') as f:
        img = Image.open(f)
        return img.convert('RGB')


def accimage_loader(path):
    import accimage
    try:
        return accimage.Image(path)
    except IOError:
        # Potentially a decoding problem, fall back to PIL.Image
        return pil_loader(path)


def default_loader(path):
    from torchvision import get_image_backend
    if get_image_backend() == 'accimage':
        return accimage_loader(path)
    else:
        return pil_loader(path)


class ImageFolder(DatasetFolder):
    """A generic data loader where the images are arranged in this way: ::

        root/dog/xxx.png
        root/dog/xxy.png
        root/dog/xxz.png

        root/cat/123.png
        root/cat/nsdf3.png
        root/cat/asd932_.png

    Args:
        root (string): Root directory path.
        transform (callable, optional): A function/transform that  takes in an PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
        loader (callable, optional): A function to load an image given its path.
        is_valid_file (callable, optional): A function that takes path of an Image file
            and check if the file is a valid_file (used to check of corrupt files)

     Attributes:
        classes (list): List of the class names.
        class_to_idx (dict): Dict with items (class_name, class_index).
        imgs (list): List of (image path, class_index) tuples
    """

    def __init__(self, root, transform=None, target_transform=None,
                 loader=default_loader, is_valid_file=None,input_size=2000,with_heatmap=False,with_heatmap_v2=False,
                 DR_REFERRABLE=False):
        super(ImageFolder, self).__init__(root, loader, IMG_EXTENSIONS if is_valid_file is None else None,
                                          transform=transform,
                                          target_transform=target_transform,
                                          is_valid_file=is_valid_file,
                                          input_size=input_size,
                                          with_heatmap=with_heatmap,
                                          with_heatmap_v2 = with_heatmap_v2,
                                          DR_REFERRABLE=DR_REFERRABLE)
        self.imgs = self.samples
    def get_imgs(self):
        return self.imgs
    def set_imgs(self,imgs):
        self.samples = imgs