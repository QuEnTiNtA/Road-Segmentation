import os
import shutil
from torch.utils.data import DataLoader
import numpy as np
from PIL import Image
from patchify import patchify
from train import *
import albumentations as A

def save_checkpoint(state, filename="my_checkpoint.pth"):
    print("=> Saving checkpoint")
    torch.save(state, filename)

def load_checkpoint(checkpoint, model):
    print("=> Loading checkpoint")
    model.load_state_dict(checkpoint["state_dict"])

# class RoadDataset(Dataset):
#     def __init__(self, image_dir, mask_dir, transform=None):
#         self.image_dir = image_dir
#         self.mask_dir = mask_dir
#         self.transform = transform
#         self.images = os.listdir(image_dir) # list all the files that are in that folder

#     def __len__(self):
#         return len(self.images)

#     def __getitem__(self, index):
#         img_path = os.path.join(self.image_dir, self.images[index])
#         mask_path = os.path.join(self.mask_dir, self.images[index])
#         image = np.array(Image.open(img_path).convert("RGB"))
#         mask = np.array(Image.open(mask_path).convert("L"), dtype=np.float32) # grayscale
#         mask = np.where(mask > 4.0, 1.0, 0.0)
#         # mask[mask == 237.0] = 1.0 # white --> 1, implement sigmoid as the last activation. rgb(0,0,0): black, rgb(255, 255, 255):

#         if self.transform is not None:
#             augmentations = self.transform(image=image, mask=mask)
#             image = augmentations["image"]
#             mask = augmentations["mask"]

#         return image, mask

