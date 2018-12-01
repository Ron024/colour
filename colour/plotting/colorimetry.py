# -*- coding: utf-8 -*-
"""
Colorimetry Plotting
====================

Defines the colorimetry plotting objects:

-   :func:`colour.plotting.plot_single_spd`
-   :func:`colour.plotting.plot_multi_spds`
-   :func:`colour.plotting.plot_single_cmfs`
-   :func:`colour.plotting.plot_multi_cmfs`
-   :func:`colour.plotting.plot_single_illuminant_spd`
-   :func:`colour.plotting.plot_multi_illuminant_spds`
-   :func:`colour.plotting.plot_visible_spectrum`
-   :func:`colour.plotting.plot_single_lightness_function`
-   :func:`colour.plotting.plot_multi_lightness_functions`
-   :func:`colour.plotting.plot_single_luminance_function`
-   :func:`colour.plotting.plot_multi_luminance_functions`
-   :func:`colour.plotting.plot_blackbody_spectral_radiance`
-   :func:`colour.plotting.plot_blackbody_colours`

References
----------
-   :cite:`Spiker2015a` : Spiker, N. (2015). Private Discussion with
    Mansencal, T. Retrieved from http://www.invisiblelightimages.com/
"""

from __future__ import division

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from six.moves import reduce

from colour.algebra import LinearInterpolator
from colour.colorimetry import (
    ILLUMINANTS, ILLUMINANTS_SPDS, LIGHTNESS_METHODS, LUMINANCE_METHODS,
    MultiSpectralPowerDistribution, SpectralShape, spd_blackbody, spd_ones,
    spectral_to_XYZ, wavelength_to_XYZ)
from colour.plotting import (
    ColourSwatch, COLOUR_STYLE_CONSTANTS, XYZ_to_plotting_colourspace, artist,
    filter_passthrough, filter_cmfs, filter_illuminants, override_style,
    render, single_colour_swatch_plot, multi_function_plot)
from colour.utilities import (domain_range_scale, first_item,
                              normalise_maximum, suppress_warnings, tstack)

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013-2018 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = [
    'plot_single_spd', 'plot_multi_spds', 'plot_single_cmfs',
    'plot_multi_cmfs', 'plot_single_illuminant_spd',
    'plot_multi_illuminant_spds', 'plot_visible_spectrum',
    'plot_single_lightness_function', 'plot_multi_lightness_functions',
    'plot_single_luminance_function', 'plot_multi_luminance_functions',
    'plot_blackbody_spectral_radiance', 'plot_blackbody_colours'
]


