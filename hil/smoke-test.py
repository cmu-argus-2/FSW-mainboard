import argparse
import datetime
import errno
import logging
import os
import sys
import time
from pathlib import Path

import serial

RETRY_DELAY = 5         # seconds

# Logging
def setup_logger(log_path):
    logger = logging.getLogger("hil_smoke_test")
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Formatter with timestamp + level
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

CUBESAT_LEVEL = 15
logging.addLevelName(CUBESAT_LEVEL, "CUBESAT")

def cubesat(self, message, *args, **kwargs):
    if self.isEnabledFor(CUBESAT_LEVEL):
        self._log(CUBESAT_LEVEL, message, args, **kwargs)

logging.Logger.cubesat = cubesat


# Try resolving the most likely CPy board symlink
def resolve_serial_symlink():
    by_id_path = Path("/dev/serial/by-id/")
    if not by_id_path.exists():
        raise FileNotFoundError("/dev/serial/by-id does not exist. Is the board connected?")
    
    candidates = list(by_id_path.glob("*"))
    if not candidates:
        raise FileNotFoundError("No serial devices found in /dev/serial/by-id")

    logger.info(f"Using resolved device: {candidates[0]} -> {candidates[0].resolve()}")
    return str(candidates[0].resolve())  # Resolves to /dev/ttyACM*

# Mainboard serial commands
def exit_to_repl(ser, logger):
    logger.info("[MINICOM] Exiting to REPL")
    ser.write(b'\x03' * 3)  # Ctrl-C (interrupt)
    time.sleep(0.5)

def reset(ser, logger):
    logger.info("[MINICOM] Soft Reset")
    ser.write(b'\x04')      # Ctrl-D (soft reboot)
    time.sleep(0.5)

# Generate logfile path using ISO 8601 timestamp
def generate_log_path():
    timestamp = datetime.datetime.now().isoformat(timespec='seconds').replace(":", "-")
    log_path = f"smoke_test_logs/smoke_output_{timestamp}.log"
    return log_path


# Main serial logging function
def monitor_serial_with_retries(port, baudrate=115200, max_retries=3, duration=300):
    retries = 0
    start_time = time.time()

    while retries < max_retries:
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                logger.info(f"Connected to port: {port}")                

                # On first connect only
                if retries == 0:
                    exit_to_repl(ser, logger)
                    reset(ser, logger)

                # Adjust remaining time
                remaining_time = duration - (time.time() - start_time)
                if remaining_time <= 0:
                    logger.info("Duration exhausted.")
                    break

                log_start = time.time()
                while time.time() - log_start < remaining_time:
                    if ser.in_waiting:
                        line = ser.readline().decode(errors='ignore').strip()
                        logger.cubesat(line)

                exit_to_repl(ser, logger)
                break  # Success, exit the retry loop

        except (OSError, serial.SerialException) as e:
            if isinstance(e, OSError) and e.errno != errno.EIO:
                raise  # Re-raise unknown OSError

            logger.warning(f"Mainboard serial connection lost. Retrying... (attempt {retries + 1}/{max_retries}): {e}\n")
            retries += 1
            time.sleep(RETRY_DELAY)

        except KeyboardInterrupt:
            logger.warning("Interrupted by user.\n")
            sys.exit(0)

    if retries >= max_retries:
        logger.critical("Failed to reconnect to serial device after multiple attempts.\n")
        sys.exit(1)

    return 


if __name__ == "__main__":

    # CLI arguments: number of retries and test duration
    parser = argparse.ArgumentParser(description="Run a smoke test on the mainboard over serial.")
    parser.add_argument("-r", "--retries", type=int, default=5,
                        help="Number of retry attempts on serial disconnect (-1 for infinite) (default: 5)")
    parser.add_argument("-d", "--duration", type=int, default=300,
                        help="Duration of the smoke test in seconds (default: 300)")

    args = parser.parse_args()

    log_path = generate_log_path()
    logger = setup_logger(log_path)

    try:
        port = resolve_serial_symlink()
        

        logger.info(f"Log file path: {log_path}")

        # Run the test!
        retries = args.retries if args.retries >= 0 else float("inf")

        # confirm specified args
        logger.info(f"Max retries: {retries}")
        logger.info(f"Test duration: {args.duration}")

        monitor_serial_with_retries(port, max_retries=retries, duration=args.duration)

        logger.info(f"\nSmoke test completed. Log saved to {log_path}")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"\n[FATAL] {e}")
        sys.exit(1)