class RoadDataset(Dataset):
    def __init__(self, image_dir, mask_dir, transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        if transform != None:
            self.transform_both = transform[0]   # transforms that should be applied to both images and masks
            self.transform_image = transform[1]  # transforms that should only be applied to images
        self.images = os.listdir(image_dir)  # list all the files that are in that folder

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        img_path = os.path.join(self.image_dir, self.images[index])
        mask_path = os.path.join(self.mask_dir, self.images[index])
        image = np.array(Image.open(img_path).convert("RGB"))
        mask = np.array(Image.open(mask_path).convert("L"), dtype=np.float32) # grayscale
        mask = np.where(mask > 4.0, 1.0, 0.0)
        # mask[mask == 237.0] = 1.0 # white --> 1, implement sigmoid as the last activation. rgb(0,0,0): black, rgb(255, 255, 255):

        if self.transform_both is not None:
            augmentations = self.transform_both(image=image, mask=mask)
            image = augmentations["image"]
            mask = augmentations["mask"]
            augmentations = self.transform_image(image=image)
            image = augmentations["image"]

        if img_path == mask_path:  # if the paths are the same, the dataset is for the reconstruction pretraining
            return image, image
        else:
            return image, mask

# def get_transform(
#     image_height,
#     image_width,
#     max_rotation,
#     p_hflip,
#     p_vflip,
#     normalize,
#     crop_width,
#     crop_height
# ):
#     cwidth = int(crop_width)
#     cheight = int(crop_height)
#     transformations = []
#     if(image_height != 0):
#         transformations.append(A.Resize(height=image_height, width=image_width))
#     if(max_rotation > 0):
#         transformations.append(A.Rotate(limit=max_rotation, p=1.0))
#     if(p_hflip > 0):
#         transformations.append(A.HorizontalFlip(p=p_hflip))
#     if(p_vflip > 0):
#         transformations.append(A.VerticalFlip(p=p_vflip))
#     if(normalize):
#         transformations.append(A.Normalize(
#             mean=[0.0, 0.0, 0.0],
#             std=[1.0, 1.0, 1.0],
#             max_pixel_value=237.0, # dividing by 237, get a value between 0 and 1
#         ))
#     if(cwidth > 0):
#         transformations.append(A.RandomCrop(width=cwidth, height=cheight))
#     transformations.append(A.pytorch.ToTensorV2())
#     return A.Compose(transformations)

# def get_train_transform():
#     transform = A.Compose(
#         [
#             A.Resize(height=400, width=400),
#             A.ShiftScaleRotate(rotate_limit=180, p=0.6),
#             A.HorizontalFlip(p=0.5),
#             A.VerticalFlip(p=0.1),
#             A.GaussNoise(p=0.1),
#             A.GaussianBlur(blur_limit=(3, 7), sigma_limit=0, p=0.1),
#             A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
#             A.ElasticTransform(p=0.05),
#             A.Normalize(
#                 mean=[0.0, 0.0, 0.0],
#                 std=[1.0, 1.0, 1.0],
#                 max_pixel_value=237.0, # dividing by 237, get a value between 0 and 1
#             ),
#             # A.RandomCrop(height = 300, width = 300, p = 0.5),
#             # A.PadIfNeeded(min_height=600, min_width=600),
#             A.pytorch.ToTensorV2()
#         ])
#     return transform

# def get_val_transform():
#     transform = A.Compose(
#         [
#             A.Resize(height=400, width=400),
#             A.Normalize(
#                 mean=[0.0, 0.0, 0.0],
#                 std=[1.0, 1.0, 1.0],
#                 max_pixel_value=237.0, # dividing by 237, get a value between 0 and 1
#             ),
#             A.pytorch.ToTensorV2()
#         ])
#     return transform

def get_transform(train):
    if train:
        transform_0 = A.Compose(
            [
                A.Normalize(
                    # mean=[0.0, 0.0, 0.0],
                    # std=[1.0, 1.0, 1.0],
                    mean=[0.5, 0.5, 0.5],
                    std=[0.5, 0.5, 0.5],
                    max_pixel_value=255.0,
                ),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                # A.RandomRotate90(p=0.5),  # Randomly rotate the input by 90 degrees zero or more times; performance no difference
                # A.ElasticTransform(p=0.2),
                # A.ShiftScaleRotate(rotate_limit=180, p=0.2),
                A.Rotate(limit=90, p=0.2), 
                # A.RandomResizedCrop(height=400, width=400, scale=(0.6, 1.0), ratio=(0.8, 1.2), p=0.2)
                A.RandomCrop(height=304, width=304, p=1)
                # A.OneOf([
                #     A.RandomResizedCrop(height=304, width=304, scale=(0.6, 1.0), ratio=(0.8, 1.2), p=0.5),
                #     A.RandomCrop(height=304, width=304, p=1)
                # ], p=1)
            ]
        )
        transform_1 = A.Compose(
            [ 
                A.GaussianBlur(p=0.2),
                # A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.2),  # much worse performance
                A.pytorch.ToTensorV2(),
            ]
        )
        transform = [transform_0, transform_1]
    else:
        transform = A.Compose(
            [
                # A.Resize(height=608, width=608),
                A.Normalize(
                    # mean=[0.0, 0.0, 0.0],
                    # std=[1.0, 1.0, 1.0],
                    mean=[0.5, 0.5, 0.5],
                    std=[0.5, 0.5, 0.5],
                    max_pixel_value=255.0,
                ),           
                A.pytorch.ToTensorV2(),
            ]
        )

    return transform


# if fold 'test_images' is empty
# determination = 'data/test_images/'
# if not os.path.exists(determination):
#     os.makedirs(determination)

# path = 'data/test/'
# folders = os.listdir(path)
# for folder in folders:
#     dir = path + '/' + str(folder)
#     files = os.listdir(dir)
#     for file in files:
#         source = dir + '/' + str(file)
#         deter = determination + '/' + str(file)
#         shutil.copyfile(source, deter)


class RoadData_test_set(Dataset):

    def __init__(self, image_dir, transform=None, test_dir='data/test_images/'):
        self.image_dir = image_dir
        self.transform = transform
        path_list = os.listdir(test_dir)
        path_list.sort(key=lambda x: int(x.split(".")[0].split("_")[1]))
        self.images = path_list # list all the files that are in that folder

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        img_path = os.path.join(self.image_dir, self.images[index])
        image = np.array(Image.open(img_path).convert("RGB"))

        if self.transform is not None:
            augmentations = self.transform(image=image)
            image = augmentations["image"]
        
        # patches = patchify(np.array(image), (3, 400, 400), step=208)
        # patches = patchify(np.array(image), (3, 304, 304), step=152)
        patches = patchify(np.array(image), (3, 304, 304), step=76)  # (608 - 304) / 4 = 76
        # patches = patchify(np.array(image), (3, 304, 304), step=38)  # (608 - 304) / 8 = 38

        # return torch.Tensor(patches).reshape(4, 3, 304, 304)
        # return torch.Tensor(patches).reshape(9, 3, 304, 304)
        return torch.Tensor(patches).reshape(25, 3, 304, 304)  # (608 - 304) / 76 + 1 = 5
        # return torch.Tensor(patches).reshape(81, 3, 304, 304)  # (608 - 304) / 38 + 1 = 9
        # return torch.Tensor(patches).reshape(16, 3, 152, 152)

def get_test_loader(batch_size, num_workers, pin_memory, test_dir='data/test_images/'):

    image_height = 608  #  400 pixels originally
    image_width = 608  #  400 pixels originally

    # test_transform = get_transform(image_height, image_width, 0, 0, 0, True, 0, 0)
    test_transform = get_transform(train=False)

    test_dataset = RoadData_test_set(
        image_dir = test_dir,
        transform=test_transform,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=False
    )

    return test_loader
