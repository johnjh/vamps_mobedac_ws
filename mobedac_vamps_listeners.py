import cherrypy
import MySQLdb
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import MEDIUMTEXT
import sys
import traceback
import json
import time
from threading import Thread
from mycfg import *

projects = {'p1' : {'id' : 'p1', 'name': 'ICM_PRJ', 'about': 'This is projectG update2', 'url' : 'testurl', 'pi' : 'John Hufnagle',
        "funding_source" : "keck",
        "description" : "project S description",
"metadata":
    {
     "project_code" : "JJH_ICM",
    "project_funding":"European",
    "firstname":" - ",
    "PI_organization":"Division de Microbiologa, Universidad Miguel Hernndez",
    "PI_firstname":"Francisco",
    "PI_organization_url":"http://egg.umh.es/frvalera/",
    "lastname":" - ",
    "organization_url":" - ",
    "email":" - ",
    "PI_organization_address":"03550 San Juan de Alicante",
    "PI_organization_country":"Alicante, Spain",
    "organization_address":" - ",
    "organization_country":" - ",
    "PI_lastname":"Rodriguez-Valera",
    "project_description":"In general, a remarkable number of similarities were found with the deep meso-pelagic Pacific and a convergence at the level of taxa found and types of metabolism with the soil microbiota is starting to be perceived. The authors use the term \"invisible soil\" paraphrasing the \"invisible forest\" coined by Paul Falkowski to refer to the hidden but gigantic primary productivity found in the photic zone. The diversity of metabolic enzymes involved in resilient organic compounds degradation was very high. However, many microbes could complement their heterotrophic metabolism with chemolithotrophic energy supplies and, specifically in the Mediterranean, the oxidation of carbon monoxide, probably released by tectonic activity, could be important. There is also evidence that the microbes rarely live isolated. The free living planktonic lifestyle is probably not very popular in this extremely depleted environment. Quorum sensing genes indicate that instead, microbes tend to aggregate in particles and they could become luminescent maybe to attract and be eaten by animals. This strategy could provide the cells with a sporadic visit to the nutritious oasis of an animal gut. Overall, this paper shows that the deep ocean possesses a rich and mostly unknown microbiota that deserves much more studies.\r\n\r\nA recent analysis of a metagenomic library from the deep Mediterranean shows a surprising high number of quorum sensing or lux genes that are only expressed when bacteria live in colonies. The deep ocean might be too depleted in resources for microbes to live independently. Instead the association to detritus particles might give them a rich microenvironment. Now, some of the genes detected have been positively identified as luxA, directly involved in bioluminescence.\r\n\r\nWhy would deep sea bacteria be luminescent? One possible explanation is that they become attractive to animals that at these depths are very photosensitive. Being swallowed by one of these creatures would give the bacteria a temporary oasis of nutrient-rich conditions before another long dip in the abyssal black.",
    "PI_email":"frvalera@umh.es",
    "organization":" - "}
   }}

