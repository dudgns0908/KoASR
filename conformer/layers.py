import numpy as np
import torch
from torch import nn, Tensor
import torch.nn.functional as F


class ScaledDotProductAttention(nn.Module):
    """ Scaled Dot-Product Attention """

    def __init__(self, dim: int = 8):
        super().__init__()
        self.dim = np.sqrt(dim)

    def forward(self, query: Tensor, key: Tensor, value: Tensor) -> Tensor:
        scaled_matmul = torch.bmm(query, torch.transpose(key, 1, 2)) / self.dim
        softmax = F.softmax(scaled_matmul)
        attention = torch.bmm(softmax, value)

        return attention


class MultiHeadAttention(nn.Module):
    """ Multi-Head Attention """

    def __init__(
            self,
            dim: int = 512,
            num_heads: int = 8,
            dropout_p: float = 0.1,
    ):
        super().__init__()

        self.num_heads = num_heads
        self.dk = dim // num_heads

        self.query_projection = nn.Linear(dim, dim * self.dk)
        self.key_projection = nn.Linear(dim, dim * self.dk)
        self.value_projection = nn.Linear(dim, dim * self.dk)
        self.scaled_dot_product_attention = ScaledDotProductAttention(self.dk)

    def forward(self, query: Tensor, key: Tensor, value: Tensor) -> Tensor:
        batch_size = query.shape[0]

        query_output = self.query_projection(query).view(batch_size, self.num_heads, self.dk)
        key_output = self.key_projection(key).view(batch_size, self.num_heads, self.dk)
        value_output = self.value_projection(value).view(batch_size, self.num_heads, self.dk)

        attention_output = self.scaled_dot_product_attention(query_output, key_output, value_output)
        # return attention_output


class PositionalEmbedding(nn.Module):
    """ Relative Positional Embedding """

    def __init__(
            self,
            d_model: int,
            max_len: int = 5000,
    ) -> None:
        super().__init__()

        pe = torch.zeros(max_len, d_model, requires_grad=False)
        pos = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * -(np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div_term)
        pe[:, 1::2] = torch.cos(pos * div_term)
        pe = self.pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, length: int) -> Tensor:
        return self.pe[:, :length]


class PointwiseConv1d(nn.Module):
    def __init__(
            self,
            in_channels: int,
            out_channels: int,
            stride: int = 1,
            padding: int = 0,
            dilation: int = 1,
            bias: bool = True,
            device: torch.device = 'cpu'
    ):
        super().__init__()
        self.device = device
        self.pointwise = nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride, padding=padding,
                                   dilation=dilation, groups=in_channels, bias=bias)

    def forward(self, inputs: Tensor) -> Tensor:
        return self.pointwise(inputs.to(self.device))


class DepthwiseConv1d(nn.Module):
    def __init__(
            self,
            in_channels: int,
            out_channels: int,
            kernel_size: int = 10,
            stride: int = 1,
            padding: int = 0,
            dilation: int = 1,
            bias: bool = True,
    ):
        super().__init__()
        self.depthwise = nn.Conv1d(in_channels, out_channels, kernel_size, stride=stride, padding=padding,
                                   dilation=dilation, groups=in_channels, bias=bias)

    def forward(self, x):
        return self.depthwise(x)


class Transpose(nn.Module):
    def __init__(
            self,
            dim0: int = 0,
            dim1: int = 1,
    ):
        super().__init__()
        self.dim0 = dim0
        self.dim1 = dim1

    def forward(self, inputs: Tensor) -> Tensor:
        return inputs.transpose(self.dim0, self.dim1)
