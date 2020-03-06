import pytest
import copy
import os
import inspect
import logging.config
from scgid.codons import Codons, RSCUTree, CDSConcatenate, SmallTreeError, NoGoodCladesError
from scgid.sequence import DNASequenceCollection
from scgid.error import is_ok, Ok, check_result

tests_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

cds_concatenate1 = CDSConcatenate(
	header = "NODE_6239",
	string = "ATGGCTTTAGAGCAATTTCCATATAAGAAGGATGTTGAAGTTGAGTTTAAAAGTTTTGAATTAGACCAAAATGCTCCAATCTATTCTGGAACAAGTATTAATGAAGTACTTGCATCAAAGTATGGAATTAGTATTGAAGAAGCTAAGCGTAATAACGTACAGTTAGGAAATCATGCAGCTAGTATGGGTTTAAGTTTTAATTTTGATGAGATGAAGCCGACTAATACTTTTGATGCGCATCGTCTTGCGAAGTTTGCAAAGAATCAAGGGAAAGAAAAAGAGATTACAGAAAATCTACTTTTTGCATATTTCACTGAATCGAAAAATTTAAGCGATGTGGATACACTTGCTACTATCGCTGAAGCTTCAGGTTTAGATAAGCAAGAAGCTTTAAATGTTATTAATGATAAAAATGCGTATGCAAATGATGTTAGAATTGATGAAGCGATTGCTCAGCAATATCAAATTTCGGGAGTGCCTTATTTTATTATTAATCAAAAGTATGCTATTTCAGGTGCACAACCACTTGAAACTTTTGTTGGTGCACTTCAGCAAGTGTGGGAAGAAGAGAATCCTGCACCTAAGTTGCAAGAACTTTCTTCAGAGGGTGGAAGCGATCTTTCTTGTACTGATGGAAGTTGTTCGGTGCCGTCGAAAGAACAAATGTTAGTTGGGAATTATTTTTATAACTACGCGTTAAATGCGAAACAAGAAAAAGAATTTTTGCAAGATAATCCTCATTTAGTAGAAACGGTAAATGCGTCGGGAGATGTATTGGCTGCAAATGAAGAAAAGAATGCAAACTTCGTATCGAAGTATAAACCTAACACATTAACTATACGTTCTTTCGATAAATTAAATTTAAAAGGTTATGAATATATGAATGAACCATCCAGTCATAAATGGGCAATTGTAGTTCATGGATACAATGGTAGAGCATCAGAAATGACGAAATATGTTCGTAACTTTTATGAACAAGGCTATAATGTCATAGCACCAGACCTTCGTGGACACGGAAATAGTGAAGGGGATTATGTTGGTATGGGCTGGCATGATCGTAAAGATGTTTTGATTTGGATTCAACAAATCTTGAAGAAAGACCCTAATGCTGAAATAGCTCTATTTGGTGTTTCAATGGGCGGGGCAACTGTAATGATGACTTCAGGAGAAGATTTACCTTCTAATGTTAAAGTTATTATTGAAGATTGTGGATACTCAACTGTTATTGATGAATTTACTTATCAACTAAAAGATTTATTCCATTTACCGAAGTTTCCTGTTATGAATGCGGCAAATATGGTTACTAAATTAAGAGCTGGTTACGATTTAGAAGAGGCTTCAGCTGTAAAACAAGTAGCGAAAAGTAAAACACCTATGTTATTCATTCATGGGGATGCTGATACATTCGTTCCTTTTGAAATGTTAGATGAAGTATATAATGCTGCAAAAGTAGAAAAAGAGAAATTAATTGTTCCAGGTGCTGGACATGGAGAAGCGGAGAAAGTAGATTCGAATAAATATTGGAATACTGTATGGAAGTTCGTAGGGAAGTATATTCCGGCA"
	)

