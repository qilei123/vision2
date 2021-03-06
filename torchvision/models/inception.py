from collections import namedtuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from .utils import load_state_dict_from_url


__all__ = ['Inception3', 'inception_v3','inception_v3_wide']


model_urls = {
    # Inception v3 ported from TensorFlow
    'inception_v3_google': 'https://download.pytorch.org/models/inception_v3_google-1a9a5a14.pth',
}

_InceptionOuputs = namedtuple('InceptionOuputs', ['logits', 'aux_logits'])


def inception_v3(pretrained=False, progress=True, **kwargs):
    r"""Inception v3 model architecture from
    `"Rethinking the Inception Architecture for Computer Vision" <http://arxiv.org/abs/1512.00567>`_.

    .. note::
        **Important**: In contrast to the other models the inception_v3 expects tensors with a size of
        N x 3 x 299 x 299, so ensure your images are sized accordingly.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
        aux_logits (bool): If True, add an auxiliary branch that can improve training.
            Default: *True*
        transform_input (bool): If True, preprocesses the input according to the method with which it
            was trained on ImageNet. Default: *False*
    """
    if pretrained:
        if 'transform_input' not in kwargs:
            kwargs['transform_input'] = True
        if 'aux_logits' in kwargs:
            original_aux_logits = kwargs['aux_logits']
            kwargs['aux_logits'] = True
        else:
            original_aux_logits = True
        model = Inception3(**kwargs)
        state_dict = load_state_dict_from_url(model_urls['inception_v3_google'],
                                              progress=progress)
        model_dict=model.state_dict()
        pretrained_dict = {k: v for k, v in state_dict.items() if not('Conv2d_1a_3x3' in k or 'deephead' in k)}
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)
        if not original_aux_logits:
            model.aux_logits = False
            del model.AuxLogits
        return model

    return Inception3(**kwargs)

def inception_v3_wide(pretrained=False, progress=True, **kwargs):
    r"""Inception v3 model architecture from
    `"Rethinking the Inception Architecture for Computer Vision" <http://arxiv.org/abs/1512.00567>`_.

    .. note::
        **Important**: In contrast to the other models the inception_v3 expects tensors with a size of
        N x 3 x 299 x 299, so ensure your images are sized accordingly.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr
        aux_logits (bool): If True, add an auxiliary branch that can improve training.
            Default: *True*
        transform_input (bool): If True, preprocesses the input according to the method with which it
            was trained on ImageNet. Default: *False*
    """
    if pretrained:
        if 'transform_input' not in kwargs:
            kwargs['transform_input'] = True
        if 'aux_logits' in kwargs:
            original_aux_logits = kwargs['aux_logits']
            kwargs['aux_logits'] = True
        else:
            original_aux_logits = True
        model = Inception3(**kwargs)
        state_dict = load_state_dict_from_url(model_urls['inception_v3_google'],
                                              progress=progress)
        model_dict=model.state_dict()
        pretrained_dict = {k: v for k, v in state_dict.items() if not('Conv2d_1a_3x3' in k)}
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)
        if not original_aux_logits:
            model.aux_logits = False
            del model.AuxLogits
        return model

    return Inception3(wide = True,**kwargs)

