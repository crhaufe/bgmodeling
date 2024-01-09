import glob

th_excess_jobs_file = open("th_excess_jobs_MJDstats.txt","a")
string_list = []
#seed_list = []
i = 21
#glob_list = glob.glob('../../FitSpectra_Models/DSgt0_cut26_opentoymcx1000_10xactivityTh232LMFEs_pooled_M1vM2_origpriors_10_100_3000_Model/trace*')
#for entry in glob_list:
#    seed_number = int(entry[121:])
#    seed_list.append(seed_number)
while i<40:
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232Bellows_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37781 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1Bellows bulk_M2Bellows > ../logs/Bellows_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232LMFEs_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 39795 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1LMFEs bulk_M2LMFEs > ../logs/LMFEs_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232Seals_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37789 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1Seals bulk_M2Seals > ../logs/Seals_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232Cables_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38698 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CrossarmAndCPCables bulk_M2CrossarmAndCPCables bulk_M1StringCables bulk_M2StringCables > ../logs/Cables_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232CryostatCuNear_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37983 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CryostatCopperNear bulk_M2CryostatCopperNear > ../logs/CryostatCopperNear_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232CryostatCuFar_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37778 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1CryostatCopperFar bulk_M2CryostatCopperFar > ../logs/CryostatCopperFar_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232DUStringCu_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37846 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_M1DUStringCopper bulk_M2DUStringCopper > ../logs/DUStringCopper_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232InnerCuShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37777 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldCuInner > ../logs/RadShieldCuInner_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232PbShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38001 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldAssembly_001_RadShieldPb_001 > ../logs/RadShieldPb_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_10xactivityTh232OuterCuShield_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 38102 --toymc_targeted_vals --toymc_targeted_vals_mult 10 --toymc_targeted_vals_dc Th232 --toymc_targeted_vals_comp bulk_RadShieldCuOuter > ../logs/RadShieldCuOuter_%i.log 2>&1' % i)
  string_list.append('python3 Fit.py --model_dirname ../../FitSpectra_Models/DSgt0_cut26_opentoymcx1_pooled_M1vM2_origpriors_10_100_3000_Model/ --model_type pooled --mcmc_draws 10000 --mcmc_cores 3 --mcmc_target_accept 0.99 --mcmc_random_seed --distribution_bin_wid 10.0 --fit_range 100.0 3000.0 --toymc --toymc_draws 37527 > ../logs/NoExcess_%i.log 2>&1' % i)
  i+=1
th_excess_jobs_file.writelines("%s\n" % l for l in string_list)
th_excess_jobs_file.close()