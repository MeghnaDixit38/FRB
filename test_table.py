import make_lightcurves
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import time
import os
from astropy.stats import sigma_clipped_stats


script_start_time = time.time()

directory = 'local_level2'

#set list of dates to target
years = [2023]
months = [3,4]
days = range(1,32)



orbit_count=0
total_computation_time=0

for year in years:
    for month in months:
        for day in days:
            prefix = f'{year:04}{month:02}{day:02}'
            prefixed = [filename for filename in os.listdir(directory) if filename.startswith(prefix)]
            for pref in prefixed:
                print("current day:", pref)
                path = f'{directory}/{pref}/czti/orbit/'
                orbits = [filename for filename in os.listdir(path)]
                for orbit in orbits:
                    try:
                        orbit_count+=1
                        orbit_start_time = time.time()
                        print("orbit:", orbit)
                        path_internal = path+orbit + '/'
                        lc_all = []
                        mask_all = []
                        times_all = []
                        for quadrant_num in range(4):
                            light_curve_file = path_internal+f'{orbit}_1.0_3_Q{quadrant_num}.lc'
                            lc_detrend, mask_lc,startbins3,stopbins3, error_flag = make_lightcurves.getlc_clean(1, light_curve_file,10, 'median', 0, 10, 1)
                            times = fits.getdata(light_curve_file)['time']
                            lc_all.append(lc_detrend)
                            mask_all.append(mask_lc)
                            times_all.append(times)

                        computation_start_time = time.time()
                    
                        coinc_arr = [1,2,3,4]
                        sigma_arr = [0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]
                        coinc_sigma_table =  np.zeros((len(sigma_arr), len(coinc_arr)))
                    # coinc_sigma_table2 =  np.zeros((len(sigma_arr), len(coinc_arr)))
                    except:
                        print("error in orbit")
                        orbit_count-=1
                        continue

                    cutoffs = np.zeros((4,len(sigma_arr)))
                    for quadno in range(4):
                        stats = sigma_clipped_stats(lc_all[quadno], mask=mask_all[quadno],
                                                    sigma=5.0, maxiters=3)
                        for sigma_id in range(len(sigma_arr)):
                            cutrate = stats[0] + sigma_arr[sigma_id]*stats[2]
                            cutoffs[quadno, sigma_id] = cutrate


                    arr_len = max(len(lc_all[0]),len(lc_all[1]),len(lc_all[2]),len(lc_all[3]))
                    complete_arr = np.zeros((4,arr_len))
                    for i in range(4):
                        complete_arr[i,:len(lc_all[i])] = lc_all[i]


                    for coinc in range(len(coinc_arr)):
                        peak_ind_bin = np.where(complete_arr[0] - complete_arr[0] == 0)
                        complete_arr2 = complete_arr[:,peak_ind_bin[0]]
                        for cutoff_set in range(len(cutoffs[0])):
                            # print('peak_ind_bin: ', peak_ind_bin[0][:10])

                            peak_map = np.zeros((4,len(peak_ind_bin[0])))
                            # peak_map2 = np.zeros((4,arr_len))
                            complete_arr2 = complete_arr2[:,peak_ind_bin[0]]
                            if len(complete_arr2[0,:])==0:
                                break
                            # print(np.shape(complete_arr2))
                            # print(np.shape(complete_arr))
                            # cutoffs2 = cutoffs[:, peak_ind_bin]
                            for i in range(4):
                                peak_map[i][complete_arr2[i] > cutoffs[i,cutoff_set]] = 1
                                # peak_map2[i][complete_arr[i] > cutoffs[i,cutoff_set]] = 1
                            
                            # print(peak_map[:,:10])
                            # print(peak_map2[:,:10])

                            peak_ind_bin =  np.where(np.sum(peak_map, axis=0) >= coinc_arr[coinc])
                            # peak_ind_bin2 =  np.where(np.sum(peak_map2, axis=0) >= coinc_arr[coinc])

                            # print('setting val 1: ', len(peak_ind_bin[0]))
                            # print('setting val 2: ', len(peak_ind_bin2[0]))

                            coinc_sigma_table[cutoff_set, coinc] =  len(peak_ind_bin[0])
                            # coinc_sigma_table2[cutoff_set, coinc] =  len(peak_ind_bin2[0])


                    #print(coinc_sigma_table)
#table = np.array([[1.03, 1.031, 19.2],[2.10, 1.00, 9.87],[1.83, 8.42, 9.000]])
                    
                    col_arr = []
                    t=0
                    for sigma in sigma_arr:
                        col_arr.append(fits.Column(name=str(sigma), format = 'J', array=coinc_sigma_table[t]))
                        t+=1
                    
                    hdu = fits.BinTableHDU.from_columns(col_arr)
                    hdu.writeto(path_internal+f"{orbit}_1.0_3_CoincSigmaTable.fits", overwrite=True)

                    print("time on orbit:",time.time()-orbit_start_time)
                    computation_time=time.time()-computation_start_time
                    print("time_for_my_computation:",computation_time)
                    total_computation_time+=computation_time





total_time = time.time()-script_start_time

print("total orbits analyzed:", orbit_count)
print("total time taken:", total_time)
print("average time per orbit:", total_time/orbit_count)
print("average computation time:", total_computation_time/orbit_count)


                    # print(coinc_sigma_table2)




                    # plt.plot(sigma_arr, coinc_sigma_table[:,3])
                    # plt.title('4 quadrant coincidences')
                    # plt.xlabel('nsigma value')
                    # plt.ylabel('counts')











