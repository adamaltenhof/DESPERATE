# DEnoising SPEctRA in pyThon with wavElets (DESPERATE)

DESPERATE is a Python library for processing and denoising NMR spectra


## Requirements
- All testing has been done with Python 3.10 and newer
- NumPy
- SciPy
- matplotlib
- PyWavelets
- nmrglue (mainly optional)

## Installation
- pip #

## Features
- wavelet_denoise.py contains all wavelet denoising functions; wavelet_denoise and wavelet_denoise2 are for 1D and 2D spectra, respectively
- functions.py contains some processing functions for Topspin data including loading FID's or SER's, FFT, window functions, phasing, automatic phasing, a manual phasing widget, Cadzow denoising, and PCA denoising
- simpson.py contains some processing functions for simulated data that are in this distribution
- example 1D and 2D simulated and experimental datasets and processing scripts are included

## Citing
If you use DESPERATE please cite the following:
A.R. Altenhof, H. E. Mason, and R.W. Schurko, 2022. DESPERATE: A Python Library for Processing and Denoising NMR Spectra. J. Magn. Reson. 346, 107320 DOI:10.1016/j.jmr.2022.107320

## Creators
- Harris Mason
- Adam Altenhof

## Contact
Please contact rschurko@fsu.edu with any quesitons, feedback, or suggestions.

## Support
This software was supported (in part) by the National Science Foundation Chemical Measurement and Imaging Program, with partial co-funding from the Solid State and Materials Chemistry Program (NSF-2003854).

## License
MIT

[//]: # ()
