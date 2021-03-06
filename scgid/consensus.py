"""
Created on Tue Dec 12 02:59:19 2017

@author: kevinamses
"""
if __name__ == "__main__":
    raise NotImplementedError(f"Calling this script directly is not implemented.")

else:
    import argparse
    import pandas as pd
    import os
    from scgid.modcomm import (LoggingEntity, Head)
    from scgid.module import Module
    from scgid.reuse import ReusableOutput, ReusableOutputManager
    from scgid.parsers import PathStore
    from scgid.sequence import DNASequenceCollection

    class Consensus (Module, LoggingEntity, Head):
        def __init__(self, argdict = None):
            super().__init__(self.__class__)
            if argdict is not None:
                self.config.load_argdict(argdict)
            else:
                self.argparser = self.generate_argparser()
                self.parsed_args = self.argparser.parse_args()
                self.config.load_cmdline( self.parsed_args)

            self.set_rundir(self.config.get("prefix"))

            self.config.reusable.populate(
                ReusableOutput (
                    arg = "gct",
                    pattern = ".*[.]gct[.]filtered[.]assembly[.]fasta",
                    genfunc = None,
                    genfunc_args = None
                ),
                ReusableOutput (
                    arg = "codons",
                    pattern = ".*[.]codons[.]filtered[.]assembly[.]fasta",
                    genfunc = None,
                    genfunc_args = None
                ),
                ReusableOutput (
                    arg = "kmers",
                    pattern = ".*[.]kmers[.]filtered[.]assembly[.]fasta",
                    genfunc = None,
                    genfunc_args = None
                )
            )

        def generate_argparser(self):
            parser = argparse.ArgumentParser()
            parser.add_argument("mod", nargs="*")
            parser.add_argument('-n','--nucl', metavar = "contig_fasta", action=PathStore,required=True,help = "A FASTA file containing the genome assembly.")
            parser.add_argument('-g','--gct', metavar = 'gct_fasta', action=PathStore, required=False, help="The location of")
            parser.add_argument('-c', '--codons', metavar = "codons_fasta", action=PathStore, required=False, help = "The location of")
            parser.add_argument('-k','--kmers', metavar = "kmers_fasta", action=PathStore, required=False, help = "The location of")
            parser.add_argument('-ex','--exclude_annot_nt', required = False, action ='store_true', help="Include this flag if you would like taxonomically-annottated scaffolds identified by scgid blob as nontarget to be automatically excluded despite consensus.")
            #parser.add_argument('--except', metavar = 'exception_list', required=False, action = 'store', default = help="A newline-separated list of contigs to not include in final genome regardless of consensus by majority rule between methods. DEFAULT = list of spdb-annotated scaffolds generated by scgid blob (ie blob/exluded_by_taxonomy.list)")
            parser.add_argument('-f','--prefix', metavar = 'prefix_for_output', action='store', required=False, default='scgid', help="The prefix that you would like to be used for all output files. DEFAULT = scgid")
            parser.add_argument('--venn', action='store_true', help = 'Include this flag if you would like to print information about which methods excluded which contigs from consensus.')
            
            return parser

        def run(self):
            
            self.setwd( __name__ )

            ##############################################
            ######## Skip this if called directly ########
            ######## (i.e., in tests)             ########
            ##############################################
            if self.root is not None:
                self.log_to_rundir(type(self).__name__)
                self.log_config()

            self.config.reusable.check()
            self.config.dependencies.check(self.config)
            self.config.reusable.generate_outputs()

            #'''
            unfiltered = DNASequenceCollection().from_fasta(self.config.get("nucl"))
            gct = DNASequenceCollection().from_fasta(self.config.get("gct"))
            codons = DNASequenceCollection().from_fasta(self.config.get("codons"))
            kmers = DNASequenceCollection().from_fasta(self.config.get("kmers"))

            include_mat = pd.DataFrame(index=list(unfiltered.headers()))
            include_mat["gct"] = [1 if (h in gct.headers()) else 0 for h in include_mat.index]
            include_mat["codons"] = [1 if (h in codons.headers()) else 0 for h in include_mat.index]
            include_mat["kmers"] = [1 if (h in kmers.headers()) else 0 for h in include_mat.index]

            include_mat.to_csv("consensus_matrix.tsv", sep="\t", index=True)
            #os.rename("consensus_matrix.tsv", "../consensus_matrix.tsv")
            #'''
            #include_mat = pd.read_csv("../consensus_matrix.tsv", sep="\t")
            
            include_mat = include_mat.assign(votes = include_mat.gct+include_mat.codons+include_mat.kmers )

            to_keep = include_mat.loc[include_mat.votes >= 2]

            final_assembly = unfiltered.header_list_filter(to_keep.index.to_list())

            # Compute final filtered assembly stats
            filtered_size = sum([len(s.string) for s in final_assembly.seqs()])
            filtered_ncontigs = len(final_assembly.seqs())

            self.logger.info(f"Filtered assembly contains {filtered_ncontigs:,} contigs with a cumulative size of {filtered_size:,} bp ({filtered_size/1e6:.2f} Mbp).")
            
            # Print final filtered assembly to FASTA
            final_fname = f"{self.config.get('prefix')}.consensus.filtered.assembly.fasta"
            final_assembly.write_fasta( final_fname )

            self.logger.info(f"Final filtered assembly written in FASTA format to `{final_fname}`")

            # Migrate and then remove temp dir, cd back to starting dir
            self.migrate_temp_dir()
            self.resetwd()

            self.logger.info("Consensus filtering complete. Returning to SCGid.")

            return final_assembly