samples = {'s1' : {'id' : 's1',  'name': 'Sample1', 'about': 'This is sample', 'url' : 'testurl', "project" : "p1",
"metadata":
    {
    "sample1":"European",
  "STUDY_ID"  : {"value" : "1"},
  "SAMPLE_NAME" : {"value" : "s1"},
  "PUBLIC"  : {"value" : "3"},
  "ASSIGNED_FROM_GEO"  : {"value" : "4"},
  "ALTITUDE" : {"value" : "5"},
  "CHEM_ADMINISTRATION"  : {"value" : "6"},
  "COLLECTION_DATE" : {"value" : "7"},
  "COUNTRY" : {"value" : "8"},
  "DEPTH"  : {"value" : "9"},
  "ELEVATION" : {"value" : "10"},
  "ENV_BIOME" : {"value" : "1"},
  "ENV_FEATURE" : {"value" : "2"},
  "ENV_MATTER" : {"value" : "3"},
  "ORGANISM_COUNT" : {"value" : "4"},
  "OXY_STAT_SAMP"  : {"value" : "5"},
  "PERTURBATION"  : {"value" : "6"},
  "PH" : {"value" : "7"},
  "LATITUDE" : {"value" : "8"},
  "LONGITUDE" : {"value" : "9"},
  "SAMP_COLLECT_DEVICE" : {"value" : "10"},
  "SAMP_MAT_PROCESS" : {"value" : "1"},
  "SAMP_SALINITY" : {"value" : "2"},
  "SAMP_SIZE" : {"value" : "3"},
  "SAMP_STORE_DUR" : {"value" : "4"},
  "SAMP_STORE_LOC" : {"value" : "5"},
  "SAMP_STORE_TEMP" : {"value" : "6"},
  "TEMP" : {"value" : "7"},
  "TITLE" : {"value" : "8"},
  "TAXON_ID"  : {"value" : "9"},
  "COMMON_NAME" : {"value" : "10"},
  "ANONYMIZED_NAME" : {"value" : "1"},
  "DESCRIPTION"  : {"value" : "2"},   

  # the COMMON fields
  "ALKALINITY" : {"value" : "2"},
  "ALKYL_DIETHERS" : {"value" : "2.1"},
  "AMINOPEPT_ACT" : {"value" : "2.1"},
  "AMMONIUM" : {"value" : "2.1"},
  "BACTERIA_CARB_PROD" : {"value" : "2.1"},
  "BIOMASS" : {"value" : "big"},
  "BISHOMOHOPANOL" : {"value" : "2.3"},
  "BROMIDE" : {"value" : "2.5"},
  "CALCIUM" : {"value" : "2.6"},
  "CARB_NITRO_RATIO" : {"value" : "2.7"},
  "CHLORIDE" : {"value" : "2.8"},
  "CHLOROPHYLL" : {"value" : "2.9"},
  "CURRENT" : {"value" : "2.1"},
  "DENSITY" : {"value" : "2.2"},
  "DIETHER_LIPIDS" : {"value" : "many fats"},
  "DISS_CARB_DIOXIDE" : {"value" : "2.3"},
  "DISS_HYDROGEN" : {"value" : "2.4"},
  "DISS_ORG_CARBON" : {"value" : "2.5"},
  "DISS_OXYGEN" : {"value" : "2.6"},
  "GLUCOSIDASE_ACT" : {"value" : "2.7"},
  "MAGNESIUM" : {"value" : "2.8"},
  "MEAN_FRICT_VEL" : {"value" : "2.9"},
  "MEAN_PEAK_FRICT_VEL" : {"value" : "2.1"},
  "METHANE" : {"value" : "2.2"},
  "N_ALKANES" : {"value" : "2.3"},
  "NITRATE" : {"value" : "2.4"},
  "NITRITE" : {"value" : "2.5"},
  "NITRO" : {"value" : "2.6"},
  "ORG_CARB" : {"value" : "2.7"},
  "ORG_MATTER" : {"value" : "2.8"},
  "ORG_NITRO" : {"value" : "2.9"},
  "ORGANISM_COUNT" : {"value" : "lots of bugs and stuff"},
  "OXYGEN" : {"value" : "2.1"},
  "PART_ORG_CARB" : {"value" : "2.2"},
  "PETROLEUM_HYDROCARB" : {"value" : "2.3"},
  "PH" : {"value" : "2.4"},
  "PHAEOPIGMENTS" : {"value" : "red green yellow"},
  "PHOSPHATE" : {"value" : "2.5"},
  "PHOSPLIPID_FATT_ACID" : {"value" : "fat and more fat"},
  "POTASSIUM" : {"value" : "2.6"},
  "PRESS" : {"value" : "2.7"},
  "REDOX_POTENTIAL" : {"value" : "2.8"},
  "SALINITY" : {"value" : "2.9"},
  "SILICATE" : {"value" : "2.1"},
  "SULFATE" : {"value" : "2.2"},
  "SULFIDE" : {"value" : "2.3"},
  "TOT_CARB" : {"value" : "2.4"},
  "TOT_NITRO" : {"value" : "2.5"},
  "TOT_ORG_CARB" : {"value" : "2.6"},
  "TURBIDITY" : {"value" : "2.7"},
  "WATER_CONTENT"  : {"value" : "2.8"},


#human gut
"gastrointest_disord" : {"value" : "none"},
"liver_disord" : {"value" : "none"},
"special_diet" : {"value" : "none"},
"host_subject_id" : {"value" : "johnh"},
"host_subject_id" : {"value" : "johnh"},
"host_subject_id" : {"value" : "johnh"},
"age" : {"value" : "23"},
"sex" : {"value" : "male"},
"disease_stat" : {"value" : "none"},
"ihmc_medication_code" : {"value" : "23"},
"chem_administration" : {"value" : "233"},
"body_site" : {"value" : "chest"},
"body_product" : {"value" : "product"},
"tot_mass" : {"value" : "333"},
"height" : {"value" : "233"},
"diet" : {"value" : "food"},
"last_meal" : {"value" : "beans"},
"family_relationship" : {"value" : "good"},
"genotype" : {"value" : "freckles"},
"phenotype" : {"value" : "recessive"},
"host_body_temp" : {"value" : "98.6"},
"body_mass_index" : {"value" : "2.0"},
"ihmc_ethnicity" : {"value" : "22"},
"occupation" : {"value" : "programmer"},
"medic_hist_perform" : {"value" : "3"},
"pulse" : {"value" : "80"},
"perturbation" : {"value" : "2"},
"samp_salinity" : {"value" : "2.3"},
"oxy_stat_samp" : {"value" : "2"},
"organism_count" : {"value" : "2"},
"samp_store_temp" : {"value" : "2"},
"samp_store_dur" : {"value" : "long time"},
"samp_store_loc" : {"value" : "closet"},
"misc_param" : {"value" : "2"},



# human associated
#"hide_human_associated" :
#{
  "BODY_MASS_INDEX" : {"value" : "2.1"},
  "DRUG_USAGE" : {"value" : "no"},
  "HIV_STAT"  : {"value" : "0"},
  "IHMC_ETHNICITY" : {"value" : "white"},
# skip...foreign key type
#  "IHMC_OCCUPATION"  : {"value" : "programmer"},
  "LAST_MEAL" : {"value" : "turkey"},
  "DIET_LAST_SIX_MONTH" : {"value" : "yes"},
  "MEDIC_HIST_PERFORM"  : {"value" : "1"},
  "PET_FARM_ANIMAL" : {"value" : "pigs"},
  "PULSE" : {"value" : "80"},
  "SMOKER"  : {"value" : "0"},
  "TRAVEL_OUT_SIX_MONTH" : {"value" : "no"},
  "TWIN_SIBLING"  : {"value" : "0"},
  "WEIGHT_LOSS_3_MONTH" : {"value" : "4"},
  "NOSE_THROAT_DISORD" : {"value" : "none"},
  "PULMONARY_DISORD" : {"value" : "none"},
# skip...is a foreign key
#  "STUDY_COMPLT_STAT"  : {"value" : ""},
  "AMNIOTIC_FLUID_COLOR"  : {"value" : "clear"},
  "GESTATION_STATE" : {"value" : "large"},
  "FOETAL_HEALTH_STAT" : {"value" : "excellent"},
  "MATERNAL_HEALTH_STAT" : {"value" : "excellent"},
  "BLOOD_DISORD" : {"value" : "none"},
  "GASTROINTEST_DISORD" : {"value" : "none"},
  "LIVER_DISORD" : {"value" : "none"},
  "SPECIAL_DIET" : {"value" : "chocolate...and lots of it"},
  "NOSE_MOUTH_TEETH_THROAT_DISORD" : {"value" : "should floss more"},
  "TIME_LAST_TOOTHBRUSH" : {"value" : "5.0"},
  "DERMATOLOGY_DISORD" : {"value" : "none"},
  "DOMINANT_HAND"  : {"value" : "right"},
  "TIME_SINCE_LAST_WASH" : {"value" : "1"},
  "KIDNEY_DISORD" : {"value" : "none"},
# skip for now
#  "URINE_COLLECT_METH"  : {"value" : "clear catch"},
  "UROGENIT_TRACT_DISOR" : {"value" : "none"},
  "BIRTH_CONTROL"  : {"value" : "yes...just say no!"},
  "DOUCHE" : {"value" : "2012-01-01"},
  "GYNECOLOGIC_DISORD" : {"value" : "none"},
  "MENARCHE" : {"value" : "2012-01-01"},
  "HRT" : {"value" : "2012-01-01"},
  "HYSTERECTOMY"  : {"value" : "0"},
  "MENOPAUSE" : {"value" : "2012-01-01"},
  "PREGNANCY" : {"value" : "2012-01-01"},
  "SEXUAL_ACT" : {"value" : "none"},
  "UROGENIT_DISORD" : {"value" : "none"}
,#},
     
       
# HOST_ASSOC_VERTIBRATE these hidden ones aren't in the field map so they will be skipped
#"Hide_HOST_ASSOC_VERTIBRATE" :
#{
  "BODY_HABITAT" : {"value" : "habitat"},
  "BODY_SITE" : {"value" : "site"},
  "BODY_PRODUCT" : {"value" : "product"},
  "BLOOD_PRESS_DIAST" : {"value" : "120"},
  "BLOOD_PRESS_SYST" : {"value" : "80"},
  "HOST_BODY_TEMP" : {"value" : "98.6"},
  "DIET"  : {"value" : "mcdonalds"},
  "FAMILY_RELATIONSHIP" : {"value" : "good"},
  "MEDICATIONS" : {"value" : "garlic"},
  "GRAVIDITY"  : {"value" : "0"},
  "GRAVIDITY_DUE_DATE" : {"value" : "2012-01-01"},
  "HOST_GROWTH_COND" : {"value" : "growth"},
  "LAST_MEAL" : {"value" : "turkey"},
  "SCIENTIFIC_NAME" : {"value" : "food"},
# controlled vocab..skip for now
#  "SEX"  : {},
  "SUBSTRATE" : {"value" : "metal"},
  "TIME_SINCE_LAST_MEDICATION" : {"value" : "2.0"},
  "DATE_OF_BIRTH" : {"value" : "2012-01-01"}
,#},

  
  # the AIR specific fields
"hide_air" :
{
  "BAROMETRIC_PRESS" : {"value" : "23.4"},
  "CARB_DIOXIDE" : {"value" : "2.2"},
  "CARB_MONOXIDE" : {"value" : "2.6"},
  "HUMIDITY" : {"value" : "5.6"},
  "POLLUTANTS" : {"value" : "smog, ozone and more"},
  "RESP_PART_MATTER" : {"value" : "lots of bad stuff"},
  "SOLAR_IRRADIANCE" : {"value" : "55.66"},
  "VENTILATION_RATE" : {"value" : "77.88"},
  "VENTILATION_TYPE" : {"value" : "fans"},
  "VOLATILE_ORG_COMP" : {"value" : "benzene and other bad stuff"},
  "WIND_DIRECTION"  : {"value" : "270"},
  "WIND_SPEED"   : {"value" : "66.66"}
}  
   }
   }}

