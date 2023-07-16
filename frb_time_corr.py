import pandas as pd
import argparse
import numpy as np
from astropy.time import Time

def time_delay(freq,dm): # freq in MHz, DM in pc/cc
    delta_t = 4.15*(1e3/freq)**2*dm/1e3
    return delta_t

def utc_to_astrosat(time):
	time0 = '2010-01-01T00:00:00'
	t0 = Time(time0,format='isot',scale='utc')
	t = Time(time)
	dt = t - t0
	return dt.sec

def process_csv(in_file):
    df = pd.read_csv(in_file)
    df.insert(27, column = "Discovery_time_inff", value = 0)
    df.insert(28, column = "time_delay", value = 0)
    for i in df['Discovery Date (UT)']:
        t = utc_to_astrosat(i)
        print(i , t)
        delta_t = time_delay(400.1953125, df['DM'][df['Discovery Date (UT)']==i]) ## add list of freqs
        print(delta_t)
        df.loc[(df['Discovery Date (UT)']==i),'time_delay'] = - delta_t
        df.loc[(df['Discovery Date (UT)']==i),'Discovery_time_inff'] = t - delta_t
    df.to_csv('chime_time_corr.csv')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_file",
        type=str,
        help="Name of the csv file in which FRBs are stored",
    )
    args = parser.parse_args()
    in_file = args.csv_file
    process_csv(in_file)

