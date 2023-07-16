import pandas as pd

def time_delay(freq,dm): # freq in MHz, DM in pc/cc
    delta_t = 4.15*(1e3/freq)**2*dm/1e3
    return delta_t