libraries = {
             'l1' : { 'id' : 'l1',
         'name': 'Library1',
         'about': 'This is sample', 
         'url' : 'testurl', 
         'lib_type' : 'solo', 
         'lib_insert_len' : 0,
         "sample" : "s1",
#         "sequence_sets" : ["icml1"],
         "sequence_sets" : [{"stage_name":"upload","file_name":"60410.fastq.gz","stage_type":"fastq","id":"mgm4492980.3-050-1","stage_id":"050"},{"stage_name":"upload","file_name":"60410.fna.gz","stage_type":"fna","id":"mgm4492980.3-050-2","stage_id":"050"},{"stage_name":"preprocess","file_name":"100.preprocess.passed.fna.gz","stage_type":"passed","id":"mgm4492980.3-100-1","stage_id":"100"},{"stage_name":"preprocess","file_name":"100.preprocess.removed.fna.gz","stage_type":"removed","id":"mgm4492980.3-100-2","stage_id":"100"},{"stage_name":"dereplication","file_name":"150.dereplication.passed.fna.gz","stage_type":"passed","id":"mgm4492980.3-150-1","stage_id":"150"},{"stage_name":"dereplication","file_name":"150.dereplication.removed.fna.gz","stage_type":"removed","id":"mgm4492980.3-150-2","stage_id":"150"},{"stage_name":"screen","file_name":"299.screen.passed.fna.gz","stage_type":"passed","id":"mgm4492980.3-299-1","stage_id":"299"},{"stage_name":"genecalling","file_name":"350.genecalling.coding.faa.gz","stage_type":"coding","id":"mgm4492980.3-350-1","stage_id":"350"},{"stage_name":"genecalling","file_name":"350.genecalling.coding.fna.gz","stage_type":"coding","id":"mgm4492980.3-350-2","stage_id":"350"},{"stage_name":"search","file_name":"425.search.rna.fna.gz","stage_type":"rna","id":"mgm4492980.3-425-1","stage_id":"425"},{"stage_name":"cluster","file_name":"440.cluster.rna97.fna.gz","stage_type":"rna97","id":"mgm4492980.3-440-1","stage_id":"440"},{"stage_name":"cluster","file_name":"550.cluster.aa90.faa.gz","stage_type":"aa90","id":"mgm4492980.3-550-1","stage_id":"550"}],
         "metadata":
                {
# "run_key" : "CTACT",  
# "direction" : "F",  
# "domain" : "Archeal",
# "region" : "v6",
# "num_primers" : "2", 
# "primer_1_name" : "1048R", "primer_1_direction" : "R", "primer_1_sequence" : "GWGGTRCATGGCY?GY?CG", "primer_1_region" : "v6", "primer_1_location" : "1048R" ,
# "primer_2_name" : "958F", "primer_2_direction" : "F", "primer_2_sequence" : "AATTGGA.?TCAACGCC.G", "primer_2_region" : "v6", "primer_2_location" : "958F",
#                "library1":"European",

        "forward_barcodes": {"value" : "GCTTGCTT"}, #run_key
        "target_subfragment": {"value" : "V2V3"},   #dna_region
        "seq_chem": {"value" : "GS FLX Titanium"},
        "seq_meth": {"value" : "454"},
        "seq_center": {"value" : "engencore"},
        "domain": {"value" : "Bacteria"},           #domain
        "target_gene": {"value" : "16S rRNA"},
        "metagenome_name": {"value" : "M4"},
        "seq_direction": {"value" : "forward"},     #direction
        "sample_name": {"value" : "M4"},
        "investigation_type": {"value" : "mimarks-survey"},
        "forward_primers": {"value" : "AATTGGA.?TCAACGCC.G,CAACGCGAAGAACCTTACC"}, #primers
        "reverse_primers": {"value" : "GWGGTRCATGGCY?GY?CG"},

#sequence_prep metadata
      "NUCL_ACID_EXT" : {"value" : "NUCL_ACID_EXT"},
      "NUCL_ACID_AMP" : {"value" : "NUCL_ACID_AMP"},
      "LIB_SIZE"  : {"value" : "23232323232323"},
      "LIB_READS_SEQD" : {"value" : "23232323232323"},
      "LIB_VECTOR" : {"value" : "LIB_VECTOR"},
      "LIBR_SCREEN" : {"value" : "LIBR_SCREEN"},
      "TARGET_GENE" : {"value" : "TARGET_GENE"},
      "TARGET_SUBFRAGMENT" : {"value" : "TARGET_SUBFRAGMENT"},
      "PCR_PRIMERS" : {"value" : "PCR_PRIMERS"},
      "MULTIPLEX_IDENT" : {"value" : "MULTIPLEX_IDENT"},
      "PCR_COND" : {"value" : "PCR_COND"},
      "SEQUENCING_METH" : {"value" : "SEQUENCING_METH"},
      "SEQ_QUALITY_CHECK" : {"value" : "333"},
      "CHIMERA_CHECK" : {"value" : "2222"},
      "SOP" : {"value" : "SOP"},
      "URL" : {"value" : "URL"},
      "EXPERIMENT_ALIAS" : {"value" : "EXPERIMENT_ALIAS"},
      "EXPERIMENT_CENTER" : {"value" : "EXPERIMENT_CENTER"},
      "EXPERIMENT_TITLE" : {"value" : "EXPERIMENT_TITLE"},
      "EXPERIMENT_ACCESSION" : {"value" : "EXPERIMENT_ACCESSION"},
      "STUDY_ACCESSION" : {"value" : "STUDY_ACCESSION"},
      "STUDY_REF" : {"value" : "STUDY_REF"},
      "STUDY_CENTER" : {"value" : "STUDY_CENTER"},
      "EXPERIMENT_DESIGN_DESCRIPTION" : {"value" : "EXPERIMENT_DESIGN_DESCRIPTION"},
      "LIBRARY_CONSTRUCTION_PROTOCOL" : {"value" : "LIBRARY_CONSTRUCTION_PROTOCOL"},
      "SAMPLE_ACCESSION" : {"value" : "SAMPLE_ACCESSION"},
      "SAMPLE_ALIAS" : {"value" : "SAMPLE_ALIAS"},
      "SAMPLE_CENTER" : {"value" : "SAMPLE_CENTER"},
      "POOL_MEMBER_ACCESSION" : {"value" : "POOL_MEMBER_ACCESSION"},
      "POOL_MEMBER_NAME" : {"value" : "POOL_MEMBER_NAME"},
      "POOL_PROPORTION" : {"value" : "POOL_PROPORTION"},
      "BARCODE_READ_GROUP_TAG" : {"value" : "BARCODE_READ_GROUP_TAG"},
      "BARCODE" : {"value" : "BARCODE"},
      "LINKER" : {"value" : "LINKER"},
      "KEY_SEQ" : {"value" : "KEY_SEQ"},
      "PRIMER_READ_GROUP_TAG" : {"value" : "PRIMER_READ_GROUP_TAG"},
      "PRIMER" : {"value" : "PRIMER"},
      "RUN_PREFIX" : {"value" : "RUN_PREFIX"},
      "REGION" : {"value" : "REGION"},
      "PLATFORM" : {"value" : "PLATFORM"},
      "RUN_ACCESSION" : {"value" : "RUN_ACCESSION"},
      "RUN_ALIAS" : {"value" : "RUN_ALIAS"},
      "RUN_CENTER" : {"value" : "RUN_CENTER"},
      "RUN_DATE" : {"value" : "RUN_DATE"},
      "INSTRUMENT_NAME" : {"value" : "INSTRUMENT_NAME"},
      "LIBRARY_STRATEGY" : {"value" : "LIBRARY_STRATEGY"},
      "LIBRARY_SOURCE" : {"value" : "LIBRARY_SOURCE"},
      "LIBRARY_SELECTION" : {"value" : "LIBRARY_SELECTION"},
  "ROW_INT" :  {"value" : "22"}                
                }
        },
             'l2' : { 'id' : 'l2',
         'name': 'Library2',
         'about': 'This is sample', 
         'url' : 'testurl', 
         'lib_type' : 'solo', 
         'lib_insert_len' : 0,
         "sample" : "s1",
         "sequence_sets" : ["icml2"],
         "metadata":
                {
# "run_key" : "CTACT",  
# "direction" : "F",  
# "domain" : "Bacterial",
# "region" : "v6",
# "num_primers" : "2", 
# "primer_1_name" : "1048R", "primer_1_direction" : "R", "primer_1_sequence" : "GWGGTRCATGGCY?GY?CG", "primer_1_region" : "v6", "primer_1_location" : "1048R" ,
# "primer_2_name" : "958F", "primer_2_direction" : "F", "primer_2_sequence" : "AATTGGA.?TCAACGCC.G", "primer_2_region" : "v6", "primer_2_location" : "958F",
#                "library1":"European",
        "forward_barcodes": {"value" : "GCTTGCTT"}, #run_key
        "target_subfragment": {"value" : "V2V3"},   #dna_region
        "seq_chem": {"value" : "GS FLX Titanium"},
        "seq_meth": {"value" : "454"},
        "seq_center": {"value" : "engencore"},
        "domain": {"value" : "Bacteria"},           #domain
        "target_gene": {"value" : "16S rRNA"},
        "metagenome_name": {"value" : "M4"},
        "seq_direction": {"value" : "forward"},     #direction
        "sample_name": {"value" : "M4"},
        "investigation_type": {"value" : "mimarks-survey"},
        "forward_primers": {"value" : "AATTGGA.?TCAACGCC.G,CAACGCGAAGAACCTTACC"}, #primers
        "reverse_primers": {"value" : "GWGGTRCATGGCY?GY?CG"},                
#sequence_prep metadata
  "NUCL_ACID_EXT" : {"value" : "2NUCL_ACID_EXT"},
  "NUCL_ACID_AMP" : {"value" : "2NUCL_ACID_AMP"},
  "LIB_SIZE"  : {"value" : "223232323232323"},
  "LIB_READS_SEQD" : {"value" : "223232323232323"},
  "LIB_VECTOR" : {"value" : "2LIB_VECTOR"},
  "LIBR_SCREEN" : {"value" : "2LIBR_SCREEN"},
  "TARGET_GENE" : {"value" : "2TARGET_GENE"},
  "TARGET_SUBFRAGMENT" : {"value" : "2TARGET_SUBFRAGMENT"},
  "PCR_PRIMERS" : {"value" : "2PCR_PRIMERS"},
  "MULTIPLEX_IDENT" : {"value" : "2MULTIPLEX_IDENT"},
  "PCR_COND" : {"value" : "2PCR_COND"},
  "SEQUENCING_METH" : {"value" : "2SEQUENCING_METH"},
  "SEQ_QUALITY_CHECK" : {"value" : "2333"},
  "CHIMERA_CHECK" : {"value" : "22222"},
  "SOP" : {"value" : "2SOP"},
  "URL" : {"value" : "2URL"},
  "EXPERIMENT_ALIAS" : {"value" : "2EXPERIMENT_ALIAS"},
  "EXPERIMENT_CENTER" : {"value" : "2EXPERIMENT_CENTER"},
  "EXPERIMENT_TITLE" : {"value" : "2EXPERIMENT_TITLE"},
  "EXPERIMENT_ACCESSION" : {"value" : "2EXPERIMENT_ACCESSION"},
  "STUDY_ACCESSION" : {"value" : "2STUDY_ACCESSION"},
  "STUDY_REF" : {"value" : "2STUDY_REF"},
  "STUDY_CENTER" : {"value" : "2STUDY_CENTER"},
  "EXPERIMENT_DESIGN_DESCRIPTION" : {"value" : "2EXPERIMENT_DESIGN_DESCRIPTION"},
  "LIBRARY_CONSTRUCTION_PROTOCOL" : {"value" : "2LIBRARY_CONSTRUCTION_PROTOCOL"},
  "SAMPLE_ACCESSION" : {"value" : "2SAMPLE_ACCESSION"},
  "SAMPLE_ALIAS" : {"value" : "2SAMPLE_ALIAS"},
  "SAMPLE_CENTER" : {"value" : "2SAMPLE_CENTER"},
  "POOL_MEMBER_ACCESSION" : {"value" : "2POOL_MEMBER_ACCESSION"},
  "POOL_MEMBER_NAME" : {"value" : "2POOL_MEMBER_NAME"},
  "POOL_PROPORTION" : {"value" : "2POOL_PROPORTION"},
  "BARCODE_READ_GROUP_TAG" : {"value" : "2BARCODE_READ_GROUP_TAG"},
  "BARCODE" : {"value" : "2BARCODE"},
  "LINKER" : {"value" : "2LINKER"},
  "KEY_SEQ" : {"value" : "2KEY_SEQ"},
  "PRIMER_READ_GROUP_TAG" : {"value" : "2PRIMER_READ_GROUP_TAG"},
  "PRIMER" : {"value" : "2PRIMER"},
  "RUN_PREFIX" : {"value" : "2RUN_PREFIX"},
  "REGION" : {"value" : "2REGION"},
  "PLATFORM" : {"value" : "2PLATFORM"},
  "RUN_ACCESSION" : {"value" : "2RUN_ACCESSION"},
  "RUN_ALIAS" : {"value" : "2RUN_ALIAS"},
  "RUN_CENTER" : {"value" : "2RUN_CENTER"},
  "RUN_DATE" : {"value" : "2RUN_DATE"},
  "INSTRUMENT_NAME" : {"value" : "2INSTRUMENT_NAME"},
  "LIBRARY_STRATEGY" : {"value" : "2LIBRARY_STRATEGY"},
  "LIBRARY_SOURCE" : {"value" : "2LIBRARY_SOURCE"},
  "LIBRARY_SELECTION" : {"value" : "2LIBRARY_SELECTION"},
  "ROW_INT" :  {"value" : "22"}                
                
                }
        },
             'l3' : { 'id' : 'l3',
         'name': 'Library3',
         'about': 'This is sample', 
         'url' : 'testurl', 
         'lib_type' : 'solo', 
         'lib_insert_len' : 0,
         "sample" : "s1",
         "sequence_sets" : ["icml3"],
         "metadata":
                {
# "run_key" : "CTACT",  
# "direction" : "F",  
# "domain" : "Archeal",
# "region" : "v6",
# "num_primers" : "2", 
# "primer_1_name" : "1048R", "primer_1_direction" : "R", "primer_1_sequence" : "GWGGTRCATGGCY?GY?CG", "primer_1_region" : "v6", "primer_1_location" : "1048R" ,
# "primer_2_name" : "958F", "primer_2_direction" : "F", "primer_2_sequence" : "AATTGGA.?TCAACGCC.G", "primer_2_region" : "v6", "primer_2_location" : "958F",
#                "library1":"European",
                "forward_barcodes": {"value" : "GCTTGCTT"}, #run_key
                "target_subfragment": {"value" : "V2V3"},   #dna_region
                "seq_chem": {"value" : "GS FLX Titanium"},
                "seq_meth": {"value" : "454"},
                "seq_center": {"value" : "engencore"},
                "domain": {"value" : "Bacteria"},           #domain
                "target_gene": {"value" : "16S rRNA"},
                "metagenome_name": {"value" : "M4"},
                "seq_direction": {"value" : "forward"},     #direction
                "sample_name": {"value" : "M4"},
                "investigation_type": {"value" : "mimarks-survey"},
                "forward_primers": {"value" : "AATTGGA.?TCAACGCC.G,CAACGCGAAGAACCTTACC"}, #primers
                "reverse_primers": {"value" : "GWGGTRCATGGCY?GY?CG"},                
#sequence_prep metadata
  "NUCL_ACID_EXT" : {"value" : "32NUCL_ACID_EXT"},
  "NUCL_ACID_AMP" : {"value" : "32NUCL_ACID_AMP"},
  "LIB_SIZE"  : {"value" : "3223232323232323"},
  "LIB_READS_SEQD" : {"value" : "3223232323232323"},
  "LIB_VECTOR" : {"value" : "32LIB_VECTOR"},
  "LIBR_SCREEN" : {"value" : "32LIBR_SCREEN"},
  "TARGET_GENE" : {"value" : "32TARGET_GENE"},
  "TARGET_SUBFRAGMENT" : {"value" : "32TARGET_SUBFRAGMENT"},
  "PCR_PRIMERS" : {"value" : "32PCR_PRIMERS"},
  "MULTIPLEX_IDENT" : {"value" : "32MULTIPLEX_IDENT"},
  "PCR_COND" : {"value" : "32PCR_COND"},
  "SEQUENCING_METH" : {"value" : "32SEQUENCING_METH"},
  "SEQ_QUALITY_CHECK" : {"value" : "32333"},
  "CHIMERA_CHECK" : {"value" : "322222"},
  "SOP" : {"value" : "32SOP"},
  "URL" : {"value" : "32URL"},
  "EXPERIMENT_ALIAS" : {"value" : "32EXPERIMENT_ALIAS"},
  "EXPERIMENT_CENTER" : {"value" : "32EXPERIMENT_CENTER"},
  "EXPERIMENT_TITLE" : {"value" : "32EXPERIMENT_TITLE"},
  "EXPERIMENT_ACCESSION" : {"value" : "32EXPERIMENT_ACCESSION"},
  "STUDY_ACCESSION" : {"value" : "32STUDY_ACCESSION"},
  "STUDY_REF" : {"value" : "32STUDY_REF"},
  "STUDY_CENTER" : {"value" : "32STUDY_CENTER"},
  "EXPERIMENT_DESIGN_DESCRIPTION" : {"value" : "32EXPERIMENT_DESIGN_DESCRIPTION"},
  "LIBRARY_CONSTRUCTION_PROTOCOL" : {"value" : "32LIBRARY_CONSTRUCTION_PROTOCOL"},
  "SAMPLE_ACCESSION" : {"value" : "32SAMPLE_ACCESSION"},
  "SAMPLE_ALIAS" : {"value" : "32SAMPLE_ALIAS"},
  "SAMPLE_CENTER" : {"value" : "32SAMPLE_CENTER"},
  "POOL_MEMBER_ACCESSION" : {"value" : "32POOL_MEMBER_ACCESSION"},
  "POOL_MEMBER_NAME" : {"value" : "32POOL_MEMBER_NAME"},
  "POOL_PROPORTION" : {"value" : "32POOL_PROPORTION"},
  "BARCODE_READ_GROUP_TAG" : {"value" : "32BARCODE_READ_GROUP_TAG"},
  "BARCODE" : {"value" : "32BARCODE"},
  "LINKER" : {"value" : "32LINKER"},
  "KEY_SEQ" : {"value" : "32KEY_SEQ"},
  "PRIMER_READ_GROUP_TAG" : {"value" : "32PRIMER_READ_GROUP_TAG"},
  "PRIMER" : {"value" : "32PRIMER"},
  "RUN_PREFIX" : {"value" : "32RUN_PREFIX"},
  "REGION" : {"value" : "32REGION"},
  "PLATFORM" : {"value" : "32PLATFORM"},
  "RUN_ACCESSION" : {"value" : "32RUN_ACCESSION"},
  "RUN_ALIAS" : {"value" : "32RUN_ALIAS"},
  "RUN_CENTER" : {"value" : "32RUN_CENTER"},
  "RUN_DATE" : {"value" : "32RUN_DATE"},
  "INSTRUMENT_NAME" : {"value" : "32INSTRUMENT_NAME"},
  "LIBRARY_STRATEGY" : {"value" : "32LIBRARY_STRATEGY"},
  "LIBRARY_SOURCE" : {"value" : "32LIBRARY_SOURCE"},
  "LIBRARY_SELECTION" : {"value" : "32LIBRARY_SELECTION"},
  "ROW_INT" :  {"value" : "322"}                
                
                }
        }
             
             }

