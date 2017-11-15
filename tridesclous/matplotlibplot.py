import numpy as np
import matplotlib.pyplot as plt

from .tools import median_mad
from .dataio import DataIO
from .catalogueconstructor import CatalogueConstructor


    
    
def plot_probe_geometry(dataio, chan_grp=0):
    channel_group = dataio.channel_groups[chan_grp]
    channels = channel_group['channels']
    geometry = channel_group['geometry']
    
    fig, ax = plt.subplots()
    for chan in channels:
        x, y = geometry[chan]
        ax.plot([x], [y], marker='o', color='w')
        ax.text(x, y, str(chan))
    
    return fig

    
def plot_signals(dataio_or_cataloguecconstructor, chan_grp=0, seg_num=0, time_slice=(0., 5.), 
            signal_type='initial', with_span=False, with_peaks=False):
    
    if isinstance(dataio_or_cataloguecconstructor, CatalogueConstructor):
        cataloguecconstructor = dataio_or_cataloguecconstructor
        dataio = cataloguecconstructor.dataio
        chan_grp = cataloguecconstructor.chan_grp
    elif isinstance(dataio_or_cataloguecconstructor, DataIO):
        cataloguecconstructor = None
        dataio = dataio_or_cataloguecconstructor
        
    channel_group = dataio.channel_groups[chan_grp]
    channels = channel_group['channels']
    
    i_start = int(time_slice[0]*dataio.sample_rate)
    i_stop = int(time_slice[1]*dataio.sample_rate)
    
    raw_sigs = dataio.get_signals_chunk(seg_num=seg_num, chan_grp=chan_grp,
                i_start=i_start, i_stop=i_stop,
                signal_type=signal_type, return_type='raw_numpy')
    
    if signal_type=='initial':
        med, mad = median_mad(raw_sigs)
        sigs = (raw_sigs-med)/mad
        ratioY = 0.3
    elif signal_type=='processed':
        sigs = raw_sigs.copy()
        ratioY = 0.05

    #spread signals
    sigs *= ratioY
    sigs += np.arange(0, len(channels))[np.newaxis, :]
    
    
    
    times = np.arange(sigs.shape[0])/dataio.sample_rate
    fig, ax = plt.subplots()
    ax.plot(times, sigs)
    
    if with_peaks or with_span:
        assert cataloguecconstructor is not None
        peaks = cataloguecconstructor.all_peaks
        
        keep = (peaks['segment']==seg_num) & (peaks['index']>=i_start) & (peaks['index']<i_stop)
        peak_indexes = peaks[keep]['index'].copy()
        peak_indexes -= i_start
        
        if with_peaks:
            for i in range(len(channels)):
                ax.plot(times[peak_indexes], sigs[peak_indexes, i], ls='None', marker='o', color='k')
        
        if with_span:
            d = cataloguecconstructor.info['params_peakdetector']
            s = d['peak_span']
            for ind in peak_indexes:
                ax.axvspan(times[ind]-s, times[ind]+s, color='b', alpha = .3)
    
    ax.set_yticks([])
    
    return fig



def plot_waveforms_with_geometry(waveforms, channels, geometry,
            ax=None, ratioY=1, deltaX= 50, margin=150, color='k'):
    """
    
    
    """
    if ax is None:
        fig, ax = plt.subplots()
    

    wf = waveforms.copy()
    if wf.ndim ==2:
        wf = wf[None, : ,:]
    
    width = wf.shape[1]
    
    
    vect =np.zeros(wf.shape[1]*wf.shape[2])
    
    wf *= ratioY
    for i, chan in enumerate(channels):
        x, y = geometry[chan]
        vect[i*width:(i+1)*width] = np.linspace(x-deltaX, x+deltaX, num=width)
        wf[:, :, i] += y
    
    wf[:, 0,:] = np.nan
    wf = wf.swapaxes(1,2).reshape(wf.shape[0], -1).T
    
    ax.plot(vect, wf, color=color, lw=1, alpha=.3)

    for i, chan in enumerate(channels):
        x, y = geometry[i, :]
        #~ ax.plot([x], [y], marker='o', color='w')
        ax.text(x, y, str(chan), color='r')
    
    ax.set_xlim(np.min(geometry[:, 0])-margin, np.max(geometry[:, 0])+margin)
    ax.set_ylim(np.min(geometry[:, 1])-margin, np.max(geometry[:, 1])+margin)
    
    return ax



def plot_waveforms(cataloguecconstructor, labels=None, nb_max=50):
    cc = cataloguecconstructor
    channels = cc.dataio.channel_groups[cc.chan_grp]['channels']
    geometry = cc.dataio.get_geometry(chan_grp=cc.chan_grp)
    all_wfs = cc.some_waveforms
    
    
    
    fig, ax = plt.subplots()
    if labels is None:
        wfs = all_wfs[:nb_max,:, :]
        plot_waveforms_with_geometry(wfs, channels, geometry, ax=ax, ratioY=10, color='k')
    else:
        if not hasattr(cc, 'colors'):
            cc.refresh_colors()
        
        if isinstance(labels, int):
            labels = [labels]
        for label in labels:
            peaks = cc.all_peaks[cc.some_peaks_index]
            keep = peaks['label'] == label
            wfs = all_wfs[keep][:nb_max]
            color = cc.colors.get(label, 'k')
            plot_waveforms_with_geometry(wfs, channels, geometry, ax=ax, ratioY=10, color=color)


def plot_features_scatter_2d(cataloguecconstructor, labels=None, nb_max=500):
    cc = cataloguecconstructor
    
    all_feat = cc.some_features
    n = all_feat.shape[1]
    
    fig, axs = plt.subplots(nrows=n, ncols=n)
    
    l = []
    if labels is None:
        l.append( (cc.some_features[:nb_max], 'k') )
    else:
        if not hasattr(cc, 'colors'):
            cc.refresh_colors()
        
        if isinstance(labels, int):
            labels = [labels]
        for label in labels:
            peaks = cc.all_peaks[cc.some_peaks_index]
            keep = peaks['label'] == label
            feat = cc.some_features[keep][:nb_max]
            color = cc.colors.get(label, 'k')
            l.append((feat, color))
    
    for c in range(n):
        for r in range(n):
            ax = axs[r, c]
            
            if c==r:
                for feat, color in l:
                    y, x = np.histogram(feat[:, r], bins=100)
                    ax.plot(x[:-1], y, color=color)
            elif c<r:
                for feat, color in l:
                    ax.plot(feat[:, r], feat[:, c], color=color, markersize=2, ls='None', marker='o')
            else:
                fig.delaxes(ax)
    
    
