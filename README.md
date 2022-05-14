# acl-reproducibility-analysis

## Setup

```bash
wget https://aclanthology.org/anthology.bib.gz
gzip -dk anthology.bib.gz
python process_anthology.py --anthology_path "data/anthology.bib" --export_dir "data"
```


```bash
cd acl-reproduciblity-analysis

docker build -f docker/Dockerfile -t acl-rep-analysis-image .


docker save --output acl-rep-analysis-image.tar acl-rep-analysis-image
docker load --input acl-rep-analysis-image.tar
```