@override_style()
def plot_single_spd(spd,
                    cmfs='CIE 1931 2 Degree Standard Observer',
                    out_of_gamut_clipping=True,
                    **kwargs):
    """
    Plots given spectral power distribution.

    Parameters
    ----------
    spd : SpectralPowerDistribution
        Spectral power distribution to plot.
    out_of_gamut_clipping : bool, optional
        Whether to clip out of gamut colours otherwise, the colours will be
        offset by the absolute minimal colour leading to a rendering on
        gray background, less saturated and smoother.
    cmfs : unicode
        Standard observer colour matching functions used for spectrum creation.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    References
    ----------
    :cite:`Spiker2015a`

    Examples
    --------
    >>> from colour import SpectralPowerDistribution
    >>> data = {
    ...     500: 0.0651,
    ...     520: 0.0705,
    ...     540: 0.0772,
    ...     560: 0.0870,
    ...     580: 0.1128,
    ...     600: 0.1360
    ... }
    >>> spd = SpectralPowerDistribution(data, name='Custom')
    >>> plot_single_spd(spd)  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Single_SPD.png
        :align: center
        :alt: plot_single_spd
    """

    figure, axes = artist(**kwargs)

    cmfs = first_item(filter_cmfs(cmfs).values())

    spd = spd.copy()
    spd.interpolator = LinearInterpolator
    wavelengths = cmfs.wavelengths[np.logical_and(
        cmfs.wavelengths >= max(min(cmfs.wavelengths), min(spd.wavelengths)),
        cmfs.wavelengths <= min(max(cmfs.wavelengths), max(spd.wavelengths)),
    )]
    values = spd[wavelengths]

    colours = XYZ_to_plotting_colourspace(
        wavelength_to_XYZ(wavelengths, cmfs),
        ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['E'],
        apply_encoding_cctf=False)

    if not out_of_gamut_clipping:
        colours += np.abs(np.min(colours))

    colours = COLOUR_STYLE_CONSTANTS.colour.colourspace.encoding_cctf(
        normalise_maximum(colours))

    x_min, x_max = min(wavelengths), max(wavelengths)
    y_min, y_max = 0, max(values) + max(values) * 0.05

    polygon = Polygon(
        np.vstack([
            (x_min, 0),
            tstack([wavelengths, values]),
            (x_max, 0),
        ]),
        facecolor='none',
        edgecolor='none')
    axes.add_patch(polygon)

    padding = 0.1
    axes.bar(
        x=wavelengths - padding,
        height=max(values),
        width=1 + padding,
        color=colours,
        align='edge',
        clip_path=polygon)

    axes.plot(wavelengths, values, color=COLOUR_STYLE_CONSTANTS.colour.dark)

    settings = {
        'axes': axes,
        'bounding_box': (x_min, x_max, y_min, y_max),
        'title': '{0} - {1}'.format(spd.strict_name, cmfs.strict_name),
        'x_label': 'Wavelength $\\lambda$ (nm)',
        'y_label': 'Spectral Power Distribution',
    }
    settings.update(kwargs)

    return render(**settings)


@override_style()
def plot_multi_spds(spds,
                    cmfs='CIE 1931 2 Degree Standard Observer',
                    use_spds_colours=False,
                    normalise_spds_colours=False,
                    **kwargs):
    """
    Plots given spectral power distributions.

    Parameters
    ----------
    spds : array_like or MultiSpectralPowerDistribution
        Spectral power distributions or multi-spectral power distributions to
        plot. `spds` can be a single
        :class:`colour.MultiSpectralPowerDistribution` class instance, a list
        of :class:`colour.MultiSpectralPowerDistribution` class instances or a
        list of :class:`colour.SpectralPowerDistribution` class instances.
    cmfs : unicode, optional
        Standard observer colour matching functions used for spectrum creation.
    use_spds_colours : bool, optional
        Whether to use spectral power distributions colours.
    normalise_spds_colours : bool
        Whether to normalise spectral power distributions colours.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> from colour import SpectralPowerDistribution
    >>> data_1 = {
    ...     500: 0.004900,
    ...     510: 0.009300,
    ...     520: 0.063270,
    ...     530: 0.165500,
    ...     540: 0.290400,
    ...     550: 0.433450,
    ...     560: 0.594500
    ... }
    >>> data_2 = {
    ...     500: 0.323000,
    ...     510: 0.503000,
    ...     520: 0.710000,
    ...     530: 0.862000,
    ...     540: 0.954000,
    ...     550: 0.994950,
    ...     560: 0.995000
    ... }
    >>> spd1 = SpectralPowerDistribution(data_1, name='Custom 1')
    >>> spd2 = SpectralPowerDistribution(data_2, name='Custom 2')
    >>> plot_multi_spds([spd1, spd2])  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Multi_SPDs.png
        :align: center
        :alt: plot_multi_spds
    """

    figure, axes = artist(**kwargs)

    if isinstance(spds, MultiSpectralPowerDistribution):
        spds = spds.to_spds()
    else:
        spds = list(spds)
        for i, spd in enumerate(spds[:]):
            if isinstance(spd, MultiSpectralPowerDistribution):
                spds.remove(spd)
                spds[i:i] = spd.to_spds()

    cmfs = first_item(filter_cmfs(cmfs).values())

    illuminant = ILLUMINANTS_SPDS[
        COLOUR_STYLE_CONSTANTS.colour.colourspace.illuminant]

    x_limit_min, x_limit_max, y_limit_min, y_limit_max = [], [], [], []
    for spd in spds:
        wavelengths, values = spd.wavelengths, spd.values

        shape = spd.shape
        x_limit_min.append(shape.start)
        x_limit_max.append(shape.end)
        y_limit_min.append(min(values))
        y_limit_max.append(max(values))

        if use_spds_colours:
            with domain_range_scale('1'):
                XYZ = spectral_to_XYZ(spd, cmfs, illuminant)

            if normalise_spds_colours:
                XYZ = normalise_maximum(XYZ, clip=False)

            RGB = np.clip(XYZ_to_plotting_colourspace(XYZ), 0, 1)

            axes.plot(wavelengths, values, color=RGB, label=spd.strict_name)
        else:
            axes.plot(wavelengths, values, label=spd.strict_name)

    bounding_box = (min(x_limit_min), max(x_limit_max), min(y_limit_min),
                    max(y_limit_max) + max(y_limit_max) * 0.05)
    settings = {
        'axes': axes,
        'bounding_box': bounding_box,
        'legend': True,
        'x_label': 'Wavelength $\\lambda$ (nm)',
        'y_label': 'Spectral Power Distribution',
    }
    settings.update(kwargs)

    return render(**settings)


