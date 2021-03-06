# Let's Encrypt R53 Certificate Issuer

Create certs using Let's encrypt for domains hosted on AWS R53.

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


## Create or renew a certificate
```
./issue-cert.py glenndesmidt.com > glenndesmidt.com.pem
```
