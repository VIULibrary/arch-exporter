# arch-export #

**Download AIPs from the Archivematica API**


## USAGE ##

1.   Get a list of available AIPs from your instance, and save to a JSON file

```
curl --location --request GET 'https://viu1.coppul.archivematica.org:8000/api/v2/file/?package_type=AIP&status=UPLOADED&limit=2000&offset=0'' --header 'Authorization: ApiKey USERNAME:APIKEY' | jq . > uploaded.json

```
- it should look like: `uploaded.json.sample`

2.  Add your credentials to `api_creds.json.sample` and rename as `api_creds.json`

3.  Run the script `python aip-exporter.py`


## NOTES ##

-   console log gives a file count, and size of current download
-   progress log stored at `download_log.txt`
-   script can be paused or stopped, download will resume on restart
-   clear the downloads folder and the `download_log.txt` to reset
