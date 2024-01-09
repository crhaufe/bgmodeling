import glob

th_excess_jobs_file = open("trace_to_pandas.txt","a")
string_list = []
seed_list = []
#i = 1
glob_list = glob.glob('../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232OuterCuShield_pooled_M1vM2_origpriors_10_100_3000_Model/trace*')
for entry in glob_list:
    seed_number = int(entry[129:])
    seed_list.append(seed_number)
for seed in seed_list:
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232Bellows_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37780536 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1Bellows bulk_M2Bellows > ../pandas_logs/Bellows_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232LMFEs_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 39795316 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1LMFEs bulk_M2LMFEs > ../pandas_logs/LMFEs_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232Seals_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37788745 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1Seals bulk_M2Seals > ../pandas_logs/Seals_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232Cables_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38697654 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CrossarmAndCPCables bulk_M2CrossarmAndCPCables bulk_M1StringCables bulk_M2StringCables > ../pandas_logs/Cables_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232CryostatCuNear_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37983039 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CryostatCopperNear bulk_M2CryostatCopperNear > ../pandas_logs/CryostatCuNear_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232CryostatCuFar_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37777883 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CryostatCopperFar bulk_M2CryostatCopperFar > ../pandas_logs/CryostatCuFar_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232DUStringCu_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37846033 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1DUStringCopper bulk_M2DUStringCopper > ../pandas_logs/DUStringCu_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232InnerCuShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37776742 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldCuInner> ../pandas_logs/InnerCutShield_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232PbShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38000674 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldAssembly_001_RadShieldPb_001 > ../pandas_logs/RadShieldPb_%i.log 2>&1' % (seed,seed))
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232OuterCuShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38102261 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldCuOuter > ../pandas_logs/OuterCuShield_%i.log 2>&1' % (seed,seed))
  #string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_seed_number %i --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37527395 > ../pandas_logs/NoExcess_%i.log 2>&1' % (seed,seed))
  #i+=1
th_excess_jobs_file.writelines("%s\n" % l for l in string_list)
th_excess_jobs_file.close()
