-- MySQL dump 10.13  Distrib 5.5.18, for osx10.6 (i386)
--
-- Host: localhost    Database: mobedac
-- ------------------------------------------------------
-- Server version	5.5.18

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `analysis_request`
--

DROP TABLE IF EXISTS `analysis_request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `analysis_request` (
  `id` int(11) NOT NULL,
  `library_ids` varchar(1024) DEFAULT NULL,
  `user` varchar(45) DEFAULT NULL,
  `project_code` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `library`
--

DROP TABLE IF EXISTS `library`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `library` (
  `id` varchar(64) NOT NULL,
  `name` varchar(250) NOT NULL,
  `about` varchar(1024) DEFAULT NULL,
  `url` varchar(512) DEFAULT NULL,
  `version` int(11) NOT NULL,
  `creation` datetime NOT NULL,
  `metadata` mediumtext,
  `lib_type` varchar(256) DEFAULT NULL,
  `lib_insert_len` int(11) DEFAULT NULL,
  `sample_id` varchar(64) NOT NULL,
  `run_key` varchar(16) DEFAULT NULL,
  `primers` mediumtext,
  `direction` varchar(16) DEFAULT NULL,
  `region` varchar(32) DEFAULT NULL,
  `domain` varchar(45) DEFAULT NULL,
  `sequence_set_ids` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `sample_id` (`sample_id`),
  CONSTRAINT `library_ibfk_1` FOREIGN KEY (`sample_id`) REFERENCES `sample` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `primer`
--

DROP TABLE IF EXISTS `primer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `primer` (
  `primer_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `primer` varchar(16) NOT NULL DEFAULT '' COMMENT 'name of the sequencing primer',
  `direction` enum('F','R') NOT NULL COMMENT 'direction of priming, forward or reverse',
  `sequence` varchar(64) NOT NULL DEFAULT '' COMMENT 'primer sequence -- includes regular expressions for multiple bases or fuzzy matching',
  `region` varchar(16) NOT NULL DEFAULT '' COMMENT 'region of the genome being amplified',
  `original_seq` varchar(64) NOT NULL DEFAULT '' COMMENT 'primer sequence as ordered from the primer supply company',
  `domain` enum('bacteria','archaea','eukarya','') DEFAULT NULL,
  PRIMARY KEY (`primer_id`),
  UNIQUE KEY `primer` (`primer`)
) ENGINE=InnoDB AUTO_INCREMENT=259 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `primer_suite`
--

DROP TABLE IF EXISTS `primer_suite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `primer_suite` (
  `primer_suite_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `primer_suite` varchar(25) NOT NULL DEFAULT '',
  PRIMARY KEY (`primer_suite_id`),
  UNIQUE KEY `primer_suite` (`primer_suite`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `primer_vamps`
--

DROP TABLE IF EXISTS `primer_vamps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `primer_vamps` (
  `primer_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `primer` varchar(16) NOT NULL DEFAULT '' COMMENT 'name of the sequencing primer',
  `direction` enum('F','R') NOT NULL COMMENT 'direction of priming, forward or reverse',
  `sequence` varchar(64) NOT NULL DEFAULT '' COMMENT 'primer sequence -- includes regular expressions for multiple bases or fuzzy matching',
  `region` varchar(16) NOT NULL DEFAULT '' COMMENT 'region of the genome being amplified',
  `original_seq` varchar(64) NOT NULL DEFAULT '' COMMENT 'primer sequence as ordered from the primer supply company',
  `domain` enum('bacteria','archaea','eukarya','') DEFAULT NULL,
  PRIMARY KEY (`primer_id`),
  UNIQUE KEY `primer` (`primer`)
) ENGINE=InnoDB AUTO_INCREMENT=259 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` varchar(64) NOT NULL,
  `name` varchar(250) NOT NULL,
  `about` varchar(1024) DEFAULT NULL,
  `url` varchar(512) DEFAULT NULL,
  `version` int(11) NOT NULL,
  `creation` datetime NOT NULL,
  `metadata` mediumtext,
  `pi` varchar(256) NOT NULL DEFAULT 'JH',
  `funding_source` varchar(1024) DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_primer_suite_primer`
--

DROP TABLE IF EXISTS `ref_primer_suite_primer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ref_primer_suite_primer` (
  `primer_suite_id` smallint(5) unsigned NOT NULL,
  `primer_id` smallint(5) unsigned NOT NULL,
  KEY `primer_suite_id` (`primer_suite_id`),
  KEY `primer_id` (`primer_id`),
  CONSTRAINT `ref_primer_suite_primer_ibfk_1` FOREIGN KEY (`primer_suite_id`) REFERENCES `primer_suite` (`primer_suite_id`),
  CONSTRAINT `ref_primer_suite_primer_ibfk_2` FOREIGN KEY (`primer_id`) REFERENCES `primer_vamps` (`primer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sample`
--

DROP TABLE IF EXISTS `sample`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sample` (
  `id` varchar(64) NOT NULL,
  `name` varchar(250) NOT NULL,
  `about` varchar(1024) DEFAULT NULL,
  `url` varchar(512) DEFAULT NULL,
  `version` int(11) NOT NULL,
  `creation` datetime NOT NULL,
  `metadata` mediumtext,
  `project_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `sample_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sequenceset`
--

DROP TABLE IF EXISTS `sequenceset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sequenceset` (
  `id` varchar(64) NOT NULL,
  `name` varchar(250) NOT NULL,
  `about` varchar(1024) DEFAULT NULL,
  `url` varchar(512) DEFAULT NULL,
  `version` int(11) NOT NULL,
  `creation` datetime NOT NULL,
  `metadata` mediumtext,
  `type` varchar(256) DEFAULT NULL,
  `protein` varchar(45) DEFAULT NULL,
  `library_id` varchar(64) NOT NULL,
  `provenance` mediumtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  KEY `library_id` (`library_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submission`
--

DROP TABLE IF EXISTS `submission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `library_ids_str` varchar(1024) DEFAULT NULL,
  `analysis_params_str` varchar(1024) DEFAULT NULL,
  `user` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submission_details`
--

DROP TABLE IF EXISTS `submission_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submission_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `submission_id` int(11) DEFAULT NULL,
  `project_id` varchar(64) DEFAULT NULL,
  `sample_id` varchar(64) DEFAULT NULL,
  `library_id` varchar(64) DEFAULT NULL,
  `sequenceset_id` varchar(64) DEFAULT NULL,
  `vamps_project_name` varchar(64) DEFAULT NULL,
  `next_action` varchar(64) DEFAULT NULL,
  `vamps_status_record_id` varchar(45) DEFAULT NULL,
  `current_status_msg` varchar(512) DEFAULT NULL,
  `vamps_dataset_name` varchar(64) DEFAULT NULL,
  `region` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `submission_id` (`submission_id`),
  CONSTRAINT `submission_details_ibfk_2` FOREIGN KEY (`submission_id`) REFERENCES `submission` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-02-09 15:58:12
