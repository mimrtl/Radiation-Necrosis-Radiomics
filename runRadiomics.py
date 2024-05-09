import collections
import csv
import logging
import os

import SimpleITK as sitk

import radiomics
from radiomics import featureextractor

######################## SET YOUR VARIABLES ##########################
# Initialize the root dir
ROOT = '/shares/mimrtl/Users/Chengnan/SRS_Necrosis'
# Directory to hold radiomic results and scripts
RADIOMICS_PATH = 'Intact_Cohort/Radiomics/'
# Sequences to create batch files
SEQUENCES = ['T2_SkullStrip_BFC_IntStnd.nii.gz',
             'T2FLAIR_SkullStrip_BFC_IntStnd.nii.gz']
# initialize the params files
PARAMS_SETTING = 'nonorm_fbw'
######################################################################

# global paths
radiomics_path = os.path.join(ROOT, RADIOMICS_PATH)
if not os.path.exists(radiomics_path):
    os.mkdir(radiomics_path)
params_path = os.path.join(ROOT, 'Radiomics_Scripts', 'Params_{}.yaml'.format(PARAMS_SETTING))
logging_path = os.path.join(radiomics_path, 'logging')
if not os.path.exists(logging_path):
    os.mkdir(logging_path)

def runRadiomics(outPath, batchFile, params, seq_name):
    """Runs radiomics on the batchFile with the given settings

    Args:
        outPath: base path to hold all the input and output files
        batchFile: path to batchFile csv
        params: path for params file (if it exists)
        seq_name: sequence name
    """

    # initializing the output path, and logging path
    outputFilepath = os.path.join(outPath, '{}_{}_radiomic_features.csv'.format(seq_name, PARAMS_SETTING))
    if os.path.exists(outputFilepath): # remove and restart outputFilepaths
        os.remove(outputFilepath)
    progress_filename = os.path.join(logging_path, '{}_{}_pyrad_log.txt'.format(seq_name, PARAMS_SETTING))

    # Configure logging
    rLogger = logging.getLogger('radiomics')

    # Set logging level
    # rLogger.setLevel(logging.INFO)  # Not needed, default log level of logger is INFO

    # Create handler for writing to log file
    handler = logging.FileHandler(filename=progress_filename, mode='w')
    handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
    rLogger.addHandler(handler)

    # Initialize logging for batch log messages
    logger = rLogger.getChild('batch')

    # Set verbosity level for output to stderr (default level = WARNING)
    radiomics.setVerbosity(logging.INFO)

    logger.info('pyradiomics version: %s', radiomics.__version__)
    logger.info('Loading CSV')

    flists = []
    try: # store CSV input
        with open(batchFile, 'r') as inFile:
            cr = csv.DictReader(inFile, lineterminator='\n')
            flists = [row for row in cr]
    except Exception:
        logger.error('CSV READ FAILED', exc_info=True)

    logger.info('Loading Done')
    logger.info('Patients: %d', len(flists))

    if os.path.isfile(params):
        extractor = featureextractor.RadiomicsFeatureExtractor(params)
    else:  # Parameter file not found, use hardcoded settings instead
        settings = {}
        settings['binWidth'] = 25
        settings['resampledPixelSpacing'] = None  # [3,3,3]
        settings['interpolator'] = sitk.sitkBSpline
        settings['enableCExtensions'] = True

        extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
        # extractor.enableInputImages(wavelet= {'level': 2})

    logger.info('Enabled input images types: %s', extractor.enabledImagetypes)
    logger.info('Enabled features: %s', extractor.enabledFeatures)
    logger.info('Current settings: %s', extractor.settings)

    headers = None

    for idx, entry in enumerate(flists, start=1): # iterate through each row of CSV
        logger.info("(%d/%d) Processing Patient (Image: %s, Mask: %s)", idx, len(flists), entry['Image'], entry['Mask'])

        imageFilepath = entry['Image']
        maskFilepath = entry['Mask']
        label = entry.get('Label', None)

        if str(label).isdigit():
            label = int(label)
        else:
            label = None

        if (imageFilepath is not None) and (maskFilepath is not None):
            featureVector = collections.OrderedDict(entry)
            # first two columns are the image and mask file paths
            featureVector['Image'] = imageFilepath
            featureVector['Mask'] = maskFilepath

            try: # update additional columns with extracted features
                featureVector.update(extractor.execute(imageFilepath, maskFilepath, label))
                with open(outputFilepath, 'a') as outputFile:
                    writer = csv.writer(outputFile, lineterminator='\n')
                    if headers is None: # write column headers as first line
                        headers = list(featureVector.keys())
                        writer.writerow(headers)

                    row = []
                    for h in headers:
                        row.append(featureVector.get(h, "N/A"))
                    writer.writerow(row)
            except Exception:
                logger.error('FEATURE EXTRACTION FAILED', exc_info=True)

def main():
    # Extract radiomics for all sequences:
    for sequence in SEQUENCES:
        batchfile_name = os.path.join(radiomics_path, '{}_batchFile.csv'.format(sequence.split('.')[0]))
        runRadiomics(radiomics_path, batchfile_name, params_path, sequence.split('.')[0])

if __name__ == "__main__":
    main() 
