#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 02:59:19 2017

@author: kevinamses
"""

import argparse
import operator
import os
import sys
import inspect
import pandas as pd
from sequence import *
from lib import *

bin_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
pkg_home = os.path.dirname(bin_dir)

parser = argparse.ArgumentParser()
parser.add_argument('-n','--nucl', metavar = "contig_fasta", action="store",required=True,help = "A FASTA file containing the genome assembly.")
parser.add_argument('-e','--esom', metavar = "esom_fasta", action="store", required=False, help = "The location of")
parser.add_argument('-r', '--rscu', metavar = "rscu_fasta", required=False, help = "The location of")
parser.add_argument('-b','--blob', metavar = 'blob_fasta', required=False, help="The location of")

parser.add_argument('-ex','--exclude_annot_nt', required = False, action ='store_true', help="Include this flag if you would like taxonomically-annottated scaffolds identified by scgid blob as nontarget to be automatically excluded despite consensus.")

#parser.add_argument('--except', metavar = 'exception_list', required=False, action = 'store', default = help="A newline-separated list of contigs to not include in final genome regardless of consensus by majority rule between methods. DEFAULT = list of spdb-annotated scaffolds generated by scgid blob (ie blob/exluded_by_taxonomy.list)")

parser.add_argument('-f','--prefix', metavar = 'prefix_for_output', action='store', required=False, default='scgid', help="The prefix that you would like to be used for all output files. DEFAULT = scgid")
parser.add_argument('--venn', action='store_true', help = 'Include this flag if you would like to print information about which methods excluded which contigs from consensus.')
args = parser.parse_args()

prefix = args.prefix
nucl_path = os.path.abspath(args.nucl)

## Make sure that all three draft genomes are present in default or specified locations
if args.esom is None:
    esom_path = os.path.join(os.getcwd(),prefix+"_scgid_output","esom",prefix+'_esom_final_genome.fasta')
    if os.path.isfile(esom_path) is False:
        raise IOError("ESOM draft genome not detected in default location. Specificy its path with -e|--esom")
        logger.critical(IOError("ESOM draft genome not detected in default location. Specificy its path with -e|--esom"))
else:
    esom_path = os.path.abspath(args.esom)
    if os.path.isfile(esom_path) is False:
        raise IOError("ESOM draft genome not present in specified location: "+esom_path)
        logger.critical(IOError("ESOM draft genome not present in specified location: "+esom_path))

if args.rscu is None:
    rscu_path = os.path.join(os.getcwd(),prefix+"_scgid_output","rscu",prefix+'_rscu_final_genome.fasta')
    if os.path.isfile(rscu_path) is False:
        raise IOError("RSCU draft genome not detected in default location. Specificy its path with -r|--rscu")
        logger.critical(IOError("RSCU draft genome not detected in default location. Specificy its path with -r|--rscu"))
else:
    rscu_path = os.path.abspath(args.rscu)
    if os.path.isfile(rscu_path) is False:
        raise IOError("RSCU draft genome not present in specified location: "+rscu_path)
        logger.critical(IOError("RSCU draft genome not present in specified location: "+rscu_path))

if args.blob is None:
    blob_path = os.path.join(os.getcwd(),prefix+"_scgid_output","blob",prefix+'_blob_final_genome.fasta')
    if os.path.isfile(blob_path) is False:
        raise IOError("BLOB draft genome not detected in default location. Specificy its path with -b|--blob")
        logger.critical(IOError("BLOB draft genome not detected in default location. Specificy its path with -b|--blob"))
else:
    blob_path = os.path.abspath(args.blob)
    if os.path.isfile(blob_path) is False:
        raise IOError("BLOB draft genome not present in specified location: "+blob_path)
        logger.critical(IOError("BLOB draft genome not present in specified location: "+blob_path))

try:
    os.chdir(args.prefix+'_scgid_output')
except:
    os.mkdir(args.prefix+'_scgid_output')
    os.chdir(args.prefix+'_scgid_output')

logs = start_logging('consensus', args, sys.argv)
logger = logs[0]
blogger = logs[1]

#generate list of scaffolds to ad hoc exclude based on swissprot taxonomy
exclude_by_tax = []
if args.exclude_annot_nt:
    exclude_by_tax = open(os.path.join('blob','excluded_by_sp_taxonomy')).readlines()
    exclude_by_tax = map(str.strip, exclude_by_tax)

try:
    os.chdir('consensus')
except:
    os.mkdir('consensus')
    os.chdir('consensus')

all_contigs = pkl_fasta_in_out(nucl_path)
logger.info("Assembly FASTA read-in successfully.")

from_esom = readFasta(esom_path)
logger.info("ESOM draft genome FASTA read-in successfully.")

from_rscu = readFasta(rscu_path)
logger.info("RSCU draft genome FASTA read-in successfully.")

from_blob = readFasta(blob_path)
logger.info("BLOB draft genome FASTA read-in successfully.")

labels_from_esom = get_attribute_list(from_esom,'label')
labels_from_rscu = get_attribute_list(from_rscu,'label')
labels_from_blob = get_attribute_list(from_blob,'label')

to_consensus = []
exclude = []

kicked_by = {'esom':[],'rscu':[],'blob':[]}
acc_by = {'esom':[], 'rscu':[], 'blob':[]}
for tig in all_contigs:
    repdex = 0
    if tig.label in labels_from_esom:
        repdex += 1
        acc_by['esom'].append(tig.label)
    else:
        kicked_by['esom'].append(tig.label)

    if tig.label in labels_from_blob:
        repdex += 1
        acc_by['blob'].append(tig.label)
    else:
        kicked_by['blob'].append(tig.label)

    if tig.label in labels_from_rscu:
        repdex += 1
        acc_by['rscu'].append(tig.label)
    else:
        kicked_by['rscu'].append(tig.label)

    if repdex >= 2:
        tig_shortname = '_'.join(tig.name.split('_')[0:2])
        #print tig_shortname
        if tig_shortname in exclude_by_tax:
            exclude.append(tig)
        else:
            to_consensus.append(tig)
    else:
        exclude.append(tig)
#logger.info(str(len(kicked_by['rscu'])))
total_len = 0
with open(prefix+'_consensus_final_genome.fasta','w') as fasta:
    for tig in to_consensus:
        total_len += tig.length
        fasta.write(tig.outFasta()+'\n')
with open(prefix+'_nontarget_bin.fasta','w') as fasta:
    for tig in exclude:
        fasta.write(tig.outFasta()+'\n')

logger.info("Final consensus genome written to "+os.path.join(os.getcwd(),prefix+'_consensus_final_genome.fasta'))
logger.info("Final consensus-predicted genome consists of "+str(total_len)+" nucleotides on "+str(len(to_consensus))+" scaffolds.")

if not args.venn:
    sys.exit(0)

## Else continue with this stuff...

''' kicked by method

for meth in kicked_by:
    for tig_label in kicked_by[meth]:
        print "kicked_by_"+meth+","+tig_label

'''
logger.info(len(acc_by['rscu']))
logger.info(len(acc_by['blob']))
logger.info(len(acc_by['esom']))
#logger.info(len(kicked_by['rscu']))
#logger.info(len(kicked_by['blob']))
#logger.info(len(kicked_by['esom']))

#cons_labels = get_attribute_list(to_consensus,'label')

### Filtered out by consensus but included in each method
#for tig_label in acc_by[meth]:
#    if tig_label not in cons_labels:
#        print "filtered_OUT_by_consensus_"+meth+","+tig_label