@override_style()
def plot_single_cmfs(cmfs='CIE 1931 2 Degree Standard Observer', **kwargs):
    """
    Plots given colour matching functions.

    Parameters
    ----------
    cmfs : unicode, optional
        Colour matching functions to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_single_cmfs('CIE 1931 2 Degree Standard Observer')
    ... # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Single_CMFS.png
        :align: center
        :alt: plot_single_cmfs
    """

    cmfs = first_item(filter_cmfs(cmfs).values())
    settings = {
        'title': '{0} - Colour Matching Functions'.format(cmfs.strict_name)
    }
    settings.update(kwargs)

    return plot_multi_cmfs((cmfs.name, ), **settings)


@override_style()
def plot_multi_cmfs(cmfs=None, **kwargs):
    """
    Plots given colour matching functions.

    Parameters
    ----------
    cmfs : array_like, optional
        Colour matching functions to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> cmfs = ('CIE 1931 2 Degree Standard Observer',
    ...         'CIE 1964 10 Degree Standard Observer')
    >>> plot_multi_cmfs(cmfs)  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Multi_CMFS.png
        :align: center
        :alt: plot_multi_cmfs
    """

    if cmfs is None:
        cmfs = ('CIE 1931 2 Degree Standard Observer',
                'CIE 1964 10 Degree Standard Observer')

    cmfs = filter_cmfs(cmfs).values()

    figure, axes = artist(**kwargs)

    axes.axhline(color=COLOUR_STYLE_CONSTANTS.colour.dark, linestyle='--')

    x_limit_min, x_limit_max, y_limit_min, y_limit_max = [], [], [], []
    for i, cmfs_i in enumerate(cmfs):
        for j, RGB in enumerate([(1, 0, 0), (0, 1, 0), (0, 0, 1)]):
            RGB = [reduce(lambda y, _: y * 0.5, range(i), x) for x in RGB]
            values = cmfs_i.values[:, j]

            shape = cmfs_i.shape
            x_limit_min.append(shape.start)
            x_limit_max.append(shape.end)
            y_limit_min.append(min(values))
            y_limit_max.append(max(values))

            axes.plot(
                cmfs_i.wavelengths,
                values,
                color=RGB,
                label='{0} - {1}'.format(cmfs_i.strict_labels[j],
                                         cmfs_i.strict_name))

    bounding_box = (min(x_limit_min), max(x_limit_max),
                    min(y_limit_min) - abs(min(y_limit_min)) * 0.05,
                    max(y_limit_max) + abs(max(y_limit_max)) * 0.05)
    title = '{0} - Colour Matching Functions'.format(', '.join(
        [cmfs_i.strict_name for cmfs_i in cmfs]))

    settings = {
        'axes': axes,
        'bounding_box': bounding_box,
        'legend': True,
        'title': title,
        'x_label': 'Wavelength $\\lambda$ (nm)',
        'y_label': 'Tristimulus Values',
    }
    settings.update(kwargs)

    return render(**settings)