sequencesets = {
                'icml1' : {'id' : 'icml1', 'name': 'SequenceSet1', 'about': 'This is sample', 'url' : 'testurl', 'library_id' : "l1", 'type' : 'reads', 'protein' : True, 'provenance' : "don't know the provenance",
    "sequences" : "http://localhost:8081/mobedac/sequencefile/icml1",
    "metadata":
        {
        "sequenceset1":"European"}
       },
                'icml2' : {'id' : 'icml2', 'name': 'SequenceSet1', 'about': 'This is sample', 'url' : 'testurl', 'library_id' : "l2", 'type' : 'reads', 'protein' : True, 'provenance' : "don't know the provenance",
    "sequences" : "http://localhost:8081/mobedac/sequencefile/icml2",
    "metadata":
        {
        "sequenceset1":"European"}
       },
                'icml3' : {'id' : 'icml3', 'name': 'SequenceSet1', 'about': 'This is sample', 'url' : 'testurl', 'library_id' : "l3", 'type' : 'reads', 'protein' : True, 'provenance' : "don't know the provenance",
    "sequences" : "http://localhost:8081/mobedac/sequencefile/icml3",
    "metadata":
        {
        "sequenceset1":"European"}
       }
                }

sequencefiles_by_types = {
                "sff_large" : 
                {'icml1' : {'name' : work_path_local+'/src/icml1.sff_large',
                            'format' : "sff"}
                 },
                "sff_small" : 
                {'icml1' : {'name' : work_path_local+'/src/icml1.sff_small',
                            'format' : "sff"}
                 },
                "fastq_small" : 
                {'icml1' : {'name' : work_path_local+'/src/icml1.fastq_small',
                            'format' : "fastq"}
                 },
                "fastq_large" : 
                {'icml1' : {'name' : work_path_local+'/src/icml1.fastq_large',
                            'format' : "fastq"}
                 },
                "fasta" : 
                {'icml1' : {'name' : work_path_local+'/src/icml1.fa',
                            'format' : "fasta"},
                 'icml2' : {'name' : work_path_local+'/src/icml2.fa',
                            'format' : "fasta"},
                 'icml3' : {'name' : work_path_local+'/src/icml3.fa',
                            'format' : "fasta"}
                 }
                }
