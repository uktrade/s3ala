# s3ala

A basic CLI-based aggregator to extract some very basic metrics from ALB logs stored in an S3 bucket

> [!NOTE]
> Work in progress. This README serves as a rough design spec


## Installation

```shell
pip install s3ala
```


## Usage

To use the pre-configured AWS profile to extract metrics of ALB logs in the bucket "bucket" under "prefix/" in the time range [2024-01-01T00:00:00, 2024-01-02T00:00:00)

```shell
AWS_PROFILE=my-aws-profile s3ala bucket prefix/ 2024-01-01T00:00:00 2024-01-02T00:00:00
```