@override_style()
def plot_single_illuminant_spd(illuminant='A',
                               cmfs='CIE 1931 2 Degree Standard Observer',
                               **kwargs):
    """
    Plots given single illuminant spectral power distribution.

    Parameters
    ----------
    illuminant : unicode, optional
        Factory illuminant to plot.
    cmfs : unicode, optional
        Standard observer colour matching functions to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.
    out_of_gamut_clipping : bool, optional
        {:func:`colour.plotting.plot_single_spd`},
        Whether to clip out of gamut colours otherwise, the colours will be
        offset by the absolute minimal colour leading to a rendering on
        gray background, less saturated and smoother.

    Returns
    -------
    tuple
        Current figure and axes.

    References
    ----------
    :cite:`Spiker2015a`

    Examples
    --------
    >>> plot_single_illuminant_spd('A')  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Single_Illuminant_SPD.png
        :align: center
        :alt: plot_single_illuminant_spd
    """

    cmfs = first_item(filter_cmfs(cmfs).values())
    title = 'Illuminant {0} - {1}'.format(illuminant, cmfs.strict_name)

    illuminant = first_item(filter_illuminants(illuminant).values())

    settings = {'title': title, 'y_label': 'Relative Power'}
    settings.update(kwargs)

    return plot_single_spd(illuminant, **settings)


@override_style()
def plot_multi_illuminant_spds(illuminants=None, **kwargs):
    """
    Plots given illuminants spectral power distributions.

    Parameters
    ----------
    illuminants : array_like, optional
        Factory illuminants to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.
    use_spds_colours : bool, optional
        {:func:`colour.plotting.plot_multi_spds`}
        Whether to use spectral power distributions colours.
    normalise_spds_colours : bool
        {:func:`colour.plotting.plot_multi_spds`}
        Whether to normalise spectral power distributions colours.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_multi_illuminant_spds(['A', 'B', 'C'])  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Multi_Illuminant_SPDs.png
        :align: center
        :alt: plot_multi_illuminant_spds
    """

    if illuminants is None:
        illuminants = ('A', 'B', 'C')

    illuminants = filter_illuminants(illuminants).values()

    title = '{0} - Illuminants Spectral Power Distributions'.format(
        ', '.join([illuminant.strict_name for illuminant in illuminants]))

    settings = {'title': title, 'y_label': 'Relative Power'}
    settings.update(kwargs)

    return plot_multi_spds(illuminants, **settings)


@override_style(**{
    'ytick.left': False,
    'ytick.labelleft': False,
})
def plot_visible_spectrum(cmfs='CIE 1931 2 Degree Standard Observer',
                          out_of_gamut_clipping=True,
                          **kwargs):
    """
    Plots the visible colours spectrum using given standard observer *CIE XYZ*
    colour matching functions.

    Parameters
    ----------
    cmfs : unicode, optional
        Standard observer colour matching functions used for spectrum creation.
    out_of_gamut_clipping : bool, optional
        Whether to clip out of gamut colours otherwise, the colours will be
        offset by the absolute minimal colour leading to a rendering on
        gray background, less saturated and smoother.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    References
    ----------
    :cite:`Spiker2015a`

    Examples
    --------
    >>> plot_visible_spectrum()  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Visible_Spectrum.png
        :align: center
        :alt: plot_visible_spectrum
    """

    cmfs = first_item(filter_cmfs(cmfs).values())

    bounding_box = (min(cmfs.wavelengths), max(cmfs.wavelengths), 0, 1)

    settings = {'bounding_box': bounding_box, 'y_label': None}
    settings.update(kwargs)
    settings['standalone'] = False

    figure, axes = plot_single_spd(
        spd_ones(cmfs.shape),
        cmfs=cmfs,
        out_of_gamut_clipping=out_of_gamut_clipping,
        **settings)

    # Removing wavelength line as it doubles with the axes spine.
    axes.lines.pop(0)

    settings = {
        'axes': axes,
        'standalone': True,
        'title': 'The Visible Spectrum - {0}'.format(cmfs.strict_name),
        'x_label': 'Wavelength $\\lambda$ (nm)',
    }
    settings.update(kwargs)

    return render(**settings)


