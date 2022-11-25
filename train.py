import os
from PIL import Image
from torch.utils.data import Dataset
import numpy as np
import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2
import torchvision.transforms.functional as TF
import torchvision
from tqdm import tqdm

def train_epoch(train_loader, model, optimizer, epoch, loss_fn, scaler, scheduler):
    loop = tqdm(train_loader)

    TP = 0
    FP = 0
    TN = 0
    FN = 0
    num_correct = 0
    num_pixels = 0

    for batch_idx, (data, targets) in enumerate(loop):
        data = data.to(device=DEVICE)
        targets = targets.float().unsqueeze(1).to(device=DEVICE) # add a channel dimension
        # forward
        with torch.cuda.amp.autocast():
            output = model(data)
            loss = loss_fn(output, targets)
            
        scheduler.step(loss)
        
        # backward
        optimizer.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        # update tqdm loop
        loop.set_postfix(loss=loss.item())

        preds = torch.sigmoid(output)
        preds = (preds > 0.5).float()
        #print(TP,FP,FN,preds.sum())
        TP += ((preds == 1)*(targets==1)).sum()
        FP += ((preds == 1)*(targets==0)).sum()
        FN += ((preds == 0)*(targets==1)).sum()
        num_pixels += torch.numel(preds)
        num_correct += (preds == targets).sum()

    recall = TP/(TP+FN)
    precision = TP/(TP+FP)

    print(
        f"Training set: epoch-{epoch} got {num_correct}/{num_pixels} with acc {num_correct/num_pixels*100:.2f}% and F1-score {2*recall*precision/(recall+precision):.2f} "
    )

    return num_correct/num_pixels, 2*recall*precision/(recall+precision)


def check_F1_score(val_loader, model, epoch):
    TP = 0
    FP = 0
    TN = 0
    FN = 0
    num_correct = 0
    num_pixels = 0
    model.eval()

    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device=DEVICE)
            y = y.to(device=DEVICE).unsqueeze(1) # the grayscale does not have channels, add
            preds = torch.sigmoid(model(x))
            preds = (preds > 0.5).float()
            #print(TP,FP,FN,preds.sum())
            TP += ((preds == 1)*(y==1)).sum()
            FP += ((preds == 1)*(y==0)).sum()
            FN += ((preds == 0)*(y==1)).sum()
            num_pixels += torch.numel(preds)
            num_correct += (preds == y).sum()
    recall = TP/(TP+FN)
    precision = TP/(TP+FP)
    
    print(
        f"Validation set: epoch-{epoch} got {num_correct}/{num_pixels} with acc {num_correct/num_pixels*100:.2f}% and F1-score {2*recall*precision/(recall+precision):.2f}"
    )
    model.train()

    return num_correct/num_pixels, 2*recall*precision/(recall+precision)

def save_predictions_as_imgs(
    test_loader, model, folder="saved_images", device="cuda"
):
    model.eval()
    for idx, x in enumerate(test_loader):
        x = x.to(device=device)
        with torch.no_grad():
            preds = torch.sigmoid(model(x))
            preds = (preds > 0.5).float()
        torchvision.utils.save_image(
            preds, f"{folder}/pred_{idx+1}.png"
        )

    model.train()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

