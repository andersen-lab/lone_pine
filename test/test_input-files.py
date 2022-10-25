#import pytest
import pandas as pd

VOC_FILE = "resources/voc.txt"
VOI_FILE = "resources/voi.txt"

def test_voc_file_correct_format():
    with open( VOC_FILE, "r" ) as voc_file:
        assert all( len( line.split( "," ) ) == 2 for line in voc_file ), "VOC file is not the proper format. Two columns are not found in every file."

def test_voi_file_correct_format():
    with open( VOI_FILE, "r" ) as voi_file:
        assert all( len( line.split( "," ) ) == 2 for line in voi_file ), "VOI file is not the proper format. Two columns are not found in every file."