@override_style()
def plot_single_lightness_function(function='CIE 1976', **kwargs):
    """
    Plots given *Lightness* function.

    Parameters
    ----------
    function : unicode, optional
        *Lightness* function to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_single_lightness_function('CIE 1976')  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Single_Lightness_Function.png
        :align: center
        :alt: plot_single_lightness_function
    """

    settings = {'title': '{0} - Lightness Function'.format(function)}
    settings.update(kwargs)

    return plot_multi_lightness_functions((function, ), **settings)


@override_style()
def plot_multi_lightness_functions(functions=None, **kwargs):
    """
    Plots given *Lightness* functions.

    Parameters
    ----------
    functions : array_like, optional
        *Lightness* functions to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_multi_lightness_functions(['CIE 1976', 'Wyszecki 1963'])
    ... # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Multi_Lightness_Functions.png
        :align: center
        :alt: plot_multi_lightness_functions
    """

    if functions is None:
        functions = ('CIE 1976', 'Wyszecki 1963')

    functions = filter_passthrough(LIGHTNESS_METHODS, functions)

    settings = {
        'bounding_box': (0, 1, 0, 1),
        'legend': True,
        'title': '{0} - Lightness Functions'.format(', '.join(functions)),
        'x_label': 'Normalised Relative Luminance Y',
        'y_label': 'Normalised Lightness',
    }
    settings.update(kwargs)

    with domain_range_scale(1):
        return multi_function_plot(functions, **settings)


@override_style()
def plot_single_luminance_function(function='CIE 1976', **kwargs):
    """
    Plots given *Luminance* function.

    Parameters
    ----------
    function : unicode, optional
        *Luminance* function to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_single_luminance_function('CIE 1976')  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Single_Luminance_Function.png
        :align: center
        :alt: plot_single_luminance_function
    """

    settings = {'title': '{0} - Luminance Function'.format(function)}
    settings.update(kwargs)

    return plot_multi_luminance_functions((function, ), **settings)


@override_style()
def plot_multi_luminance_functions(functions=None, **kwargs):
    """
    Plots given *Luminance* functions.

    Parameters
    ----------
    functions : array_like, optional
        *Luminance* functions to plot.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_multi_luminance_functions(['CIE 1976', 'Newhall 1943'])
    ... # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Multi_Luminance_Functions.png
        :align: center
        :alt: plot_multi_luminance_functions
    """

    if functions is None:
        functions = ('CIE 1976', 'Newhall 1943')

    functions = filter_passthrough(LUMINANCE_METHODS, functions)

    settings = {
        'bounding_box': (0, 1, 0, 1),
        'legend': True,
        'title': '{0} - Luminance Functions'.format(', '.join(functions)),
        'x_label': 'Normalised Munsell Value / Lightness',
        'y_label': 'Normalised Relative Luminance Y',
    }
    settings.update(kwargs)

    with domain_range_scale(1):
        return multi_function_plot(functions, **settings)


