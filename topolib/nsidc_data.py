import io
import json
import math
import pprint
import zipfile
from statistics import mean
from xml.etree import ElementTree

import fiona

from topolib import EarthData

# To read KML files with geopandas, we will need to enable KML support
# in fiona (disabled by default)
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'


class IceSat2Data:
    PRODUCT_NAME = 'ATL06'

    NSIDC_URL = 'https://n5eil02u.ecs.nsidc.org'
    CAPABILITY_API = f'{NSIDC_URL}/egi/capabilities'
    DATA_REQUEST_URL = f'{NSIDC_URL}/egi/request'
    DOWNLOAD_URL = f'{NSIDC_URL}/esir/'

    REQUEST_HEADERS = {'Accept': 'application/json'}
    REQUEST_MODE = 'async'
    ORDER_PAGE_SIZE = 10

    EARTHDATA_URL = 'https://cmr.earthdata.nasa.gov'
    TOKEN_API_URL = f'{EARTHDATA_URL}/legacy-services/rest/tokens'
    CMR_COLLECTIONS_URL = f'{EARTHDATA_URL}/search/collections.json'
    GRANULE_SEARCH_URL = f'{EARTHDATA_URL}/search/granules'

    BEAM_VARIABLES = [
        '/land_ice_segments/atl06_quality_summary',
        '/land_ice_segments/delta_time',
        '/land_ice_segments/h_li',
        '/land_ice_segments/h_li_sigma',
        '/land_ice_segments/latitude',
        '/land_ice_segments/longitude',
        '/land_ice_segments/segment_id',
        '/land_ice_segments/sigma_geo_h',
        # # Other variables to add to coverage
        # '/land_ice_segments/geophysical/r_eff',
        # '/land_ice_segments/ground_track/x_atc',
        # '/land_ice_segments/n_fit_photons',
        # '/land_ice_segments/w_surface_window_final',
        # '/land_ice_segments/h_rms_misft',
        # '/land_ice_segments/h_robust_sprd',
        # '/land_ice_segments/snr',
        # '/land_ice_segments/snr_significance',
        # '/land_ice_segments/dh_fit_dx',
    ]
    BEAMS = ['gt1r', 'gt1l', 'gt2r', 'gt2l', 'gt3r', 'gt3l']

    def __init__(self, user_id, password, **kwargs):
        self.session = EarthData(user_id, password)
        self.product_name = kwargs.get('product', self.PRODUCT_NAME)
        self.product_version_id = self.latest_version_id()

    def latest_version_id(self):
        """
        Find most recent 'version_id' in metadata
        """
        response = self.session.get(
            self.CMR_COLLECTIONS_URL,
            params={'short_name': self.product_name}
        )
        response = json.loads(response.content)
        return max(
            [entry['version_id'] for entry in response['feed']['entry']]
        )

    def get_capabilities(self):
        """
        Query service capability URL
        :return:
        """
        capability_url = \
            f'{self.CAPABILITY_API}/' \
            f'{self.product_name}.{self.product_version_id}.xml'

        return self.session.get(capability_url)

    @staticmethod
    def time_range_params(start_date, end_date):
        """
        Input temporal range if you have a specific range, otherwise, this is unnecessary

        :param start_date: Start date in yyyy-MM-dd format
        :param end_date: End date in yyyy-MM-dd format

        :return: Time string for request parameter
        """
        start_time = '00:00:00'  # Start time in HH:mm:ss format
        end_time = '23:59:59'    # End time in HH:mm:ss format

        return f'{start_date}T{start_time}Z,{end_date}T{end_time}Z'

    def search_granules(self, start_date, end_date, **kwargs):
        temporal = self.time_range_params(start_date, end_date)

        if kwargs.get('bounding_box', None) is not None:
            # bounding box input:
            params = {
                'short_name': self.product_name,
                'version': self.product_version_id,
                'temporal': temporal,
                'page_size': 100,
                'page_num': 1,
                'bounding_box': ','.join(kwargs.get('bounding_box').values()),
            }
        elif kwargs.get('polygon', None) is not None:
            # If polygon input (either via coordinate pairs or shapefile/KML/KMZ):
            params = {
                'short_name': self.product_name,
                'version': self.product_version_id,
                'temporal': temporal,
                'page_size': 100,
                'page_num': 1,
                'polygon': kwargs.get('polygon'),
            }
        else:
            print('Missing bounding box or polygon to search for')
            return -1

        granules = []

        while True:
            response = self.session.get(
                self.GRANULE_SEARCH_URL,
                params=params,
                headers=self.REQUEST_HEADERS
            )

            results = json.loads(response.content)

            if len(results['feed']['entry']) == 0:
                # Out of results, so break out of loop
                break

            # Collect results and increment page_num
            granules.extend(results['feed']['entry'])
            params['page_num'] += 1

        if len(granules) > 0:
            granule_sizes = [float(granule['granule_size']) for granule in
                             granules]

            print('Number of granules:')
            print(f'    {len(granule_sizes)}')

            print('Average size of granules in MB:')
            print(f'    {mean(granule_sizes)}')
            print('Total size in MB:')
            print(f'    {sum(granule_sizes)}')

            return len(granule_sizes)
        else:
            return 0

    def coverage_variables(self):
        """
        Specify variables of interest
        :return:
        """
        return ','.join(
            [
                f'/{beam}{variable}' for variable in self.BEAM_VARIABLES
                for beam in self.BEAMS
             ]
        ) + '/ancillary_data/atlas_sdp_gps_epoch,\
        /orbit_info/cycle_number,\
        /orbit_info/rgt,\
        /orbit_info/orbit_number'

    def order_data(
            self, email, destination_folder, start_date, end_date, bounding_box
    ):

        number_of_granules = self.search_granules(
            start_date, end_date, bounding_box=bounding_box
        )

        # Determine number of pages based on page_size and total granules.
        # Loop requests by this value
        page_num = math.ceil(number_of_granules / self.ORDER_PAGE_SIZE)

        bounding_box = ','.join(bounding_box.values())
        time = self.time_range_params(start_date, end_date)

        subset_params = {
            'short_name': self.product_name,
            'version': self.product_version_id,
            'temporal': time,
            'time': time.replace('Z', ''),
            'bounding_box': bounding_box,
            'bbox': bounding_box,
            'Coverage': self.coverage_variables(),
            'request_mode': self.REQUEST_MODE,
            'page_size': self.ORDER_PAGE_SIZE,
            'email': email,
        }

        # Request data service for each page number, and unzip outputs
        for i in range(page_num):
            page_val = i + 1
            print('Order: ', page_val)
            subset_params.update({'page_num': page_val})

            # Post polygon to API endpoint for polygon subsetting to subset
            # based on original, non-simplified KML file
            # shape_post = {'shapefile': open(kml_filepath, 'rb')}
            # request = self.session.post(
            #   self.DATA_REQUEST_URL, params=subset_params, files=shape_post
            # )

            # For all other requests that do not utilized an uploaded polygon
            # file, use a get request instead of post:
            request = self.session.get(
                self.DATA_REQUEST_URL, params=subset_params
            )

            print('Request HTTP response: ', request.status_code)

            # Raise bad request: Loop will stop for bad response code.
            request.raise_for_status()

            # Look up order ID
            orderlist = []
            esir_root = ElementTree.fromstring(request.content)

            for order in esir_root.findall("./order/"):
                orderlist.append(order.text)
            orderID = orderlist[0]
            print('order ID: ', orderID)

            # Create status URL
            status_url = f'{self.DATA_REQUEST_URL}/{orderID}'
            # Find order status
            request_response = self.session.get(status_url)

            # Raise bad request: Loop will stop for bad response code.
            request_response.raise_for_status()
            request_root = ET.fromstring(request_response.content)
            statuslist = []
            for status in request_root.findall("./requestStatus/"):
                statuslist.append(status.text)
            status = statuslist[0]
            print('Data request ', page_val, ' is submitting...')
            print('Initial request status is ', status)

            # Continue to loop while request is still processing
            while status == 'pending' or status == 'processing':
                print('Status is not complete. Trying again.')
                time.sleep(10)
                loop_response = self.session.get(status_url)

                # Raise bad request: Loop will stop for bad response code.
                loop_response.raise_for_status()
                loop_root = ET.fromstring(loop_response.content)

                # Find status
                statuslist = []
                for status in loop_root.findall("./requestStatus/"):
                    statuslist.append(status.text)
                status = statuslist[0]
                print('Retry request status is: ', status)
                if status == 'pending' or status == 'processing':
                    continue

            # Order can either complete, complete_with_errors, or fail:
            # Provide complete_with_errors error message:
            if status == 'complete_with_errors' or status == 'failed':
                messagelist = []
                for message in loop_root.findall("./processInfo/"):
                    messagelist.append(message.text)
                print('error messages:')
                pprint.pprint(messagelist)

            # Download zipped order if status is complete or complete_with_errors
            if status == 'complete' or status == 'complete_with_errors':
                download_url = self.DOWNLOAD_URL + orderID + '.zip'
                print('Beginning download of zipped output...')
                zip_response = self.session.get(download_url)
                # Raise bad request: Loop will stop for bad response code.
                zip_response.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
                    z.extractall(destination_folder)
                print('Data request', page_val, 'is complete.')
            else:
                print('Request failed.')

    def show_capabilities(self):
        response = self.get_capabilities()
        root = ElementTree.fromstring(response.content)

        # collect lists with each service option
        subagent = [
            subset_agent.attrib for subset_agent in root.iter('SubsetAgent')
        ]

        # variable subsetting
        variables = [
            SubsetVariable.attrib for SubsetVariable in root.iter('SubsetVariable')
        ]
        variables_raw = [variables[i]['value'] for i in range(len(variables))]
        variables_join = [
            ''.join(('/', v)) if v.startswith('/') == False else v for v in variables_raw
        ]
        variable_vals = [v.replace(':', '/') for v in variables_join]

        # reformatting
        # formats = [Format.attrib for Format in root.iter('Format')]
        # format_vals = [formats[i]['value'] for i in range(len(formats))]
        # format_vals.remove('')

        # reprojection only applicable on ICESat-2 L3B products, yet to be available.
        #
        # # reformatting options that support reprojection
        # normalproj = [Projections.attrib for Projections in root.iter('Projections')]
        # format_proj = normalproj[0]['normalProj'].split(',')
        # format_proj.remove('')
        # format_proj.append('No reformatting')
        #
        # # reprojection options
        # projections = [Projection.attrib for Projection in root.iter('Projection')]
        # proj_vals = []
        # for i in range(len(projections)):
        #     if (projections[i]['value']) != 'NO_CHANGE':
        #         proj_vals.append(projections[i]['value'])

        if len(subagent) < 1:
            agent = 'NO'
        else:
            print(subagent)

        print(variable_vals)
