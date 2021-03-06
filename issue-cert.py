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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class IssueCert( object ):

    def __init__( self, options, logger ):

        self.opts = options
        self.log = logger
        self.domain = None
        self.output_pem = False
        self.key_file = '.lets_encrypt.pem'
        self.account_key = None
        self.key_type='rsa3072'
        self.email = ''
        self.new_account = True

    # -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    def issue_cert( self, domain:str ) -> None:

        if not os.environ.get( 'AWS_SECRET_ACCESS_KEY' ) or not os.environ.get( 'AWS_ACCESS_KEY_ID' ):
            self.log.warning( "AWS_SECRET_ACCESS_KEY and/or AWS_ACCESS_KEY_ID not set. Sewer uses environment variables to access AWS R53" )
            return

        filename, extension = os.path.splitext( self.key_file )
        self.account_key_file = "{}_account{}".format( filename, extension )
        self.certificate_key_file = "{}_certificate{}".format( filename, extension )
        
        if os.path.exists( self.key_file ):
            self.log.info( "loading Let's Encrypt account keys" )
            self.account = sewer.crypto.AcemAccount.read_pem(self.account_key_file)
            self.certificate = sewer.crypto.read_pem(self.certificate_key_file)
            self.new_account = False
        else:
            self.log.info( "creating Let's Encrypt account keys" )
            self.account = sewer.crypto.AcmeAccount.create(self.key_type)
            self.certificate = sewer.crypto.AcmeKey.create(self.key_type)

        dns_provider = sewer.dns_providers.route53.Route53Dns()

        if domain[:4] == 'www.':
            self.naked_domain = domain[4:]
        else:
            self.naked_domain = domain

        if not self.email:
            self.email = "info@{}".format( self.naked_domain )
            
        self.log.info( "making a cert request for {}".format( self.naked_domain ) )

        try:
            client = sewer.client.Client(
                domain_name = "*.{}".format( self.naked_domain ),
                domain_alt_names=[ self.naked_domain ],
                contact_email = self.email,
                provider = dns_provider,
                LOG_LEVEL = "DEBUG",
                account=self.account,
                cert_key=self.certificate,
                is_new_acct = self.new_account,
            )

        except Exception as e:
            self.log.warning( "failed to request certificate from Let's Encrypt server: {}".format( e ) )
            return

        self.log.info("requesting certificate for {}".format(self.naked_domain) )
        certificate = client.get_certificate()

        self.log.info( "writing account credentials to {}".format( self.account_key_file) )
        self.account.write_pem( self.account_key_file )
        self.log.info( "writing certificate key to {}".format( self.certificate_key_file ) )
        self.certificate.write_pem( self.certificate_key_file )
        
        print( certificate )

            
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':

    opts = docopt.docopt( __doc__, version='cms-cli' )
    logger = logging.getLogger( __name__ )
    # Turn off detailed logging from core libraries
    logging.getLogger( 'urllib3' ).setLevel( logging.WARNING )
    logging.getLogger( 'botocore' ).setLevel( logging.WARNING )
    logging.getLogger('boto3').setLevel( logging.WARNING )
    logging.getLogger('nose').setLevel( logging.WARNING )
            
    coloredlogs.install(level='DEBUG', logger=logger)

    ic = IssueCert( options = opts, logger = logger )
    if opts.get( '--account' ):
        ic.key_file = opts.get( '--account' )
    ic.issue_cert( domain = opts.get( '<domain>' ) )

