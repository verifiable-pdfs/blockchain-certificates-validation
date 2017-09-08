Simple webapp to validate blockchain certificates issued to the blockchain. Uses blockchain-certificates code to validate.

FOR PRODUCTION make sure that:
- verify.py checks on the appropriate network (mainnet, testnet) and 
  with the correct prefix
- verify.html and verification.html have 82.116.203.239:8080 for mainnet
  and 82.116.203.239:18080 for testnet