class Inception3(nn.Module):

    def __init__(self, num_classes=1000, aux_logits=True, transform_input=False,
                            wide = False,wider = False,wide2=False,wider2=False,bigger_wider = False,
                            with_heatmap=False,with_heatmap_v2=False,with_deephead_v1=False,with_deephead_v2=False):
        super(Inception3, self).__init__()
        self.with_deephead_v1 = with_deephead_v1
        self.with_deephead_v2 = with_deephead_v2
        self.aux_logits = aux_logits
        self.transform_input = transform_input
        #print(self.transform_input)
        self.wider = wider
        self.wide2 = wide2
        self.wider2 = wider2
        self.bigger_wider = bigger_wider
        self.with_heatmap = with_heatmap
        self.with_heatmap_v2 = with_heatmap_v2
        if bigger_wider:
            self.Conv2d_1a_3x3a = BasicConv2d(3, 32, kernel_size=21, stride=10,padding = 10)
            self.Conv2d_1a_3x3b = BasicConv2d(3, 32, kernel_size=41, stride=10,padding = 20)
            self.Conv2d_1a_3x3c = BasicConv2d(3, 32, kernel_size=81, stride=10,padding = 40)
        elif wider2:
            self.Conv2d_1a_3x3 = BasicConv2d_wider2(3, 32)
        elif wider:
            self.Conv2d_1a_3x3a = BasicConv2d(3, 32, kernel_size=15, stride=5,padding = 7)
            self.Conv2d_1a_3x3b = BasicConv2d(3, 32, kernel_size=31, stride=5,padding = 15)
            self.Conv2d_1a_3x3c = BasicConv2d(3, 32, kernel_size=61, stride=5,padding = 30)
        elif wide:
            self.Conv2d_1a_3x3 = BasicConv2d(3, 32, kernel_size=15, stride=5,padding = 7)
        elif with_heatmap:
            self.Conv2d_1a_3x3_with_heatmap = BasicConv2d(7, 32, kernel_size=3, stride=2)
        elif with_heatmap_v2:
            self.Conv2d_1a_3x3_with_heatmap = BasicConv2d(15, 32, kernel_size=3, stride=2)
        else:
            self.Conv2d_1a_3x3 = BasicConv2d(3, 32, kernel_size=3, stride=2)
        self.Conv2d_2a_3x3 = BasicConv2d(32, 32, kernel_size=3)
        self.Conv2d_2b_3x3 = BasicConv2d(32, 64, kernel_size=3, padding=1)
        self.Conv2d_3b_1x1 = BasicConv2d(64, 80, kernel_size=1)
        self.Conv2d_4a_3x3 = BasicConv2d(80, 192, kernel_size=3)
        self.Mixed_5b = InceptionA(192, pool_features=32)
        self.Mixed_5c = InceptionA(256, pool_features=64)
        self.Mixed_5d = InceptionA(288, pool_features=64)
        self.Mixed_6a = InceptionB(288)
        self.Mixed_6b = InceptionC(768, channels_7x7=128)
        self.Mixed_6c = InceptionC(768, channels_7x7=160)
        self.Mixed_6d = InceptionC(768, channels_7x7=160)
        self.Mixed_6e = InceptionC(768, channels_7x7=192)
        if aux_logits:
            self.AuxLogits = InceptionAux(768, num_classes)
        self.Mixed_7a = InceptionD(768)
        self.Mixed_7b = InceptionE(1280)
        self.Mixed_7c = InceptionE(2048)
        
        if self.with_deephead_v1:
            self.deephead = Deephead_v1(2048)
        if self.with_deephead_v2:
            self.deephead = Deephead_v2(2048)
        self.fc = nn.Linear(2048, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                import scipy.stats as stats
                stddev = m.stddev if hasattr(m, 'stddev') else 0.1
                X = stats.truncnorm(-2, 2, scale=stddev)
                values = torch.as_tensor(X.rvs(m.weight.numel()), dtype=m.weight.dtype)
                values = values.view(m.weight.size())
                with torch.no_grad():
                    m.weight.copy_(values)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        '''
        if self.transform_input:
            x_ch0 = torch.unsqueeze(x[:, 0], 1) * (0.229 / 0.5) + (0.485 - 0.5) / 0.5
            x_ch1 = torch.unsqueeze(x[:, 1], 1) * (0.224 / 0.5) + (0.456 - 0.5) / 0.5
            x_ch2 = torch.unsqueeze(x[:, 2], 1) * (0.225 / 0.5) + (0.406 - 0.5) / 0.5
            x = torch.cat((x_ch0, x_ch1, x_ch2), 1)
        '''
        if self.with_heatmap:
            #print(x.size())
            x_ch0 = torch.unsqueeze(x[:, 0], 1) / 0.5 - 1
            x_ch1 = torch.unsqueeze(x[:, 1], 1) / 0.5 - 1
            x_ch2 = torch.unsqueeze(x[:, 2], 1) / 0.5 - 1
            x_ch3 = torch.unsqueeze(x[:, 3], 1) / 0.5 - 1
            x_ch4 = torch.unsqueeze(x[:, 4], 1) / 0.5 - 1
            x_ch5 = torch.unsqueeze(x[:, 5], 1) / 0.5 - 1
            x_ch6 = torch.unsqueeze(x[:, 6], 1) / 0.5 - 1
            x = torch.cat((x_ch0, x_ch1, x_ch2,x_ch3,x_ch4,x_ch5,x_ch6), 1) 
        elif self.with_heatmap_v2:

            #x = x[:,0:4]+x[:,0:4]*x[:,4]+x[:,0:4]*x[:,5]+x[:,0:4]*x[:,6]
            #print(x.size())
            x_ch0 = torch.unsqueeze(x[:, 0], 1) / 0.5 - 1
            for i in range(1,15):
                x_ch = torch.unsqueeze(x[:, i], 1) / 0.5 - 1
                if i==1:
                    temp_x = torch.cat((x_ch0,x_ch),1)
                else:
                    temp_x = torch.cat((temp_x,x_ch),1)

            x = temp_x   
        else:
            x_ch0 = torch.unsqueeze(x[:, 0], 1) / 0.5 - 1
            x_ch1 = torch.unsqueeze(x[:, 1], 1) / 0.5 - 1
            x_ch2 = torch.unsqueeze(x[:, 2], 1) / 0.5 - 1
            x = torch.cat((x_ch0, x_ch1, x_ch2), 1)           
        # N x 3 x 299 x 299
        if self.wider or self.bigger_wider:
            x1 = self.Conv2d_1a_3x3a(x)
            x2 = self.Conv2d_1a_3x3b(x)
            x3 = self.Conv2d_1a_3x3c(x)
            x = x1+x2+x3
        elif self.with_heatmap or self.with_heatmap_v2:
            x = self.Conv2d_1a_3x3_with_heatmap(x)
        else:
            x = self.Conv2d_1a_3x3(x)
        # N x 32 x 149 x 149
        x = self.Conv2d_2a_3x3(x)
        # N x 32 x 147 x 147
        x = self.Conv2d_2b_3x3(x)
        # N x 64 x 147 x 147
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 64 x 73 x 73
        x = self.Conv2d_3b_1x1(x)
        # N x 80 x 73 x 73
        x = self.Conv2d_4a_3x3(x)
        # N x 192 x 71 x 71
        x = F.max_pool2d(x, kernel_size=3, stride=2)
        # N x 192 x 35 x 35
        x = self.Mixed_5b(x)
        # N x 256 x 35 x 35
        x = self.Mixed_5c(x)
        # N x 288 x 35 x 35
        x = self.Mixed_5d(x)
        # N x 288 x 35 x 35
        x = self.Mixed_6a(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6b(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6c(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6d(x)
        # N x 768 x 17 x 17
        x = self.Mixed_6e(x)
        # N x 768 x 17 x 17
        if self.training and self.aux_logits:
            aux = self.AuxLogits(x)
        # N x 768 x 17 x 17
        x = self.Mixed_7a(x)
        # N x 1280 x 8 x 8
        x = self.Mixed_7b(x)
        # N x 2048 x 8 x 8
        x = self.Mixed_7c(x)
        # N x 2048 x 8 x 8
        # Adaptive average pooling
        if self.with_deephead_v1 or self.with_deephead_v2:
            x=self.deephead(x)
            #print(x.shape)
        else:
            #print(x.shape)
            x = F.adaptive_avg_pool2d(x, (1, 1))
            # N x 2048 x 1 x 1
        x = F.dropout(x, training=self.training)
        # N x 2048 x 1 x 1
        x = x.view(x.size(0), -1)
        # N x 2048
        x = self.fc(x)
        # N x 1000 (num_classes)
        if self.training and self.aux_logits:
            return _InceptionOuputs(x, aux)
        return x


class InceptionA(nn.Module):

    def __init__(self, in_channels, pool_features):
        super(InceptionA, self).__init__()
        self.branch1x1 = BasicConv2d(in_channels, 64, kernel_size=1)

        self.branch5x5_1 = BasicConv2d(in_channels, 48, kernel_size=1)
        self.branch5x5_2 = BasicConv2d(48, 64, kernel_size=5, padding=2)

        self.branch3x3dbl_1 = BasicConv2d(in_channels, 64, kernel_size=1)
        self.branch3x3dbl_2 = BasicConv2d(64, 96, kernel_size=3, padding=1)
        self.branch3x3dbl_3 = BasicConv2d(96, 96, kernel_size=3, padding=1)

        self.branch_pool = BasicConv2d(in_channels, pool_features, kernel_size=1)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch5x5 = self.branch5x5_1(x)
        branch5x5 = self.branch5x5_2(branch5x5)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch5x5, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionB(nn.Module):

    def __init__(self, in_channels):
        super(InceptionB, self).__init__()
        self.branch3x3 = BasicConv2d(in_channels, 384, kernel_size=3, stride=2)

        self.branch3x3dbl_1 = BasicConv2d(in_channels, 64, kernel_size=1)
        self.branch3x3dbl_2 = BasicConv2d(64, 96, kernel_size=3, padding=1)
        self.branch3x3dbl_3 = BasicConv2d(96, 96, kernel_size=3, stride=2)

    def forward(self, x):
        branch3x3 = self.branch3x3(x)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = self.branch3x3dbl_3(branch3x3dbl)

        branch_pool = F.max_pool2d(x, kernel_size=3, stride=2)

        outputs = [branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionC(nn.Module):

    def __init__(self, in_channels, channels_7x7):
        super(InceptionC, self).__init__()
        self.branch1x1 = BasicConv2d(in_channels, 192, kernel_size=1)

        c7 = channels_7x7
        self.branch7x7_1 = BasicConv2d(in_channels, c7, kernel_size=1)
        self.branch7x7_2 = BasicConv2d(c7, c7, kernel_size=(1, 7), padding=(0, 3))
        self.branch7x7_3 = BasicConv2d(c7, 192, kernel_size=(7, 1), padding=(3, 0))

        self.branch7x7dbl_1 = BasicConv2d(in_channels, c7, kernel_size=1)
        self.branch7x7dbl_2 = BasicConv2d(c7, c7, kernel_size=(7, 1), padding=(3, 0))
        self.branch7x7dbl_3 = BasicConv2d(c7, c7, kernel_size=(1, 7), padding=(0, 3))
        self.branch7x7dbl_4 = BasicConv2d(c7, c7, kernel_size=(7, 1), padding=(3, 0))
        self.branch7x7dbl_5 = BasicConv2d(c7, 192, kernel_size=(1, 7), padding=(0, 3))

        self.branch_pool = BasicConv2d(in_channels, 192, kernel_size=1)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch7x7 = self.branch7x7_1(x)
        branch7x7 = self.branch7x7_2(branch7x7)
        branch7x7 = self.branch7x7_3(branch7x7)

        branch7x7dbl = self.branch7x7dbl_1(x)
        branch7x7dbl = self.branch7x7dbl_2(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_3(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_4(branch7x7dbl)
        branch7x7dbl = self.branch7x7dbl_5(branch7x7dbl)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch7x7, branch7x7dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionD(nn.Module):

    def __init__(self, in_channels):
        super(InceptionD, self).__init__()
        self.branch3x3_1 = BasicConv2d(in_channels, 192, kernel_size=1)
        self.branch3x3_2 = BasicConv2d(192, 320, kernel_size=3, stride=2)

        self.branch7x7x3_1 = BasicConv2d(in_channels, 192, kernel_size=1)
        self.branch7x7x3_2 = BasicConv2d(192, 192, kernel_size=(1, 7), padding=(0, 3))
        self.branch7x7x3_3 = BasicConv2d(192, 192, kernel_size=(7, 1), padding=(3, 0))
        self.branch7x7x3_4 = BasicConv2d(192, 192, kernel_size=3, stride=2)

    def forward(self, x):
        branch3x3 = self.branch3x3_1(x)
        branch3x3 = self.branch3x3_2(branch3x3)

        branch7x7x3 = self.branch7x7x3_1(x)
        branch7x7x3 = self.branch7x7x3_2(branch7x7x3)
        branch7x7x3 = self.branch7x7x3_3(branch7x7x3)
        branch7x7x3 = self.branch7x7x3_4(branch7x7x3)

        branch_pool = F.max_pool2d(x, kernel_size=3, stride=2)
        outputs = [branch3x3, branch7x7x3, branch_pool]
        return torch.cat(outputs, 1)


class InceptionE(nn.Module):

    def __init__(self, in_channels):
        super(InceptionE, self).__init__()
        self.branch1x1 = BasicConv2d(in_channels, 320, kernel_size=1)

        self.branch3x3_1 = BasicConv2d(in_channels, 384, kernel_size=1)
        self.branch3x3_2a = BasicConv2d(384, 384, kernel_size=(1, 3), padding=(0, 1))
        self.branch3x3_2b = BasicConv2d(384, 384, kernel_size=(3, 1), padding=(1, 0))

        self.branch3x3dbl_1 = BasicConv2d(in_channels, 448, kernel_size=1)
        self.branch3x3dbl_2 = BasicConv2d(448, 384, kernel_size=3, padding=1)
        self.branch3x3dbl_3a = BasicConv2d(384, 384, kernel_size=(1, 3), padding=(0, 1))
        self.branch3x3dbl_3b = BasicConv2d(384, 384, kernel_size=(3, 1), padding=(1, 0))

        self.branch_pool = BasicConv2d(in_channels, 192, kernel_size=1)

    def forward(self, x):
        branch1x1 = self.branch1x1(x)

        branch3x3 = self.branch3x3_1(x)
        branch3x3 = [
            self.branch3x3_2a(branch3x3),
            self.branch3x3_2b(branch3x3),
        ]
        branch3x3 = torch.cat(branch3x3, 1)

        branch3x3dbl = self.branch3x3dbl_1(x)
        branch3x3dbl = self.branch3x3dbl_2(branch3x3dbl)
        branch3x3dbl = [
            self.branch3x3dbl_3a(branch3x3dbl),
            self.branch3x3dbl_3b(branch3x3dbl),
        ]
        branch3x3dbl = torch.cat(branch3x3dbl, 1)

        branch_pool = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
        branch_pool = self.branch_pool(branch_pool)

        outputs = [branch1x1, branch3x3, branch3x3dbl, branch_pool]
        return torch.cat(outputs, 1)


class InceptionAux(nn.Module):

    def __init__(self, in_channels, num_classes):
        super(InceptionAux, self).__init__()
        self.conv0 = BasicConv2d(in_channels, 128, kernel_size=1)
        self.conv1 = BasicConv2d(128, 768, kernel_size=5)
        self.conv1.stddev = 0.01
        self.fc = nn.Linear(768, num_classes)
        self.fc.stddev = 0.001

    def forward(self, x):
        # N x 768 x 17 x 17
        x = F.avg_pool2d(x, kernel_size=5, stride=3)
        
        # N x 768 x 5 x 5
        x = self.conv0(x)
        # N x 128 x 5 x 5
        x = self.conv1(x)
        # N x 768 x 1 x 1
        # Adaptive average pooling
        x = F.adaptive_avg_pool2d(x, (1, 1))
        # N x 768 x 1 x 1
        x = x.view(x.size(0), -1)
        # N x 768
        x = self.fc(x)
        # N x 1000
        return x


class BasicConv2d(nn.Module):

    def __init__(self, in_channels, out_channels, **kwargs):
        super(BasicConv2d, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, bias=False, **kwargs)
        self.bn = nn.BatchNorm2d(out_channels, eps=0.001)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return F.relu(x, inplace=True)

class BasicConv2d_wide2(nn.Module):

    def __init__(self, in_channels, out_channels, **kwargs):
        super(BasicConv2d_wide2, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, bias=False, **kwargs)
        self.bn = nn.BatchNorm2d(out_channels, eps=0.001)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return F.relu(x, inplace=True)
class BasicConv2d_wider2(nn.Module):

    def __init__(self, in_channels, out_channels, **kwargs):
        super(BasicConv2d_wider2, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, bias=False, kernel_size=15, stride=5,padding = 7)
        self.conv2 = nn.Conv2d(in_channels, out_channels, bias=False, kernel_size=31, stride=5,padding = 15)
        self.conv3 = nn.Conv2d(in_channels, out_channels, bias=False, kernel_size=61, stride=5,padding = 30)
        self.bn = nn.BatchNorm2d(out_channels, eps=0.001)

    def forward(self, x):
        x1 = self.conv1(x)
        x2 = self.conv2(x)
        x3 = self.conv3(x)
        x = x1+x2+x3
        x = self.bn(x)
        return F.relu(x, inplace=True)

class Deephead_v1(nn.Module):

    def __init__(self, in_channels, **kwargs):
        super(Deephead_v1, self).__init__()
        self.conv1 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #8x8
        self.conv2 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #4x4
        self.conv3 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #2x2
        self.conv4 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        self.conv5 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        return x

class Deephead_v2(nn.Module):

    def __init__(self, in_channels, **kwargs):
        super(Deephead_v2, self).__init__()
        self.conv1 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #8x8
        self.conv2 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #4x4
        self.conv3 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        #2x2
        self.conv4 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        self.conv5 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)
        self.conv6 = BasicConv2d(in_channels,in_channels,kernel_size=3, stride=2,padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        return x