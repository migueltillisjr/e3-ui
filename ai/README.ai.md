# e3-text-based
e3-text-based

## Run it
```
python -m venv .e3tb
. .e3tb/bin/activate
pip install -r requirements.txt
./setup.sh
python -m mailgun
```

## Notes:
- Don't format email elements such as pictures, buttons w/ divs, use tables, some email providers can only interpret tables.

## Campaign
[] Craft email design, layout, text subject, preview
[] Upload contacts csv
    [] add to db
    [] validate
[x] Upload design to designated s3 bucket and return url for payload as "html"
[x] Add details to payload
[x] Associate domain with new email sending service
    [x] Mailgun
[x] Prune email list with service
    [x] NeverBounce, used ui/ux
    [x] NeverBounce, use python, got validated emails
[x] Save valid emails
[x] Organzie valid email contacts into send group batches of small 100 groups
[x] Craft email remainder of send payload
[x] Send email
[x] Gather email results of batches
[x] Aggregate results
[] Add the capability to select a time period for which to pull metrics
[] Create an identifier/tag to associate groupings of campaigns
[] Create an identifier to associate users
[] Separate validated from unvalidated contacts to keep a delta just incase the validation process fails for any reason such as lack of tokens.
[] speed up validation with concurrency
[] Handle errors stemming from validation, if can't validate fail gracefully sample error below

### Get started

1. Install Docker

2. Set your env variables
PROJECT_ROOT/.env
```
TAVILY_API_KEY=""
AWS_REGION="us-west-2"
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
DB_USER="nldbpostgres"
DB_PASS="nldbpostgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="e3nldbpostgres"
DB_URL="postgresql://e3nldbpostgres:e3nldbpostgres@localhost:5432/e3nldbpostgres"
AWS_ACCOUNT_ID=""
```

3. Do this at the command line...

```
python3 -m venv .cnldb
. .cndlb/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name=.cnldb --display-name "Python (.e3tb)"
./setup.sh
```

4. Run the nldb tool
```bash
python -m nldb "return all validated contacts"
python -m mailgun send
python -m mailgun metrics
python -m nlemaildesign "edit email to have better colors"
python -m python -m modify_html "add bright colors <h1>visit Hawaii and learn how to teach</h2>"
```

4. Run the app agent via jupyter notebook

```
jupyter notebook notebooks/nldb-wireframe-agent.ipynb
```

### Misc.

Explore the DB
```
psql -h localhost -p 5432 -U nldbpostgres -d nldbpostgres
\d
SELECT * from crm_contacts LIMIT 10;
```