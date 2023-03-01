# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/api/00_drr.ipynb.

# %% ../notebooks/api/00_drr.ipynb 3
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from fastcore.basics import patch

from .siddon import siddon_raycast
from .detector import Detector
from .utils import reshape_subsampled_drr

# %% auto 0
__all__ = ['DRR']

# %% ../notebooks/api/00_drr.ipynb 4
class DRR(nn.Module):
    """Torch module that computes differentiable digitally reconstructed radiographs."""

    def __init__(
        self,
        volume: np.ndarray,  # CT volume
        spacing: np.ndarray,  # Dimensions of voxels in the CT volume
        height: int,  # Height of the rendered DRR
        delx: float,  # X-axis pixel size
        width: int
        | None = None,  # Width of the rendered DRR (if not provided, set to `height`)
        dely: float | None = None,  # Y-axis pixel size (if not provided, set to `delx`)
        p_subsample: float | None = None,  # Proportion of pixels to randomly subsample
        reshape: bool = True,  # Return DRR with shape (b, h, w)
        params: torch.Tensor
        | None = None,  # The parameters of the camera, including SDR, rotations, and translations.
    ):
        super().__init__()

        if params is not None:
            self.sdr = nn.Parameter(params[..., 0:1])
            self.rotations = nn.Parameter(params[..., 1:4])
            self.translations = nn.Parameter(params[..., 4:7])

        # Initialize the X-ray detector
        width = height if width is None else width
        dely = delx if dely is None else dely
        self.detector = Detector(
            height,
            width,
            delx,
            dely,
            n_subsample=int(height * width * p_subsample)
            if p_subsample is not None
            else None,
        )

        # Initialize the volume
        self.register_buffer("spacing", torch.tensor(spacing))
        self.register_buffer("volume", torch.tensor(volume).flip([0]))
        self.reshape = reshape

        # Dummy tensor for device and dtype
        self.register_buffer("dummy", torch.tensor([0.0]))

    def reshape_transform(self, img, batch_size):
        if self.reshape:
            if self.detector.n_subsample is None:
                img = img.view(-1, 1, self.detector.height, self.detector.width)
            else:
                img = reshape_subsampled_drr(img, self.detector, batch_size)
        return img

# %% ../notebooks/api/00_drr.ipynb 5
@patch
def _update_params(self: DRR, params: torch.Tensor):
    state_dict = self.state_dict()
    state_dict["sdr"].copy_(params[..., 0:1])
    state_dict["rotations"].copy_(params[..., 1:4])
    state_dict["translations"].copy_(params[..., 4:7])

# %% ../notebooks/api/00_drr.ipynb 7
@patch
def forward(self: DRR):
    """Forward call if DRR has been initialized with params."""
    if any(param is None for param in [self.sdr, self.rotations, self.translations]):
        raise ValueError("Pose parameters are uninitialized.")
    source, target = self.detector.make_xrays(
        sdr=self.sdr,
        rotations=self.rotations,
        translations=self.translations,
    )
    img = siddon_raycast(source, target, self.volume, self.spacing)
    return self.reshape_transform(img, batch_size=len(self.sdr))

# %% ../notebooks/api/00_drr.ipynb 9
@patch
def project(
    self: DRR,
    sdr: float,
    theta: float,
    phi: float,
    gamma: float,
    bx: float,
    by: float,
    bz: float,
):
    sdr = torch.tensor([[sdr]]).to(self.dummy)
    rotations = torch.tensor([[theta, phi, gamma]]).to(self.dummy)
    translations = torch.tensor([[bx, by, bz]]).to(self.dummy)
    source, target = self.detector.make_xrays(
        sdr=sdr,
        rotations=rotations,
        translations=translations,
    )
    img = siddon_raycast(source, target, self.volume, self.spacing)
    return self.reshape_transform(img, batch_size=len(sdr))
