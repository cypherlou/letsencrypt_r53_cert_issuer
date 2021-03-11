#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cms-cli.py


Usage:
  issue-cert.py issue <domain> <pem-file> [--account=<key-file>] [--email=<email>]
  issue-cert.py issue <domain>... --directory=<directory> [--account=<key-file>] [--email=<email>]
  issue-cert.py renew <domain> <pem-file> [--account=<key-file>] [--email=<email>] [--check=<days> [--server=<server>]]
  issue-cert.py renew <domain>... --directory=<directory> [--account=<key-file>] [--email=<email>] [--check=<days> [--server=<server>]]
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


def check_cert(domain, server, logger) -> None:
    cd = ic.cert.Cert(logger=logger, server=server)
    cd.get_expiration(domain)
    if cd.error:
        sys.exit(1)

    if cd.expiration_date:
        print(cd.expires_in)
    else:
        print("0")
        sys.exit(1)


def issue_cert(logger, domain: str, account: str = '',
               directory: str = None, pem: str = None):

    issue = ic.cert.IssueCert(logger=logger)
    if account:
        issue.key_file = account

    issue.issue_cert(domain=domain)
    if issue.error:
        logger.error("cert issue returned an error - aborting")
        return

    if pem:
        if pem == '-':
            print(issue.pem)
        else:
            logger.info("saving certificate to {}".format(pem))
            _save_to_file(pem, issue.pem)

    if directory:
        logger.info("saving {} certificate to {}".format(domain, pem))
        filename = "{}/{}.pem".format(directory, domain)
        _save_to_file(filename, issue.pem)


def renew_cert(logger, domain: str, account: str = '', directory: str = None,
               pem: str = None, check: int = 0, server: str = ''):

    if check:
        cd = ic.cert.Cert(logger=logger, server=server)
        cd.get_expiration(domain)
        if cd.expires_in > check:
            logger.debug(
                "cert valid for {} days which is greater than the"
                " {} day check - aborting".format(cd.expires_in, check))
            return

    issue_cert(logger, domain, account, directory, pem)


def _save_to_file(name, value):
    with open(name, 'w') as f:
        f.write(value)
    f.close()


if __name__ == '__main__':

    opts = docopt.docopt(__doc__, version='cms-cli')
    logger = logging.getLogger(__name__)
    # Turn off detailed logging from core libraries
    for logger_name in ['urllib3', 'botocore', 'boto3', 'nose']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=logger)

    if opts.get('issue'):
        for domain in opts.get('<domain>'):
            issue_cert(
                logger=logger,
                account=opts.get('--account'),
                domain=domain,
                directory=opts.get('--directory'),
                pem=opts.get('<pem-file>'),
            )

    if opts.get('renew'):
        for domain in opts.get('<domain>'):
            renew_cert(
                logger=logger,
                account=opts.get('--account'),
                domain=domain,
                check=int(opts.get('--check')),
                server=opts.get('--server'),
                directory=opts.get('--directory'),
                pem=opts.get('<pem-file>'),
            )

    if opts.get('expiration'):
        check_cert(
            logger=logger,
            server=opts.get('--server'),
            domain=opts.get('<domain>')[0],
        )
