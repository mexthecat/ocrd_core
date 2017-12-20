# -*- coding: utf-8 -*-

import os
import xml.etree.ElementTree as ET
import requests

ns = { 'mets'  : "http://www.loc.gov/METS/",
       'mods'  : "http://www.loc.gov/mods/v3",
       'xlink' : "http://www.w3.org/1999/xlink",
     }

class Initializer:

    def __init__(self):
        """
        The constructor.
        """

        self.clear()

    def clear(self):
        """
        Resets the Initializer.
        """

        self.tree = ET.ElementTree()
        self.set_working_dir("./")
        self.img_src = {}
        self.img_files = {}
        self.fulltext = {}

    def set_working_dir(self,path):
        """
        (Re)sets the working directory.
        """
        self.working_dir = path

    def load_string(self,mets_xml):
        """
        Loads METS XML from a string.
        """
        pass

    def load(self,mets_xml_file):
        """
        Loads METS XML from a file (i.e. file name).
        """
        self.tree.parse(mets_xml_file)

    def initialize(self):
        """
        Performs the initialization.

        Image files are crawled and copied to the WD.
        PAGE XML files are either crawled or created and copied to the WD.
        """

        self._load_images()
        self._load_or_create_page()


    def _load_or_create_page(self):
        """
        Loads or creates missing PAGE XML from internal METS tree.
        """
        page_fileGrps = self.tree.getroot().findall(".//mets:fileGrp[@USE='FULLTEXT']", ns)
        # case load page
        if page_fileGrps:
            for page_file in page_fileGrps[0].findall("mets:file", ns):
                print(page_file)
        # case create page TODO
        else:
            pass

    def _load_images(self):
        """
        Retrieves images referenced in the METS and copies them to the WD.
        """
        img_fileGrps = self.tree.getroot().findall(".//mets:fileGrp[@USE='IMAGE']", ns)
        for img_fileGrp in img_fileGrps:
            img_files = img_fileGrp.findall("./mets:file", ns)
            for img_file in img_files:
                # extract information from elem
                img_ID = img_file.get("ID")
                ID = img_ID.rstrip("_IMAGE")
                img_url = img_file.find("mets:FLocat", ns).get("{%s}href" % ns["xlink"])

                # make a local copy
                img_data = requests.get(img_url)
                if img_data.status_code == 200:
                    self.img_src[ID] = img_url
                    self.img_files[ID] = "%s/%s" % (self.working_dir, os.path.basename(img_url))
                    with open(self.img_files[ID], 'wb') as f:  
                        f.write(img_data.content)
                
