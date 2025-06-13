# Metadatatable.py
# Put PNG metadata into a pyQt QTableWidget formatted table.
# aka MDT. FWIW ILTLA's LOL
# G. Moore 2024-Oct

import ast
import json
# import pprint
import logging
from pathlib import Path
from collections import Counter

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QHeaderView
from PyQt6.QtGui import QFont

from sd_prompt_reader.image_data_reader import ImageDataReader
from .latent_tools import SamplerNames, show_error_box

# TODO: Convert to using latent_tools StringEnum
# actual human readable sampler names
SAMPLERS_NAMES = {
    'ddim': 'DDIM',
    'ddpm': 'DDPM',
    'deis': 'DEIS',
    'dpm_a': 'DPM Apaptive',
    'dpm_fast': 'DPM fast',
    'dpm_2': 'DPM2',
    'dpm_2_ancestral': 'DPM2 Ancestral',
    'dpm2_karras': 'DPM2 Karras',
    'dpm2_ancestral_karras':'DPM2 Ancestral Karras',
    'dpmpp_sde': 'DPM++ SDE',
    'dpmpp_sde_karras': 'DPM++ SDE Karras',
    'dpmpp_2': 'DPM++_2',
    'dpmpp_2_ancestral': 'DPM++ 2 ancestral',
    'dpmpp_2m': 'DPM++ 2M',
    'dpmpp_2m_sde': 'DPM++ 2M SDE',
    'dpmpp_2m_sde_gpu': 'DPM++ 2M SDE GPU',
    'dpmpp_2m_karras': 'DPM++ 2M Karras',
    'dpmpp_2s_ancestral': 'DPM++ 2S ancestral',
    'dpmpp_2s_ancestral_karras': 'DPM++ 2S ancestral Karras',
    'dpmpp_3m_sde':'DPM++ 3M SDE',
    'dpmpp_3m_sde_gpu':'DPM++ 3M SDE GPU',
    'dpmpp_3m_karras': 'DPM++ 3M Karras',
    'dpm_adaptive': 'DPM Adaptive',
    'euler_a': 'Euler Ancestral',
    'euler a': 'Euler Ancestral',
    'euler':  'Euler',
    'gradient_estimation': 'gradient estimation',
    'heun': 'Heun',
    'heunpp2': 'Heun2++',
    'ipndm': 'IPNDM',
    'ipndm_v': 'IPNDM V',
    'k_lms': 'LMS',
    'k_euler_ancestral': 'Euler Ancestral',
    'k_euler': 'Euler',
    'k_heun': 'Heun',
    'k_dpm_2': 'DPM2',
    'k_dpm_2_ancestral': 'DPM2 Ancestral',
    'lms': 'LMS',
    'lms_karras': 'LMS Karras',
    'plms': 'PLMS',
    'res_multistep': 'res multistep',
    'res_multistep_cfg_pp': 'res_multistep cfg++',
    'res_multistep_ancestral': 'res multistep ancestral',
    'res_multistep_ancestral_cfg_pp': 'res multistep ancestral cfg++',
    'unipc': 'UniPC',
    'uni_pc_bh2': 'UniPC bh2'
}

# Set up logging
logger = logging.getLogger(__name__)

