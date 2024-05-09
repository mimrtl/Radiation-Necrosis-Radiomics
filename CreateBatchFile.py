# file management
import os
import csv

######################## SET YOUR VARIABLES ##########################
# Initialize the root dir
ROOT = '/shares/mimrtl/Users/Chengnan/SRS_Necrosis'
# Directory that holds data
DIR_NAME = 'Intact_Cohort/'
# Directory to hold batch file path
BATCHFILE_PATH = 'Intact_Cohort/Radiomics/'
# Sequences to create batch files
SEQUENCES = ['T1_SkullStrip_BFC_IntStnd.nii.gz',
             'T2_SkullStrip_BFC_IntStnd.nii.gz',
             'T2FLAIR_SkullStrip_BFC_IntStnd.nii.gz']
######################################################################

# global paths
data_path = os.path.join(ROOT, DIR_NAME)
batchfile_path = os.path.join(ROOT, BATCHFILE_PATH)
if not os.path.exists(batchfile_path):
    os.mkdir(batchfile_path)

def createBatchFile(base, batchFileName, sequence):
    """Creates a batch file for an imaging sequence and updates any missing information

    Args:
        base: path file to hold all the data
        batchFileName: name of csv to write to
        sequence: Name of the sequence file (either 'T1.nii.gz', 'T2.nii.gz', or 'T2Flair.nii.gz')
    """
    print('Creating batch file with image and mask path pairs: ', batchFileName)

    with open(batchFileName, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Image", "Mask"])
        for subject in sorted(os.listdir(base)):
            if not subject.isnumeric():  # skip any dir that are not subject ids
                continue
            subject_path = os.path.join(base, subject)

            for session in os.listdir(subject_path):
                if session == '.DS_Store':
                    continue
                session_path = os.path.join(subject_path, session)
                image_path = ''
                mask_paths = []

                for nifti_file in os.listdir(session_path):
                    if '.nii' not in nifti_file:  # skip any non-nifti files
                        continue
                    if sequence == nifti_file:
                        image_path = os.path.join(session_path, nifti_file)
                    elif 'Mask' in nifti_file:
                        mask_paths.append(os.path.join(session_path, nifti_file))

                if image_path and mask_paths:
                    print("Writing", image_path)
                    for mask_path in mask_paths:
                        writer.writerow([image_path, mask_path])
                        print("Writing", mask_path)
                if not image_path:
                    print('{} sequence does not exist for patient {} and session {}\n'.format(sequence, subject, session))

def main():
    # Create batchfile for all sequences:
    for sequence in SEQUENCES:
        batchfile_name = os.path.join(batchfile_path, '{}_batchFile.csv'.format(sequence.split('.')[0]))
        createBatchFile(data_path, batchfile_name, sequence)
        
if __name__ == "__main__":
    main()  

