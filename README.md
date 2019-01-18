Simple webapp to validate blockchain certificates issued to the blockchain. Uses blockchain-certificates code to validate.

- verify.py checks on the mainnet by default (comment/uncomment appropriate code for testnet)


COMPATIBILITY
- Supports all UNic published certificates except those with index file
  . blockchain-certificates <= v0.9
  . this is a TODO
- validates self-contained certificates with old pdf metadata structure
  . blockchain-certificates v0.9.0
  . expects pdf metadata with keys: issuer, issuer_address and chainpoint_proof
- validates self-contained certificates with new pdf metadata structure
  . blockchain-certificates v0.10.0
  . expects pdf metadata with keys: metadata_object and chainpoint_proof
  . metadata_object is JSON that requires keys: issuer and issuer_address
- validates self-contained certificates with CRED meta-protocol support
  . blockchain-certificates v1.0.0

UI
- Note that when displaying the metadata take into account the metadata structure
  and display accordingly.
- It was possible to have a generic metadata display but it would not be ordered
  and we would have to use the keys as values
  . while now we display the metadata in any order we like with any caption/title
