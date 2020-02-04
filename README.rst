=============
Log Generator
=============
``log_generator`` generates dummy logs based on configuration files.

::

    usage: log-generator [-h] [--level LEVEL] [--truncate] /path/to/config

    Generate log events

    positional arguments:
      /path/to/config       Path to configuration directory or file

    optional arguments:
      -h, --help            show this help message and exit
      --level LEVEL, -l LEVEL
                            Logging level
      --truncate, -t        Truncate the log files on start


------------------
Configuration File
------------------
Log generator uses a set of configuration files to define how to generate logs.
You can see the schema for configuration files in ``log_generator/schema.yaml``.
There are 6 required properties: ``name``, ``file``, ``format``, ``frequency``, ``amount``, and ``fields``:

:name:      Name of the logs being generated (for logging purposes only)
:file:      The path to the file where to write the logs to
:frequency: Time frame of how frequently to output logs
:amount:    Number of logs to create per tick
:enabled:   (optional) Boolean as to whether the configuration file should be used (default True)
:offset:    (optional) Time frame of the offset, from now, the timestamps should be
:jitter:    (optional) Time frame of the jitter the timestamps should be.
:format:    The format of the log
:fields:    A dictionary of fields to be substituted into the log format


Each property of ``fields`` should be one of the following types:

:type:      One of ``enum``, ``timestamp``, ``integer``, ``float``, ``chance``, ``ip``
:repeat:    (optional) Number of times to repeat the current value before generating (default 1)
:change:    (optional) Float probability [0..1] that the current value will change (default 1)
:value:     (optional) The initial value for the field

Enum (``enum``)
    A list of values that have a uniform distribution of being selected.

    :values:    List of possible options

Timestamp (``timestamp``)
    A timestamp.

    :format:    The format that the timestamp should have

Integer (``integer``)
    A random integer value.

    :min:   Minimum value of the integer
    :max:   Maximum value of the integer

Float (``float``)
    A random floating point value.

    :min:   Minimum value of the float
    :max:   Maximum value of the float

Chance (``chance``)
    A set of options and associated weights to define the probability of being selected

    :choices:          A list of objects with two properties: ``option`` and ``weight``
    :choices.*.option: The value of the option
    :choices.*.weight: The probability of being selected

IP Address (``ip``)
    A randomly generated IP address.


^^^^^^^^
Examples
^^^^^^^^
Apache 2.4 Access:

::

    name: Apache General Access
    file: /var/log/httpd/apache_access
    format: "{log_ip} - - [{log_time} +0000] \"{log_method} {log_path} HTTP/1.1\" {log_status} {log_bytes}"
    frequency:
      seconds: 5
    offset:
      seconds: 0
    jitter:
      seconds: 5
    amount: 50
    fields:
      log_ip:
        type: ip
      log_time:
        type: timestamp
        format: "%d/%b/%Y:%H:%M:%S"
      log_method:
        type: enum
        values: [POST, GET, PUT, PATCH, DELETE]
      log_path:
        type: enum
        values:
          - /auth
          - /alerts
          - /events
          - /playbooks
          - /lists
          - /fieldsets
          - /customers
          - /collectors
          - /parsers
          - /users
      log_status:
        type: enum
        values: [200, 201, 204, 300, 301, 400, 401, 403, 404, 500, 503]
      log_bytes:
        type: integer
        min: 2000
        max: 5000


Custom log:

::

    name: Simulated Field Change
    file: /var/log/server/status
    format: "{log_time} server status: {log_colour}"
    frequency:
      seconds: 11
    offset:
      seconds: 0
    amount: 1
    fields:
      log_time:
        type: timestamp
        format: "%Y-%m-%dT%H:%M:%SZ"
      log_colour:
        type: chance
        repeat: 11
        change: 0.25
        value: green
        choices:
          - option: red
            weight: 0.2
          - option: yellow
            weight: 0.2
          - option: green
            weight: 0.6
