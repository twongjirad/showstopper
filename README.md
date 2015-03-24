# showstopper

## dependencies

* numpy_root: converts tree into numpy array
* numpy
* pandas: sponging 
* pyqtgraph: plotting
* pyroot: plotting

## Contents

* analyze_crosstalk.py: select pickup channels, dump out statistics based on electronics groupings
* fft_spunge.py: main data analyzer
* wire_plot_fft.py: plots amplitude ratio data or FFT RGB score for each wire. Uses VireViewer
* fft_run83_subrun00_00_expanded_search.ipynb: notebook allowing one to visualize waveforms and power spectra for each wire. Used to study selection cut.
* update_data.sh: get data processed by Kazu


## flow [deprecated]

* get pulse data file from Kazu
* sponge_data.py 
  - makes a table of crate, slot, femch, max(amp), badch, pulsed (amp>700)
  - outputs output/runXXX.npyz, stores table as numpy array
* analyze_data.py
  - takes in all data produced by sponge_data.py and makes a 2D array plotting unpulsed max(amp) vs. pulsed channel
  - labels each channel ichannel = crate*64*15 + 64*(slot-4) + slot
  - maxadc.npy
* plot.py
  - plots array in maxadc as 2D histogram
