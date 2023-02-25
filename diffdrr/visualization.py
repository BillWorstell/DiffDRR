# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/api/05_visualization.ipynb.

# %% auto 0
__all__ = ['plot_drr', 'animate']

# %% ../notebooks/api/05_visualization.ipynb 3
import tempfile

import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

# %% ../notebooks/api/05_visualization.ipynb 4
def plot_drr(drr, title=None, ticks=True, axs=None):
    """
    Plot an DRR output by the projector module.
    Inputs
    ------
    drr : torch.Tensor
        DRR image in torch tensor with shape (batch, channel, height, width)
    title : str, optional
        Title for the plot
    ticks : Bool
        Toggle ticks and ticklabels.
    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure with plotted image
    axs : matplotlib.axes._subplots.AxesSubplot
        Axis with plotted image
    """
    if axs is None:
        fig, axs = plt.subplots(ncols=len(drr), figsize=(10, 5))
    if len(drr) == 1:
        axs = [axs]
    for img, ax in zip(drr, axs):
        ax.imshow(img.squeeze().cpu().detach(), cmap="gray")
        _, nx, ny = img.shape
        ax.xaxis.tick_top()
        ax.set(
            title=title,
            xticks=[0, nx - 1],
            xticklabels=[1, nx],
            yticks=[0, ny - 1],
            yticklabels=[1, ny],
        )
        if ticks is False:
            ax.set_xticks([])
            ax.set_yticks([])
    return axs

# %% ../notebooks/api/05_visualization.ipynb 5
def animate(out, df, sdr, drr, ground_truth=None, verbose=True, **kwargs):
    """Animate the optimization of a DRR."""
    # Make the axes
    if ground_truth is None:

        def make_fig():
            fig, ax_opt = plt.subplots(
                figsize=(3, 3),
                constrained_layout=True,
            )
            return fig, ax_opt

    else:

        def make_fig(ground_truth):
            fig, (ax_fix, ax_opt) = plt.subplots(
                ncols=2,
                figsize=(6, 3),
                constrained_layout=True,
            )
            plot_drr(ground_truth, axs=ax_fix)
            ax_fix.set(xlabel="Fixed DRR")
            return fig, ax_opt

    # Compute DRRs, plot, and save to temporary folder
    if verbose:
        itr = tqdm(df.iterrows(), desc="Precomputing DRRs", total=len(df))
    else:
        itr = df.iterrows()

    with tempfile.TemporaryDirectory() as tmpdir:
        idxs = []
        for idx, row in itr:
            fig, ax_opt = make_fig() if ground_truth is None else make_fig(ground_truth)
            params = row[["theta", "phi", "gamma", "bx", "by", "bz"]].values
            itr = drr(sdr, *params)
            _ = plot_drr(itr, axs=ax_opt)
            ax_opt.set(xlabel="Moving DRR")
            fig.savefig(f"{tmpdir}/{idx}.png")
            plt.close(fig)
            idxs.append(idx)
        frames = np.stack(
            [iio.imread(f"{tmpdir}/{idx}.png") for idx in idxs],
            axis=0,
        )

    # Make the animation
    return iio.imwrite(out, frames, **kwargs)