sequencefiles = None

# This is a very important array
# This array will contain the names of each function below that got called
# by the API server.  In this way during a test run we tell the API server to 
# process a request and it calls over here to these 2 listeners who imitate MOBEDAC and VAMPS
# The test_gast_taxtable.py test script check to make sure that these 2 listeners got the correct
# number of calls made to them in order to have correctly handled a submission request.
requests_array = []

class VampsListener():
    
    # this method pretends to be the URL that would be called by our api on the VAMPS server
    # for upload of data with a qual file
    @cherrypy.expose
    def upload_data_post_with_qual_file(self, seqfile, primfile, keyfile, paramfile, qualfile):
        global requests_array
        requests_array.append("upload_data_post")
        # create the row in VAMPS db
        dbConn = MySQLdb.connect("localhost", db_user_local, db_passw_local,"vamps_test" )
        cursor = dbConn.cursor()
        cursor.execute("insert into vamps_upload_status(user, status, status_message) values ('mobedac', 'TRIM_PROCESSING', 'Vamps is processing');")
        status_id = dbConn.insert_id()
        dbConn.commit()
        dbConn.close()
        return str(status_id)

    # this method pretends to be the URL that would be called by our api on the VAMPS server
    # for upload of data without a qual file
    @cherrypy.expose
    def upload_data_post(self, seqfile, primfile, keyfile, paramfile):
        global requests_array
        requests_array.append("upload_data_post")
        # create the row in VAMPS db
        dbConn = MySQLdb.connect("localhost", db_user_local, db_passw_local,"vamps_test" )
        cursor = dbConn.cursor()
        cursor.execute("insert into vamps_upload_status(user, status, status_message) values ('mobedac', 'TRIM_PROCESSING', 'Vamps is processing');")
        status_id = dbConn.insert_id()
        dbConn.commit()
        dbConn.close()
        return str(status_id)

    # this method pretends to be the URL that would be called by our api on the VAMPS server
    # for GASTing
    @cherrypy.expose
    def upload_data_gast(self, *vpath, **params):
        global requests_array
        requests_array.append("upload_data_gast")
        dbConn = MySQLdb.connect("localhost", db_user_local, db_passw_local,"vamps_test" )
        cursor = dbConn.cursor()
        sql = "UPDATE vamps_upload_status SET status='GAST_PROCESSING' WHERE id in (" + params['run_number'].replace("[","").replace("]","") + ");"
        print "updating gast processing vamps upload status with sql: " + sql
        cursor.execute(sql)
        dbConn.commit()
        dbConn.close()
        # find the vamps_upload_status record
        return "in VampsListener upload_data_gast"

    # this method pretends to be the URL that would be called by our api on the VAMPS server
    # for generating a tax table in the special biom sparse format
    @cherrypy.expose
    def generate_taxonomy_table(self, *vpath, **params):
        global requests_array
        requests_array.append("generate_taxonomy_table")
        # find the vamps_upload_status record
        return '{"taxonomy_table" : "table results"}'