@override_style()
def plot_blackbody_spectral_radiance(
        temperature=3500,
        cmfs='CIE 1931 2 Degree Standard Observer',
        blackbody='VY Canis Major',
        **kwargs):
    """
    Plots given blackbody spectral radiance.

    Parameters
    ----------
    temperature : numeric, optional
        Blackbody temperature.
    cmfs : unicode, optional
        Standard observer colour matching functions.
    blackbody : unicode, optional
        Blackbody name.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_blackbody_spectral_radiance(3500, blackbody='VY Canis Major')
    ... # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Blackbody_Spectral_Radiance.png
        :align: center
        :alt: plot_blackbody_spectral_radiance
    """

    figure = plt.figure()

    figure.subplots_adjust(hspace=COLOUR_STYLE_CONSTANTS.geometry.short / 2)

    cmfs = first_item(filter_cmfs(cmfs).values())

    spd = spd_blackbody(temperature, cmfs.shape)

    axes = figure.add_subplot(211)
    settings = {
        'axes': axes,
        'title': '{0} - Spectral Radiance'.format(blackbody),
        'y_label': 'W / (sr m$^2$) / m',
    }
    settings.update(kwargs)
    settings['standalone'] = False

    plot_single_spd(spd, cmfs.name, **settings)

    axes = figure.add_subplot(212)

    with domain_range_scale('1'):
        XYZ = spectral_to_XYZ(spd, cmfs)

    RGB = normalise_maximum(XYZ_to_plotting_colourspace(XYZ))

    settings = {
        'axes': axes,
        'aspect': None,
        'title': '{0} - Colour'.format(blackbody),
        'x_label': '{0}K'.format(temperature),
        'y_label': '',
    }
    settings.update(kwargs)
    settings['standalone'] = False

    figure, axes = single_colour_swatch_plot(
        ColourSwatch(name='', RGB=RGB), **settings)

    # Removing "x" and "y" ticks.
    axes.set_xticks([])
    axes.set_yticks([])

    settings = {'axes': axes, 'standalone': True}
    settings.update(kwargs)

    return render(**settings)


@override_style(**{
    'ytick.left': False,
    'ytick.labelleft': False,
})
def plot_blackbody_colours(
        shape=SpectralShape(150, 12500, 50),
        cmfs='CIE 1931 2 Degree Standard Observer',
        **kwargs):
    """
    Plots blackbody colours.

    Parameters
    ----------
    shape : SpectralShape, optional
        Spectral shape to use as plot boundaries.
    cmfs : unicode, optional
        Standard observer colour matching functions.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        {:func:`colour.plotting.artist`, :func:`colour.plotting.render`},
        Please refer to the documentation of the previously listed definitions.

    Returns
    -------
    tuple
        Current figure and axes.

    Examples
    --------
    >>> plot_blackbody_colours(SpectralShape(150, 12500, 50))  # doctest: +SKIP

    .. image:: ../_static/Plotting_Plot_Blackbody_Colours.png
        :align: center
        :alt: plot_blackbody_colours
    """

    figure, axes = artist(**kwargs)

    cmfs = first_item(filter_cmfs(cmfs).values())

    colours = []
    temperatures = []

    with suppress_warnings():
        for temperature in shape:
            spd = spd_blackbody(temperature, cmfs.shape)

            with domain_range_scale('1'):
                XYZ = spectral_to_XYZ(spd, cmfs)

            RGB = normalise_maximum(XYZ_to_plotting_colourspace(XYZ))

            colours.append(RGB)
            temperatures.append(temperature)

    x_min, x_max = min(temperatures), max(temperatures)
    y_min, y_max = 0, 1

    padding = 0.1
    axes.bar(
        x=np.array(temperatures) - padding,
        height=1,
        width=shape.interval + (padding * shape.interval),
        color=colours,
        align='edge')

    settings = {
        'axes': axes,
        'bounding_box': (x_min, x_max, y_min, y_max),
        'title': 'Blackbody Colours',
        'x_label': 'Temperature K',
        'y_label': None,
    }
    settings.update(kwargs)

    return render(**settings)
