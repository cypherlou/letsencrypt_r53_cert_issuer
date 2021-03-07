#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cms-cli.py


Usage:
  issue-cert.py issue <domain> [--account=<key-file>] [--email=<email>]
  issue-cert.py renew <domain> [--account=<key-file>] [--email=<email>] [--check=<days> [--server=<server>]]
  issue-cert.py expiration <domain> [--server=<server>]
  issue-cert.py --help

Options:
  --help                                Display this.
  --account=<key-file>                  The key used to access the Let's Encrypt. If this
                                        file doersnt exist then it is created.
  --email=<email>                       Email sent to Let's Encrypt, defaults to info@<domain>.
  --server=<server>                     If the server hosting the domain is not at the address of the domain.
  --check=<days>                        Do not request the cert if it's less than check days
                                        until expiration [default: 10].
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
import sys

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def check_cert( domain, server, logger) -> None:
    cd = ic.cert.Cert( logger=logger, server=server )
    cd.get_expiration(domain)
    if cd.error:
        sys.exit(1)
        
    if cd.expiration_date:
        print( cd.expires_in )
    else:
        print( "0" )
        sys.exit(1)


def issue_cert(logger, domain:str, account:str=''):

    issue = ic.cert.IssueCert( logger = logger )
    if account:
        issue.key_file = account

    issue.issue_cert( domain = domain )
    print( issue.pem )


def renew_cert(logger, domain:str, account:str='', check:int=0, server:str=''):

    if check:
        cd = ic.cert.Cert( logger=logger, server=server )
        cd.get_expiration(domain)
        if cd.expires_in > check:
            logger.debug(
                "cert valid for {} days which is greater than the"
                " {} day check - aborting".format( cd.expires_in, check ) )
            return

    issue_cert( logger, domain, account )


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

    if opts.get( 'issue' ):
        issue_cert(
            logger=logger,
            account=opts.get( '--account' ),
            domain=opts.get( '<domain>' ),
        )

    if opts.get( 'renew' ):
        issue_cert(
            logger=logger,
            account=opts.get( '--account' ),
            domain=opts.get( '<domain>' ),
            check=int(opts.get( '--check' )),
            server=opts.get('--server'),
        )

    if opts.get( 'expiration' ):
        check_cert(
            logger=logger,
            server=opts.get('--server'),
            domain=opts.get('<domain>'),
        )
            
    