#This class pretends to be the Mobedac server which will send us mobedac projects, samples, libraries and
# sequence files
# as well as accept our results when we are done.
# this class is not used to actually generate the original request to our API server to do a processing submission
# that is simply handled by the test_gast_taxtable.py script
class MobedacListener():
    @cherrypy.expose
    def project(self, *vpath, **params):
#        global requests_array
#        requests_array.append("GET project")
        return json.dumps(projects[vpath[0]]) 

    @cherrypy.expose
    def sample(self, *vpath, **params):
#        global requests_array
#        requests_array.append("GET sample")
        return json.dumps(samples[vpath[0]]) 

    @cherrypy.expose
    def library(self, *vpath, **params):
#        global requests_array
#        requests_array.append("GET library")
        return json.dumps(libraries[vpath[0]]) 

    @cherrypy.expose
    def set_sequence_set_file_type(self, *vpath, **params):
        global sequencefiles
        global sequencefiles_by_types
        sequencefiles = sequencefiles_by_types[vpath[0]]
    
    @cherrypy.expose
    def sequenceSet(self, *vpath, **params):
#        global requests_array
#        requests_array.append("GET sequenceset")
        global sequencefiles
        filepath = sequencefiles[vpath[0]]['name']
        format = sequencefiles[vpath[0]]['format']
        seqfile = open(filepath,"r")
        cherrypy.response.headers['content-type'] = 'application/' + format
        return seqfile.read()

    @cherrypy.expose
    def results(self, *vpath, **params):
        global requests_array
        print "results: "
        print cherrypy.request.body.read()
        requests_array.append("POST results")
        return ""

