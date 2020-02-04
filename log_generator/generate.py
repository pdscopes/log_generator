import argparse
import datetime
import glob
import logging
import os
import random
import signal
import sys
import threading
import time
from typing import List, Union

import yaml
from jsonschema import validate, ValidationError


class Generator:
    def __init__(self, conf_dir: str, truncate: bool = False):
        self.conf_dir = conf_dir.rstrip('/')
        self.events = []
        self.logger = logging.getLogger()
        self.running = False
        self.reload = True
        self.truncate = truncate
        self.schema = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'schema.yaml')))

    def handle_signal(self, sig: int, _) -> None:
        """
        Handles signals to either exit or reload configuration files.
        """
        if sig == signal.SIGHUP:
            self.logger.info('Receiving SIGHUP({:d}), reloading config...'.format(sig))
            self.truncate = False
            self.reload = True
        elif sig == signal.SIGINT:
            self.logger.critical('Receiving SIGINT({:d}), exiting...'.format(sig))
            self.stop()

    def run(self) -> None:
        self.running = True
        self.reload = True

        self.logger.info('Starting normal execution')
        # Block while running
        while self.running:
            if self.reload:

                # Stop constant reloading
                self.reload = False
                self.stop_generating()
                self.events = []

                # Load the configuration files
                for config_file in Generator.gather_configs(self.conf_dir):
                    try:
                        event = threading.Event()
                        config = Generator.load_config(config_file, self.schema)
                        # Skip over disabled configurations
                        if not config['enabled']:
                            self.logger.info('Skipped: {:s}'.format(config_file))
                            continue

                        self.logger.info('Loaded:  {:s}'.format(config_file))
                        threading.Thread(target=self.generate_log_entry, args=(event, config)).start()
                        self.events.append(event)
                    except ValidationError as e:
                        self.logger.critical('Invalid configuration file: {:s}'.format(config_file))
                        self.logger.critical(e)

    def stop(self) -> None:
        self.running = False
        self.stop_generating()

    def stop_generating(self) -> None:
        for e in self.events:
            e.set()

    @staticmethod
    def gather_configs(config_dir: str):
        if not os.path.exists(config_dir):
            raise FileNotFoundError(f'No such file or directory: {config_dir!r}')
        elif os.path.isfile(config_dir):
            return [config_dir]
        else:
            return glob.glob(f'{config_dir}/*.yaml')

    @staticmethod
    def load_config(config_file: str, schema: dict) -> dict:
        with open(config_file, 'r') as stream:
            config = yaml.safe_load(stream)
            validate(config, schema)

            config.setdefault('enabled', True)
            config.setdefault('offset', {'seconds': 0})
            config.setdefault('jitter', {'seconds': 0})
            config.setdefault('fields', {})

            config['frequency'] = datetime.timedelta(**config['frequency'])
            config['offset'] = datetime.timedelta(**config['offset'])
            config['jitter'] = datetime.timedelta(**config['jitter'])

            for name in config['fields']:
                config['fields'][name].setdefault('count', 0)

            return config

    @staticmethod
    def get_timestamps(config: dict, timestamp: datetime.datetime) -> List[datetime.datetime]:
        timestamp -= config['offset']
        timestamps = []
        for _ in range(config['amount']):
            seconds = random.randint(0, config['jitter'].total_seconds())
            timestamps.append(timestamp - datetime.timedelta(seconds=seconds))
        return sorted(timestamps)

    @staticmethod
    def next_value(config: dict, name: str) -> str:
        """
        Get the next value for the field.
        :param dict config: Configuration dictionary
        :param str name: Name of the field
        """
        fields = config['fields']
        fields[name]['count'] += 1

        # If the value should be repeated
        if 'value' in fields[name] and 'repeat' in fields[name]:
            if fields[name]['count'] <= fields[name]['repeat']:
                return fields[name]['value']
            else:
                fields[name]['count'] = 0

        # If the value should change
        if 'value' in fields[name] and 'change' in fields[name]:
            if random.random() > fields[name]['change']:
                return fields[name]['value']
            else:
                fields[name]['count'] = 0

        # Determine the value
        fields[name]['value'] = Generator.get_value(config, name)

        return fields[name]['value']

    @staticmethod
    def get_value(config: dict, name: str) -> Union[str, None]:
        """
        Generate a value based on field type.
        :param dict config: Configuration dictionary
        :param str name: Name of the field
        """
        field = config['fields'][name]

        if field['type'] == 'enum':
            return str(random.choice(field['values']))

        elif field['type'] == 'chance':
            options = [i['option'] for i in field['choices']]
            weights = [i['weight'] for i in field['choices']]
            return str(random.choices(options, weights)[0])

        elif field['type'] == 'integer':
            return str(random.randint(field['min'], field['max']))

        elif field['type'] == 'float':
            return str(random.uniform(field['min'], field['max']))

        elif field['type'] == 'timestamp':
            return config['timestamp'].strftime(field['format'])

        elif field['type'] == 'ip':
            return '.'.join(str(random.randint(0, 255)) for _ in range(4))

        else:
            return None

    def generate_log_entry(self, event: threading.Event, config: dict) -> None:
        # Create the directory if not there
        if not os.path.exists(os.path.dirname(config['file'])):
            os.makedirs(os.path.dirname(config['file']))

        # Truncate the log file
        if self.truncate:
            with open(config['file'], 'w') as log_file:
                log_file.truncate()
        else:
            with open(config['file'], 'a'):
                os.utime(config['file'], None)
        time.sleep(0)

        while not event.wait(config['frequency'].total_seconds()):
            self.logger.info('Writing %4d logs for "%s" (%s)' % (config['amount'], config['name'], config['file']))
            for ts in self.get_timestamps(config, datetime.datetime.utcnow()):
                config['timestamp'] = ts
                values = {field: self.next_value(config, field) for field in config['fields']}
                log_entry = config['format'].format(**values)
                with open(config['file'], 'a') as log_file:
                    log_file.write(log_entry + '\n')


def main() -> None:
    # Define the command arguments
    parser = argparse.ArgumentParser(description='Generate log events')
    parser.add_argument('config_dir', metavar='/path/to/config', type=str, help='Path to configuration directory or file')
    parser.add_argument('--level', '-l', default=logging.getLevelName(logging.INFO), help='Logging level')
    parser.add_argument('--truncate', '-t', action='store_true', help='Truncate the log files on start')
    args = parser.parse_args()

    # Get the logger
    logging.basicConfig(stream=sys.stderr, level=args.level,
                        format='%(asctime)s %(levelname)-8s %(message)s')
    logger = logging.getLogger()

    # Create the generator
    generator = Generator(args.config_dir, args.truncate)
    generator.logger = logger

    # Specify the signal handler
    signal.signal(signal.SIGINT, generator.handle_signal)
    signal.signal(signal.SIGHUP, generator.handle_signal)

    # Run the generator
    try:
        generator.run()
    except FileNotFoundError as e:
        generator.logger.critical(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