cds_concatenate2 = CDSConcatenate(
	header = "NODE_6237",
	string = "CGGCTCGCGCCGCTGCAGGAGAGGCTGCTGGCGAAGCGGACCGTGGTGGGATTAATCGACCTAACCGGTCAGCTGGAATTCGTCGACCTGACCCTCGATCCAACGGCAGCTATCGGGAGCTGGTGCTGCCGCCGACCTTCGTGCAGGGCGTCGGCGTGCGGTCCCGCGTGGAGGACTGGCCGCTGGATCCCAGCCGCGCAGCTGCTCTAAATGCTCTGCAGCAGCTGCAGCAGGCGCCGCAGCAGGCGCAGCAGCAGGCGCTGCAGCCCTCAGGGCCGGGCGCACGAGGCCCGCTGCGGGAAATCCAGCATCACACGGCGGTGGGGGCGGCGGGAGCGGCGGCGCGCCCTGCGGCCCTGCGGCGGAGACGCTGACGCAGGTCCTGGAGGGCAAAATGACCGGCACAGAGCTGCGCAAGGCCAGGATTTGGGTGGAGCTGCAGGCTCGTGGGTTCCAGTTCTTCGTCCGGTGCGTTCAGGAGAAGGGGAGGGCTTCAAGGGGTGCGGCAGAGCACATGCATGCACTGCTACCGGCTATTCG"
	)

cds_concatenate3 = CDSConcatenate(
	header = "NODE_6474",
	string = "TGCAAGGCCGTGGTAAGGCGGCAGTAGCAACACAGCAGTCGACTCGAACAGTATTGAGACCCACCGGGGATGGACGCTGCTGTGCTGAAGCCATGGCCCTTACGCCGCGGCCTATCGCTGTTGCGACACGCCACTTGTACCGCCAACCTTGCCACCAACCAGCGACACGGTGTTGGAGCTGCCACCCAAACCCATGTTCCGTTCCCCTGACGAAGCACCAAAGTTGTCCACGGGACCCGAGCTCCCCTTTCACGTCCAGCTATCGCTTGATGCGATTCGTCTCCTTCCGGCCCTGTCAAGCGCTCACCTGGCCGCGCAGGCGCCCGATCGTGGGACGTGTGGCCTGCAACACACCGCCATGTGGGACGTACTGCAAGACGGCATGAGGATGGGAGAGCAACGACAAGACGGCACGCCTAGTCAGGAGGACTCACGTCCTGTCACGCCCGCTGTGTGGCACCGGTACCCCCTGCCGCGCAACATGGGCACTTCGCCTCGCAAACCCTCAACGAATTATAAGGTTGCTGGCCTACTGTACGCCCTGCTGCATCGGGTCCTATACCACACGGTCCTGGGCAAGAGCGACAACCACTCGCGGAGCAGCAGTCTCGACTCACCTGCTTTCATGGCTGAGCACTCCGCTGATGCAACATGCACGTATGAGGCGCCGGCGCCCACGCCACCACCGGAACCACCGCCGCGTGTGTATGTTGGACATGGCGCGAGACAGTCGTTACTACGAGGAAGATACGTGCTACGTGCCGTATGAGGAGTATGAAACACACCCTGACGCCGAGCGAGGGGGCGAGCAGGTGACCGTCCCTTCCACACAACCGTATGCGCCGGACACCCCTGAGCTCACACCATATTCCACACCTGTAACTGCGCTTGCGCACCCACCTCGCGCCACCTTCCCGACGCACGTTTACGTCATGCAGCAGACCGTATCCCCGCCGCCAGCAGTAATACGGGATGACACGCCCCAGCGGGCATATCACTTGGAGCAGATTCCCGCGCAGCAGCCCGCGCAACCTGCGGAGGAGAGCCATGATGGTGCAAGCGAGGACGTGAAAGGCGTGGACATGTACCCCATGCCGTTGCATCCAACACTCGGATGGGACGCCGTATGCAATCAGGACCCGGCGCAGCCCATCGAGAGCGCACCTACTGTAAACCCCGGCAGTTCCGTGCCTGGTGTCCAATCGTCACTCCAACACTTGCCAACCGTGGAAAGGGATACGCCCGTGCTCGAGTCGCCCGACACCCGCGAGAGGCTTACTCGGGAGTCACCCGCTGTGCAGCAGATGCCGCCAGCAGCGCCGTATTTGCCTGAGCACGCCTCGACACCACAGCTTCAGCAGACAGCGCTCCCGTCAGCTCCGCCGGCGGCTTGGCTTGCTTGTACGCCGCCGCGTGCTTGCCTTGATGCCTCGACAGGGCAACCTGCCGATATGACAAGGTGTCAGGGGAATCGCCAGTCAGATGAGCTGCACGCGCCAG"
	)

