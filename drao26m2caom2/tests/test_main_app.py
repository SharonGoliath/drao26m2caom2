# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2018.                            (c) 2018.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#
import pytest

from drao26m2caom2 import main_app, APPLICATION, COLLECTION
from caom2.diff import get_differences
from caom2pipe import manage_composable as mc

from hashlib import md5
import os
import sys

from mock import patch

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
TESTDATA_DIR = os.path.join(THIS_DIR, 'data')
PLUGIN = os.path.join(os.path.dirname(THIS_DIR), '{}.py'.format(APPLICATION))


# def pytest_generate_tests(metafunc):
#     if os.path.exists(TESTDATA_DIR):
#         files = [os.path.join(TESTDATA_DIR, name) for name in
#                  os.listdir(TESTDATA_DIR) if name.endswith('header')]
#         metafunc.parametrize('test_name', files)


@pytest.mark.parametrize('test_name', [])
def test_main_app(test_name):
    basename = os.path.basename(test_name)
    product_id = basename.split('.fits')[0]
    lineage = _get_lineage(product_id, basename)
    output_file = '{}.actual.xml'.format(test_name)
    local = _get_local(test_name)
    plugin = PLUGIN

    with patch('caom2utils.fits2caom2.CadcDataClient') as data_client_mock:
        def get_file_info(archive, file_id):
            if '_prev' in file_id:
                return {'size': 10290,
                        'md5sum': md5('-37'.encode()).hexdigest(),
                        'type': 'image/jpeg'}
            else:
                return {'size': 37,
                        'md5sum': md5('-37'.encode()).hexdigest(),
                        'type': 'application/fits'}
        data_client_mock.return_value.get_file_info.side_effect = \
            get_file_info

        sys.argv = \
            ('{} --no_validate --local {} '
             '--plugin {} --module {} --observation {} {} -o {} --lineage {}'.
             format(APPLICATION, local, plugin, plugin, COLLECTION, product_id,
                    output_file, lineage)).split()
        print(sys.argv)
        main_app()
        obs_path = test_name.replace('header', 'xml')
        expected = mc.read_obs_from_file(obs_path)
        actual = mc.read_obs_from_file(output_file)
        result = get_differences(expected, actual, 'Observation')
        if result:
            msg = 'Differences found in observation {}\n{}'. \
                format(expected.observation_id, '\n'.join(
                [r for r in result]))
            raise AssertionError(msg)
        # assert False  # cause I want to see logging messages


def _get_local(test_name):
    prev_name = test_name.replace('.fits.header', '_prev.jpg')
    prev_256_name = test_name.replace('.fits.header', '_prev_256.jpg')
    return '{} {} {}'.format(test_name, prev_name, prev_256_name)


def _get_lineage(product_id, basename):
    return '{}/ad:{}/{}.fits.gz'.format(COLLECTION, product_id, product_id)
