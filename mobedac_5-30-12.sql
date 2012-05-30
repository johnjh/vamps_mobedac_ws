# ************************************************************
# Sequel Pro SQL dump
# Version 3408
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.10-log)
# Database: mobedac
# Generation Time: 2012-05-30 17:08:32 -0400
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table sequence_prep
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sequence_prep`;

CREATE TABLE `sequence_prep` (
  `SEQUENCE_PREP_ID` int(11) NOT NULL AUTO_INCREMENT,
  `SAMPLE_METADATA_ID` int(11) NOT NULL,
  `NUCL_ACID_EXT` varchar(4000) DEFAULT NULL,
  `NUCL_ACID_AMP` varchar(4000) DEFAULT NULL,
  `LIB_SIZE` int(11) DEFAULT NULL,
  `LIB_READS_SEQD` int(11) DEFAULT NULL,
  `LIB_VECTOR` varchar(1000) DEFAULT NULL,
  `LIBR_SCREEN` varchar(1000) DEFAULT NULL,
  `TARGET_GENE` varchar(500) DEFAULT NULL,
  `TARGET_SUBFRAGMENT` varchar(500) DEFAULT NULL,
  `PCR_PRIMERS` varchar(2000) DEFAULT NULL,
  `MULTIPLEX_IDENT` varchar(500) DEFAULT NULL,
  `PCR_COND` varchar(2000) DEFAULT NULL,
  `SEQUENCING_METH` varchar(200) DEFAULT NULL,
  `SEQ_QUALITY_CHECK` int(11) DEFAULT NULL,
  `CHIMERA_CHECK` int(11) DEFAULT NULL,
  `SOP` varchar(1000) DEFAULT NULL,
  `URL` varchar(1000) DEFAULT NULL,
  `EXPERIMENT_ALIAS` varchar(500) DEFAULT NULL,
  `EXPERIMENT_CENTER` varchar(500) DEFAULT NULL,
  `EXPERIMENT_TITLE` varchar(500) DEFAULT NULL,
  `EXPERIMENT_ACCESSION` varchar(500) DEFAULT NULL,
  `STUDY_ACCESSION` varchar(500) DEFAULT NULL,
  `STUDY_REF` varchar(500) DEFAULT NULL,
  `STUDY_CENTER` varchar(500) DEFAULT NULL,
  `EXPERIMENT_DESIGN_DESCRIPTION` varchar(4000) DEFAULT NULL,
  `LIBRARY_CONSTRUCTION_PROTOCOL` varchar(4000) DEFAULT NULL,
  `SAMPLE_ACCESSION` varchar(500) DEFAULT NULL,
  `SAMPLE_ALIAS` varchar(500) DEFAULT NULL,
  `SAMPLE_CENTER` varchar(500) DEFAULT NULL,
  `POOL_MEMBER_ACCESSION` varchar(500) DEFAULT NULL,
  `POOL_MEMBER_NAME` varchar(500) DEFAULT NULL,
  `POOL_PROPORTION` varchar(500) DEFAULT NULL,
  `BARCODE_READ_GROUP_TAG` varchar(500) DEFAULT NULL,
  `BARCODE` varchar(500) DEFAULT NULL,
  `LINKER` varchar(500) DEFAULT NULL,
  `KEY_SEQ` varchar(500) DEFAULT NULL,
  `PRIMER_READ_GROUP_TAG` varchar(500) DEFAULT NULL,
  `PRIMER` varchar(500) DEFAULT NULL,
  `RUN_PREFIX` varchar(500) DEFAULT NULL,
  `REGION` varchar(500) DEFAULT NULL,
  `PLATFORM` varchar(500) DEFAULT NULL,
  `RUN_ACCESSION` varchar(500) DEFAULT NULL,
  `RUN_ALIAS` varchar(500) DEFAULT NULL,
  `RUN_CENTER` varchar(500) DEFAULT NULL,
  `RUN_DATE` varchar(500) DEFAULT NULL,
  `INSTRUMENT_NAME` varchar(500) DEFAULT NULL,
  `LIBRARY_STRATEGY` varchar(500) DEFAULT NULL,
  `LIBRARY_SOURCE` varchar(500) DEFAULT NULL,
  `LIBRARY_SELECTION` varchar(500) DEFAULT NULL,
  `ROW_INT` int(11) NOT NULL DEFAULT '-1',
  `VAMPS_PROJECT` varchar(45) NOT NULL,
  `VAMPS_DATASET` varchar(45) NOT NULL,
  `metagenome_name` varchar(100) NOT NULL DEFAULT '',
  `seq_meth` enum('Sanger','pyrosequencing','ABI-solid','454','Illumina','assembeled','other') DEFAULT '454',
  `seq_center` varchar(300) NOT NULL DEFAULT '',
  `seq_url` varchar(300) NOT NULL DEFAULT '',
  `seq_make` varchar(300) NOT NULL DEFAULT '',
  `seq_model` varchar(300) NOT NULL DEFAULT '',
  `seq_chem` varchar(300) NOT NULL DEFAULT '',
  `seq_direction` enum('forward','reverse','both') DEFAULT NULL,
  `domain` enum('bacteria','archaea','eukarya','') DEFAULT '',
  `forward_barcodes` varchar(300) NOT NULL DEFAULT '',
  `reverse_barcodes` varchar(300) NOT NULL DEFAULT '',
  `forward_primers` varchar(300) NOT NULL DEFAULT '',
  `reverse_primers` varchar(300) NOT NULL DEFAULT '',
  `thermocycler` varchar(300) NOT NULL DEFAULT '',
  `run_machine_type` varchar(300) NOT NULL DEFAULT '',
  `cloning_kit` varchar(300) NOT NULL DEFAULT '',
  `host_cells` varchar(300) NOT NULL DEFAULT '',
  `amp_polymerase` varchar(300) NOT NULL DEFAULT '',
  `cycle_count` int(10) unsigned NOT NULL DEFAULT '0',
  `cycle_annealing_duration` varchar(300) NOT NULL DEFAULT '',
  `cycle_annealing_temp` varchar(300) NOT NULL DEFAULT '',
  `cycle_annealing_method` enum('static','touchdown','gradient','other') DEFAULT NULL,
  `cycle_denaturation_duration` varchar(300) NOT NULL DEFAULT '',
  `cycle_denaturation_temp` varchar(300) NOT NULL DEFAULT '',
  `cycle_extension_duration` varchar(300) NOT NULL DEFAULT '',
  `cycle_extension_temp` varchar(300) NOT NULL DEFAULT '',
  `denaturation_duration_initial` varchar(300) NOT NULL DEFAULT '',
  `denaturation_temp_initial` varchar(300) NOT NULL DEFAULT '',
  `extension_duration_final` varchar(300) NOT NULL DEFAULT '',
  `extension_temp_final` varchar(300) NOT NULL DEFAULT '',
  `forward_primer_final_conc` varchar(300) NOT NULL DEFAULT '',
  `reverse_primer_final_conc` varchar(300) NOT NULL DEFAULT '',
  `dATP_final_conc` varchar(300) NOT NULL DEFAULT '',
  `dCTP_final_conc` varchar(300) NOT NULL DEFAULT '',
  `dGTP_final_conc` varchar(300) NOT NULL DEFAULT '',
  `dTTP_final_conc` varchar(300) NOT NULL DEFAULT '',
  `gelatin_final_conc` varchar(300) NOT NULL DEFAULT '',
  `BSA_final_conc` varchar(300) NOT NULL DEFAULT '',
  `KCl_final_conc` varchar(300) NOT NULL DEFAULT '',
  `MgCl2_final_conc` varchar(300) NOT NULL DEFAULT '',
  `Tris_HCl_final_conc` varchar(300) NOT NULL DEFAULT '',
  `library_institute` varchar(300) NOT NULL DEFAULT '',
  `library_notes` varchar(300) NOT NULL DEFAULT '',
  `local_NAP_ids` varchar(300) NOT NULL DEFAULT '',
  `NAP_volume` varchar(300) NOT NULL DEFAULT '',
  `pcr_clean_up_kits` varchar(300) NOT NULL DEFAULT '',
  `pcr_clean_up_methods` varchar(300) NOT NULL DEFAULT '',
  `pcr_notes` varchar(300) NOT NULL DEFAULT '',
  `pcr_replicates` varchar(300) NOT NULL DEFAULT '',
  `pcr_buffer_pH` varchar(300) NOT NULL DEFAULT '',
  `pcr_volume` varchar(300) NOT NULL DEFAULT '',
  `polymerase_units` varchar(300) NOT NULL DEFAULT '',
  `tail_polymerase` varchar(300) NOT NULL DEFAULT '',
  `tail_duration` varchar(300) NOT NULL DEFAULT '',
  `tail_temp` varchar(300) NOT NULL DEFAULT '',
  `other_additives` varchar(300) NOT NULL DEFAULT '',
  PRIMARY KEY (`SEQUENCE_PREP_ID`),
  KEY `IDX_SP_SEQ_METH` (`SEQUENCING_METH`),
  KEY `IDX_SP_SEQ_QUAL_CHK` (`SEQ_QUALITY_CHECK`),
  KEY `IDX_SP_CHIMERA_CHECK` (`CHIMERA_CHECK`),
  KEY `IDX_SEQ_PREP_ROW_NUM` (`ROW_INT`),
  KEY `IDX_SEQ_PREP_RNUM_SAMPID` (`SAMPLE_METADATA_ID`,`ROW_INT`),
  CONSTRAINT `FK_SPREP_TO_SAMPLE_SAMPLE_METADATA_ID` FOREIGN KEY (`SAMPLE_METADATA_ID`) REFERENCES `SAMPLE_METADATA` (`SAMPLE_METADATA_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