class MetadataTable(QWidget):
    """
    Pulls the Stable Diffusion metadata out of an image
    and creates a Styled QTableWidget from the data
    """
    def __init__(self):
        super().__init__()

        logger.debug('Initializing MetadataTable')
        # is there any stable diffusion metadata in the image?
        self.valid_md = False

    def set_table_styling(self, table):
        """
        Add style to the passed in table.
        style consists of header row, colors,
        and fonts.
        Args: table to style
        """
        logger.debug('entering table_styling()')
        # Define fonts and colors. Eventually this should make its way to Settings.

        fontsize = 15
        fontname = 'Arial'                # yea, its boring but its on every platform.
        background_color = "#5A5A5A"    # light blue
        alternate_color = "#00246B"     # dark blue
        header_color = "#0B2E40"        # dark indigo
        text_color = "#FFFFFF"          # White

        table_style_string = f"""
            QTableWidget {{
                background-color: {background_color};
                alternate-background-color: {alternate_color};
            }}
            QHeaderView::section {{
                background-color: {header_color};
                color: {text_color};
                font-size: 14pt;
            }}
            """
        table.setFont(QFont(fontname, fontsize))
        table.setAlternatingRowColors(True)
        table.setStyleSheet(table_style_string)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def populate_table(self, metadata):
        """
        Populate the table with metadata key-value pairs.
        Args: dict containing SD metadata.
        """
        logger.debug('entering populate_table()')
        if self.valid_md:
            logger.debug('populating table')
            self.table.setRowCount(len(metadata.keys()))

            for row, (key, value) in enumerate(metadata.items()):
                self.table.setItem(row, 0, QTableWidgetItem(str(key).capitalize()))
                self.table.setItem(row, 1, QTableWidgetItem(str(value).strip()))
                if row in [0,1]:
                    self.table.item(row, 1).setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                    self.table.item(row, 1).setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.table.item(row, 1).setFlags(self.table.item(row, 1).flags() | Qt.ItemFlag.ItemIsSelectable)
                    # interesting... if the string is 151 chars, the next line works fine but if the line is, say, 371 chars
                    # it doesn't work properly and appears to set the row size to about double the height of a regular row.
                    # I wonder why and where the cut off is. Does column width matter?

    def get_metadata_table(self, image_path):
        """
        this takes care of:
        - getting the image metadata
        - creating and styling the a QTableWidget
        - populating new table with the obtained metadata

        Returns False if no metadata is found in the image and of course no table
        Returns a styled and populated table if metadata exists
        """
        # Get the info from the image
        if image_path:
            # message something to the effect that the perms issue or something else
            # and cant access file at image_path
            self.metadata = self.get_image_metadata(image_path)
        else:
            logger.debug('get_metadata_table(): image_path is null or not set.')
            logger.warning(f'When attempting to read the metadata for {image_path}. it is either invalid, inaccessable, null or not set.')
            show_error_box(f'When attempting to read the metadata for {image_path}. it is either invalid, inaccessable, null or not set.', 'warning')

        if self.valid_md:
            # Create a table widget
            self.table = QTableWidget(self)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(['Image Info', 'Value'])
            # set a style as defined in table_styling()
            self.set_table_styling(self.table)
            # populate the metadata gleaned from the image into the table
            self.populate_table(self.metadata)
            logger.debug('get_metadata_table(): returning styled and populated table')
            return self.table
        else:
            logger.debug('get_metadata_table(): (invalid metadata format. calling no_data_table()')
            nada_table = self.no_data_table(image_path)
            return nada_table

    def no_data_table(self, filename):
        """
        create a 1 row table. does the header row count?
        indicating that there wasn't any SD metadata in
        the chosen image.
        Args: string - filename
        returns: A styled table with a single row indicating no metadata.
        """
        # ensure the table is styled and no ellipsis for the text.
        # Why? because the the table was being updates and only the
        # first row was changing and the rest of the many rows contained
        # data. This takes care of that problem

        logger.debug('no_data_table(): Metadata Table NOT populated')
        logger.warning('Metadata Table NOT populated. Possibly no SD Metadata in image: %s.', filename)
        diddley = QTableWidget()    # no, not as in Bo. As in diddley squat
        diddley.setColumnCount(2)
        diddley.setRowCount(1)
        diddley.setItem(0, 0,  QTableWidgetItem(' No Metadata '))
        msg = f'found in {Path(filename).name}'
        diddley.setItem(0, 1,  QTableWidgetItem(msg))
        self.set_table_styling(diddley)
        diddley.setWordWrap(True)
        diddley.setColumnWidth(1, 600)
        diddley.resizeRowToContents(0)
        diddley.resizeRowToContents(1)
        return diddley

    # Flatten inner dictionaries
    def flatten_dict(self, some_dict):
        """
        Flattens nested dictionaries into a single-level dictionary.
        Args: dict to flatten
        Returns: flattened dict.
        """
        # maybe comprehension would be more concise but
        # this easier in terms of clarity and readability. Zen Like?
        flat = {}
        for key, value in some_dict.items():
            if isinstance(value, dict):
                flat.update(value)
            else:
                flat[key] = value
        return flat

    def get_image_metadata(self, image_path):
        """Read image metadata from Stable Diffusion generated image
           using sd-prompt reader to pull out the data.

           Args: image_path: str. FQFN of graphic image file
           Returns: dict. processed dict with metadata from image or
                    False if no metadata.
        """

        # Parse metadata from Stable Diffusion
        logger.debug(f'get_image_metadata(): image_path: {image_path}')
        try:
            with open(image_path, "rb+") as f:
                image_metadata = ImageDataReader(f)
        except Exception as err:
            # see note in thumbnail_view.py around line 190
            self.valid_md = False
            logger.critical(f'failed to read {image_path} with Exception {err}')
            show_error_box(f'failed to read {image_path} with Exception {err}', 'critical')
            return False

        if image_metadata.status.name != 'READ_SUCCESS':
            logger.error(f'get_image_metadata(): Error reading image metadata from: {image_path}')
            self.valid_md = False
            return False
        else:
            logger.debug('metadata successfully read. ')
            self.valid_md = True
            # build the metadata dict that will be use for the Table
            metadata = json.loads(image_metadata.props)
            md_orig_key_count = len(metadata)
            settings_str = image_metadata.setting
            logger.debug(f'{settings_str=}')

            # is settings_str empty or only white space?
            if settings_str and not settings_str.isspace():
            # create the settings dict from the setting string.
            # Preserve 'generation_time' as a string, then convert
            # any ints, floats or bool to str and strip whitespace.
            # Added try except because sometimes the setting string is
            # not properly formatted or at least formatted as expected.
                try:
                    settings_dict = {
                        k.strip(): (v if 'generation_time' in k else
                            ast.literal_eval(v) if v.replace('.', '', 1).isdigit() or v in ['True', 'False'] else v
                        )
                        for k, v in (pair.split(': ', 1) for pair in settings_str.split(', '))
                    }
                    logger.debug(f"setting key count: {len(settings_dict)}")
                except ValueError as e:
                    logger.debug(f'ValueError encountered with {image_path} while parsing settings_str. Probable badly formatted data:\n {e}')
                    settings_dict = {}
                    metadata['settings'] = settings_str
            else:
                settings_dict = {}
                logger.debug('setting metadata empty')

            # add the tool used to create image
            if image_metadata.tool:
                metadata['tool_used'] = image_metadata.tool
            else:
                metadata['tool_used'] = 'Unknown'

            metadata = self.flatten_dict(metadata)
            if settings_dict is None:
                settings_dict = self.flatten_dict(settings_dict)

            # before the blending remove the 'setting' key since we no longer need it.
            metadata.pop('setting')

            # Merge the metadata and setting dictionaries
            # if the keys are the same but the value is different
            # then add a -[number] to the key name.
            # make sure there are no dupes
            # key_lc = key_lowercase
            blended = {}
            key_counter = Counter()
            for source in (metadata, settings_dict):
                for key, value in source.items():
                    key_lc = key.lower()
                    str_value = str(value)

                    if key_lc in blended:
                        # case-insensitive check if values are different
                        if str(blended[key_lc]) != str_value:
                            count = key_counter[key_lc] + 1
                            new_key = f"{key}-{count}"
                            blended[new_key] = value
                            key_counter[key_lc] += 1
                    else:
                        blended[key_lc] = value
                        key_counter[key_lc] = 0

            # Restore original case for keys
            metadata = dict(blended)

            # If sampler_name is not None or an empty string and exists
            # in SAMPLERS_NAMES, it updates metadata['sampler'] with a
            # the full name of the sampler replacing the acronym.
            sampler_name = metadata.get('sampler')
            if sampler_name:
                metadata['sampler'] = SAMPLERS_NAMES.get(sampler_name.lower(), sampler_name)
            else:
                metadata['sampler'] = 'Unknown'

            if metadata.get('cfg') and metadata.get('cfg scale'):
                if str(metadata.get('cfg')) == str(metadata.get('cfg scale')):
                    metadata.pop('cfg')

            logger.debug('Processed Metadata cleaning up and remove leftovers.')
            metadata.pop('height')
            metadata.pop('width')
            # the next bit of code is a bit clunky. I found cases where
            # the is_sdxl key did not contain all the keys so I put
            # this in
            if not metadata['is_sdxl']:
                try:
                    for key in ['is_sdxl', 'positive_sdxl', 'negative_sdxl']:
                        metadata.pop(key)
                except KeyError:
                    pass
            logger.debug(f'initial metadata key count: {md_orig_key_count}')
            logger.debug(f'key count of blended {len(blended)}')
            logger.debug(f"Final metadata key count: {len(metadata)}")

            # cleanup a bit
            del settings_dict
            del blended
            logger.debug('get_image_metadata(): returning processed metadata. ')
        return metadata
