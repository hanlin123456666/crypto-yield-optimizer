import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams

from utils import get_token_address
from protocol_operator import get_protocol_operator

logger = logging.getLogger(__name__)

