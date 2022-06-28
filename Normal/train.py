import time
import torch
import torchvision
from torch import nn
from torch.utils.data import DataLoader
from torchvision.models import alexnet
from torchvision import transforms
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='CV Train')
    parser.add_mutually_exclusive_group()
    parser.add_argument('--dataset', type=str, default='CIFAR10', help='CIFAR10')
    parser.add_argument('--dataset_root', type=str, default='../data', help='Dataset root directory path')
    parser.add_argument('--img_size', type=int, default=227, help='image size')
    parser.add_argument('--tensorboard', type=str, default=True, help='Use tensorboard for loss visualization')
    parser.add_argument('--tensorboard_log', type=str, default='../tensorboard', help='tensorboard folder')
    parser.add_argument('--cuda', type=str, default=True, help='if is cuda available')
    parser.add_argument('--batch_size', type=int, default=64, help='batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='learning rate')
    parser.add_argument('--epochs', type=int, default=20, help='Number of epochs to train.')
    parser.add_argument('--checkpoint', type=str, default='../checkpoint', help='Save .pth fold')
    return parser.parse_args()


args = parse_args()

# 1.Create SummaryWriter
if args.tensorboard:
    writer = SummaryWriter(args.tensorboard_log)

# 2.Ready dataset
if args.dataset == 'CIFAR10':
    train_dataset = torchvision.datasets.CIFAR10(root=args.dataset_root, train=True, transform=transforms.Compose(
        [transforms.Resize(args.img_size), transforms.ToTensor()]), download=True)
else:
    raise ValueError("Dataset is not CIFAR10")
cuda = torch.cuda.is_available()
print('CUDA available: {}'.format(cuda))

# 3.Length
train_dataset_size = len(train_dataset)
print("the train dataset size is {}".format(train_dataset_size))

# 4.DataLoader
train_dataloader = DataLoader(dataset=train_dataset, batch_size=args.batch_size)

# 5.Create model
model = alexnet()

if args.cuda == cuda:
    model = model.cuda()

# 6.Create loss
cross_entropy_loss = nn.CrossEntropyLoss()

# 7.Optimizer
optim = torch.optim.AdamW(model.parameters(), lr=args.lr)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optim, patience=3, verbose=True)
# 8. Set some parameters to control loop
# epoch
iter = 0
t0 = time.time()
for epoch in range(args.epochs):
    t1 = time.time()
    print(" -----------------the {} number of training epoch --------------".format(epoch))
    model.train()
    for data in train_dataloader:
        loss = 0
        imgs, targets = data
        if args.cuda == cuda:
            cross_entropy_loss = cross_entropy_loss.cuda()
            imgs, targets = imgs.cuda(), targets.cuda()
        outputs = model(imgs)
        loss_train = cross_entropy_loss(outputs, targets)
        loss = loss_train.item() + loss
        if args.tensorboard:
            writer.add_scalar("train_loss", loss_train.item(), iter)

        optim.zero_grad()
        loss_train.backward()
        optim.step()
        iter = iter + 1
        if iter % 100 == 0:
            print(
                "Epoch: {} | Iteration: {} | lr: {} | loss: {} | np.mean(loss): {} "
                    .format(epoch, iter, optim.param_groups[0]['lr'], loss_train.item(),
                            np.mean(loss)))
    if args.tensorboard:
        writer.add_scalar("lr", optim.param_groups[0]['lr'], epoch)
    scheduler.step(np.mean(loss))
    t2 = time.time()
    h = (t2 - t1) // 3600
    m = ((t2 - t1) % 3600) // 60
    s = ((t2 - t1) % 3600) % 60
    print("epoch {} is finished, and time is {}h{}m{}s".format(epoch, int(h), int(m), int(s)))

    if epoch % 1 == 0:
        print("Save state, iter: {} ".format(epoch))
        torch.save(model.state_dict(), "{}/AlexNet_{}.pth".format(args.checkpoint, epoch))

torch.save(model.state_dict(), "{}/AlexNet.pth".format(args.checkpoint))
t3 = time.time()
h_t = (t3 - t0) // 3600
m_t = ((t3 - t0) % 3600) // 60
s_t = ((t3 - t0) % 3600) // 60
print("The finished time is {}h{}m{}s".format(int(h_t), int(m_t), int(s_t)))
if args.tensorboard:
    writer.close()
