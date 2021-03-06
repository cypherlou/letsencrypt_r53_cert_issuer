#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cms-cli.py


Usage:
  issue-cert.py <domain> [--account=<key-file>] [--email=<email>]
  issue-cert.py --help

Options:
  --help                                Display this.
  --account=<key-file>                  The key used to access the Let's Encrypt. If this
                                        file doersnt exist then it is created.
  --email=<email>                       Email sent to Let's Encrypt, defaults to info@<domain>.
"""

import os.path
import docopt
import coloredlogs
import logging
import sewer
import sewer.dns_providers.route53
import sewer.client
import sewer.crypto
import ic.cert

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':

    opts = docopt.docopt( __doc__, version='cms-cli' )
    logger = logging.getLogger( __name__ )
    # Turn off detailed logging from core libraries
    logging.getLogger( 'urllib3' ).setLevel( logging.WARNING )
    logging.getLogger( 'botocore' ).setLevel( logging.WARNING )
    logging.getLogger('boto3').setLevel( logging.WARNING )
    logging.getLogger('nose').setLevel( logging.WARNING )

    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=logger)

    ic = ic.cert.IssueCert( options = opts, logger = logger )
    if opts.get( '--account' ):
        ic.key_file = opts.get( '--account' )
    ic.issue_cert( domain = opts.get( '<domain>' ) )
    print( ic.pem )