cds_concatenate_dict = {
	cds_concatenate1.header: cds_concatenate1.string,
	cds_concatenate2.header: cds_concatenate2.string,
	cds_concatenate3.header: cds_concatenate3.string,
}

cds_concatenate_collection = DNASequenceCollection().from_dict(cds_concatenate_dict)

# Module argdicts
codons_argdict = {
	"clams_path": "/home/aimzez/apps/ClaMS-CLI/ClaMS-CLI.jar",
	"default_spdb": "/home/aimzez/database/uniprot_sprot_13-Nov-2019.fasta",
	"default_taxdb": "/home/aimzez/database/uniprot_sprot_13-Nov-2019.fasta.taxdb",
	"esom_path": "/Applications/ESOM",
	"mpicmd": "mpirun",
	"path_to_Rscript": "/usr/bin/Rscript",
	"spdb_version": "13-Nov-2019",
	"taxonomy_all_tab": "/Users/aimzez/dev/SCGid/database/uniprot-taxonomy-all-121019.tab",
	"mod": ['codons'],
	"gene_models": os.path.join(tests_dir, "data/gene_models.gff3"),
	"assembly_fasta": os.path.join(tests_dir, "data/test.contigs.fasta"),
	"protein_fasta": None,
	"target_taxa": "Fungi",
	"exception_taxa": None,
	"output_prefix": "tests",
	"cpus": 1,
	"annotation_mode": "blastp",
	"minlen": 100,
	"mincladesize": 2,
	"augustus_species": None,
	"blast_evalue_cutoff": "1e-5",
	"spdb_blast_output": os.path.join(tests_dir, "data/spdb.blastout"),
	"infotable": os.path.join(tests_dir, "data/infotable.tsv"),
	"noplot": False,
	"available_memory": "2g",
	"swissprot_fasta": "/home/aimzez/database/uniprot_sprot_13-Nov-2019.fasta",
	"swissprot_taxdb": "/home/aimzez/database/uniprot_sprot_13-Nov-2019.fasta.taxdb"
}

# Module object(s)
CodonsInstance = Codons(argdict = codons_argdict)
CodonsInstance.start_logging()
#CodonsInstance.config.logger.setLevel(logging.INFO)

RSCUTreeInstance = RSCUTree(
		treepath = os.path.join(tests_dir, "data/tests_rscu_nj.tre"),
		head = CodonsInstance
		)

def test_correctly_catch_SmallTreeError():
	
	smaller_collection = copy.deepcopy(cds_concatenate_collection)
	smaller_collection.index.pop("NODE_6239")
	smaller_collection.index.pop("NODE_6237")

	retval = CodonsInstance.check_n_concatenates(
		seq_collection = smaller_collection,
		error_catch = False
		)

	assert isinstance(retval, SmallTreeError)

def test_correctly_do_not_catch_SmallTreeError():
	retval = CodonsInstance.check_n_concatenates(
		seq_collection = cds_concatenate_collection,
		error_catch = False
		)
	assert retval is None

def test_correctly_catch_NoGoodCladesError():
	RSCUTreeInstance_retarget = copy.deepcopy(RSCUTreeInstance)
	
	RSCUTreeInstance_retarget.infotable.set_target(target = "Nothing_alive")
	RSCUTreeInstance_retarget.infotable.parse_lineage()
	RSCUTreeInstance_retarget.infotable.clear_decisions()
	RSCUTreeInstance_retarget.infotable.decide_inclusion()

	RSCUTreeInstance_retarget.annotate()
	retval = RSCUTreeInstance_retarget.pick_clade(error_catch = False)

	assert isinstance(retval, NoGoodCladesError)

def test_correctly_do_not_catch_NoGoodCladesError():
	RSCUTreeInstance.annotate()
	retval = RSCUTreeInstance.pick_clade(error_catch = False)

	assert is_ok(retval)

def test_run():
	retval = CodonsInstance.run()

	assert isinstance(retval, DNASequenceCollection)
	assert len(retval.seqs()) == 2
	assert [x.header for x in retval.seqs()] == ["NODE_6239_length_2449_cov_19.254468", "NODE_6437_length_2226_cov_10.959567"]
	assert sum([len(s.string) for s in retval.seqs()]) == 4675
