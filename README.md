# Let's Encrypt R53 Certificate Issuer

Create certs using Let's Encrypt for domains hosted on AWS R53.

## Install

* create a virtual environment
* activate the environment
* install dependancies

```
virtualenv -p $(which python3) env
source env/bin/activate
pip install -r requirements.txt
```

## AWS
Ensure environment variables containing your AWS credentials are set.
```
export AWS_SECRET_ACCESS_KEY=SH1SHq1Jsv1tJG1qFT1!DR1Qb1161s1UJlI18i01
export AWS_ACCESS_KEY_ID=1KI15N1FK1B1X1HL1O41
```
Ensure that your Amazon User has the ability to create and remove text records on your hosted Zones.

## Usage
```
cms-cli.py

Usage:
  issue-cert.py issue <domain> [--account=<key-file>] [--email=<email>]
  issue-cert.py renew <domain> [--account=<key-file>] [--email=<email>] [--check=<days> [--server=<server>]]
  issue-cert.py expiration <domain> [--server=<server>]
  issue-cert.py --help

Options:
  --help                                Display this.
  --account=<key-file>                  The key used to access the Let's Encrypt. If this file doersnt exist then it is created.
  --email=<email>                       Email sent to Let's Encrypt, defaults to info@<domain>.
  --server=<server>                     If the server hosting the domain is not at the address of the domain.
  --check=<days>                        Do not request the cert if it's less than check days until expiration, defaults to 10.
```

## Create a certificate
```
certificate.py issue glenndesmidt.com > /etc/application/certs/glenndesmidt.com.pem
```
Issue a new certificate for glenndesmidt.com and save the resulting PEM file to `/etc/application/certs/glenndesmidt.com.pem`

## Renew a certificate
```
certificate.py renew --check 30 glenndesmidt.com > /etc/application/certs/glenndesmidt.com.pem
```
Renew the certificate for glenndesmidt.com if it is due to expire in less than 30 days.

## Check certificate renewal
The `expiration` command will check when the certificate is going to expire and return the number of days.
```
ehco "days to renewal: $(certificate.py expiration glenndesmidt.com)"
```

## Exit codes
If `certificate.py` fails to complete an operation it will exit with a status of 1, check `$?` if you are using a bash shell.

## `--server`
If you are running `certificate.py` on the server that is hosting the certificates or are operating in an environment where multiple nodes might be involved, the
`--server` option allows the host to be specified. This is also useful when dealing with firewalls that lack NAT traversal.
```
certificate.py renew --check 30 --server=localhost glenndesmidt.com > /etc/application/certs/glenndesmidt.com.pem
```

## References
[1] https://komuw.github.io/sewer/sewer-as-a-library

