from Crypto.PublicKey import RSA

key = RSA.generate(4096)
 
private_key = key.export_key()
public_key = key.publickey().export_key()

with open("admin_private_key.pem", "wb") as f:
    f.write(private_key)

with open("public_key.pem", "wb") as r:
    r.write(public_key)
