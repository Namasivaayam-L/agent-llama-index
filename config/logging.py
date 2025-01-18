import logging
import sys

# Define logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(filename)s - %(funcName)s - line %(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", mode="a")
    ]
)

# Example of setting up logger for your application
logger = logging.getLogger("uvicorn-app")