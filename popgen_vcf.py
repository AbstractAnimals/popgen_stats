import sys
import argparse
import cyvcf
import pgstats as pg
import gzip

def calc_rac(snp):
     rac = (snp.num_hom_ref * 2) + snp.num_het

     return rac

parser = argparse.ArgumentParser(description="Program to calculate population genetic statistics from a region in VCF file")
parser.add_argument('-i', '--vcf', required=True, dest='vcf_infile', help="VCF input file (Needs to be filtered in some way. SNPs without PASS in filter field will be excluded by default, but may be included if the -u flag is used (see below))")
#parser.add_argument('-o', '--out', required=False, dest='vcf_infile', default=stdout, help="File where the output is written (default is to write to stdout)")
parser.add_argument('-u', '--unifiltered_sites', required=False, action='store_true', dest='unfiltered', help="VCF input file (Include sites with a PASS in the filter field of the VCF (default; False")
#parser.add_argument('-x', '--pop_1', required=False, dest='pop1', help="Samples belonging to population 1")
#parser.add_argument('-y', '--pop_2', required=False, dest='pop2', help="Samples belonging to population 2")
#parser.add_argument('-r', '--region', required=False, dest='region', help="Region to calculate stats. Format is chromosome:start-end or file listing regions (or sites) (1-based coordinate system). If region is not given the stats will be calculated on the whole vcf file")
parser.add_argument('-d', '--min_dp', required=False, dest='min_dp', type = int, help="Minimum depth per genotype")
parser.add_argument('-D', '--max_dp', required=False, dest='max_dp', type = int, help="Maximum depth per genotype")    
args = parser.parse_args()


min_dp = 1
if args.min_dp:
     min_dp = args.min_dp

max_dp = None
if args.max_dp:
     max_dp = args.max_dp


#vcf_infile = cyvcf.Reader(gzip.open(args.vcf_infile, 'r'))

vcf_infile = cyvcf.Reader(open(args.vcf_infile, 'r'))

samples = vcf_infile.samples

n_total = 2*len(samples) # assumes diploid genotypes. 


pop1_index = []
pop2_index = []

n1 = len(pop1_index)
n2 = len(pop2_index)


indels = 0
low_call_rate = 0
spanning_deletion = 0
multiallelic_snp = 0
valid_sites = 0
failed_snp= 0
ref_N = 0

rac_list = [] # list to hold reference allele counts from SNP sites

for site in vcf_infile:
#for site in vcf_reader.fetch(chrom, start - 1, end):
     if site.REF == 'N':
          #ref_N += 1
          continue

     if site.is_indel:
          #indels += 1
          continue
      
     if len(site.ALT) >= 1 and site.ALT[-1] == '*': # SNPs at spanning deletion
          #spanning_deletion += 1
          continue
     
     all_DP =[x['DP'] for x in site.samples] # get the genotype depths
     
     
     if 0 in all_DP or site.call_rate < 1.0: # only consider sites where all samples have coverage
         #low_call_rate += 1
         continue

     if site.is_monomorphic:
          valid_sites += 1
          continue

     if site.is_snp:
          if len(site.ALT) >  1:
               #multiallelic_snp += 1
               continue 
          if site.aaf == 1.0 or site.aaf == 0.0: # only want SNPs polymorphic in ou\r sample                         
               valid_sites += 1
               continue

          if not args.unfiltered:
               if site.FILTER == 'PASS':
                    rac = calc_rac(site)
                    rac_list.append(rac)
                    valid_sites += 1
                    continue
               else:
                    #failed_snp += 1
                    continue
          else:
               rac = calc_rac(site)
               ral_list.append(site)
               valid_sites += 1
               continue
     else:          
          problem_site = site.CHROM + '\t' + str(site.POS)
          error_message = 'Could not assign ' + problem_site + ' to site type'
          sys.exit(error_message)
                    

S = len(rac_list)
theta_w = pg.thetaW(n_total, rac_list)
pi = pg.pi(n_total, rac_list)
tajD = pg.TajimasD(n_total, S, theta_w, pi)


print 'S:', S
print 'thetaW:', theta_w / float(valid_sites)
print 'pi:', pi / float(valid_sites)
print "Tajima's D:", tajD
print 'valid sites:', valid_sites
print 'ref N:', ref_N
print 'indels:', indels 
print 'snp spanning deletion:', spanning_deletion
print 'low call rate:', low_call_rate
print 'multiallelic snps:', multiallelic_snp 
print 'failed biallelic snps:', failed_snp
print 'total sites considered:', valid_sites + indels + spanning_deletion + low_call_rate + multiallelic_snp + failed_snp