# an instance of this class is passed to the cherrypy module
class Root(object):
    # accept calls in to url:  .../vamps/abcd
    # send the above .../vamps/abcd request to VampsListener.abcd() 
    vamps = VampsListener()
    # accept  .../mobedac/efgh....
    # send the above .../vamps/efgh request to MobedacListener.efgh() 
    mobedac = MobedacListener()    
    def __init__(self ):
        pass
    @cherrypy.expose
    def index(self):
        return "test client index"
    @cherrypy.expose
    def get_requests(self):
        global requests_array
        return json.dumps(requests_array)
    @cherrypy.expose
    def clear_requests(self):
        global requests_array
        requests_array = []


# This VAMPS processor thread is running in the background as part of trying to imitate VAMPS doing trimming, gasting
# This exists because we want to pretend that our calls to VAMPS really take a minute or two to complete each step of trimming and gasting.
# in this way our API server will really be tested because it uses a processing thread loop that keeps checking VAMPS status of our requests
# This routine slowly changes the status of the VAMPS status record from TRIM_PROCESSING to TRIM_SUCCESS and then
# from GAST_PROCESSING to GAST_SUCCESS slowly just like VAMPS would do.
def vamps_processor_thread(*args):
    while True:
        # create the row in VAMPS db
        dbConn = MySQLdb.connect("localhost", db_user_local, db_passw_local,"vamps_test" )
        cursor = dbConn.cursor()

        cursor.execute("SELECT * FROM vamps_upload_status WHERE status='TRIM_PROCESSING';")
        for result_row in cursor.fetchall():
            print "got TRIM_PROCESSING status row id: " + str(result_row[4])
        cursor.execute("SELECT * FROM vamps_upload_status WHERE status='GAST_PROCESSING';")
        for result_row in cursor.fetchall():
            print "got status row id: " + str(result_row[4])
            
        cursor.execute("UPDATE vamps_upload_status SET status='GAST_SUCCESS' WHERE status='GAST_PROCESSING';")
        if cursor.rowcount > 0:
            print "Number of rows updated GAST_PROCESSING => GAST_SUCCESS: %d" % cursor.rowcount
        dbConn.commit()
        
        cursor.execute("UPDATE vamps_upload_status SET status='TRIM_SUCCESS' WHERE status='TRIM_PROCESSING';")
        if cursor.rowcount > 0:
            print "Number of rows updated TRIM_PROCESSING => TRIM_SUCCESS: %d" % cursor.rowcount
        dbConn.commit()

        
        dbConn.close()
        time.sleep(80)
        pass

# some threading code...this starts up the above vamps_processor_thread
make_thread = lambda fn, *args: Thread(None, fn, None, args).start()  
make_thread(vamps_processor_thread)

# this routine does all the work
# it tells cherrypy to use this Root object which is configured to listen to urls:
# http://localhost:8081/vamps/...
# and
# http://localhost:8081/mobedac/...
#
# The ../vamps/...  calls will goto the VampsListener class methods
# The ../mobedac/...  calls will goto the MobedacListener class methods
# 

def start_listeners():
    try:
        cherrypy.server.max_request_body_size = 0
        cherrypy.config.update({'server.socket_port': 8081,})
        the_root = Root()
        cherrypy.quickstart(the_root, '/')        
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit()

# come here to really run things
if __name__ == '__main__':
    start_listeners()
    
