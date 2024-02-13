import re
import zlib
from collections import Counter
from datetime import datetime
from io import TextIOWrapper

import boto3
import click
from to_file_like_obj import to_file_like_obj


def gunzip(chunks):
    dobj = zlib.decompressobj(32 + zlib.MAX_WBITS)
    for chunk in chunks:
        uncompressed_chunk = dobj.decompress(chunk)
        if uncompressed_chunk:
            yield uncompressed_chunk

    uncompressed_chunk = dobj.flush()
    if uncompressed_chunk:
        yield uncompressed_chunk


@click.command()
@click.argument('bucket')
@click.argument('prefix')
@click.argument('start', type=click.DateTime())
@click.argument('end', type=click.DateTime())
def main(bucket, prefix, start, end):
    s3_client = boto3.client('s3')

    # Fetch all log lines
    objs = (
        obj
        for page in s3_client.get_paginator("list_objects_v2").paginate(
            Bucket=bucket, Prefix=prefix,
        )
        for obj in page.get('Contents', [])
        if obj['Key'].endswith('.log.gz')
    )
    gzipped_logs_chunks = (
        s3_client.get_object(Key=obj['Key'], Bucket=bucket)['Body']
        for obj in objs
    )
    logs_files = (
        to_file_like_obj(gunzip(gzipped_logs_chunks))
        for gzipped_logs_chunks in gzipped_logs_chunks
    )
    log_lines = (
        line
        for log_file in logs_files
        for line in TextIOWrapper(log_file, encoding="utf-8", newline="")
    )

    # Parse lines
    # Based on https://docs.aws.amazon.com/athena/latest/ug/application-load-balancer-logs.html
    regex = re.compile(r'([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) (.*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-_]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\s]+?)\" \"([^\s]+)\" \"([^ ]*)\" \"([^ ]*)\"')
    fields = (
        'type',
        'time',
        'elb',
        'client_ip',
        'client_port',
        'target_ip',
        'target_port',
        'request_processing_time',
        'target_processing_time',
        'response_processing_time',
        'elb_status_code',
        'target_status_code',
        'received_bytes',
        'sent_bytes',
        'request_verb',
        'request_url',
        'request_proto',
        'user_agent',
        'ssl_cipher',
        'ssl_protocol',
        'target_group_arn',
        'trace_id',
        'domain_name',
        'chosen_cert_arn',
        'matched_rule_priority',
        'request_creation_time ',
        'actions_executed string',
        'redirect_url',
        'lambda_error_reason',
        'target_port_list',
        'target_status_code_list',
        'classification',
        'classification_reason',
    )
    parsed_lines = (
        dict(zip(fields, regex.match(line).groups()))
        for line in log_lines
    )
    parsed_lines_in_time_period = (
        parsed_line
        for parsed_line in parsed_lines
        if start <= datetime.strptime(parsed_line['time'], "%Y-%m-%dT%H:%M:%S.%fZ") < end
    )
    domain_counter = Counter()
    for i, line in enumerate(parsed_lines_in_time_period):
        domain_counter.update({line['domain_name'].split('.')[0].partition('-')[0]: 1})
        if i % 10000 == 0:
            click.echo(line['time'])
            click.echo(domain_counter)
    click.echo(domain_counter)
    click.echo('Done')
